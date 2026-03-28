from flask import Flask, render_template, request, redirect, session, flash
import psycopg2
import os
import hashlib
from cryptography.fernet import Fernet

app = Flask(__name__)

# -------------------------
# CONFIG
# -------------------------
DATABASE_URL = os.environ.get("DATABASE_URL")
SECRET_KEY = os.environ.get("SECRET_KEY")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL not set")

if not SECRET_KEY:
    raise ValueError("SECRET_KEY not set")

app.secret_key = SECRET_KEY

cipher = Fernet(SECRET_KEY.encode())

# -------------------------
# DB CONNECTION
# -------------------------
def get_connection():
    return psycopg2.connect(DATABASE_URL)

# -------------------------
# CREATE TABLES
# -------------------------
def init_db():
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS passwords (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        app_name TEXT,
        app_username TEXT,
        app_password TEXT
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
# ROUTES
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

        try:
            c.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                (username, password)
            )
            conn.commit()
            flash("Account created successfully!", "success")
        except:
            conn.close()
            flash("Username already exists!", "error")
            return redirect("/register")

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

        c.execute(
            "SELECT id FROM users WHERE username=%s AND password_hash=%s",
            (username, password)
        )

        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user[0]
            flash("Login successful!", "success")
            return redirect("/dashboard")
        else:
            flash("Invalid credentials!", "error")
            return redirect("/login")

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

    # SAVE PASSWORD
    if request.method == "POST":
        app_name = request.form["app_name"]
        app_username = request.form["app_username"]
        app_password = request.form["app_password"]

        encrypted = cipher.encrypt(app_password.encode()).decode()

        c.execute("""
            INSERT INTO passwords (user_id, app_name, app_username, app_password)
            VALUES (%s, %s, %s, %s)
        """, (session["user_id"], app_name, app_username, encrypted))

        conn.commit()
        flash("Password saved!", "success")

    # FETCH PASSWORDS
    c.execute("""
        SELECT id, app_name, app_username, app_password
        FROM passwords
        WHERE user_id=%s
    """, (session["user_id"],))

    data = c.fetchall()
    conn.close()

    passwords = []

    for row in data:
        decrypted = cipher.decrypt(row[3].encode()).decode()
        passwords.append({
            "id": row[0],
            "app_name": row[1],
            "app_username": row[2],
            "app_password": decrypted
        })

    return render_template("dashboard.html", passwords=passwords)

# -------------------------
# DELETE
# -------------------------
@app.route("/delete/<int:id>", methods=["POST"])
def delete_password(id):
    if "user_id" not in session:
        return redirect("/login")

    conn = get_connection()
    c = conn.cursor()

    c.execute(
        "DELETE FROM passwords WHERE id=%s AND user_id=%s",
        (id, session["user_id"])
    )

    conn.commit()
    conn.close()

    flash("Password deleted!", "success")
    return redirect("/dashboard")

# -------------------------
# LOGOUT
# -------------------------
@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect("/login")
@app.route("/clear")
def clear_all():
    conn = get_connection()
    c = conn.cursor()

    c.execute("DELETE FROM passwords")

    conn.commit()
    conn.close()

    return "All passwords deleted"
# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)