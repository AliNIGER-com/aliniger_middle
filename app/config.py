# app/config.py
import os

class Config:
    SQLALCHEMY_DATABASE_URI = (
        'mysql+mysqlconnector://root:TkAdlBaXUclWYbIPUhTprVWwXBwQFqIa'
        '@crossover.proxy.rlwy.net:43313/railway'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'une_chaine_complexe_et_secrete'
    JWT_TOKEN_LOCATION = ["headers"]
