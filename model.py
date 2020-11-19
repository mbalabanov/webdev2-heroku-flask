import datetime
import os

from sqla_wrapper import SQLAlchemy

DEFAULT_DB = "sqlite:///blog.sqlite"
db = SQLAlchemy(os.getenv("DATABASE_URL", DEFAULT_DB))


# 3 Klassen:
# - Post
# - User
# - Comment

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    username = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True)
    role = db.Column(db.String(55), nullable=False, default='admin')
    session_cookie = db.Column(db.String(255), nullable=True, unique=True)
    session_expiry_datetime = db.Column(db.DateTime)

    posts = db.relationship('Post', backref='users')
    comments = db.relationship('Comment', backref='users')


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    title = db.Column(db.String)
    text = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship(User)

    comments = db.relationship('Comment', backref='posts')


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created = db.Column(db.DateTime, default=datetime.datetime.now)
    updated = db.Column(db.DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    text = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship(User)

    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    post = db.relationship(Post)


if __name__ == '__main__':
    db.create_all()
