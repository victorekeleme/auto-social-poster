import os
from werkzeug.utils import secure_filename
import requests
from datetime import datetime


def save_media(media_file):
    # Ensure the uploads directory exists
    if not os.path.exists('uploads'):
        os.makedirs('uploads')

    # Save the media file to the uploads directory
    filename = secure_filename(media_file.filename)
    media_path = os.path.join('uploads', filename)
    media_file.save(media_path)
    
    return media_path


def schedule_post(post_id, scheduled_time):
    # Define the endpoint URL (adjust the URL and port as needed)
    url = "http://localhost:5000/schedule"

    # Convert datetime to a JSON-serializable format
    if isinstance(scheduled_time, datetime):
        scheduled_time_str = scheduled_time.isoformat()  # Converts datetime to ISO 8601 format
    else:
        scheduled_time_str = str(scheduled_time)  # Convert non-datetime objects to strings

    # Create the data to send in the POST request
    data = {
        "post_id": post_id,
        "scheduled_time": scheduled_time_str  # Use the string format
    }
    # Send the POST request with JSON data
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})

    # Check the response status
    if response.status_code == 200:
        print("Task scheduled successfully:", response.json())
    else:
        print("Error scheduling task:", response.status_code, response.text)


def cancel_schedule_post(post_id):
    # Define the endpoint URL (adjust the URL and port as needed)
    url = f"http://localhost:5000/cancel"

    # Create the data to send in the POST request
    data = {
        "post_id": post_id,
    }
    # Send the POST request with JSON data
    response = requests.post(url, json=data, headers={"Content-Type": "application/json"})

    # Check the response status
    if response.status_code == 200:
        print("Task cancelled successfully:", response.json())
    else:
        print("Error cancelling task:", response.status_code, response.text)











# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# from apscheduler.schedulers.background import BackgroundScheduler
# from datetime import datetime, timedelta

# app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'your_database_uri'
# db = SQLAlchemy(app)
# scheduler = BackgroundScheduler()

# # Define your models here

# def post_scheduler():
#     # Get all users
#     users = User.query.all()

#     for user in users:
#         # Get user settings
#         settings = Settings.query.filter_by(user_id=user.id).first()
#         if settings:
#             posts_per_day = settings.posts_per_day
#             recycle_post_after = settings.recycle_post_after

#             # Get unscheduled posts for the user
#             unscheduled_posts = Post.query.filter_by(user_id=user.id, is_published=False, scheduled_time=None).all()
#             unscheduled_posts_count = len(unscheduled_posts)

#             if unscheduled_posts_count > 0:
#                 # Schedule posts evenly throughout the day
#                 interval = timedelta(minutes=24 * 60 // posts_per_day) if posts_per_day else timedelta(hours=24)
#                 current_time = datetime.now()

#                 for i, post in enumerate(unscheduled_posts):
#                     # Calculate scheduled time for the post
#                     scheduled_time = current_time + interval * i
#                     if scheduled_time > current_time:
#                         # Schedule the post
#                         scheduler.add_job(publish_post, 'date', args=[post.id, user.id], run_date=scheduled_time)

#         # Get scheduled posts to recycle
#         scheduled_posts = Scheduler.query.filter_by(user_id=user.id).all()
#         for scheduled_post in scheduled_posts:
#             if scheduled_post.scheduled_time and scheduled_post.scheduled_time < datetime.now():
#                 # Reschedule the post
#                 scheduled_post.scheduled_time = None
#                 db.session.commit()

# scheduler.add_job(post_scheduler, 'interval', minutes=5)
# scheduler.start()

# if __name__ == '__main__':
#     app.run(debug=True)
