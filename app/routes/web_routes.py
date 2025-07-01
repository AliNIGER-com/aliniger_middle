from flask import Blueprint, render_template, request, redirect, url_for, flash
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

web_routes = Blueprint('web_routes', __name__, url_prefix='/admin')

UPLOAD_FOLDER_IMAGES = 'app/static/uploads/images'
UPLOAD_FOLDER_VIDEOS = 'app/static/uploads/videos'

# Assurez-vous que les dossiers existent
os.makedirs(UPLOAD_FOLDER_IMAGES, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_VIDEOS, exist_ok=True)

# Dashboard
@web_routes.route('/')
def dashboard():
    return render_template('index.html')

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
@web_routes.route('/boutique')
def voir_boutique():
    boutiques = Boutique.query.all()

    return render_template(
        'boutique.html',
        boutiques=boutiques
    )

# === visionner liste boutique ===
@web_routes.route('/afrique')
def voir_afrique():
    produits_afrique = ProduitAfrique.query.all()

    return render_template(
        'produits_afrique.html',
        produits_afrique=produits_afrique
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
        email = request.form['email']
        mot_de_passe = request.form['mot_de_passe']
        vendeur = Vendeur.query.filter_by(email=email).first()
        if vendeur and check_password_hash(vendeur.mot_de_passe, mot_de_passe):
            login_user(vendeur)
            return redirect(url_for('dashboard_vendeur'))
        else:
            flash('Identifiants invalides', 'danger')
    return render_template('login_vendeur.html')

@web_routes.route('/vendeur/dashboard')
@login_required
def dashboard_vendeur():
    return render_template('dashboard_vendeur.html', vendeur=current_user)

@web_routes.route('/vendeur/logout')
@login_required
def logout_vendeur():
    logout_user()
    flash("Déconnexion réussie.", "success")
    return redirect(url_for('login_vendeur'))

@web_routes.route('/vendeur/promo', methods=['POST'])
@login_required
def lancer_promo():
    produit_id = request.form.get('produit_id')
    nouvelle_remise = request.form.get('remise')  # exemple : 20 pour -20%

    produit = ProduitAfrique.query.filter_by(id=produit_id, vendeur_id=current_user.id).first()

    if produit:
        try:
            nouvelle_remise = float(nouvelle_remise)
            # Appliquer la remise sur le prix actuel
            ancien_prix = produit.prix
            produit.prix = round(produit.prix * (1 - nouvelle_remise / 100), 2)
            db.session.commit()
            flash(f"✅ Promotion appliquée : {ancien_prix} → {produit.prix} FCFA", "success")
        except:
            flash("Erreur dans le format de la remise.", "danger")
    else:
        flash("Produit non trouvé ou non autorisé.", "danger")

    return redirect(url_for('dashboard_vendeur'))

@web_routes.route('/admin/boutique/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_boutique(id):
    boutique = Boutique.query.get_or_404(id)
    form = BoutiqueForm(obj=boutique)  # Pré-remplir le formulaire

    vendeurs = Vendeur.query.all()
    form.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in vendeurs]

    if form.validate_on_submit():
        # Mise à jour des champs texte
        boutique.nom = form.nom.data
        boutique.description = form.description.data
        boutique.localisation = form.localisation.data
        boutique.note = form.note.data
        boutique.vendeur_id = form.vendeur_id.data
        boutique.pays = form.pays.data

        # Mise à jour des images si nouvelles fournies
        images = request.files.getlist('images')
        if images and images[0].filename != '':
            image_filenames = []
            for image in images:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                image.save(image_path)
                image_filenames.append(filename)
            boutique.image = ",".join(image_filenames)

        # Mise à jour des vidéos si nouvelles fournies
        videos = request.files.getlist('videos')
        if videos and videos[0].filename != '':
            video_filenames = []
            for video in videos:
                filename = secure_filename(video.filename)
                video_path = os.path.join(UPLOAD_FOLDER_VIDEOS, filename)
                video.save(video_path)
                video_filenames.append(filename)
            boutique.video = ",".join(video_filenames)

        db.session.commit()
        flash("✅ Boutique mise à jour avec succès !", "success")
        return redirect(url_for('web_routes.voir_boutique'))

    return render_template('edit_boutique.html', form=form, boutique=boutique)


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

@web_routes.route('/admin/produit_afrique/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_produit_afrique(id):
    produit = ProduitAfrique.query.get_or_404(id)
    form = ProduitAfriqueForm(obj=produit)

    # Préparer les choix dynamiques
    vendeurs = Vendeur.query.all()
    form.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in vendeurs]
    boutiques = Boutique.query.all()
    form.boutique_id.choices = [(b.id, b.nom) for b in boutiques]

    if form.validate_on_submit():
        produit.nom = form.nom.data
        produit.description = form.description.data
        produit.prix = form.prix.data
        produit.categorie = form.categorie.data
        produit.stock = form.stock.data
        produit.vendeur_id = form.vendeur_id.data
        produit.boutique_id = form.boutique_id.data
        produit.pays_origine = form.pays_origine.data

        # Mise à jour des images
        images = request.files.getlist('images')
        if images and images[0].filename != '':
            image_filenames = []
            for image in images:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                image.save(image_path)
                image_filenames.append(filename)
            produit.image = ",".join(image_filenames)

        db.session.commit()
        flash("✅ Produit modifié avec succès !", "success")
        return redirect(url_for('web_routes.voir_afrique'))

    return render_template('edit_afrique.html', form=form, produit=produit)


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


@web_routes.route('/admin/produit_alibaba/modifier/<int:id>', methods=['GET', 'POST']) 
def modifier_produit_alibaba(id):
    produit = ProduitAlibaba.query.get_or_404(id)
    form = ProduitAlibabaForm(obj=produit)

    if form.validate_on_submit():
        produit.nom = form.nom.data
        produit.description = form.description.data
        produit.prix_estime = form.prix_estime.data
        produit.min_commande = form.min_commande.data
        produit.frais_livraison_estime = form.frais_livraison_estime.data
        produit.vendeur = form.vendeur.data
        produit.note = form.note.data
        produit.couleur = form.couleur.data

        # Mise à jour des images si nouveau fichier
        images = request.files.getlist('images')
        if images and images[0].filename != '':
            image_filenames = []
            for image in images:
                filename = secure_filename(image.filename)
                image_path = os.path.join(UPLOAD_FOLDER_IMAGES, filename)
                image.save(image_path)
                image_filenames.append(filename)
            produit.image = ",".join(image_filenames)

        db.session.commit()
        flash("✅ Produit Alibaba modifié avec succès !", "success")
        return redirect(url_for('web_routes.voir_alibaba'))

    return render_template('edit_alibaba.html', form=form, produit=produit)


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


@web_routes.route('/admin/vendeur/modifier/<int:id>', methods=['GET', 'POST'])
def modifier_vendeur(id):
    vendeur = Vendeur.query.get_or_404(id)
    form = VendeurForm(obj=vendeur)

    if form.validate_on_submit():
        vendeur.nom = form.nom.data
        vendeur.prenom = form.prenom.data
        vendeur.email = form.email.data
        vendeur.tel = form.tel.data
        vendeur.adresse = form.adresse.data
        vendeur.ville = form.ville.data
        vendeur.pays = form.pays.data

        # Optionnel : mise à jour mot de passe (uniquement si changé)
        if form.mot_de_passe.data:
            vendeur.mot_de_passe = form.mot_de_passe.data  # à hasher si non déjà fait dans le model

        db.session.commit()
        flash("✅ Vendeur modifié avec succès !", "success")
        return redirect(url_for('web_routes.voir_vendeur'))

    return render_template('edit_vendeur.html', form=form, vendeur=vendeur)


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