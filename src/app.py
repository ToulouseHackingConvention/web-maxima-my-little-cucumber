#!/usr/bin/env python3
from flask import Flask
import settings


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = settings.DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    from models import db
    db.init_app(app)

    from views import views
    app.register_blueprint(views)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000)
