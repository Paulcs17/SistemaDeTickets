from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash
from ..forms import LoginForm
from ..models import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def home():
    return render_template("landing.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.strip().lower()).first()
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            flash("Welcome back to MuniDesk.", "success")
            return redirect(url_for("dashboard.index"))
        flash("Invalid email or password.", "danger")

    demo_users = [
        {"role": "Admin", "email": "admin@munidesk.com", "password": "123456"},
        {"role": "Technician", "email": "technician@munidesk.com", "password": "123456"},
        {"role": "Requester", "email": "requester@munidesk.com", "password": "123456"},
    ]

    return render_template("auth/login.html", form=form, demo_users=demo_users)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have signed out successfully.", "info")
    return redirect(url_for("auth.home"))