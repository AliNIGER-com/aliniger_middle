from flask import Blueprint, request, jsonify, current_app as app
import jwt
from ..models import User
from app import db

auth_routes = Blueprint('auth_routes', __name__)

# ➕ Enregistrement rapide (nom + téléphone)
@auth_routes.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()
    nom = data.get('nom')
    tel = data.get('tel')

    if not nom or not tel:
        return jsonify({'error': 'Nom et téléphone sont requis'}), 400

    # Vérifier si le numéro est déjà utilisé
    existing_user = User.query.filter_by(tel=tel).first()
    if existing_user:
        return jsonify({
            'message': 'Utilisateur déjà inscrit',
            'user_id': existing_user.id,
            'token': generate_token(existing_user.id)
        }), 200

    # Création du nouvel utilisateur
    new_user = User(nom=nom, tel=tel, prenom="", email="", adresse="", ville="", pays="")
    db.session.add(new_user)
    db.session.commit()

    # Générer un token JWT
    token = generate_token(new_user.id)

    return jsonify({
        'message': 'Utilisateur enregistré',
        'user_id': new_user.id,
        'token': token
    }), 201


# 🔐 Connexion rapide par téléphone
@auth_routes.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    tel = data.get('tel')

    if not tel:
        return jsonify({'error': 'Téléphone requis'}), 400

    user = User.query.filter_by(tel=tel).first()

    if not user:
        return jsonify({'error': 'Aucun utilisateur trouvé avec ce numéro'}), 404

    token = generate_token(user.id)

    return jsonify({
        'message': 'Connexion réussie',
        'user_id': user.id,
        'token': token
    }), 200


# ✅ Token sans expiration
def generate_token(user_id):
    return jwt.encode(
        {
            'user_id': user_id
            # pas de champ 'exp' donc pas d'expiration
        },
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
