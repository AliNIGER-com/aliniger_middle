from flask import Blueprint, send_from_directory
import os

media_routes = Blueprint('media_routes', __name__)

@media_routes.route('/media/<filename>')
def serve_uploaded_image(filename):
    path = os.path.join('static', 'uploads', 'images')
    return send_from_directory(path, filename)
