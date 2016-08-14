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
PIECES_PER_ROW = 3


def response_data(text):
    data = {
        'response_type': 'in_channel',
        'text': 'Current tic tac toe board',
        'attachments': [
            {
                'text': '%s' % text
            },
        ]
    }
    return jsonify(data)

def default_response_data():
    return response_data("""
        /ticslacktoe showboard
        /ticslacktoe startgame [username]
        /ticslacktoe play [x] [y], where x and y are coordinates 0-2 on the board
        """)

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

    if len(args) == 0:
        return default_response_data()

    if args[0] == 'showboard':
        return show_board(current_game)

    # /ticslacktoe startgame [username]
    elif args[0] == 'startgame':
        if len(args) < 2:
            return response_data('invalid arguments. to start: /ticslacktoe startgame [username]')

        requested_player_name = args[1]

        # TODO: verify that specified user is in the channel (RTM API)

        if current_game is not None:
            is_done = current_game.pieces.count() == MAX_PIECES
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

        try:
            x, y = int(args[1]), int(args[2])
        except ValueError:
            return response_data('positions x and y must be integers between 0 and 2')

        if x < 0 or x > 2 or y < 0 or y > 2:
            return response_data('positions x and y must be integers between 0 and 2')

        return play(current_game, team_id, user_name, x, y)

    else:
        return default_response_data()

def show_board(current_game):
    if current_game is not None:
        pieces = current_game.pieces.order_by(Piece.position_y, Piece.position_x).all()
        pieces = []
        for y in xrange(2, -1, -1):
            for x in xrange(3):
                piece = current_game.pieces.filter_by(position_x=x, position_y=y).first()
                if piece is None:
                    pieces.append(' ')
                elif piece.player is current_game.player1:
                    pieces.append('X')
                else:
                    pieces.append('O')
    else:
        pieces = [' ' for x in xrange(9)]

    board = "|%s|%s|%s|\n|%s|%s|%s|\n|%s|%s|%s|" % tuple(pieces)
    return response_data(board)

def play(current_game, team_id, user_name, x, y):
    def is_win():
        # check for 3 pieces in the same row or column
        pieces_in_row_query = current_game.pieces.filter_by(position_x=x, player=player)
        pieces_in_col_query = current_game.pieces.filter_by(position_y=y, player=player)
        if (pieces_in_row_query.count() == PIECES_PER_ROW or
            pieces_in_col_query.count() == PIECES_PER_ROW):
            return True

        # check for 3 pieces in the north-east diagonal
        north_east_diagonal_pieces = filter(None, [
            current_game.pieces.filter_by(position_x=z, position_y=z).first() for z in xrange(3)])

        if len(north_east_diagonal_pieces) == PIECES_PER_ROW:
            return True

        # check for 3 pieces in the north-west diagonal
        coords = [(0,2), (1,1), (2,0)]
        north_west_diagonal_pieces = filter(None, [
            current_game.pieces.filter_by(position_x=i, position_y=j).first() for i, j in coords])
        return len(north_west_diagonal_pieces) == PIECES_PER_ROW

    # game has not been started
    if current_game is None or current_game.pieces.count() == MAX_PIECES:
        return response_data('must start game with: /ticslacktoe startgame [username]')

    # only the players in the current game can play
    player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
    if not player:
        return response_data("only the current players %s and %s can play" %
            (current_game.player1.user_name, current_game.player2.user_name))

    # it is not user's turn
    if player is not current_game.turn:
        return response_data("it is %s's turn" % current_game.turn.user_name)

    # the position on the board is already taken
    if Piece.query.filter_by(game=current_game, position_x=x, position_y=y).first():
        return response_data("position %d %d is already taken" % (x, y))

    # add the game piece
    piece = Piece(current_game, player, x, y)
    db.session.add(piece)

    # change the turn of the game
    other = current_game.player2 if player is current_game.player1 else current_game.player1
    current_game.turn = other
    db.session.commit()

    # check for win
    if is_win():
        return response_data("%s is the winner" % player.user_name)

    return response_data('playing turn')

@app.route('/hello')
def hello_world():
    return jsonify('Hello, World!')
