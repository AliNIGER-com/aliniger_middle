from flask import Blueprint, jsonify, request
from ..models import Notification
from .. import db

notification_routes = Blueprint('notification_routes', __name__)

@notification_routes.route('/api/notifications/<int:user_id>', methods=['GET'])
def get_user_notifications(user_id):
    notifications = Notification.query.filter_by(user_id=user_id).order_by(Notification.date.desc()).all()

    data = []
    for notif in notifications:
        data.append({
            "id": notif.id,
            "titre": notif.titre,
            "message": notif.message,
            "lu": notif.lu,
            "date": notif.date.strftime('%Y-%m-%d %H:%M:%S')
        })

    return jsonify(data)

@notification_routes.route('/api/notifications/mark_read/<int:notification_id>', methods=['POST'])
def mark_notification_as_read(notification_id):
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification non trouvée'}), 404

    notif.lu = True
    db.session.commit()
    return jsonify({'message': 'Notification marquée comme lue'})

@notification_routes.route('/api/notifications/unread_count/<int:user_id>', methods=['GET'])
def count_unread_notifications(user_id):
    count = Notification.query.filter_by(user_id=user_id, lu=False).count()
    return jsonify({'unread_count': count})
