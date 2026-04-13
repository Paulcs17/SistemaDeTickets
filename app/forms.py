from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, BooleanField
from wtforms.validators import DataRequired, Email, Length

CATEGORIES = [("Hardware","Hardware"),("Software","Software"),("Red e Internet","Red e Internet"),("Correo institucional","Correo institucional"),("Impresoras","Impresoras"),("Accesos y cuentas","Accesos y cuentas"),("Mantención","Mantención"),("Otro","Otro")]
PRIORITIES = [("Baja","Baja"),("Media","Media"),("Alta","Alta"),("Crítica","Crítica")]
STATUSES = [("Nuevo","Nuevo"),("En revisión","En revisión"),("Asignado","Asignado"),("En proceso","En proceso"),("Resuelto","Resuelto"),("Cerrado","Cerrado"),("Reabierto","Reabierto")]

class LoginForm(FlaskForm):
    email = StringField("Correo", validators=[DataRequired(), Email()])
    password = PasswordField("Contraseña", validators=[DataRequired()])
    submit = SubmitField("Ingresar")

class TicketForm(FlaskForm):
    title = StringField("Título", validators=[DataRequired(), Length(max=160)])
    description = TextAreaField("Descripción", validators=[DataRequired(), Length(min=10)])
    category = SelectField("Categoría", choices=CATEGORIES, validators=[DataRequired()])
    priority = SelectField("Prioridad", choices=PRIORITIES, validators=[DataRequired()])
    department = StringField("Departamento", validators=[DataRequired(), Length(max=120)])
    submit = SubmitField("Crear ticket")

class CommentForm(FlaskForm):
    content = TextAreaField("Comentario", validators=[DataRequired(), Length(min=2)])
    internal = BooleanField("Comentario interno")
    submit = SubmitField("Agregar comentario")

class AssignmentForm(FlaskForm):
    technician_id = SelectField("Técnico", coerce=int, validators=[DataRequired()])
    status = SelectField("Estado", choices=STATUSES, validators=[DataRequired()])
    priority = SelectField("Prioridad", choices=PRIORITIES, validators=[DataRequired()])
    submit = SubmitField("Guardar cambios")
