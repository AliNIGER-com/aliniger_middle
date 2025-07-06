from flask import Blueprint, jsonify, current_app
from ..models import Vendeur, Boutique, ProduitAfrique

boutique_routes = Blueprint('boutique_routes', __name__)

@boutique_routes.route('/api/boutiques', methods=['GET'])
def get_boutiques():
    boutiques = Boutique.query.all()
    return jsonify([{
        "id": b.id,
        "nom": b.nom,
        "description": b.description,
        "icone": f"/media/{b.icone}" if b.icone else None,
        "image": f"/media/{b.image}" if b.image else None,
        "video": f"/media/{b.video}" if b.video else None,
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
        "image": f"/media/{b.image}" if b.image else None,
        "video": f"/media/{b.video}" if b.video else None,
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
            "image": f"/media/{p.image}" if p.image else None,
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
        "image": f"/media/{v.image}" if v.image else None
    } for v in vendeurs])


@boutique_routes.route('/api/vendeurs/<int:vendeur_id>', methods=['GET'])
def get_vendeur_detail(vendeur_id):
    v = Vendeur.query.get_or_404(vendeur_id)
    return jsonify({
        "id": v.id,
        "nom": v.nom,
        "email": v.email,
        "telephone": v.tel,
        "adresse": v.adresse,
        "ville": v.ville,
        "pays": v.pays,
        "description": v.description,
        "image": f"/media/{v.image}" if v.image else None
    })
