from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# Import du modèle ici uniquement pour user_loader
from .models import Vendeur

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Limite d'upload (50 Mo)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    login_manager.init_app(app)

    # Configuration de Flask-Login
    login_manager.login_view = 'web_routes.login_vendeur'

    @login_manager.user_loader
    def load_user(user_id):
        return Vendeur.query.get(int(user_id))

    # Enregistrement des blueprints
    from .routes import register_routes
    register_routes(app)

    return app
