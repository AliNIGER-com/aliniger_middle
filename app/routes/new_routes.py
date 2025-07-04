# routes/new_routes.py

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

from app import db
from app.models import (
    Boutique, ProduitAfrique, BoutiqueVisit, BoutiqueView,
    Commande, DetailCommande, CommandeReview,
    Paiement, Notification, User
)

new_routes = Blueprint('new_routes', __name__)

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== BOUTIQUES ====================

@new_routes.route('/boutiques/search', methods=['POST'])
def search_boutiques():
    try:
        data = request.get_json()
        query = data.get('query', '')
        category = data.get('category')

        boutiques = Boutique.query
        if query:
            boutiques = boutiques.filter(Boutique.nom.ilike(f"%{query}%") | Boutique.description.ilike(f"%{query}%"))
        if category:
            boutiques = boutiques.join(ProduitAfrique).filter(ProduitAfrique.categorie == category)
        
        result = [b.to_dict() for b in boutiques.all()]
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/view', methods=['POST'])
def track_boutique_view():
    try:
        data = request.get_json()
        boutique_id = data.get('boutique_id')
        user_id = data.get('user_id')

        if not boutique_id:
            return jsonify({'error': 'boutique_id requis'}), 400

        view = BoutiqueView(
            boutique_id=boutique_id,
            user_id=user_id,
            date_view=datetime.utcnow(),
            ip_address=request.remote_addr
        )
        db.session.add(view)

        boutique = Boutique.query.get(boutique_id)
        if boutique:
            boutique.nb_vues = (boutique.nb_vues or 0) + 1

        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/<int:boutique_id>/produits', methods=['GET'])
