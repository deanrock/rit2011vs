from app import db

ROLE_USER = 0
ROLE_ADMIN = 1

user_vaje = db.Table('user_vaje',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('vaje_id', db.Integer, db.ForeignKey('vaje.id'), primary_key=True)
)

class User(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    nickname = db.Column(db.String(64), unique = True)
    email = db.Column(db.String(120), unique = True)
    role = db.Column(db.SmallInteger, default = ROLE_USER)
    projekt = db.Column(db.String(50))

    vaje = db.relationship('Vaje', secondary=user_vaje,
                            backref=db.backref('users', 
                                               lazy='dynamic'),
                            lazy='dynamic')

    def posodobi_termin_vaje(self, predmet, termin=None):
        vaje = self.vaje.filter(Vaje.predmet==predmet).all()

        for v in vaje:
            self.vaje.remove(v)
            db.session.commit()

        if termin:
            v = Vaje.query.filter_by(id=termin).first()
            if v:
                self.vaje.append(v)
                db.session.commit()
       

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


