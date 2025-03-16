from flask import Flask
from archilog.views.web_ui import web_ui

from archilog.models import init_db

def create_app():
    # Création de l'instance de l'application Flask
    app = Flask(__name__)
    # Désactiver CSRF en ne configurant pas SECRET_KEY
    app.config['WTF_CSRF_ENABLED'] = False  # Désactive la protection CSRF  
    # Initialisation de la base de données
    init_db()

    # Enregistrement des blueprints
    app.register_blueprint(web_ui)
   #app.register_blueprint(api)  implementation plus tard

    return app
