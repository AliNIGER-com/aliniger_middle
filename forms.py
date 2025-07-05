from flask_wtf import FlaskForm
from wtforms import EmailField, PasswordField  # si tu ne les as pas encore
from wtforms import StringField, DecimalField, IntegerField, SubmitField
from wtforms import  FloatField, IntegerField, SubmitField, TextAreaField, SelectField, MultipleFileField
from wtforms.validators import DataRequired, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed, FileRequired, MultipleFileField
from app.models import Vendeur, Boutique

def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    self.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in Vendeur.query.filter_by(role='vendeur').all()]

# === PRODUIT AFRIQUE ===
class ProduitAfriqueForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    prix = DecimalField('Prix', validators=[DataRequired(), NumberRange(min=0)])
    images = MultipleFileField('Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images uniquement !')
    ])
    pays_origine = StringField('Pays d\'origine', validators=[Optional()])
    categorie = StringField('Catégorie', validators=[Optional()])
    vendeur_id = SelectField('Vendeur', coerce=int, validators=[DataRequired()])
    boutique_id = SelectField('Boutique', coerce=int, validators=[DataRequired()])
    stock = IntegerField('Stock', validators=[Optional(), NumberRange(min=0)])
    submit = SubmitField('Ajouter produit Afrique')

# === PRODUIT ALIBABA ===
class ProduitAlibabaForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    prix_estime = DecimalField('Prix estimé', validators=[DataRequired(), NumberRange(min=0)])
    images = MultipleFileField('Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement !')
    ])
    min_commande = IntegerField('Commande minimum', validators=[Optional(), NumberRange(min=1)])
    frais_livraison_estime = DecimalField('Frais livraison estimés', validators=[Optional(), NumberRange(min=0)])
    categorie = StringField('Catégorie', validators=[DataRequired()])
    vendeur = StringField('Nom du vendeur', validators=[Optional()])
    note = DecimalField('Note', validators=[Optional(), NumberRange(min=0, max=5)])
    couleur = StringField('Couleur', validators=[Optional()])
    submit = SubmitField('Ajouter produit Alibaba')


# === BOUTIQUE ===
class BoutiqueForm(FlaskForm):
    nom = StringField('Nom de la boutique', validators=[DataRequired()])
    description = StringField('Description')
    localisation = StringField('Localisation')
    note = FloatField('Note')

    icone = FileField('Icône (logo)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement')
    ])
    images = MultipleFileField('Images')
    videos = MultipleFileField('Vidéos')

    vendeur_id = SelectField('Vendeur', coerce=int, validators=[DataRequired()])
    pays = StringField('Pays')
    submit = SubmitField('Ajouter')

# === vendeur ===
class VendeurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    tel = StringField('Téléphone')
    mot_de_passe = PasswordField('Mot de passe', validators=[DataRequired()])
    adresse = StringField('Adresse')
    ville = StringField('Ville')
    pays = StringField('Pays')
    submit = SubmitField('Créer le vendeur')
