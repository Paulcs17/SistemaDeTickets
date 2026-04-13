from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import Ticket, User

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")

@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == "jefe":
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
        stats = {"total": Ticket.query.count(), "nuevo": Ticket.query.filter_by(status="Nuevo").count(), "proceso": Ticket.query.filter(Ticket.status.in_(["Asignado","En proceso","En revisión"])).count(), "resuelto": Ticket.query.filter_by(status="Resuelto").count()}
    elif current_user.role == "tecnico":
        tickets = Ticket.query.filter_by(technician_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        stats = {"total": len(tickets), "nuevo": Ticket.query.filter_by(technician_id=current_user.id, status="Nuevo").count(), "proceso": Ticket.query.filter(Ticket.technician_id==current_user.id, Ticket.status.in_(["Asignado","En proceso","En revisión"])).count(), "resuelto": Ticket.query.filter_by(technician_id=current_user.id, status="Resuelto").count()}
    else:
        tickets = Ticket.query.filter_by(requester_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        stats = {"total": len(tickets), "nuevo": Ticket.query.filter_by(requester_id=current_user.id, status="Nuevo").count(), "proceso": Ticket.query.filter(Ticket.requester_id==current_user.id, Ticket.status.in_(["Asignado","En proceso","En revisión"])).count(), "resuelto": Ticket.query.filter_by(requester_id=current_user.id, status="Resuelto").count()}
    return render_template("dashboard/index.html", tickets=tickets, stats=stats)
