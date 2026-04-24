from flask import Flask, render_template, request, redirect, session
import sqlite3, os
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)

# 🔐 secret key (Render env)
app.secret_key = os.environ.get("SECRET_KEY", "fallback123")

# 🔒 cookie settings (Render HTTPS)
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_SAMESITE="None",
    SESSION_COOKIE_HTTPONLY=True,
)

# 🌐 proxy fix (Render)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
# DB create
def init_db():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            name TEXT,
            username TEXT UNIQUE,
            password TEXT,
            role TEXT
        )
    ''')

    # student table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY,
            name TEXT,
            regno TEXT,
            admission TEXT,
            year TEXT,
            dept TEXT,
            phone TEXT,
            parent TEXT,
            address TEXT,
            assignment TEXT,
            batch TEXT
        )
    ''')

    # staff table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS staff (
            id INTEGER PRIMARY KEY,
            name TEXT,
            dept TEXT,
            contact TEXT,
            position TEXT
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY,
            date TEXT,
            regno TEXT,
            status TEXT,
            year TEXT
        )
    ''')

    conn.commit()
    conn.close()

# call DB init
init_db()


@app.route('/')
def root():
    return redirect('/login')


@app.route('/register')
def register_page():
    return render_template("register.html")


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/dashboard')
def dashboard():
    return render_template("dashboard.html")


@app.route('/register', methods=['POST'])
def register():
    name = request.form['name']
    username = request.form['username']
    password = request.form['password']
    role = request.form['role']

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # check existing user
    cur.execute("SELECT * FROM users WHERE username=?", (username,))
    existing_user = cur.fetchone()

    if existing_user:
        conn.close()
        return render_template("register.html", error="User already registered!")

    cur.execute("INSERT INTO users (name, username, password, role) VALUES (?, ?, ?, ?)",
                (name, username, password, role))

    conn.commit()
    conn.close()

    return redirect('/login')


@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')
    role = request.form.get('role')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM users WHERE username=? AND password=? AND role=?",
        (username, password, role)
    )
    user = cur.fetchone()

    print("USER:", user)

    if user:
        session.clear()
        session["role"] = role
        session["username"] = username

        print("SESSION SET:", dict(session))  # 🔥

        conn.close()
        return redirect('/home')

    conn.close()
    print("LOGIN FAILED")
    return render_template("login.html", error="Invalid login")

    




@app.route("/add_student", methods=["POST"])
def add_student():

    year = request.form.get("year")

    conn = sqlite3.connect("users.db")   # 🔥 FIX HERE
    cur = conn.cursor()

    cur.execute("""
    INSERT INTO students
    (name, regno, admission, year, dept, phone, parent, address, assignment, batch)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        request.form["name"],
        request.form["regno"],
        request.form["admission"],
        year,
        request.form["dept"],
        request.form["phone"],
        request.form["parent"],
        request.form["address"],
        request.form["assignment"],
        request.form["batch_year"]
    ))

    conn.commit()
    conn.close()

    if year == "1":
        return redirect("/first_year")
    else:
        return redirect("/second_year")


@app.route('/add_staff', methods=['POST'])
def add_staff():
    data = tuple(request.form.values())

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("INSERT INTO staff VALUES (NULL,?,?,?,?)", data)

    conn.commit()
    conn.close()

    return redirect('/staff')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/home')
def home():
    print("SESSION IN HOME:", dict(session))  # 🔥

    if not session.get("role"):
        return redirect('/login')

    return render_template("home.html")


@app.route('/first_year', methods=['GET', 'POST'])
def first_year():

    selected_year = request.form.get('filter_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if selected_year:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("1", selected_year)
        )
    else:
        cur.execute(
            "SELECT * FROM students WHERE year=?",
            ("1",)
        )

    students = cur.fetchall()
    conn.close()

    return render_template("first_year.html", students=students)


@app.route('/second_year', methods=['GET', 'POST'])
def second_year():

    selected_year = request.form.get('filter_year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if selected_year:
        cur.execute(
            "SELECT * FROM students WHERE year=? AND batch=?",
            ("2", selected_year)
        )
    else:
        cur.execute(
            "SELECT * FROM students WHERE year=?",
            ("2",)
        )

    students = cur.fetchall()
    conn.close()

    return render_template("second_year.html", students=students)


@app.route('/staff')
def staff():
    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT * FROM staff")
    staff_list = cur.fetchall()

    conn.close()

    return render_template("staff.html", staff=staff_list)


from datetime import date

from datetime import date

# 🔥 ATTENDANCE PAGE
@app.route('/attendance')
def attendance():

    today = date.today()

    # 🔥 student login → no student list load
    if session.get("role") == "student":
        return render_template(
            "attendance.html",
            today=today,
            role="student"
        )

    # 🔥 staff login → allow year selection
    year = request.args.get('year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    if year:
        cur.execute(
            "SELECT name, regno FROM students WHERE year=? ORDER BY name",
            (year,)
        )
        students = cur.fetchall()
    else:
        students = []

    conn.close()

    return render_template(
        "attendance.html",
        students=students,
        today=today,
        selected_year=year,
        role="staff"
    )


# 🔥 SAVE ATTENDANCE (STAFF ONLY)
@app.route('/save_attendance', methods=['POST'])
def save_attendance():

    if session.get("role") != "staff":
        return "Access Denied"

    date_val = request.form.get('date')
    year = request.form.get('year')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    cur.execute("SELECT regno FROM students WHERE year=?", (year,))
    students = cur.fetchall()

    for s in students:
        regno = s[0]

        status = "Present" if f"present_{regno}" in request.form else "Absent"

        cur.execute(
            "INSERT INTO attendance (date, regno, status, year) VALUES (?, ?, ?, ?)",
            (date_val, regno, status, year)
        )

    conn.commit()
    conn.close()

    return redirect('/attendance?year=' + year)


# 🔥 SEARCH ATTENDANCE (SECURE)
@app.route('/search_attendance', methods=['POST'])
def search_attendance():

    search_date = request.form.get('date')

    conn = sqlite3.connect("users.db")
    cur = conn.cursor()

    # 🔥 STUDENT → OWN DATA ONLY
    if session.get("role") == "student":

        cur.execute('''
        SELECT date, status 
        FROM attendance
        WHERE date=? AND regno=?
        ''', (search_date, session.get("regno")))

        records = cur.fetchall()

        conn.close()

        return render_template(
            "attendance.html",
            records=records,
            role="student"
        )

    # 🔥 STAFF → FULL DATA
    cur.execute('''
    SELECT students.name, attendance.regno, attendance.status, attendance.date
    FROM attendance
    JOIN students ON attendance.regno = students.regno
    WHERE attendance.date=?
    ''', (search_date,))

    records = cur.fetchall()

    conn.close()

    return render_template(
        "attendance.html",
        records=records,
        role="staff"
    )
    
import os
from flask import request, redirect, send_from_directory

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.context_processor
def inject_data():
    return dict(show_result=show_result)

@app.route("/upload", methods=["POST"])
def upload():
    if session.get("role") != "staff":
        return "Access Denied"

    file = request.files["file"]
    file.save(os.path.join(app.config["UPLOAD_FOLDER"], file.filename))
    return redirect("/materials")

@app.route("/download/<filename>")
def download(filename):
    return send_from_directory("uploads", filename, as_attachment=True)

@app.route("/timetable", methods=["GET","POST"])
def timetable():
    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        file = request.files["image"]
        file.save("static/timetable.png")

    return render_template("timetable.html")

announcements = []

@app.route("/announcement", methods=["GET","POST"])
def announcement():
    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        file = request.files["image"]
        filename = file.filename
        file.save("static/" + filename)

        from datetime import date
        announcements.append((filename, str(date.today())))

    return render_template("announcement.html", data=announcements[::-1])

results = []
show_result = False   # 🔥 control

@app.route("/result", methods=["GET","POST"])
def result():
    global show_result

    if request.method == "POST":
        if session.get("role") != "staff":
            return "Access Denied"

        name = request.form["name"]
        mark = request.form["mark"]
        results.append((name, mark))

    return render_template("result.html", results=results, show=show_result)

from flask import flash

show_result = False

@app.route("/enable_result")
def enable_result():
    global show_result
    if session.get("role") == "staff":
        show_result = True
        flash("Result Enabled Successfully ✅")
    return redirect("/result")


@app.route("/disable_result")
def disable_result():
    global show_result
    if session.get("role") == "staff":
        show_result = False
        flash("Result Disabled Successfully ❌")
    return redirect("/result")


@app.route("/add_student_page")
def add_student_page():
    year = request.args.get("year")
    return render_template("add_student.html", year=year)




# 🚀 RUN
if __name__ == "__main__":
    app.run()
