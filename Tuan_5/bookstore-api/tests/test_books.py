import pytest

from app import create_app
from seed import seed

URL = "/api/v1/books"
TOTAL = 45


@pytest.fixture
def client():
    app = create_app("sqlite://")  # DB in-memory
    with app.app_context():
        seed(TOTAL)
    return app.test_client()


def get(client, **params):
    r = client.get(URL, query_string=params)
    return r.status_code, r.get_json()


def walk_cursor(client, **params):
    """Đi hết mọi trang bằng cursor, trả về list id."""
    ids, cursor = [], None
    for _ in range(100):
        q = dict(params)
        if cursor:
            q["cursor"] = cursor
        status, body = get(client, **q)
        assert status == 200
        ids += [b["id"] for b in body["data"]]
        if not body["pagination"]["has_more"]:
            return ids
        cursor = body["pagination"]["next_cursor"]
    pytest.fail("Vòng lặp phân trang không kết thúc")


def walk_offset(client, step, **params):
    ids, offset = [], 0
    for _ in range(100):
        status, body = get(client, strategy="offset", offset=offset, limit=step, **params)
        assert status == 200
        ids += [b["id"] for b in body["data"]]
        if not body["pagination"]["has_more"]:
            return ids
        offset += step
    pytest.fail("Vòng lặp phân trang không kết thúc")


def test_default_is_cursor_sorted_by_id_desc(client):
    status, body = get(client)
    assert status == 200
    nums = [int(b["id"].split("_")[1]) for b in body["data"]]
    assert len(nums) == 20
    assert nums == sorted(nums, reverse=True)
    assert body["pagination"]["strategy"] == "cursor"
    assert body["pagination"]["has_more"] is True
    assert body["pagination"]["next_cursor"]


def test_limit_is_capped_at_100(client):
    _, body = get(client, limit=1000)
    assert body["pagination"]["limit"] == 100


def test_cursor_walk_has_no_duplicates_or_gaps_with_tied_prices(client):
    _, full = get(client, sort="-price,title", limit=100)
    expected = [b["id"] for b in full["data"]]
    assert len(expected) == TOTAL

    ids = walk_cursor(client, sort="-price,title", limit=7)
    assert len(ids) == len(set(ids)) == TOTAL
    assert ids == expected


def test_multi_key_sort_order(client):
    _, body = get(client, sort="-price,title", limit=100)
    items = body["data"]
    for a, b in zip(items, items[1:]):
        pa, pb = a["price"]["amount"], b["price"]["amount"]
        assert pa >= pb
        if pa == pb:
            assert a["title"] <= b["title"]


def test_offset_strategy_returns_total_and_matches_cursor_order(client):
    _, body = get(client, strategy="offset", offset=10, limit=5)
    assert body["pagination"]["total"] == TOTAL
    assert body["pagination"]["offset"] == 10
    assert len(body["data"]) == 5

    expected = walk_cursor(client, sort="price,-title", limit=9)
    assert walk_offset(client, 8, sort="price,-title") == expected


def test_genre_filter_offset_and_cursor(client):
    _, body = get(client, strategy="offset", genre="tech", limit=100)
    assert body["pagination"]["total"] == TOTAL // 3
    assert all(b["category"]["slug"] == "tech" for b in body["data"])

    ids = walk_cursor(client, genre="tech", sort="price", limit=4)
    assert len(ids) == len(set(ids)) == TOTAL // 3


def test_unknown_genre_returns_empty_page(client):
    status, body = get(client, genre="khong-ton-tai")
    assert status == 200
    assert body["data"] == []
    assert body["pagination"]["has_more"] is False


@pytest.mark.parametrize(
    "params, code",
    [
        ({"sort": "foo"}, "bad_sort"),
        ({"sort": "-price,price"}, "bad_sort"),
        ({"strategy": "page"}, "bad_strategy"),
        ({"limit": "abc"}, "bad_param"),
        ({"strategy": "offset", "offset": -1}, "bad_param"),
        ({"cursor": "!!!khong-hop-le"}, "bad_cursor"),
    ],
)
def test_invalid_input_returns_400(client, params, code):
    status, body = get(client, **params)
    assert status == 400
    assert body["error"] == code


def test_cursor_cannot_be_reused_with_different_sort_or_genre(client):
    _, body = get(client, sort="price", limit=5)
    cursor = body["pagination"]["next_cursor"]

    status, err = get(client, sort="-price", cursor=cursor)
    assert status == 400 and err["error"] == "cursor_mismatch"

    status, err = get(client, sort="price", genre="tech", cursor=cursor)
    assert status == 400 and err["error"] == "cursor_mismatch"
