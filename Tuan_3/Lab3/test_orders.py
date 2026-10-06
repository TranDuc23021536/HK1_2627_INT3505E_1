import pytest
from app import ORDERS, app

@pytest.fixture
def client():
    return app.test_client()

def test_default_limit_and_shape(client):
    body = client.get("/orders").get_json()
    assert len(body["data"]) == 20
    assert body["next_cursor"]

def test_limit_5(client):
    assert len(client.get("/orders?limit=5").get_json()["data"]) == 5

@pytest.mark.parametrize("limit", ["0", "101", "abc", "-1"])
def test_bad_limit_400(client, limit):
    r = client.get(f"/orders?limit={limit}")
    assert r.status_code == 400
    assert r.headers["Content-Type"].startswith("application/problem+json")

def test_filter_status(client):
    data = client.get("/orders?status=paid&limit=100").get_json()["data"]
    assert data and all(o["status"] == "paid" for o in data)

def test_filter_customer_and_status(client):
    data = client.get("/orders?status=paid&customer_id=3&limit=100").get_json()["data"]
    assert all(o["status"] == "paid" and o["customer_id"] == 3 for o in data)

def test_sparse_fields(client):
    data = client.get("/orders?fields=id,total").get_json()["data"]
    assert all(set(o) == {"id", "total"} for o in data)

def test_unknown_field_400(client):
    assert client.get("/orders?fields=id,password_hash").status_code == 400

def _walk(client, query):
    """Di het cac trang, tra ve list id."""
    ids, cursor = [], None
    while True:
        url = f"/orders?limit=7&{query}" + (f"&cursor={cursor}" if cursor else "")
        body = client.get(url).get_json()
        ids += [o["id"] for o in body["data"]]
        cursor = body["next_cursor"]
        if not cursor:
            return ids

def test_cursor_walk_no_dup_no_gap(client):
    ids = _walk(client, "sort=id")
    assert ids == sorted(o["id"] for o in ORDERS)

@pytest.mark.parametrize("sort", ["sort=-id", "sort=total", "sort=-total", "sort=-created_at"])
def test_cursor_walk_all_sorts(client, sort):
    ids = _walk(client, sort)
    assert len(ids) == len(set(ids)) == len(ORDERS)

def test_sort_order_total_desc(client):
    data = client.get("/orders?sort=-total&limit=50").get_json()["data"]
    totals = [o["total"] for o in data]
    assert totals == sorted(totals, reverse=True)

def test_walk_with_filter(client):
    ids = _walk(client, "status=shipped&sort=total")
    assert set(ids) == {o["id"] for o in ORDERS if o["status"] == "shipped"}

def test_broken_cursor_400(client):
    r = client.get("/orders?cursor=garbage!!")
    assert r.status_code == 400
    assert r.get_json()["type"].endswith("/invalid-cursor")

def test_cursor_sort_mismatch_400(client):
    cursor = client.get("/orders?sort=id&limit=5").get_json()["next_cursor"]
    assert client.get(f"/orders?sort=total&cursor={cursor}").status_code == 400

def test_invalid_sort_400(client):
    assert client.get("/orders?sort=password").status_code == 400