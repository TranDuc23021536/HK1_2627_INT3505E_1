import sqlite3
from flask import Flask, jsonify, request, make_response, g

app = Flask(__name__)
DB_PATH = "orders.db"

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()

def row_to_dict(row):
    return {"id": row["id"], "item": row["item"], "quantity": row["quantity"], "status": row["status"]}

@app.get("/orders")
def list_orders():
    db = get_db()
    rows = db.execute("SELECT * FROM orders").fetchall()
    return jsonify({"data": [row_to_dict(r) for r in rows], "total": len(rows)}), 200

@app.post("/orders")
def create_order():
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    body = request.get_json(silent=True)
    if body is None:
        return jsonify(error="malformed JSON"), 400
    item = (body.get("item") or "").strip()
    quantity = body.get("quantity")
    if not item or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(error="item and positive integer quantity required"), 422
    db = get_db()
    cur = db.execute(
        "INSERT INTO orders (item, quantity, status) VALUES (?, ?, ?)",
        (item, quantity, "pending"),
    )
    db.commit()
    order = row_to_dict(db.execute("SELECT * FROM orders WHERE id = ?", (cur.lastrowid,)).fetchone())
    resp = make_response(jsonify(order), 201)
    resp.headers["Location"] = f"/orders/{order['id']}"
    return resp

@app.get("/orders/<int:oid>")
def get_order(oid):
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    return jsonify(row_to_dict(row)), 200

@app.put("/orders/<int:oid>")
def put_order(oid):
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    body = request.get_json(silent=True) or {}
    item = (body.get("item") or "").strip()
    quantity = body.get("quantity")
    status = body.get("status") or "pending"
    if not item or not isinstance(quantity, int) or quantity <= 0:
        return jsonify(error="item and positive integer quantity required"), 422
    db.execute("UPDATE orders SET item = ?, quantity = ?, status = ? WHERE id = ?", (item, quantity, status, oid))
    db.commit()
    updated = row_to_dict(db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone())
    return jsonify(updated), 200

@app.delete("/orders/<int:oid>")
def delete_order(oid):
    db = get_db()
    row = db.execute("SELECT * FROM orders WHERE id = ?", (oid,)).fetchone()
    if row is None:
        return jsonify(error="not found"), 404
    db.execute("DELETE FROM orders WHERE id = ?", (oid,))
    db.commit()
    return "", 204

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=5000, debug=True)