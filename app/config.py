# app/config.py
import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev_key")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
