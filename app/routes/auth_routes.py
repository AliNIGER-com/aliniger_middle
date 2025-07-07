from flask import Blueprint, request, jsonify, current_app as app
import jwt
from ..models import User
from app import db

auth_routes = Blueprint('auth_routes', __name__)

# ➕ Enregistrement sécurisé (nom + mot de passe hashé)
@auth_routes.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()
    nom = data.get('nom')
    mot_de_passe = data.get('mot_de_passe')

    if not nom or not mot_de_passe:
        return jsonify({'error': 'Nom et mot de passe requis'}), 400

    if len(mot_de_passe) < 6:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères.'}), 400

    new_user = User(
        nom=nom,
        prenom="",
        email="",
        adresse="",
        ville="",
        pays="",
        tel="",
        role="client"
    )
    new_user.set_password(mot_de_passe)

    db.session.add(new_user)
    db.session.commit()

    token = generate_token(new_user.id)

    return jsonify({
        'message': 'Utilisateur enregistré',
        'user_id': new_user.id,
        'token': token
    }), 201


# 🔐 Connexion avec vérification de mot de passe hashé
@auth_routes.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    nom = data.get('nom')
    mot_de_passe = data.get('mot_de_passe')

    if not nom or not mot_de_passe:
        return jsonify({'error': 'Nom et mot de passe requis'}), 400

    user = User.query.filter_by(nom=nom).first()

    if not user or not user.check_password(mot_de_passe):
        return jsonify({'error': 'Nom ou mot de passe incorrect'}), 401

    token = generate_token(user.id)

    return jsonify({
        'message': 'Connexion réussie',
        'user_id': user.id,
        'token': token
    }), 200


# ✅ Génération de token JWT sans expiration
def generate_token(user_id):
    return jwt.encode(
        {'user_id': user_id},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
