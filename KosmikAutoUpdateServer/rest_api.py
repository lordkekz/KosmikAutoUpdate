import json

from flask import Flask, request, jsonify

from version_manager import VersionManager

DL_HOST = "http://0.0.0.0/"
INDEX_PATH = None
DL_PATH = None
KEYS_PATH = None

app = Flask(__name__)


@app.route('/GET_CHANNELS', methods=['POST'])
def get_channels():
    vm = VersionManager(INDEX_PATH, DL_PATH)
    channels = dict()
    for x in vm.get_channels():
        channels[x["name"]] = str(x["version"])

    vm.dispose()
    return jsonify({"channels": channels}), 200


@app.route('/GET_VERSION', methods=['POST'])
def get_version():
    data = request.json
    # Initialize the VersionManager in this (worker) thread, since the SQLite connection can't be shared
    vm = VersionManager(INDEX_PATH, DL_PATH)

    # Helper functions
    def make_url_version_archive(ver_id: str) -> str:
        return DL_HOST + "version_zips/" + ver_id + ".zip"

    def make_url_file(file_hash: str) -> str:
        return DL_HOST + "hashed_files/" + file_hash + ".zip"

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

    vm.dispose()
    if app.debug:
        return json.dumps(resp, indent=4)
    else:
        return jsonify(resp)


if __name__ == "__main__":
    INDEX_PATH = "index.db"
    DL_PATH = "dl/"
    app.run(port=8080, debug=True)
