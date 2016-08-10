from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ticslacktoe'
heroku = Heroku(app)
db = SQLAlchemy(app)

# database models
class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player1 = db.relationship('Player')
    player1_marker = db.Column(db.String(1))

    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player2 = db.relationship('Player')
    player2_marker = db.Column(db.String(1))

    turn = db.Column(db.Integer)  # 1 or 2 for player. TODO: change to Enum

    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

    def __repr__(self):
        return '<Game %r %r>' % self.player1.username, self.player2.username

class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)
    username = db.Column(db.String(80), unique=True)

    def __init__(self, user_id, username):
        self.user_id = user_id
        self.username = username

    def __repr__(self):
        return '<Player %r>' % self.username

class Piece(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))
    game = db.relationship('Game', backref=db.backref('pieces'))

    player_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player = db.relationship('Player', backref=db.backref('pieces'))

    # (position_x,position_y), where the board looks like:
    # (0,2) (1,2) (2,2)
    # (0,1) (1,1) (2,1)
    # (0,0) (1,0) (2,0)
    position_x = db.Column(db.SmallInteger)
    position_y = db.Column(db.SmallInteger)

    def __init__(self, game, player, position_x, position_y):
        self.game = game
        self.player = player
        self.position_x = position_x
        self.position_y = position_y

    def __repr__(self):
        return '<Piece %r %r>' % self.position_x, self.position_y

@app.route('/show', methods=['POST'])
def show_board():
    # show the current tic tac toe board
    token        = request.form.get('token')
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

    data = {
        'response_type': 'in_channel',
        'text': 'Current tic tac toe board',
        'attachments': [
            {
                'text': '---|---|---'
            }
        ]
    }

    return jsonify(data)








@app.route('/')
def hello_world():
    return 'Hello, World!'

@app.route('/user/<username>')
def show_user_profile(username):
    # show the user profile for that user
    return 'User %s' % username

@app.route('/post/<int:post_id>')
def show_post(post_id):
    # show the post with the given id, the id is an integer
    return 'Post %d' % post_id
