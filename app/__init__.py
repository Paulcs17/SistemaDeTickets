import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Please sign in to continue."
login_manager.login_message_category = "warning"

ROLE_LABELS = {
    "admin": "Admin",
    "technician": "Technician",
    "requester": "Requester",
}

STATUS_LABELS = {
    "new": "New",
    "review": "Under Review",
    "assigned": "Assigned",
    "in_progress": "In Progress",
    "resolved": "Resolved",
    "closed": "Closed",
    "reopened": "Reopened",
}

PRIORITY_LABELS = {
    "low": "Low",
    "medium": "Medium",
    "high": "High",
    "critical": "Critical",
}


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    os.makedirs(app.instance_path, exist_ok=True)

    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)

    from .models import User, Ticket, TicketComment, TicketHistory
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.tickets import tickets_bp
    from .routes.admin import admin_bp
    from werkzeug.security import generate_password_hash

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @app.context_processor
    def inject_labels():
        return {
            "ROLE_LABELS": ROLE_LABELS,
            "STATUS_LABELS": STATUS_LABELS,
            "PRIORITY_LABELS": PRIORITY_LABELS,
        }

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp)

    @app.cli.command("init-db")
    def init_db():
        db.drop_all()
        db.create_all()
        print("Database created successfully.")

    @app.cli.command("seed-data")
    def seed_data():
        TicketComment.query.delete()
        TicketHistory.query.delete()
        Ticket.query.delete()
        User.query.delete()
        db.session.commit()

        admin = User(
            name="Maria Soto",
            email="admin@munidesk.com",
            password_hash=generate_password_hash("123456"),
            role="admin",
            department="IT",
            active=True,
        )
        technician = User(
            name="Luis Ramirez",
            email="technician@munidesk.com",
            password_hash=generate_password_hash("123456"),
            role="technician",
            department="IT",
            active=True,
        )
        requester = User(
            name="Ana Perez",
            email="requester@munidesk.com",
            password_hash=generate_password_hash("123456"),
            role="requester",
            department="Finance",
            active=True,
        )

        db.session.add_all([admin, technician, requester])
        db.session.commit()
        print("Demo data created successfully.")

    with app.app_context():
        db.create_all()

        if User.query.count() == 0:
            admin = User(
                name="Maria Soto",
                email="admin@munidesk.com",
                password_hash=generate_password_hash("123456"),
                role="admin",
                department="IT",
                active=True,
            )
            technician = User(
                name="Luis Ramirez",
                email="technician@munidesk.com",
                password_hash=generate_password_hash("123456"),
                role="technician",
                department="IT",
                active=True,
            )
            requester = User(
                name="Ana Perez",
                email="requester@munidesk.com",
                password_hash=generate_password_hash("123456"),
                role="requester",
                department="Finance",
                active=True,
            )

            db.session.add_all([admin, technician, requester])
            db.session.commit()

    return app