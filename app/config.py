import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqlconnector://ibrahim:ibbigboSS227@@localhost:3306/flaskdb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sécurité
    SECRET_KEY = os.environ.get('SECRET_KEY', 'valeur_par_defaut')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'valeur_par_defaut_jwt')

    # Configuration du JWT
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
