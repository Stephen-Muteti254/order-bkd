from flask import Blueprint, request, jsonify
from sqlalchemy import text
from app.models import db

users_bp = Blueprint("users", __name__, url_prefix="/api/v1/users")

@users_bp.route("/change-password", methods=["POST"])
def change_password():
    data = request.get_json()

    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    if not current_password or not new_password:
        return jsonify({
            "success": False,
            "message": "Missing fields"
        }), 400

    # Fetch the single user
    result = db.session.execute(
        text("SELECT password FROM users LIMIT 1")
    ).mappings().first()

    if not result:
        return jsonify({
            "success": False,
            "message": "User not found"
        }), 404

    if result["password"] != current_password:
        return jsonify({
            "success": False,
            "message": "Current password is incorrect"
        }), 400

    # Update password
    db.session.execute(
        text("""
            UPDATE users
            SET password = :new_password, updated_at = NOW()
        """),
        {"new_password": new_password}
    )

    db.session.commit()

    return jsonify({
        "success": True,
        "message": "Password updated successfully"
    })


from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import text
import datetime
from app.models import db

@users_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({
            "success": False,
            "message": "Email and password are required"
        }), 400

    user = db.session.execute(
        text("""
            SELECT id, name, email, password
            FROM users
            WHERE email = :email
        """),
        {"email": email}
    ).mappings().first()

    if not user or user["password"] != password:
        return jsonify({
            "success": False,
            "message": "Invalid email or password"
        }), 401

    return jsonify({
        "success": True,
        "access_token": "token123",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"]
        }
    })
