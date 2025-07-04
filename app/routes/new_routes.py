from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os
from datetime import datetime
import uuid

# Créer le blueprint pour les nouvelles routes
new_routes = Blueprint('new_routes', __name__)

# Configuration pour upload d'images
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def execute_query(query, params=None, fetch_one=False, fetch_all=True):
    """Helper function pour exécuter les requêtes SQL"""
    try:
        from app import get_db_connection  # Remplacer par votre module DB
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        print(f"Erreur base de données: {e}")
        return None

# ==================== BOUTIQUES ====================

@new_routes.route('/boutiques/search', methods=['POST'])
def search_boutiques():
    """Recherche de boutiques"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        category = data.get('category')
        
        sql = """
            SELECT b.*, COUNT(p.id) as nb_produits
            FROM boutiques b
            LEFT JOIN produits p ON b.id = p.boutique_id
            WHERE b.nom LIKE %s OR b.description LIKE %s
        """
        params = [f'%{query}%', f'%{query}%']
        
        if category:
            sql += " AND b.categorie = %s"
            params.append(category)
            
        sql += " GROUP BY b.id ORDER BY nb_produits DESC"
        
        boutiques = execute_query(sql, params)
        
        return jsonify(boutiques or []), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/filter', methods=['POST'])
def filter_boutiques():
    """Filtrage des boutiques"""
    try:
        data = request.get_json()
        category = data.get('category')
        search = data.get('search', '')
        
        sql = "SELECT * FROM boutiques WHERE 1=1"
        params = []
        
        if category:
            sql += " AND categorie = %s"
            params.append(category)
            
        if search:
            sql += " AND (nom LIKE %s OR description LIKE %s)"
            params.extend([f'%{search}%', f'%{search}%'])
            
        sql += " ORDER BY nom ASC"
        
        boutiques = execute_query(sql, params)
        
        return jsonify(boutiques or []), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/view', methods=['POST'])
def track_boutique_view():
    """Suivi des vues de boutiques"""
    try:
        data = request.get_json()
        boutique_id = data.get('boutique_id')
        user_id = data.get('user_id')
        
        if not boutique_id:
            return jsonify({'error': 'boutique_id requis'}), 400
            
        # Insérer la vue
        sql = """
            INSERT INTO boutique_views (boutique_id, user_id, date_view, ip_address)
            VALUES (%s, %s, %s, %s)
        """
        params = [boutique_id, user_id, datetime.now(), request.remote_addr]
        
        execute_query(sql, params, fetch_all=False)
        
        # Mettre à jour le compteur de vues
        sql_update = "UPDATE boutiques SET nb_vues = nb_vues + 1 WHERE id = %s"
        execute_query(sql_update, [boutique_id], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/<int:boutique_id>/produits', methods=['GET'])
def get_boutique_produits(boutique_id):
    """Récupérer les produits d'une boutique"""
    try:
        sql = """
            SELECT p.*, c.nom as categorie_nom
            FROM produits p
            LEFT JOIN categories c ON p.categorie_id = c.id
            WHERE p.boutique_id = %s
            ORDER BY p.date_creation DESC
        """
        
        produits = execute_query(sql, [boutique_id])
        
        return jsonify(produits or []), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/boutiques/visit', methods=['POST'])
