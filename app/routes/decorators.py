from flask import request, jsonify, current_app as app
from functools import wraps
import jwt
from ..models import User

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if not token:
            return jsonify({'error': 'Token manquant'}), 403
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = User.query.get(data['user_id'])
        except Exception:
            return jsonify({'error': 'Token invalide'}), 403
        return f(current_user, *args, **kwargs)
    return decorated
