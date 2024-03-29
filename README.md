set FLASK_APP=app
flask db stamp head
flask db migrate
flask db upgrade