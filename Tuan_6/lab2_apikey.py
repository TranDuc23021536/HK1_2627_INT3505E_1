import hashlib
import secrets
import sqlite3
import sys
from datetime import datetime, timezone
from functools import wraps

from flask import Flask, g, jsonify, request

DB_PATH = "lab2.db"
app = Flask(__name__)


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def mint_key(prefix):
    raw = secrets.token_urlsafe(32)
    digest = hashlib.sha256(raw.encode()).hexdigest()[:8]
    plain = f"{prefix}_{raw}_{digest}"
    store = hashlib.sha256(plain.encode()).hexdigest()
    return plain, store


def init_db():
    conn = db()
    conn.execute("DROP TABLE IF EXISTS api_keys")
    conn.execute(
        """CREATE TABLE api_keys (
            id INTEGER PRIMARY KEY,
            prefix TEXT,
            hash TEXT,
            last4 TEXT,
            owner_id INTEGER,
            scopes TEXT,
            created_at TEXT,
            expires_at TEXT,
            revoked_at TEXT,
            ip_allowlist TEXT
        )"""
    )
    plain, store = mint_key("sk_live")
    conn.execute(
        "INSERT INTO api_keys (prefix, hash, last4, owner_id, scopes, created_at) VALUES (?,?,?,?,?,?)",
        ("sk_live", store, plain[-4:], 1, "orders:read", now_utc()),
    )
    conn.commit()
    conn.close()
    print("API KEY (chỉ hiện 1 lần):")
    print(plain)


def revoke_key():
    conn = db()
    conn.execute("UPDATE api_keys SET revoked_at=? WHERE id=1", (now_utc(),))
    conn.commit()
    conn.close()
    print("Đã thu hồi key id=1")


def require_api_key(scopes=None):
    def d(fn):
        @wraps(fn)
        def w(*a, **kw):
            key = request.headers.get("X-Api-Key", "")
            if not key:
                return jsonify({"e": "missing"}), 401
            hashed = hashlib.sha256(key.encode()).hexdigest()
            conn = db()
            row = conn.execute(
                "SELECT id, owner_id, scopes, revoked_at, expires_at FROM api_keys WHERE hash=?",
                (hashed,),
            ).fetchone()
            conn.close()
            if (
                not row
                or row["revoked_at"]
                or (row["expires_at"] is not None and row["expires_at"] <= now_utc())
            ):
                return jsonify({"e": "invalid"}), 401
            granted = set(row["scopes"].split(","))
            if scopes and not set(scopes).issubset(granted):
                return jsonify({"e": "scope"}), 403
            g.api_key_id = row["id"]
            g.owner_id = row["owner_id"]
            g.api_scopes = granted
            return fn(*a, **kw)

        return w

    return d


@app.get("/api/orders")
@require_api_key(scopes=["orders:read"])
def list_orders():
    return jsonify({"orders": ["o-001"], "owner_id": g.owner_id, "scopes": sorted(g.api_scopes)})


@app.post("/pay")
@require_api_key(scopes=["pay:write"])
def pay():
    return jsonify({"status": "paid"})


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    if cmd == "init":
        init_db()
    elif cmd == "revoke":
        revoke_key()
    else:
        app.run(port=5002)