def get_boutique_produits(boutique_id):
    try:
        produits = ProduitAfrique.query.filter_by(boutique_id=boutique_id).order_by(ProduitAfrique.date_creation.desc()).all()
        return jsonify([p.to_dict() for p in produits]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/visit', methods=['POST'])
@jwt_required()
def add_boutique_visit():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        boutique_id = data.get('boutiqueId')

        if not boutique_id:
            return jsonify({'error': 'boutiqueId requis'}), 400

        visit = BoutiqueVisit(
            boutique_id=boutique_id,
            user_id=user_id,
            date_visit=datetime.utcnow()
        )
        db.session.add(visit)
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ==================== COMMANDES ====================

@new_routes.route('/commandes/details/<int:commande_id>', methods=['GET'])
@jwt_required()
def get_commande_details(commande_id):
    try:
        user_id = get_jwt_identity()
        commande = Commande.query.filter_by(id=commande_id, user_id=user_id).first()
        if not commande:
            return jsonify({'error': 'Commande non trouvée'}), 404

        commande_data = commande.to_dict()
        user = User.query.get(commande.user_id)
        commande_data['user_nom'] = user.nom if user else ''
        commande_data['user_prenom'] = user.prenom if user else ''

        details = DetailCommande.query.filter_by(commande_id=commande_id).all()
        details_data = [d.to_dict(with_produit=True) for d in details]

        return jsonify({'commande': commande_data, 'details': details_data}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/commandes/<int:commande_id>/review', methods=['POST'])
@jwt_required()
def add_review(commande_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        rating = data.get('rating')
        comment = data.get('comment', '')

        if not rating or not (1 <= rating <= 5):
            return jsonify({'error': 'Rating invalide (1-5)'}), 400

        commande = Commande.query.filter_by(id=commande_id, user_id=user_id).first()
        if not commande:
            return jsonify({'error': 'Commande non trouvée'}), 404

        review = CommandeReview(
            commande_id=commande_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            date_review=datetime.utcnow()
        )
        db.session.add(review)
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@new_routes.route('/commandes/<int:commande_id>/status', methods=['PUT'])
@jwt_required()
def update_commande_status(commande_id):
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        status = data.get('status')
        note = data.get('note', '')

        if not status:
            return jsonify({'error': 'Status requis'}), 400

        permission = (
            db.session.query(Commande)
            .join(DetailCommande, Commande.id == DetailCommande.commande_id)
            .join(ProduitAfrique, DetailCommande.produit_id == ProduitAfrique.id)
            .join(Boutique, ProduitAfrique.boutique_id == Boutique.id)
            .filter(Commande.id == commande_id, Boutique.user_id == user_id)
            .first()
        )
        if not permission:
            return jsonify({'error': 'Permission refusée'}), 403

        commande = Commande.query.get(commande_id)
        commande.status = status
        commande.note_vendeur = note
        commande.date_maj = datetime.utcnow()
        db.session.commit()

        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

# Blueprint (déjà créé, mais je le rappelle ici pour cohérence)
new_routes = Blueprint('new_routes', __name__)

# Configuration upload
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """Exécute une requête SQL brute (à ajuster selon ta config)"""
    try:
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if fetch_one:
            result = cursor.fetchone()
        elif fetch_all:
            result = cursor.fetchall()
        else:
            result = None

        conn.commit()
        cursor.close()
        conn.close()
        return result
    except Exception as e:
        current_app.logger.error(f"Erreur DB: {e}")
        return None


# ==================== PAIEMENTS ====================

@new_routes.route('/config/paiement', methods=['GET'])
def get_paiement_config():
    try:
        config = {
            'methods': [
                {'id': 'orange_money', 'name': 'Orange Money', 'enabled': True},
                {'id': 'moov_money', 'name': 'Moov Money', 'enabled': True},
                {'id': 'airtel_money', 'name': 'Airtel Money', 'enabled': True},
                {'id': 'virement', 'name': 'Virement bancaire', 'enabled': True}
            ],
            'fees': {
                'orange_money': 0.02,
                'moov_money': 0.025,
                'airtel_money': 0.02,
                'virement': 0.01
            }
        }
        return jsonify(config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@new_routes.route('/paiements', methods=['POST'])
@jwt_required()
def create_paiement():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        amount = data.get('amount')
        method = data.get('method')
        commande_id = data.get('commandeId')

        if not all([amount, method, commande_id]):
            return jsonify({'error': 'Données manquantes'}), 400

        payment_id = f"PAY_{uuid.uuid4().hex[:12]}"

        # Ici tu peux utiliser ORM ou insert SQL selon ton choix
        sql = """
            INSERT INTO paiements (payment_id, user_id, commande_id, amount, method, status, date_creation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        execute_query(sql, [payment_id, user_id, commande_id, amount, method, 'pending', datetime.utcnow()], fetch_all=False)

        payment_url = f"https://payment-gateway.com/pay/{payment_id}"

        return jsonify({'paymentId': payment_id, 'paymentUrl': payment_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@new_routes.route('/admin/validate-payment', methods=['POST'])
@jwt_required()
def validate_payment():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({'error': 'Permission refusée'}), 403

        data = request.get_json()
        payment_id = data.get('paymentId')
        status = data.get('status')

        if not payment_id or not status:
            return jsonify({'error': 'Données manquantes'}), 400

        paiement = Paiement.query.filter_by(payment_id=payment_id).first()
        if not paiement:
            return jsonify({'error': 'Paiement non trouvé'}), 404

        paiement.status = status
        paiement.date_validation = datetime.utcnow()
        paiement.validated_by = user_id

        db.session.commit()
        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== NOTIFICATIONS ====================

@new_routes.route('/notifications/nouvelle-commande', methods=['POST'])
@jwt_required()
def send_notification():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        commande_id = data.get('commandeId')
        vendeur_id = data.get('vendeurId')
        message = data.get('message')

        if not all([commande_id, vendeur_id, message]):
            return jsonify({'error': 'Données manquantes'}), 400

        notification = Notification(
            user_id=vendeur_id,
            type='nouvelle_commande',
            title='Nouvelle commande reçue',
            message=message,
            data=f'{{"commandeId": {commande_id}}}',
            date_creation=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@new_routes.route('/notifications/order-confirmation', methods=['POST'])
@jwt_required()
def send_order_confirmation():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        commande_id = data.get('commandeId')
        user_target_id = data.get('userId')
        details = data.get('details', {})

        if not all([commande_id, user_target_id]):
            return jsonify({'error': 'Données manquantes'}), 400

        notification = Notification(
            user_id=user_target_id,
            type='confirmation_commande',
            title='Commande confirmée',
            message=f'Votre commande #{commande_id} a été confirmée',
            data=str(details),
            date_creation=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()

        return jsonify({'success': True}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ==================== FRAIS ====================

@new_routes.route('/frais/configuration', methods=['GET'])
def get_frais_configuration():
    try:
        config = {
            'fraisPortAfrique': 1000,
            'fraisPortAlibaba': 3000,
            'fraisTransaction': 2000
        }
        return jsonify(config), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PARTAGE ====================

@new_routes.route('/orders/share', methods=['POST'])
@jwt_required()
def share_order():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        commande_id = data.get('commandeId')
        platform = data.get('platform')
        message = data.get('message', '')

        if not all([commande_id, platform]):
            return jsonify({'error': 'Données manquantes'}), 400

        # Vérifier que la commande appartient bien à l'utilisateur
        sql_check = "SELECT id FROM commandes WHERE id = %s AND user_id = %s"
        commande_check = execute_query(sql_check, [commande_id, user_id], fetch_one=True)

        if not commande_check:
            return jsonify({'error': 'Commande non trouvée'}), 404

        share_url = f"https://votre-app.com/orders/{commande_id}/share"

        sql = """
            INSERT INTO order_shares (commande_id, user_id, platform, message, date_share)
            VALUES (%s, %s, %s, %s, %s)
        """
        execute_query(sql, [commande_id, user_id, platform, message, datetime.utcnow()], fetch_all=False)

        return jsonify({'shareUrl': share_url}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== PRODUITS ====================

@new_routes.route('/produits/view', methods=['POST'])
@jwt_required()
def add_product_view():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        produit_id = data.get('produitId')

        if not produit_id:
            return jsonify({'error': 'produitId requis'}), 400

        sql = """
            INSERT INTO product_views (produit_id, user_id, date_view, ip_address)
            VALUES (%s, %s, %s, %s)
        """
        execute_query(sql, [produit_id, user_id, datetime.utcnow(), request.remote_addr], fetch_all=False)

        sql_update = "UPDATE produits SET nb_vues = nb_vues + 1 WHERE id = %s"
        execute_query(sql_update, [produit_id], fetch_all=False)

        return jsonify({'success': True}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ==================== UTILISATEURS ====================

@new_routes.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403

        data = request.get_json()
        allowed_fields = ['nom', 'prenom', 'email', 'tel', 'adresse', 'ville', 'pays']

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        modified = False
        for field in allowed_fields:
            if field in data:
                setattr(user, field, data[field])
                modified = True

        if not modified:
            return jsonify({'error': 'Aucun champ à modifier'}), 400

        user.date_maj = datetime.utcnow()
        db.session.commit()

        return jsonify({'user': user.to_dict()}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@new_routes.route('/users/<int:user_id>/avatar', methods=['PUT'])
@jwt_required()
def update_user_avatar(user_id):
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403

        if 'avatar' not in request.files:
            return jsonify({'error': 'Aucun fichier fourni'}), 400

        file = request.files['avatar']
        if file.filename == '':
            return jsonify({'error': 'Aucun fichier sélectionné'}), 400

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{user_id}_{uuid.uuid4().hex}_{filename}"
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            file.save(file_path)

            user = User.query.get(user_id)
            if not user:
                return jsonify({'error': 'Utilisateur non trouvé'}), 404

            user.avatar_url = unique_filename
            db.session.commit()

            return jsonify({'avatarUrl': unique_filename}), 200
        else:
            return jsonify({'error': 'Type de fichier non autorisé'}), 400

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@new_routes.route('/users/<int:user_id>/produits-inspires', methods=['GET'])
@jwt_required()
def get_produits_inspires(user_id):
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403

        subquery = (
            db.session.query(DetailCommande.produit_id)
            .join(Commande)
            .filter(Commande.user_id == user_id)
            .subquery()
        )
        produits = (
            db.session.query(ProduitAfrique)
            .join(DetailCommande)
            .join(Commande)
            .filter(Commande.user_id != user_id)
            .filter(~ProduitAfrique.id.in_(subquery))
            .order_by(ProduitAfrique.popularite.desc())
            .limit(10)
            .all()
        )
        return jsonify([p.to_dict() for p in produits]), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@new_routes.route('/users/<int:user_id>/referral-link', methods=['POST'])
@jwt_required()
def generate_referral_link(user_id):
    try:
        current_user_id = get_jwt_identity()
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403

        referral_code = f"ref-{user_id}-{uuid.uuid4().hex[:8]}"
        base_url = "https://aliniger.com/signup"
        referral_link = f"{base_url}?referral={referral_code}"

        sql = """
            INSERT INTO referral_codes (user_id, code, created_at)
            VALUES (%s, %s, %s)
        """
        execute_query(sql, [user_id, referral_code, datetime.utcnow()], fetch_all=False)

        return jsonify({'referralLink': referral_link}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500
