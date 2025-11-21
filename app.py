from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from flask_mysqldb import MySQL
import random
import MySQLdb.cursors
import json

from datetime import datetime
import pytz



from dotenv import load_dotenv
load_dotenv()
import os


import resend

resend.api_key=os.getenv("apikeyforresend")




app = Flask(__name__)



app.secret_key = "djsofdsiofndjbngbdfklnerhbryjoweih2492304nr98tnunvhpkhrnjdibgirnrnrenivuchvchnasndssnkjvoiijfhfdhfhdsigjgdigkniojdngjgjigndjdjfghduenrjvidfjvidshguhernjiwp"

app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')
app.config['MYSQL_PORT'] = int(os.getenv('MYSQL_PORT', 3306))



# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'viveksinghald1050@gmail.com'   # your Gmail
# app.config['MAIL_PASSWORD'] = 'okqf idxe sfhw bauj'          # use Gmail App Password





mysql = MySQL(app)




def check_student_login():
    if 'student_id' not in session:
        flash("Please log in as student first.", "warning")
        return redirect(url_for("login"))
    return None


def check_instructor_login():
    if 'instructor_id' not in session:
        flash("Please log in as instructor first.", "warning")
        return redirect(url_for("loginforinstructor"))
    return None

def send_mail(to, subject, body):
    resend.Emails.send({
        "from": "no-reply@learnifyhub.space",
        "to": [to],
        "subject": subject,
        "html": f"<p>{body}</p>"
    })

# -------------------------
# Helpers
# -------------------------
def get_cursor(dict_cursor=False):
    if dict_cursor:
        return mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    return mysql.connection.cursor()

# -------------------------
# Routes
# -------------------------
@app.route('/', methods=['GET', 'POST'])
def mainhomepage():
    return render_template('mainhomepage.html')

