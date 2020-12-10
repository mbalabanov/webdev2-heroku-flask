import datetime
import logging
import os
import re

from flask import request, redirect, url_for

from model import User

LOCALHOST_NAME = "localhost"
LOCALHOST_PORT = 7890

HOST_ADDR = os.getenv("HOST_ADDR", f'http://{LOCALHOST_NAME}:{LOCALHOST_PORT}')

EMAIL_REGEX = '^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'

SENDER = "@gmail.com"

WEBSITE_LOGIN_COOKIE_NAME = "science/session_token"
COOKIE_DURATION = 900  # in seconds

def check_email(email: str) -> bool:
    return bool(re.search(EMAIL_REGEX, email))

def require_session_token(func):
    """Decorator to require authentication to access routes"""

    def wrapper(*args, **kwargs):
        session_token = request.cookies.get(WEBSITE_LOGIN_COOKIE_NAME)
        redirect_url = request.path or '/'

        if not session_token:
            logging.error('no token in request')
            return redirect(url_for('login', redirectTo=redirect_url))

        user = User.query \
            .filter_by(session_cookie=session_token) \
            .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
            .first()

        if not user:
            logging.error(f'token {session_token} not valid')
            return redirect(url_for('login', redirectTo=redirect_url))

        logging.info(
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

        user = User.query \
            .filter_by(session_cookie=session_token) \
            .filter(User.session_expiry_datetime >= datetime.datetime.now()) \
            .first()

        request.user = user
        return func(*args, **kwargs)

    wrapper.__name__ = func.__name__
    return wrapper