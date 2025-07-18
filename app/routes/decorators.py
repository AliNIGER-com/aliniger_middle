from flask import request, jsonify, current_app
from functools import wraps
import jwt
from ..models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        token = None

        if auth_header.startswith('Bearer '):
            token = auth_header[7:]

        if not token:
            return jsonify({'error': 'Token manquant'}), 401

        try:
            data = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
            user_id = data.get('user_id')

            if not user_id:
                return jsonify({'error': 'Token invalide (user_id manquant)'}), 401

            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 401

        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        except Exception as e:
            return jsonify({'error': f'Erreur de token: {str(e)}'}), 401

        return f(user, *args, **kwargs)
    return decorated


def generate_token(user_id):
    return jwt.encode(
        {'user_id': user_id},
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
