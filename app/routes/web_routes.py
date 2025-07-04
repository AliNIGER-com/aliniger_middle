from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from werkzeug.utils import secure_filename
from app.models import db, ProduitAfrique, ProduitAlibaba, Boutique
from forms import ProduitAfriqueForm, ProduitAlibabaForm, BoutiqueForm, VendeurForm
import os
from sqlalchemy import func, extract
from app.models import Vendeur, Vente
from datetime import datetime, timedelta
from flask_login import login_user, login_required, logout_user, current_user
from app import db, login_manager
from werkzeug.security import check_password_hash
from sqlalchemy import desc


web_routes = Blueprint('web_routes', __name__, url_prefix='/admin')

UPLOAD_FOLDER_IMAGES = 'app/static/uploads/images'
UPLOAD_FOLDER_VIDEOS = 'app/static/uploads/videos'

# Assurez-vous que les dossiers existent
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_VIDEOS, exist_ok=True)

# Dashboard
@web_routes.route('/')
def dashboard():
    vendeur = Vendeur.query.first()  # Ou vendeur connecté
    return render_template('index.html', vendeur=vendeur)

from flask import render_template
from datetime import datetime, timedelta
from sqlalchemy import func, extract

@web_routes.route('/catalogue')
def statistiques():
    # Total vendeurs
    total_vendeurs = Vendeur.query.count()

    # Total boutiques
    total_boutiques = Boutique.query.count()

    # Ventes de la semaine (derniers 7 jours)
    une_semaine = datetime.utcnow() - timedelta(days=7)
    ventes_semaine = Vente.query.filter(Vente.date >= une_semaine).count()

    # Ventes du mois
    now = datetime.utcnow()
    debut_mois = datetime(now.year, now.month, 1)
    ventes_mois = Vente.query.filter(Vente.date >= debut_mois).count()

    # Boutique en hausse (ex: plus de 10 ventes cette semaine)
    boutiques_hausses = (
        db.session.query(Boutique)
        .join(Vente)
        .filter(Vente.date >= une_semaine)
        .group_by(Boutique.id)
        .having(func.count(Vente.id) > 10)
        .all()
    )

    # Boutique en chute (moins de 3 ventes cette semaine)
    boutiques_chute = (
        db.session.query(Boutique)
        .join(Vente)
        .filter(Vente.date >= une_semaine)
        .group_by(Boutique.id)
        .having(func.count(Vente.id) < 3)
        .all()
    )

    # Catégories les plus populaires (les plus vendues)
    categories_populaires = (
        db.session.query(ProduitAfrique.categorie, func.count(Vente.id).label('total'))
        .join(Vente, Vente.produit_id == ProduitAfrique.id)
        .group_by(ProduitAfrique.categorie)
        .order_by(func.count(Vente.id).desc())
        .limit(5)
        .all()
    )

    current_year = now.year
    current_month = now.month

    # Chiffre d'affaires du mois courant
    chiffre_affaires_mensuel = (
        db.session.query(func.sum(ProduitAfrique.prix * Vente.quantite))
        .select_from(Vente)
        .join(ProduitAfrique, ProduitAfrique.id == Vente.produit_id)
        .filter(Vente.date >= debut_mois)
        .scalar()
    ) or 0  # si None, on met 0

    # Calcul du mois précédent
    if current_month == 1:
        prev_month = 12
        prev_year = current_year - 1
    else:
        prev_month = current_month - 1
        prev_year = current_year

    # Chiffre d'affaires du mois précédent
    chiffre_affaires_mois_prec = (
        db.session.query(func.sum(ProduitAfrique.prix * Vente.quantite))
        .select_from(Vente)
        .join(ProduitAfrique, ProduitAfrique.id == Vente.produit_id)
        .filter(extract('year', Vente.date) == prev_year)
        .filter(extract('month', Vente.date) == prev_month)
        .scalar()
    ) or 0

    # Calcul du taux de croissance en pourcentage
    if chiffre_affaires_mois_prec == 0:
        taux_croissance = 100 if chiffre_affaires_mensuel > 0 else 0
    else:
        taux_croissance = round(
            ((chiffre_affaires_mensuel - chiffre_affaires_mois_prec) / chiffre_affaires_mois_prec) * 100,
            2
        )

    return render_template("statistiques.html",
        total_vendeurs=total_vendeurs,
        total_boutiques=total_boutiques,
        ventes_semaine=ventes_semaine,
        ventes_mois=ventes_mois,
        nb_hausses=len(boutiques_hausses),
        nb_chutes=len(boutiques_chute),
        categories_populaires=categories_populaires,
        chiffre_affaires_mensuel=round(chiffre_affaires_mensuel, 2),
        taux_croissance=taux_croissance
    )


