from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    redirect,
    session,
    url_for,
    flash
)

import os
from werkzeug.utils import secure_filename
import math
from flask_migrate import Migrate
from datetime import date, timedelta, datetime
from flask_sqlalchemy import SQLAlchemy

# Ensure these models exist in your models.py!
from models import (
    db,
    Student,
    Driver,
    Poll,
    PollOption,
    PollVote,
    Attendance,
    StudentSlot,
    Slot,
    VanLocation
)
import random
from flask_mail import Mail, Message


app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
#app.config['MAIL_USERNAME'] = 'collage749@gmail.com' # Aapka email
#app.config['MAIL_PASSWORD'] = 'uewh zbvj rjfr xjsl'    # Google App Password
app.config['MAIL_DEFAULT_SENDER'] = 'collage749e@gmail.com'
mail = Mail(app)

# --- Configuration ---
if os.environ.get('VERCEL'):
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/database.db'
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=30)
app.secret_key = "college-van-secret-unique-key"
UPLOAD_FOLDER = 'static/profile_pics'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db.init_app(app)
migrate = Migrate(app, db)

# --- Initialization Helpers ---

def create_slots():
    if Slot.query.first():
        return
    slots = [
        ("Slot-1", "09:00", "10:00"),
        ("Slot-2", "10:00", "11:00"),
        ("Slot-3", "11:30", "1:00"),
        ("Slot-4", "2:00", "3:30"),
    ]
    for name, start, end in slots:
        db.session.add(Slot(name=name, start_time=start, end_time=end))
    db.session.commit()

def create_tomorrow_polls():
    tomorrow = date.today() + timedelta(days=1)
    if Poll.query.filter_by(poll_date=tomorrow).first():
        return
    
    m_poll = Poll(poll_type="morning", poll_date=tomorrow)
    db.session.add(m_poll)
    db.session.commit()
    # Timings ke saath AM/PM add karein
    for t in ["07:15 AM", "09:00 AM", "10:40 AM", "12:15 PM", "02:00 PM"]:
        db.session.add(PollOption(poll_id=m_poll.id, time=t))

    r_poll = Poll(poll_type="return", poll_date=tomorrow)
    db.session.add(r_poll)
    db.session.commit()
    # Timings ke saath AM/PM add karein
    for t in ["10:00 AM", "11:40 AM", "01:30 PM", "03:00 PM", "04:30 PM", "06:00 PM", "07:30 PM"]:
        db.session.add(PollOption(poll_id=r_poll.id, time=t))
        
    db.session.commit()

def get_target_date():
    """7:45 PM ke baad 'Kal' ki date dega, pehle 'Aaj' ki."""
    now = datetime.now()
    # 19:45 = 7:45 PM
    if now.hour > 19 or (now.hour == 19 and now.minute >= 45):
        return date.today() + timedelta(days=1)
    return date.today()

from datetime import datetime

def reset_daily_data():
    now = datetime.now()
    # Shaam ke 7:45 PM ka cutoff
    cutoff_time = now.replace(hour=19, minute=45, second=0, microsecond=0)
    
    # Agar abhi ka time 7:45 PM se zyada hai
    if now > cutoff_time:
        # Sabhi students ka status aur delay clear kar do
        students = Student.query.all()
        for s in students:
            s.status = None        # "PRESENT" ya "LATE" sab hat jayega
            s.delay_time = 0
        db.session.commit()


def get_distance(lat1, lon1, lat2, lon2):
    if None in [lat1, lon1, lat2, lon2]: return 999
    radius = 6371 # km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    return radius * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

# --- Auth Routes ---





