from flask import Blueprint, request, jsonify
from app.models import db, Client

clients_bp = Blueprint("clients", __name__, url_prefix="/api/v1/clients")

def client_to_dict(client: Client):
    return {
        "id": client.id,
        "clientName": client.clientName,
        "institution": client.institution,
        "phone": client.phone,
        "email": client.email,
        "createdAt": client.createdAt.isoformat() if client.createdAt else None,
        "updatedAt": client.updatedAt.isoformat() if client.updatedAt else None,
    }


@clients_bp.route("", methods=["GET"])
def get_clients():
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    search = request.args.get("search", "")
    start_date_str = request.args.get("start_date")
    end_date_str = request.args.get("end_date")

    query = Client.query

    if search:
        query = query.filter(Client.clientName.ilike(f"%{search}%"))

    from datetime import datetime
    if start_date_str:
        try:
            start_date = datetime.fromisoformat(start_date_str)
            query = query.filter(Client.createdAt >= start_date)
        except ValueError:
            pass

    if end_date_str:
        try:
            end_date = datetime.fromisoformat(end_date_str)
            query = query.filter(Client.createdAt <= end_date)
        except ValueError:
            pass

    clients = query.paginate(page=page, per_page=page_size, error_out=False)

    return jsonify({
        "data": [client_to_dict(c) for c in clients.items],
        "total": clients.total,
        "page": page,
        "page_size": page_size,
        "totalPages": clients.pages
    })



@clients_bp.route("", methods=["POST"])
def create_client():
    data = request.json
    client = Client(**data)
    db.session.add(client)
    db.session.commit()
    return jsonify(client_to_dict(client)), 201

@clients_bp.route("/<client_id>", methods=["PUT", "PATCH"])
def update_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    data = request.json

    # Update allowed fields
    client.clientName = data.get("clientName", client.clientName)
    client.institution = data.get("institution", client.institution)
    client.phone = data.get("phone", client.phone)
    client.email = data.get("email", client.email)

    db.session.commit()

    return jsonify(client_to_dict(client))

@clients_bp.route("/<client_id>", methods=["DELETE"])
def delete_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({"error": "Client not found"}), 404

    db.session.delete(client)
    db.session.commit()
    return '', 204
