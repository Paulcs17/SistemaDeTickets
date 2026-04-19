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
    app.config.from_object(Config)
    db.init_app(app)
    login_manager.init_app(app)

    from .models import User, Ticket, TicketComment, TicketHistory
    from .routes.auth import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.tickets import tickets_bp
    from .routes.admin import admin_bp

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
        from werkzeug.security import generate_password_hash

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

        t1 = Ticket(
            code="MUNI-2026-0001",
            title="Main printer is not responding",
            description="The main printer in the Finance department stopped working and users cannot print documents.",
            category="Printers",
            priority="high",
            status="in_progress",
            department="Finance",
            requester_id=requester.id,
            technician_id=technician.id,
        )
        t2 = Ticket(
            code="MUNI-2026-0002",
            title="Office installation request",
            description="A new workstation in the Administration office needs Microsoft Office installed.",
            category="Software",
            priority="medium",
            status="new",
            department="Administration",
            requester_id=requester.id,
        )
        t3 = Ticket(
            code="MUNI-2026-0003",
            title="Cannot access institutional email",
            description="The user cannot sign in to the municipal email account and needs urgent access restored.",
            category="Email",
            priority="critical",
            status="resolved",
            department="Human Resources",
            requester_id=requester.id,
            technician_id=technician.id,
        )

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        history_entries = [
            TicketHistory(
                ticket_id=t1.id,
                user_id=requester.id,
                action="Ticket created",
                detail="Ticket created with status New.",
            ),
            TicketHistory(
                ticket_id=t1.id,
                user_id=admin.id,
                action="Assigned",
                detail="Ticket assigned to Luis Ramirez.",
            ),
            TicketHistory(
                ticket_id=t1.id,
                user_id=technician.id,
                action="Status updated",
                detail="Status changed to In Progress.",
            ),
            TicketHistory(
                ticket_id=t3.id,
                user_id=technician.id,
                action="Resolved",
                detail="Email access was restored successfully.",
            ),
        ]

        comments = [
            TicketComment(
                ticket_id=t1.id,
                user_id=technician.id,
                content="I checked the print queue and verified the cable connection.",
                internal=False,
            ),
            TicketComment(
                ticket_id=t3.id,
                user_id=technician.id,
                content="The account was locked after multiple failed login attempts.",
                internal=False,
            ),
        ]

        db.session.add_all(history_entries + comments)
        db.session.commit()
        print("Demo data created successfully.")

    return app