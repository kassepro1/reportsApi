from .home import home_bp
from .report import report_bp
from .form import form_bp


def init_app(app):
    app.register_blueprint(home_bp)
    app.register_blueprint(report_bp)
    app.register_blueprint(form_bp)

