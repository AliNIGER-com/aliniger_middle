from flask import Blueprint, jsonify, request
from sqlalchemy import or_, func
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
        "image": f"/uploads/afrique/{p.image}" if p.image else None,
        "categorie": p.categorie,
        "vendeur_id": p.vendeur_id,
        "vendeur": p.vendeur.to_dict() if p.vendeur else None,
        "stock": p.stock,
        "délai_livraison": p.delais_livraison,
        "frais": p.frais,
        "couleur": p.couleur
    } for p in produits])

@produit_routes.route('/api/produits_alibaba', methods=['GET'])
def get_produits_alibaba():
    produits = ProduitAlibaba.query.all()
    return jsonify([{
        "id": p.id,
        "nom": p.nom,
        "description": p.description,
        "prix_estime": p.prix_estime,
        "image": f"/uploads/alibaba/{p.image}" if p.image else None,
        "min_commande": p.min_commande,
        "frais_livraison_estime": p.frais_livraison_estime,
        "vendeur": p.vendeur,
        "note": p.note,
        "couleur": p.couleur,
        "délai_livraison": p.delais_livraison
    } for p in produits])


@produit_routes.route('/api/categories', methods=['GET'])
def get_categories():
    categories = [
        "Électronique", "Beauté", "Industrie", "Santé", "Maison", "Vêtements",
        "Sport", "Automobile", "Jouets", "Bricolage", "Mobilier", "Bijoux",
        "Papeterie", "Informatique", "Chaussures", "Alimentation", "Accessoires",
        "Montres", "Téléphones", "Éclairage"
    ]
    return jsonify(categories)


@produit_routes.route('/api/produits_afrique_similaires', methods=['POST'])
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

    resultats = [{
        "id": p.id,
        "nom": p.nom,
        "categorie": p.categorie,
        "prix": p.prix,
        "origine": p.pays_origine,
        "image": f"/media/{p.image.split(',')[0]}" if p.image else None
    } for p in produits_similaires]

    return jsonify(resultats), 200


@produit_routes.route('/api/produits_alibaba_similaires', methods=['POST'])
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

    resultats = [{
        "id": p.id,
        "nom": p.nom,
        "categorie": p.categorie,
        "prix_estime": p.prix_estime,
        "image": f"/uploads/alibaba/{p.image}" if p.image else None,
        "vendeur": p.vendeur,
        "note": p.note,
        "couleur": p.couleur,
        "délai_livraison": p.delais_livraison
    } for p in produits_similaires]

    return jsonify(resultats), 200
