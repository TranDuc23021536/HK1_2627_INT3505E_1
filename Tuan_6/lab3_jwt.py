import secrets

import bcrypt
from flask import Flask, jsonify, request
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    create_refresh_token,
    get_jwt,
    get_jwt_identity,
    jwt_required,
)

app = Flask(__name__)
app.config.update(
    JWT_SECRET_KEY=secrets.token_urlsafe(48),
    JWT_ACCESS_TOKEN_EXPIRES=900,
    JWT_REFRESH_TOKEN_EXPIRES=2592000,
    JWT_ALGORITHM="HS256",
)
jwt = JWTManager(app)

USERS = {
    "an@vnu.edu.vn": {
        "id": 1,
        "pwd_hash": bcrypt.hashpw(b"correct horse battery staple", bcrypt.gensalt()),
        "roles": ["admin"],
        "scopes": ["orders:read", "orders:write"],
    }
}
REVOKED = set()


def load_permissions(uid):
    for u in USERS.values():
        if str(u["id"]) == str(uid):
            return {"roles": u["roles"], "scopes": u["scopes"]}
    return {"roles": [], "scopes": []}


@jwt.token_in_blocklist_loader
def check_revoked(_h, claims):
    return claims["jti"] in REVOKED


@jwt.revoked_token_loader
def on_revoked(_h, _p):
    return jsonify(error="token_revoked"), 401


@app.post("/api/auth/login")
def login():
    body = request.get_json(silent=True) or {}
    user = USERS.get(body.get("email"))
    pwd = (body.get("password") or "").encode()
    if not user or not bcrypt.checkpw(pwd, user["pwd_hash"]):
        return jsonify(error="invalid_credentials"), 401
    claims = load_permissions(user["id"])
    uid = str(user["id"])
    return jsonify(
        access=create_access_token(identity=uid, additional_claims=claims),
        refresh=create_refresh_token(identity=uid, additional_claims=claims),
    )


@app.get("/api/orders")
@jwt_required()
def list_orders():
    uid = get_jwt_identity()
    claims = get_jwt()
    if "orders:read" not in claims.get("scopes", []):
        return jsonify(error="insufficient_scope"), 403
    return jsonify(user=uid, orders=["o-001", "o-002"])


@app.post("/api/auth/refresh")
@jwt_required(refresh=True)
def refresh():
    uid = get_jwt_identity()
    claims = load_permissions(uid)
    return jsonify(access=create_access_token(identity=uid, additional_claims=claims))


@app.post("/api/auth/logout")
@jwt_required(verify_type=False)
def logout():
    REVOKED.add(get_jwt()["jti"])
    return jsonify(status="revoked")


if __name__ == "__main__":
    app.run(port=5003)