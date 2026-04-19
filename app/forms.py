from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length, Optional

CATEGORIES = [
    ("hardware", "Hardware"),
    ("software", "Software"),
    ("network", "Network & Internet"),
    ("email", "Email"),
    ("printers", "Printers"),
    ("accounts", "Accounts & Access"),
    ("maintenance", "Maintenance"),
    ("other", "Other"),
]

PRIORITIES = [
    ("low", "Low"),
    ("medium", "Medium"),
    ("high", "High"),
    ("critical", "Critical"),
]

STATUSES = [
    ("new", "New"),
    ("review", "Under Review"),
    ("assigned", "Assigned"),
    ("in_progress", "In Progress"),
    ("resolved", "Resolved"),
    ("closed", "Closed"),
    ("reopened", "Reopened"),
]


class LoginForm(FlaskForm):
    email = StringField("Email address", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Sign in")


class TicketForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Description", validators=[DataRequired(), Length(min=10)])
    category = SelectField("Category", choices=CATEGORIES, validators=[DataRequired()])
    priority = SelectField("Priority", choices=PRIORITIES, validators=[DataRequired()])
    department = StringField("Department", validators=[DataRequired(), Length(max=120)])

    requester_id = SelectField("Requester", coerce=int, validators=[Optional()], choices=[])
    technician_id = SelectField("Technician", coerce=int, validators=[Optional()], choices=[])

    submit = SubmitField("Create Ticket")


class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[DataRequired(), Length(min=2)])
    internal = BooleanField("Internal note")
    submit = SubmitField("Add Comment")


class AssignmentForm(FlaskForm):
    technician_id = SelectField("Technician", coerce=int, validators=[Optional()])
    status = SelectField("Status", choices=STATUSES, validators=[DataRequired()])
    priority = SelectField("Priority", choices=PRIORITIES, validators=[DataRequired()])
    submit = SubmitField("Save Changes")
