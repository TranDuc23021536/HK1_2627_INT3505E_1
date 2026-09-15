from flask import Flask, jsonify, request
from uuid import uuid4

app = Flask(__name__)

STUDENTS = []

BOOKS = [
    {"id": "book-1", "t": "Tran Manh Duc"},
    {"id": "book-2", "t": "Kien truc huong dich vu"},
]

ORDERS = {
    "ord_1": {"status": "pending"},
    "ord_2": {"status": "shipped"},
    "ord_3": {"status": "delivered"},
}


def find_by_id(book_id):
    return next((b for b in BOOKS if b["id"] == book_id), None)


@app.route("/students", methods=["POST"])
def create_student():
    body = request.get_json(silent=True) or {}
    name = body.get("name")

    if not name:
        return jsonify({"error": "name là bắt buộc"}), 400

    student = {
        "id": str(uuid4()),
        "name": name,
        "gpa": body.get("gpa", 0.0),
    }

    STUDENTS.append(student)

    return {
        "id": student["id"],
        "name": student["name"]
    }, 201


@app.route("/books/<book_id>", methods=["GET"])
def get_book(book_id):
    book = find_by_id(book_id)
    if book is None:
        return jsonify({"error": "not found"}), 404
    return jsonify(book), 200


@app.route("/items/<int:item_id>")
def get_item(item_id):
    return jsonify({"id": item_id}), 200

@app.route("/books", methods=["GET"])
def list_books():
    limit = int(request.args.get("limit", 20))
    q = request.args.get("q", "").strip().lower()
    items = [b for b in BOOKS if q in b["t"].lower()]
    return jsonify({"items": items}), 200

@app.route("/orders/<id>", methods=["DELETE"])
def delete_order(id):
    order = ORDERS.get(id)

    if order is None:
        return {"error": "not found"}, 404

    if order["status"] in ("shipped", "delivered"):
        return {"error": "cannot delete"}, 409

    ORDERS.pop(id, None)

    return "", 204


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)