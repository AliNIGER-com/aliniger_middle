from flask import Blueprint, send_from_directory, abort
import os

media_routes = Blueprint('media_routes', __name__)

# Ce chemin doit correspondre à ton dossier "media" à la racine de ton projet
MEDIA_FOLDER = os.path.join(os.getcwd(), 'media')

@media_routes.route('/media/<path:filename>')
def serve_media_file(filename):
    try:
        return send_from_directory(MEDIA_FOLDER, filename)
    except FileNotFoundError:
        abort(404, description="Fichier non trouvé")
