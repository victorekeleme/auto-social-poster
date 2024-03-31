import os
from werkzeug.utils import secure_filename

def save_media(media_file):
    # Ensure the uploads directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    # Save the media file to the uploads directory
    filename = secure_filename(media_file.filename)
    media_path = os.path.join('uploads', filename)
    media_file.save(media_path)
    
    return media_path


# function for scheduling posts

def scheduler(schedule):
    pass
