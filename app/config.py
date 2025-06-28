# app/config.py

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:@localhost/aliniger_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'une_chaine_complexe_et_secrete'
