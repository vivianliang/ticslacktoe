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

def response_data(text, color):
    data = {
        'response_type': 'in_channel',
        'attachments': [
            {
                'color': color,
                'text': '%s' % text,
                'mrkdwn_in': ['text']
            }
        ]
    }
    return jsonify(data)

def board_response_data(pretext, board, current_game, win=False):
    data = {
        'response_type': 'in_channel',
        'attachments': [
            {
                'color': 'good' if win else None,
                'pretext': pretext,
                'title': 'Current tic slack toe board',
                'text': "```%s```" % board,
                'mrkdwn_in': ['pretext', 'text']
            }
        ]
    }
    if current_game is not None and not win:
        data['attachments'].append({
                'text': """*Player 1 (X):* %s\n*Player 2 (O):* %s\n*Current turn:* %s\n""" % (
                    current_game.player1.user_name,
                    current_game.player2.user_name,
                    current_game.turn.user_name),
                'mrkdwn_in': ['text']
            })
    return jsonify(data)

def help_response_data():
    data = {
        'response_type': 'in_channel',
        'attachments': [
            {
                'title': 'Help is on the way!',
                'text': (
                    "To connect your user name, `/ticslacktoe connect`\n"
                    "To show current board, `/ticslacktoe show`\n"
                    "To start a game, `/ticslacktoe start [username]`\n"
                    "To play a move on your turn, `/ticslacktoe play [x] [y]`, where x and y are "
                    "coordinates 0-2 on the board:\n"
                    "```|0 2|1 2|2 2|\n|0 1|1 1|2 1|\n|0 0|1 0|2 0|```"
                ),
                'mrkdwn_in': ['text']
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

# def is_game_done(game):
#     return game.pieces.count() == MAX_PIECES

def get_board(current_game):
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

    return "|%s|%s|%s|\n|%s|%s|%s|\n|%s|%s|%s|" % tuple(pieces)


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
        return response_data('Unauthorized request', 'danger')

    # TODO: future improvement - verify user, team, channel via RTM API

    args = text.split()

    # TODO: now that we're deleting the game, we can just get the one and only game
    current_game = (Game.query
        .filter_by(team_id=team_id, channel_id=channel_id)
        .order_by(Game.id.desc())
        .first())

    if len(args) == 0 or args[0] == 'help':
        return help_response_data()

    if args[0] == 'connect':
        # TODO: future improvement - verify user via RTM API
        player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
        if player is not None:
            return response_data(
                'User %s has already connected to tic-slack-toe' % player.user_name, 'warning')

        player = Player(team_id=team_id, user_name=user_name)
        db.session.add(player)
        db.session.commit()
        return response_data((
            "You (%s) are now connected to tic-slack-toe. There is no need to"
            "reconnect unless your Slack user name changes.") % player.user_name, 'good')

    elif args[0] == 'show':
        return board_response_data('', get_board(current_game), current_game)

    # /ticslacktoe start [username]
    elif args[0] == 'start':
        if len(args) < 2:
            return response_data(
                'Invalid arguments. to start: `/ticslacktoe start [username]`', 'danger')

        requested_player_name = args[1]

        player2 = Player.query.filter_by(team_id=team_id, user_name=requested_player_name).first()
        if player2 is None:
            return response_data(
                "User %s needs to connect to tic-slack-toe with `/ticslacktoe connect`" %
                requested_player_name, 'danger')

        # if current_game is not None and not is_game_done(current_game):
        if current_game is not None:
            return response_data('A game is already in progress', 'warning')

        player1 = get_or_create_player(team_id, user_name)

        game = Game(team_id, channel_id, player1, player2)
        db.session.add(game)
        db.session.commit()

        return response_data('New game started between %s and %s' %
            (player1.user_name, player2.user_name), 'good')

    # /ticslacktoe play [x] [y], where x and y are from 0-2
    elif args[0] == 'play':
        if len(args) < 3:
            return response_data('Invalid arguments. to play: `/ticslacktoe play [x] [y]`', 'danger')

        try:
            x, y = int(args[1]), int(args[2])
        except ValueError:
            return response_data('Positions x and y must be integers between 0 and 2', 'danger')

        if x < 0 or x > 2 or y < 0 or y > 2:
            return response_data('Positions x and y must be integers between 0 and 2', 'danger')

        return play(current_game, team_id, user_name, x, y)

    else:
        return help_response_data()

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
    # if current_game is None or current_game.pieces.count() == MAX_PIECES:
    if current_game is None:
        return response_data('Must start game with: `/ticslacktoe start [username]`', 'warning')

    # only the players in the current game can play
    player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
    if not player:
        return response_data("Only the current players %s and %s can play" %
            (current_game.player1.user_name, current_game.player2.user_name), 'warning')

    # it is not user's turn
    if player is not current_game.turn:
        return response_data("It is %s's turn" % current_game.turn.user_name, 'warning')

    # the position on the board is already taken
    if Piece.query.filter_by(game=current_game, position_x=x, position_y=y).first():
        return response_data("Position %d %d is already taken" % (x, y), 'warning')

    # add the game piece
    piece = Piece(current_game, player, x, y)
    db.session.add(piece)

    # change the turn of the game
    other = current_game.player2 if player is current_game.player1 else current_game.player1
    current_game.turn = other
    db.session.commit()

    board = get_board(current_game)

    # check for win
    if is_win():
        db.session.delete(current_game)
        db.session.commit()
        return board_response_data(
            "*%s is the winner!*" % player.user_name, board, current_game, True)
    return board_response_data(
        "%s played piece %d %d" % (player.user_name, x, y), board, current_game)

@app.route('/hello')
def hello_world():
    return jsonify('Hello, World!')
