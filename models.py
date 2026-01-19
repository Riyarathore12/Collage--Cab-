from flask_sqlalchemy import SQLAlchemy
from datetime import date, datetime
from werkzeug.security import generate_password_hash, check_password_hash

from sqlalchemy import MetaData
from flask_sqlalchemy import SQLAlchemy

# Naming convention define karein taaki SQLite error na de
convention = {
    "ix": 'ix_%(column_label)s',
    "sq": "sq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)
db = SQLAlchemy(metadata=metadata)


class Student(db.Model):
    __tablename__ = "student"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    route = db.Column(db.String(50))
    stop = db.Column(db.String(50))
    home_lat = db.Column(db.Float)
    assigned_van_id = db.Column(db.String(20), nullable=True)
    profile_pic = db.Column(db.String(200), default='default.png') # Ye zaroori hai
    home_lng = db.Column(db.Float)
    # email = db.Column(db.String(100)) # Naya Column
    # phone = db.Column(db.String(20))  # Naya Column
    attendances = db.relationship('Attendance', backref='student', lazy=True)
    status = db.Column(db.String(20), default="Absent") # Present, Delay, ya Absent
    delay_time = db.Column(db.Integer, default=0)       # Kitne min late hai
    last_update = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Driver(db.Model):
    __tablename__ = "driver"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    phone_number = db.Column(db.String(15), nullable=True)
    van_number = db.Column(db.String(20), nullable=False)
    def set_password(self, password):
        self.password = generate_password_hash(password)
    def check_password(self, password):
        return check_password_hash(self.password, password)

class Poll(db.Model):
    __tablename__ = "poll"
    id = db.Column(db.Integer, primary_key=True)
    poll_type = db.Column(db.String(20)) 
    poll_date = db.Column(db.Date, default=date.today)
    options = db.relationship('PollOption', backref='poll', lazy=True)

class PollOption(db.Model):
    __tablename__ = "poll_option"
    id = db.Column(db.Integer, primary_key=True)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"), nullable=False)
    time = db.Column(db.String(10))

class PollVote(db.Model):
    __tablename__ = "poll_vote"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    poll_id = db.Column(db.Integer, db.ForeignKey("poll.id"), nullable=False)
    option_id = db.Column(db.Integer, db.ForeignKey("poll_option.id"), nullable=False)
    # Relationship to get name and phone
    voter = db.relationship('Student', backref='votes')

class Attendance(db.Model):
    __tablename__ = "attendance"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    status = db.Column(db.String(20))
    delay_minutes = db.Column(db.Integer, default=0)
    date = db.Column(db.Date, default=date.today)

class Slot(db.Model):
    __tablename__ = "slot"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    start_time = db.Column(db.String(10))
    end_time = db.Column(db.String(10))

# Missing class that caused your error
class StudentSlot(db.Model):
    __tablename__ = "student_slot"
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student.id"), nullable=False)
    slot_id = db.Column(db.Integer, db.ForeignKey("slot.id"), nullable=False)
    date = db.Column(db.Date, default=date.today)

class VanLocation(db.Model):
    __tablename__ = "van_location"
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    van_id = db.Column(db.String(50), nullable=True)