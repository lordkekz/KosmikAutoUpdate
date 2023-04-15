import json
import sys
import time

from flask import Flask, request, jsonify

from version_manager import VersionManager

DL_HOST = "http://0.0.0.0/"
INDEX_PATH = None
DL_PATH = None
KEYS_PATH = None

app = Flask(__name__)


@app.route('/get_channels', methods=['POST'])
def get_channels():
    vm = VersionManager(INDEX_PATH, DL_PATH)
    channels = dict()
    for x in vm.get_channels():
        channels[x["name"]] = str(x["version"])

    vm.dispose()
    return jsonify({"channels": channels}), 200


@app.route('/get_version', methods=['POST'])
def get_version():
    data = request.json
    ip = request.remote_addr

    # Initialize the VersionManager in this (worker) thread, since the SQLite connection can't be shared
    vm = VersionManager(INDEX_PATH, DL_PATH)

    # Helper functions
    def make_url_version_archive(ver_id: str) -> str:
        relative_path = "/version_zips/" + ver_id + ".zip"
        return DL_HOST + relative_path + "?token=" + vm.make_download_token(relative_path, ip)["token"]

    def make_url_file(file_hash: str) -> str:
        relative_path = "/hashed_files/" + file_hash + ".zip"
        return DL_HOST + relative_path + "?token=" + vm.make_download_token(relative_path, ip)["token"]

    if "version_id" in data and "channel" in data:
        vm.dispose()
        return "Must request either by version_id or by channel; not both.", 400

    elif "version_id" in data:
        ver_id = data["version_id"]
        ver = vm.get_version(ver_id)
        if ver is None:
            vm.dispose()
            return "Unknown version_id", 404

    elif "channel" in data:
        ver_id = vm.get_version_id_by_channel(data["channel"])
        if ver_id is None:
            vm.dispose()
            return "Unknown channel", 404

        ver = vm.get_version(ver_id)
        if ver is None:
            vm.dispose()
            return "Broken Channel. Please report to admin.", 500

    else:
        vm.dispose()
        return "Must request either by version_id or channel.", 400

    resp = {
        "version_id": ver_id,
        "date": ver["date"],
        "archive_bytes": ver["archive_bytes"],
        "archive_md5": ver["archive_md5"],
        "archive_url": make_url_version_archive(ver_id),
        "files": dict([(x["path"], {
            "md5": x["file_hash"],
            "archive_bytes": x["archive_bytes"],
            "file_url": make_url_file(x["file_hash"])
        }) for x in vm.get_version_files(ver_id)])
    }

    # Purge expired tokens and save changes (including new tokens)
    vm.purge_expired_tokens()
    vm.dispose()
    if app.debug:
        return json.dumps(resp, indent=4)
    else:
        return jsonify(resp)


@app.route('/check_access/<path:relative_path>', methods=['GET'])
def check_access(relative_path: str):
    relative_path = "/" + relative_path
    if "token" not in request.args:
        return "Token required", 403
    if "X-Original-IP" not in request.headers:
        return "Missing header", 500
    token = request.args["token"]
    ip = request.headers["X-Original-IP"]
    print(end=f"Checking access to {relative_path} with token {token} for {ip}", file=sys.stderr)

    vm = VersionManager(INDEX_PATH, DL_PATH)
    dt = vm.get_download_token(relative_path, ip)
    vm.dispose()

    if dt is not None and token == dt["token"] and dt["expiration"] > time.strftime("%Y-%m-%d %H:%M:%S"):
        print("    OK", file=sys.stderr)
        return "Valid token", 200
    print("    INVALID TOKEN", file=sys.stderr)
    return "Invalid token", 403


if __name__ == "__main__":
    INDEX_PATH = "index.db"
    DL_PATH = "dl/"
    app.run(port=8080, debug=True)
