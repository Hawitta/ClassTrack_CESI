from flask import Flask, Response, json,jsonify, request,render_template,redirect,session,url_for,flash
# import joblib
from influxdb_client import InfluxDBClient, Point, WritePrecision
import ssl
import certifi
import os
from models import db, Furniture,Classroom
from flask_migrate import Migrate
from datetime import datetime,timedelta, timezone, UTC
from sqlalchemy import func,case,text
from zoneinfo import ZoneInfo
from werkzeug.security import check_password_hash
from flask_socketio import SocketIO


ssl_context = ssl.create_default_context(cafile=certifi.where())

app = Flask(__name__)
app.secret_key = "my_super_random_secret_key_12345"

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB and migrations 
db.init_app(app)
migrate = Migrate(app, db)
now_utc = datetime.now(UTC)
local_time = now_utc + timedelta(hours=1)


@app.route("/", methods=['POST','GET'])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = db.session.execute(
            text("SELECT id, password_hash FROM users WHERE username = :username"),
            {"username": username}
        ).fetchone()

        if user and check_password_hash(user.password_hash, password):
            session["user_id"] = user.id
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid username or password", "danger")

    return render_template("login.html")

@app.route("/dashboard", methods=['GET'])
def dashboard():

    furniture_list = Furniture.query.order_by(Furniture.last_moved.desc()).all()
    now = datetime.now() # current time
    twenty_minutes_ago = now - timedelta(minutes=300)

    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    recent_furniture = Furniture.query.filter(
        Furniture.last_moved >= twenty_minutes_ago
    ).order_by(Furniture.last_moved.desc()).all()
  
    for item in furniture_list:
        item.local_time = item.last_moved + timedelta(hours = 1)

    for item in recent_furniture:
        item.local_time = item.last_moved + timedelta (hours = 1)
    
    return render_template("index.html", furniture = furniture_list, now = now, recent_furniture = recent_furniture, current_user = current_user)


@app.route("/edit", methods=['GET'])
def get_edit():
    furniture_list = Furniture.query.order_by(Furniture.last_moved.desc()).all()
    now = datetime.now() # current time
    
    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    for item in furniture_list:
        item.local_time = item.last_moved + timedelta(hours = 1)

    return render_template("edit.html", current_user = current_user, now = now, furniture = furniture_list)

@app.route("/new_room", methods=['GET'])
def get_new_room():
    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    return render_template("reports.html",current_user = current_user)

@app.route("/help", methods = ['GET'])
def get_help():
    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    return render_template("help.html", current_user = current_user)

@app.route("/first_floor", methods=["GET"])
def get_first_floor():
    # Get all first-floor classrooms
    first_floor_rooms = Classroom.query.filter_by(floor="1").all()

    # pass current user to regulate admin/user privileges
    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    # Count furniture per type for each room where current_room matches classroom
    results = (
    db.session.query(
        Classroom.class_name,
        func.sum(
            case((func.lower(Furniture.furniture_type) == "chair", 1), else_=0)
        ).label("chairs"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "table", 1), else_=0)
        ).label("tables"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "monitor", 1), else_=0)
        ).label("monitors"),
    )
    .outerjoin(Furniture, Furniture.current_room == Classroom.class_name)
    .filter(Classroom.floor == '1')
    .group_by(Classroom.class_name)
    .all()
    )

    # Convert results to dictionary for the table
    furniture_counts = {r.class_name: r for r in results}

    return render_template(
        "first_floor.html",
        rooms=first_floor_rooms,
        furniture_counts=furniture_counts,
        current_user = current_user
    )
    

@app.route("/second_floor", methods=["GET"])
def get_second_floor():
   
    second_floor_rooms = Classroom.query.filter_by(floor="2").all()

    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()

    # Count furniture per type for each room where current_room matches classroom
    results = (
    db.session.query(
        Classroom.class_name,
        func.sum(
            case((func.lower(Furniture.furniture_type) == "chair", 1), else_=0)
        ).label("chairs"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "table", 1), else_=0)
        ).label("tables"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "monitor", 1), else_=0)
        ).label("monitors"),
    )
    .outerjoin(Furniture, Furniture.current_room == Classroom.class_name)
    .filter(Classroom.floor == '2')
    .group_by(Classroom.class_name)
    .all()
    )

    # Convert results to dictionary for easy lookup in Jinja
    furniture_counts = {r.class_name: r for r in results}

    return render_template(
        "second_floor.html",
        rooms=second_floor_rooms,
        furniture_counts=furniture_counts,
        current_user = current_user
    )

