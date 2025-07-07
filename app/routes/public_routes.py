# app/routes/public_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Commande
from forms import VendeurForm
from app import db

public_routes = Blueprint('public_routes', __name__)  # pas de préfixe

@public_routes.route('/inscription-vendeur', methods=['GET', 'POST'])
def inscription_vendeur():
    form = VendeurForm()
    if form.validate_on_submit():
        from app.models import Vendeur  # éviter import circulaire
        nouveau_vendeur = Vendeur(
            nom=form.nom.data,
            prenom=form.prenom.data,
            email=form.email.data,
            tel=form.tel.data,
            mot_de_passe=form.mot_de_passe.data,
            adresse=form.adresse.data,
            ville=form.ville.data,
            pays=form.pays.data
        )
        db.session.add(nouveau_vendeur)
        db.session.commit()
        flash('Inscription réussie. Vous serez contacté bientôt.', 'success')
        return redirect(url_for('public_routes.inscription_vendeur'))

    return render_template('inscription_vendeur.html', form=form)

@public_routes.route('/tracking/<code_suivi>')
def suivi_commande(code_suivi):
    commande = Commande.query.filter_by(code_suivi=code_suivi).first()

    if not commande:
        flash("❌ Code de suivi invalide ou commande introuvable.", "danger")
        return redirect(url_for('public_routes.inscription_vendeur'))  # ou page d’accueil

    return render_template('commande_tracking.html', commande=commande)
