import webview
import sqlite3 as sql
import random
import time
import threading
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "12345"
db_name = "Profile.db"


def oppen_db():
    with sql.connect(db_name) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         name TEXT, 
                         age INTEGER, 
                         user_code TEXT UNIQUE)''')


def background_timer(user_db, task_name, wait_hours):
    try:
        wait_seconds = float(wait_hours) * 3600
        time.sleep(wait_seconds)
        with sql.connect(user_db) as con:
            con.execute("UPDATE tasks SET Progess=? WHERE Tasks=?", ("Done", task_name))
            con.commit()
    except Exception as e:
            pass


@app.route("/")
def signup_sc():
    return render_template("Register.html")
@app.route("/login")
def login_sc():
    return render_template("Login.html")
@app.route("/locator", methods=['POST'])
def Locator():
    name = request.form.get("Name").strip().lower()
    age = request.form.get("age")

    if not age or not age.isdigit():
        return render_template("Register.html", message="Please enter a valid age.")

    user_code = f"{name}_{age}_{random.randint(1, 100000)}"

    try:
        with sql.connect(db_name) as conn:
            cur = conn.cursor()
            cur.execute("INSERT INTO users (name, age, user_code) VALUES (?, ?, ?)",
                        (name, age, user_code))
            conn.commit()

        with sql.connect(f"{user_code}.db") as con:
            con.execute('''CREATE TABLE IF NOT EXISTS tasks 
                            (Tasks TEXT, 
                             Progess TEXT, 
                             Time TEXT, 
                             Description TEXT)''')
            con.commit()

        session['user_code'] = user_code
        return redirect(url_for('home'))
    except Exception:
        return render_template("Register.html", message="Xəta baş verdi.")

@app.route("/Locatorone", methods=['POST'])
def locatoroe():
    task_id = request.form.get("Task_ID", "").strip()
    name = request.form.get("Player_Name", "").strip().lower()

    try:
        conn = sql.connect(db_name)
        conn.row_factory = sql.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE user_code = ? AND name = ?", (task_id, name))
        user1 = cur.fetchone()

        if user1:
            session['user_code'] = task_id
            return redirect(url_for('home'))
        else:
            return render_template("Login.html", message="Kod və ya ad səhvdir.")
    except Exception:
        return render_template("Login.html", message="Giriş zamanı xəta.")
    finally:
        conn.close()

@app.route("/home")
def home():
    if 'user_code' in session:
        return render_template("Home.html", kod=session['user_code'])
    return redirect(url_for('login_sc'))


@app.route("/add_file", methods=['POST'])
def add_task():
    if 'user_code' not in session:
        return redirect(url_for('login_sc'))

    user_code = session['user_code']
    task = request.form.get("task_content")
    time_val = request.form.get("Time")
    description = request.form.get("Description")
    user_db = f"{user_code}.db"
    try:
        with sql.connect(user_db) as con:
            con.execute("INSERT INTO tasks (Tasks, Progess, Time, Description) VALUES (?, ?, ?, ?)",
                        (task, "In Progress", time_val, description))
            con.commit()

        thread = threading.Thread(target=background_timer, args=(user_db, task, time_val))
        thread.start()

    except Exception as e:
        print(f"Database error: {e}")

    return redirect(url_for('home'))


@app.route("/Tasks")
def Tasks():
    if 'user_code' not in session:
        return redirect(url_for('login_sc'))

    user_code = session['user_code']
    with sql.connect(f"{user_code}.db") as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT Tasks, Progess, Time, Description FROM tasks")
        rows = cur.fetchall()

    return render_template("tasks.html", tasks_list=rows)


@app.route("/edit_task", methods=['POST'])
def edit_task():
    if 'user_code' in session:
        old_name = request.form.get("old_task_name")
        new_name = request.form.get("new_name")
        description = request.form.get("Description")
        user_db = f"{session['user_code']}.db"

        with sql.connect(user_db) as con:
            con.execute("UPDATE tasks SET Tasks=?, Description=? WHERE Tasks=?",
                        (new_name, description, old_name))
            con.commit()
    return redirect(url_for("home"))


@app.route("/loginout")
def disconnect():
    session.clear()
    return redirect(url_for("login_sc"))


if __name__ == "__main__":
    oppen_db()
    app.run(debug=True)