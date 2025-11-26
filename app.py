from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    jsonify,
    send_from_directory,
)
import sqlite3
import os
import jwt
from datetime import datetime


app = Flask(__name__)
app.secret_key = "hardcoded_inventory_secret_987"  
app.config["DEBUG"] = True  
app.config["UPLOAD_FOLDER"] = "uploads"
app.config["JWT_SECRET"] = "inventory_jwt"  

os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

ALLOWED_EXTENSIONS = {"txt", "pdf", "png", "jpg", "jpeg", "gif", "php", "ps1"}


def get_db():
    conn = sqlite3.connect("inventory.db")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    from setup_db import init_db as seed

    seed()


@app.route("/")
def index():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        conn = get_db()
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        user = conn.execute(query).fetchone()
        conn.close()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]

            payload = {
                "sub": user["id"],
                "username": user["username"],
                "role": user["role"],
            }
            token = jwt.encode(payload, app.config["JWT_SECRET"], algorithm="HS256")
            session["jwt"] = token

            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Invalid username or password", "error")

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        role = request.form.get("role") or "staff"

        conn = get_db()
        try:
            conn.execute(
                f"INSERT INTO users (username, password, role) VALUES ('{username}', '{password}', '{role}')"
            )
            conn.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("Username already in use.", "error")
        finally:
            conn.close()

    return render_template("register.html")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    filter_value = request.args.get("filter", "")
    conn = get_db()
    items = conn.execute(
        f"SELECT * FROM items WHERE name LIKE '%{filter_value}%' ORDER BY last_updated DESC"
    ).fetchall()

    total_row = conn.execute(
        f"SELECT COUNT(*) as total_items, SUM(quantity) as total_qty FROM items WHERE name LIKE '%{filter_value}%'"
    ).fetchone()
    conn.close()

    return render_template(
        "dashboard.html",
        items=items,
        total_row=total_row,
        filter_value=filter_value,
        user=session,
    )


@app.route("/items/add", methods=["GET", "POST"])
def add_item():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        quantity = request.form.get("quantity", 0)
        unit_cost = request.form.get("unit_cost", 0)

        conn = get_db()
        conn.execute(
            f"INSERT INTO items (name, description, quantity, unit_cost, created_by) "
            f"VALUES ('{name}', '{description}', {quantity}, {unit_cost}, {session['user_id']})"
        )
        conn.commit()
        conn.close()
        flash("Item added.", "success")
        return redirect(url_for("dashboard"))

    return render_template("add_item.html")


@app.route("/items/edit/<int:item_id>", methods=["GET", "POST"])
def edit_item(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description")
        quantity = request.form.get("quantity", 0)
        unit_cost = request.form.get("unit_cost", 0)

        conn.execute(
            f"UPDATE items SET name = '{name}', description = '{description}', quantity = {quantity}, "
            f"unit_cost = {unit_cost}, last_updated = datetime('now') WHERE id = {item_id}"
        )
        conn.commit()
        conn.close()
        flash("Item updated.", "success")
        return redirect(url_for("dashboard"))

    item = conn.execute(f"SELECT * FROM items WHERE id = {item_id}").fetchone()
    conn.close()
    if not item:
        flash("Item not found.", "error")
        return redirect(url_for("dashboard"))

    return render_template("edit_item.html", item=item)


@app.route("/items/delete/<int:item_id>", methods=["POST"])
def delete_item(item_id):
    conn = get_db()
    conn.execute(f"DELETE FROM items WHERE id = {item_id}")
    conn.commit()
    conn.close()
    flash(f"Item #{item_id} deleted.", "success")
    return redirect(url_for("dashboard"))


@app.route("/admin")
def admin():
    conn = get_db()
    users = conn.execute("SELECT * FROM users ORDER BY id DESC").fetchall()
    logs = conn.execute(
        "SELECT id, name, quantity, last_updated FROM items ORDER BY last_updated DESC LIMIT 20"
    ).fetchall()
    conn.close()

    return render_template("admin.html", users=users, logs=logs)


@app.route("/api/items")
def api_items():
    order = request.args.get("order", "id")
    limit = request.args.get("limit", "50")
    conn = get_db()
    rows = conn.execute(f"SELECT * FROM items ORDER BY {order} LIMIT {limit}").fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/api/search")
def api_search():
    keyword = request.args.get("q", "")
    conn = get_db()
    rows = conn.execute(
        f"SELECT * FROM items WHERE name LIKE '%{keyword}%' OR description LIKE '%{keyword}%'"
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in rows])


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        file = request.files.get("file")
        if not file or file.filename == "":
            flash("Choose a file first.", "error")
            return redirect(url_for("upload"))

        if allowed_file(file.filename):
            filepath = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
            file.save(filepath)

            conn = get_db()
            conn.execute(
                f"INSERT INTO uploads (filename, original_filename, uploader) "
                f"VALUES ('{file.filename}', '{file.filename}', {session['user_id']})"
            )
            conn.commit()
            conn.close()

            flash(f"Uploaded {file.filename}", "success")
            return redirect(url_for("upload"))

        flash("File type not allowed.", "error")

    conn = get_db()
    uploads = conn.execute(
        f"SELECT * FROM uploads WHERE uploader = {session['user_id']} ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return render_template("upload.html", uploads=uploads)


@app.route("/uploads/<path:filename>")
def get_upload(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)


@app.route("/logout")
def logout():
    session.clear()
    flash("You are logged out.", "info")
    return redirect(url_for("login"))


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=7000, debug=True)


