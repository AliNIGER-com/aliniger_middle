from flask_wtf import FlaskForm
from wtforms import (
    StringField, DecimalField, IntegerField, FloatField, SubmitField,
    SelectField, PasswordField, TextAreaField, EmailField
)
from wtforms.validators import DataRequired, Optional, NumberRange
from flask_wtf.file import FileField, FileAllowed, MultipleFileField
from app.models import Vendeur, Boutique

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
    delais_livraison = StringField('Délai de livraison', validators=[Optional()])
    Frais = StringField('Frais de livraison', validators=[Optional()]) 
    submit = SubmitField('Ajouter produit Afrique')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in Vendeur.query.all()]
        self.boutique_id.choices = [(b.id, b.nom) for b in Boutique.query.all()]



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
    delais_livraison = StringField('Délai de livraison', validators=[Optional()])  # Ajouté ici
    submit = SubmitField('Ajouter produit Alibaba')

class BoutiqueForm(FlaskForm):
    nom = StringField('Nom de la boutique', validators=[DataRequired()])
    description = StringField('Description', validators=[Optional()])
    localisation = StringField('Localisation', validators=[Optional()])
    note = FloatField('Note', validators=[Optional()])
    
    icone = FileField('Icône (logo)', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement')
    ])
    images = MultipleFileField('Images', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Images uniquement')
    ])
    videos = MultipleFileField('Vidéos', validators=[
        FileAllowed(['mp4', 'avi', 'mov'], 'Vidéos uniquement')
    ])
    
    vendeur_id = SelectField('Vendeur', coerce=int, validators=[DataRequired()])
    pays = StringField('Pays', validators=[Optional()])
    submit = SubmitField('Ajouter Boutique')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vendeur_id.choices = [(v.id, f"{v.nom} {v.prenom}") for v in Vendeur.query.all()]


# === VENDEUR ===
class VendeurForm(FlaskForm):
    nom = StringField('Nom', validators=[DataRequired()])
    prenom = StringField('Prénom', validators=[DataRequired()])
    email = EmailField('Email', validators=[DataRequired()])
    tel = StringField('Téléphone', validators=[Optional()])
    mot_de_passe = PasswordField('Mot de passe', validators=[DataRequired()])
    adresse = StringField('Adresse', validators=[Optional()])
    ville = StringField('Ville', validators=[Optional()])
    pays = StringField('Pays', validators=[Optional()])
    submit = SubmitField('Créer le vendeur')

class CommandeForm(FlaskForm):
    nom_client = StringField('Nom du client', validators=[DataRequired()])
    tel_client = StringField('Téléphone du client', validators=[DataRequired()])
    adresse = StringField('Adresse de livraison', validators=[DataRequired()])
    type_commande = SelectField('Type de commande', choices=[
        ('alibaba', 'Commande Alibaba'),
        ('afrique', 'Produit Afrique')
    ], validators=[DataRequired()])
    code_suivi = StringField('Code de suivi (auto)', render_kw={'readonly': True})
    submit = SubmitField('Créer la commande')
