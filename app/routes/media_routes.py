from flask import Blueprint, send_from_directory, jsonify, url_for, current_app
import os

media_routes = Blueprint('media_routes', __name__)

@media_routes.route('/static/uploads/<filename>')
def get_image(filename):
    return send_from_directory('static/uploads', filename)

@media_routes.route('/api/images', methods=['GET'])
def get_images():
    image_folder = os.path.join(current_app.root_path, 'static', 'images')
    images = []
    for filename in os.listdir(image_folder):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
            # Construire l'URL complète
            url = url_for('static', filename=f'images/{filename}', _external=True)
            images.append(url)
    return jsonify(images)
