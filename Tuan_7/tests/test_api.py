from sqlalchemy import event, text

from app.extensions import db
from app.models import Product


def make_product(client, sku="SKU-001", **overrides):
    payload = {"sku": sku, "name": "Mouse", "price_cents": 250000, "qty_in_stock": 5}
    payload.update(overrides)
    return client.post("/api/v1/products", json=payload)


def make_order(client, items, customer="An"):
    return client.post("/api/v1/orders", json={"customer": customer, "items": items})


def run_counting_queries(call):
    statements = []

    def on_execute(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(db.engine, "before_cursor_execute", on_execute)
    try:
        response = call()
    finally:
        event.remove(db.engine, "before_cursor_execute", on_execute)
    return response, statements


def test_create_product_returns_201(client):
    response = make_product(client)
    assert response.status_code == 201
    body = response.get_json()
    assert body["sku"] == "SKU-001"
    assert body["qty_in_stock"] == 5
    assert body["archived"] is False


def test_create_product_duplicate_sku_returns_409(client):
    make_product(client)
    response = make_product(client)
    assert response.status_code == 409
    assert response.get_json()["error"] == "conflict"


def test_create_product_invalid_body_returns_422(client):
    response = make_product(client, sku="ab", price_cents=-1)
    assert response.status_code == 422
    detail = response.get_json()["detail"]
    assert "sku" in detail
    assert "price_cents" in detail


def test_create_product_malformed_json_returns_400(client):
    response = client.post(
        "/api/v1/products", data="{bad", content_type="application/json"
    )
    assert response.status_code == 400
    assert response.get_json()["error"] == "bad_request"


def test_get_product_returns_200_and_404(client):
    product_id = make_product(client).get_json()["id"]
    assert client.get(f"/api/v1/products/{product_id}").status_code == 200
    missing = client.get("/api/v1/products/9999")
    assert missing.status_code == 404
    assert missing.get_json()["error"] == "not_found"


def test_list_products_is_paginated(client):
    for index in range(3):
        make_product(client, sku=f"SKU-00{index}")
    first = client.get("/api/v1/products?page=1&size=2").get_json()
    second = client.get("/api/v1/products?page=2&size=2").get_json()
    assert len(first["items"]) == 2
    assert len(second["items"]) == 1
    assert first["total"] == 3
    assert first["page"] == 1
    assert first["size"] == 2


def test_list_products_rejects_non_integer_page(client):
    assert client.get("/api/v1/products?page=abc").status_code == 422


def test_reserve_decrements_stock_and_blocks_oversell(client):
    product_id = make_product(client).get_json()["id"]
    ok = client.post(f"/api/v1/products/{product_id}/reserve", json={"qty": 3})
    assert ok.status_code == 200
    assert ok.get_json()["qty_in_stock"] == 2
    over = client.post(f"/api/v1/products/{product_id}/reserve", json={"qty": 3})
    assert over.status_code == 409
    assert over.get_json()["error"] == "out_of_stock"
    assert client.get(f"/api/v1/products/{product_id}").get_json()["qty_in_stock"] == 2


def test_reserve_invalid_qty_returns_422(client):
    product_id = make_product(client).get_json()["id"]
    response = client.post(f"/api/v1/products/{product_id}/reserve", json={"qty": 0})
    assert response.status_code == 422


def test_patch_changes_only_given_fields(client):
    product_id = make_product(client).get_json()["id"]
    response = client.patch(f"/api/v1/products/{product_id}", json={"price_cents": 1})
    body = response.get_json()
    assert response.status_code == 200
    assert body["price_cents"] == 1
    assert body["name"] == "Mouse"
    assert body["qty_in_stock"] == 5


def test_delete_is_soft_delete(client):
    product_id = make_product(client).get_json()["id"]
    assert client.delete(f"/api/v1/products/{product_id}").status_code == 204
    assert client.get(f"/api/v1/products/{product_id}").status_code == 404
    assert client.get("/api/v1/products").get_json()["total"] == 0
    assert db.session.get(Product, product_id).archived is True


def test_create_order_with_items_returns_201(client):
    mouse = make_product(client, sku="MOUSE-1", price_cents=100).get_json()["id"]
    keyboard = make_product(client, sku="KEYB-1", price_cents=300).get_json()["id"]
    response = make_order(
        client,
        [{"product_id": mouse, "qty": 2}, {"product_id": keyboard, "qty": 1}],
    )
    body = response.get_json()
    assert response.status_code == 201
    assert len(body["items"]) == 2
    assert body["total_cents"] == 500
    assert body["items"][0]["sku"] == "MOUSE-1"
    assert client.get(f"/api/v1/products/{mouse}").get_json()["qty_in_stock"] == 3


def test_create_order_out_of_stock_rolls_back_everything(client):
    ok = make_product(client, sku="OK-1").get_json()["id"]
    short = make_product(client, sku="SHORT-1", qty_in_stock=1).get_json()["id"]
    response = make_order(
        client,
        [{"product_id": ok, "qty": 1}, {"product_id": short, "qty": 9}],
    )
    assert response.status_code == 409
    assert response.get_json()["error"] == "out_of_stock"
    assert client.get(f"/api/v1/products/{ok}").get_json()["qty_in_stock"] == 5
    assert client.get("/api/v1/orders").get_json()["total"] == 0


def test_create_order_unknown_product_returns_422(client):
    response = make_order(client, [{"product_id": 9999, "qty": 1}])
    assert response.status_code == 422


def test_create_order_requires_items(client):
    response = client.post("/api/v1/orders", json={"customer": "An", "items": []})
    assert response.status_code == 422


def test_add_item_to_existing_order(client):
    first = make_product(client, sku="A-1").get_json()["id"]
    second = make_product(client, sku="B-1").get_json()["id"]
    order_id = make_order(client, [{"product_id": first, "qty": 1}]).get_json()["id"]
    response = client.post(
        f"/api/v1/orders/{order_id}/items", json={"product_id": second, "qty": 2}
    )
    assert response.status_code == 201
    assert len(response.get_json()["items"]) == 2


def test_add_same_product_merges_quantity(client):
    product = make_product(client, sku="A-1").get_json()["id"]
    order_id = make_order(client, [{"product_id": product, "qty": 1}]).get_json()["id"]
    response = client.post(
        f"/api/v1/orders/{order_id}/items", json={"product_id": product, "qty": 2}
    )
    items = response.get_json()["items"]
    assert len(items) == 1
    assert items[0]["qty"] == 3


def test_get_order_404(client):
    assert client.get("/api/v1/orders/9999").status_code == 404


def test_list_orders_has_no_n_plus_1(app, client):
    product_ids = [
        make_product(client, sku=f"P-{n}", qty_in_stock=100).get_json()["id"]
        for n in range(4)
    ]
    items = [{"product_id": pid, "qty": 1} for pid in product_ids[:3]]

    for _ in range(2):
        make_order(client, items)
    small, small_statements = run_counting_queries(
        lambda: client.get("/api/v1/orders?size=100")
    )

    for _ in range(6):
        make_order(client, items)
    large, large_statements = run_counting_queries(
        lambda: client.get("/api/v1/orders?size=100")
    )

    print(
        f"\nGET /orders: {len(small_statements)} queries with 2 orders, "
        f"{len(large_statements)} queries with 8 orders"
    )
    assert small.get_json()["total"] == 2
    assert large.get_json()["total"] == 8
    assert len(large_statements) == len(small_statements)
    assert len(large_statements) <= 4


def test_healthz_returns_200(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_ready_returns_200_when_db_ok(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["checks"]["db"] == "ok"


def test_ready_returns_503_when_db_fails_but_healthz_stays_200(client, monkeypatch):
    monkeypatch.setattr(
        "app.health.text", lambda _sql: text("SELECT * FROM table_does_not_exist")
    )
    ready = client.get("/ready")
    assert ready.status_code == 503
    assert ready.get_json()["status"] == "degraded"
    assert client.get("/healthz").status_code == 200