@app.route("/")
def home():
    return render_template("index.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('home'))

@app.route('/driver-register', methods=['GET', 'POST'])
def driver_register():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')  # Ensure this matches name="email" in HTML
        phone = request.form.get('phone')
        vehicle_no = request.form.get('vehicle_no')
        password = request.form.get('password')

        # Safety check: email null nahi hona chahiye
        if not email:
            flash("Email is required!", "error")
            return redirect(url_for('driver_register'))

        if Driver.query.filter_by(email=email).first():
            flash("Driver already registered!", "error")
            return redirect(url_for('driver_register'))

        new_driver = Driver(
            name=name, 
            email=email, 
            phone_number=phone, 
            van_number=vehicle_no
        )
        new_driver.set_password(password)
        db.session.add(new_driver)
        db.session.commit()
        return redirect(url_for('driver_login'))
    return render_template('driver_register.html')

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name, email = request.form.get("name"), request.form.get("email")
        pwd, phone = request.form.get("password"), request.form.get("phone")
        van_no = request.form.get('assigned_van_id').strip().upper()
        lat, lng = request.form.get("latitude"), request.form.get("longitude")
        
        if Student.query.filter_by(email=email).first():
            flash("Email already registered!", "error")
            return redirect(url_for('register'))
            
        new_student = Student(
            name=name, email=email, phone_number=phone,
            latitude=float(lat) if lat else None,
            longitude=float(lng) if lng else None,
            assigned_van_id=van_no
            
        )
        new_student.set_password(pwd)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('student_login'))
    return render_template("student_register.html")

@app.route("/student-login", methods=["GET", "POST"])
def student_login():
    if request.method == "POST":
        email, pwd = request.form.get("email"), request.form.get("password")
        student = Student.query.filter_by(email=email).first()
        if student and student.check_password(pwd):
            session.permanent = True
            session["student_id"] = student.id
            session["user_name"] = student.name
            return redirect(url_for('attendance_page'))
        flash("Invalid credentials", "error")
    return render_template("student_login.html")

@app.route("/profile", methods=["GET", "POST"])
def profile_page():
    student_id = session.get('student_id')
    if not student_id: return redirect(url_for('student_login'))
    
    student = Student.query.get(student_id) # Purana data fetch karein
    
    if request.method == "POST":
        # 1. Text data update karein
        student.name = request.form.get("name")
        student.phone_number = request.form.get("phone")
        
        # 2. File handle karein
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file and file.filename != '':
                filename = secure_filename(f"user_{student.id}_{file.filename}")
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                student.profile_pic = filename # DB mein filename save karein
        
        db.session.commit() # Changes save karein
        session["user_name"] = student.name
        return redirect(url_for('attendance_page'))
        
    return render_template("profile.html", student=student)
# --- Student Functionality ---

@app.route('/attendance-page')
def attendance_page():
    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    
    # Ye check karein ki abhi Morning hai ya Return
    # Maan lijiye 12:00 PM ke baad return journey hai
    from datetime import datetime
    is_morning = datetime.now().hour < 12 
    
    return render_template("attendance.html", student=student, is_morning=is_morning)

@app.route('/attendance/<int:student_id>/<status_type>')
def mark_attendance(student_id, status_type):
    student = Student.query.get(student_id)
    if not student: return "Student not found", 404

    if status_type == "present":
        student.status = "Present"
        student.delay_time = 0
    elif "delay" in status_type:
        # delay-1, delay-2 format se number nikaalein
        minutes = int(status_type.split('-')[1])
        student.status = f"Late ({minutes}m)"
        student.delay_time = minutes
    
    student.last_update = datetime.utcnow()
    db.session.commit()
    return redirect(url_for('attendance_page'))

# --- Update these two functions in your app.py ---
@app.route("/slot")
def slot_page():
    student_id = session.get('student_id')
    if not student_id: return redirect(url_for('student_login'))
    
    student = Student.query.get(student_id)
    # Student ki apni van ka ID
    my_van_id = student.assigned_van_id 

    target_date = get_target_date() 
    morning_poll = Poll.query.filter_by(poll_type="morning", poll_date=target_date).first()
    
    poll_options = []
    user_voted_id = None

    if morning_poll:
        # User ka apna vote check karne ke liye
        existing_vote = PollVote.query.filter_by(student_id=student_id, poll_id=morning_poll.id).first()
        user_voted_id = existing_vote.option_id if existing_vote else None

        # Saare options loop karein
        for opt in morning_poll.options:
            # FIX: Filter voters by the student's assigned van ID only
            voters_data = db.session.query(Student.name, Student.phone_number)\
                .join(PollVote, Student.id == PollVote.student_id)\
                .filter(PollVote.option_id == opt.id, Student.assigned_van_id == my_van_id)\
                .all()
            
            voters_list = [{"name": name, "phone": phone} for name, phone in voters_data]
            
            # Percentage calculate karne ke liye sirf is van ke total votes chahiye
            van_total_votes = db.session.query(PollVote).join(Student)\
                .filter(PollVote.poll_id == morning_poll.id, Student.assigned_van_id == my_van_id).count()

            poll_options.append({
                'id': opt.id, 
                'time': opt.time, 
                'count': len(voters_list),
                'voters': voters_list,
                'percent': (len(voters_list) / van_total_votes * 100) if van_total_votes > 0 else 0
            })

    return render_template("slot_selection.html", 
                           options=poll_options, 
                           user_voted_id=user_voted_id, 
                           day_name=target_date.strftime('%A'),
                           display_date=target_date.strftime('%d %b'))


