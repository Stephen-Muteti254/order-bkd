from flask import Flask
from app.models import db
from app.config import Config
from app.routes.clients import clients_bp
from app.routes.products import products_bp
from app.routes.orders import orders_bp
from app.routes.invoices import invoices_bp
from app.routes.classes_genres import meta_bp
from app.routes.classes_genres import classes_bp
from app.routes.auth import users_bp
from app.routes.analytics import analytics_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    app.register_blueprint(clients_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(invoices_bp)
    app.register_blueprint(meta_bp)
    app.register_blueprint(classes_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(analytics_bp)

    return app
