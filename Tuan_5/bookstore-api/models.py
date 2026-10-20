from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

book_authors = db.Table(
    "book_authors",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id"), primary_key=True),
    db.Column("author_id", db.Integer, db.ForeignKey("authors.id"), primary_key=True),
)


class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)


class Author(db.Model):
    __tablename__ = "authors"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text)


class Book(db.Model):
    __tablename__ = "books"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    isbn = db.Column(db.String(13), unique=True)
    price_vnd = db.Column(db.Integer, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))

    category = db.relationship("Category")
    authors = db.relationship("Author", secondary=book_authors)

    def to_dict(self):
        return {
            "id": f"book_{self.id}",
            "title": self.title,
            "isbn": self.isbn,
            "price": {"amount": self.price_vnd, "currency": "VND"},
            "stock": self.stock,
            "category": (
                {"id": self.category.id, "slug": self.category.slug}
                if self.category
                else None
            ),
            "authors": [{"id": a.id, "name": a.name} for a in self.authors],
        }
