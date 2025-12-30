from flask import Blueprint, request, jsonify
from sqlalchemy import or_, desc, asc
from datetime import datetime

from app.models import db, Product

products_bp = Blueprint("products", __name__, url_prefix="/api/v1/products")


# -------------------------
# GET /products
# List products with filters, pagination, sorting
# -------------------------
@products_bp.route("", methods=["GET"])
def get_products():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", 20))
    search = request.args.get("search")
    sort_by = request.args.get("sortBy", "createdAt")
    sort_order = request.args.get("sortOrder", "desc")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")

    query = Product.query

    # Search filter
    if search:
        query = query.filter(
            or_(
                Product.name.ilike(f"%{search}%")
            )
        )

    # Date filters
    if start_date:
        query = query.filter(Product.createdAt >= datetime.fromisoformat(start_date))
    if end_date:
        query = query.filter(Product.createdAt <= datetime.fromisoformat(end_date))

    # Sorting
    sort_column = getattr(Product, sort_by, Product.createdAt)
    query = query.order_by(desc(sort_column) if sort_order == "desc" else asc(sort_column))

    pagination = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        "data": [serialize_product(p) for p in pagination.items],
        "total": pagination.total,
        "page": page,
        "pageSize": page_size,
        "totalPages": pagination.pages
    })


# -------------------------
# GET /products/:id
# Get single product
# -------------------------
@products_bp.route("/<string:id>", methods=["GET"])
def get_product(id):
    product = Product.query.get_or_404(id)
    return jsonify(serialize_product(product))


# -------------------------
# POST /products
# Create product
# -------------------------
@products_bp.route("", methods=["POST"])
def create_product():
    data = request.json

    if not all(k in data for k in ("productId", "name", "pricePerUnit")):
        return error_response("VALIDATION_ERROR", "Missing required fields")

    product = Product(
        name=data["name"],
        pricePerUnit=float(data["pricePerUnit"])
    )

    db.session.add(product)
    db.session.commit()

    return jsonify(serialize_product(product)), 201


# -------------------------
# PUT /products/:id
# Update product
# -------------------------
@products_bp.route("/<string:id>", methods=["PUT"])
def update_product(id):
    product = Product.query.get_or_404(id)
    data = request.json

    product.name = data.get("name", product.name)
    product.pricePerUnit = data.get("pricePerUnit", product.pricePerUnit)

    db.session.commit()
    return jsonify(serialize_product(product))


# -------------------------
# DELETE /products/:id
# Delete product
# -------------------------
@products_bp.route("/<string:id>", methods=["DELETE"])
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200


# -------------------------
# Helpers
# -------------------------
def serialize_product(product):
    return {
        "id": product.id,
        "name": product.name,
        "pricePerUnit": product.pricePerUnit,
        "createdAt": product.createdAt.isoformat(),
        "updatedAt": product.updatedAt.isoformat()
    }


def error_response(code, message, details=None):
    return jsonify({
        "error": {
            "code": code,
            "message": message,
            "details": details or {}
        }
    }), 400
