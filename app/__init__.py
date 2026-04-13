from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Debes iniciar sesión para continuar."
login_manager.login_message_category = "warning"

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

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(admin_bp)

    @app.cli.command("init-db")
    def init_db():
        db.drop_all()
        db.create_all()
        print("Base de datos creada correctamente.")

    @app.cli.command("seed-data")
    def seed_data():
        from werkzeug.security import generate_password_hash

        TicketComment.query.delete()
        TicketHistory.query.delete()
        Ticket.query.delete()
        User.query.delete()
        db.session.commit()

        jefe = User(name="María Soto", email="jefe@municipalidad.cl", password_hash=generate_password_hash("123456"), role="jefe", department="Informática", active=True)
        tecnico = User(name="Luis Ramírez", email="tecnico@municipalidad.cl", password_hash=generate_password_hash("123456"), role="tecnico", department="Informática", active=True)
        funcionario = User(name="Ana Pérez", email="funcionario@municipalidad.cl", password_hash=generate_password_hash("123456"), role="solicitante", department="Finanzas", active=True)
        db.session.add_all([jefe, tecnico, funcionario])
        db.session.commit()

        t1 = Ticket(code="MUNI-2026-0001", title="Impresora no responde", description="La impresora principal del departamento de Finanzas dejó de imprimir.", category="Impresoras", priority="Alta", status="En proceso", department="Finanzas", requester_id=funcionario.id, technician_id=tecnico.id)
        t2 = Ticket(code="MUNI-2026-0002", title="Instalación de Office", description="Se necesita instalar Office en un nuevo equipo de Secretaría.", category="Software", priority="Media", status="Nuevo", department="Secretaría", requester_id=funcionario.id)
        t3 = Ticket(code="MUNI-2026-0003", title="Acceso a correo institucional", description="No es posible iniciar sesión en el correo municipal.", category="Correo institucional", priority="Crítica", status="Resuelto", department="Recursos Humanos", requester_id=funcionario.id, technician_id=tecnico.id)
        db.session.add_all([t1, t2, t3]); db.session.commit()

        h = [
            TicketHistory(ticket_id=t1.id, user_id=funcionario.id, action="Creación", detail="Ticket creado con estado Nuevo."),
            TicketHistory(ticket_id=t1.id, user_id=jefe.id, action="Asignación", detail="Ticket asignado al técnico Luis Ramírez."),
            TicketHistory(ticket_id=t1.id, user_id=tecnico.id, action="Estado", detail="Estado cambiado a En proceso."),
            TicketHistory(ticket_id=t3.id, user_id=tecnico.id, action="Resolución", detail="Se restableció el acceso al correo."),
        ]
        c = [
            TicketComment(ticket_id=t1.id, user_id=tecnico.id, content="Se revisó el cableado y la cola de impresión.", internal=False),
            TicketComment(ticket_id=t3.id, user_id=tecnico.id, content="La cuenta estaba bloqueada por intentos fallidos.", internal=False),
        ]
        db.session.add_all(h + c); db.session.commit()
        print("Datos demo creados correctamente.")

    return app
