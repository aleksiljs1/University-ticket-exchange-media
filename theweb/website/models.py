from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func


class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)


class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    departments = db.relationship("Department", backref="faculty", lazy=True)


class Department(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), unique=True, nullable=False)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=False)
    users = db.relationship("User", backref="department", lazy=True)


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    first_name = db.Column(db.String(150), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey("department.id"), nullable=True)
    faculty_id = db.Column(db.Integer, db.ForeignKey("faculty.id"), nullable=True)
    gpa = db.Column(db.Float, nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey("role.id"), nullable=False)
    allow_ticket_visibility = db.Column(
        db.Boolean, default=True
    )  # New field for visibility

    # Removed the 'tickets' relationship to avoid conflict with 'creator' in Ticket model

    role = db.relationship("Role", backref="users", lazy=True)
    faculty = db.relationship("Faculty", backref="users", lazy=True)


class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.String(1000), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    image = db.Column(db.String(100), nullable=True)
    upvotes = db.Column(db.Integer, default=0)

    # Foreign keys
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), nullable=True
    )  # Make this field nullable
    recipient_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    reply_to_ticket_id = db.Column(
        db.Integer, db.ForeignKey("ticket.id"), nullable=True
    )

    # Relationships
    creator = db.relationship("User", backref="created_tickets", foreign_keys=[user_id])
    recipient = db.relationship(
        "User", backref="received_tickets", foreign_keys=[recipient_id]
    )
    original_ticket = db.relationship(
        "Ticket", remote_side=[id], backref="replies", foreign_keys=[reply_to_ticket_id]
    )

    # Cascade delete for upvotes and visibility
    upvoted_by = db.relationship(
        "TicketUpvote", backref="ticket", cascade="all, delete", lazy=True
    )
    visibility = db.relationship(
        "TicketVisibility", backref="ticket", cascade="all, delete", lazy=True
    )


# separate
class TicketUpvote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"), nullable=False)

    __table_args__ = (
        db.UniqueConstraint("user_id", "ticket_id", name="unique_user_ticket_upvote"),
    )


class TicketVisibility(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey("ticket.id"), nullable=False)

    # Visibility options
    students_in_department = db.Column(db.Boolean, default=False, nullable=False)
    students_in_all_departments = db.Column(db.Boolean, default=False, nullable=False)
    professors_in_department = db.Column(db.Boolean, default=False, nullable=False)
    professors_in_all_departments = db.Column(db.Boolean, default=False, nullable=False)
    visible_to_admins = db.Column(db.Boolean, default=False, nullable=False)


# New AllowedEmail model
class AllowedEmail(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
