from flask import Blueprint, jsonify, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from .models import (
    Department,
    Role,
    Ticket,
    Faculty,
    TicketUpvote,
    TicketVisibility,
    User,
    AllowedEmail,
)
from . import db
import os
from werkzeug.utils import secure_filename
from sqlalchemy import and_, or_


views = Blueprint("views", __name__)

# Set the upload folder and allowed extensions
UPLOAD_FOLDER = os.path.join("website", "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}


if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from sqlalchemy import or_
from .models import Ticket, TicketUpvote, TicketVisibility
from . import db


@views.route("/", methods=["GET", "POST"])
@login_required
def home():
    category = request.args.get("category")

    tickets_query = Ticket.query.join(TicketVisibility)

    if current_user.role.name == "Student":
        tickets_query = tickets_query.filter(
            or_(
                TicketVisibility.students_in_all_departments == True,
                and_(
                    TicketVisibility.students_in_department == True,
                    Ticket.creator.has(department_id=current_user.department_id),
                ),
            )
        )
    elif current_user.role.name == "Teacher":
        tickets_query = tickets_query.filter(
            or_(
                TicketVisibility.professors_in_all_departments == True,
                and_(
                    TicketVisibility.professors_in_department == True,
                    Ticket.creator.has(department_id=current_user.department_id),
                ),
            )
        )

    # Filter by category if provided
    if category:
        tickets_query = tickets_query.filter(Ticket.category == category)

    # Order by date
    tickets = tickets_query.order_by(Ticket.date.desc()).all()

    # Fetch upvoted tickets for the current user
    upvoted_tickets = [
        upvote.ticket_id
        for upvote in TicketUpvote.query.filter_by(user_id=current_user.id).all()
    ]

    return render_template(
        "home.html", user=current_user, tickets=tickets, upvoted_tickets=upvoted_tickets
    )


@views.route("/personalized")
@login_required
def personalized():
    tickets = (
        Ticket.query.filter_by(recipient_id=current_user.id)
        .order_by(Ticket.date.desc())
        .all()
    )
    return render_template("personalized.html", user=current_user, tickets=tickets)


@views.route("/refer-administration")
@login_required
def refer_administration():
    if current_user.role.name not in ["Admin", "Super Admin"]:
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    tickets = (
        Ticket.query.join(TicketVisibility)
        .filter(TicketVisibility.visible_to_admins == True)
        .order_by(Ticket.date.desc())
        .all()
    )

    return render_template(
        "refer_administration.html", user=current_user, tickets=tickets
    )


@views.route("/ask-the-desk", methods=["GET", "POST"])
@login_required
def ask_the_desk():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        file = request.files["image"]

        if not title or not content or not category:
            flash("Please fill out all fields", category="error")
        elif file and not allowed_file(file.filename):
            flash("File type not allowed", category="error")
        else:
            filename = None
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_ticket = Ticket(
                title=title,
                content=content,
                category=category,
                image=filename,
                user_id=current_user.id,
            )
            db.session.add(new_ticket)
            db.session.commit()

            # Mark visibility only for admins and super admins
            visibility = TicketVisibility(
                ticket_id=new_ticket.id, visible_to_admins=True
            )
            db.session.add(visibility)
            db.session.commit()

            flash("Your request has been submitted!", category="success")
            return redirect(url_for("views.home"))

    return render_template("ask_the_desk.html", user=current_user)


@views.route("/profile")
@login_required
def profile():
    tickets = (
        Ticket.query.filter_by(user_id=current_user.id)
        .order_by(Ticket.date.desc())
        .all()
    )
    return render_template("profile.html", user=current_user, tickets=tickets)


@views.route("/create-ticket", methods=["GET", "POST"])
@login_required
def create_ticket():
    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")

        students_in_department = "students_in_department" in request.form
        students_in_all_departments = "students_in_all_departments" in request.form
        professors_in_department = "professors_in_department" in request.form
        professors_in_all_departments = "professors_in_all_departments" in request.form
        visible_to_admin = "visible_to_admin" in request.form

        file = request.files["image"]

        if not title or not content or not category:
            flash("Please fill out all fields", category="error")
        elif file and not allowed_file(file.filename):
            flash("File type not allowed", category="error")
        else:
            filename = None
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_ticket = Ticket(
                title=title,
                content=content,
                category=category,
                image=filename,
                user_id=current_user.id,
            )
            db.session.add(new_ticket)
            db.session.commit()

            # Add visibility settings
            visibility = TicketVisibility(
                ticket_id=new_ticket.id,
                students_in_department=students_in_department,
                students_in_all_departments=students_in_all_departments,
                professors_in_department=professors_in_department,
                professors_in_all_departments=professors_in_all_departments,
                visible_to_admins=visible_to_admin,
            )
            db.session.add(visibility)
            db.session.commit()

            flash("Ticket created!", category="success")
            return redirect(url_for("views.home"))

    return render_template("ticket.html", user=current_user)


@views.route("/users")
@login_required
def users():
    if current_user.role.name != "Super Admin":
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    sort_by = request.args.get("sort_by", "role")  # Default sort by role

    if sort_by == "name":
        users = User.query.order_by(User.first_name.asc()).all()
    elif sort_by == "email":
        users = User.query.order_by(User.email.asc()).all()
    else:  # Default to sorting by role
        users = (
            User.query.join(Role).order_by(Role.name.asc(), User.first_name.asc()).all()
        )

    return render_template("users.html", user=current_user, users=users)


@views.route("/edit-user/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_user(user_id):
    if current_user.role.name != "Super Admin":
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    user = User.query.get_or_404(user_id)

    if request.method == "POST":
        user.first_name = request.form.get("first_name")
        user.email = request.form.get("email")
        user.role_id = request.form.get("role_id")
        db.session.commit()
        flash("User updated successfully.", category="success")
        return redirect(url_for("views.users"))

    roles = Role.query.all()
    return render_template(
        "edit_user.html", user=current_user, edit_user=user, roles=roles
    )


@views.route("/delete-user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    if current_user.role.name != "Super Admin":
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash("User deleted successfully.", category="success")
    return redirect(url_for("views.users"))


@views.route("/register-emails", methods=["GET", "POST"])
@login_required
def register_emails():
    if current_user.role.name != "Super Admin":
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    if request.method == "POST":
        new_email = request.form.get("email")
        if new_email:
            existing_email = AllowedEmail.query.filter_by(email=new_email).first()
            if existing_email:
                flash("Email already registered.", category="error")
            else:
                email_entry = AllowedEmail(email=new_email)
                db.session.add(email_entry)
                db.session.commit()
                flash("Email successfully registered.", category="success")
        else:
            flash("Please enter a valid email.", category="error")

    allowed_emails = AllowedEmail.query.all()
    return render_template(
        "register_emails.html", allowed_emails=allowed_emails, user=current_user
    )


@views.route("/delete-allowed-email/<int:email_id>", methods=["POST"])
@login_required
def delete_allowed_email(email_id):
    if current_user.role.name != "Super Admin":
        flash("Access denied.", category="error")
        return redirect(url_for("views.home"))

    email_entry = AllowedEmail.query.get_or_404(email_id)
    db.session.delete(email_entry)
    db.session.commit()
    flash("Allowed email deleted successfully.", category="success")
    return redirect(url_for("views.register_emails"))


@views.route("/upvote/<int:ticket_id>", methods=["POST"])
@login_required
def upvote_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    upvote_exists = TicketUpvote.query.filter_by(
        user_id=current_user.id, ticket_id=ticket_id
    ).first()

    if upvote_exists:
        flash("You have already upvoted this ticket.", category="error")
    else:
        upvote = TicketUpvote(user_id=current_user.id, ticket_id=ticket_id)
        ticket.upvotes += 1
        db.session.add(upvote)
        db.session.commit()
        flash("Ticket upvoted!", category="success")

    return redirect(url_for("views.home"))


@views.route("/delete-ticket/<int:ticket_id>", methods=["POST"])
@login_required
def delete_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if ticket.user_id != current_user.id and current_user.role.name not in [
        "Admin",
        "Super Admin",
    ]:
        flash("You do not have permission to delete this ticket.", category="error")
        return redirect(url_for("views.home"))

    db.session.delete(ticket)
    db.session.commit()
    flash("Ticket deleted successfully.", category="success")
    return redirect(url_for("views.home"))


@views.route("/edit-ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    if current_user.role.name != "Super Admin":
        flash("You do not have permission to edit this ticket.", category="error")
        return redirect(url_for("views.home"))

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        file = request.files["image"]

        if not title or not content or not category:
            flash("Please fill out all fields", category="error")
        elif file and not allowed_file(file.filename):
            flash("File type not allowed", category="error")
        else:
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                ticket.image = filename

            ticket.title = title
            ticket.content = content
            ticket.category = category
            db.session.commit()
            flash("Ticket updated successfully.", category="success")
            return redirect(url_for("views.home"))

    return render_template("edit_ticket.html", user=current_user, ticket=ticket)


@views.route("/reply-ticket/<int:ticket_id>", methods=["GET", "POST"])
@login_required
def reply_ticket(ticket_id):
    original_ticket = Ticket.query.get_or_404(ticket_id)
    recipient = original_ticket.creator

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        file = request.files["image"]

        if not title or not content or not category:
            flash("Please fill out all fields", category="error")
        elif file and not allowed_file(file.filename):
            flash("File type not allowed", category="error")
        else:
            filename = None
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

            reply_ticket = Ticket(
                title=title,
                content=content,
                category=category,
                image=filename,
                user_id=current_user.id,
                recipient_id=recipient.id,
                reply_to_ticket_id=original_ticket.id,  # This field references the original ticket
            )
            db.session.add(reply_ticket)
            db.session.commit()
            flash("Reply sent!", category="success")
            return redirect(url_for("views.personalized"))

    # Pass the original_ticket to the template
    return render_template(
        "compose_ticket.html",
        user=current_user,
        recipient=recipient,
        original_ticket=original_ticket,
    )


@views.route("/get_departments/<int:faculty_id>")
def get_departments(faculty_id):
    departments = Department.query.filter_by(faculty_id=faculty_id).all()
    departments_list = [{"id": dept.id, "name": dept.name} for dept in departments]
    return jsonify(departments=departments_list)


@views.route("/search_users", methods=["GET"])
@login_required
def search_users():
    query = request.args.get("q", "")
    if query:
        users = User.query.filter(User.first_name.ilike(f"%{query}%")).all()
        users_list = [{"id": user.id, "first_name": user.first_name} for user in users]
        return jsonify(users=users_list)
    return jsonify(users=[])


@views.route("/ticket", methods=["GET", "POST"])
@login_required
def ticket():
    return render_template("ticket.html", user=current_user)


@views.route("/compose-ticket/<int:user_id>", methods=["GET", "POST"])
@login_required
def compose_ticket(user_id):
    recipient = User.query.get_or_404(user_id)

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        category = request.form.get("category")
        file = request.files["image"]

        if not title or not content or not category:
            flash("Please fill out all fields", category="error")
        elif file and not allowed_file(file.filename):
            flash("File type not allowed", category="error")
        else:
            filename = None
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(UPLOAD_FOLDER, filename))

            new_ticket = Ticket(
                title=title,
                content=content,
                category=category,
                image=filename,
                user_id=current_user.id,
                recipient_id=recipient.id,  # Set the recipient of the ticket
            )
            db.session.add(new_ticket)
            db.session.commit()
            flash("Personal ticket sent!", category="success")
            return redirect(url_for("views.user_profile", user_id=user_id))

    return render_template(
        "compose_ticket.html", user=current_user, recipient=recipient
    )


@views.route("/user_profile/<int:user_id>")
@login_required
def user_profile(user_id):
    user = User.query.get_or_404(user_id)
    tickets = (
        Ticket.query.filter_by(user_id=user_id, recipient_id=None)
        .order_by(Ticket.date.desc())
        .all()
    )  # Exclude personalized tickets
    return render_template("user_profile.html", user=user, tickets=tickets)


@views.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    if request.method == "POST":
        # Handle visibility toggle
        allow_ticket_visibility = "allow_ticket_visibility" in request.form
        current_user.allow_ticket_visibility = allow_ticket_visibility

        # Update user details
        current_user.first_name = request.form.get("first_name")
        if current_user.role.name == "Student":
            current_user.gpa = request.form.get("gpa")
        elif current_user.role.name == "Teacher":
            current_user.faculty_id = request.form.get("faculty")

        db.session.commit()
        flash("Settings updated successfully.", category="success")

    return render_template("settings.html", user=current_user)


@views.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    user = User.query.get_or_404(current_user.id)
    db.session.delete(user)
    db.session.commit()
    flash("Your account has been deleted.", category="success")
    return redirect(url_for("auth.logout"))
