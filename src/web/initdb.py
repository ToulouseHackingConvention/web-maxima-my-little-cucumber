#!/usr/bin/env python3
from app import create_app
import json

if __name__ == '__main__':
    app = create_app('my-little-cucumber')

    with app.app_context():
        from models import db, Pony

        db.create_all()

        with open('ponies.json') as f:
            for pony in json.load(f):
                db.session.add(Pony(pony['name'], pony['url'], pony['desc']))

        db.session.commit()
