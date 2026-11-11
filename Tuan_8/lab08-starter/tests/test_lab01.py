import copy

import pytest
from jsonschema import validate, ValidationError

from tools import get_book_schema


def test_list_books_empty(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.get_json() == []


def test_get_missing_book(client):
    response = client.get("/books/9999")

    assert response.status_code == 404
    assert response.get_json()["code"] == "NOT_FOUND"


def test_create_book_missing_title(client):
    """C. POST /books with only author returns 400 and title error."""
    response = client.post(
        "/books",
        json={"author": "J.J. Geewax"}
    )

    assert response.status_code == 400

    data = response.get_json()
    assert "errors" in data
    assert any(
        error["field"] == "title"
        for error in data["errors"]
    )


def test_delete_book_then_get_returns_404(client):
    """D. Create a book, delete it, then GET the same ID."""
    create_response = client.post(
        "/books",
        json={
            "title": "Test Book",
            "author": "Test Author"
        }
    )

    assert create_response.status_code == 201

    book_id = create_response.get_json()["id"]

    delete_response = client.delete(f"/books/{book_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/books/{book_id}")
    assert get_response.status_code == 404


def test_response_extra_field_blocked(client):
    create_response = client.post(
        "/books",
        json={
            "title": "API Design Patterns",
            "author": "J.J. Geewax",
            "year": 2021
        }
    )

    assert create_response.status_code == 201

    book_data = create_response.get_json()
    schema = get_book_schema()
    
    validate(instance=book_data, schema=schema)

    invalid_book = copy.deepcopy(book_data)
    invalid_book["password_hash"] = "should-not-be-exposed"

    with pytest.raises(ValidationError):
        validate(instance=invalid_book, schema=schema)
