import base64
import json
import random
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from errors import ApiProblem, register_error_handlers

app = Flask(__name__)
register_error_handlers(app)

DEFAULT_LIMIT = 20
MAX_LIMIT = 100
ALLOWED_FIELDS = {"id", "customer_id", "status", "total", "created_at"}
SORTABLE = {"id", "created_at", "total"}
STATUSES = ["pending", "paid", "shipped", "cancelled"]


def _seed(n=120):
    rnd = random.Random(42)
    base = datetime(2026, 1, 1)
    return [
        {
            "id": i,
            "customer_id": rnd.randint(1, 10),
            "status": rnd.choice(STATUSES),
            "total": round(rnd.uniform(10, 500), 2),
            "created_at": (base + timedelta(hours=i)).isoformat() + "Z",
        }
        for i in range(1, n + 1)
    ]

ORDERS = _seed()

def encode_cursor(sort_field, desc, last):
    payload = {"s": sort_field, "d": desc, "v": last[sort_field], "id": last["id"]}
    return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()

def decode_cursor(token):
    try:
        data = json.loads(base64.urlsafe_b64decode(token.encode()))
        assert {"s", "d", "v", "id"} <= data.keys()
        return data
    except Exception:
        raise ApiProblem(400, "Invalid cursor", "The cursor is malformed or expired.", "invalid-cursor")

def parse_limit():
    raw = request.args.get("limit", DEFAULT_LIMIT)
    try:
        limit = int(raw)
    except ValueError:
        raise ApiProblem(400, "Invalid limit", "limit must be an integer.", "invalid-limit")
    if limit < 1 or limit > MAX_LIMIT:
        raise ApiProblem(400, "Invalid limit", f"limit must be between 1 and {MAX_LIMIT}.", "invalid-limit")
    return limit

def parse_sort():
    raw = request.args.get("sort", "-id") 
    desc = raw.startswith("-")
    field = raw.lstrip("-+")
    if field not in SORTABLE:
        raise ApiProblem(400, "Invalid sort field", f"sort must be one of {sorted(SORTABLE)}.", "invalid-sort")
    return field, desc

def parse_fields():
    raw = request.args.get("fields")
    if not raw:
        return None
    fields = [f.strip() for f in raw.split(",") if f.strip()]
    unknown = set(fields) - ALLOWED_FIELDS
    if unknown: 
        raise ApiProblem(
            400, "Unknown field", f"Unknown fields: {sorted(unknown)}.", "unknown-field", allowed=sorted(ALLOWED_FIELDS)
        )
    return fields

@app.get("/orders")
def list_orders():
    limit = parse_limit()
    sort_field, desc = parse_sort()
    fields = parse_fields()
    items = ORDERS
    status = request.args.get("status")
    if status:
        if status not in STATUSES:
            raise ApiProblem(400, "Invalid status", f"status must be one of {STATUSES}.", "invalid-status")
        items = [o for o in items if o["status"] == status]
    customer_id = request.args.get("customer_id")
    if customer_id:
        try:
            cid = int(customer_id)
        except ValueError:
            raise ApiProblem(400, "Invalid customer_id", "customer_id must be an integer.", "invalid-customer-id")
        items = [o for o in items if o["customer_id"] == cid]
    items = sorted(items, key=lambda o: (o[sort_field], o["id"]), reverse=desc)
    token = request.args.get("cursor")
    if token:
        c = decode_cursor(token)
        if c["s"] != sort_field or c["d"] != desc:
            raise ApiProblem(400, "Invalid cursor", "Cursor does not match the current sort.", "invalid-cursor")
        key = (c["v"], c["id"])
        if desc:
            items = [o for o in items if (o[sort_field], o["id"]) < key]
        else:
            items = [o for o in items if (o[sort_field], o["id"]) > key]
    page = items[: limit + 1]
    has_more = len(page) > limit
    page = page[:limit]
    next_cursor = encode_cursor(sort_field, desc, page[-1]) if has_more else None
    data = [{k: o[k] for k in fields} for o in page] if fields else page
    return jsonify({"data": data, "next_cursor": next_cursor, "limit": limit})

if __name__ == "__main__":
    app.run(port=5000, debug=False)