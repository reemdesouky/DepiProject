from flask import Blueprint, request, jsonify, session
import os

auth_bp = Blueprint("auth", __name__)

STORE_CREDENTIALS = {
    "x": {"username": os.getenv("STORE_X_USER", "admin_x"), "password": os.getenv("STORE_X_PASS", "passX")},
    "y": {"username": os.getenv("STORE_Y_USER", "admin_y"), "password": os.getenv("STORE_Y_PASS", "passY")},
    "z": {"username": os.getenv("STORE_Z_USER", "admin_z"), "password": os.getenv("STORE_Z_PASS", "passZ")},
}

@auth_bp.route("/login", methods=["POST"])
def login():
    body = request.get_json()
    if not body:
        return jsonify({"error": "Invalid request"}), 400

    username = body.get("username", "").strip()
    password = body.get("password", "").strip()
    store    = body.get("store", "").strip().lower()

    creds = STORE_CREDENTIALS.get(store)
    if not creds:
        return jsonify({"error": "Invalid store"}), 400

    if username == creds["username"] and password == creds["password"]:
        session["user"]  = username
        session["store"] = store
        return jsonify({"status": "ok", "store": store})

    return jsonify({"error": "Invalid username or password"}), 401


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "logged out"})


@auth_bp.route("/me")
def me():
    user  = session.get("user")
    store = session.get("store")
    if not user:
        return jsonify({"error": "Not authenticated"}), 401
    return jsonify({"user": user, "store": store})