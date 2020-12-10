from flask import render_template, request, Blueprint

from sites import provide_user, require_session_token

blueprint = Blueprint("main", __name__, url_prefix="/", static_folder="../../static")

@blueprint.route('/', methods=["GET"])
@provide_user
def index():
    return render_template("index.html", user=request.user)

@blueprint.route('/about', methods=["GET"])
@provide_user
def about():
    return render_template("about.html", user=request.user, active4="active")

@blueprint.route('/js-example', methods=["GET"])
def jsexample():
    return render_template("js-example.html")

@blueprint.route('/js-example2', methods=["GET"])
def jsexample2():
    return render_template("js-example2.html")

@blueprint.route('/faq', methods=["GET"])
@require_session_token
def faq():
    return render_template("faq.html", user=request.user, active3="active")