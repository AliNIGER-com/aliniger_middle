from flask import Blueprint, jsonify
from ..models import User
from .. import db

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)

    if not user:
        return jsonify({'error': 'Utilisateur non trouvé'}), 404

    return jsonify({
        "id": user.id,
        "nom": user.nom,
        "prenom": user.prenom,
        "email": user.email,
        "tel": user.tel,
        "adresse": user.adresse,
        "ville": user.ville,
        "pays": user.pays
    })
