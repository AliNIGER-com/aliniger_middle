from app import create_app, db
from app.models import *  # importe tous les modèles

app = create_app()

with app.app_context():
    db.drop_all()   # supprime tables si besoin
    db.create_all() # crée les tables

    print("Tables recréées avec succès.")
