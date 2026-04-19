from datetime import datetime
from flask_login import UserMixin
from . import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="requester")
    department = db.Column(db.String(120))
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    requested_tickets = db.relationship(
        "Ticket",
        backref="requester",
        foreign_keys="Ticket.requester_id",
        lazy=True,
    )
    assigned_tickets = db.relationship(
        "Ticket",
        backref="technician",
        foreign_keys="Ticket.technician_id",
        lazy=True,
    )


class Ticket(db.Model):
    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    title = db.Column(db.String(160), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(80), nullable=False)
    priority = db.Column(db.String(20), nullable=False, default="medium")
    status = db.Column(db.String(20), nullable=False, default="new")
    department = db.Column(db.String(120), nullable=False)
    requester_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    technician_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)

    comments = db.relationship(
        "TicketComment",
        backref="ticket",
        lazy=True,
        cascade="all, delete-orphan",
    )
    history_entries = db.relationship(
        "TicketHistory",
        backref="ticket",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def can_view(self, user):
        return (
            user.role == "admin"
            or (user.role == "technician" and self.technician_id == user.id)
            or (user.role == "requester" and self.requester_id == user.id)
        )


class TicketComment(db.Model):
    __tablename__ = "ticket_comments"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    internal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User")


class TicketHistory(db.Model):
    __tablename__ = "ticket_history"

    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    action = db.Column(db.String(80), nullable=False)
    detail = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    actor = db.relationship("User")