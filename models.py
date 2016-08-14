from ticslacktoe import db


class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    team_id = db.Column(db.String)
    channel_id = db.Column(db.String)

    player1_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    player2_id = db.Column(db.Integer, db.ForeignKey('player.id'))

    player1 = db.relationship('Player', foreign_keys=[player1_id])
    player2 = db.relationship('Player', foreign_keys=[player2_id])

    pieces = db.relationship('Piece', backref='game', lazy='dynamic')

    turn_id = db.Column(db.Integer, db.ForeignKey('player.id'))
    turn = db.relationship('Player', foreign_keys=[turn_id])

    def __init__(self, team_id, channel_id, player1, player2):
        self.team_id = team_id
        self.channel_id = channel_id
        self.player1 = player1
        self.player2 = player2
        self.turn = player1

    def __repr__(self):
        return '<Game %r %r>' % (self.player1.user_name, self.player2.user_name)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.String)
    user_name = db.Column(db.String)

    def __init__(self, team_id, user_name):
        self.team_id = team_id
        self.user_name = user_name

    def __repr__(self):
        return '<Player %r>' % self.user_name


class Piece(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    game_id = db.Column(db.Integer, db.ForeignKey('game.id'))

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
        return '<Piece %r %r>' % (self.position_x, self.position_y)
