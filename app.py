from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session
from werkzeug.utils import secure_filename
from flask_session import Session
from werkzeug.security import generate_password_hash, check_password_hash
import os
from pdf2docx import Converter
from flask_socketio import SocketIO, emit
import asyncio
import uuid  # Import the uuid module



app = Flask(__name__)
# app.secret_key = '_5#y2L"F4Q8z\n\xec]/'
app.config['SECRET_KEY'] = '_5#y2L"F4Q8z\n\xec]/'
socketio = SocketIO(app)

app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['SESSION_USE_SIGNER'] = True
# app.config["PERMANENT_SESSION_LIFETIME"] = 300
app.config['UPLOAD_FOLDER'] = './files/uploads'
app.config['OUTPUT_FOLDER'] = './files/outputs'

# Global dictionary to store selected formats
selected_formats = {}

def get_file_list(folder):
    return [{'id': id, 'filename': filename} for id, filename in enumerate(os.listdir(folder), 1)]

async def convert_file_async(input_file_path, output_file_path, selected_format, user_id):
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, convert_file_sync, input_file_path, output_file_path, selected_format, user_id)

def convert_file_sync(input_file_path, output_file_path, selected_format, user_id):
    fileExt = str(input_file_path).split('.')[-1].upper()
    print(fileExt)
    if selected_format != fileExt:
            if selected_format == str("docx").upper():
                socketio.emit('flash_message', {'user_id': user_id, 'message': 'Conversion in progress...'})
                cv = Converter(input_file_path)
                cv.convert(output_file_path, start=0, end=None)
                cv.close()
                socketio.emit('flash_message', {'user_id': user_id, 'message': 'File Successfully Converted!'})
            else:
                print("select docx")
    else:
        socketio.emit('flash_message', {'user_id': user_id, 'message': f"Please select format and try again"})


def get_user_folder(user_id):
    user_upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')
    user_output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f'user_{user_id}')
    os.makedirs(user_upload_folder, exist_ok=True)
    os.makedirs(user_output_folder, exist_ok=True)


@app.route('/')
def index():
    user_id = str(session.get('user_id', None)).replace('-', '')
    if user_id:
        get_user_folder(user_id)
    else:
        # Generate a unique user_id if not present in the session
        user_id = str(uuid.uuid4().hex)[:16].replace('-', '')
        session['user_id'] = user_id
        get_user_folder(user_id)

    files = get_file_list(f"./files/uploads/user_{user_id}")
    outputs = get_file_list(f"./files/outputs/user_{user_id}")

    return render_template('index.html', user_id=user_id, files=files, outputs=outputs)


# Add this route to your Flask app
@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/add', methods=['POST'])
def add():
    user_id = str(session.get('user_id', None)).replace('-', '')  # Default user_id if not set

    file = request.files.get('file')

    if file:
        upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')
        filename = secure_filename(file.filename)
        file.save(os.path.join(upload_folder, filename))
        flash("File Uploaded Successfully")

    return redirect(url_for('index'))

@app.route('/convert/<int:file_id>')
async def convert(file_id):

    user_id = str(session.get('user_id', None)).replace('-', '')
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f'user_{user_id}')

    files = get_file_list(upload_folder)
    input_file_path = os.path.join(upload_folder, files[file_id - 1]['filename'])
    output_file_path = os.path.join(output_folder, files[file_id - 1]['filename'].replace(".pdf", ".docx"))

    # Fetch the selected format from the global dictionary
    selected_format = selected_formats.get(str(file_id))

    if selected_format:
        try:
            # Use the selected format in your conversion logic
            print(selected_format)
            await convert_file_async(input_file_path, output_file_path, selected_format, user_id)
        except Exception as e:
            socketio.emit('flash_message', {'user_id': user_id, 'message': f'Error during conversion: {str(e)}'})
    else:
        socketio.emit('flash_message', {'user_id': user_id, 'message': 'Error fetching selected format'})

    return redirect(url_for('index'))


@app.route('/download/<int:file_id>')
def download(file_id):
    user_id = str(session.get('user_id', None)).replace('-', '')
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f'user_{user_id}')

    try:
        files = get_file_list(output_folder)
        file_path = os.path.join(output_folder, files[file_id - 1]['filename'])
        flash('File Downloaded Successfully')
        return send_file(file_path, as_attachment=True)
    except IndexError:
        flash("Error Downloading File")
        return "File not found", 404


@app.route('/delete/<int:file_id>')
def delete(file_id):
    user_id = str(session.get('user_id', None)).replace('-', '')
    upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], f'user_{user_id}')

    try:
        files = get_file_list(upload_folder)
        file_path = os.path.join(upload_folder, files[file_id - 1]['filename'])
        os.remove(file_path)
        flash("File Deleted Successfully")

    except (IndexError, OSError) as e:
        flash("Error Deleting File")
        return f"Error deleting file: {str(e)}", 500

    return redirect(url_for('index'))


@app.route('/delete_converted/<int:file_id>')
def delete_converted(file_id):
    user_id = str(session.get('user_id', None)).replace('-', '')
    output_folder = os.path.join(app.config['OUTPUT_FOLDER'], f'user_{user_id}')

    try:
        output_files = get_file_list(output_folder)
        file_path = os.path.join(output_folder, output_files[file_id - 1]['filename'])
        os.remove(file_path)
        flash("File Deleted Successfully")
    except (IndexError, OSError) as e:
        flash("Error Deleting File")
        return f"Error deleting converted file: {str(e)}", 500

    return redirect(url_for('index'))

@app.route('/update_format', methods=['POST'])
def update_format():
    selected_format = request.form['selected_format']
    print(selected_format)
    file_id = request.form['file_id']
    print(selected_format, file_id)

    # Update the selected format in the global dictionary
    selected_formats[file_id] = selected_format
    return 'Format updated successfully'

if __name__ == '__main__':
    socketio.run(app,debug=True, use_reloader=False)