@app.route("/third_floor", methods=["GET"])
def get_third_floor():
      # Get all first-floor classrooms
    third_floor_rooms = Classroom.query.filter_by(floor="3").all()
    user_id = session.get("user_id")
    current_user = db.session.execute(
        text("SELECT id, username, user_role FROM users WHERE id = :id"),
        {"id": user_id}
    ).fetchone()
    # Count furniture per type for each room where current_room matches classroom
    results = (
    db.session.query(
        Classroom.class_name,
        func.sum(
            case((func.lower(Furniture.furniture_type) == "chair", 1), else_=0)
        ).label("chairs"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "table", 1), else_=0)
        ).label("tables"),
        func.sum(
            case((func.lower(Furniture.furniture_type) == "monitor", 1), else_=0)
        ).label("monitors"),
    )
    .outerjoin(Furniture, Furniture.current_room == Classroom.class_name)
    .filter(Classroom.floor == '3')
    .group_by(Classroom.class_name)
    .all()
    )

    # Convert results to dictionary for easy lookup in Jinja
    furniture_counts = {r.class_name: r for r in results}

    return render_template(
        "third_floor.html",
        rooms=third_floor_rooms,
        furniture_counts=furniture_counts,
        current_user = current_user
    )


@app.route('/furniture/delete/<int:id>', methods=['POST', 'GET'])
def delete_furniture(id):
    # Get the item by id
    item = Furniture.query.get_or_404(id)
    
    try:
        db.session.delete(item)   # Delete the item
        db.session.commit()       # Commit the change
        flash('Furniture item deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
    
    # Redirect back to the furniture list page
    return redirect(url_for('get_edit'))



@app.route("/test_chairs", methods = ['GET'])
def test_chairs():
    furniture = Furniture.query.all()
    return jsonify([
        {
            'id': f.id, 'type': f.type, 'classroom': f.classroom_name
        }
        for f in furniture
    ])

@app.route('/add_classrooms', methods=['POST'])
def add_classrooms():
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({"error": "Send a list of classrooms"}), 400

    added = []
    skipped = []

    for item in data:
        class_name = item.get('class_name')
        floor = item.get('floor')

        if not class_name:
            skipped.append({"reason": "Missing name", "data": item})
            continue

        # Skip if classroom already exists
        if Classroom.query.get(class_name):
            skipped.append({"reason": "Already exists", "name": class_name})
            continue

        new_classroom = Classroom(class_name=class_name, floor=floor)
        db.session.add(new_classroom)
        added.append(class_name)

    db.session.commit()

    return jsonify({
        "added": added,
        "skipped": skipped
    }), 201



@app.route('/add_furniture', methods=['POST'])
def add_furniture():
    data = request.get_json()

    if not isinstance(data, list):
        return jsonify({"error": "Send a list of furniture"}), 400

    added = []
    skipped = []

    for item in data:
        furniture_type = item.get('furniture_type')
        previous_room = item.get('previous_room')
        current_room = item.get('current_room')
        last_moved = item.get('last_moved')
        if last_moved:
            try:
                last_moved = datetime.fromisoformat(last_moved)
            except ValueError:
                return jsonify({"error": "Invalid date format. Use YYYY-MM-DDTHH:MM:SS"}), 400
        else:
            last_moved = datetime.utcnow()


        new_furniture = Furniture(furniture_type=furniture_type, previous_room = previous_room, current_room = current_room, last_moved = last_moved)
        db.session.add(new_furniture)
        added.append(furniture_type)

    db.session.commit()

    return jsonify({
        "added": added,
        "skipped": skipped
    }), 201

@app.route("/logout", methods=["POST"])
def logout():
    session.pop("user_id", None)  # Remove the user from session
    flash("You have been logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port = 5000, debug=True)