from flask import Flask, jsonify, request

app = Flask(__name__)

_next = 1

BOOKS = [
    {"id": 1, "title": "Clean Code", "author": "R. Martin", "year": 2008}
]


def find(bid):
    return next((b for b in BOOKS if b["id"] == bid), None)


@app.route("/books", methods=["GET"])
def list_books():
    n = int(request.args.get("limit", 100))
    q = request.args.get("q", "").strip().lower()
    sort = request.args.get("sort", "").strip().lower()
    items = BOOKS
    if q:
        items = [b for b in items if q in b["title"].lower()]
    if sort == "title":
        items = sorted(items, key=lambda b: b["title"].lower())
    return jsonify(items[:n]), 200

@app.route("/books/<int:bid>", methods=["GET"])
def get_book(bid):
    book = find(bid)
    if not book:
        return {"error": "not found"}, 404
    return jsonify(book), 200

@app.route("/books", methods=["POST"])
def create_book():
    global _next
    body = request.get_json(silent=True) or {}
    t = body.get("title")
    a = body.get("author")
    year = body.get("year")
    if not t or not a:
        return {"error": "need title+author"}, 400
    if not isinstance(year, int) or isinstance(year, bool) or year < 1900:
        return {"error": "year must be an integer >= 1900"}, 400
    book = {
        "id": _next,
        "title": t,
        "author": a,
        "year": year
    }
    _next += 1
    BOOKS.append(book)
    return jsonify(book), 201, {
        "Location": f"/books/{book['id']}"
    }


@app.route("/books/<int:bid>", methods=["PUT", "DELETE"])
def modify_book(bid):
    book = find(bid)
    if not book:
        return {"error": "not found"}, 404
    if request.method == "PUT":
        body = request.get_json(silent=True) or {}
        if "year" in body:
            year = body["year"]
            if not isinstance(year, int) or isinstance(year, bool) or year < 1900:
                return {"error": "year must be an integer >= 1900"}, 400
        book.update(body)
        return jsonify(book), 200
    BOOKS.remove(book)
    return "", 204

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
