import datetime
import hashlib
import uuid

from flask import Flask, render_template, request, make_response, redirect, url_for

from model import db, User, Post

app = Flask(__name__)

db.create_all()

WEBSITE_LOGIN_COOKIE_NAME = "science/session_token"
COOKIE_DURATION = 900  # in seconds


def require_session_token(func):
    """Decorator to require authentication to access routes"""
    def wrapper(*args, **kwargs):
        session_token = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        redirect_url = request.path or '/'

        if not session_token:
            app.logger.error('no token in request')
            return redirect(url_for('login', redirectTo=redirect_url))

        user = db.query(User)\
            .filter_by(session_cookie=session_token)\
            .filter(User.session_expiry_datetime >= datetime.datetime.now())\
            .first()

        if not user:
            app.logger.error(f'token {session_token} not valid')
            return redirect(url_for('login', redirectTo=redirect_url))

        app.logger.info(f'authenticated user {user.username} with token {user.session_cookie} valid until {user.session_expiry_datetime.isoformat()}')
        request.user = user
        return func(*args, **kwargs)

    # Renaming the function name:
    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/', methods=["GET"])
def index():
    return "You are Home! Enter /login to continue"

@app.route('/login', methods=["GET", "POST"])
def login():
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
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)
        if user is None:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user = User(username=username,
                        password_hash=password_hash,
                        session_cookie=session_cookie,
                        session_expiry_datetime=expiry_time)
            db.add(user)
            db.commit()
            app.logger.info(f"User {username} is registered")
        else:
            user.session_cookie = session_cookie
            user.session_expiry_datetime = expiry_time
            db.add(user)
            db.commit()
            app.logger.info(f"User {username} is logged in")

        redirect_url = request.args.get('redirectTo')
        response = make_response(redirect(redirect_url))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
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

        return render_template("login.html", logged_in=logged_in)


@app.route('/about', methods=["GET"])
def about():
    return render_template("about.html")


@app.route('/faq', methods=["GET"])
@require_session_token
def faq():
    return render_template("faq.html")

@app.route('/blog', methods=["GET", "POST"])
@require_session_token
def blog():

    session_token = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
    bloguser = db.query(User) \
        .filter_by(session_cookie=session_token) \
        .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
        .first()

    if request.method == "POST":
        title = request.form.get("posttitle")
        content = request.form.get("postcontent")
        post = Post(title=title, content=content, user_id=bloguser)
        db.add(post)
        db.commit()
    return render_template("blog.html")

if __name__ == '__main__':
    app.run(host='localhost', port=7890)
