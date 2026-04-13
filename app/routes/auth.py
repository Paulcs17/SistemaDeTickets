from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash
from ..forms import LoginForm
from ..models import User

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Bienvenido a MuniDesk Demo.", "success")
            return redirect(url_for("dashboard.index"))
        flash("Credenciales inválidas.", "danger")
    demo_users = [
        {"role":"Jefe","email":"jefe@municipalidad.cl","password":"123456"},
        {"role":"Técnico","email":"tecnico@municipalidad.cl","password":"123456"},
        {"role":"Funcionario","email":"funcionario@municipalidad.cl","password":"123456"},
    ]
    return render_template("auth/login.html", form=form, demo_users=demo_users)

@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("Has cerrado sesión.", "info")
    return redirect(url_for("auth.home"))
