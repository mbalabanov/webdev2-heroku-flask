import datetime
import hashlib
import os
import uuid
import re

from flask import Flask, render_template, request, make_response, redirect, url_for, flash
from flask_mail import Mail, Message

from model import db, User, Post, Comment
import email_config

app = Flask(__name__)

# Keep this secret!
# necessary for flash messages
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

LOCALHOST_NAME = "localhost"
LOCALHOST_PORT = 7890

HOST_ADDR = os.getenv("HOST_ADDR", f'http://{LOCALHOST_NAME}:{LOCALHOST_PORT}')

app.config.update(
    DEBUG=True,
    # EMAIL SETTINGS
    MAIL_SERVER=os.getenv("MAIL_SERVER", email_config.MAIL_SERVER),
    MAIL_PORT=int(os.getenv("MAIL_PORT", email_config.MAIL_PORT)),
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", email_config.MAIL_USERNAME),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", email_config.MAIL_PASSWORD),
)

mail = Mail(app)

db.create_all()

WEBSITE_LOGIN_COOKIE_NAME = "science/session_token"
COOKIE_DURATION = 900  # in seconds

# Make a regular expression for validating an Email
# for custom mails use: '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w+$'
#EMAIL_REGEX = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
EMAIL_REGEX = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

# EMAIL SENDER FOR ALL SITE NOTIFICATIONS
SENDER = "beachvolley.vienna.park@gmail.com"


@app.route("/test-mail")
def test_mail():
    try:
        msg = Message(
            subject="Flask WebDev Project Test Email",
            sender=SENDER,
            recipients=[SENDER]
        )
        msg.body = "There is a new Blogpost!, Check this out!"
        mail.send(msg)
        return "Flask sent your mail!"
    except Exception as e:
        return str(e)


def check_email(email: str) -> bool:
    return bool(re.search(EMAIL_REGEX, email))


def require_session_token(func):
    """Decorator to require authentication to access routes"""

    def wrapper(*args, **kwargs):
        session_token = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        redirect_url = request.path or '/'

        if not session_token:
            app.logger.error('no token in request')
            return redirect(url_for('login', redirectTo=redirect_url))

        user = db.query(User) \
            .filter_by(session_cookie=session_token) \
            .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
            .first()

        if not user:
            app.logger.error(f'token {session_token} not valid')
            return redirect(url_for('login', redirectTo=redirect_url))

        app.logger.info(
            f'authenticated user {user.username} with token {user.session_cookie} valid until {user.session_expiry_datetime.isoformat()}')
        request.user = user
        return func(*args, **kwargs)

    # Renaming the function name:
    wrapper.__name__ = func.__name__
    return wrapper


def provide_user(func):
    """Decorator to read user info if available"""

    def wrapper(*args, **kwargs):
        session_token = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)

        if not session_token:
            request.user = None
            return func(*args, **kwargs)

        user = db.query(User) \
            .filter_by(session_cookie=session_token) \
            .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
            .first()

        request.user = user
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper


@app.route('/', methods=["GET"])
@provide_user
def index():
    return render_template("index.html", user=request.user)


@app.route('/login', methods=["GET", "POST"])
@provide_user
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # query, check if there is a user with this username in the DB
        # user = db.query(User).filter(User.username == username).one()  # -> needs to find one, otherwise raises Error
        # user = db.query(User).filter(User.username == username).first()  # -> find first entry, if no entry, return None
        # users = db.query(User).filter(User.username == username).all()  # -> find all, always returns list. if not entry found, empty list

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # right way to find user with correct password
        user = db.query(User) \
            .filter(User.username == username, User.password_hash == password_hash) \
            .first()

        session_cookie = str(uuid.uuid4())
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)

        if user is None:
            flash("Username or password is wrong", "warning")
            app.logger.info(f"User {username} failed to login with wrong password.")
            redirect_url = request.args.get('redirectTo', url_for('index'))
            return redirect(url_for('login', redirectTo=redirect_url))
        else:
            user.session_cookie = session_cookie
            user.session_expiry_datetime = expiry_time
            db.add(user)
            db.commit()
            app.logger.info(f"User {username} is logged in")

        redirect_url = request.args.get('redirectTo', url_for('index'))
        response = make_response(redirect(redirect_url))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
        return response

    elif request.method == "GET":
        cookie = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        user = None

        if cookie is not None:
            user = db.query(User) \
                .filter_by(session_cookie=cookie) \
                .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
                .first()

        if user is None:
            logged_in = False
        else:
            logged_in = True

        return render_template("login.html", logged_in=logged_in, user=request.user)


