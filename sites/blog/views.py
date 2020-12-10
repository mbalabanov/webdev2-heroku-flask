from flask import render_template, request, redirect, url_for, Blueprint
from flask_mail import Message

from extensions import db, mail
from model import Post, Comment
from sites import SENDER, HOST_ADDR, require_session_token

blueprint = Blueprint("blog", __name__, url_prefix="/blog", static_folder="../../static")

@blueprint.route('/posts', methods=["GET", "POST"])
@require_session_token
def posts():
    current_user = request.user

    if request.method == "POST":

        title = request.form.get("posttitle")
        text = request.form.get("posttext")
        post = Post(
            title=title, text=text,
            user=current_user
        )
        db.session.add(post)
        db.session.commit()

        # send notification email
        msg = Message(
            subject="WebDev Blog - Posted a post",
            sender=SENDER,
            recipients=[current_user.email]
        )

        full_post_link = HOST_ADDR + url_for('blog.post', post_id=post.id)

        msg.body = f"Hi {current_user.username}!\n" \
                   f"There is news, check this out:{full_post_link}\n" \
                   f"Enjoy!"
        msg.html = render_template("new_post.html",
                                   username=current_user.username,
                                   link=f"{full_post_link}",
                                   post=post)
        mail.send(msg)

        return redirect(url_for('blog.posts'))

    if request.method == "GET":
        posts = Post.query.all()
        return render_template("posts.html", posts=posts, user=request.user, active1="active")


@blueprint.route('/posts/<post_id>', methods=["GET", "POST"])
@require_session_token
def post(post_id):
    current_user = request.user
    post = Post.query.filter(Post.id == post_id).first()

    if request.method == "POST":

        text = request.form.get("text")
        comment = Comment(
            text=text,
            post=post,
            user=current_user
        )
        db.session.add(comment)
        db.session.commit()
        return redirect(url_for("blog.post", post_id=post.id))

    elif request.method == "GET":
        comments = Comment.query.filter(Comment.post_id == post_id).all()
        return render_template('post.html', post=post, comments=comments, user=request.user, active1="active")