from flask import request, jsonify, current_app as app
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
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            user_id = data.get('user_id')
            if not user_id:
                return jsonify({'error': 'Token invalide : user_id manquant'}), 401
            
            current_user = User.query.get(user_id)
            if not current_user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        except Exception as e:
            return jsonify({'error': 'Erreur lors de la vérification du token'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated
