from __future__ import annotations

import hashlib
import os
import secrets
import sqlite3
import time
import zipfile

from gitsemanticversion import GitSemanticVersion

CREATE_DB_SCHEMA = """
-- Enable enforcing of foreign keys
PRAGMA foreign_keys = ON;

-- Versions table
CREATE TABLE IF NOT EXISTS versions (
    version_id text PRIMARY KEY,
    ver_datetime text NOT NULL,
    archive_bytes integer,
    archive_md5 string
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    md5 text PRIMARY KEY,
    bytes integer NOT NULL,
    archive_bytes integer NOT NULL
);

-- Relationship of versions to their constituting files
CREATE TABLE IF NOT EXISTS version_files (
    version_id text NOT NULL,
    path text NOT NULL,
    md5 text NOT NULL,
    FOREIGN KEY (version_id) REFERENCES versions (version_id),
    FOREIGN KEY (md5) REFERENCES files (md5),
    PRIMARY KEY (version_id, path)
);

-- Channels to point so some versions
CREATE TABLE IF NOT EXISTS channels (
    name text PRIMARY KEY,
    version_id text NOT NULL,
    FOREIGN KEY (version_id) REFERENCES versions (version_id)
);

-- Tokens to authorize downloading a specific file
CREATE TABLE IF NOT EXISTS download_tokens (
    relative_path text NOT NULL,
    ip text NOT NULL,
    token text NOT NULL,
    expiration text NOT NULL,
    PRIMARY KEY (relative_path, ip)
);
"""


