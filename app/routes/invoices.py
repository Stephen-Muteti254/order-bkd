from flask import Blueprint, request, jsonify
from app.services import generate_invoice
from datetime import datetime

invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/v1/invoices")

@invoices_bp.route("/data", methods=["GET"])
def get_invoice_data():
    client_id = request.args.get("clientId")
    start_date = request.args.get("startDate")
    end_date = request.args.get("endDate")
    
    start_date = datetime.fromisoformat(start_date)
    end_date = datetime.fromisoformat(request.args.get("endDate")).replace(hour=23, minute=59, second=59)    
    invoice = generate_invoice(client_id, start_date, end_date)
    return jsonify(invoice)

from flask import Blueprint, request, jsonify, send_file
from app.services import generate_invoice, generate_invoice_excel, generate_invoice_pdf
from datetime import datetime

invoices_bp = Blueprint("invoices", __name__, url_prefix="/api/v1/invoices")

@invoices_bp.route("/data", methods=["GET"])
def get_invoice_data():
    client_id = request.args.get("clientId")
    start_date = datetime.fromisoformat(request.args.get("startDate"))
    end_date = datetime.fromisoformat(request.args.get("endDate")).replace(hour=23, minute=59, second=59)
    invoice = generate_invoice(client_id, start_date, end_date)
    return jsonify(invoice)

@invoices_bp.route("/download/excel", methods=["GET"])
def download_invoice_excel():
    client_id = request.args.get("clientId")
    start_date = datetime.fromisoformat(request.args.get("startDate"))
    end_date = datetime.fromisoformat(request.args.get("endDate")).replace(hour=23, minute=59, second=59)

    invoice = generate_invoice(client_id, start_date, end_date)
    excel_file = generate_invoice_excel(invoice)
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        download_name=f"invoice_{client_id}_{start_date.date()}_{end_date.date()}.xlsx",
        as_attachment=True
    )

@invoices_bp.route("/download/pdf", methods=["GET"])
def download_invoice_pdf():
    client_id = request.args.get("clientId")
    start_date = datetime.fromisoformat(request.args.get("startDate"))
    end_date = datetime.fromisoformat(request.args.get("endDate")).replace(hour=23, minute=59, second=59)
    invoice = generate_invoice(client_id, start_date, end_date)
    pdf_file = generate_invoice_pdf(invoice)
    return send_file(
        pdf_file,
        mimetype='application/pdf',
        download_name=f"invoice_{client_id}_{start_date.date()}_{end_date.date()}.pdf",
        as_attachment=True
    )
