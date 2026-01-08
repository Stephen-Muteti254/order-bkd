from flask import Blueprint, request, jsonify
from app.models import db, Class, Genre

meta_bp = Blueprint("meta", __name__, url_prefix="/api/v1/meta")

# --- Classes ---
@meta_bp.route("/classes", methods=["GET"])
def get_classes():
    return jsonify([{"id": c.id, "name": c.name} for c in Class.query.all()])

@meta_bp.route("/classes", methods=["POST"])
def add_class():
    data = request.json
    new_class = Class(name=data["name"])
    db.session.add(new_class)
    db.session.commit()
    return jsonify({"id": new_class.id, "name": new_class.name}), 201

# --- Genres ---
@meta_bp.route("/genres", methods=["GET"])
def get_genres():
    return jsonify([{"id": g.id, "name": g.name} for g in Genre.query.all()])

@meta_bp.route("/genres", methods=["POST"])
def add_genre():
    data = request.json
    new_genre = Genre(name=data["name"])
    db.session.add(new_genre)
    db.session.commit()
    return jsonify({"id": new_genre.id, "name": new_genre.name}), 201

classes_bp = Blueprint("classes", __name__, url_prefix="/api/v1/classes")


@classes_bp.route("", methods=["GET"])
def list_classes():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    search = request.args.get("search")

    query = Class.query

    if search:
        query = query.filter(Class.name.ilike(f"%{search}%"))

    total = query.count()

    classes = (
        query
        .order_by(Class.name.asc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return jsonify({
        "data": [{"id": c.id, "name": c.name} for c in classes],
        "total": total,
        "page": page,
        "page_size": page_size
    })
