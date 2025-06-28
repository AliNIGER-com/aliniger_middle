from flask import Blueprint, jsonify
from .decorators import token_required
from ..models import User

user_routes = Blueprint('user_routes', __name__)

@user_routes.route('/api/users/<int:user_id>', methods=['GET'])
@token_required
def get_user(current_user, user_id):
    if current_user.id != user_id:
        return jsonify({'error': 'Accès refusé'}), 403
    return jsonify({
        "nom": current_user.nom,
        "prenom": current_user.prenom,
        "email": current_user.email,
        "tel": current_user.tel,
        "adresse": current_user.adresse,
        "ville": current_user.ville,
        "pays": current_user.pays
    })
