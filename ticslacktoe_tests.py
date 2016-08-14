import unittest

from flask_testing import TestCase

from ticslacktoe import app as ticslacktoeapp, db
from models import Game, Player, Piece


class TicSlackToeTestCase(TestCase):

    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    TESTING = True

    def create_app(self):
        app = ticslacktoeapp
        app.config['TESTING'] = True
        return app

    def setUp(self):
        db.session.close()
        db.drop_all()
        db.create_all()

        self.post_form(None, self.get_payload('connect', 'Rosa'))

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    # -------------------- #
    #        utils
    # -------------------- #

    def get_payload(self, text, user_name='Steve'):
        return {
            'token'       : '6quahLsQgU7EJIOoENkl66vp',
            'team_id'     : 'T0001',
            'team_domain' : 'example',
            'channel_id'  : 'C2147483705',
            'channel_name': 'test',
            'user_id'     : 'U2147483697',
            'user_name'   : user_name,
            'command'     : '/weather',
            'text'        : text,
            'response_url': 'https://hooks.slack.com/commands/1234/5678'
        }

    def post_form(self, space_separated_args, payload=None):
        response = self.client.post('/',
            data = payload or self.get_payload(space_separated_args),
            content_type = 'application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, 200)
        return response

    # -------------------- #
    #        tests
    # -------------------- #

    def test_hello(self):
        response = self.client.get('/hello')
        self.assertEqual(response.json, 'Hello, World!')

    def test_models(self):
        player1 = Player(team_id='team1', user_name='player1')
        db.session.add(player1)
        db.session.commit()
        assert player1 in db.session

        player2 = Player(team_id='team1', user_name='player2')
        db.session.add(player2)
        db.session.commit()
        assert player2 in db.session

        game = Game('team1', 'channel1', player1, player2)
        db.session.add(game)
        db.session.commit()
        assert game in db.session
        self.assertEqual(game.turn, player1)

    def test_default_response(self):
        response = self.post_form('')
        text = response.json.get('attachments')[0].get('text')
        self.assertIn('/ticslacktoe', text)
        self.assertIn('where x and y are coordinates', text)

        response = self.post_form('invalid')
        text = response.json.get('attachments')[0].get('text')
        self.assertIn('/ticslacktoe', text)
        self.assertIn('where x and y are coordinates', text)

    def test_show_board(self):
        response = self.post_form('show')
        text = response.json.get('attachments')[0].get('text')
        pieces = [' ' for x in xrange(9)]
        expected_board = "```|%s|%s|%s|\n|%s|%s|%s|\n|%s|%s|%s|```" % tuple(pieces)
        self.assertEqual(text, expected_board)

    # -------------------- #
    #    start tests
    # -------------------- #

    def test_start_game_bad_params(self):
        response = self.post_form('start')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Invalid arguments. to start: `/ticslacktoe start [username]`')

    def test_start_game_user_validation(self):
        # TODO
        pass

    def test_start_game_already_in_progress(self):
        self.post_form('start Rosa')
        self.post_form(None, self.get_payload('connect', 'Bob'))
        response = self.post_form('start Bob')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'A game is already in progress')

    def test_get_or_create_players(self):
        pass

    def test_create_game_and_players(self):
        response = self.post_form('start Rosa')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'New game started between Steve and Rosa')

        self.assertEqual(Game.query.count(), 1)

        players = Player.query.order_by(Player.id).all()
        self.assertEqual(len(players), 2)
        self.assertEqual(players[0].user_name, 'Rosa')
        self.assertEqual(players[1].user_name, 'Steve')
        self.assertEqual(Game.query.first().turn, players[1])

    # -------------------- #
    #    play tests
    # -------------------- #

    def test_play_game_bad_params(self):
        response = self.post_form('play 0')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Invalid arguments. to play: `/ticslacktoe play [x] [y]`')

        response = self.post_form('play abc def')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Positions x and y must be integers between 0 and 2')

        response = self.post_form('play -1 0')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Positions x and y must be integers between 0 and 2')

    def test_play_game_no_game_in_progress(self):
        response = self.post_form('play 0 1')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Must start game with: `/ticslacktoe start [username]`')

    def test_play_game_non_player(self):
        # game started between Steve and Rosa
        self.post_form('start Rosa')

        # play attempted by Bob
        response = self.post_form(None, self.get_payload('play 0 1', 'Bob'))
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Only the current players Steve and Rosa can play')

    def test_play_game_other_players_turn(self):
        # game started between Steve and Rosa. it is Steve's turn to start
        self.post_form('start Rosa')

        # play attempted by Rosa
        response = self.post_form(None, self.get_payload('play 0 1', 'Rosa'))
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, "It is Steve's turn")

    def test_play(self):
        self.post_form('start Rosa')

        # Steve plays 0 2
        self.post_form('play 0 2')
        self.assertEqual(Piece.query.count(), 1)
        game = Game.query.first()

        # Rosa attempts to plays 0 2 again
        response = self.post_form(None, self.get_payload('play 0 2', 'Rosa'))
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, 'Position 0 2 is already taken')
        self.assertEqual(Piece.query.count(), 1)

        # Rosa plays 2 0
        response = self.post_form(None, self.get_payload('play 2 0', 'Rosa'))
        self.assertEqual(Piece.query.count(), 2)

        # Steve plays 1 0
        response = self.post_form('play 1 0')
        self.assertEqual(Piece.query.count(), 3)
        text = response.json.get('attachments')[0].get('pre-text')
        self.assertEqual(text, 'Steve played piece 1 0')

        # Rosa plays 1 1 to win
        response = self.post_form(None, self.get_payload('play 1 1', 'Rosa'))
        self.assertEqual(Piece.query.count(), 4)
        text = response.json.get('attachments')[0].get('pre-text')
        self.assertEqual(text, 'Rosa is the winner')
        text = response.json.get('attachments')[0].get('text')
        self.assertEqual(text, "```|X| | |\n| |O| |\n| |X|O|```")
        # self.assertEqual(text, 'Rosa is the winner')

        # response = self.post_form('show')
        # self.assertEqual(Piece.query.count(), 4)
        # text = response.json.get('attachments')[0].get('text')
        # self.assertEqual(text, "```|X| | |\n| |O| |\n| |X|O|```")

if __name__ == '__main__':
    unittest.main()
