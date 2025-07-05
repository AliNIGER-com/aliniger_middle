from flask import Blueprint, jsonify, url_for, current_app, request
import os
from ..models import ProduitAfrique, ProduitAlibaba
from sqlalchemy import or_, func
produit_routes = Blueprint('produit_routes', __name__)

@produit_routes.route('/api/produits_afrique', methods=['GET'])
def get_produits_afrique():
    produits = ProduitAfrique.query.all()
    
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix": p.prix,
        "image": f"https://alinigermiddle-production.up.railway.app/media/{p.image}",
        "categorie": p.categorie,
        "vendeur_id": p.vendeur_id,
        "vendeur": p.vendeur.to_dict() if p.vendeur else None,
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
        "image": f"https://alinigermiddle-production.up.railway.app/media/{p.image}",
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

@produit_routes.route('/produits_afrique_similaires', methods=['POST'])
def produits_afrique_similaires():
    data = request.json
    nom = data.get('nom', '').strip()
    categorie = data.get('categorie', '').strip()

    if not nom or not categorie:
        return jsonify({"error": "Nom et catégorie sont requis."}), 400

    produits_similaires = ProduitAfrique.query.filter(
        func.lower(ProduitAfrique.categorie) == categorie.lower(),
        or_(
            func.lower(ProduitAfrique.nom).like(f"%{nom.lower()}%"),
            func.lower(ProduitAfrique.description).like(f"%{nom.lower()}%")
        )
    ).all()

    resultats = []
    for p in produits_similaires:
        resultats.append({
            "id": p.id,
            "nom": p.nom,
            "categorie": p.categorie,
            "prix": p.prix,
            "origine": p.pays_origine,
            "image": f"https://alinigermiddle-production.up.railway.app/media/{p.image.split(',')[0]}" if p.image else ""
        })

    return jsonify(resultats), 200


@produit_routes.route('/produits_alibaba_similaires', methods=['POST'])
def produits_alibaba_similaires():
    data = request.json
    nom = data.get('nom', '').strip()
    categorie = data.get('categorie', '').strip()

    if not nom or not categorie:
        return jsonify({"error": "Nom et catégorie sont requis."}), 400

    produits_similaires = ProduitAlibaba.query.filter(
        func.lower(ProduitAlibaba.categorie) == categorie.lower(),
        or_(
            func.lower(ProduitAlibaba.nom).like(f"%{nom.lower()}%"),
            func.lower(ProduitAlibaba.description).like(f"%{nom.lower()}%")
        )
    ).all()

    resultats = []
    for p in produits_similaires:
        resultats.append({
            "id": p.id,
            "nom": p.nom,
            "categorie": p.categorie,
            "prix_estime": p.prix_estime,
            "image": f"https://alinigermiddle-production.up.railway.app/media/{p.image.split(',')[0]}" if p.image else "",
            "vendeur": p.vendeur,
            "note": p.note,
            "couleur": p.couleur
        })

    return jsonify(resultats), 200
