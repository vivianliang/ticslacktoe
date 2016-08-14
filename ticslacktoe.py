import os

from flask import Flask, jsonify, url_for, redirect, request
from flask_dance.contrib.slack import make_slack_blueprint, slack
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku
from werkzeug.contrib.fixers import ProxyFix
from slackclient import SlackClient


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = 'sosecretblah'
app.config['SLACK_OAUTH_CLIENT_ID'] = os.environ.get("SLACK_OAUTH_CLIENT_ID")
app.config['SLACK_OAUTH_CLIENT_SECRET'] = os.environ.get("SLACK_OAUTH_CLIENT_SECRET")

slack_bp = make_slack_blueprint(scope=["identify,chat:write:bot"])
app.register_blueprint(slack_bp, url_prefix='/login')
slack_client = SlackClient('xoxp-67708760471-68778205813-69333865026-a746f316f2')

heroku = Heroku(app)
db = SQLAlchemy(app)

from models import Game, Piece, Player
from response_utils import response_data, board_response_data, help_response_data

MAX_PIECES = 9
PIECES_PER_ROW = 3


def create_player(team_id, user_name):
    player = Player(team_id=team_id, user_name=user_name)
    db.session.add(player)
    db.session.commit()
    return player

def get_or_create_player(team_id, user_name):
    player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
    if not player:
        player = create_player(team_id, user_name)
    return player

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


@app.route('/slack', methods=['POST'])
def tic_slack_toe():
    token        = request.form.get('token')
    team_id      = request.form.get('team_id')
    channel_id   = request.form.get('channel_id')
    user_id      = request.form.get('user_id')
    user_name    = request.form.get('user_name')
    command      = request.form.get('command')
    text         = request.form.get('text')
    response_url = request.form.get('response_url')

    # TODO: this is hard-coded for now. Test 28032589 is the only team that can access this app.
    #       can be moved to an environment variable on Heroku
    if token != '6quahLsQgU7EJIOoENkl66vp':
        return response_data('Unauthorized request', 'danger')

    # TODO: future improvement - verify user, team, channel via RTM API
    api_call = slack_client.api_call('users.list')
    print api_call
    if api_call.get('ok'):
        users = api_call.get('members')
        print users

    args = text.split()

    current_game = Game.query.filter_by(team_id=team_id, channel_id=channel_id).first()

    if len(args) == 0 or args[0] == 'help':
        return help_response_data()

    if args[0] == 'connect':
        # TODO: future improvement - verify user via RTM API
        player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
        if player is not None:
            msg = 'User %s has already connected to tic-slack-toe'
            return response_data(msg % player.user_name, 'warning')

        player = create_player(team_id=team_id, user_name=user_name)

        return response_data((
            "You (%s) are now connected to tic-slack-toe. There is no need to"
            "reconnect unless your Slack user name changes.") % player.user_name, 'good')

    elif args[0] == 'show':
        return board_response_data('', get_board(current_game), current_game)

    elif args[0] == 'start':

        # ------------#
        #  validation
        # ------------#

        if len(args) < 2:
            msg = 'Invalid arguments. to start: `/ticslacktoe start [username]`'
            return response_data(msg, 'danger')

        requested_player_name = args[1]

        # requested player must have self-connected with the app previously
        player2 = Player.query.filter_by(team_id=team_id, user_name=requested_player_name).first()
        if player2 is None:
            msg = "User %s needs to connect to tic-slack-toe with `/ticslacktoe connect`"
            return response_data(msg % requested_player_name, 'danger')

        if current_game is not None:
            return response_data('A game is already in progress', 'warning')

        # -----------------#
        #  start new game
        # -----------------#

        player1 = get_or_create_player(team_id, user_name)

        game = Game(team_id, channel_id, player1, player2)
        db.session.add(game)
        db.session.commit()

        msg = 'New game started between %s and %s. ' % (player1.user_name, player2.user_name)
        msg += '%s begins' % (player1.user_name)
        return response_data(msg, 'good')

    elif args[0] == 'play':

        # ------------#
        #  validation
        # ------------#

        if len(args) < 3:
            msg = 'Invalid arguments. to play: `/ticslacktoe play [x] [y]`'
            return response_data(msg, 'danger')

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
            current_game.pieces.filter_by(
                position_x=z, position_y=z, player=player).first() for z in xrange(3)])

        if len(north_east_diagonal_pieces) == PIECES_PER_ROW:
            return True

        # check for 3 pieces in the north-west diagonal
        coords = [(0,2), (1,1), (2,0)]
        north_west_diagonal_pieces = filter(None, [
            current_game.pieces.filter_by(
                position_x=i, position_y=j, player=player).first() for i, j in coords])
        return len(north_west_diagonal_pieces) == PIECES_PER_ROW

    # -----------------#
    #  play validation
    # -----------------#

    # game has not been started
    if current_game is None:
        return response_data('Must start game with: `/ticslacktoe start [username]`', 'warning')

    # only the players in the current game can play
    player = Player.query.filter_by(team_id=team_id, user_name=user_name).first()
    player_not_in_game = player is not current_game.player1 and player is not current_game.player2

    if not player or player_not_in_game:
        msg_text = "Only the current players %s and %s can play"
        msg =  msg_text % (current_game.player1.user_name, current_game.player2.user_name)
        return response_data(msg, 'warning')

    # it is not user's turn
    if player is not current_game.turn:
        return response_data("It is %s's turn" % current_game.turn.user_name, 'warning')

    # the position on the board is already taken
    if Piece.query.filter_by(game=current_game, position_x=x, position_y=y).first():
        return response_data("Position %d %d is already taken" % (x, y), 'warning')

    # ------#
    #  play
    # ------#

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
            "*Game over: %s is the winner!*" % player.user_name, board, current_game, True)

    # check for draw
    if current_game.pieces.count() == MAX_PIECES:
        db.session.delete(current_game)
        db.session.commit()
        return board_response_data(
            "*Game over: It's a draw!*", board, current_game, True)

    return board_response_data(
        "%s played piece %d %d" % (player.user_name, x, y), board, current_game)

@app.route('/')
def welcome():
    if not slack.authorized:
        print 'not authorized redirect'
        return redirect(url_for('slack.login'))

    print 'authorized'
    resp = slack.post("chat.postMessage", data={
        "channel": "#random",
        "text": "Hello, world!",
        "icon_emoji": ":robot_face:",
    })
    assert resp.json()["ok"], resp.text

    return jsonify("Welcome to Tic Slack Toe! Use command '/ticslacktoe help'"
        "in a channel on https://ae28032589test0.slack.com/ to begin.")

@app.route('/login/slack/authorized')
def authorized():
    'redirected'
    # if not slack.authorized:
    #     print 'not authorized redirect'
    #     return redirect(url_for('slack.login'))

    print 'authorized'
    resp = slack.post("chat.postMessage", data={
        "channel": "#random",
        "text": "Hello, world!",
        "icon_emoji": ":robot_face:",
    })
    assert resp.json()["ok"], resp.text

    return jsonify("Welcome to Tic Slack Toe! Use command '/ticslacktoe help'"
        "in a channel on https://ae28032589test0.slack.com/ to begin.")
