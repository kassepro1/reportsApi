from flask import Flask
import routes
from models.messages_manager import MessageManager


def create_app():
    app = Flask(__name__)
    app.config.from_envvar('REPORTS_CONFIG')

    app.config["MSG_MANAGER"] = MessageManager()

    routes.init_app(app)
    return app
