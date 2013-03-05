from flask import render_template, flash, redirect, session, url_for, request, g, jsonify
from flask.ext.login import login_user, logout_user, current_user, login_required
from app import app, db, lm, oid
from forms import LoginForm
from models import User, ROLE_USER, ROLE_ADMIN, Vaje, user_vaje
from app.phpbb_login import PHPBB_Login
import datetime
from flaskext.babel import Babel, format_datetime, format_date 
from time import mktime
from functools import wraps
from app.timetable_parser import timetable_parser
import json
import os.path, time

def jinja_datetime(value, format='medium'):
    if format == 'full':
        format="EEEE, d. MMMM y 'at' HH:mm"
    elif format == 'medium':
        format="dd.MM.y HH:mm"
    return format_datetime(value+datetime.timedelta(days=1), format)

def jinja_date(value, format='medium'):
    if not value:
        return ""
    value=value

    date = value
    
    today = datetime.datetime.now()
    
    tomorrow = (today+datetime.timedelta(days=1)).date()
    yesterday = (today-datetime.timedelta(days=1)).date()
    
    if format == 'full':
        format="EEEE, d. MMMM y"
    elif format == 'medium':
        format="dd.MM.y"
    
    
    return format_date(value, format).lower()

def jinja_day(value):
    value=str(value)

    if value == '1':
        return 'Pon'
    if value == '2':
        return 'Tor'
    if value == '3':
        return 'Sre'
    if value == '4':
        return u'Čet'
    if value == '5':
        return 'Pet'

def jinja_datediff(value):
    return jinja_date(value, 'diff')

app.jinja_env.filters['datetime'] = jinja_datetime
app.jinja_env.filters['date'] = jinja_date
app.jinja_env.filters['datediff'] = jinja_datediff
app.jinja_env.filters['day'] = jinja_day

@app.route('/')
@app.route('/index')
def index():

    return redirect(url_for('urnik'))
    

@lm.user_loader
def load_user(id):
    return User.query.get(int(id))

@app.route('/login_oid')
@oid.loginhandler
def login_oid():
    if g.user is not None and g.user.is_authenticated():
        return redirect(url_for('index'))

    return oid.try_login('https://www.google.com/accounts/o8/id', ask_for = ['nickname', 'email'])

@oid.after_login
def after_login(resp):
    if 'projekt' in session:
        session.pop('projekt', None)

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
    return redirect(url_for('index'))

@app.before_request
def before_request():
    g.user = current_user

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

def get_project():
    if g.user.is_authenticated():
        return g.user.projekt

    if 'projekt' in session:
        return session['projekt']

    return None

def get_schedule(day, project):
    project_ids={'pametni-telefon': 90,
                 'feri-navigator': 89 }
    date = '.'.join(map(str, map(int, day.strftime("%d-%m-%Y").split("-"))))
    
    path = 'tmp/timetables/'+str(project)+'-'+date

    data = {}

    if os.path.isfile(path) and datetime.datetime.fromtimestamp(os.path.getmtime(path)) + datetime.timedelta(hours=1) > datetime.datetime.now():
        with open(path, 'r') as c:
            data = json.loads(c.read())
    else:
        timetable = timetable_parser.generateTimetable('json',
                            date,
                            '12',
                            '2',
                            project_ids[project])
        
        with open(path, 'w') as c:
            c.write(json.dumps(timetable))


        with open(path, 'r') as c:
            data = json.loads(c.read())
    
    return data

def time_to_i(t):
    start = 7*60
    s = t.split(':')
    t2 = int(s[0])*60 + int(s[1])
    return (t2-start)/30

def i_to_time(i):
    start = 7*60

    time = start + i*30

    hour = time/60
    minutes = time-hour*60

    t = ""
    if len(str(hour)) == 1:
        t+="0"

    t+=str(hour) + ":"
        
    if len(str(minutes)) == 1:
        t+="0"

    t+=str(minutes)

    return t

@app.route('/json/urnik', methods=['GET','POST'])
def json_urnik():
    #settings
    selected = g.user.vaje.all() if g.user.is_authenticated() else None

    #calendar
    date = datetime.date.today()

    if 'date' in request.args:
        try:
            date = datetime.datetime.strptime(request.args['date'], '%d-%m-%Y').date()
        except:
            return redirect(url_for('json_urnik'))

    monday = date-datetime.timedelta(days=date.weekday())

    timetable = get_schedule(date, get_project())

    hour_data = []
    reservations = []

    for event in timetable:
        if 'start' in event:
            hour_data.append(event)
        else:
            found=False

            if selected:
                for s in selected:
                    if event['lecture'].lower() == s.predmet.lower():
                        e=event
                        t = s.termin.split('-')
                        e['start'] = t[0]
                        e['end'] = t[1]
                        e['day'] = s.dan

                        hour_data.append(e)

                        found = True
                        break
            if not found:
                reservations.append(event)

    return jsonify({'schedule': hour_data,'reservations': reservations, 'monday':str(monday)})


@app.route('/urnik/<day>', methods=['GET', 'POST'])
@app.route('/urnik', methods=['GET', 'POST'])
def urnik(day=None):
    if g.user and g.user.is_authenticated() and g.user.projekt is None:
        return redirect(url_for('izberi_projekt'))

    if not g.user.is_authenticated() and not 'projekt' in session:
        return redirect(url_for('izberi_projekt'))

    #change settings
    if g.user.is_authenticated():
        if 'vaje_clear' in request.form and 'predmet' in request.form:
            g.user.posodobi_termin_vaje(request.form['predmet'], None)
        elif 'vaje_termin' in request.form  and 'predmet' in request.form:
            g.user.posodobi_termin_vaje(request.form['predmet'], request.form['vaje_termin'])

    #settings
    izbirne_vaje = {}

    selected = g.user.vaje.all()
    vaje = Vaje.query.all()

    for termin in vaje:
        if not termin.predmet in izbirne_vaje:
            izbirne_vaje[termin.predmet]={ 'termini': [],
                                           'predmet': termin.predmet }

        t = termin

        if t in selected:
            t.selected = True

        izbirne_vaje[termin.predmet]['termini'].append(t)

    #calendar
    date = datetime.date.today()

    if day:
        try:
            date = datetime.datetime.strptime(day, '%d-%m-%Y').date()
        except:
            return redirect(url_for('urnik'))

    monday = date-datetime.timedelta(days=date.weekday())
    saturday = monday + datetime.timedelta(days=5)
    prev_week = format_date(monday - datetime.timedelta(days=7), "dd-MM-y")
    next_week = format_date(monday + datetime.timedelta(days=7), "dd-MM-y")

    return render_template('urnik.html',
        title = 'Urnik',
        date = date,
        izbirne_vaje=izbirne_vaje,

        monday=monday,
        saturday = saturday,
        prev_week = prev_week,
        next_week = next_week)

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
            if 'remember-me' in request.form:
                session['remember_me'] = True

            after_login(login_info(nick, email))

    return render_template('login.html')

@app.route('/my-profile')
@login_required
def profile():
    return render_template('profile.html')

@app.route('/izberi-projekt', methods=['GET', 'POST'])
def izberi_projekt():
    if 'projekt' in request.form:
        if request.form['projekt'] == 'feri-navigator' or request.form['projekt'] == 'pametni-telefon':

            if g.user.is_authenticated():
                g.user.projekt = request.form['projekt']
                db.session.commit()
            else:
                session['projekt'] = request.form['projekt']
        return redirect(url_for('index'))

    return render_template('izberi-projekt.html')
