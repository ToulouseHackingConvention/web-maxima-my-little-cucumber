from Crypto.Cipher import AES
from flask import Blueprint, render_template, request, make_response, redirect, abort
from sqlalchemy import func
import codecs
import pickle
import string

from models import db, Pony, User
import settings

views = Blueprint('views', __name__)

with open(settings.PRIVATE_KEY_FILE, 'rb') as f:
    private_key = f.read(16)


def encode_cookie(user_id, username, vote_pony_id):
    buf = pickle.dumps([user_id, username, vote_pony_id]) # pickle
    buf += b'\x00' * ((16 - len(buf) % 16) % 16) # padding
    buf = AES.new(private_key, AES.MODE_ECB).encrypt(buf) # cipher with AES 128
    return codecs.encode(buf, 'hex').decode('ascii')


def decode_cookie(buf):
    if not all(c in string.hexdigits for c in buf):
        return False

    buf = codecs.decode(buf, 'hex')

    if len(buf) % 16 != 0:
        return False

    buf = AES.new(private_key, AES.MODE_ECB).decrypt(buf)

    try:
        return pickle.loads(buf) # xD lol, my code is very secure!
    except:
        return False


def attach_session_cookie(response, user):
    response.set_cookie('session', encode_cookie(user.id, user.username, user.vote_pony_id))


class AnonymousUser:
    def __init__(self):
        pass

    def is_authenticated(self):
        return False


class AuthenticatedUser:
    def __init__(self, id, username, vote_pony_id):
        self.id = id
        self.username = username
        self.vote_pony_id = vote_pony_id

    def is_authenticated(self):
        return True


@views.before_request
def start_session():
    request.user = AnonymousUser()

    if 'session' in request.cookies:
        session = decode_cookie(request.cookies['session'])
        if session and isinstance(session, list) and len(session) == 3:
            request.user = AuthenticatedUser(*session)


@views.route('/')
def index():
    return render_template('index.html')


@views.route('/ponies')
def ponies():
    subquery = db.session.query(User.vote_pony_id.label('pony_id'), func.count(User.id).label('votes')).group_by(User.vote_pony_id).subquery()
    query = db.session.query(Pony.id, Pony.name, Pony.url, subquery.c.votes.label('votes'))
    query = query.outerjoin(subquery, Pony.id == subquery.c.pony_id)
    query = query.order_by(subquery.c.votes.desc())
    return render_template('ponies.html', ponies=query.all())


@views.route('/vote/<int:pony_id>')
def vote(pony_id):
    if not request.user.is_authenticated():
        abort(401)

    user = User.query.get(request.user.id)

    if not user: # invalid session
        return logout()

    pony = Pony.query.get_or_404(pony_id)
    user.vote_pony_id = pony.id
    db.session.add(user)
    db.session.commit()

    response = make_response(redirect('/ponies'))
    attach_session_cookie(response, user)
    return response


@views.route('/unvote')
def unvote():
    if not request.user.is_authenticated():
        abort(401)

    user = User.query.get(request.user.id)

    if not user: # invalid session
        return logout()

    user.vote_pony_id = None
    db.session.add(user)
    db.session.commit()

    response = make_response(redirect('/ponies'))
    attach_session_cookie(response, user)
    return response


# This is a troll (totally safe)
@views.route('/description.php')
def description():
    if 'inc' in request.args and request.args['inc'].isdigit():
        pony_id = int(request.args['inc'])
        pony = Pony.query.filter_by(id=pony_id).first()
        if pony:
            return pony.description

    return ''


@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.user.is_authenticated():
        return render_template('please-logout.html')

    if request.method == 'POST':
        if 'username' in request.form and request.form['username'] \
                and 'password' in request.form and request.form['password']:
            username = request.form['username']
            password = request.form['password']

            user = User.query.filter_by(username=username).first()
            if user and user.check_password(password):
                response = make_response(redirect('/'))
                attach_session_cookie(response, user)
                return response
            else:
                return render_template('login.html', error="Bad login/password")
        else:
            return render_template('login.html', error="Missing field")
    else:
        return render_template('login.html')


@views.route('/logout')
def logout():
    response = make_response(redirect('/'))
    response.set_cookie('session', '', expires=0)
    return response


@views.route('/register', methods=['GET', 'POST'])
def register():
    if request.user.is_authenticated():
        return render_template('please-logout.html')

    if request.method == 'POST':
        if 'username' in request.form and request.form['username'] \
                and 'password' in request.form and request.form['password'] \
                and 'password-confirm' in request.form and request.form['password-confirm']:
            username = request.form['username']
            password = request.form['password']
            password_confirm = request.form['password-confirm']

            if len(username) > 255:
                return render_template('register.html', error="Username too long (max 255 characters)")
            elif len(password) < 8:
                return render_template('register.html', error="Password too short (min 8 characters)")
            elif password != password_confirm:
                return render_template('register.html', error="Passwords don't match")
            elif User.query.filter_by(username=username).count() > 0:
                return render_template('register.html', error="Username already taken")
            else:
                # register user
                user = User(username, password)
                db.session.add(user)
                db.session.commit()

                response = make_response(render_template('register-success.html', username=username))
                response.set_cookie('session', encode_cookie(user.id, username, None))
                return response
        else:
            return render_template('register.html', error="Missing field")
    else:
        return render_template('register.html')
