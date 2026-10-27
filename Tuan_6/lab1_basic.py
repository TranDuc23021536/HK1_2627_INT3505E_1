from flask import Flask, jsonify
from flask_httpauth import HTTPBasicAuth
import bcrypt

app = Flask(__name__)
auth = HTTPBasicAuth()

_users = {
    "an@vnu.edu.vn": bcrypt.hashpw(b"correct horse battery staple", bcrypt.gensalt())
}


@auth.verify_password
def verify_password(username, password):
    stored = _users.get(username)
    if stored is None:
        return None
    if bcrypt.checkpw(password.encode(), stored):
        return username
    return None


@auth.error_handler
def on_auth_error(status):
    return jsonify({"error": "unauthorized"}), 401, {
        "WWW-Authenticate": 'Basic realm="orders"'
    }


@app.route("/api/orders", methods=["GET"])
@auth.login_required
def list_orders():
    return jsonify({"orders": ["o-001"], "principal": auth.current_user()})


if __name__ == "__main__":
    app.run(port=5001, ssl_context="adhoc")