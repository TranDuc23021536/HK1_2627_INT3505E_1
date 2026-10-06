"""Lab 2 - demo app dung errors.py"""
import logging

from flask import Flask, jsonify

from errors import ApiProblem, register_error_handlers

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = Flask(__name__)
app.json.sort_keys = False  # giu thu tu type/title/status/... cho de doc
register_error_handlers(app)

# Du lieu gia lap thay cho User.query.get(id)
USERS = {1: {"id": 1, "name": "An"}, 2: {"id": 2, "name": "Binh"}}


@app.get("/users/<int:id>")
def get_user(id):
    user = USERS.get(id)
    if not user:
        raise ApiProblem(
            status=404,
            title="User not found",
            detail=f"No user with id {id}.",
            type_path="user-not-found",
            resource_id=id,
        )
    return jsonify(user)


@app.get("/resources/<int:id>")
def get_resource(id):
    raise ApiProblem(
        404,
        "Resource not found",
        detail=f"Resource {id} does not exist.",
        type_path="resource-not-found",
        resource_id=id,
    )


@app.get("/test-500")
def test_500():
    raise RuntimeError("secret DB password leaked?")  # khong duoc lo ra client


if __name__ == "__main__":
    app.run(port=5000, debug=False)