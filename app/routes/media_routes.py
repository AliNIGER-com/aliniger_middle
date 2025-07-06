from flask import Blueprint, send_from_directory, abort
import os

media_routes = Blueprint('media_routes', __name__)

# Chemin vers le dossier uploads dans static
UPLOADS_FOLDER = os.path.join(os.getcwd(), 'static', 'uploads')

@media_routes.route('/uploads/<path:filename>')
def serve_uploaded_file(filename):
    try:
        return send_from_directory(UPLOADS_FOLDER, filename)
    except FileNotFoundError:
        abort(404, description="Fichier non trouvé")