class VersionManager:
    def __init__(self, index_path: str, dl_dir: str):
        self.__conn = sqlite3.connect(index_path)
        self.__dl_hashes_path = os.path.join(dl_dir, "hashed_files")
        self.__dl_versions_path = os.path.join(dl_dir, "version_zips")
        os.makedirs(self.__dl_hashes_path, exist_ok=True)
        os.makedirs(self.__dl_versions_path, exist_ok=True)
        self.__conn.executescript(CREATE_DB_SCHEMA)
        self.__conn.commit()

    def get_channels(self) -> list[dict]:
        return [{"name": name, "version": version} for name, version in
                self.__conn.execute("""SELECT name, version_id FROM channels""").fetchall()]

    def get_version_id_by_channel(self, channel: str) -> str | None:
        x = self.__conn.execute("""SELECT version_id FROM channels WHERE name=?""", [channel]).fetchone()
        return x[0] if x is not None else None

    def get_version(self, version: str | GitSemanticVersion) -> dict | None:
        x = self.__conn.execute(
            """SELECT version_id, ver_datetime, archive_bytes, archive_md5 FROM versions WHERE version_id=?""",
            [str(version)]).fetchone()
        return {"version": x[0],
                "date": x[1],
                "archive_bytes": x[2],
                "archive_md5": x[3]} if x is not None else None

    def get_version_files(self, version: str | GitSemanticVersion) -> list[dict]:
        return [{"file_hash": a, "path": b, "bytes": c, "archive_bytes": d} for a, b, c, d in
                self.__conn.execute(""" SELECT vf.md5, vf.path, f.bytes, f.archive_bytes
                                        FROM version_files vf, files f 
                                        WHERE vf.version_id=? AND vf.md5=f.md5""",
                                    [str(version)]).fetchall()]

    def get_fileinfo(self, file_hash: str) -> dict | None:
        x = self.__conn.execute("""SELECT bytes, archive_bytes FROM files WHERE md5=?""",
                                [file_hash]).fetchone()
        return {"bytes": x[0], "archive_bytes": x[1]} if x is not None else None

    def has_channel(self, channel: str) -> bool:
        return channel in self.get_channels()

    def has_version(self, version: str | GitSemanticVersion) -> bool:
        return self.get_version(version) is not None

    def has_file(self, file_hash: str) -> bool:
        return self.get_fileinfo(file_hash) is not None

    def is_file_used(self, file_hash: str) -> bool:
        x = self.__conn.execute("""SELECT version_id FROM files WHERE md5=? LIMIT 1""", [file_hash]).fetchone()
        return x is not None

    def get_download_token(self, relative_path: str, ip: str):
        x = self.__conn.execute("""SELECT token, expiration FROM download_tokens WHERE relative_path=? AND ip=?""",
                                [relative_path, ip]).fetchone()
        return {"token": x[0], "expiration": x[1]} if x is not None else None

    def make_download_token(self, relative_path: str, ip: str) -> dict:
        dt = self.get_download_token(relative_path, ip)
        if dt is not None:
            return dt

        # Generate random token data and hash it to always have consistent length and simple chars
        random_token = hashlib.md5(secrets.token_bytes(64)).hexdigest()

        # Expiration time is current time plus 10 minutes
        expiration = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time() + 10 * 60))

        self.__conn.execute("""INSERT INTO download_tokens(relative_path, ip, token, expiration) VALUES (?,?,?,?)""",
                            [relative_path, ip, random_token, expiration])
        self.__conn.commit()
        return {"token": random_token, "expiration": expiration}

    def purge_expired_tokens(self):
        self.__conn.execute("""DELETE FROM download_tokens WHERE expiration<?""",
                            [time.strftime("%Y-%m-%d %H:%M:%S")])
        self.__conn.commit()

    def add_version(self, version: str | GitSemanticVersion, directory_path: str):
        assert not self.has_version(version)
        print("Adding version", version)

        # Create version
        self.__conn.execute("""INSERT INTO versions(version_id, ver_datetime) VALUES (?, ?)""",
                            [str(version), time.strftime("%Y-%m-%d %H:%M:%S")])

        # Process files in directory_path
        archive_path = os.path.join(self.__dl_versions_path, str(version) + ".zip")
        with zipfile.ZipFile(archive_path, "w") as version_archive:
            for current_dir, _, files in os.walk(directory_path):
                for filename in files:
                    absolute_path = os.path.abspath(os.path.join(current_dir, filename))
                    filepath = os.path.relpath(absolute_path, directory_path)
                    print(end=f"Version {version}; Processing file {filepath}")

                    size_bytes = os.path.getsize(absolute_path)
                    md5 = hashlib.md5(open(absolute_path, "rb").read()).hexdigest()
                    hash_path = os.path.join(self.__dl_hashes_path, md5 + ".zip")

                    # Store compressed file
                    if not self.has_file(md5):
                        with zipfile.ZipFile(hash_path, "x") as file_archive:
                            file_archive.write(absolute_path, md5)
                            archive_bytes = os.path.getsize(hash_path)
                        self.__conn.execute("""INSERT INTO files(md5, bytes, archive_bytes) VALUES (?,?,?)""",
                                            [md5, size_bytes, archive_bytes])
                    else:
                        archive_bytes = os.path.getsize(hash_path)
                    print(end=f"; MD5 {md5}; Bytes {size_bytes}; Archive {archive_bytes}")

                    # Add file to version
                    self.__conn.execute("""INSERT INTO version_files(version_id, md5, path) VALUES (?,?,?)""",
                                        [str(version), md5, filepath])

                    # Add file to version archive
                    version_archive.write(absolute_path, filepath)
                    print("; DONE")

        # Update archive info
        self.__conn.execute("""UPDATE versions SET archive_bytes=?, archive_md5=? WHERE version_id=?""",
                            [os.path.getsize(archive_path),
                             hashlib.md5(open(archive_path, "rb").read()).hexdigest(),
                             str(version)])
        self.__conn.commit()
        print("Version", version, "DONE")

    def set_channel(self, channel: str, version: str | GitSemanticVersion) -> None:
        assert self.has_version(version)
        if self.has_channel(channel):
            self.__conn.execute("""UPDATE channels SET version_id = ? WHERE name = ?""", [str(version), channel])
        else:
            self.__conn.execute("""INSERT INTO channels(name, version_id) VALUES (?, ?)""", [channel, str(version)])
        self.__conn.commit()

    def dispose(self):
        self.__conn.close()


if __name__ == "__main__":
    vm = VersionManager("/index.db", "/dl/")
    vm.add_version(GitSemanticVersion(1, 2, 3), "/pwd/")
    vm.set_channel("main", GitSemanticVersion(1, 2, 3))
    # vm.set_channel("test", GitSemanticVersion(1, 2, 7))
