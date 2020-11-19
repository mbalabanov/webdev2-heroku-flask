import datetime
import hashlib
import os
import uuid
import re

from flask import Flask, render_template, request, make_response, redirect, url_for, flash
from flask_mail import Mail, Message

import email_config
from model import db, User, Post, Comment

app = Flask(__name__)

# Keep this secret!
# necessary for flash messages
app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

app.config.update(
    DEBUG=True,
    # EMAIL SETTINGS
    MAIL_SERVER=os.getenv("MAIL_SERVER", email_config.MAIL_SERVER),
    MAIL_PORT=os.getenv("MAIl_PORT", email_config.MAIL_PORT),
    MAIL_USE_SSL=os.getenv("MAIL_USE_SSL", email_config.MAIL_USE_SSL),
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", email_config.MAIL_USERNAME),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", email_config.MAIL_PASSWORD)
)

mail = Mail(app)

@app.route("/test-mail")
def test_mail():
    try:
        msg = Message(
            subject="Flask WebDev Project Test Email",
            sender="sendinatorizer@gmail.com",
            recipients=["sendinatorizer@gmail.com"]
        )
        msg.body = "There is a new Blogpost!, Check this out!"
        mail.send(msg)
        return "Flask sent your mail!"
    except Exception as e:
        return str(e)

db.create_all()

WEBSITE_LOGIN_COOKIE_NAME = "science/session_token"
COOKIE_DURATION = 900  # in seconds
# EMAIL_REGEX = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
EMAIL_REGEX = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
SENDER = "sendinatorizer@gmail.com"


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

        user = db.query(User)\
            .filter_by(session_cookie=session_token)\
            .filter(User.session_expiry_datetime >= datetime.datetime.now())\
            .first()

        request.user = user
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper



@app.route('/', methods=["GET"])
def index():
    return render_template("index.html")


@app.route('/login', methods=["GET", "POST"])
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
        user = db.query(User)\
            .filter(User.username == username, User.password_hash == password_hash)\
            .first()

        session_cookie = str(uuid.uuid4())
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)

        if user is None:
            flash("warning", "Username or password is wrong")
            app.logger.info(f"User {username} failed to login with wrong password.")
            redirect_url = request.args.get('redirectTo')
            return redirect(url_for('login', redirectTo=redirect_url))
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
            user = db.query(User) \
                .filter_by(session_cookie=cookie) \
                .filter(User.session_expiry_datetime >= datetime.datetime.now())\
                .first()

        if user is None:
            logged_in = False
        else:
            logged_in = True

        return render_template("login.html", logged_in=logged_in)


@app.route("/registration", methods=["GET", "POST"])
def registration():
    if request.method=="POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        repeat = request.form.get("repeat")

        if password!=repeat:
            flash("warning", "Password and repeat did not match!")
            return redirect(url_for("registration"))

        is_valid = check_email(email)
        if not is_valid:
            flash("warning", "Email is not valid")
            return redirect(url_for('registration'))

        user = db.query(User).filter_by(email=email).first()
        if user:
            flash("warning", "Email is used already")
            return redirect(url_for('registration'))

        # check if username is already taken in Database!
        user = db.query(User).filter_by(username=username).first()
        if user:
            flash("warning", "Username is already taken")
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
        flash("success", "Registration Successful!")

        # send registration confirmation email
        msg = Message(
            subject="Blog Heroku Flask App Registration successful",
            sender=SENDER,
            recipients=[email],
            bcc=[SENDER]
        )
        msg.body = f"Hi {username}!\nWelcome to our site!\n Enjoy!"
        # render_template geht mit dieser Message
        mail.send(msg)

        # set cookie for the browser

        response = make_response(redirect(url_for('index')))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
        return response

    elif request.method=="GET":
        return render_template("registration.html")


@app.route('/about', methods=["GET"])
@provide_user
def about():
    return render_template("about.html")


@app.route('/faq', methods=["GET"])
@require_session_token
def faq():
    return render_template("faq.html")


@app.route('/logout', methods=["GET"])
@provide_user
def logout():
    response = make_response(redirect(url_for('index')))
    response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, expires=0)

    user = db.query(User)\
        .filter_by(username=request.user.username)\
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
    email_recipient = request.user.email

    if request.method == "POST":
        title = request.form.get("posttitle")
        text = request.form.get("posttext")
        post = Post(
            title=title, text=text,
            user=current_user
        )
        db.add(post)
        db.commit()

        msg = Message(
            subject="A new post has been posted",
            sender=SENDER,
            recipients=[email_recipient],
        )
        msg.body = f"Hi!\nA new post has been posted\n Enjoy!"
        msg.html = render_template("new_post.html", username=current_user.username, post=post)
        mail.send(msg)

        return redirect(url_for('blog'))

    if request.method == "GET":
        posts = db.query(Post).all()
        return render_template("blog.html", posts=posts)

@app.route('/users', methods=["GET"])
@require_session_token
def users():
    current_user = request.user

    if request.method == "GET":
        allusers = db.query(User).all()
        return render_template("users.html", users=allusers)

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

        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
        commentrecipients = []

        for comment_item in comments:
            commentuserid = db.query(User).filter(User.id == comment_item.user_id).first()
            print(commentuserid.email)
            commentrecipients.append(commentuserid.email)
        commentrecipients = list(dict.fromkeys(commentrecipients))
        print(commentrecipients)

        for commentuseremail in commentrecipients:
            msg = Message(
                subject="A comment was added",
                sender=SENDER,
                recipients=[commentuseremail],
            )
            msg.body = f"Hi!\nA new comment has been added!"
            msg.html = render_template("new_comment.html", post=post)
            mail.send(msg)

        return redirect('/posts/{}'.format(post_id))

    elif request.method == "GET":
        comments = db.query(Comment).filter(Comment.post_id == post_id).all()
        return render_template('posts.html', post=post, comments=comments)


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    app.run(host='localhost', port=7890)
