from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
import uuid

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    clientName = db.Column(db.String, nullable=False)
    institution = db.Column(db.String, nullable=True)
    phone = db.Column(db.String, nullable=True)
    email = db.Column(db.String, nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = db.relationship("Order", back_populates="client", lazy=True)


class Product(db.Model):
    __tablename__ = "products"
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    name = db.Column(db.String, nullable=False)
    pricePerUnit = db.Column(db.Float, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    orders = db.relationship("Order", back_populates="product", lazy=True)


class Order(db.Model):
    __tablename__ = "orders"
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    clientId = db.Column(db.String, db.ForeignKey('clients.id'), nullable=False)
    productId = db.Column(db.String, db.ForeignKey('products.id'), nullable=False)
    classId = db.Column(db.String, db.ForeignKey('classes.id'), nullable=True)
    genreId = db.Column(db.String, db.ForeignKey('genres.id'), nullable=True)
    description = db.Column(db.String, nullable=True)
    week = db.Column(db.String, nullable=True)
    pagesOrSlides = db.Column(db.Integer, nullable=False)
    totalCost = db.Column(db.Float, nullable=False)
    createdAt = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    updatedAt = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    order_class = db.relationship("Class", backref="orders")
    order_genre = db.relationship("Genre", backref="orders")
    
    client = db.relationship("Client", back_populates="orders", lazy=True)
    product = db.relationship("Product", back_populates="orders", lazy=True)


class Class(db.Model):
    __tablename__ = "classes"
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    name = db.Column(db.String, unique=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Genre(db.Model):
    __tablename__ = "genres"
    id = db.Column(db.String, primary_key=True, default=generate_uuid)
    name = db.Column(db.String, unique=True, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    updatedAt = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
