from app.models import db, Client, Product, Order
from datetime import datetime

def calculate_total_cost(product_price, quantity):
    return product_price * quantity

from datetime import datetime, timezone, timedelta

EAT = timezone(timedelta(hours=3))

def create_order(data):
    product = Product.query.get(data['productId'])
    if not product:
        raise ValueError("Product not found")

    total_cost = calculate_total_cost(
        product.pricePerUnit,
        data['pagesOrSlides']
    )

    created_at = None
    if data.get("orderDate"):
        # Parse EAT datetime
        eat_dt = datetime.fromisoformat(data["orderDate"])

        # If frontend didn't send tzinfo, assume EAT
        if eat_dt.tzinfo is None:
            eat_dt = eat_dt.replace(tzinfo=EAT)

        # Convert to UTC for storage
        created_at = eat_dt.astimezone(timezone.utc)

    order = Order(
        clientId=data['clientId'],
        productId=data['productId'],
        classId=data.get('orderClass'),
        genreId=data.get('genre'),
        week=data.get('week'),
        pagesOrSlides=data['pagesOrSlides'],
        totalCost=total_cost,
        description=data.get('description'),
        createdAt=created_at  # UTC
    )

    db.session.add(order)
    db.session.commit()
    return order

def generate_invoice(client_id, start_date, end_date):
    orders = Order.query.filter(
        Order.clientId == client_id,
        Order.createdAt >= start_date,
        Order.createdAt <= end_date
    ).all()
    
    total_amount = sum(order.totalCost for order in orders)
    client = Client.query.get(client_id)
    
    return {
        "client": client,
        "orders": orders,
        "totalAmount": total_amount,
        "startDate": start_date,
        "endDate": end_date
    }


import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def generate_invoice_excel(invoice_data):
    """Generate Excel file for invoice"""
    df = pd.DataFrame([{
        "Product": o.product.name,
        "Pages/Slides": o.pagesOrSlides,
        "Price Per Unit": o.product.pricePerUnit,
        "Total Cost": o.totalCost,
        "Week": o.week,
        "Genre": o.order_genre.name if o.order_genre else None,
        "Class": o.order_class.name if o.order_class else None,
        "Date": o.createdAt.strftime("%Y-%m-%d")
    } for o in invoice_data['orders']])

    
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Invoice')
        # Add summary row
        summary_df = pd.DataFrame([{"Total Amount": invoice_data['totalAmount']}])
        summary_df.to_excel(writer, index=False, sheet_name='Summary')
    output.seek(0)
    return output

def generate_invoice_pdf(invoice_data):
    """Generate PDF file for invoice"""
    output = BytesIO()
    c = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 50

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, f"Invoice for {invoice_data['client'].clientName}")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Institution: {invoice_data['client'].institution}")
    y -= 20
    c.drawString(50, y, f"Period: {invoice_data['startDate'].date()} - {invoice_data['endDate'].date()}")
    y -= 30

    # Table header
    headers = ["Order ID", "Product", "Pages/Slides", "Price/Unit", "Total Cost"]
    x_positions = [50, 150, 300, 400, 500]
    for i, h in enumerate(headers):
        c.drawString(x_positions[i], y, h)
    y -= 20

    # Table rows
    for o in invoice_data['orders']:
        values = [o.product.name, str(o.pagesOrSlides), f"{o.product.pricePerUnit:.2f}", f"{o.totalCost:.2f}"]
        for i, val in enumerate(values):
            c.drawString(x_positions[i], y, val)
        y -= 20
        if y < 50:  # new page if needed
            c.showPage()
            y = height - 50

    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Total Amount: {invoice_data['totalAmount']:.2f}")
    c.save()
    output.seek(0)
    return output
