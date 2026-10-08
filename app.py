from flask import Flask, request, render_template, redirect, url_for, session, jsonify, make_response
import sqlite3
from functools import wraps

app = Flask(__name__)
app.secret_key = "dev-secret-key-123"  # LAB ONLY: intentionally weak session secret

DB = "secureshop.db"

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
        username TEXT UNIQUE,
        password TEXT,
        role TEXT DEFAULT 'user'
    );
    CREATE TABLE IF NOT EXISTS orders(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        product_id INTEGER,
        quantity INTEGER
    );
    """)
    if not conn.execute("SELECT 1 FROM users WHERE username='admin'").fetchone():
        conn.execute("INSERT INTO users(username,password,role) VALUES('admin','admin123','admin')")
    if not conn.execute("SELECT 1 FROM users WHERE username='student'").fetchone():
        conn.execute("INSERT INTO users(username,password,role) VALUES('student','student123','user')")
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
            return "Admin access required", 403
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def home():
    return render_template("home.html", products=PRODUCTS)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]  # LAB ONLY: plaintext storage
        try:
            conn = db()
            conn.execute("INSERT INTO users(username,password) VALUES(?,?)", (username,password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "Username already exists", 400
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        # A03 Injection lab weakness: intentionally unsafe SQL concatenation.
        query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
        conn = db()
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
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
    q = request.args.get("q", "")
    # Safe search used for normal catalogue functionality.
    result = [p for p in PRODUCTS if q.lower() in p[1].lower()]
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
    user = conn.execute("SELECT * FROM users WHERE id=?", (session["user_id"],)).fetchone()
    conn.close()
    return render_template("profile.html", user=user)

@app.route("/orders")
@login_required
def orders():
    # A01 lab weakness: IDOR - user-controlled user_id decides whose orders are shown.
    user_id = request.args.get("user_id", session["user_id"])
    conn = db()
    rows = conn.execute("""
        SELECT orders.id, orders.user_id, orders.product_id, orders.quantity,
               users.username
        FROM orders JOIN users ON orders.user_id=users.id
        WHERE orders.user_id=?
    """, (user_id,)).fetchall()
    conn.close()
    return render_template("orders.html", orders=rows)

@app.route("/cart", methods=["GET","POST"])
@login_required
def cart():
    if request.method == "POST":
        product_id = int(request.form["product_id"])
        quantity = int(request.form.get("quantity", 1))
        conn = db()
        conn.execute("INSERT INTO orders(user_id,product_id,quantity) VALUES(?,?,?)",
                     (session["user_id"], product_id, quantity))
        conn.commit()
        conn.close()
        return redirect(url_for("cart"))
    conn = db()
    rows = conn.execute("SELECT * FROM orders WHERE user_id=?", (session["user_id"],)).fetchall()
    conn.close()
    return render_template("cart.html", orders=rows, products=PRODUCTS)

@app.route("/admin")
@admin_required
def admin():
    conn = db()
    users = conn.execute("SELECT id,username,role,password FROM users").fetchall()
    conn.close()
    # A05/A07 lab weakness: sensitive passwords exposed to administrator page.
    return render_template("admin.html", users=users)

@app.route("/admin/delete-user/<int:user_id>")
@admin_required
def delete_user(user_id):
    # A01 lab weakness: admin function lacks CSRF protection.
    conn = db()
    conn.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("admin"))

@app.route("/health")
def health():
    return jsonify(status="ok", application="SecureShop", environment="LOCAL LAB")

@app.after_request
def security_headers(response):
    # Intentionally incomplete headers for ZAP to identify.
    response.headers["X-Lab-Target"] = "SecureShop"
    return response

if __name__ == "__main__":
    init_db()
    app.run(host="127.0.0.1", port=8080, debug=True)
