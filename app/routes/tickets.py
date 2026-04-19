@tickets_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_ticket():
    form = TicketForm()

    requesters = User.query.filter_by(role="requester", active=True).order_by(User.name.asc()).all()
    technicians = User.query.filter_by(role="technician", active=True).order_by(User.name.asc()).all()

    form.requester_id.choices = [(0, "Select a requester")] + [(u.id, u.name) for u in requesters]
    form.technician_id.choices = [(0, "Unassigned")] + [(u.id, u.name) for u in technicians]

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
            add_history(ticket.id, current_user.id, "Assignment updated", "Ticket assigned during creation.")

        flash("Ticket created successfully.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    return render_template("tickets/create.html", form=form)