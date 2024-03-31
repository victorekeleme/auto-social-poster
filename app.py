from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import asyncio
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required
from utils import save_media
from datetime import datetime



app = Flask(__name__)

# app.config['SESSION_TYPE'] = 'filesystem'
# app.config['SESSION_PERMANENT'] = True
# app.config['SESSION_USE_SIGNER'] = True
app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///posts.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    post_text = db.Column(db.String(255), nullable=False)
    post_media = db.Column(db.String(255), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, post_text, post_media=None, is_published=False):
        self.post_text = post_text
        self.post_media = post_media
        self.is_published = is_published

# User model for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    settings = db.relationship('Settings', backref='user', uselist=False)

# Define Settings model with foreign key to User
class Settings(db.Model):
    __tablename__ = 'settings'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Corrected foreign key reference
    posts_per_day = db.Column(db.Integer, nullable=True)
    weekly_schedule = db.Column(db.String(255), nullable=True)
    recycle_post_after = db.Column(db.Integer, nullable=True)


# User loader function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists. Please choose a different one.', 'error')
            return redirect(url_for('register'))

        # Hash the password
        hashed_password = generate_password_hash(password)

        # Create a new user
        new_user = User(username=username, password_hash=hashed_password)
        db.session.add(new_user)
        db.session.commit()

        flash('User registered successfully. Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register_user.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user)  # Use Flask-Login's login_user function
            flash('Logged in successfully', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required  # Protect logout route, ensuring only logged-in users can access it
def logout():
    logout_user()  # Use Flask-Login's logout_user function
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))


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


# @app.route('/settings', methods=['GET', 'POST'])
# def settings():

#     if request.method == 'POST':
#         # Process form data
#         posts_per_day = request.form.get('postsPerDay')
#         weekly_schedule = ','.join(request.form.getlist('weeklySchedule'))
#         recycle_post_after = request.form.get('recyclePostAfter')
        
#         # Do something with the settings data, such as updating the database
#         new_settings = Settings(posts_per_day=posts_per_day, weekly_schedule=weekly_schedule, recycle_post_after=recycle_post_after)
        
#         db.session.add(new_settings)
#         db.session.commit()

#         # For demonstration purposes, let's just print the received data
#         print("Posts Per Day:", posts_per_day)
#         print("Weekly Schedule:", weekly_schedule)
#         print("Recycle Post After:", recycle_post_after)
        
#         flash("Settings saved successfully", 'success')
#         # Redirect to a success page or render a template
#         return redirect(url_for('settings'))
#     else:
#         # Render the settings page template
#         return render_template('settings.html')


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    user_id = session.get('user_id')
    user = User.query.filter_by(id=user_id).first()  # Retrieve the user object from the database

    if request.method == 'POST':
        # Process form data
        posts_per_day = request.form.get('postsPerDay')
        weekly_schedule = ','.join(request.form.getlist('weeklySchedule'))
        recycle_post_after = request.form.get('recyclePostAfter')

        # Update the user's settings if they exist, otherwise create new settings
        if user.settings:
            user.settings.posts_per_day = posts_per_day
            user.settings.weekly_schedule = weekly_schedule
            user.settings.recycle_post_after = recycle_post_after
        else:
            new_settings = Settings(posts_per_day=posts_per_day, weekly_schedule=weekly_schedule, recycle_post_after=recycle_post_after)
            user.settings = new_settings

        db.session.commit()

        flash("Settings saved successfully", 'success')
        return redirect(url_for('settings'))
    else:
        return render_template('settings.html', user=user)



if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
    # socketio.run(app, debug=True, use_reloader=False)
