from app import app, db
from models import Student, Driver

with app.app_context():
    s = Student(name="Riya", email="riya@student.com", password="1234")
    d = Driver(name="Driver1", email="driver@van.com", password="1234")

    db.session.add_all([s, d])
    db.session.commit()

print("Dummy users added successfully")
