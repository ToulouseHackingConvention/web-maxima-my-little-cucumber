#!/usr/bin/env python3
from flask import Flask
import settings


def create_app(name):
    app = Flask(name)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['PROPAGATE_EXCEPTIONS'] = True

    from models import db
    db.init_app(app)

    from views import views
    app.register_blueprint(views)

    return app


if __name__ == '__main__':
    app = create_app('my-little-cucumber-dev')
    app.run(host='0.0.0.0', port=5000)
