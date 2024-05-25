import requests
from flask import session

# Endpoint for posting tweets
TWEET_URL = "https://api.twitter.com/2/tweets"

@app.route("/tweet", methods=["POST"])
def post_tweet():
    access_token = session.get("access_token")  # Retrieve the stored access token

    if not access_token:
        return "Access token not found.", 401  # Unauthorized if no token

    tweet_content = "Hello, Twitter!"  # Content of the tweet

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    data = {
        "text": tweet_content  # Tweet text content
    }

    response = requests.post(TWEET_URL, headers=headers, json=data)

    if response.status_code == 201:  # HTTP 201 means the tweet was created
        return "Tweet posted successfully!"
    else:
        return f"Failed to post tweet. Status code: {response.status_code}"
