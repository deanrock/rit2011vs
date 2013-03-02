from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    projekt = db.Column(db.String(50))

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return unicode(self.id)

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Vaje(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    naziv = db.Column(db.String(255))
    predmet = db.Column(db.String(255))
    prostor = db.Column(db.String(255))
    dan = db.Column(db.Integer)
    termin = db.Column(db.String(255))
    asistent = db.Column(db.String(255))

    def __repr__(self):
        return '<Vaje %r>' % (self.naziv)