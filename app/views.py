from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from models import User, ROLE_USER, ROLE_ADMIN
from app.phpbb_login import PHPBB_Login

@app.route('/')
@app.route('/index')
def index():

    return redirect(url_for('urnik'))
    

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login_oid', methods = ['GET', 'POST'])
@oid.loginhandler
def login_oid():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    return oid.try_login('https://www.google.com/accounts/o8/id', ask_for = ['nickname', 'email'])

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Napačna prijava. Prosim poizkusi ponovno.')
        redirect(url_for('login'))
    user = User.query.filter_by(email = resp.email).first()
    if user is None:
        nickname = resp.nickname
        if nickname is None or nickname == "":
            nickname = resp.email.split('@')[0]
        user = User(nickname = nickname, email = resp.email, role = ROLE_USER)
        db.session.add(user)
        db.session.commit()
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    login_user(user, remember = remember_me)
    flash(u'Uspešno si se prijavil.', 'warning')
    return redirect(request.args.get('next') or url_for('index'))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/urnik')
def urnik():
    return render_template('urnik.html',
        title = 'Urnik')

class login_info:
    def __init__(self, nick, email):
        self.nickname=nick
        self.email=email

@app.route('/login', methods=['GET', 'POST'])
def login():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    if 'username' in request.form and 'password' in request.form:
        login = PHPBB_Login('http://rit2011vs.mojforum.si')

        nick, email = login.check_login(request.form['username'], request.form['password'])

        if nick == None:
            flash(u'Napačno uporabniško ime in/ali geslo.', 'error')
        else:
            after_login(login_info(nick, email))

    return render_template('login.html')

@app.route('/my-profile')
@login_required
def profile():
    return render_template('profile.html')
