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
    mot_de_passe_hash = generate_password_hash(data['mot_de_passe'])
    new_user = User(**{k: data[k] for k in data if k != 'mot_de_passe'}, mot_de_passe=mot_de_passe_hash)
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
