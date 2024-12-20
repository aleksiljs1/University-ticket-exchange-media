from website import create_app, db
from website.models import Faculty, Department, Role, User
from werkzeug.security import generate_password_hash

app = create_app()

with app.app_context():
    # Check if there are any faculties or departments
    if not Faculty.query.first():
        # Add Faculties
        eng_faculty = Faculty(name="Faculty of Engineering")
        eco_faculty = Faculty(name="Faculty of Economy")
        
        db.session.add(eng_faculty)
        db.session.add(eco_faculty)
        db.session.commit()
        
        # Add Departments
        dept1 = Department(name="Department of Software Engineering", faculty=eng_faculty)
        dept2 = Department(name="Department of Electronics and Telecommunications Engineering", faculty=eng_faculty)
        dept3 = Department(name="Department of Business Administration", faculty=eco_faculty)
        dept4 = Department(name="Department of Business Administration & IT", faculty=eco_faculty)
        
        db.session.add(dept1)
        db.session.add(dept2)
        db.session.add(dept3)
        db.session.add(dept4)
        db.session.commit()

    if not Role.query.first():
        # Add Roles
        student_role = Role(name="Student")
        teacher_role = Role(name="Teacher")
        admin_role = Role(name="Admin")  # Admin role
        super_admin_role = Role(name="Super Admin")
        desk_support_role = Role(name="Desk Support")  # New Desk Support role

        db.session.add(student_role)
        db.session.add(teacher_role)
        db.session.add(admin_role)
        db.session.add(super_admin_role)
        db.session.add(desk_support_role)  # Add the new role to the database
        db.session.commit()

    # Create Super Admin account if it doesn't exist
    super_admin_email = "aleksissuper@gmail.com"
    super_admin_user = User.query.filter_by(email=super_admin_email).first()
    if not super_admin_user:
        hashed_password = generate_password_hash("superpassword", method='pbkdf2:sha256')
        super_admin_user = User(
            email=super_admin_email,
            first_name="Aleksis Super Admin",
            password=hashed_password,
            role_id=super_admin_role.id
        )
        db.session.add(super_admin_user)
        db.session.commit()

    print("Database populated with initial data.")
