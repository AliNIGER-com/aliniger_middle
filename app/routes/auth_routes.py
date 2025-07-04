from flask import Blueprint, request, jsonify, current_app as app
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from ..models import User
from app import db  # ✅ correct

auth_routes = Blueprint('auth_routes', __name__)

@auth_routes.route('/api/users', methods=['POST'])
def register_user():
    data = request.get_json()

    # Vérifie si le champ 'password' est présent
    if 'password' not in data:
        return jsonify({'error': 'Le mot de passe est requis.'}), 400

    # Hash le mot de passe
    mot_de_passe_hash = generate_password_hash(data['password'])

    # Crée un nouvel utilisateur en remplaçant 'password' par 'mot_de_passe'
    user_data = {k: data[k] for k in data if k != 'password'}
    user_data['mot_de_passe'] = mot_de_passe_hash

    new_user = User(**user_data)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'Utilisateur enregistré'}), 201


@auth_routes.route('/api/login', methods=['POST'])
def login_user():
    data = request.get_json()
    user = User.query.filter_by(email=data.get('email')).first()
    if user and check_password_hash(user.mot_de_passe, data.get('password')):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.utcnow() + timedelta(days=1)
        }, app.config['SECRET_KEY'], algorithm='HS256')
        return jsonify({'token': token, 'user_id': user.id}), 200
    return jsonify({'error': 'Email ou mot de passe incorrect'}), 401
