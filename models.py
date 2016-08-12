from ticslacktoe import db


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    channel_id = db.Column(db.String, unique=True)
    team_id = db.Column(db.String, unique=True)

    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'))

    player1 = db.relationship('Player', foreign_keys=[player1_id])
    player2 = db.relationship('Player', foreign_keys=[player2_id])

    player1_marker = db.Column(db.String(1))
    player2_marker = db.Column(db.String(1))

    turn = db.Column(db.Integer)  # 1 or 2 for player. TODO: change to Enum

    def __init__(self, player1, player2):
        self.player1 = player1
        self.player2 = player2

    def __repr__(self):
        return '<Game %r %r>' % self.player1.user_name, self.player2.user_name


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, unique=True)
    user_name = db.Column(db.String)

    def __init__(self, user_id, user_name):
        self.user_id = user_id
        self.user_name = user_name

    def __repr__(self):
        return '<Player %r>' % self.user_name


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
