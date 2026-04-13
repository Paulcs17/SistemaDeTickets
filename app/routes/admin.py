from flask import Blueprint, abort, render_template
from flask_login import login_required, current_user
from ..models import User, Ticket

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

@admin_bp.before_request
@login_required
def protect_admin():
    if current_user.role != "jefe":
        abort(403)

@admin_bp.route("/users")
def users():
    return render_template("admin/users.html", users=User.query.order_by(User.role.asc(), User.name.asc()).all())

@admin_bp.route("/tickets")
def all_tickets():
    return render_template("admin/tickets.html", tickets=Ticket.query.order_by(Ticket.created_at.desc()).all())