@app.route("/return-poll/<int:student_id>")
def return_poll(student_id):
    if "student_id" not in session or session["student_id"] != student_id:
        return redirect(url_for('student_login'))

    target_date = get_target_date()
    poll = Poll.query.filter_by(poll_type="return", poll_date=target_date).first()
    
    poll_options = []
    total_votes = 0
    user_voted_id = None

    if poll:
        total_votes = PollVote.query.filter_by(poll_id=poll.id).count()
        existing_vote = PollVote.query.filter_by(student_id=student_id, poll_id=poll.id).first()
        user_voted_id = existing_vote.option_id if existing_vote else None

        for opt in poll.options:
            voters_data = PollVote.query.filter_by(option_id=opt.id).all()
            voters_list = [{"name": v.voter.name, "phone": v.voter.phone_number} for v in voters_data]
            
            poll_options.append({
                'id': opt.id, 
                'time': opt.time, 
                'count': len(voters_list),
                'voters': voters_list,
                'percent': (len(voters_list) / total_votes * 100) if total_votes > 0 else 0
            })

    return render_template("return_poll.html", 
                           options=poll_options, 
                           user_voted_id=user_voted_id, 
                           day_name=target_date.strftime('%A'),
                           display_date=target_date.strftime('%d %b'))

@app.route('/vote/<int:option_id>')
def vote(option_id):
    student_id = session.get('student_id')
    if not student_id: return redirect(url_for('student_login'))

    option = db.session.get(PollOption, option_id)
    if not option: return redirect(url_for('attendance_page'))
    
    existing_vote = PollVote.query.filter_by(student_id=student_id, poll_id=option.poll_id).first()
    if existing_vote: db.session.delete(existing_vote)
    
    new_vote = PollVote(student_id=student_id, poll_id=option.poll_id, option_id=option_id)
    db.session.add(new_vote)
    db.session.commit()
    
    parent_poll = db.session.get(Poll, option.poll_id)
    if parent_poll.poll_type == "morning":
        return redirect(url_for('slot_page'))
    return redirect(url_for('return_poll', student_id=student_id))

# --- Driver Routes ---


@app.route("/driver-login", methods=["GET", "POST"])
def driver_login():
    if request.method == "POST":
        email, pwd = request.form.get("email"), request.form.get("password")
        driver = Driver.query.filter_by(email=email).first()
        if driver and driver.check_password(pwd):
            session["driver_id"] = driver.id
            session["van_number"] = driver.van_number
            return redirect(url_for('driver_ui'))
        flash("Invalid credentials", "error")
    return render_template("driver_login.html")


