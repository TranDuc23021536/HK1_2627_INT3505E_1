from sqlalchemy import func, select

from app import create_app
from models import Author, Book, Category, db


def seed(n_books=50):
    """Tạo dữ liệu mẫu. Giá cố tình bị trùng để test tie-break của cursor."""
    cats = [Category(name=s.title(), slug=s) for s in ("tech", "novel", "science")]
    authors = [Author(name=f"Author {i}", bio="Tiểu sử mẫu") for i in range(1, 6)]
    db.session.add_all(cats + authors)
    db.session.flush()

    prices = [100000, 150000, 200000, 250000]
    for i in range(1, n_books + 1):
        book = Book(
            title=f"Book {i:02d}",
            isbn=f"{9780000000000 + i}",
            price_vnd=prices[i % 4],
            stock=i % 7,
            category=cats[i % 3],
        )
        book.authors = [authors[i % 5]]
        if i % 2 == 0:
            book.authors.append(authors[(i + 1) % 5])
        db.session.add(book)
    db.session.commit()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        if db.session.scalar(select(func.count(Book.id))):
            print("DB đã có dữ liệu, bỏ qua.")
        else:
            seed(50)
            print("Đã tạo 50 sách mẫu.")
