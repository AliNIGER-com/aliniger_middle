from flask import Blueprint, request, jsonify
from app import db
from models import Panier, PanierItem, TypeProduitEnum, ProduitAfrique, ProduitAlibaba, User
from datetime import datetime

wnew_routes = Blueprint('wnew_routes', __name__)

# 🔄 Ajouter un produit au panier
@wnew_routes.route('/panier/ajouter', methods=['POST'])
def ajouter_au_panier():
    data = request.get_json()
    user_id = data.get('user_id')
    produit_id = data.get('produit_id')
    type_produit = data.get('type_produit')
    quantite = data.get('quantite', 1)

    if not all([user_id, produit_id, type_produit]):
        return jsonify({"error": "Champs manquants"}), 400

    # Vérifier le type et récupérer le prix
    if type_produit == 'afrique':
        produit = ProduitAfrique.query.get(produit_id)
        if not produit:
            return jsonify({"error": "Produit Afrique introuvable"}), 404
        prix = produit.prix
    elif type_produit == 'alibaba':
        produit = ProduitAlibaba.query.get(produit_id)
        if not produit:
            return jsonify({"error": "Produit Alibaba introuvable"}), 404
        prix = produit.prix_estime
    else:
        return jsonify({"error": "Type de produit invalide"}), 400

    # Créer ou récupérer le panier
    panier = Panier.query.filter_by(user_id=user_id).first()
    if not panier:
        panier = Panier(user_id=user_id)
        db.session.add(panier)
        db.session.commit()

    # Vérifier si le produit est déjà dans le panier
    item = PanierItem.query.filter_by(panier_id=panier.id, produit_id=produit_id, type_produit=TypeProduitEnum(type_produit)).first()
    if item:
        item.quantite += quantite
    else:
        item = PanierItem(
            panier_id=panier.id,
            produit_id=produit_id,
            type_produit=TypeProduitEnum(type_produit),
            quantite=quantite,
            prix_unitaire=prix
        )
        db.session.add(item)

    db.session.commit()
    return jsonify({"message": "Produit ajouté au panier"}), 201

# 📦 Voir le panier d’un utilisateur
@wnew_routes.route('/panier/<int:user_id>', methods=['GET'])
def voir_panier(user_id):
    panier = Panier.query.filter_by(user_id=user_id).first()
    if not panier:
        return jsonify({"panier": [], "total": 0.0}), 200

    items_data = []
    total = 0.0

    for item in panier.items:
        produit_info = None
        if item.type_produit == TypeProduitEnum.afrique:
            produit = ProduitAfrique.query.get(item.produit_id)
        elif item.type_produit == TypeProduitEnum.alibaba:
            produit = ProduitAlibaba.query.get(item.produit_id)
        else:
            produit = None

        if produit:
            produit_info = {
                "id": produit.id,
                "nom": produit.nom,
                "image": produit.image,
                "categorie": getattr(produit, "categorie", ""),
                "type_produit": item.type_produit.value,
                "prix_unitaire": item.prix_unitaire,
                "quantite": item.quantite,
                "prix_total": item.quantite * item.prix_unitaire
            }
            total += produit_info["prix_total"]

        if produit_info:
            items_data.append(produit_info)

    return jsonify({"panier": items_data, "total": total}), 200

# ✏️ Modifier la quantité
@wnew_routes.route('/panier/modifier', methods=['PUT'])
def modifier_quantite_panier():
    data = request.get_json()
    user_id = data.get('user_id')
    produit_id = data.get('produit_id')
    type_produit = data.get('type_produit')
    quantite = data.get('quantite')

    panier = Panier.query.filter_by(user_id=user_id).first()
    if not panier:
        return jsonify({"error": "Panier introuvable"}), 404

    item = PanierItem.query.filter_by(panier_id=panier.id, produit_id=produit_id, type_produit=TypeProduitEnum(type_produit)).first()
    if not item:
        return jsonify({"error": "Produit non trouvé dans le panier"}), 404

    item.quantite = quantite
    db.session.commit()
    return jsonify({"message": "Quantité mise à jour"}), 200

# 🗑️ Supprimer un article
@wnew_routes.route('/panier/supprimer', methods=['DELETE'])
def supprimer_article_panier():
    data = request.get_json()
    user_id = data.get('user_id')
    produit_id = data.get('produit_id')
    type_produit = data.get('type_produit')

    panier = Panier.query.filter_by(user_id=user_id).first()
    if not panier:
        return jsonify({"error": "Panier introuvable"}), 404

    item = PanierItem.query.filter_by(panier_id=panier.id, produit_id=produit_id, type_produit=TypeProduitEnum(type_produit)).first()
    if not item:
        return jsonify({"error": "Produit non trouvé dans le panier"}), 404

    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Produit supprimé du panier"}), 200

# ❌ Vider le panier
@wnew_routes.route('/panier/vider/<int:user_id>', methods=['DELETE'])
def vider_panier(user_id):
    panier = Panier.query.filter_by(user_id=user_id).first()
    if not panier:
        return jsonify({"message": "Panier déjà vide"}), 200

    PanierItem.query.filter_by(panier_id=panier.id).delete()
    db.session.commit()
    return jsonify({"message": "Panier vidé avec succès"}), 200
