from flask import Flask, request, jsonify

from version_manager import VersionManager

DL_HOST = "http://0.0.0.0/"
VERSION_MANAGER = None

app = Flask(__name__)


@app.route('/GET_CHANNELS', methods=['POST'])
def get_channels():
    VERSION_MANAGER.reload()
    channels = VERSION_MANAGER.get_channels()

    return jsonify(channels), 200


@app.route('/GET_VERSION', methods=['POST'])
def get_version():
    VERSION_MANAGER.reload()
    data = request.json

    def prep_response(resp, ver):
        resp["version_id"] = ver
        resp["archive_url"] = DL_HOST + "version_zips/" + ver + ".zip"
        for file in resp["files"]:
            resp["files"][file]["url"] = DL_HOST + "hashed_files/" + resp["files"][file]["md5"]
        return resp

    if "channel" in data:
        ver = VERSION_MANAGER.get_channel_version(data["channel"])
        if ver is None:
            return "Unknown channel", 404
        r = VERSION_MANAGER.get_version(ver)
        return jsonify(prep_response(r, ver)) if r is not None else ("Broken Channel. Please report to admin.", 500)

    if "version_id" in data:
        r = VERSION_MANAGER.get_version(data["version_id"])
        if r is None:
            return "Unknown version_id", 404
        return jsonify(prep_response(r, data["version_id"]))

    return "Must request either by version_id or channel.", 400


if __name__ == "__main__":
    VERSION_MANAGER = VersionManager("version.json", "dl/")
    app.run(port=8080)
