from flask import Blueprint, jsonify, request
from sqlalchemy.exc import IntegrityError

from .errors import Conflict
from .extensions import db
from .models import Product
from .pagination import parse_pagination
from .schemas import ProductIn, ProductOut, ProductPatch, ReserveIn
from .services import get_active_product, reserve_stock

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


@products_bp.get("")
def list_products():
    page, size = parse_pagination()
    active = Product.archived.is_(False)
    rows = (
        db.session.execute(
            db.select(Product)
            .where(active)
            .order_by(Product.id)
            .offset((page - 1) * size)
            .limit(size)
        )
        .scalars()
        .all()
    )
    total = db.session.scalar(
        db.select(db.func.count()).select_from(Product).where(active)
    )
    return (
        jsonify(
            {
                "items": ProductOut(many=True).dump(rows),
                "page": page,
                "size": size,
                "total": total,
            }
        ),
        200,
    )


@products_bp.get("/<int:product_id>")
def get_product(product_id):
    return ProductOut().dump(get_active_product(product_id)), 200


@products_bp.post("")
def create_product():
    body = ProductIn().load(request.get_json())
    product = Product(**body)
    db.session.add(product)
    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        raise Conflict("sku already exists")
    return ProductOut().dump(product), 201


@products_bp.post("/<int:product_id>/reserve")
def reserve_product(product_id):
    body = ReserveIn().load(request.get_json())
    product = get_active_product(product_id)
    reserve_stock(product, body["qty"])
    db.session.commit()
    return ProductOut().dump(product), 200


@products_bp.patch("/<int:product_id>")
def patch_product(product_id):
    body = ProductPatch().load(request.get_json(), partial=True)
    product = get_active_product(product_id)
    for key, value in body.items():
        setattr(product, key, value)
    db.session.commit()
    return ProductOut().dump(product), 200


@products_bp.delete("/<int:product_id>")
def delete_product(product_id):
    product = get_active_product(product_id)
    product.archived = True
    db.session.commit()
    return "", 204
