from flask import Flask, jsonify, request, make_response

app = Flask(__name__)
BOOKS = []
_next_id = 1

DEFAULT_SIZE, MAX_SIZE = 20, 100

@app.post("/books")
def create_book():
    global _next_id
    if not request.is_json:
        return jsonify(error="expected JSON"), 415
    p = request.get_json(silent=True) or {}
    t = (p.get("title") or "").strip()
    a = (p.get("author") or "").strip()
    if not t or not a:
        return jsonify(error="title and author required"), 422
    book = {"id": _next_id, "title": t, "author": a}
    BOOKS.append(book); _next_id += 1
    resp = make_response(jsonify(book), 201)
    resp.headers["Location"] = f"/books/{book['id']}"
    return resp

@app.get("/books")
def list_books():
    try:
        page = int(request.args.get("page", 1))
        size = int(request.args.get("size", DEFAULT_SIZE))
    except ValueError:
        return jsonify(error="page and size must be int"), 400
    page = max(page, 1); size = max(min(size, MAX_SIZE), 1)
    flt = BOOKS
    a = request.args.get("author")
    if a: flt = [b for b in flt if b["author"].lower() == a.lower()]
    q = (request.args.get("q") or "").lower()
    if q: flt = [b for b in flt if q in b["title"].lower()]
    total = len(flt); start = (page - 1) * size; end = start + size
    items = flt[start:end]; last = (total + size - 1) // size
    def u(p): return f"/books?page={p}&size={size}"
    links = {"self": {"href": u(page)},
             "first": {"href": u(1)},
             "last": {"href": u(max(last, 1))}}
    if page > 1: links["prev"] = {"href": u(page - 1)}
    if end < total: links["next"] = {"href": u(page + 1)}
    body = {"data": items,
            "pagination": {"page": page, "size": size, "total": total, "total_pages": last},
            "_links": links}
    resp = make_response(jsonify(body), 200)
    resp.headers["Cache-Control"] = "public, max-age=30"
    return resp

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)