from datetime import datetime
from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import login_required, current_user
from .. import db
from ..forms import TicketForm, CommentForm, AssignmentForm
from ..models import Ticket, TicketComment, TicketHistory, User

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


def add_history(ticket_id, user_id, action, detail):
    db.session.add(TicketHistory(ticket_id=ticket_id, user_id=user_id, action=action, detail=detail))
    db.session.commit()


def generate_ticket_code():
    return f"MUNI-{datetime.utcnow().year}-{Ticket.query.count() + 1:04d}"


@tickets_bp.route("/")
@login_required
def list_tickets():
    if current_user.role == "admin":
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    elif current_user.role == "technician":
        tickets = Ticket.query.filter_by(technician_id=current_user.id).order_by(Ticket.created_at.desc()).all()
    else:
        tickets = Ticket.query.filter_by(requester_id=current_user.id).order_by(Ticket.created_at.desc()).all()

    return render_template("tickets/list.html", tickets=tickets)


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = TicketForm()

    if current_user.department and not form.department.data:
        form.department.data = current_user.department

    if form.validate_on_submit():
        ticket = Ticket(
            code=generate_ticket_code(),
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            priority=form.priority.data,
            status="new",
            department=form.department.data.strip(),
            requester_id=current_user.id,
        )
        db.session.add(ticket)
        db.session.commit()

        add_history(ticket.id, current_user.id, "Ticket created", f"Ticket created with status New.")
        flash("Ticket created successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    return render_template("tickets/create.html", form=form)


@tickets_bp.route("/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not ticket.can_view(current_user):
        abort(403)

    comment_form = CommentForm(prefix="comment")
    assignment_form = AssignmentForm(prefix="assign")

    techs = User.query.filter_by(role="technician", active=True).order_by(User.name.asc()).all()
    assignment_form.technician_id.choices = [(0, "Select a technician")] + [(u.id, u.name) for u in techs]

    if not assignment_form.is_submitted():
        assignment_form.technician_id.data = ticket.technician_id or 0
        assignment_form.status.data = ticket.status
        assignment_form.priority.data = ticket.priority

    if comment_form.validate_on_submit() and comment_form.submit.data:
        internal = bool(comment_form.internal.data and current_user.role != "requester")
        db.session.add(
            TicketComment(
                ticket_id=ticket.id,
                user_id=current_user.id,
                content=comment_form.content.data.strip(),
                internal=internal,
            )
        )
        db.session.commit()
        add_history(ticket.id, current_user.id, "Comment added", "A new comment was added.")
        flash("Comment added successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if current_user.role == "admin" and assignment_form.validate_on_submit() and assignment_form.submit.data:
        previous_status = ticket.status
        previous_technician = ticket.technician_id

        ticket.technician_id = assignment_form.technician_id.data or None
        ticket.status = assignment_form.status.data
        ticket.priority = assignment_form.priority.data

        if ticket.status == "resolved" and not ticket.resolved_at:
            ticket.resolved_at = datetime.utcnow()
        elif ticket.status != "resolved":
            ticket.resolved_at = None

        db.session.commit()

        if previous_technician != ticket.technician_id:
            add_history(ticket.id, current_user.id, "Assignment updated", "Ticket assigned or reassigned.")

        if previous_status != ticket.status:
            add_history(
                ticket.id,
                current_user.id,
                "Status updated",
                f"Status changed from {previous_status} to {ticket.status}.",
            )

        flash("Ticket updated successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comments = [c for c in ticket.comments if not (c.internal and current_user.role == "requester")]
    history_entries = sorted(ticket.history_entries, key=lambda x: x.created_at, reverse=True)

    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        comment_form=comment_form,
        assignment_form=assignment_form,
        comments=comments,
        history_entries=history_entries,
    )


@tickets_bp.route("/<int:ticket_id>/status/<string:new_status>", methods=["POST"])
@login_required
def quick_status(ticket_id, new_status):
    ticket = Ticket.query.get_or_404(ticket_id)

    if new_status not in {"in_progress", "resolved", "reopened"}:
        abort(400)

    if current_user.role not in ["technician", "admin"]:
        abort(403)

    if current_user.role == "technician" and ticket.technician_id != current_user.id:
        abort(403)

    previous_status = ticket.status
    ticket.status = new_status

    if new_status == "resolved":
        ticket.resolved_at = datetime.utcnow()
    elif new_status == "reopened":
        ticket.resolved_at = None

    db.session.commit()

    add_history(
        ticket.id,
        current_user.id,
        "Quick status update",
        f"Status changed from {previous_status} to {new_status}.",
    )
    flash("Status updated successfully.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))