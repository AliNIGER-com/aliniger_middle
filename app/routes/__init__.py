from .auth_routes import auth_routes
from .user_routes import user_routes
from .boutique_routes import boutique_routes
from .produit_routes import produit_routes
from .media_routes import media_routes
from .commande_routes import commande_routes
from .web_routes import web_routes  # Nouveau
from .new_routes import new_routes

def register_routes(app):
    app.register_blueprint(auth_routes)
    app.register_blueprint(user_routes)
    app.register_blueprint(boutique_routes)
    app.register_blueprint(produit_routes)
    app.register_blueprint(media_routes)
    app.register_blueprint(commande_routes)
    app.register_blueprint(web_routes)  # Enregistrement du nouveau
    app.register_blueprint(new_routes, url_prefix='/api')
