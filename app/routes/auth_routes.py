from flask import Blueprint, request, jsonify, current_app as app
import jwt
from ..models import User
from app import db

auth_routes = Blueprint('auth_routes', __name__)

# ➕ Enregistrement sécurisé (tous les champs requis)
@auth_routes.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()

    required_fields = ['nom', 'prenom', 'email', 'tel', 'adresse', 'ville', 'pays', 'mot_de_passe']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'Le champ {field} est requis.'}), 400

    mot_de_passe = data.get('mot_de_passe')
    if len(mot_de_passe) < 6:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 6 caractères.'}), 400

    # Vérification email ou téléphone déjà utilisé
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Cet email est déjà utilisé.'}), 400

    if User.query.filter_by(tel=data['tel']).first():
        return jsonify({'error': 'Ce numéro de téléphone est déjà utilisé.'}), 400

    new_user = User(
        nom=data['nom'],
        prenom=data['prenom'],
        email=data['email'],
        tel=data['tel'],
        adresse=data['adresse'],
        ville=data['ville'],
        pays=data['pays'],
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


# 🔐 Connexion (par email ou téléphone)
@auth_routes.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    identifiant = data.get('identifiant')  # Email ou téléphone
    mot_de_passe = data.get('mot_de_passe')

    if not identifiant or not mot_de_passe:
        return jsonify({'error': 'Identifiant (email ou téléphone) et mot de passe requis.'}), 400

    user = User.query.filter(
        (User.email == identifiant) | (User.tel == identifiant)
    ).first()

    if not user or not user.check_password(mot_de_passe):
        return jsonify({'error': 'Identifiant ou mot de passe incorrect.'}), 401

    token = generate_token(user.id)

    return jsonify({
        'message': 'Connexion réussie',
        'user_id': user.id,
        'token': token
    }), 200


# ✅ Génération du token JWT
def generate_token(user_id):
    return jwt.encode(
        {'user_id': user_id},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
