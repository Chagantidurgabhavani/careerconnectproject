from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import matplotlib.pyplot as plt
from io import BytesIO
#--------------------------------------------


import random
import smtplib
from email.mime.text import MIMEText



app = Flask(__name__)
app.secret_key = "careerconnect"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT UNIQUE,
        password TEXT)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        company TEXT,
        location TEXT)
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        job_id INTEGER)
    """)

    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route("/")
def home():
    return render_template("home.html")

# ---------- REGISTER ----------
@app.route("/register", methods=["GET","POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (name,email,password) VALUES (?,?,?)",
            (name,email,password)
        )

        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# ---------- LOGIN ----------
@app.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM users WHERE email=? AND password=?",
            (email,password)
        )

        user = cur.fetchone()
        conn.close()

        if user:

            session["user_id"] = user[0]
            session["user_name"] = user[1]

            return redirect("/dashboard")

        else:
            return "Invalid Credentials"

    return render_template("login.html")
#------------------------------------------------------

@app.route("/interview", methods=["GET","POST"])
def interview():
    role = request.args.get("role")  # e.g., "Python Developer"

    if not role:
        return "Please select a role first!"

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    # Fetch 5 random questions for the role
    cur.execute(
        "SELECT question FROM questions WHERE role=? ORDER BY RANDOM() LIMIT 5",
        (role,)
    )
    questions = cur.fetchall()
    conn.close()

    # Flatten list of tuples to list of strings
    questions = [q[0] for q in questions]

    return render_template("ai_interview.html", questions=questions, role=role)  

    

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():

    if "user_id" in session:
        return render_template("dashboard.html", name=session["user_name"])

    return redirect("/login")


@app.route("/jobs")
def jobs():

    search = request.args.get("search")

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    if search:
        cur.execute("SELECT * FROM jobs WHERE title LIKE ?", ('%'+search+'%',))
    else:
        cur.execute("SELECT * FROM jobs")

    all_jobs = cur.fetchall()
    conn.close()

    return render_template("jobs.html", jobs=all_jobs)
# ---------- APPLY JOB ----------
@app.route("/apply/<int:job_id>")
def apply(job_id):

    if "user_id" in session:

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO applications (user_id,job_id) VALUES (?,?)",
            (session["user_id"], job_id)
        )

        conn.commit()
        conn.close()

        return "Applied Successfully!"

    return redirect("/login")

# ---------- ADD JOB ----------

#----------------------------------------
@app.route("/addjob", methods=["GET","POST"])
def addjob():

    if request.method == "POST":

        title = request.form["title"]
        company = request.form["company"]
        location = request.form["location"]

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO jobs (title,company,location) VALUES (?,?,?)",
            (title,company,location)
        )

        conn.commit()
        conn.close()

        return redirect("/jobs")

    return render_template("addjob.html")
# ------------------------------
@app.route("/deletejob/<int:job_id>")
def deletejob(job_id):

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("DELETE FROM jobs WHERE id=?", (job_id,))

    conn.commit()
    conn.close()

    return redirect("/jobs")

# ---------- ANALYTICS ----------
@app.route("/analytics")
def analytics():

    conn = sqlite3.connect("database.db")
    cur = conn.cursor()

    cur.execute("""
    SELECT jobs.title, COUNT(applications.id)
    FROM jobs
    LEFT JOIN applications
    ON jobs.id = applications.job_id
    GROUP BY jobs.id
    """)

    data = cur.fetchall()
    conn.close()

    jobs = [row[0] for row in data]
    counts = [row[1] for row in data]

    plt.figure(figsize=(8,5))
    plt.bar(jobs, counts)
    plt.title("Job Applications Statistics")
    plt.xlabel("Job Title")
    plt.ylabel("Applications")

    img = BytesIO()
    plt.savefig(img, format="png")
    img.seek(0)
    plt.close()

    return send_file(img, mimetype="image/png")
# ----------------excel data--------------------------------
@app.route("/export_excel")

def export_excel():
    import pandas as pd

    conn = sqlite3.connect("database.db")

    query = """
    SELECT users.name, users.email, jobs.title, jobs.company
    FROM applications
    JOIN users ON applications.user_id = users.id
    JOIN jobs ON applications.job_id = jobs.id
    """

    df = pd.read_sql_query(query, conn)

    file_path = "job_applications.xlsx"
    df.to_excel(file_path, index=False)

    conn.close()

    return send_file(file_path, as_attachment=True)

# ---------- LOGOUT ----------
@app.route("/logout")
def logout():

    session.clear()
    return redirect("/")

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)

@app.route("/ai_interview", methods=["GET","POST"])
def ai_interview():

    answer = ""
    question = ""

    if request.method == "POST":

        question = request.form.get("question","").lower().strip()

        # remove spelling mistakes simple fix
        question = question.replace("wht","what")

        if "python" in question:
            answer = "Python is a high-level, interpreted programming language."

        elif "data types" in question:
            answer = "Python has int, float, string, list, tuple, dict, set."

        elif "pep 8" in question:
            answer = "PEP 8 is the coding style guide for Python."

        elif "sql" in question:
            answer = "SQL is used to manage and query databases."

        else:
            answer = "Sorry, I don't know this answer."

    return render_template("ai_interview.html", answer=answer, question=question)