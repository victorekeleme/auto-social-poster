from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import asyncio
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from utils import save_media


app = Flask(__name__)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True

app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    post_text = db.Column(db.String(255), nullable=False)
    post_media = db.Column(db.String(255), nullable=True)  # Changed from post_video_link
    is_published = db.Column(db.Boolean, default=False)

    def __init__(self, post_text, post_media=None, is_published=False):
        self.post_text = post_text
        self.post_media = post_media
        self.is_published = is_published



@app.route('/')
def index():
    user_id = str(session.get('user_id', None)).replace('-', '')
    # Get all published posts
    published_posts = Post.query.filter_by(is_published=True).all()
    # Get all unpublished posts
    unpublished_posts = Post.query.filter_by(is_published=False).all()

    if user_id:
        session['user_id'] = user_id
    else:
        user_id = str(uuid.uuid4().hex)[:16].replace('-', '')
        session['user_id'] = user_id
        
    return render_template('index.html', user_id=user_id, published_posts=published_posts, unpublished_posts=unpublished_posts )

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add', methods=['POST'])
def add_post():
    post_text = request.form['post_text']
    post_media = request.files['post_media']  # Update from post_video

    if post_media.filename == '' and post_text == '':
        flash("No content provided.", 'failed')
        return redirect(url_for('index'))

    if post_media.filename == '':
        media_path = ""
    else:
        media_path = save_media(post_media)  # Update the saving function for media

    new_post = Post(post_text=post_text, post_media=media_path, is_published=False)

    db.session.add(new_post)
    db.session.commit()

    flash("Post Created Successfully", 'success')

    return redirect(url_for('index'))


@app.route('/delete/<int:post_id>', methods=['GET','POST'])
def delete_post(post_id):
    # Query the post by its ID
    post = Post.query.get_or_404(post_id)

    try:
        # Delete the post from the database
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully.', 'success')
    except:
        db.session.rollback()
        flash('An error occurred while deleting the post.', 'error')

    # Redirect to the home page or wherever you want after deleting the post
    return redirect(url_for('index'))


@app.route('/edit/<int:post_id>', methods=['POST'])
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)

    if request.method == 'POST':
        post_text = request.form['post_text']
        post_media = request.files['post_media']  # Update from post_video

        post.post_text = post_text

        if post_media.filename != '':
            media_path = save_media(post_media)  # Update the saving function for media
            post.post_media = media_path

        db.session.commit()

        flash("Post updated successfully", 'success')

        return redirect(url_for('index'))

    return redirect(url_for('index'))


@app.route('/settings')
def settings():
    return render_template('settings.html')


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
    # socketio.run(app, debug=True, use_reloader=False)
