from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, abort
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, emit
import asyncio
import uuid
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from utils import save_media
from datetime import datetime, timezone



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


# User model for authentication
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    posts = db.relationship('Post', backref='users_post', lazy=True)

    def __init__(self, username, password_hash):
        self.username = username
        self.password_hash = password_hash


class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    post_text = db.Column(db.String(255), nullable=False)
    post_media = db.Column(db.String(255), nullable=True)
    is_published = db.Column(db.Boolean, default=False)
    date_created = db.Column(db.DateTime, default=datetime.now(timezone.utc))
    scheduled_time = db.Column(db.DateTime, nullable=True)  # Changed default to nullable

    def __init__(self, post_text, post_media=None, is_published=False, user_id=None, scheduled_time=None):
        self.post_text = post_text
        self.post_media = post_media
        self.is_published = is_published
        self.user_id = user_id
        self.scheduled_time = scheduled_time


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

# Define unauthorized handler to redirect users to the login page
@login_manager.unauthorized_handler
def unauthorized_callback():
    flash("You must be logged in to access this page.", "error")
    return redirect(url_for('login'))

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
@login_required  # Ensure only logged-in users can access this route
def index():
    user = current_user  # Get the current logged-in user object
    
    # Get all published posts
    published_posts = Post.query.filter_by(user_id=user.id, is_published=True).all()
    # Get all unpublished posts
    unpublished_posts = Post.query.filter_by(user_id=user.id, is_published=False).all()

    return render_template('index.html', user=user, published_posts=published_posts, unpublished_posts=unpublished_posts)

@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/add', methods=['POST'])
@login_required
def add_post():
    post_text = request.form['post_text']
    post_media = request.files['post_media']
    schedule_time_str = request.form.get('schedule_time')  # Get scheduled time from form

    user_id = current_user.id
    user = User.query.get(user_id)  # Assuming you're using the primary key for user lookup

    if post_media.filename == '' and post_text == '':
        flash("No content provided.", 'failed')
        return redirect(url_for('index'))

    media_path = ""
    if post_media.filename != '':
        media_path = save_media(post_media)

    if schedule_time_str:
        try:
            scheduled_time = datetime.strptime(schedule_time_str, '%m/%d/%Y %I:%M %p')
        except ValueError:
            flash("Invalid date format. Please use MM/DD/YYYY H:MM AM/PM format.", 'failed')
            return redirect(url_for('index'))
    else:
        scheduled_time = None

    new_post = Post(
        post_text=post_text,
        post_media=media_path,
        is_published=False,
        user_id=user.id,
        scheduled_time=scheduled_time
    )

    db.session.add(new_post)
    db.session.commit()

    posts = Post.query.all()
    for post in posts:
        print(post.id, post.post_text, post.scheduled_time, post.date_created)

    flash("Post Created Successfully", 'success')

    return redirect(url_for('index'))


@app.route('/delete/<int:post_id>', methods=['GET', 'POST'])
@login_required
def delete_post(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()

    try:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash('An error occurred while deleting the post.', 'error')

    return redirect(url_for('index'))


@app.route('/edit/<int:post_id>', methods=['POST'])
@login_required
def edit_post(post_id):
    post = Post.query.filter_by(id=post_id, user_id=current_user.id).first_or_404()
    
    if request.method == 'POST':
        post_text = request.form['post_text']
        post_media = request.files['post_media']
        schedule_time_str = request.form.get('edit_schedule_time')

        if schedule_time_str:
            try:
                scheduled_time = datetime.strptime(schedule_time_str, '%m/%d/%Y %I:%M %p')
                print(scheduled_time)
            except ValueError:
                flash("Invalid date format. Please use MM/DD/YYYY H:MM AM/PM format.", 'failed')
                return redirect(url_for('index'))
        else:
            scheduled_time = None

        if post_media.filename != '':
            media_path = save_media(post_media)
            post.post_media = media_path

        post.post_text = post_text
        post.scheduled_time = scheduled_time

        db.session.commit()

        flash("Post updated successfully", 'success')

    return redirect(url_for('index'))


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user_id = current_user.id
    user = User.query.filter_by(id=user_id).first()  # Retrieve the user object from the database
    settings = Settings.query.filter_by(user_id=user_id).first()

    if request.method == 'POST':
        # Process form data
        posts_per_day = request.form.get('postsPerDay')
        weekly_schedule = ','.join(request.form.getlist('weeklySchedule'))
        recycle_post_after = request.form.get('recyclePostAfter')

        # Get user's existing settings if they exist
        settings = Settings.query.filter_by(user_id=user_id).first()

        if settings:
            # Update settings
            settings.posts_per_day = posts_per_day
            settings.weekly_schedule = weekly_schedule
            settings.recycle_post_after = recycle_post_after
        else:
            # Create new settings for the user
            settings = Settings(user_id=user_id, posts_per_day=posts_per_day, weekly_schedule=weekly_schedule, recycle_post_after=recycle_post_after)
            db.session.add(settings)

            print(settings.posts_per_day, settings.weekly_schedule, settings.recycle_post_after, settings.user_id)

        db.session.commit()

        flash("Settings saved successfully", 'success')
        return redirect(url_for('settings'))
    else:
        return render_template('settings.html', user=user, settings=settings)


@app.route('/post/<int:post_id>', methods=['GET'])
@login_required
def post(post_id):
    post = Post.query.filter_by(user_id=current_user.id, id=post_id).first()

    if post:
        post.is_published = True
        db.session.commit()
        flash('Post published successfully.', 'success')
    else:
        flash('Post not found.', 'error')

    return redirect(url_for('index'))








if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
    # socketio.run(app, debug=True, use_reloader=False)