# === visionner liste boutique ===
@web_routes.route('/voir-boutique/<int:vendeur_id>')
def voir_boutique(vendeur_id):
    vendeur = Vendeur.query.get_or_404(vendeur_id)
    boutiques = Boutique.query.all()
    produits = ProduitAlibaba.query.filter_by(vendeur=vendeur.nom).all()
    return render_template('voir_boutique.html', vendeur=vendeur, produits=produits, boutiques=boutiques)

# === Visionner la liste des produits Afrique avec vendeurs associés ===
@web_routes.route('/afrique')
def voir_afrique():
    produits_afrique = ProduitAfrique.query.all()
    vendeurs = Vendeur.query.all()  # Ajoute la liste des vendeurs

    return render_template(
        'produits_afrique.html',
        produits_afrique=produits_afrique,
        vendeurs=vendeurs  # Passe la liste à Jinja
    )


# === visionner liste boutique ===
@web_routes.route('/alibaba')
def voir_alibaba():
    produits_alibaba = ProduitAlibaba.query.all()

    return render_template(
        'produits_alibaba.html',
        produits_alibaba=produits_alibaba
    )

# === visionner liste boutique ===
@web_routes.route('/vendeur')
def voir_vendeur():
    vendeurs = Vendeur.query.all()

    return render_template(
        'vendeur.html',
        vendeurs=vendeurs
    )

# === 1. Ajouter Produit Afrique ===
@web_routes.route('/ajouter-produit-afrique', methods=['GET', 'POST'])
def ajouter_produit_afrique():
    form = ProduitAfriqueForm()
    form.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in Vendeur.query.all()]
    # Charger dynamiquement les vendeurs pour le SelectField
    boutique = Boutique.query.all()
    form.boutique_id.choices = [(v.id, f"{v.nom}") for v in boutique]
    if form.validate_on_submit():
        # Sauvegarde multiple d’images
        image_filenames = []
        for file in request.files.getlist('images'):
            if file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                file.save(path)
                image_filenames.append(filename)

        produit = ProduitAfrique(
            nom=form.nom.data,
            description=form.description.data,
            prix=form.prix.data,
            image=",".join(image_filenames),
            pays_origine=form.pays_origine.data,
            categorie=form.categorie.data,
            stock=form.stock.data,
            vendeur_id=form.vendeur_id.data,
            boutique_id=form.boutique_id.data
        )
        db.session.add(produit)
        db.session.commit()
        flash('Produit Afrique ajouté avec succès.', 'success')
        return redirect(url_for('web_routes.ajouter_produit_afrique'))

    return render_template('add_afrique.html', form=form)

# === 2. Ajouter Produit Alibaba ===
@web_routes.route('/ajouter-produit-alibaba', methods=['GET', 'POST'])
def ajouter_produit_alibaba():
    form = ProduitAlibabaForm()
    if form.validate_on_submit():
        image_filenames = []
        for file in request.files.getlist('images'):
            if file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                file.save(path)
                image_filenames.append(filename)

        produit = ProduitAlibaba(
    nom=form.nom.data,
    description=form.description.data,
    prix_estime=form.prix_estime.data,
    image=",".join(image_filenames),
    min_commande=form.min_commande.data,
    frais_livraison_estime=form.frais_livraison_estime.data,
    categorie=form.categorie.data,          # <-- Ajouté ici
    vendeur=form.vendeur.data,
    note=form.note.data,
    couleur=form.couleur.data
)

        db.session.add(produit)
        db.session.commit()
        flash('Produit Alibaba ajouté avec succès.', 'success')
        return redirect(url_for('web_routes.ajouter_produit_alibaba'))
    return render_template('add_alibaba.html', form=form)

