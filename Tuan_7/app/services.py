from sqlalchemy import update

from .errors import NotFound, OutOfStock
from .extensions import db
from .models import Product


def get_active_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None or product.archived:
        raise NotFound(f"product {product_id} not found")
    return product


def reserve_stock(product, qty):
    result = db.session.execute(
        update(Product)
        .where(
            Product.id == product.id,
            Product.archived.is_(False),
            Product.qty_in_stock >= qty,
        )
        .values(qty_in_stock=Product.qty_in_stock - qty)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        db.session.refresh(product)
        raise OutOfStock(f"only {product.qty_in_stock} left for sku {product.sku}")
    db.session.refresh(product)
