from flask import Blueprint, request, jsonify
from datetime import datetime
from ..models import Commande, DetailCommande, CommandeGroupee, Tracking
from app import db

commande_routes = Blueprint('commande_routes', __name__)

@commande_routes.route('/api/commandes', methods=['POST'])
def create_commande():
    data = request.get_json()
    commande = Commande(
        user_id=data['user_id'],
        type_commande=data['type_commande'],
        date_commande=datetime.utcnow(),
        statut='en_attente'
    )
    db.session.add(commande)
    db.session.commit()
    return jsonify({'message': 'Commande créée', 'commande_id': commande.id}), 201


@commande_routes.route('/api/details_commande', methods=['POST'])
def add_detail_commande():
    data = request.get_json()
    detail = DetailCommande(**data)
    db.session.add(detail)
    db.session.commit()
    return jsonify({'message': 'Détail commande ajouté'}), 201


@commande_routes.route('/api/commandes_groupees', methods=['POST'])
def create_commande_groupee():
    data = request.get_json()
    groupee = CommandeGroupee(
        produit_alibaba_id=data['produit_alibaba_id'],
        statut='en_cours',
        nb_utilisateurs=1,
        deadline=data['deadline'],
        frais_partage_total=data['frais_partage_total']
    )
    db.session.add(groupee)
    db.session.commit()
    return jsonify({'message': 'Commande groupée créée'}), 201


@commande_routes.route('/api/commandes_groupees/<int:produit_id>', methods=['GET'])
def get_commande_groupee(produit_id):
    groupe = CommandeGroupee.query.filter_by(produit_alibaba_id=produit_id, statut='en_cours').first()
    if groupe:
        return jsonify({
            "id": groupe.id,
            "deadline": groupe.deadline,
            "nb_utilisateurs": groupe.nb_utilisateurs,
            "frais_partage_total": groupe.frais_partage_total
        })
    return jsonify({"message": "Aucune commande groupée active"}), 404


@commande_routes.route('/api/tracking/<int:commande_id>', methods=['GET'])
def get_tracking(commande_id):
    tracking = Tracking.query.filter_by(commande_id=commande_id).first()
    if tracking:
        return jsonify({
            "etat": tracking.etat,
            "date_maj": tracking.date_maj
        })
    return jsonify({"message": "Aucun suivi trouvé"}), 404


@commande_routes.route('/api/commandes/<int:user_id>', methods=['GET'])
def get_commandes_user(user_id):
    commandes = Commande.query.filter_by(user_id=user_id).all()
    return jsonify([{
        "id": c.id,
        "type_commande": c.type_commande,
        "date_commande": c.date_commande,
        "statut": c.statut
    } for c in commandes])
