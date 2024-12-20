from flask import Blueprint, render_template, request, flash, redirect, url_for
from .models import AllowedEmail, Faculty, Role, User
from werkzeug.security import generate_password_hash, check_password_hash
from . import db   ##means from __init__.py import db
from flask_login import login_user, login_required, logout_user, current_user


auth = Blueprint('auth', __name__)


@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('Email does not exist.', category='error')

    return render_template("login.html", user=current_user)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        role_name = request.form.get('role')
        email = request.form.get('email')
        first_name = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        faculty_id = request.form.get('faculty')
        department_id = request.form.get('department')
        gpa = request.form.get('gpa')

        # Check if email is allowed
        allowed_email = AllowedEmail.query.filter_by(email=email).first()
        if not allowed_email:
            flash('This email is not allowed to sign up.', category='error')
            return redirect(url_for('auth.sign_up'))

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        elif len(email) < 4:
            flash('Email must be greater than 3 characters.', category='error')
        elif len(first_name) < 2:
            flash('First name must be greater than 1 character.', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match.', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters.', category='error')
        else:
            role = Role.query.filter_by(name=role_name).first()
            if not role:
                flash('Invalid role selected.', category='error')
            else:
                new_user = User(
                    email=email,
                    first_name=first_name,
                    password=generate_password_hash(password1, method='pbkdf2:sha256'),
                    department_id=department_id if role.name == 'Student' else None,
                    faculty_id=faculty_id,
                    gpa=gpa if role.name == 'Student' else None,
                    role_id=role.id
                )
                db.session.add(new_user)
                db.session.commit()
                login_user(new_user, remember=True)
                flash('Account created!', category='success')
                return redirect(url_for('views.home'))

    faculties = Faculty.query.all()
    roles = Role.query.filter(Role.name != 'Super Admin').all()  # Exclude Super Admin from available roles
    return render_template("sign_up.html", user=current_user, faculties=faculties, roles=roles)


@auth.route('/profile')
@login_required
def profile():
    user = User.query.get(current_user.id)
    return render_template('profile.html', user=user)