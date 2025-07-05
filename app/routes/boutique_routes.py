from flask import Blueprint, jsonify, url_for, current_app
from ..models import Vendeur, Boutique, ProduitAfrique

boutique_routes = Blueprint('boutique_routes', __name__)

@boutique_routes.route('/api/boutiques', methods=['GET'])
def get_boutiques():
    boutiques = Boutique.query.all()
    return jsonify([{
        "id": b.id,
        "nom": b.nom,
        "description": b.description,
        # ici on génère l'URL complète pour l'image
        "image": url_for('static', filename=f'media/{b.image}', _external=True) if b.image else None,
        "video": b.video,
        "note": b.note,
        "localisation": b.localisation,
        "ville": b.ville,
        "pays": b.pays,
        "vendeur_id": b.vendeur_id,
        "vendeur_nom": b.vendeur.nom if b.vendeur else None
    } for b in boutiques])

@boutique_routes.route('/api/boutiques/<int:boutique_id>', methods=['GET'])
def get_boutique_detail(boutique_id):
    b = Boutique.query.get_or_404(boutique_id)
    produits = ProduitAfrique.query.filter_by(vendeur_id=b.vendeur_id).all()
    return jsonify({
        "id": b.id,
        "nom": b.nom,
        "description": b.description,
        "image": url_for('static', filename=f'media/{b.image}', _external=True) if b.image else None,
        "video": b.video,
        "note": b.note,
        "localisation": b.localisation,
        "ville": b.ville,
        "pays": b.pays,
        "vendeur_id": b.vendeur_id,
        "vendeur_nom": b.vendeur.nom if b.vendeur else None,
        "produits": [{
            "id": p.id,
            "nom": p.nom,
            "description": p.description,
            "prix": p.prix,
            "image": url_for('static', filename=f'media/{p.image}', _external=True) if p.image else None,
            "categorie": p.categorie,
            "stock": p.stock
        } for p in produits]
    })

@boutique_routes.route('/api/vendeurs', methods=['GET'])
def get_vendeurs():
    vendeurs = Vendeur.query.all()
    return jsonify([{
        "id": v.id,
        "nom": v.nom,
        "email": v.email,
        "telephone": v.telephone,
        "adresse": v.adresse,
        "ville": v.ville,
        "pays": v.pays,
        "description": v.description,
        "image": url_for('static', filename=f'media/{v.image}', _external=True) if v.image else None
    } for v in vendeurs])

@boutique_routes.route('/api/vendeurs/<int:vendeur_id>', methods=['GET'])
def get_vendeur_detail(vendeur_id):
    v = Vendeur.query.get_or_404(vendeur_id)
    return jsonify({
        "id": v.id,
        "nom": v.nom,
        "email": v.email,
        "telephone": v.telephone,
        "adresse": v.adresse,
        "ville": v.ville,
        "pays": v.pays,
        "description": v.description,
        "image": url_for('static', filename=f'media/{v.image}', _external=True) if v.image else None
    })
