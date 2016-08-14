import os

from flask import Flask, jsonify, request
# from flask_api import status
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
db = SQLAlchemy(app)

from models import Game, Piece, Player

MAX_PIECES = 9


def response_data(text):
    data = {
        'response_type': 'in_channel',
        'text': 'Current tic tac toe board',
        'attachments': [
            {
                'text': '%s' % (text)
            }
        ]
    }
    return jsonify(data)

def get_or_create_player(team_id, user_name):
    player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
    if not player:
        player = Player(team_id=team_id, user_name=user_name)
        db.session.add(player)
        db.session.commit()
    return player


@app.route('/', methods=['POST'])
def tic_slack_toe():
    token        = request.form.get('token')
    team_id      = request.form.get('team_id')
    channel_id   = request.form.get('channel_id')
    user_id      = request.form.get('user_id')
    user_name    = request.form.get('user_name')
    command      = request.form.get('command')
    text         = request.form.get('text')
    response_url = request.form.get('response_url')

    if token != '6quahLsQgU7EJIOoENkl66vp':
        return response_data('unauthorized')

    # TODO: validate team_id, channel_id, user_id, user_name (RTM API)

    args = text.split()

    current_game = (Game.query
        .filter_by(team_id=team_id, channel_id=channel_id)
        .order_by(Game.id.desc())
        .first())

    # /ticslacktoe showboard
    if args[0] == 'showboard':
        # show board for current channel
        pieces = [' ' for x in xrange(9)]
        board = """|%s|%s|%s|\n|%s|%s|%s|\n|%s|%s|%s|""" % tuple(pieces)
        return response_data(board)

    # /ticslacktoe startgame [username]
    elif args[0] == 'startgame':
        if len(args) < 2:
            return response_data('invalid arguments. to start: /ticslacktoe startgame [username]')
        requested_player_name = args[1]

        # TODO: verify that specified user is in the channel (RTM API)

        if current_game is not None:
            is_done = len(current_game.pieces) == MAX_PIECES
            if not is_done:
                return response_data('game is in progress')

        player1 = get_or_create_player(team_id, user_name)
        player2 = get_or_create_player(team_id, requested_player_name)

        game = Game(team_id, channel_id, player1, player2)
        db.session.add(game)
        db.session.commit()

        return response_data('new game started between %s and %s' %
            (player1.user_name, player2.user_name))

    # /ticslacktoe play [x] [y], where x and y are from 0-2
    elif args[0] == 'play':
        if len(args) < 3:
            return response_data('invalid arguments. to play: /ticslacktoe play [x] [y]')

        x = int(args[1])
        y = int(args[2])
        if x > 2 or y > 2:
            return response_data('positions x and y must be between 0 and 2')

        if current_game is None or len(current_game.pieces) == MAX_PIECES:
            return response_data('must start game with: /ticslacktoe startgame [username]')

        player1 = current_game.player1.user_name
        player2 = current_game.player2.user_name

        # only the players in the current game can play
        player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
        if not player:
            return response_data("""
                only the current players %s and %s can play.
                any user can display the current board: /ticslacktoe showboard
                """ % (player1, player2))

        if player is not current_game.turn:
            return response_data('it is %s\'s turn' % current_game.turn.user_name)

        return response_data('playing turn')

    return response_data('the end')


@app.route('/hello')
def hello_world():
    return jsonify('Hello, World!')
