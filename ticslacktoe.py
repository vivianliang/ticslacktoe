from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_heroku import Heroku


app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://localhost/ticslacktoe'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
heroku = Heroku(app)
db = SQLAlchemy(app)

from models import Game, Piece, Player

MAX_PIECES = 9


def response_data(user_id, user_name, text):
    data = {
        'response_type': 'in_channel',
        'text': 'Current tic tac toe board',
        'attachments': [
            {
                'pretext': user_id
            },
            {
                'text': '%s %s' % (user_name, text)
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
def show_board():
    token        = request.form.get('token')
    team_id      = request.form.get('team_id')
    channel_id   = request.form.get('channel_id')
    user_id      = request.form.get('user_id')
    user_name    = request.form.get('user_name')
    command      = request.form.get('command')
    text         = request.form.get('text')
    response_url = request.form.get('response_url')

    # TODO: validate data and raise

    print token
    print team_id
    print user_id, user_name
    print command
    print text
    print response_url

    args = text.split()

    if args[0] == 'showboard':
        # show board for current channel
        return response_data(user_id, user_name, 'show board')

    elif args[0] == 'startgame':
        if len(args) > 1:
            requested_player_name = args[1]
        else:
            abort(400)  # TODO: include 'no user name provided' error message

        # TODO: verify that specified user is in the channel (RTM API)

        # check if there is a game in progress
        last_game = (Game.query.filter_by(team_id=team_id, channel_id=channel_id)
            .order_by(Game.id.desc())
            .first())

        if last_game is not None:
            is_done = last_game.pieces.count() == MAX_PIECES
            if not is_done:
                return response_data(user_id, user_name, 'game is in progress')

        player1 = get_or_create_player(team_id, user_name)
        player2 = get_or_create_player(team_id, requested_player_name)

        game = Game(team_id, channel_id, player1, player2)
        db.session.add(game)
        db.session.commit()

        print game.turn







        # request_user = Player.query.filter_by(user_id=user_id).first()
        # if request_user is None:
        #     player = Player()
        # game = Game.query.filter_by(team_id=team_id, channel_id=channel_id).first()
        # if game is None:
        #     # create new game for this channel
        #     game = Game() # todo
        #     db.session.add(game)
        #     db.session.commit()
        # else:
            # start new game and update players
        return response_data(user_id, user_name, 'creating new game')

    return response_data(user_id, user_name, 'the end')


@app.route('/hello')
def hello_world():
    return 'Hello, World!'
