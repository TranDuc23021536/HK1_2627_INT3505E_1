from flask import Flask, request, jsonify

app = Flask(__name__)

posts = [
    {
        "id": 1,
        "title": "Sinh vien",
        "body": "Ten Tran Manh Duc",
        "author_id": 1
    },
    {
        "id": 2,
        "title": "MSV",
        "body": "23021536",
        "author_id": 2
    }
]

@app.route("/api/v1/posts", methods=["GET"])
def get_posts():
    result = posts
    author_id = request.args.get("author_id")
    if author_id:
        result = [
            post for post in result
            if str(post["author_id"]) == author_id
        ]
    return jsonify(result), 200

@app.route("/api/v1/posts/<int:post_id>", methods=["GET"])
def get_post(post_id):
    for post in posts:
        if post["id"] == post_id:
            return jsonify(post), 200
    return jsonify({
        "error": "Post not found"
    }), 404

@app.route("/api/v1/posts", methods=["POST"])
def create_post():
    data = request.get_json()
    new_post = {
        "id": len(posts) + 1,
        "title": data["title"],
        "body": data["body"],
        "author_id": data["author_id"]
    }
    posts.append(new_post)
    return jsonify(new_post), 201

@app.route("/api/v1/posts/<int:post_id>", methods=["PATCH"])
def update_post(post_id):
    for post in posts:

        if post["id"] == post_id:
            data = request.get_json()
            if "title" in data:
                post["title"] = data["title"]
            if "body" in data:
                post["body"] = data["body"]
            return jsonify(post), 200
    return jsonify({
        "error": "Post not found"
    }), 404

@app.route("/api/v1/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    for post in posts:
        if post["id"] == post_id:
            posts.remove(post)
            return "", 204
    return jsonify({
        "error": "Post not found"
    }), 404

if __name__ == "__main__":
    app.run(debug=True)