import json
import os
import time
import zipfile
from typing import Optional

from gitsemanticversion import GitSemanticVersion


class VersionManager:
    def __init__(self, index_path: str, dl_dir: str):
        self.__index_path = index_path
        self.__dl_hashes_path = os.path.join(dl_dir, "hashed_files")
        self.__dl_versions_path = os.path.join(dl_dir, "version_zips")
        os.makedirs(self.__dl_hashes_path, exist_ok=True)
        os.makedirs(self.__dl_versions_path, exist_ok=True)
        self.__obj = dict()
        self.reload()

    def get_channels(self) -> object:
        return self.__obj["channels"]

    def get_version(self, version_id: str) -> Optional[object]:
        try:
            return self.__obj["versions"][version_id]
        except Exception:
            return None

    def get_channel_version(self, channel: str) -> Optional[str]:
        try:
            return self.__obj["channels"][channel]["current_version"]
        except Exception:
            return None

    def add_version(self, version: GitSemanticVersion, directory_path: str):
        assert str(version) not in self.__obj["versions"]
        ver = {"date": time.strftime("%Y-%m-%d %H:%M:%S"),
               "files": {}}
        from shutil import copyfile
        import os
        import hashlib
        archive_path = os.path.join(self.__dl_versions_path, str(version) + ".zip")
        with zipfile.ZipFile(archive_path, "w") as f:
            for current_dir, _, files in os.walk(directory_path):
                for filename in files:
                    filepath = os.path.join(current_dir[len(directory_path):], filename)
                    print(filepath)
                    absolute_path = os.path.abspath(os.path.join(directory_path, filepath))
                    ver["files"][filepath] = entry = {
                        "md5": hashlib.md5(open(absolute_path, "rb").read()).hexdigest(),
                        "bytes": os.path.getsize(absolute_path)
                    }

                    f.write(absolute_path, filepath)
                    hash_path = os.path.join(self.__dl_hashes_path, entry["md5"])
                    if not os.path.exists(hash_path):
                        copyfile(absolute_path, hash_path)
        ver["archive_bytes"] = os.path.getsize(archive_path)
        ver["archive_md5"] = hashlib.md5(open(archive_path, "rb").read()).hexdigest()
        self.__obj["versions"][str(version)] = ver
        self.save()

    def set_channel(self, channel: str, version: GitSemanticVersion):
        if channel not in self.__obj["channels"]:
            self.__obj["channels"][channel] = dict()
        self.__obj["channels"][channel]["current_version"] = str(version)
        self.save()

    def reload(self):
        try:
            with open(self.__index_path) as f:
                self.__obj = json.load(f)
        except IOError:
            pass

        if "versions" not in self.__obj:
            self.__obj["versions"] = dict()
        if "channels" not in self.__obj:
            self.__obj["channels"] = dict()
        self.save()

    def save(self):
        with open(self.__index_path, "w") as f:
            json.dump(self.__obj, f, indent=4)


if __name__ == "__main__":
    vm = VersionManager()
    # vm.add_version(GitSemanticVersion(1, 2, 7), "testpath/")
    # vm.set_channel("main", GitSemanticVersion(1, 2, 6))
    # vm.set_channel("test", GitSemanticVersion(1, 2, 7))