@app.route('/driver-ui')
def driver_ui():
    target_date = get_target_date()
    formatted_date = target_date.strftime('%A, %d %b %Y')
    
    # 1. 7:45 PM Reset logic call
    reset_daily_data() 
    
    # 2. Driver ka Van Number session se lein
    driver_van = session.get('van_number')
    
    polls = Poll.query.filter(Poll.poll_date == target_date).all()
    
    if not polls and target_date > date.today():
        create_tomorrow_polls()
        polls = Poll.query.filter(Poll.poll_date == target_date).all()

    driver_loc = VanLocation.query.order_by(VanLocation.timestamp.desc()).first()
    driver_poll_data = []
    
    for poll in polls:
        options_list = []
        is_morning = poll.poll_type.lower() == 'morning'
        
        for opt in poll.options:
            # --- FIX: Yahan filter lagaya hai taaki sirf driver ki van ke bache dikhen ---
            voted_students = db.session.query(
                Student.name, 
                Student.phone_number, 
                Student.latitude, 
                Student.longitude,
                Student.status,
                Student.delay_time
            ).join(PollVote).filter(
                PollVote.option_id == opt.id,
                Student.assigned_van_id == driver_van  # <--- YE LINE SABSE IMPORTANT HAI
            ).all()

            student_details = []
            for s_name, s_phone, s_lat, s_lng, s_status, s_delay in voted_students:
                dist = 999
                if driver_loc and s_lat is not None and s_lng is not None:
                    dist = get_distance(driver_loc.latitude, driver_loc.longitude, s_lat, s_lng)
                
                # Logic: Morning mein Late dikhao, Return mein sab fresh/empty
                if is_morning:
                    display_status = s_status if s_status else ""
                else:
                    display_status = "" 

                student_details.append({
                    'name': s_name, 
                    'phone': s_phone, 
                    'status': display_status, 
                    'delay': s_delay if is_morning else 0,
                    'is_nearby': dist <= 0.3 
                })
            
            options_list.append({
                'time': opt.time, 
                'students': student_details, 
                'count': len(student_details)
            })
            
        driver_poll_data.append({
            'type': poll.poll_type.capitalize(), 
            'options': options_list
        })
    
    return render_template('driver_dashboard.html', polls=driver_poll_data, date=formatted_date)

@app.route('/get-van-location')
def get_van_location():
    student_id = session.get('student_id')
    student = Student.query.get(student_id)
    # Latest van location database se nikaalein
    van_loc = VanLocation.query.filter_by(van_id=student.assigned_van_id).order_by(VanLocation.timestamp.desc()).first()
    if van_loc:
        return {"lat": van_loc.latitude, "lng": van_loc.longitude}
    return {"lat": None, "lng": None}

@app.route("/track-van")
def track_van():
    location = VanLocation.query.order_by(VanLocation.timestamp.desc()).first()
    if not location:
        return render_template("van_location.html", lat=21.2514, lng=81.6296, time=datetime.now())
    return render_template("van_location.html", lat=location.latitude, lng=location.longitude, time=location.timestamp)
    
@app.route("/update-location", methods=["POST"])
def update_location():
    driver_id = session.get('driver_id')
    if not driver_id:
        return jsonify({"status": "error", "message": "Not logged in"}), 401
    data = request.get_json()
    driver = Driver.query.get(driver_id)
    data = request.get_json()
    new_loc = VanLocation(latitude=data['lat'], longitude=data['lng'], timestamp=datetime.now(),van_id=driver.van_number)
    db.session.add(new_loc)
    db.session.commit()
    return jsonify({"status": "success"})


from werkzeug.security import generate_password_hash, check_password_hash
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('identifier')
        student = Student.query.filter_by(email=email).first()

        if student:
            # 6-digit ka random password banayein
            temp_pw = str(random.randint(100000, 999999))
            student.password = generate_password_hash(temp_pw)
            db.session.commit()

            try:
                msg = Message("Password Reset - College Cab",
                              recipients=[student.email])
                msg.body = f"Hello,\n\nAapka temporary password reset kar diya gaya hai.\nNaya Password: {temp_pw}\n\nKripya login karne ke baad ise badal lein."
                mail.send(msg)
                flash("Naya password aapki email par bhej diya gaya hai!", "success")
                return redirect(url_for('student_login'))
            except Exception as e:
                flash(f"Mail bhejne mein error aaya. Error: {str(e)}", "danger")
        else:
            flash("Ye email hamare record mein nahi hai.", "danger")
            
    return render_template('forgot_password.html')


@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if 'student_id' not in session:
        return redirect(url_for('student_login'))
    
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        student = Student.query.get(session['student_id'])
        
        # 1. Purana password check karein
        if not check_password_hash(student.password, old_password):
            flash("Purana password galat hai!", "danger")
        # 2. Confirm password match karein
        elif new_password != confirm_password:
            flash("Naya password aur Confirm password match nahi ho rahe!", "danger")
        # 3. Password update karein
        else:
            student.password = generate_password_hash(new_password)
            db.session.commit()
            flash("Password kamyabi se badal diya gaya hai!", "success")
            return redirect(url_for('student_dashboard'))
            
    return render_template('change_password.html')


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_slots()
        create_tomorrow_polls()
    app.run(host='0.0.0.0', port=5000, debug=True)