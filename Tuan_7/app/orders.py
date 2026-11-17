from flask import Blueprint, jsonify, request
from sqlalchemy.orm import selectinload

from .errors import ApiError, NotFound, Unprocessable
from .extensions import db
from .models import Order, OrderItem, Product
from .pagination import parse_pagination
from .schemas import OrderIn, OrderItemIn, OrderOut
from .services import reserve_stock

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


def order_query():
    return db.select(Order).options(
        selectinload(Order.items).selectinload(OrderItem.product)
    )


def load_order(order_id):
    order = db.session.execute(
        order_query().where(Order.id == order_id)
    ).scalar_one_or_none()
    if order is None:
        raise NotFound(f"order {order_id} not found")
    return order


def add_item(order, product_id, qty):
    product = db.session.get(Product, product_id)
    if product is None or product.archived:
        raise Unprocessable(f"product {product_id} does not exist")
    reserve_stock(product, qty)
    existing = next((item for item in order.items if item.product_id == product.id), None)
    if existing is not None:
        existing.qty += qty
    else:
        order.items.append(
            OrderItem(product=product, qty=qty, unit_price_cents=product.price_cents)
        )


@orders_bp.post("")
def create_order():
    body = OrderIn().load(request.get_json())
    order = Order(customer=body["customer"])
    db.session.add(order)
    try:
        for item in body["items"]:
            add_item(order, item["product_id"], item["qty"])
        db.session.commit()
    except ApiError:
        db.session.rollback()
        raise
    return OrderOut().dump(load_order(order.id)), 201


@orders_bp.get("")
def list_orders():
    page, size = parse_pagination()
    rows = (
        db.session.execute(
            order_query().order_by(Order.id).offset((page - 1) * size).limit(size)
        )
        .scalars()
        .all()
    )
    total = db.session.scalar(db.select(db.func.count()).select_from(Order))
    return (
        jsonify(
            {
                "items": OrderOut(many=True).dump(rows),
                "page": page,
                "size": size,
                "total": total,
            }
        ),
        200,
    )


@orders_bp.get("/<int:order_id>")
def get_order(order_id):
    return OrderOut().dump(load_order(order_id)), 200


@orders_bp.post("/<int:order_id>/items")
def add_order_item(order_id):
    body = OrderItemIn().load(request.get_json())
    order = load_order(order_id)
    try:
        add_item(order, body["product_id"], body["qty"])
        db.session.commit()
    except ApiError:
        db.session.rollback()
        raise
    return OrderOut().dump(load_order(order_id)), 201
