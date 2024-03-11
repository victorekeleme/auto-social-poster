from flask import Flask, render_template, request, redirect, url_for, send_file, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.utils import secure_filename 
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pdf2docx import Converter
from flask_socketio import SocketIO, emit
import asyncio
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.secret_key = "abc"
db = SQLAlchemy()
login_manager = LoginManager(app)
login_manager.login_view = 'login'

socketio = SocketIO(app)

app.config['UPLOAD_FOLDER'] = './files/uploads'
app.config['OUTPUT_FOLDER'] = './files/outputs'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)



def get_file_list(folder):
    return [{'id': id, 'filename': filename} for id, filename in enumerate(os.listdir(folder), 1)]

async def convert_file_async(pdf_path, docx_path):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, convert_file_sync, pdf_path, docx_path)

def convert_file_sync(pdf_path, docx_path):
    cv = Converter(pdf_path)
    cv.convert(docx_path, start=0, end=None)
    cv.close()


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(20), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout successful!', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    return f'Hello, {current_user.id}! This is the dashboard.'


# Route to create a user
@app.route('/create_user')
def create_user():
    # Replace 'testuser' and 'password123' with your desired username and password
    username = 'user1'
    password = 'user1'

    # Check if the username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists', 'warning')
        return redirect(url_for('index'))

    # Hash the password before storing it in the database
    hashed_password = generate_password_hash(password, method='sha256')

    # Create a new user instance
    new_user = User(username=username, password=hashed_password)

    # Add the new user to the database session
    db.session.add(new_user)

    # Commit the changes to the database
    db.session.commit()

    flash('User created successfully!', 'success')
    return redirect(url_for('index'))


@app.route('/')
def index():
    files = get_file_list('./files/uploads')
    outputs = get_file_list('./files/outputs')
    return render_template('index.html', files=files, outputs=outputs)

@app.route('/add', methods=['POST'])
def add():
    file = request.files.get('file')

    if file:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        socketio.emit('flash_message', {'message': "File Uploaded Successfully"})

    return redirect(url_for('index'))

@app.route('/convert/<int:file_id>')
async def convert(file_id):
    files = get_file_list('./files/uploads')
    pdf_to_convert = os.path.join(app.config['UPLOAD_FOLDER'], files[file_id - 1]['filename'])
    docx_to_output = os.path.join(app.config['OUTPUT_FOLDER'], files[file_id - 1]['filename'].replace(".pdf", ".docx"))


    socketio.emit('flash_message', {'message': 'Conversion in progress...'})
    
    await convert_file_async(pdf_to_convert, docx_to_output)

    socketio.emit('flash_message', {'message': 'File Successfully Converted!'})

    return redirect(url_for('index'))

@app.route('/download/<int:file_id>')
def download(file_id):
    output_files = get_file_list('./files/outputs')

    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_files[file_id - 1]['filename'])
        flash("File Downloaded Successfully")
        return send_file(file_path, as_attachment=True)
    except IndexError:
        flash("Error Downloading File")
        return "File not found", 404

@app.route('/delete/<int:file_id>')
def delete(file_id):
    files = get_file_list('./files/uploads')
    try:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], files[file_id - 1]['filename'])
        os.remove(file_path)
        socketio.emit('flash_message', {'message': "File Deleted Successfully"})

    except (IndexError, OSError) as e:
        flash("Error Deleting File")
        return f"Error deleting file: {str(e)}", 500

    return redirect(url_for('index'))

@app.route('/delete_converted/<int:file_id>')
def delete_converted(file_id):
    output_files = get_file_list('./files/outputs')
    try:
        file_path = os.path.join(app.config['OUTPUT_FOLDER'], output_files[file_id - 1]['filename'])
        os.remove(file_path)
        socketio.emit('flash_message', {'message': "File Deleted Successfully"})
    except (IndexError, OSError) as e:
        flash("Error Deleting File")
        return f"Error deleting converted file: {str(e)}", 500

    return redirect(url_for('index'))

# @socketio.on('connect')
# def handle_connect():
#     print('Client connected')

# @app.route('/initdb')
# def init_db():
#     db.create_all()
#     flash('Database initialized successfully!', 'info')
#     return redirect(url_for('index'))

if __name__ == '__main__':
    socketio.run(app,debug=True)
