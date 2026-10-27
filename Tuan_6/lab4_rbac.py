import secrets
from functools import wraps

import bcrypt
from flask import Flask, g, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

app = Flask(__name__)
app.config.update(JWT_SECRET_KEY=secrets.token_urlsafe(48), JWT_ACCESS_TOKEN_EXPIRES=900)
jwt = JWTManager(app)

PWD = bcrypt.hashpw(b"password123", bcrypt.gensalt())
USERS = {
    "an@vnu.edu.vn": {"id": 1, "pwd_hash": PWD, "roles": ["admin"], "scopes": ["orders:read", "orders:write"]},
    "binh@vnu.edu.vn": {"id": 2, "pwd_hash": PWD, "roles": ["viewer"], "scopes": ["orders:read"]},
}
USERS_BY_ID = {u["id"]: u for u in USERS.values()}
ORDERS = {1: {"owner_id": 1, "item": "laptop"}, 2: {"owner_id": 2, "item": "keyboard"}}


def load_current_user(fn):
    @wraps(fn)
    def w(*a, **kw):
        g.current_user = USERS_BY_ID[int(get_jwt_identity())]
        return fn(*a, **kw)

    return w


def require_roles(*allowed):
    def d(fn):
        @wraps(fn)
        def w(*a, **kw):
            urs = set(g.current_user["roles"])
            if not urs & set(allowed):
                return jsonify({"error": "forbidden", "need_one_of": list(allowed)}), 403
            return fn(*a, **kw)

        return w

    return d


def require_scopes(*needed):
    def d(fn):
        @wraps(fn)
        def w(*a, **kw):
            granted = set(get_jwt().get("scopes", []))
            if not set(needed).issubset(granted):
                return jsonify({"error": "insufficient_scope", "need_all_of": list(needed)}), 403
            return fn(*a, **kw)

        return w

    return d


def user_owns_resource(param="id"):
    def d(fn):
        @wraps(fn)
        def w(*a, **kw):
            row = ORDERS.get(kw[param])
            if not row:
                return jsonify({"e": "nf"}), 404
            ok = str(row["owner_id"]) == str(g.current_user["id"])
            if not ok and "admin" not in g.current_user["roles"]:
                return jsonify({"error": "forbidden"}), 403
            return fn(*a, **kw)

        return w

    return d


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    user = USERS.get(body.get("email"))
    pwd = (body.get("password") or "").encode()
    if not user or not bcrypt.checkpw(pwd, user["pwd_hash"]):
        return jsonify(error="invalid_credentials"), 401
    claims = {"roles": user["roles"], "scopes": user["scopes"]}
    return jsonify(access=create_access_token(identity=str(user["id"]), additional_claims=claims))


@app.get("/api/orders/<int:id>")
@jwt_required()
@load_current_user
@require_scopes("orders:read")
@user_owns_resource("id")
def get_order(id):
    return jsonify(ORDERS[id])


@app.delete("/api/orders/<int:id>")
@jwt_required()
@load_current_user
@require_roles("admin", "manager")
@require_scopes("orders:write")
@user_owns_resource("id")
def delete_order(id):
    ORDERS.pop(id)
    return "", 204


if __name__ == "__main__":
    app.run(port=5004)