import logging
import os
import sys

from flask import Flask, render_template, request, blueprints
from flask_wtf.csrf import CSRFError

import email_config
from extensions import csrf_protect, db, mail, migrate
from sites import main, blog, user, provide_user


CONFIG = dict(
    DEBUG=True,
    MAIL_SERVER=os.getenv("MAIL_SERVER", email_config.MAIL_SERVER),
    MAIL_PORT=int(os.getenv("MAIL_PORT", email_config.MAIL_PORT)),
    MAIL_USE_SSL=True,
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", email_config.MAIL_USERNAME),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", email_config.MAIL_PASSWORD),
    SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///blog.sqlite"),
    SQLALCHEMY_TRACK_MODIFICATIONS=True
)


def register_extensions(app):
    db.init_app(app)
    mail.init_app(app)
    csrf_protect.init_app(app)
    migrate.init_app(app, db)


def register_blueprints(app):
    app.register_blueprint(blog.views.blueprint)
    app.register_blueprint(user.views.blueprint)
    app.register_blueprint(main.views.blueprint)


def create_app():
    app = Flask(__name__.split(".")[0])
    app.config.update(CONFIG)
    app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

    register_extensions(app)
    register_blueprints(app)

    configure_logger(app)

    return app


def configure_logger(app):
    handler = logging.StreamHandler(sys.stdout)
    if not app.logger.handlers:
        app.logger.addHandler(handler)


app = create_app()


@app.errorhandler(404)
@provide_user
def page_not_found(e):
    return render_template('404.html', user=request.user, reason=e.description), 404


@app.errorhandler(500)
@provide_user
def server_error(e):
    return render_template('500.html', user=request.user, reason=e.description), 500


@app.errorhandler(CSRFError)
@provide_user
def server_error(e):
    return render_template('csrf_error.html', user=request.user, reason=e.description), 300


if __name__ == '__main__':
    LOCALHOST_NAME = "localhost"
    LOCALHOST_PORT = 7890
    app.run(host=LOCALHOST_NAME, port=LOCALHOST_PORT)
