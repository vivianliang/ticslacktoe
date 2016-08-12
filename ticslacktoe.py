from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ticslacktoe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
db = SQLAlchemy(app)

from models import Player


@app.route('/show', methods=['POST'])
def show_board():
    # show the current tic tac toe board
    token        = request.form.get('token')
    team_id      = request.form.get('team_id')
    channel_id   = request.form.get('channel_id')
    user_id      = request.form.get('user_id')
    user_name    = request.form.get('user_name')
    command      = request.form.get('command')
    text         = request.form.get('text')
    response_url = request.form.get('response_url')

    print token
    print user_id, user_name
    print command
    print text
    print response_url

    if text == 'show':
        data = {
            'response_type': 'in_channel',
            'text': 'Current tic tac toe board',
            'attachments': [
                {
                    'pretext': user_id
                },
                {
                    'text': 'show board %s' % user_name
                }
            ]
        }
    else:
        # request_user = Player.query.filter_by(user_id=user_id).first()
        # if request_user is None:
        #     player = Player()

        data = {
            'response_type': 'in_channel',
            'text': 'Current tic tac toe board',
            'attachments': [
                {
                    'pretext': user_id
                },
                {
                    'text': 'play %s' % user_name
                }
            ]
        }

    return jsonify(data)


@app.route('/')
def hello_world():
    return 'Hello, World!'
