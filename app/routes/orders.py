from flask import Blueprint, request, jsonify
from app.models import db, Order, Class, Genre, Client, Product
from app.services import create_order

from flask import Blueprint, request, jsonify
from app.models import db, Order
from sqlalchemy import desc

orders_bp = Blueprint("orders", __name__, url_prefix="/api/v1/orders")


from datetime import timezone, timedelta

EAT = timezone(timedelta(hours=3))

def to_eat(dt):
    if not dt:
        return None

    # DB returned naive datetime → treat as UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(EAT).isoformat()

def order_to_dict(order: Order):
    return {
        "id": order.id,
        "totalCost": order.totalCost,
        "pagesOrSlides": order.pagesOrSlides,
        "description": order.description,
        "week": order.week,
        "createdAt": to_eat(order.createdAt),
        "client": {
            "id": order.client.id,
            "clientName": order.client.clientName
        } if order.client else None,
        "product": {
            "id": order.product.id,
            "name": order.product.name,
            "pricePerUnit": order.product.pricePerUnit,
        } if order.product else None,
    }


@orders_bp.route("", methods=["POST"])
def add_order():
    data = request.json
    order = create_order(data)
    return jsonify(order_to_dict(order)), 201

from datetime import datetime
from sqlalchemy import or_, desc

@orders_bp.route("", methods=["GET"])
def get_orders():
    # Pagination
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("pageSize", request.args.get("page_size", 20)))

    # Filters
    search = request.args.get("search")
    client_id = request.args.get("clientId")
    product_id = request.args.get("productId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    sort = request.args.get("sort", "-createdAt")

    query = Order.query

    # ---- Date filtering ----
    if start_date:
        eat_start = datetime.fromisoformat(start_date)
        if eat_start.tzinfo is None:
            eat_start = eat_start.replace(tzinfo=EAT)
        query = query.filter(
            Order.createdAt >= eat_start.astimezone(timezone.utc)
        )

    if end_date:
        eat_end = datetime.fromisoformat(end_date)
        if eat_end.tzinfo is None:
            eat_end = eat_end.replace(tzinfo=EAT)
        query = query.filter(
            Order.createdAt <= eat_end.astimezone(timezone.utc)
        )


    # ---- Client filtering ----
    if client_id:
        query = query.filter(Order.clientId == client_id)

    # ---- Product filtering ----
    if product_id:
        query = query.filter(Order.productId == product_id)

    # ---- Search filtering ----
    if search:
        query = query.filter(
            or_(
                Order.order_class.has(Class.name.ilike(f"%{search}%")),
                Order.order_genre.has(Genre.name.ilike(f"%{search}%")),
                Order.client.has(Client.clientName.ilike(f"%{search}%")),
                Order.product.has(Product.name.ilike(f"%{search}%")),
                Order.product.has(Client.institution.ilike(f"%{search}%")),
            )
        )


    # ---- Sorting ----
    if sort.startswith("-"):
        sort_col = getattr(Order, sort[1:], Order.createdAt)
        query = query.order_by(desc(sort_col))
    else:
        sort_col = getattr(Order, sort, Order.createdAt)
        query = query.order_by(sort_col)

    # ---- Pagination ----
    pagination = query.paginate(
        page=page,
        per_page=page_size,
        error_out=False
    )

    return jsonify({
        "data": [order_to_dict(o) for o in pagination.items],
        "total": pagination.total,
        "page": page,
        "page_size": page_size,
        "totalPages": pagination.pages
    }), 200


@orders_bp.route("/summary", methods=["GET"])
def orders_summary():
    total_orders = Order.query.count()
    total_revenue = db.session.query(db.func.sum(Order.totalCost)).scalar() or 0
    return jsonify({
        "totalOrders": total_orders,
        "totalRevenue": total_revenue
    })


@orders_bp.route("/<order_id>", methods=["PUT"])
def update_order(order_id):
    """
    Update an order's editable fields:
    week, clientId, productId, classId, genreId, pagesOrSlides, description
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    data = request.json

    # Update editable fields if present in payload
    if "week" in data:
        order.week = data["week"]
    if "clientId" in data:
        order.clientId = data["clientId"]
    if "productId" in data:
        order.productId = data["productId"]
    if "classId" in data:  # now using foreign key
        order.classId = data["classId"]
    if "genreId" in data:  # now using foreign key
        order.genreId = data["genreId"]
    if "pagesOrSlides" in data:
        order.pagesOrSlides = data["pagesOrSlides"]
    if "description" in data:
        order.description = data["description"]
    if "orderDate" in data:
        eat_dt = datetime.fromisoformat(data["orderDate"])
        if eat_dt.tzinfo is None:
            eat_dt = eat_dt.replace(tzinfo=EAT)

        order.createdAt = eat_dt.astimezone(timezone.utc)

    # Recalculate totalCost if product or pages changed
    if order.product:
        order.totalCost = order.product.pricePerUnit * order.pagesOrSlides

    db.session.commit()

    return jsonify(order_to_dict(order)), 200

@orders_bp.route("/<order_id>", methods=["DELETE"])
def delete_order(order_id):
    """
    Delete an order by its ID
    """
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    db.session.delete(order)
    db.session.commit()

    return jsonify({"message": f"Order {order_id} deleted successfully"}), 200
