<<<<<<< HEAD
from cryptography.fernet import Fernet
import os

from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
app = Flask(__name__)
# -------------------------
# ENCRYPTION SETUP
# -------------------------
if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)

with open("secret.key", "rb") as f:
    key = f.read()

cipher = Fernet(key)
app.secret_key = "mysecretkey"   # Needed for session

# -------------------------
# CREATE DATABASE
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password_hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            app_name TEXT,
            app_username TEXT,
            app_password TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------------
# HASH FUNCTION
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return redirect("/login")

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

        else:
            return "Invalid Credentials!"

    return render_template("login.html")
# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # If form submitted
    if request.method == "POST":
        app_name = request.form["app_name"]
        app_username = request.form["app_username"]
        app_password = request.form["app_password"]
        encrypted_password = cipher.encrypt(app_password.encode()).decode()

        c.execute("""
            INSERT INTO passwords (user_id, app_name, app_username, app_password)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], app_name, app_username, encrypted_password))

        conn.commit()

    # Fetch saved passwords
    c.execute("SELECT app_name, app_username, app_password FROM passwords WHERE user_id=?",
              (session["user_id"],))
    data = c.fetchall()
    conn.close()

    passwords = []

    for row in data:
        decrypted = cipher.decrypt(row[2].encode()).decode()
        passwords.append((row[0], row[1], decrypted))

    return render_template("dashboard.html", passwords=passwords)

if __name__ == "__main__":
    init_db()   # make sure tables are created
=======
from cryptography.fernet import Fernet
import os

from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "database.db")
app = Flask(__name__)
# -------------------------
# ENCRYPTION SETUP
# -------------------------
if not os.path.exists("secret.key"):
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)

with open("secret.key", "rb") as f:
    key = f.read()

cipher = Fernet(key)
app.secret_key = "mysecretkey"   # Needed for session

# -------------------------
# CREATE DATABASE
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password_hash TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS passwords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            app_name TEXT,
            app_username TEXT,
            app_password TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# -------------------------
# HASH FUNCTION
# -------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return redirect("/login")

# -------------------------
# REGISTER
# -------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                  (username, password))
        conn.commit()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

# -------------------------
# LOGIN
# -------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = hash_password(request.form["password"])

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=? AND password_hash=?",
                  (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            return redirect("/dashboard")

        else:
            return "Invalid Credentials!"

    return render_template("login.html")
# -------------------------
# DASHBOARD
# -------------------------
@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user_id" not in session:
        return redirect("/login")

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # If form submitted
    if request.method == "POST":
        app_name = request.form["app_name"]
        app_username = request.form["app_username"]
        app_password = request.form["app_password"]
        encrypted_password = cipher.encrypt(app_password.encode()).decode()

        c.execute("""
            INSERT INTO passwords (user_id, app_name, app_username, app_password)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], app_name, app_username, encrypted_password))

        conn.commit()

    # Fetch saved passwords
    c.execute("SELECT app_name, app_username, app_password FROM passwords WHERE user_id=?",
              (session["user_id"],))
    data = c.fetchall()
    conn.close()

    passwords = []

    for row in data:
        decrypted = cipher.decrypt(row[2].encode()).decode()
        passwords.append((row[0], row[1], decrypted))

    return render_template("dashboard.html", passwords=passwords)

if __name__ == "__main__":
    init_db()   # make sure tables are created
>>>>>>> 5b2823330013de61922bdd2fed580205957a7c2a
    app.run(debug=True)