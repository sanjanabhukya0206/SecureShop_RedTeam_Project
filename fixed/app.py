from flask import Flask, request, render_template, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
from functools import wraps

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "local-lab-change-me"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
DB = os.environ.get("SECURESHOP_FIXED_DB", "secureshop_fixed.db")

PRODUCTS = [
    (1, "Laptop", 55000, "Student laptop"),
    (2, "Headphones", 2500, "Wireless headphones"),
    (3, "Keyboard", 1800, "Mechanical keyboard"),
    (4, "Mouse", 900, "Wireless mouse"),
]


def db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT DEFAULT 'user'
    );
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL CHECK(quantity > 0)
    );
    """)
    if not conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        conn.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("admin", generate_password_hash("ChangeThisAdminPassword!"), "admin"),
        )
    if not conn.execute("SELECT 1 FROM users WHERE username='student'").fetchone():
        conn.execute(
            "INSERT INTO users(username,password_hash,role) VALUES(?,?,?)",
            ("student", generate_password_hash("ChangeThisStudentPassword!"), "user"),
        )
    conn.commit()
    conn.close()


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            return "Forbidden", 403
        return fn(*args, **kwargs)
    return wrapper


@app.route("/")
def home():
    return render_template("home.html", products=PRODUCTS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 8:
            return "Username must be 3+ chars and password 8+ chars", 400
        try:
            conn = db()
            conn.execute(
                "INSERT INTO users(username,password_hash) VALUES(?,?)",
                (username, generate_password_hash(password)),
            )
            conn.commit()
            conn.close()
        except sqlite3.IntegrityError:
            return "Username already exists", 400
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = db()
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("profile"))
        return "Invalid credentials", 401
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/products")
def products():
    q = request.args.get("q", "").strip().lower()
    result = [p for p in PRODUCTS if q in p[1].lower()]
    return render_template("products.html", products=result, q=q)


@app.route("/product/<int:product_id>")
def product(product_id):
    item = next((p for p in PRODUCTS if p[0] == product_id), None)
    if not item:
        return "Product not found", 404
    return render_template("product.html", product=item)


@app.route("/profile")
@login_required
def profile():
    conn = db()
    user = conn.execute("SELECT id,username,role FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)


@app.route("/orders")
@login_required
def orders():
    # Fixed: ownership is derived from the authenticated session, never request parameters.
    user_id = session["user_id"]
    conn = db()
    rows = conn.execute("""
        SELECT orders.id, orders.user_id, orders.product_id, orders.quantity,
               users.username
        FROM orders JOIN users ON orders.user_id=users.id
        WHERE orders.user_id=?
        ORDER BY orders.id DESC
    """, (user_id,)).fetchall()
    conn.close()
    return render_template("orders.html", orders=rows)


@app.route("/cart", methods=["GET", "POST"])
@login_required
def cart():
    if request.method == "POST":
        try:
            product_id = int(request.form["product_id"])
            quantity = int(request.form.get("quantity", 1))
        except (KeyError, ValueError):
            return "Invalid cart data", 400
        if product_id not in {p[0] for p in PRODUCTS} or quantity < 1 or quantity > 20:
            return "Invalid product or quantity", 400
        conn = db()
        conn.execute(
            "INSERT INTO orders(user_id,product_id,quantity) VALUES(?,?,?)",
            (session["user_id"], product_id, quantity),
        )
        conn.commit()
        conn.close()
        return redirect(url_for("cart"))
    conn = db()
    rows = conn.execute("SELECT * FROM orders WHERE user_id=? ORDER BY id DESC", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("cart.html", orders=rows, products=PRODUCTS)


@app.route("/admin")
@admin_required
def admin():
    conn = db()
    users = conn.execute("SELECT id,username,role FROM users ORDER BY id").fetchall()
    conn.close()
    return render_template("admin.html", users=users, fixed=True)


@app.route("/admin/delete-user/<int:user_id>", methods=["POST"])
@admin_required
def delete_user(user_id):
    if user_id == session.get("user_id"):
        return "You cannot delete the active admin account", 400
    conn = db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))


@app.route("/health")
def health():
    return jsonify(status="ok", application="SecureShop", environment="LOCAL LAB", mode="fixed")


@app.after_request
def security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Content-Security-Policy"] = "default-src 'self'; style-src 'self' 'unsafe-inline'"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8080")), debug=False)
