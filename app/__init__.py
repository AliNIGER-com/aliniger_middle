from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_jwt_extended import JWTManager  # ✅ Ajout
from .config import Config
import os

# Initialisation des extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
jwt = JWTManager()  # ✅ Ajout

# Import du modèle ici uniquement pour user_loader
from .models import Vendeur

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ✅ Limite d'upload (50 Mo)
    app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB

    # ✅ Dossiers d'uploads
    app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
    app.config['UPLOAD_ALIBABA'] = os.path.join(app.config['UPLOAD_FOLDER'], 'alibaba')
    app.config['UPLOAD_AFRIQUE'] = os.path.join(app.config['UPLOAD_FOLDER'], 'afrique')
    app.config['UPLOAD_BOUTIQUE'] = os.path.join(app.config['UPLOAD_FOLDER'], 'boutique')

    # ✅ Création automatique des dossiers
    os.makedirs(app.config['UPLOAD_ALIBABA'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_AFRIQUE'], exist_ok=True)
    os.makedirs(app.config['UPLOAD_BOUTIQUE'], exist_ok=True)

    # Initialisation des extensions
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)
    login_manager.init_app(app)
    jwt.init_app(app)  # ✅ Initialisation du JWT

    # Configuration de Flask-Login
    login_manager.login_view = 'web_routes.login_vendeur'

    @login_manager.user_loader
    def load_user(user_id):
        return Vendeur.query.get(int(user_id))

    # Enregistrement des blueprints
    from .routes import register_routes
    register_routes(app)

    return app