# === 3. Ajouter une Boutique ===
@web_routes.route('/ajouter-boutique', methods=['GET', 'POST'])
def ajouter_boutique():
    form = BoutiqueForm()
    # Charger dynamiquement les vendeurs pour le SelectField
    vendeurs = Vendeur.query.all()
    form.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in vendeurs]
    if form.validate_on_submit():
        image_filenames = []
        video_filenames = []

        for file in request.files.getlist('images'):
            if file.filename:
                filename = secure_filename(file.filename)
                path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                file.save(path)
                image_filenames.append(filename)

        for video in request.files.getlist('videos'):
            if video.filename:
                filename = secure_filename(video.filename)
                path = os.path.join(UPLOAD_FOLDER_VIDEOS, filename)
                video.save(path)
                video_filenames.append(filename)

        boutique = Boutique(
            nom=form.nom.data,
            description=form.description.data,
            localisation=form.localisation.data,
            note=form.note.data,
            image=",".join(image_filenames),
            video=",".join(video_filenames),
            vendeur_id=form.vendeur_id.data,
            pays=form.pays.data
        )
        db.session.add(boutique)
        db.session.commit()
        flash('Boutique ajoutée avec succès.', 'success')
        return redirect(url_for('web_routes.ajouter_boutique'))
    return render_template('add_boutique.html', form=form)

@web_routes.route('/ajouter-vendeur', methods=['GET', 'POST'])
def ajouter_vendeur():
    form = VendeurForm()
    if form.validate_on_submit():
        vendeur = Vendeur(
            nom=form.nom.data,
            prenom=form.prenom.data,
            email=form.email.data,
            tel=form.tel.data,
            mot_de_passe=form.mot_de_passe.data,
            adresse=form.adresse.data,
            ville=form.ville.data,
            pays=form.pays.data
        )
        db.session.add(vendeur)
        db.session.commit()
        flash("Vendeur ajouté avec succès !", "success")
        return redirect(url_for('web_routes.ajouter_vendeur'))
    return render_template('add_vendeur.html', form=form)

@web_routes.route('/vendeur/login', methods=['GET', 'POST'])
def login_vendeur():
    if request.method == 'POST':
        tel = request.form['tel']
        mot_de_passe = request.form['mot_de_passe']
        vendeur = Vendeur.query.filter_by(tel=tel).first()
        if vendeur and check_password_hash(vendeur.mot_de_passe, mot_de_passe):
            login_user(vendeur)
            return redirect(url_for('dashboard_vendeur'))
        else:
            flash('Numéro ou mot de passe invalide.', 'danger')
    return render_template('login_vendeur.html')

@web_routes.route('/vendeur/dashboard')
@login_required
def dashboard_vendeur():
    if not current_user.is_authenticated:
        return redirect(url_for('web_routes.login_vendeur'))
    
    return render_template('dashboard_vendeur.html', vendeur=current_user)

@web_routes.route('/vendeur/logout')
@login_required
def logout_vendeur():
    logout_user()
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('web_routes.login_vendeur'))


