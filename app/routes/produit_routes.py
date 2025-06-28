from flask import Blueprint, jsonify, url_for, current_app
import os
from ..models import ProduitAfrique, ProduitAlibaba

produit_routes = Blueprint('produit_routes', __name__)

@produit_routes.route('/api/produits_afrique', methods=['GET'])
def get_produits_afrique():
    produits = ProduitAfrique.query.all()
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix": p.prix,
        "image": f"http://192.168.149.118:5000/static/assets/produits_afrique/{p.image}",
        "categorie": p.categorie,
        "vendeur_id": p.vendeur_id,
        "vendeur": p.vendeur if p.vendeur else None,
        "stock": p.stock
    } for p in produits])

@produit_routes.route('/api/produits_alibaba', methods=['GET'])
def get_produits_alibaba():
    produits = ProduitAlibaba.query.all()
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix_estime": p.prix_estime,
        "image": f"http://192.168.149.118:5000/static/images/{p.image}",
        "min_commande": p.min_commande,
        "frais_livraison_estime": p.frais_livraison_estime,
        "vendeur": p.vendeur,
        "note": p.note,
        "couleur": p.couleur
    } for p in produits])

@produit_routes.route('/api/categories', methods=['GET'])
def get_categories():
    categories = [
        "Électronique",
        "Beauté",
        "Industrie",
        "Santé",
        "Maison",
        "Vêtements",
        "Sport",
        "Automobile",
        "Jouets",
        "Bricolage",
        "Mobilier",
        "Bijoux",
        "Papeterie",
        "Informatique",
        "Chaussures",
        "Alimentation",
        "Accessoires",
        "Montres",
        "Téléphones",
        "Éclairage",
    ]
    return jsonify(categories)
