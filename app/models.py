from app import db
from sqlalchemy import Enum
import enum
from datetime import datetime

# --- Enums ---
class TypeCommandeEnum(enum.Enum):
    afrique = "afrique"
    alibaba = "alibaba"

class StatutCommandeEnum(enum.Enum):
    en_cours = "en_cours"
    cloturee = "cloturee"

class TypeProduitEnum(enum.Enum):
    afrique = "afrique"
    alibaba = "alibaba"

# --- Modèles de base ---

class UserRoleEnum(enum.Enum):
    client = "client"
    vendeur = "vendeur"
    admin = "admin"

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tel = db.Column(db.String(20))
    mot_de_passe = db.Column(db.Text, nullable=False)
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    pays = db.Column(db.String(100))
    role = db.Column(Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.client)

    commandes = db.relationship('Commande', backref='user', lazy=True)

# --- Nouveau modèle Vendeur ---
class Vendeur(db.Model):
    __tablename__ = 'vendeurs'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    tel = db.Column(db.String(20))
    mot_de_passe = db.Column(db.Text, nullable=False)
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    pays = db.Column(db.String(100))

    boutiques = db.relationship('Boutique', backref='vendeur', lazy=True)
    produits_afrique = db.relationship('ProduitAfrique', back_populates='vendeur')

# --- Boutique ---
class Boutique(db.Model):
    __tablename__ = 'boutiques'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    localisation = db.Column(db.String(255))
    note = db.Column(db.Float)
    image = db.Column(db.Text)
    video = db.Column(db.Text)
    pays = db.Column(db.String(100))

    vendeur_id = db.Column(db.Integer, db.ForeignKey('vendeurs.id'), nullable=False)
    produits_afrique = db.relationship('ProduitAfrique', backref='boutique', lazy=True)

# --- Produits Afrique ---
class ProduitAfrique(db.Model):
    __tablename__ = 'produits_afrique'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255))
    description = db.Column(db.Text)
    prix = db.Column(db.Float)
    image = db.Column(db.Text)
    pays_origine = db.Column(db.String(50))
    categorie = db.Column(db.String(100))
    stock = db.Column(db.Integer)

    vendeur_id = db.Column(db.Integer, db.ForeignKey('vendeurs.id'))
    boutique_id = db.Column(db.Integer, db.ForeignKey('boutiques.id'))

    # Relations
    vendeur = db.relationship('Vendeur', back_populates='produits_afrique')

# --- Produits Alibaba ---
class ProduitAlibaba(db.Model):
    __tablename__ = 'produits_alibaba'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(255))
    description = db.Column(db.Text)
    prix_estime = db.Column(db.Float)
    image = db.Column(db.Text)
    min_commande = db.Column(db.Integer)
    frais_livraison_estime = db.Column(db.Float)
    categorie = db.Column(db.String(100))
    vendeur = db.Column(db.String(100))
    note = db.Column(db.Float)
    couleur = db.Column(db.String(50))

# --- Commandes ---
class Commande(db.Model):
    __tablename__ = 'commandes'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    type_commande = db.Column(Enum(TypeCommandeEnum), nullable=False)
    date_commande = db.Column(db.DateTime)
    statut = db.Column(db.String(50))

    details = db.relationship('DetailCommande', backref='commande', lazy=True)
    tracking = db.relationship('Tracking', backref='commande', lazy=True, uselist=False)

class DetailCommande(db.Model):
    __tablename__ = 'details_commande'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    produit_id = db.Column(db.Integer)
    type_produit = db.Column(Enum(TypeProduitEnum), nullable=False)
    quantite = db.Column(db.Integer)
    prix_total = db.Column(db.Float)

class CommandeGroupee(db.Model):
    __tablename__ = 'commandes_groupees'
    id = db.Column(db.Integer, primary_key=True)
    produit_alibaba_id = db.Column(db.Integer, db.ForeignKey('produits_alibaba.id'))
    statut = db.Column(Enum(StatutCommandeEnum))
    nb_utilisateurs = db.Column(db.Integer)
    deadline = db.Column(db.DateTime)
    frais_partage_total = db.Column(db.Float)

class Tracking(db.Model):
    __tablename__ = 'tracking'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'))
    etat = db.Column(db.String(100))
    date_maj = db.Column(db.DateTime)

class Vente(db.Model):
    __tablename__ = 'ventes'

    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits_afrique.id'), nullable=False)
    vendeur_id = db.Column(db.Integer, db.ForeignKey('vendeurs.id'), nullable=False)
    boutique_id = db.Column(db.Integer, db.ForeignKey('boutiques.id'), nullable=True)

    quantite = db.Column(db.Integer, nullable=False, default=1)
    montant_total = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations
    produit = db.relationship("ProduitAfrique", backref="ventes", lazy=True)
    vendeur = db.relationship("Vendeur", backref="ventes", lazy=True)
    boutique = db.relationship("Boutique", backref="ventes", lazy=True)

    def __repr__(self):
        return f"<Vente {self.id} - Produit {self.produit_id} - Vendeur {self.vendeur_id}>"

# --- Suivi des vues de boutique ---
class BoutiqueView(db.Model):
    __tablename__ = 'boutique_views'
    id = db.Column(db.Integer, primary_key=True)
    boutique_id = db.Column(db.Integer, db.ForeignKey('boutiques.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

# --- Suivi des visites de boutique ---
class BoutiqueVisit(db.Model):
    __tablename__ = 'boutique_visits'
    id = db.Column(db.Integer, primary_key=True)
    boutique_id = db.Column(db.Integer, db.ForeignKey('boutiques.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(100))

# --- Avis sur commande ---
class CommandeReview(db.Model):
    __tablename__ = 'commande_reviews'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    note = db.Column(db.Integer, nullable=False)
    commentaire = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Notifications ---
class Notification(db.Model):
    __tablename__ = 'notifications'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    titre = db.Column(db.String(255))
    message = db.Column(db.Text)
    lu = db.Column(db.Boolean, default=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Paiements ---
class Paiement(db.Model):
    __tablename__ = 'paiements'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    methode = db.Column(db.String(50))  # ex: Airtel, Moov, carte...
    statut = db.Column(db.String(50), default='en_attente')  # ou validé, échoué
    date = db.Column(db.DateTime, default=datetime.utcnow)
    validated_by = db.Column(db.String(100))  # email ou ID admin

# --- Liens de parrainage ---
class ReferralLink(db.Model):
    __tablename__ = 'referral_links'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(100), unique=True, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    nb_utilisations = db.Column(db.Integer, default=0)

# --- Partages de commande ---
class OrderShare(db.Model):
    __tablename__ = 'order_shares'
    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey('commandes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    plateforme = db.Column(db.String(50))  # ex: WhatsApp, Facebook
    date = db.Column(db.DateTime, default=datetime.utcnow)

# --- Vues de produits ---
class ProductView(db.Model):
    __tablename__ = 'product_views'
    id = db.Column(db.Integer, primary_key=True)
    produit_id = db.Column(db.Integer, db.ForeignKey('produits_afrique.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(100))