@jwt_required()
def add_boutique_visit():
    """Enregistrer une visite de boutique"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        boutique_id = data.get('boutiqueId')
        
        if not boutique_id:
            return jsonify({'error': 'boutiqueId requis'}), 400
            
        sql = """
            INSERT INTO boutique_visits (boutique_id, user_id, date_visit)
            VALUES (%s, %s, %s)
        """
        
        execute_query(sql, [boutique_id, user_id, datetime.now()], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== COMMANDES ====================

@new_routes.route('/commandes/details/<int:commande_id>', methods=['GET'])
@jwt_required()
def get_commande_details(commande_id):
    """Récupérer les détails d'une commande"""
    try:
        user_id = get_jwt_identity()
        
        # Vérifier que la commande appartient à l'utilisateur
        sql_check = "SELECT id FROM commandes WHERE id = %s AND user_id = %s"
        commande_check = execute_query(sql_check, [commande_id, user_id], fetch_one=True)
        
        if not commande_check:
            return jsonify({'error': 'Commande non trouvée'}), 404
            
        # Récupérer les détails de la commande
        sql_commande = """
            SELECT c.*, u.nom as user_nom, u.prenom as user_prenom
            FROM commandes c
            JOIN users u ON c.user_id = u.id
            WHERE c.id = %s
        """
        
        commande = execute_query(sql_commande, [commande_id], fetch_one=True)
        
        # Récupérer les détails des produits
        sql_details = """
            SELECT dc.*, p.nom as produit_nom, p.prix as produit_prix, p.image_url
            FROM details_commande dc
            JOIN produits p ON dc.produit_id = p.id
            WHERE dc.commande_id = %s
        """
        
        details = execute_query(sql_details, [commande_id])
        
        return jsonify({
            'commande': commande,
            'details': details or []
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/commandes/<int:commande_id>/review', methods=['POST'])
@jwt_required()
def add_review(commande_id):
    """Ajouter un avis sur une commande"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        rating = data.get('rating')
        comment = data.get('comment', '')
        
        if not rating or rating < 1 or rating > 5:
            return jsonify({'error': 'Rating invalide (1-5)'}), 400
            
        # Vérifier que la commande appartient à l'utilisateur
        sql_check = "SELECT id FROM commandes WHERE id = %s AND user_id = %s"
        commande_check = execute_query(sql_check, [commande_id, user_id], fetch_one=True)
        
        if not commande_check:
            return jsonify({'error': 'Commande non trouvée'}), 404
            
        sql = """
            INSERT INTO commande_reviews (commande_id, user_id, rating, comment, date_review)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        execute_query(sql, [commande_id, user_id, rating, comment, datetime.now()], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/commandes/<int:commande_id>/status', methods=['PUT'])
@jwt_required()
def update_commande_status(commande_id):
    """Mettre à jour le statut d'une commande"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        status = data.get('status')
        note = data.get('note', '')
        
        if not status:
            return jsonify({'error': 'Status requis'}), 400
            
        # Vérifier les permissions (vendeur ou admin)
        sql_check = """
            SELECT c.id FROM commandes c
            JOIN details_commande dc ON c.id = dc.commande_id
            JOIN produits p ON dc.produit_id = p.id
            JOIN boutiques b ON p.boutique_id = b.id
            WHERE c.id = %s AND b.user_id = %s
        """
        
        permission_check = execute_query(sql_check, [commande_id, user_id], fetch_one=True)
        
        if not permission_check:
            return jsonify({'error': 'Permission refusée'}), 403
            
        sql = """
            UPDATE commandes 
            SET status = %s, note_vendeur = %s, date_maj = %s
            WHERE id = %s
        """
        
        execute_query(sql, [status, note, datetime.now(), commande_id], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== UTILISATEURS ====================

@new_routes.route('/users/<int:user_id>', methods=['PUT'])
@jwt_required()
def update_user_profile(user_id):
    """Mettre à jour le profil utilisateur"""
    try:
        current_user_id = get_jwt_identity()
        
        # Vérifier que l'utilisateur modifie son propre profil
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403
            
        data = request.get_json()
        
        # Champs autorisés à la modification
        allowed_fields = ['nom', 'prenom', 'email', 'tel', 'adresse', 'ville', 'pays']
        update_fields = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                params.append(data[field])
                
        if not update_fields:
            return jsonify({'error': 'Aucun champ à modifier'}), 400
            
        params.append(user_id)
        
        sql = f"""
            UPDATE users 
            SET {', '.join(update_fields)}, date_maj = %s
            WHERE id = %s
        """
        params.insert(-1, datetime.now())
        
        execute_query(sql, params, fetch_all=False)
        
        # Récupérer l'utilisateur mis à jour
        sql_select = "SELECT * FROM users WHERE id = %s"
        user = execute_query(sql_select, [user_id], fetch_one=True)
        
        return jsonify({'user': user}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/users/<int:user_id>/avatar', methods=['PUT'])
@jwt_required()
def update_user_avatar(user_id):
    """Changer l'avatar utilisateur"""
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
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
            
            # Créer le dossier si nécessaire
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
            
            file.save(file_path)
            
            # Mettre à jour la base de données
            sql = "UPDATE users SET avatar_url = %s WHERE id = %s"
            execute_query(sql, [unique_filename, user_id], fetch_all=False)
            
            return jsonify({'avatarUrl': unique_filename}), 200
        else:
            return jsonify({'error': 'Type de fichier non autorisé'}), 400
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/users/<int:user_id>/produits-inspires', methods=['GET'])
@jwt_required()
def get_produits_inspires(user_id):
    """Récupérer les produits inspirés pour un utilisateur"""
    try:
        current_user_id = get_jwt_identity()
        
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403
            
        # Logique basée sur l'historique d'achat et les préférences
        sql = """
            SELECT DISTINCT p.* FROM produits p
            JOIN details_commande dc ON p.id = dc.produit_id
            JOIN commandes c ON dc.commande_id = c.id
            WHERE c.user_id = %s AND p.id NOT IN (
                SELECT produit_id FROM details_commande dc2
                JOIN commandes c2 ON dc2.commande_id = c2.id
                WHERE c2.user_id = %s
            )
            ORDER BY p.popularite DESC
            LIMIT 10
        """
        
        produits = execute_query(sql, [user_id, user_id])
        
        return jsonify(produits or []), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/users/<int:user_id>/referral-link', methods=['POST'])
@jwt_required()
def generate_referral_link(user_id):
    """Générer un lien de parrainage"""
    try:
        current_user_id = get_jwt_identity()
        
        if current_user_id != user_id:
            return jsonify({'error': 'Permission refusée'}), 403
            
        referral_code = f"REF_{user_id}_{uuid.uuid4().hex[:8]}"
        
        sql = """
            INSERT INTO referral_links (user_id, referral_code, date_creation)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE referral_code = %s
        """
        
        execute_query(sql, [user_id, referral_code, datetime.now(), referral_code], fetch_all=False)
        
        referral_link = f"https://votre-app.com/register?ref={referral_code}"
        
        return jsonify({'referralLink': referral_link}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PAIEMENTS ====================

@new_routes.route('/config/paiement', methods=['GET'])
def get_paiement_config():
    """Configuration des paiements"""
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
    """Créer un paiement"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        amount = data.get('amount')
        method = data.get('method')
        commande_id = data.get('commandeId')
        
        if not all([amount, method, commande_id]):
            return jsonify({'error': 'Données manquantes'}), 400
            
        payment_id = f"PAY_{uuid.uuid4().hex[:12]}"
        
        sql = """
            INSERT INTO paiements (payment_id, user_id, commande_id, amount, method, status, date_creation)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        execute_query(sql, [payment_id, user_id, commande_id, amount, method, 'pending', datetime.now()], fetch_all=False)
        
        # Générer URL de paiement selon la méthode
        payment_url = f"https://payment-gateway.com/pay/{payment_id}"
        
        return jsonify({
            'paymentId': payment_id,
            'paymentUrl': payment_url
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/admin/validate-payment', methods=['POST'])
@jwt_required()
def validate_payment():
    """Valider un paiement (admin)"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Vérifier que l'utilisateur est admin
        sql_admin = "SELECT is_admin FROM users WHERE id = %s"
        admin_check = execute_query(sql_admin, [user_id], fetch_one=True)
        
        if not admin_check or not admin_check[0]:
            return jsonify({'error': 'Permission refusée'}), 403
            
        payment_id = data.get('paymentId')
        status = data.get('status')
        
        if not payment_id or not status:
            return jsonify({'error': 'Données manquantes'}), 400
            
        sql = """
            UPDATE paiements 
            SET status = %s, date_validation = %s, validated_by = %s
            WHERE payment_id = %s
        """
        
        execute_query(sql, [status, datetime.now(), user_id, payment_id], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== NOTIFICATIONS ====================

@new_routes.route('/notifications/nouvelle-commande', methods=['POST'])
@jwt_required()
def send_notification():
    """Envoyer notification nouvelle commande"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        commande_id = data.get('commandeId')
        vendeur_id = data.get('vendeurId')
        message = data.get('message')
        
        if not all([commande_id, vendeur_id, message]):
            return jsonify({'error': 'Données manquantes'}), 400
            
        sql = """
            INSERT INTO notifications (user_id, type, title, message, data, date_creation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        execute_query(sql, [
            vendeur_id, 
            'nouvelle_commande', 
            'Nouvelle commande reçue', 
            message, 
            f'{{"commandeId": {commande_id}}}',
            datetime.now()
        ], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@new_routes.route('/notifications/order-confirmation', methods=['POST'])
@jwt_required()
def send_order_confirmation():
    """Envoyer confirmation de commande"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        commande_id = data.get('commandeId')
        user_target_id = data.get('userId')
        details = data.get('details', {})
        
        if not all([commande_id, user_target_id]):
            return jsonify({'error': 'Données manquantes'}), 400
            
        sql = """
            INSERT INTO notifications (user_id, type, title, message, data, date_creation)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        execute_query(sql, [
            user_target_id, 
            'confirmation_commande', 
            'Commande confirmée', 
            f'Votre commande #{commande_id} a été confirmée', 
            str(details),
            datetime.now()
        ], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== FRAIS ====================

@new_routes.route('/frais/configuration', methods=['GET'])
def get_frais_configuration():
    """Configuration des frais"""
    try:
        config = {
            'fraisPortAfrique': 1000,
            'fraisPortAlibaba': 3000,
            'fraisTransaction': 2000
        }
        
        return jsonify(config), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
from app import db
from app.models import (
    Boutique, ProduitAfrique, BoutiqueView, BoutiqueVisit, Commande, DetailCommande,
    CommandeReview, Paiement, Notification, User, OrderShare, ProductView
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

        q = Boutique.query.outerjoin(ProduitAfrique).with_entities(
            Boutique, db.func.count(ProduitAfrique.id).label('nb_produits')
        ).group_by(Boutique.id)

        if query:
            q = q.filter(
                (Boutique.nom.ilike(f'%{query}%')) |
                (Boutique.description.ilike(f'%{query}%'))
            )
        if category:
            q = q.filter(Boutique.categorie == category)

        q = q.order_by(db.desc('nb_produits'))

        results = []
        for boutique, nb_prods in q.all():
            d = boutique.to_dict()
            d['nb_produits'] = nb_prods
            results.append(d)

        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@new_routes.route('/boutiques/filter', methods=['POST'])
def filter_boutiques():
    try:
        data = request.get_json()
        category = data.get('category')
        search = data.get('search', '')

        q = Boutique.query

        if category:
            q = q.filter(Boutique.categorie == category)
        if search:
            q = q.filter(
                (Boutique.nom.ilike(f'%{search}%')) |
                (Boutique.description.ilike(f'%{search}%'))
            )
        q = q.order_by(Boutique.nom.asc())

        boutiques = [b.to_dict() for b in q.all()]
        return jsonify(boutiques), 200

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
        produits = (
            db.session.query(ProduitAfrique)
            .filter(ProduitAfrique.boutique_id == boutique_id)
            .order_by(ProduitAfrique.date_creation.desc())
            .all()
        )
        res = [p.to_dict() for p in produits]
        return jsonify(res), 200

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

        # Vérifier permission : utilisateur vendeur lié à boutique du produit
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
            file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
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

        # Produits recommandés: produits achetés par d'autres utilisateurs mais pas par celui-ci
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

        referral_code = f"REF_{user_id}_{uuid.uuid4().hex[:8]}"

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404

        user.referral_code = referral_code
        user.date_maj = datetime.utcnow()
        db.session.commit()

        referral_link = f"https://votre-app.com/register?ref={referral_code}"
        return jsonify({'referralLink': referral_link}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


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

        paiement = Paiement(
            payment_id=payment_id,
            user_id=user_id,
            commande_id=commande_id,
            amount=amount,
            method=method,
            status='pending',
            date_creation=datetime.utcnow()
        )
        db.session.add(paiement)
        db.session.commit()

        payment_url = f"https://payment-gateway.com/pay/{payment_id}"

        return jsonify({'paymentId': payment_id, 'paymentUrl': payment_url}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@new_routes.route('/admin/validate-payment', methods=['POST'])
@jwt_required()
def validate_payment():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        user = User.query.get(user_id)
        if not user or not getattr(user, 'is_admin', False):
            return jsonify({'error': 'Permission refusée'}), 403

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
    """Partager une commande"""
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        commande_id = data.get('commandeId')
        platform = data.get('platform')
        message = data.get('message', '')
        
        if not all([commande_id, platform]):
            return jsonify({'error': 'Données manquantes'}), 400
            
        # Vérifier que la commande appartient à l'utilisateur
        sql_check = "SELECT id FROM commandes WHERE id = %s AND user_id = %s"
        commande_check = execute_query(sql_check, [commande_id, user_id], fetch_one=True)
        
        if not commande_check:
            return jsonify({'error': 'Commande non trouvée'}), 404
            
        share_url = f"https://votre-app.com/orders/{commande_id}/share"
        
        # Enregistrer le partage
        sql = """
            INSERT INTO order_shares (commande_id, user_id, platform, message, date_share)
            VALUES (%s, %s, %s, %s, %s)
        """
        
        execute_query(sql, [commande_id, user_id, platform, message, datetime.now()], fetch_all=False)
        
        return jsonify({'shareUrl': share_url}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ==================== PRODUITS ====================

@new_routes.route('/produits/view', methods=['POST'])
@jwt_required()
def add_product_view():
    """Enregistrer une vue de produit"""
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
        
        execute_query(sql, [produit_id, user_id, datetime.now(), request.remote_addr], fetch_all=False)
        
        # Mettre à jour le compteur de vues
        sql_update = "UPDATE produits SET nb_vues = nb_vues + 1 WHERE id = %s"
        execute_query(sql_update, [produit_id], fetch_all=False)
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