@app.route("/registration", methods=["GET", "POST"])
@provide_user
def registration():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        repeat = request.form.get("repeat")

        # check email valid
        is_valid = check_email(email)
        if not is_valid:
            flash("Email is not a valid email", "warning")
            return redirect(url_for("registration"))

        if password != repeat:
            flash("Password and repeat did not match!", "warning")
            return redirect(url_for("registration"))

        # check if email is already taken:
        user = db.query(User).filter_by(email=email).first()
        if user:
            flash("Email is already taken", "warning")
            return redirect(url_for("registration"))

        # check if username is already taken in Database!
        user = db.query(User).filter_by(username=username).first()
        if user:
            flash("Username is already taken", "warning")
            return redirect(url_for('registration'))

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        session_cookie = str(uuid.uuid4())

        session_expiry_datetime = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)

        user = User(username=username,
                    email=email,
                    password_hash=password_hash,
                    session_cookie=session_cookie,
                    session_expiry_datetime=session_expiry_datetime)
        db.add(user)
        db.commit()
        flash("Registration Successful!", "success")

        # send registration confirmation email
        msg = Message(
            subject="WebDev Blog - Registration Successful",
            sender=SENDER,
            recipients=[email],
            bcc=[SENDER]
        )
        msg.body = f"Hi {username}!\nWelcome to our WebDev Flask site!\nEnjoy!"
        mail.send(msg)

        # set cookie for the browser
        response = make_response(redirect(url_for('index')))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
        return response

    elif request.method == "GET":
        return render_template("registration.html", user=request.user)


@app.route('/about', methods=["GET"])
@provide_user
def about():
    return render_template("about.html", user=request.user)


@app.route('/faq', methods=["GET"])
@require_session_token
def faq():
    return render_template("faq.html", user=request.user)


@app.route('/logout', methods=["GET"])
@provide_user
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, expires=0)

    user = db.query(User) \
        .filter_by(username=request.user.username) \
        .first()

    if user is not None:
        # reset user
        user.session_expiry_datetime = None
        user.session_cookie = None
        db.add(user)
        db.commit()
        app.logger.info(f"{user.username} has logged out.")

    return response


@app.route('/blog', methods=["GET", "POST"])
@require_session_token
def blog():
    current_user = request.user

    if request.method == "POST":
        title = request.form.get("posttitle")
        text = request.form.get("posttext")
        post = Post(
            title=title, text=text,
            user=current_user
        )
        db.add(post)
        db.commit()

        # send notification email
        msg = Message(
            subject="WebDev Blog - Registration Successful",
            sender=SENDER,
            recipients=[current_user.email]
        )
        msg.body = f"Hi {current_user.username}!\nWelcome to our WebDev Flask site!\nEnjoy!"
        msg.html = render_template("new_post.html",
                                   username=current_user.username,
                                   link=f"{HOST_ADDR}/posts/{post.id}",
                                   post=post)
        mail.send(msg)

        return redirect(url_for('blog'))

    if request.method == "GET":
        posts = db.query(Post).all()
        return render_template("blog.html", posts=posts, user=request.user)


@app.route('/posts/<post_id>', methods=["GET", "POST"])
@require_session_token
def posts(post_id):
    current_user = request.user
    post = db.query(Post).filter(Post.id == post_id).first()

    if request.method == "POST":
        text = request.form.get("text")
        comment = Comment(
            text=text,
            post=post,
            user=current_user
        )
        db.add(comment)
        db.commit()
        return redirect('/posts/{}'.format(post_id))

    elif request.method == "GET":
        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
        return render_template('posts.html', post=post, comments=comments, user=request.user)


@app.errorhandler(404)
@provide_user
def page_not_found(e):
    return render_template('404.html', user=request.user), 404


@app.errorhandler(500)
@provide_user
def server_error(e):
    return render_template('500.html', user=request.user), 500


if __name__ == '__main__':
    app.run(host=LOCALHOST_NAME, port=LOCALHOST_PORT)
