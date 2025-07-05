import json
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text

# ----- CONFIGURATION -----
DATABASE_URL = "mysql+mysqlconnector://root:TkAdlBaXUclWYbIPUhTprVWwXBwQFqIa@crossover.proxy.rlwy.net:43313/railway"
JSON_FILE = "shein_data.json"
CATEGORIE = "Vêtements"  # 💡 À modifier selon la catégorie concernée

# ----- SQLALCHEMY SETUP -----
Base = declarative_base()

class ProduitAlibaba(Base):
    __tablename__ = 'produits_alibaba'
    id = Column(Integer, primary_key=True)
    nom = Column(String(255))
    description = Column(Text)
    prix_estime = Column(Float)
    image = Column(Text)
    min_commande = Column(Integer)
    frais_livraison_estime = Column(Float)
    categorie = Column(String(100))
    vendeur = Column(String(100))
    note = Column(Float)
    couleur = Column(String(50))

# ----- CONNEXION -----
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
session = Session()

# ----- LECTURE JSON -----
with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# ----- PARSING & INSERTION -----
for item in data:
    try:
        produit = ProduitAlibaba(
            nom=item.get("name", "Produit Shein"),
            description=item.get("description", ""),
            prix_estime=float(item.get("price", 0.0)),
            image=item.get("img", ""),
            min_commande=1,  # Valeur fixe par défaut
            frais_livraison_estime=float(item.get("shipping", 0.0)) if item.get("shipping") else 0.0,
            categorie=CATEGORIE,
            vendeur=item.get("brand", "SHEIN"),
            note=float(item.get("rating", 4.0)) if item.get("rating") else 4.0,
            couleur=item.get("color", "")
        )
        session.add(produit)
    except Exception as e:
        print(f"❌ Erreur sur produit : {e}")

# ----- COMMIT FINAL -----
try:
    session.commit()
    print("✅ Insertion terminée avec succès !")
except Exception as e:
    session.rollback()
    print(f"❌ Erreur lors du commit : {e}")

session.close()
