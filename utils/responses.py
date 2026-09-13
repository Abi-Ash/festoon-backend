from flask import jsonify


def success(message="Success", data=None, status_code=200):
    payload = {"success": True, "message": message}
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status_code


def error(message="Something went wrong", status_code=400):
    return jsonify({"success": False, "message": message}), status_code
