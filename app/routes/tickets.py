from datetime import datetime

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .. import db
from ..forms import AssignmentForm, CommentForm, TicketForm
from ..models import Ticket, TicketComment, TicketHistory, User

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")


def generate_ticket_code():
    current_year = datetime.utcnow().year
    total_tickets = Ticket.query.count() + 1
    return f"MUNI-{current_year}-{total_tickets:04d}"


def add_history(ticket_id, user_id, action, detail):
    entry = TicketHistory(
        ticket_id=ticket_id,
        user_id=user_id,
        action=action,
        detail=detail,
    )
    db.session.add(entry)
    db.session.commit()


@tickets_bp.route("/")
@login_required
def list_tickets():
    if current_user.role == "admin":
        tickets = Ticket.query.order_by(Ticket.created_at.desc()).all()
    elif current_user.role == "technician":
        tickets = (
            Ticket.query.filter_by(technician_id=current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )
    else:
        tickets = (
            Ticket.query.filter_by(requester_id=current_user.id)
            .order_by(Ticket.created_at.desc())
            .all()
        )

    return render_template("tickets/list.html", tickets=tickets)


@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = TicketForm()

    requesters = (
        User.query.filter_by(role="requester", active=True)
        .order_by(User.name.asc())
        .all()
    )
    technicians = (
        User.query.filter_by(role="technician", active=True)
        .order_by(User.name.asc())
        .all()
    )

    form.requester_id.choices = [(0, "Select a requester")] + [
        (u.id, u.name) for u in requesters
    ]
    form.technician_id.choices = [(0, "Unassigned")] + [
        (u.id, u.name) for u in technicians
    ]

    if current_user.department and not form.department.data:
        form.department.data = current_user.department

    if form.validate_on_submit():
        if current_user.role == "admin":
            requester_id = form.requester_id.data
            technician_id = form.technician_id.data or None

            if requester_id == 0:
                flash("Please select a requester.", "danger")
                return render_template("tickets/create.html", form=form)

            status = "assigned" if technician_id else "new"
        else:
            requester_id = current_user.id
            technician_id = None
            status = "new"

        ticket = Ticket(
            code=generate_ticket_code(),
            title=form.title.data.strip(),
            description=form.description.data.strip(),
            category=form.category.data,
            priority=form.priority.data,
            status=status,
            department=form.department.data.strip(),
            requester_id=requester_id,
            technician_id=technician_id,
        )
        db.session.add(ticket)
        db.session.commit()

        add_history(ticket.id, current_user.id, "Ticket created", "Ticket created successfully.")

        if technician_id:
            add_history(
                ticket.id,
                current_user.id,
                "Assignment updated",
                "Ticket assigned during creation.",
            )

        flash("Ticket created successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    return render_template("tickets/create.html", form=form)


@tickets_bp.route("/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def ticket_detail(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)

    if not ticket.can_view(current_user):
        abort(403)

    comment_form = CommentForm()
    assignment_form = AssignmentForm()

    technicians = (
        User.query.filter_by(role="technician", active=True)
        .order_by(User.name.asc())
        .all()
    )
    assignment_form.technician_id.choices = [(0, "Unassigned")] + [
        (u.id, u.name) for u in technicians
    ]

    if request.method == "GET":
        assignment_form.technician_id.data = ticket.technician_id or 0
        assignment_form.status.data = ticket.status
        assignment_form.priority.data = ticket.priority

    # Admin update form
    if (
        current_user.role == "admin"
        and assignment_form.submit.data
        and assignment_form.validate_on_submit()
    ):
        previous_technician_id = ticket.technician_id
        previous_status = ticket.status
        previous_priority = ticket.priority

        ticket.technician_id = assignment_form.technician_id.data or None
        ticket.status = assignment_form.status.data
        ticket.priority = assignment_form.priority.data

        if ticket.status == "resolved" and ticket.resolved_at is None:
            ticket.resolved_at = datetime.utcnow()
        elif ticket.status != "resolved":
            ticket.resolved_at = None

        db.session.commit()

        if previous_technician_id != ticket.technician_id:
            tech_name = ticket.technician.name if ticket.technician else "Unassigned"
            add_history(
                ticket.id,
                current_user.id,
                "Assignment updated",
                f"Technician changed to {tech_name}.",
            )

        if previous_status != ticket.status:
            add_history(
                ticket.id,
                current_user.id,
                "Status updated",
                f"Status changed to {ticket.status}.",
            )

        if previous_priority != ticket.priority:
            add_history(
                ticket.id,
                current_user.id,
                "Priority updated",
                f"Priority changed to {ticket.priority}.",
            )

        flash("Ticket updated successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    # Comment form
    if (
        comment_form.submit.data
        and comment_form.validate_on_submit()
        and not assignment_form.submit.data
    ):
        internal_note = bool(comment_form.internal.data) if current_user.role != "requester" else False

        comment = TicketComment(
            ticket_id=ticket.id,
            user_id=current_user.id,
            content=comment_form.content.data.strip(),
            internal=internal_note,
        )
        db.session.add(comment)
        db.session.commit()

        add_history(ticket.id, current_user.id, "Comment added", "A new comment was added.")
        flash("Comment added successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comments = ticket.comments
    if current_user.role == "requester":
        comments = [c for c in comments if not c.internal]

    history_entries = sorted(ticket.history_entries, key=lambda x: x.created_at, reverse=True)

    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        comments=comments,
        history_entries=history_entries,
        comment_form=comment_form,
        assignment_form=assignment_form,
    )


@tickets_bp.route("/<int:ticket_id>/quick-status/<string:new_status>", methods=["POST"])
@login_required
def quick_status(ticket_id, new_status):
    ticket = Ticket.query.get_or_404(ticket_id)

    if current_user.role not in ["admin", "technician"]:
        abort(403)

    if current_user.role == "technician" and ticket.technician_id != current_user.id:
        abort(403)

    allowed_statuses = ["in_progress", "resolved", "reopened"]
    if new_status not in allowed_statuses:
        abort(400)

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
        "Status updated",
        f"Status changed from {previous_status} to {new_status}.",
    )

    flash("Ticket status updated successfully.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))