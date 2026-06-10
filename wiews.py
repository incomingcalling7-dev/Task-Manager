import sqlite3 as sql
import random
import os
import threading
import time
from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
# Veb serverdə sessiyaların təhlükəsizliyi üçün gizli açar
app.secret_key = os.urandom(24)

# Render serverində fayl yazma xətası olmasın deyə bazanın tam yolunu təyin edirik
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_name = os.path.join(BASE_DIR, "database.db")

def init_db():
    """Bütün istifadəçilər və tapşırıqlar üçün vahid bazanı qurur"""
    with sql.connect(db_name) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS users 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         name TEXT, 
                         age INTEGER, 
                         user_code TEXT UNIQUE)''')
        
        conn.execute('''CREATE TABLE IF NOT EXISTS tasks 
                        (id INTEGER PRIMARY KEY AUTOINCREMENT,
                         user_code TEXT, 
                         tasks TEXT, 
                         progress TEXT, 
                         time TEXT, 
                         description TEXT)''')
        conn.commit()

# Server işə düşən kimi bazanın yaranmasını təmin edirik
init_db()

def background_timer(task_name, user_code, wait_hours):
    """Arxa planda vaxtı sayır və statusu yeniləyir"""
    try:
        wait_seconds = float(wait_hours) * 3600
        time.sleep(wait_seconds)
        with sql.connect(db_name) as con:
            con.execute("UPDATE tasks SET progress=? WHERE tasks=? AND user_code=?", 
                        ("Done", task_name, user_code))
            con.commit()
    except Exception:
        pass

@app.route("/")
def signup_sc():
    return render_template("Register.html")

@app.route("/login")
def login_sc():
    return render_template("Login.html")

@app.route("/locator", methods=['POST'])
def Locator():
    name = request.form.get("Name", "").strip().lower()
    age = request.form.get("age", "").strip()

    if not name or not age or not age.isdigit():
        return render_template("Register.html", message="Zəhmət olmasa düzgün ad və yaş daxil edin.")

    user_code = f"{name}_{age}_{random.randint(1000, 9999)}"

    try:
        with sql.connect(db_name) as conn:
            conn.execute("INSERT INTO users (name, age, user_code) VALUES (?, ?, ?)",
                        (name, age, user_code))
            conn.commit()

        session['user_code'] = user_code
        return redirect(url_for('home'))
    except Exception as e:
        # Xətanın tam olaraq nə olduğunu anlamaq üçün mesajı ekrana ötürürük
        return render_template("Register.html", message=f"Qeydiyyat xətası: {str(e)}")

@app.route("/Locatorone", methods=['POST'])
def locatoroe():
    task_id = request.form.get("Task_ID", "").strip()
    name = request.form.get("Player_Name", "").strip().lower()

    try:
        with sql.connect(db_name) as conn:
            conn.row_factory = sql.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE user_code = ? AND name = ?", (task_id, name))
            user = cur.fetchone()

        if user:
            session['user_code'] = task_id
            return redirect(url_for('home'))
        else:
            return render_template("Login.html", message="Kod və ya ad səhvdir.")
    except Exception as e:
        return render_template("Login.html", message=f"Giriş xətası: {str(e)}")

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

    try:
        with sql.connect(db_name) as con:
            con.execute("INSERT INTO tasks (user_code, tasks, progress, time, description) VALUES (?, ?, ?, ?, ?)",
                        (user_code, task, "In Progress", time_val, description))
            con.commit()

        thread = threading.Thread(target=background_timer, args=(task, user_code, time_val))
        thread.start()

    except Exception as e:
        print(f"Database error: {e}")

    return redirect(url_for('home'))

@app.route("/Tasks")
def Tasks():
    if 'user_code' not in session:
        return redirect(url_for('login_sc'))

    user_code = session['user_code']
    with sql.connect(db_name) as con:
        con.row_factory = sql.Row
        cur = con.cursor()
        cur.execute("SELECT tasks, progress, time, description FROM tasks WHERE user_code=?", (user_code,))
        rows = cur.fetchall()

    return render_template("tasks.html", tasks_list=rows)

@app.route("/edit_task", methods=['POST'])
def edit_task():
    if 'user_code' in session:
        user_code = session['user_code']
        old_name = request.form.get("old_task_name")
        new_name = request.form.get("new_name")
        description = request.form.get("Description")

        with sql.connect(db_name) as con:
            con.execute("UPDATE tasks SET tasks=?, description=? WHERE tasks=? AND user_code=?",
                        (new_name, description, old_name, user_code))
            con.commit()
    return redirect(url_for("home"))

@app.route("/loginout")
def disconnect():
    session.clear()
    return redirect(url_for("login_sc"))

if __name__ == "__main__":
    app.run(debug=True)
