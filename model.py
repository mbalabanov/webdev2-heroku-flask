from sqla_wrapper import SQLAlchemy

db = SQLAlchemy("sqlite:///blog.sqlite")


# 3 Klassen:
# - Post
# - User
# - Comment

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    session_cookie = db.Column(db.String(255), nullable=True, unique=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String)
    content = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship(User)


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.String)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    user = db.relationship(User)

    post_id = db.Column(db.Integer, db.ForeignKey("posts.id"))
    post = db.relationship(Post)


if __name__ == '__main__':
    db.create_all()
