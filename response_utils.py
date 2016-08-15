from flask import jsonify


def response_data(text, color):
    data = {
        'response_type': 'in_channel',
        'attachments': [
            {
                'fallback': 'Status',
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
                'fallback': 'Current tic slack toe board',
                'color': 'good' if win else None,
                'pretext': pretext,
                'title': 'Current tic slack toe board',
                'text': "```%s```" % board,
                'mrkdwn_in': ['pretext', 'text']
            }
        ]
    }

    # don't show extra game information on win or draw
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
                'fallback': 'Help',
                'title': 'Help is on the way!',
                'text': (
                    "To connect your user name, `/ticslacktoe connect`\n"
                    "To show current board, `/ticslacktoe show`\n"
                    "To start a game with another user, `/ticslacktoe start [username]`\n"
                    "To play a move on your turn, `/ticslacktoe play [x] [y]`, where x and y are "
                    "coordinates 0-2 on the board:\n"
                    "```|0 2|1 2|2 2|\n|0 1|1 1|2 1|\n|0 0|1 0|2 0|```"
                ),
                'mrkdwn_in': ['text']
            }
        ]
    }
    return jsonify(data)
