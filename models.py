from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, UTC

db = SQLAlchemy()  # Initialize here, but bind to app in app.py

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    class_name = db.Column(db.String(30), primary_key = True)
    floor = db.Column(db.Integer)

    #Foreign key
    furniture = db.relationship('Furniture', backref = 'classrooms', lazy = True)

    def __repr__(self):
        return super().__repr__()



class Furniture(db.Model):
    __tablename__ = 'furniture'
    id = db.Column(db.Integer, primary_key=True)
    furniture_type = db.Column(db.String(100), nullable = False)
    previous_room = db.Column(db.String(100), nullable = True)
    # Foreign key
    current_room = db.Column(db.String(100), db.ForeignKey('classrooms.class_name',  name = 'fk_current_room'))

    last_moved = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
       return f"<Furniture {self.furniture_type} in {self.classroom_name}>"
