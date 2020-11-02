import hashlib
import uuid

from flask import Flask, render_template, request, make_response
from werkzeug.utils import redirect

from model import db, User

app = Flask(__name__)

db.create_all()

WEBSITE_LOGIN_COOKIE_NAME = "science/session_token"

@app.route('/', methods=["GET", "POST"])
def hello_world():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        repeat = request.form.get("repeat")

        if password != repeat:
            return "Password and Repeat do not match! Please try again."

        # query, check if there is a user with this username in the DB
        # user = db.query(User).filter(User.username == username).one()  # -> needs to find one, otherwise raises Error
        # user = db.query(User).filter(User.username == username).first()  # -> find first entry, if no entry, return None
        # users = db.query(User).filter(User.username == username).all()  # -> find all, always returns list. if not entry found, empty list

        user = db.query(User).filter(User.username == username).first()
        session_cookie = str(uuid.uuid4())
        if user is None:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = User(username=username, password_hash=password_hash, session_cookie=session_cookie)

            db.add(user)
            db.commit()
            app.logger.info(f"User {username} is registered")
        else:
            app.logger.info(f"User {username} is logged in")

        response = make_response(redirect('/'))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, "dummy_wert", httponly=True, samesite="Strict")
        return response

    elif request.method == "GET":
        cookie = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        user = None

        if cookie is not None:
            user = db.query(User).filter(User.session_cookie == cookie).first()

        if user is None:
            logged_in = False
        else:
            logged_in = True

        return render_template("hello_world.html", logged_in=logged_in)


@app.route('/about', methods=["GET"])
def about():
    return render_template("about.html")


@app.route('/faq', methods=["GET"])
def faq():
    return render_template("faq.html")


if __name__ == '__main__':
    app.run(host='localhost', port=7890)
