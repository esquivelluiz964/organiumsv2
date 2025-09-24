from flask import Flask, render_template, request
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user


db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'app_bp.login'

class Config:
    # Default to sqlite for quick start; override via env var FLASK_DATABASE_URI
    SQLALCHEMY_DATABASE_URI = "sqlite:///mvp.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = "dev-secret-key"  # override in production via env var

def register_error_handlers(app):
    from models import Log

    def register_log(action, status="ok"):
        user_id = current_user.id if current_user.is_authenticated else None
        ip_address = request.remote_addr
        log = Log(
            user_id=user_id,
            action=action,
            ip_address=ip_address,
            status=status
        )
        db.session.add(log)
        db.session.commit()
    @app.errorhandler(403)
    def forbidden(e):
        register_log(f"Ocorreu um erro 403, {str(e)}", "fail")
        return render_template("error/erro.html", code_error='403', detalhe_error=str(e)), 403

    @app.errorhandler(404)
    def page_not_found(e):
        register_log(f"Ocorreu um erro 404, {str(e)}", "fail")
        return render_template("error/erro.html", code_error='404', detalhe_error=str(e)), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        register_log(f"Ocorreu um erro 500, {str(e)}", "fail")
        return render_template("error/erro.html", code_error='500', detalhe_error=str(e)), 500

def create_app(config_object=None):
    app = Flask(__name__, template_folder='app/templates', static_folder='app/static')
    app.config.from_object(config_object or Config)

    # init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)

    # import aqui para evitar circular import
    from models import User

    # 🔑 registrar user_loader
    @login.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # register blueprints
    from app.views import bp as app_bp
    from api.views import bp as api_bp
    app.register_blueprint(app_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    # configurações adicionais
    app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024
    register_error_handlers(app)

    # shell context
    @app.shell_context_processor
    def make_shell_context():
        return {'db': db, 'User': User}

    return app
