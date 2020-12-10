import datetime
import hashlib
import logging
import uuid

from flask import render_template, request, make_response, redirect, url_for, flash, Blueprint
from flask_mail import Message

from extensions import db, mail
from model import User
from sites import provide_user, WEBSITE_LOGIN_COOKIE_NAME, SENDER, HOST_ADDR, check_email, COOKIE_DURATION, \
    require_session_token

blueprint = Blueprint("user", __name__, url_prefix="/users", static_folder="../../static")

@blueprint.route('/login', methods=["GET", "POST"])
@provide_user
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        # right way to find user with correct password
        user = User.query \
            .filter(User.username == username, User.password_hash == password_hash) \
            .first()

        session_cookie = str(uuid.uuid4())
        expiry_time = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)

        if user is None:
            flash("Username or password is wrong", "warning")
            logging.info(f"User {username} failed to login with wrong password.")
            redirect_url = request.args.get('redirectTo', url_for('main.index'))
            return redirect(url_for('user.login', redirectTo=redirect_url))
        else:
            user.session_cookie = session_cookie
            user.session_expiry_datetime = expiry_time
            db.session.add(user)
            db.session.commit()
            logging.info(f"User {username} is logged in")

        redirect_url = request.args.get('redirectTo', url_for('main.index'))
        response = make_response(redirect(redirect_url))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
        return response

    elif request.method == "GET":
        cookie = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        user = None

        if cookie is not None:
            user = User.query \
                .filter_by(session_cookie=cookie) \
                .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
                .first()

        if user is None:
            logged_in = False
        else:
            logged_in = True

        return render_template("login.html", logged_in=logged_in, user=request.user)


@blueprint.route("/registration", methods=["GET", "POST"])
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
            return redirect(url_for("user.registration"))

        if password != repeat:
            flash("Password and repeat did not match!", "warning")
            return redirect(url_for("user.registration"))

        # check if email is already taken:
        user = User.query.filter_by(email=email).first()
        if user:
            flash("Email is already taken", "warning")
            return redirect(url_for("user.registration"))

        # check if username is already taken in Database!
        user = User.query.filter_by(username=username).first()
        if user:
            flash("Username is already taken", "warning")
            return redirect(url_for('user.registration'))

        password_hash = hashlib.sha256(password.encode()).hexdigest()
        session_cookie = str(uuid.uuid4())

        session_expiry_datetime = datetime.datetime.now() + datetime.timedelta(seconds=COOKIE_DURATION)

        user = User(username=username,
                    email=email,
                    password_hash=password_hash,
                    session_cookie=session_cookie,
                    session_expiry_datetime=session_expiry_datetime)
        db.session.add(user)
        db.session.commit()
        flash("Registration Successful!", "success")

        # send registration confirmation email
        msg = Message(
            subject="WebDev Blog - Registration Successful",
            sender=SENDER,
            recipients=[email],
            bcc=[SENDER]
        )
        msg.body = f"Hi {username}!\n" \
                   f"Welcome to our WebDev Flask site!\n" \
                   f"Visit us: {HOST_ADDR}\n" \
                   f"Enjoy!"
        mail.send(msg)

        # set cookie for the browser
        response = make_response(redirect(url_for('main.index')))
        response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, session_cookie, httponly=True, samesite='Strict')
        return response

    elif request.method == "GET":
        return render_template("registration.html", user=request.user, active0="active")

@blueprint.route('/users', methods=["GET"])
@require_session_token
def users():
    current_user = request.user

    if request.method == "GET":
        allusers = User.query.all()
        return render_template("users.html", users=allusers, user=request.user, active2="active")

@blueprint.route('/logout', methods=["GET"])
@provide_user
def logout():
    response = make_response(redirect(url_for('main.index')))
    response.set_cookie(WEBSITE_LOGIN_COOKIE_NAME, expires=0)

    user = User.query \
        .filter_by(username=request.user.username) \
        .first()

    if user is not None:
        # reset user
        user.session_expiry_datetime = None
        user.session_cookie = None
        db.session.add(user)
        db.session.commit()
        logging.info(f"{user.username} has logged out.")

    return response

