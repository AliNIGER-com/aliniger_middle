from flask import Blueprint, jsonify, url_for

from ..models import Vendeur

vendeur_bp = Blueprint('vendeur', __name__, url_prefix='/api/vendeurs')

@vendeur_bp.route('', methods=['GET'])
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

@vendeur_bp.route('/<int:vendeur_id>', methods=['GET'])
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
