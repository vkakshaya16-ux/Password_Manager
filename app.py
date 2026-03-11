from cryptography.fernet import Fernet
import os

from flask import Flask, render_template, request, redirect, session
import sqlite3
import hashlib
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://")

DB_PATH = DATABASE_URL if DATABASE_URL else os.path.join(BASE_DIR, "database.db")
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
app.secret_key = os.urandom(24) # Needed for session

# -------------------------
# CREATE DATABASE
# -------------------------
def get_connection():
    if DB_PATH.startswith("postgresql://"):
        import psycopg2
        return psycopg2.connect(DB_PATH)
    else:
        return sqlite3.connect(DB_PATH)
def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT,
            password_hash TEXT
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS passwords (
            id SERIAL PRIMARY KEY,
            user_id INTEGER,
            app_name TEXT,
            app_username TEXT,
            app_password TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    """)

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

        conn = get_connection()
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
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

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username=%s AND password_hash=%s",
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

    conn = get_connection()
    c = conn.cursor()

    # If form submitted
    if request.method == "POST":
        app_name = request.form["app_name"]
        app_username = request.form["app_username"]
        app_password = request.form["app_password"]
        encrypted_password = cipher.encrypt(app_password.encode()).decode()

        c.execute("""
            INSERT INTO passwords (user_id, app_name, app_username, app_password)
            VALUES (%s, %s, %s, %s)
        """, (session["user_id"], app_name, app_username, encrypted_password))

        conn.commit()

    # Fetch saved passwords
    c.execute("SELECT id, app_name, app_username, app_password FROM passwords WHERE user_id=%s",
          (session["user_id"],))
    data = c.fetchall()
    conn.close()

    passwords = []

    for row in data:
        decrypted = cipher.decrypt(row[3].encode()).decode()
        passwords.append((row[0], row[1], row[2], decrypted))

    return render_template("dashboard.html", passwords=passwords)
@app.route("/delete/<int:id>")
def delete_password(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM passwords WHERE id=%s AND user_id=%s", (id, session["user_id"]))

    conn.commit()
    conn.close()

    return redirect("/dashboard")
if __name__ == "__main__":
    init_db()   # make sure tables are created
    app.run()