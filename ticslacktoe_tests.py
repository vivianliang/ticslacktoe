import unittest

from flask_testing import TestCase

# from ticslacktoe import app, db
# import ticslacktoe
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

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def get_payload(self, text):
        return {
            'token'       : 'gIkuvaNzQIHg97ATvDxqgjtO',
            'team_id'     : 'T0001',
            'team_domain' : 'example',
            'channel_id'  : 'C2147483705',
            'channel_name': 'test',
            'user_id'     : 'U2147483697',
            'user_name'   : 'Steve',
            'command'     : '/weather',
            'text'        : text,
            'response_url': 'https://hooks.slack.com/commands/1234/5678'
        }

    def test_hello(self):
        response = self.client.get('/hello')
        self.assertEqual(response.json, 'Hello, World!')

    def test_post(self):
        response = self.client.post('/',
            data=self.get_payload('showboard'),
            content_type='application/x-www-form-urlencoded')
        print response.json
        print response.json.get('attachments')[1]
        # print self.app.post('/', payload)

    def test_create_player(self):
        player = Player(team_id='team1', user_name='user1')
        db.session.add(player)
        db.session.commit()
        print player
        assert player in db.session

if __name__ == '__main__':
    unittest.main()
