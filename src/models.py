from flask_sqlalchemy import SQLAlchemy
import base64
import hashlib
import os
import settings

db = SQLAlchemy()

with open(settings.PRIVATE_KEY_FILE, 'rb') as f:
    private_key = f.read(16)


class Pony(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    url = db.Column(db.String(255))
    description = db.Column(db.Text)

    def __init__(self, name, url, description):
        self.name = name
        self.url = url
        self.description = description


def password_hash(password, salt):
    return hashlib.sha224(salt + password.encode('utf8') + private_key).hexdigest()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    salt = db.Column(db.String(255))
    password = db.Column(db.String(56))
    vote_pony_id = db.Column(db.Integer, db.ForeignKey('pony.id'), nullable=True)

    def __init__(self, username, password):
        self.username = username
        salt = os.urandom(16)
        self.salt = base64.encodebytes(salt).decode('utf8').strip()
        self.password = password_hash(password, salt)
        self.vote_pony_id = None

    def check_password(self, password):
        salt = base64.decodebytes(self.salt.encode('utf8'))
        return self.password == password_hash(password, salt)
