from flask import Blueprint, render_template
from flask_login import login_required, current_user
from ..models import Ticket

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/dashboard")


@dashboard_bp.route("/")
@login_required
def index():
    if current_user.role == "admin":
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
        stats = {
            "total": Ticket.query.count(),
            "new": Ticket.query.filter_by(status="new").count(),
            "in_progress": Ticket.query.filter(
                Ticket.status.in_(["assigned", "review", "in_progress"])
            ).count(),
            "resolved": Ticket.query.filter_by(status="resolved").count(),
        }
    elif current_user.role == "technician":
        tickets = Ticket.query.filter_by(technician_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        stats = {
            "total": len(tickets),
            "new": Ticket.query.filter_by(technician_id=current_user.id, status="new").count(),
            "in_progress": Ticket.query.filter(
                Ticket.technician_id == current_user.id,
                Ticket.status.in_(["assigned", "review", "in_progress"]),
            ).count(),
            "resolved": Ticket.query.filter_by(technician_id=current_user.id, status="resolved").count(),
        }
    else:
        tickets = Ticket.query.filter_by(requester_id=current_user.id).order_by(Ticket.created_at.desc()).all()
        stats = {
            "total": len(tickets),
            "new": Ticket.query.filter_by(requester_id=current_user.id, status="new").count(),
            "in_progress": Ticket.query.filter(
                Ticket.requester_id == current_user.id,
                Ticket.status.in_(["assigned", "review", "in_progress"]),
            ).count(),
            "resolved": Ticket.query.filter_by(requester_id=current_user.id, status="resolved").count(),
        }

    return render_template("dashboard/index.html", tickets=tickets, stats=stats)