@app.route('/aboutus', methods=['GET'])
def aboutus():
    return render_template("aboutus.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cur = get_cursor()
        try:
            cur.execute("SELECT * FROM Student WHERE email = %s", (email,))
            user = cur.fetchone()
        finally:
            cur.close()

        if user:
            # student table columns: (student_id, registration_no, name, email, password, section_name, year, questions_done)
            db_password = user[4]
            if db_password == password:
                student_id = user[0]
                student_email = user[3]
                student_name = user[2]

                session['student_email'] = student_email
                session['student_password'] = db_password
                session['student_id'] = student_id

                return redirect(url_for("view_subject_for_student", student_name=student_name))
            else:
                flash("Invalid password", "danger")
        else:
            flash("Email not found", "danger")

    return render_template("login.html")

@app.route('/loginforinstructor', methods=['GET', 'POST'])
def loginforinstructor():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        cur = get_cursor()
        try:
            cur.execute("SELECT * FROM Instructor WHERE email = %s", (email,))
            instructor = cur.fetchone()
        finally:
            cur.close()

        if instructor:
            # Instructor columns: (id, name, enrolment_id, email, password)
            db_password = instructor[4]
            if db_password == password:
                instructor_id = instructor[0]
                instructor_name = instructor[1]
                enrolment_id = instructor[2]
                instructor_email = instructor[3]

                session['instructor_id'] = instructor_id
                session['instructor_name'] = instructor_name
                session['enrolment_id'] = enrolment_id
                session['instructor_email'] = instructor_email

                return redirect(url_for("instructor_dashboard"))
            else:
                flash("Invalid password", "danger")
        else:
            flash("Email not found", "danger")

    return render_template("loginforinstructor.html")



@app.route('/regrestrationforstudent', methods=['GET', 'POST'])
def regrestrationforstudent():
    if request.method == "POST":
        registration_no = request.form.get("registration_no")
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_pass = request.form.get("confirm_password")
        section = request.form.get("section")
        year = request.form.get("year")
        section = section.strip().upper() if section else None

        if (password != confirm_pass):
            flash("Password Mismatch")
            return redirect(url_for('regrestrationforstudent'))

        cur = get_cursor()
        try:
            cur.execute("SELECT * FROM Student WHERE email = %s", (email,))
            existing_user = cur.fetchone()

            cur.execute("SELECT * FROM Student WHERE registration_no = %s", (registration_no,))
            regexit = cur.fetchone()
            if regexit:
                flash("Registration number already exists", "warning")
                return redirect(url_for('regrestrationforstudent'))

            if existing_user:
                flash("Email already registered. Please use a different email.", "danger")
                return redirect(url_for('regrestrationforstudent'))
            else:
                otp = str(random.randint(100000, 999999))
                session['otp'] = otp
                session['student_data'] = {
                    "registration_no": registration_no,
                    "name": name,
                    "email": email,
                    "password": password,
                    "section": section,
                    "year": year
                }

                # Send OTP Emai
                send_mail(
                            email,
                            "Welcome to Learnify – Your Registration OTP",
                            f"Welcome to Learnify!\n\nWe're excited to have you join our learning community. To complete your registration, please use the OTP below:\n\nYour OTP: {otp}\n\nIf you need any help, we’re always here for you.\n\nHappy learning!\nTeam Learnify"
                        )



                return render_template('verifymail.html')
        finally:
            cur.close()

    return render_template('regrestrationforstudetn.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == "POST":
        user_otp = request.form.get("otp")
        if user_otp == session.get('otp'):
            student_data = session.get('student_data')
            if not student_data:
                flash("Session expired. Please register again.", "danger")
                return redirect(url_for('regrestrationforstudent'))

            cur = get_cursor()
            try:
                cur.execute("""
                    INSERT INTO Student (registration_no, name, email, password, section_name, year)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    student_data["registration_no"],
                    student_data["name"],
                    student_data["email"],
                    student_data["password"], 
                    student_data["section"],
                    student_data["year"]
                ))
                mysql.connection.commit()
                session.pop('otp', None)
                session.pop('student_data', None)

                flash("Registration successful! You can now log in.", "success")
                return redirect(url_for('login'))
            finally:
                cur.close()
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('verify'))

    return render_template('verifymail.html')

@app.route('/resend_otp', methods=['GET'])
def resend_otp():
    student_data = session.get('student_data')
    if not student_data:
        flash("Session expired. Please register again.", "danger")
        return redirect(url_for('regrestrationforstudent'))

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp


    send_mail(student_data["email"], "Student Registration OTP (Resent)", f"Your new OTP is {otp}")


    flash("A new OTP has been sent to your email.", "info")
    return redirect(url_for('verify'))

@app.route('/regrestrationforinstructor', methods=['GET', 'POST'])
def regrestrationforinstructor():
    if request.method == 'POST':
        name = request.form.get("name")
        enroll_id = request.form.get("enroll_id")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('regrestrationforinstructor'))

        cur = get_cursor()
        try:
            cur.execute("SELECT * FROM EnrolmentID WHERE enrolment_id=%s AND is_used=FALSE", (enroll_id,))
            enrol = cur.fetchone()
        finally:
            cur.close()

        if not enrol:
            flash("Invalid or already used Enrollment ID", "error")
            return redirect(url_for('regrestrationforinstructor'))

        otp = str(random.randint(100000, 999999))
        session['otp'] = otp
        session['instructor_data'] = {
            "name": name,
            "enrol_id": enroll_id,
            "email": email,
            "password": password   # TODO: hash
        }
        send_mail(email, "Instructor OTP", f"Your OTP is {otp}")


        flash("An OTP has been sent to your email. Please verify.", "info")
        return redirect(url_for('verify_instructor'))

    return render_template("regestrationforinstructor.html")

@app.route('/verify_instructor', methods=['GET', 'POST'])
def verify_instructor():
    if request.method == "POST":
        user_otp = request.form.get("otp")
        if user_otp == session.get('otp'):
            instructor_data = session.get('instructor_data')
            if not instructor_data:
                flash("Session expired. Please register again.", "danger")
                return redirect(url_for('regrestrationforinstructor'))

            cur = get_cursor()
            try:
                cur.execute("""
                    INSERT INTO Instructor (name, enrolment_id, email, password)
                    VALUES (%s, %s, %s, %s)
                """, (
                    instructor_data["name"],
                    instructor_data["enrol_id"],
                    instructor_data["email"],
                    instructor_data["password"]
                ))
                mysql.connection.commit()

                cur.execute("""
                    UPDATE EnrolmentID
                    SET is_used = TRUE
                    WHERE enrolment_id = %s
                """, (instructor_data["enrol_id"],))
                mysql.connection.commit()

                session.pop('otp', None)
                session.pop('instructor_data', None)

                flash("Instructor registration successful! You can now log in.", "success")
                return redirect(url_for('loginforinstructor'))
            finally:
                cur.close()
        else:
            flash("Invalid OTP. Please try again.", "danger")
            return redirect(url_for('verify_instructor'))

    return render_template('verifymail_instructor.html')

@app.route('/resend_otp_instructor', methods=['GET'])
def resend_otp_instructor():
    instructor_data = session.get('instructor_data')
    if not instructor_data:
        flash("Session expired. Please register again.", "danger")
        return redirect(url_for('regrestrationforinstructor'))

    otp = str(random.randint(100000, 999999))
    session['otp'] = otp
    send_mail(instructor_data["email"], "Resent Instructor OTP", f"Your OTP is {otp}")


    flash("A new OTP has been sent to your email.", "info")
    return redirect(url_for('verify_instructor'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email")

        cur = get_cursor(dict_cursor=True)
        try:
            query = """
                SELECT 'student' as role, student_id as id, email FROM Student WHERE email=%s
                UNION
                SELECT 'instructor' as role, id as id, email FROM Instructor WHERE email=%s
            """
            cur.execute(query, (email, email))
            user = cur.fetchone()
        finally:
            cur.close()

        if not user:
            flash("Email not found!", "danger")
            return redirect(url_for('forgot_password'))

        otp = str(random.randint(100000, 999999))
        session['reset_otp'] = otp
        session['reset_email'] = email
        session['reset_role'] = user['role']

        send_mail(email, "Password Reset OTP", f"Your OTP is {otp}")



        flash("OTP sent to your email!", "info")
        return redirect(url_for('verify_reset_otp'))

    return render_template("forgetpassword.html")

@app.route('/verify_reset_otp', methods=['GET', 'POST'])
def verify_reset_otp():
    email = session.get('reset_email')
    if request.method == "POST":
        entered_otp = request.form.get("otp")
        if entered_otp == session.get('reset_otp'):
            flash("OTP verified! Please enter a new password.", "success")
            return redirect(url_for('reset_password'))
        else:
            flash("Invalid OTP!", "danger")
            return redirect(url_for('verify_reset_otp'))

    return render_template("verify_reset_otp.html", email=email)

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if request.method == "POST":
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('reset_password'))

        email = session.get('reset_email')
        role = session.get('reset_role')

        cur = get_cursor()
        try:
            if role == "student":
                cur.execute("UPDATE Student SET password=%s WHERE email=%s", (new_password, email))
            else:
                cur.execute("UPDATE Instructor SET password=%s WHERE email=%s", (new_password, email))
            mysql.connection.commit()
        finally:
            cur.close()

        session.pop('reset_email', None)
        session.pop('reset_otp', None)
        session.pop('reset_role', None)

        flash("Password reset successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template("reset_password.html")

@app.route('/instructor_dashboard')
def instructor_dashboard():
    check = check_instructor_login()
    if check: return check
  

    cur = get_cursor()
    try:
        cur.execute("SELECT section_id, section_name FROM Section")
        sections = cur.fetchall()
    finally:
        cur.close()

    return render_template(
        "instructor_section_dashboard.html",
        sections=sections,
        name=session.get('instructor_name'),
        enrolment_id=session.get('enrolment_id'),
        email=session.get('instructor_email')
    )

@app.route('/add_section_instructor', methods=['GET', 'POST'])
def add_section_instructor():
    check = check_instructor_login()
    if check: return check
    if request.method == "POST":
        section_name = request.form.get("section_name")
        if not section_name:
            flash("Section name is required.", "danger")
            return redirect(url_for('add_section_instructor'))
        section_name = section_name.strip().upper()

        cur = get_cursor()
        try:
            cur.execute("SELECT 1 FROM Section WHERE section_name = %s", (section_name,))
            existing = cur.fetchone()
            if existing:
                flash("Section already exists.", "warning")
                return redirect(url_for("instructor_dashboard"))

            cur.execute("INSERT INTO Section (section_name) VALUES (%s)", (section_name,))
            mysql.connection.commit()
            flash("Section added successfully!", "success")
            return redirect(url_for("instructor_dashboard"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
            return redirect(url_for("add_section_instructor"))
        finally:
            cur.close()

    return render_template("instuctor_add_section.html")

@app.route('/particularsectionforinstructor/<int:section_id>/<string:section_name>', methods=['GET', 'POST'])
def particularsectionforinstructor(section_id, section_name):
    check = check_instructor_login()
    if check: return check
    instructor_id = session.get('instructor_id')
    if not instructor_id:
        flash("You must be logged in as an instructor to view this page.")
        return redirect(url_for('login'))

    cursor = get_cursor()
    try:
        query = """
            SELECT * 
            FROM Subject 
            WHERE section_id = %s AND instructor_id = %s
        """
        cursor.execute(query, (section_id, instructor_id))
        subjects = cursor.fetchall()
    finally:
        cursor.close()

    return render_template(
        "particularsectionforinstructor.html",
        section_id=section_id,
        subjects=subjects,
        section_name=section_name
    )

@app.route('/addsubjectinstructor/<int:section_id>/<string:section_name>', methods=['GET','POST'])
def addsubjectinstructor(section_id, section_name):
    check = check_instructor_login()
    if check: return check
    if request.method == 'POST':
        subject_name = request.form.get("subject_name")
        subject_name = subject_name.strip().upper()

        instructor_id = session.get("instructor_id")
        if not instructor_id:
            return redirect(url_for('login'))

        cursor = get_cursor()
        try:
            cursor.execute("""
                SELECT * FROM Subject 
                WHERE subject_name = %s AND section_id = %s AND instructor_id = %s
            """, (subject_name, section_id, instructor_id))
            existing_subject = cursor.fetchone()
            if existing_subject:
                cursor.close()
                return render_template(
                    "addsubjectinstructor.html", 
                    section_id=section_id, 
                    section_name=section_name, 
                    error="⚠️ Subject already present in this section!"
                )

            cursor.execute(
                "INSERT INTO Subject (subject_name, section_id, instructor_id) VALUES (%s, %s, %s)", 
                (subject_name, section_id, instructor_id)
            )
            mysql.connection.commit()
        finally:
            cursor.close()

        return redirect(url_for('particularsectionforinstructor', section_id=section_id, section_name=section_name))

    return render_template("addsubjectinstructor.html", section_id=section_id, section_name=section_name)

@app.route('/teacher_view_question/<int:subject_id>/<string:section_name>', methods=['GET', 'POST'])
def teacher_view_question(subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    cursor = get_cursor(dict_cursor=True)
    try:
        # total students in section (avoid division by zero)
        cursor.execute("SELECT COUNT(*) as cnt FROM Student WHERE section_name = %s", (section_name,))
        total_students_row = cursor.fetchone()
        total_students = total_students_row['cnt'] if total_students_row else 0
        if total_students == 0:
            total_students = 1  # to avoid division by zero; progress will be 0 if none solved

        query = """
            SELECT q.q_id,
                   q.question_name,
                   q.level_of_question,
                   (SUM(CASE WHEN qd.question_done = 1 THEN 1 ELSE 0 END) / %s) * 100 AS progress_percent
            FROM Question q
            LEFT JOIN QuestionDone qd 
                ON q.q_id = qd.question_id
            WHERE q.subject_id = %s
            GROUP BY q.q_id, q.question_name, q.level_of_question
        """
        cursor.execute(query, (total_students, subject_id))
        questions = cursor.fetchall()
    finally:
        cursor.close()

    return render_template("questiondashboardteacher.html",
                           subject_id=subject_id,
                           section_name=section_name,
                           questions=questions)

@app.route('/add_question/<int:subject_id>/<string:section_name>', methods=['POST','GET'])
def add_question(subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    if request.method == 'POST':
        question_name = request.form.get('question_name')
        question_link = request.form.get('question_link')
        level_of_question = request.form.get('level_of_question')
        notes_of_question = request.form.get('notes_of_question')

        cursor = get_cursor()
        try:
            cursor.execute("""
                INSERT INTO Question (question_name, question_link, level_of_question, notes_of_question, subject_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (question_name, question_link, level_of_question, notes_of_question, subject_id))
            mysql.connection.commit()
        finally:
            cursor.close()

        return redirect(url_for('teacher_view_question', subject_id=subject_id, section_name=section_name))
    return render_template('addquestionteacher.html', subject_id=subject_id, section_name=section_name)

@app.route('/editquestionbyteacher/<int:q_id>/<string:q_name>/<int:subject_id>/<string:section_name>', methods=['POST', 'GET'])
def editquestionbyteacher(q_id, q_name, subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    if request.method == 'POST':
        new_notes = request.form.get('notes')
        cur = get_cursor()
        try:
            cur.execute("UPDATE Question SET notes_of_question=%s WHERE q_id=%s", (new_notes, q_id))
            mysql.connection.commit()
        finally:
            cur.close()
        flash("Notes update Successfully!", "success")
        return redirect(url_for("teacher_view_question", section_name=section_name, subject_id=subject_id))

    cur = get_cursor()
    try:
        cur.execute("SELECT notes_of_question FROM Question WHERE q_id=%s", (q_id,))
        result = cur.fetchone()
        notes_of_question = result[0] if result else ""
    finally:
        cur.close()

    return render_template('editquestionbyteacher.html', q_id=q_id, q_name=q_name, notes_of_question=notes_of_question, section_name=section_name, subject_id=subject_id)

@app.route('/deletequestion/<int:subject_id>/<string:section_name>/<int:q_id>', methods=['POST'])
def deletequestion(subject_id, section_name, q_id):
    check = check_instructor_login()
    if check: return check
    cur = get_cursor()
    try:
        cur.execute("DELETE FROM Question WHERE q_id=%s", (q_id,))
        mysql.connection.commit()
    finally:
        cur.close()

    flash("Question deleted successfully", "success")
    return redirect(url_for("teacher_view_question", section_name=section_name, subject_id=subject_id))

@app.route('/view_subject_for_student/<string:student_name>', methods=['GET', 'POST'])
def view_subject_for_student(student_name):
    check = check_student_login()
    if check: return check
    if 'student_email' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for("login"))

    student_id = session['student_id']
    cur = get_cursor()
    try:
        cur.execute("SELECT section_name FROM Student WHERE student_id = %s", (student_id,))
        student_section = cur.fetchone()
        if not student_section:
            flash("Section not found for this student.", "danger")
            return redirect(url_for("login"))
        section_name = student_section[0]

        cur.execute("SELECT section_id, section_name FROM Section WHERE section_name = %s", (section_name,))
        section_row = cur.fetchone()
        if not section_row:
            flash("Section not found in section table.", "danger")
            return redirect(url_for("login"))
        section_id, confirmed_section_name = section_row

        cur.execute("SELECT subject_id, subject_name, instructor_id FROM Subject WHERE section_id = %s", (section_id,))
        subjects = cur.fetchall()
    finally:
        cur.close()

    return render_template(
        "view_subject_for_student.html",
        subjects=subjects,
        section_name=confirmed_section_name,
        student_name=student_name
    )

@app.route('/view_question_for_student/<string:section_name>/<int:subject_id>/<string:subject_name>', methods=['GET', 'POST'])
def view_question_for_student(section_name, subject_id, subject_name):
    check = check_student_login()
    if check: return check
    student_id = session.get("student_id")
    cursor = get_cursor()
    try:
        cursor.execute("""
            SELECT q.q_id, q.question_name, q.question_link, q.level_of_question, q.notes_of_question,
                   COALESCE(qd.question_done, 0) AS done_status
            FROM Question q
            LEFT JOIN QuestionDone qd 
                ON q.q_id = qd.question_id 
               AND qd.student_id = %s
               AND qd.subject_id = %s
            WHERE q.subject_id = %s
        """, (student_id, subject_id, subject_id))
        questions = cursor.fetchall()
    finally:
        cursor.close()

    return render_template(
        'view_question_for_student.html',
        section_name=section_name,
        subject_id=subject_id,
        questions=questions,
        subject_name=subject_name
    )

@app.route('/particular_question_for_student/<int:q_id>/<int:subject_id>/<string:subject_name>/<string:section_name>', methods=['GET','POST'])
def particular_question_for_student(q_id, subject_id, subject_name, section_name):
    check = check_student_login()
    if check: return check
    cursor = get_cursor()
    try:
        query = """
            SELECT q_id, question_name, question_link, notes_of_question, subject_id
            FROM Question
            WHERE q_id = %s AND subject_id = %s
        """
        cursor.execute(query, (q_id, subject_id))
        question = cursor.fetchone()
    finally:
        cursor.close()

    if not question:
        return "Question not found", 404

    return render_template(
        "view_particular_questionstudent.html",
        q_id=question[0],
        q_name=question[1],
        q_link=question[2],
        q_notes=question[3],
        subject_id=question[4],
        subject_name=subject_name,
        section_name=section_name
    )

@app.route('/mark_as_complete/<int:q_id>/<int:subject_id>/<string:section_name>/<string:subject_name>', methods=['GET', 'POST'])
def mark_as_complete(q_id, subject_id, section_name, subject_name):
    check = check_student_login()
    if check: return check
    student_id = session.get("student_id")
    if not student_id:
        flash("Please login to mark question as complete.", "error")
        return redirect(url_for("login"))

    cursor = get_cursor()
    try:
        check_query = """
            SELECT * FROM QuestionDone
            WHERE student_id = %s AND question_id = %s AND subject_id = %s
        """
        cursor.execute(check_query, (student_id, q_id, subject_id))
        existing = cursor.fetchone()

        if not existing:
            insert_query = """
                INSERT INTO QuestionDone (student_id, question_id, subject_id, question_done)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (student_id, q_id, subject_id, 1))
            mysql.connection.commit()
            flash("Question marked as complete!", "success")
        else:
            flash("Question already marked as complete.", "info")
    finally:
        cursor.close()

    return redirect(url_for("view_question_for_student", section_name=section_name, subject_id=subject_id, subject_name=subject_name))

@app.route('/leaderboard_for_student<int:subject_id>', methods=['GET','POST'])
def leaderboard_for_student(subject_id):
    check = check_student_login()
    if check: return check
    student_id = session.get("student_id")
    cursor = get_cursor()
    try:
        query = """
            SELECT 
                s.student_id,
                s.name AS student_name,        
                COUNT(q.question_id) * 5 AS score
            FROM Student s
            JOIN QuestionDone q ON s.student_id = q.student_id
            WHERE q.question_done = 1
            AND q.subject_id = %s
            GROUP BY s.student_id, s.name
            ORDER BY score DESC, s.name ASC;
        """
        cursor.execute(query, (subject_id,))
        leaderboard = cursor.fetchall()
    finally:
        cursor.close()

    return render_template(
        "leaderboard_for_student.html",
        leaderboard=leaderboard,
        current_student_id=student_id,
    )

@app.route('/testdashboad_for_instructor/<int:subject_id>/<string:section_name>', methods=['GET', 'POST'])
def testdashboad_for_instructor(subject_id, section_name):
    check = check_instructor_login()
    if check: return check

    if 'instructor_id' not in session:
        flash("Please log in first.", "warning")
        return redirect(url_for('login'))

    instructor_id = session['instructor_id']
    cursor = None
    tests = []
    subject_name = "Unknown Subject"
    try:
        cursor = get_cursor()
        cursor.execute("SELECT subject_name FROM Subject WHERE subject_id = %s", (subject_id,))
        subject_row = cursor.fetchone()
        if subject_row:
            subject_name = subject_row[0]

        query = """
            SELECT *
            FROM Test
            WHERE instructor_id = %s AND subject_id = %s
            ORDER BY start_time DESC
        """
        cursor.execute(query, (instructor_id, subject_id))
        tests = cursor.fetchall()
    except Exception as e:
        print(" Error fetching tests or subject:", e)
        flash("An error occurred while loading test data.", "danger")
    finally:
        if cursor:
            cursor.close()

    return render_template(
        'testdashboad_for_instructor.html',
        subject_id=subject_id,
        subject_name=subject_name,
        tests=tests,
        section_name=section_name
    )




@app.route('/add_test_instructor/<int:subject_id>/<string:section_name>', methods=['GET', 'POST'])
def add_test_instructor(subject_id, section_name):
    check = check_instructor_login()
    if check: return check

    instructor_id = session['instructor_id']
    
    if request.method == 'POST':
        test_name = request.form.get('test_name')
        start_time_str = request.form.get('start_time')
        end_time_str = request.form.get('end_time')
        duration_minutes = request.form.get('duration_minutes')

        if not all([test_name, start_time_str, end_time_str, duration_minutes]):
            flash("All fields are required.", "warning")
            return redirect(url_for('add_test_instructor', subject_id=subject_id, section_name=section_name))

        # -----------------------------
        #  IST → UTC Conversion
        # -----------------------------
        ist = pytz.timezone('Asia/Kolkata')
        
        start_dt_ist = ist.localize(datetime.fromisoformat(start_time_str))
        end_dt_ist = ist.localize(datetime.fromisoformat(end_time_str))

        start_dt_utc = start_dt_ist.astimezone(pytz.utc)
        end_dt_utc = end_dt_ist.astimezone(pytz.utc)
        # -----------------------------

        cursor = get_cursor()
        try:
            insert_query = """
                INSERT INTO Test (test_name, subject_id, instructor_id, start_time, end_time, duration_minutes)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(insert_query, (test_name, subject_id, instructor_id, start_dt_utc, end_dt_utc, duration_minutes))
            mysql.connection.commit()

            flash("Test added successfully!", "success")
            return redirect(url_for('testdashboad_for_instructor', subject_id=subject_id, section_name=section_name))
        
        finally:
            cursor.close()

    return render_template("add_test_instructor.html", subject_id=subject_id, section_name=section_name)







@app.route('/delete_test/<int:test_id>/<int:subject_id>/<string:section_name>', methods=['GET'])
def delete_test(test_id, subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    cur = get_cursor()
    try:
        cur.execute("DELETE FROM Test WHERE test_id=%s", (test_id,))
        mysql.connection.commit()
    finally:
        cur.close()
    flash("Test deleted successfully!", "success")
    return redirect(url_for('testdashboad_for_instructor', subject_id=subject_id, section_name=section_name))

@app.route('/add_questions_for_test/<int:test_id>/<int:subject_id>/<string:section_name>', methods=['GET','POST'])
def add_questions_for_test(test_id, subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    if request.method == 'POST':
        question_texts = request.form.getlist('question_text[]')
        option_1s = request.form.getlist('option_1[]')
        option_2s = request.form.getlist('option_2[]')
        option_3s = request.form.getlist('option_3[]')
        option_4s = request.form.getlist('option_4[]')
        corrects = request.form.getlist('correct_option[]')

        cur = get_cursor()
        try:
            for i in range(len(question_texts)):
                cur.execute("""
                    INSERT INTO TestQuestion (test_id, subject_id, question_text, option_1, option_2, option_3, option_4, correct_option)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """, (test_id, subject_id, question_texts[i], option_1s[i], option_2s[i], option_3s[i], option_4s[i], corrects[i]))
            mysql.connection.commit()
            flash("Questions added successfully!", "success")
            return redirect(url_for('testdashboad_for_instructor', subject_id=subject_id, section_name=section_name))
        finally:
            cur.close()

    return render_template("add_question_for_test.html", test_id=test_id, subject_id=subject_id, section_name=section_name)

@app.route('/view_test_question_by_instructor/<int:test_id>/<int:subject_id>/<string:section_name>', methods=['GET','POST'])
def view_test_question_by_instructor(test_id, subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    cur = get_cursor()
    try:
        query = """
            SELECT tq_id, question_text, option_1, option_2, option_3, option_4, correct_option
            FROM TestQuestion
            WHERE test_id = %s AND subject_id = %s
        """
        cur.execute(query, (test_id, subject_id))
        data = cur.fetchall()
    finally:
        cur.close()
    return render_template("view_test_question_by_instructor.html", data=data, test_id=test_id, subject_id=subject_id, section_name=section_name)




@app.route('/test_dashboard_for_student/<int:subject_id>', methods=['GET', 'POST'])
def test_dashboard_for_student(subject_id):
    check = check_student_login()
    if check: return check
    cur = get_cursor()
    try:
        query = """
            SELECT test_id, test_name, subject_id, instructor_id, start_time, end_time, duration_minutes
            FROM Test
            WHERE subject_id = %s
            ORDER BY start_time DESC
        """
        cur.execute(query, (subject_id,))
        data = cur.fetchall()
    finally:
        cur.close()

    ist = pytz.timezone('Asia/Kolkata')
    current_time = datetime.now(ist)

    tests = []
    for row in data:
        test_id, test_name, subject_id, instructor_id, start_time, end_time, duration_minutes = row
        
        start_time = start_time.astimezone(ist)
        end_time = end_time.astimezone(ist)

        if current_time < start_time:
            status = "Not Started"
        elif start_time <= current_time <= end_time:
            status = "Active"
        else:
            status = "Completed"
        
        tests.append((test_id, test_name, subject_id, instructor_id, start_time, end_time, duration_minutes, status))

    return render_template("test_dashboard_for_student.html", subject_id=subject_id, tests=tests)






@app.route('/test_start_student/<int:test_id>/<int:subject_id>', methods=['GET','POST'])
def test_start_student(test_id, subject_id):
    check = check_student_login()
    if check: return check
    return render_template("test_start_student.html", test_id=test_id, subject_id=subject_id)

@app.route('/start_test_now_student/<int:test_id>/<int:subject_id>', methods=['GET', 'POST'])
def start_test_now_student(test_id, subject_id):
    check = check_student_login()
    if check: return check
    student_id = session.get('student_id')


    cur = get_cursor()
    try:
        check_query = "SELECT COUNT(*) FROM StudentResponse WHERE student_id = %s AND test_id = %s"
        cur.execute(check_query, (student_id, test_id))
        result = cur.fetchone()
        is_done = result[0] > 0

        cur.execute("SELECT test_name, duration_minutes FROM Test WHERE test_id = %s AND subject_id = %s", (test_id, subject_id))
        test_row = cur.fetchone()
        if not test_row:
            flash("Test not found.", "danger")
            return redirect(url_for('test_dashboard_for_student', subject_id=subject_id))
        TEST_NAME = test_row[0]; DURATION = test_row[1]

        cur.execute("SELECT name, registration_no FROM Student WHERE student_id = %s", (student_id,))
        student_row = cur.fetchone()
        if not student_row:
            flash("Student record not found.", "danger")
            return redirect(url_for('login'))
        STUDENT_NAME = student_row[0]; STUDENT_REG_NO = student_row[1]

        QUESTIONS = []
        if not is_done:
            cur.execute("""
                SELECT tq_id, question_text, option_1, option_2, option_3, option_4
                FROM TestQuestion
                WHERE test_id = %s AND subject_id = %s
            """, (test_id, subject_id))
            rows = cur.fetchall()
            QUESTIONS = [list(row) for row in rows]
    finally:
        cur.close()

    return render_template(
        "run_test_live.html",
        TEST_ID=test_id,
        SUBJECT_ID=subject_id,
        TEST_NAME=TEST_NAME,
        STUDENT_NAME=STUDENT_NAME,
        STUDENT_REG_NO=STUDENT_REG_NO,
        DURATION=DURATION,
        QUESTIONS=QUESTIONS,
        is_done=is_done
    )

@app.route('/submit_student_response_test/<int:test_id>/<int:subject_id>', methods=['POST'])
def submit_student_response_test(test_id, subject_id):
    check = check_student_login()
    if check: return check
    cur = get_cursor()
    student_id = session.get('student_id')
    if not student_id:
        return jsonify({"error": "Unauthorized: student not logged in"}), 401

    try:
        responses = request.get_json()
        if not responses:
            return jsonify({"error": "No response data received"}), 400
    except Exception as e:
        return jsonify({"error": f"Invalid JSON: {e}"}), 400

    try:
        # expect responses to be iterable of [question_id, selected_option] pairs
        for pair in responses:
            # support both [qid, opt] and {"question_id":..., "selected_option":...}
            if isinstance(pair, list) or isinstance(pair, tuple):
                question_id, selected_option = pair
            elif isinstance(pair, dict):
                question_id = pair.get('question_id')
                selected_option = pair.get('selected_option')
            else:
                continue

            if not selected_option:
                continue

            cur.execute("""
                INSERT INTO StudentResponse (student_id, test_id, question_id, selected_option)
                VALUES (%s, %s, %s, %s)
            """, (student_id, test_id, question_id, str(selected_option)))
        mysql.connection.commit()
    finally:
        cur.close()

    return jsonify({
        "message": "✅ Test submitted successfully!",
        "redirect_url": url_for('submit_success_page', subject_id=subject_id)
    }), 200

@app.route('/submit_success_page/<int:subject_id>')
def submit_success_page(subject_id):

    return render_template("Submit_sucessfully.html", subject_id=subject_id)

@app.route('/test_result_instructor/<int:test_id>/<int:subject_id>/<string:section_name>', methods=['GET', 'POST'])
def test_result_instructor(test_id, subject_id, section_name):
    check = check_instructor_login()
    if check: return check
    cur = get_cursor()
    try:
        cur.execute("SELECT test_name FROM Test WHERE test_id = %s", (test_id,))
        test_row = cur.fetchone()
        testname = test_row[0] if test_row else f"Test ID: {test_id}"

        cur.execute("SELECT COUNT(*) FROM TestQuestion WHERE test_id = %s", (test_id,))
        total_questions = cur.fetchone()[0] or 1

        cur.execute("""
            SELECT student_id, name, registration_no, email
            FROM Student
            WHERE section_name = %s
        """, (section_name,))
        students = cur.fetchall()

        results = []
        total_score_sum = 0
        highest_score = 0
        completed_count = 0

        for s in students:
            student_id, name, reg_no, email = s
            cur.execute("""
                SELECT COUNT(*) 
                FROM StudentResponse AS sr
                JOIN TestQuestion AS tq ON sr.question_id = tq.tq_id
                WHERE sr.student_id = %s
                  AND sr.test_id = %s
                  AND tq.subject_id = %s
                  AND sr.selected_option = tq.correct_option
            """, (student_id, test_id, subject_id))
            correct_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM StudentResponse WHERE student_id = %s AND test_id = %s", (student_id, test_id))
            answered = cur.fetchone()[0]
            if answered > 0:
                completed_count += 1

            score_percent = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            total_score_sum += score_percent
            highest_score = max(highest_score, score_percent)

            results.append((name, reg_no, correct_count, email))

        average_score = round(total_score_sum / len(students), 2) if students else 0
        completion_rate = round((completed_count / len(students)) * 100, 2) if students else 0
        results.sort(key=lambda x: x[0].lower())
    finally:
        cur.close()

    return render_template(
        'test_result_instructor.html',
        testname=testname,
        students=results,
        total_questions=total_questions,
        average_score=average_score,
        highest_score=round(highest_score, 2),
        completion_rate=completion_rate
    )

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('login'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