@web_routes.route('/vendeur/promo', methods=['POST'])
@login_required
def lancer_promo():
    produit_id = request.form.get('produit_id')
    nouvelle_remise = request.form.get('remise')

    produit = ProduitAfrique.query.filter_by(id=produit_id, vendeur_id=current_user.id).first()

    if produit:
        try:
            nouvelle_remise = float(nouvelle_remise)
            if 0 <= nouvelle_remise <= 100:
                ancien_prix = produit.prix
                produit.prix = round(produit.prix * (1 - nouvelle_remise / 100), 2)
                db.session.commit()
                flash(f"✅ Promotion appliquée : {ancien_prix} FCFA → {produit.prix} FCFA", "success")
            else:
                flash("La remise doit être entre 0 et 100%.", "warning")
        except ValueError:
            flash("Erreur : Veuillez entrer un pourcentage valide.", "danger")
    else:
        flash("Produit non trouvé ou non autorisé.", "danger")

    return redirect(url_for('web_routes.dashboard_vendeur'))

@web_routes.route('/admin/boutique/modifier_inline/<int:id>', methods=['POST'])
def modifier_boutique_inline(id):
    boutique = Boutique.query.get_or_404(id)
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    champs_valides = ['nom', 'note', 'localisation', 'vendeur_id']

    if field not in champs_valides:
        return jsonify({'success': False, 'message': 'Champ invalide.'}), 400

    try:
        if field == 'note':
            value = float(value)
        elif field == 'vendeur_id':
            value = int(value)

        setattr(boutique, field, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@web_routes.route('/admin/boutique/supprimer/<int:id>', methods=['POST'])
def supprimer_boutique(id):
    boutique = Boutique.query.get_or_404(id)

    try:
        db.session.delete(boutique)
        db.session.commit()
        flash("🗑️ Boutique supprimée avec succès.", "success")
    except:
        db.session.rollback()
        flash("❌ Une erreur est survenue lors de la suppression.", "danger")

    return redirect(url_for('web_routes.voir_boutique'))

@web_routes.route('/admin/produit_afrique/modifier_inline/<int:id>', methods=['POST'])
def modifier_produit_afrique_inline(id):
    produit = ProduitAfrique.query.get_or_404(id)
    data = request.get_json()
    field = data.get('field')
    value = data.get('value')

    champs_valides = ['nom', 'prix', 'categorie', 'stock', 'vendeur_id']

    if field not in champs_valides:
        return jsonify({'success': False, 'message': 'Champ invalide.'}), 400

    try:
        if field == 'prix':
            value = float(value)
        elif field == 'stock':
            value = int(value)
        elif field == 'vendeur_id':
            value = int(value)

        setattr(produit, field, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@web_routes.route('/admin/produit_afrique/supprimer/<int:id>', methods=['POST'])
def supprimer_produit_afrique(id):
    produit = ProduitAfrique.query.get_or_404(id)

    try:
        db.session.delete(produit)
        db.session.commit()
        flash("🗑️ Produit supprimé avec succès.", "success")
    except:
        db.session.rollback()
        flash("❌ Une erreur est survenue lors de la suppression.", "danger")

    return redirect(url_for('web_routes.voir_afrique'))


@web_routes.route('/admin/produit_alibaba/modifier_inline/<int:id>', methods=['POST'])
def modifier_produit_alibaba_inline(id):
    produit = ProduitAlibaba.query.get_or_404(id)
    data = request.get_json()

    field = data.get('field')
    value = data.get('value')

    champs_valides = ['nom', 'prix_estime', 'categorie', 'couleur', 'min_commande']

    if field not in champs_valides:
        return jsonify({'success': False, 'message': 'Champ invalide.'}), 400

    try:
        # Casting si nécessaire, par exemple min_commande en int, prix_estime en float
        if field == 'min_commande':
            value = int(value)
        elif field == 'prix_estime':
            value = float(value)

        setattr(produit, field, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@web_routes.route('/admin/produit_alibaba/supprimer/<int:id>', methods=['POST'])
def supprimer_produit_alibaba(id):
    produit = ProduitAlibaba.query.get_or_404(id)

    try:
        db.session.delete(produit)
        db.session.commit()
        flash("🗑️ Produit Alibaba supprimé avec succès.", "success")
    except:
        db.session.rollback()
        flash("❌ Une erreur est survenue lors de la suppression.", "danger")

    return redirect(url_for('web_routes.voir_alibaba'))

from flask import request, jsonify

@web_routes.route('/admin/vendeur/modifier_inline/<int:id>', methods=['POST'])
def modifier_vendeur_inline(id):
    vendeur = Vendeur.query.get_or_404(id)
    data = request.get_json()

    field = data.get('field')
    value = data.get('value')

    # Liste des champs modifiables
    champs_valides = ['nom', 'prenom', 'email', 'tel', 'adresse', 'ville', 'pays']

    if field not in champs_valides:
        return jsonify({'success': False, 'message': 'Champ invalide.'}), 400

    try:
        setattr(vendeur, field, value)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


@web_routes.route('/admin/vendeur/supprimer/<int:id>', methods=['POST'])
def supprimer_vendeur(id):
    vendeur = Vendeur.query.get_or_404(id)

    try:
        db.session.delete(vendeur)
        db.session.commit()
        flash("🗑️ Vendeur supprimé avec succès.", "success")
    except:
        db.session.rollback()
        flash("❌ Une erreur est survenue lors de la suppression.", "danger")

    return redirect(url_for('web_routes.voir_vendeur'))


@web_routes.route('/vendeur/reset_mdp', methods=['POST'])
def demande_reset_mdp():
    email = request.form.get('email')
    # Vérifie si l'email existe, génère un token, envoie le lien par email
    flash("Un lien de réinitialisation a été envoyé à votre adresse email.", "success")
    return redirect(url_for('web_routes.login_vendeur'))

@web_routes.route('/produits_recents', methods=['GET'])
def produits_recents():
    # Récupère les 10 derniers produits de chaque source
    produits_afrique = ProduitAfrique.query.order_by(desc(ProduitAfrique.id)).limit(10).all()
    produits_alibaba = ProduitAlibaba.query.order_by(desc(ProduitAlibaba.id)).limit(10).all()

    resultats = []

    for p in produits_afrique:
        resultats.append({
            'id': p.id,
            'nom': p.nom,
            'description': p.description,
            'prix': p.prix,
            'images': p.image.split(',') if p.image else [],
            'categorie': p.categorie,
            'source': 'afrique',
            'origine': p.pays_origine,
            'boutique_id': p.boutique_id,
            'vendeur_id': p.vendeur_id,
        })

    for p in produits_alibaba:
        resultats.append({
            'id': p.id,
            'nom': p.nom,
            'description': p.description,
            'prix': p.prix_estime,
            'images': p.image.split(',') if p.image else [],
            'categorie': getattr(p, 'categorie', 'alibaba'),
            'source': 'alibaba',
            'origine': 'Chine',
            'vendeur': p.vendeur
        })

    # Trie tous les produits ensemble par ID décroissant
    resultats.sort(key=lambda x: x['id'], reverse=True)

    return jsonify(resultats[:10]), 200

from app.models import Commande
@web_routes.route('/admin/commandes', methods=['GET'])
def voir_commandes():
    # Requête avec jointure pour accéder à user (client) et ses attributs
    commandes = Commande.query.order_by(Commande.date_commande.desc()).all()
    return render_template('commandes_dashboard.html', commandes=commandes)

@web_routes.route('/admin/commande/<int:id>/statut', methods=['POST'])
def mettre_a_jour_statut_commande(id):
    commande = Commande.query.get_or_404(id)
    nouveau_statut = request.form.get('nouveau_statut')

    statuts_valides = ['Lancé', 'En cours de lancement', 'En préparation', 'Expédié', 'Livré']
    if nouveau_statut not in statuts_valides:
        flash("Statut invalide.", "danger")
        return redirect(url_for('web_routes.voir_commandes'))

    commande.statut = nouveau_statut
    db.session.commit()
    flash(f"Statut de la commande #{commande.id} mis à jour en '{nouveau_statut}'.", "success")
    return redirect(url_for('web_routes.voir_commandes'))

# Gestion de l'erreur 413 spécifique à ce blueprint
@web_routes.app_errorhandler(413)
def handle_file_too_large(error):
    return render_template('errors/413.html'), 413