from app import app, db
# Import all your models so SQLAlchemy knows what to create
from models import Student, Driver, Attendance, Poll, PollOption, PollVote, Slot, StudentSlot, VanLocation

with app.app_context():
    print("Dropping all existing tables...")
    db.drop_all()
    print("Creating all tables with new columns (including van_number)...")
    db.create_all()
    print("Done! Now restart your app and try registering.")