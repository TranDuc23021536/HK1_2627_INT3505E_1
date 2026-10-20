from flask import Flask

from models import db
from routes.books import bp as books_bp


def create_app(db_uri="sqlite:///bookstore.db"):
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = db_uri
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    db.init_app(app)
    app.register_blueprint(books_bp)
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    create_app().run(debug=True)
