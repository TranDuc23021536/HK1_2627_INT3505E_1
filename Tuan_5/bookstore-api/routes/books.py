import base64
import json

from flask import Blueprint, jsonify, request
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from models import Book, Category, db

bp = Blueprint("books", __name__, url_prefix="/api/v1/books")

DEFAULT_LIMIT = 20
MAX_LIMIT = 100

SORT_FIELDS = {
    "id": Book.id,
    "title": Book.title,
    "price": Book.price_vnd,
    "stock": Book.stock,
}
SORT_ATTRS = {"id": "id", "title": "title", "price": "price_vnd", "stock": "stock"}

class ApiError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message

@bp.errorhandler(ApiError)
def handle_api_error(err):
    return jsonify({"error": err.code, "message": err.message}), 400

def get_int(name, default, minimum):
    raw = request.args.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        raise ApiError("bad_param", f"'{name}' phải là số nguyên")
    if value < minimum:
        raise ApiError("bad_param", f"'{name}' phải >= {minimum}")
    return value

def parse_sort(raw):
    """'-price,title' -> [('price', True), ('title', False), ('id', True)]
    Luôn thêm id vào cuối để làm tie-break (unique) cho cursor."""
    keys = []
    for part in raw.split(","):
        part = part.strip()
        desc = part.startswith("-")
        name = part[1:] if desc else part
        if name not in SORT_FIELDS:
            raise ApiError(
                "bad_sort",
                f"Không hỗ trợ sort theo '{name}'. Cho phép: {', '.join(SORT_FIELDS)}",
            )
        if any(k[0] == name for k in keys):
            raise ApiError("bad_sort", f"'{name}' bị lặp trong sort")
        keys.append((name, desc))
    if not any(name == "id" for name, _ in keys):
        keys.append(("id", keys[0][1]))
    return keys

def sort_to_str(keys):
    return ",".join(("-" if desc else "") + name for name, desc in keys)

def order_columns(keys):
    cols = []
    for name, desc in keys:
        col = SORT_FIELDS[name]
        cols.append(col.desc() if desc else col.asc())
    return cols

def encode_cursor(data):
    raw = json.dumps(data, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).decode().rstrip("=")

def decode_cursor(token):
    try:
        pad = "=" * (-len(token) % 4)
        data = json.loads(base64.urlsafe_b64decode(token + pad))
    except (ValueError, TypeError):
        raise ApiError("bad_cursor", "Cursor không hợp lệ")
    if not isinstance(data, dict):
        raise ApiError("bad_cursor", "Cursor không hợp lệ")
    return data

def read_cursor(token, keys, genre):
    data = decode_cursor(token)
    if data.get("s") != sort_to_str(keys) or data.get("g") != genre:
        raise ApiError("cursor_mismatch", "Cursor không khớp với sort/genre hiện tại")
    values = data.get("v")
    if not isinstance(values, list) or len(values) != len(keys):
        raise ApiError("bad_cursor", "Cursor không hợp lệ")
    return values

def keyset_condition(keys, values):
    """Điều kiện 'lấy các dòng đứng SAU dòng cuối của trang trước' cho sort đa khóa.
    (k1 > v1) OR (k1 = v1 AND k2 > v2) OR ...   (dùng < nếu khóa đó sort desc)"""
    branches = []
    for i, (name, desc) in enumerate(keys):
        col = SORT_FIELDS[name]
        equal_before = [SORT_FIELDS[keys[j][0]] == values[j] for j in range(i)]
        after = col < values[i] if desc else col > values[i]
        branches.append(and_(*equal_before, after))
    return or_(*branches)

@bp.get("")
def list_books():
    strategy = request.args.get("strategy", "cursor")
    if strategy not in ("cursor", "offset"):
        raise ApiError("bad_strategy", "strategy phải là 'cursor' hoặc 'offset'")

    limit = min(get_int("limit", DEFAULT_LIMIT, 1), MAX_LIMIT)
    genre = request.args.get("genre") or None
    keys = parse_sort(request.args.get("sort", "-id"))

    base = select(Book)
    if genre:
        base = base.where(Book.category.has(Category.slug == genre))

    stmt = base.options(
        selectinload(Book.authors), selectinload(Book.category)  # tránh N+1
    ).order_by(*order_columns(keys))

    if strategy == "offset":
        offset = get_int("offset", 0, 0)
        total = db.session.scalar(select(func.count()).select_from(base.subquery()))
        rows = db.session.scalars(stmt.offset(offset).limit(limit)).all()
        pagination = {
            "strategy": "offset",
            "offset": offset,
            "limit": limit,
            "total": total,
            "has_more": offset + len(rows) < total,
        }
    else:
        token = request.args.get("cursor")
        if token:
            stmt = stmt.where(keyset_condition(keys, read_cursor(token, keys, genre)))
        rows = db.session.scalars(stmt.limit(limit + 1)).all()  # +1 để biết còn trang sau
        has_more = len(rows) > limit
        rows = rows[:limit]
        next_cursor = None
        if has_more:
            last = rows[-1]
            next_cursor = encode_cursor(
                {
                    "s": sort_to_str(keys),
                    "g": genre,
                    "v": [getattr(last, SORT_ATTRS[name]) for name, _ in keys],
                }
            )
        pagination = {
            "strategy": "cursor",
            "limit": limit,
            "next_cursor": next_cursor,
            "has_more": has_more,
        }

    return jsonify({"data": [b.to_dict() for b in rows], "pagination": pagination})
