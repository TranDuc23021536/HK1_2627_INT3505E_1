from marshmallow import Schema, fields, validate


class ProductOut(Schema):
    id = fields.Int()
    sku = fields.Str()
    name = fields.Str()
    description = fields.Str(allow_none=True)
    price_cents = fields.Int()
    qty_in_stock = fields.Int()
    archived = fields.Bool()


class ProductIn(Schema):
    sku = fields.Str(required=True, validate=validate.Length(min=3, max=32))
    name = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(required=True, validate=validate.Range(min=0))
    qty_in_stock = fields.Int(load_default=0, validate=validate.Range(min=0))


class ProductPatch(Schema):
    name = fields.Str(validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True, validate=validate.Length(max=2000))
    price_cents = fields.Int(validate=validate.Range(min=0))
    qty_in_stock = fields.Int(validate=validate.Range(min=0))


class ReserveIn(Schema):
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderItemIn(Schema):
    product_id = fields.Int(required=True, validate=validate.Range(min=1))
    qty = fields.Int(required=True, validate=validate.Range(min=1))


class OrderIn(Schema):
    customer = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    items = fields.List(
        fields.Nested(OrderItemIn),
        required=True,
        validate=validate.Length(min=1),
    )


class OrderItemOut(Schema):
    id = fields.Int()
    product_id = fields.Int()
    sku = fields.Str(attribute="product.sku")
    name = fields.Str(attribute="product.name")
    qty = fields.Int()
    unit_price_cents = fields.Int()
    line_total_cents = fields.Function(lambda item: item.qty * item.unit_price_cents)


class OrderOut(Schema):
    id = fields.Int()
    customer = fields.Str()
    status = fields.Str()
    created_at = fields.DateTime()
    items = fields.List(fields.Nested(OrderItemOut))
    total_cents = fields.Int()
