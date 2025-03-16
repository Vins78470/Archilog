from flask import Flask
from archilog.views.web_ui import web_ui
from archilog.views.error_handler import register_error_handlers
from archilog.models import init_db


def create_app():
    # Création de l'instance de l'application Flask
    app = Flask(__name__)
    # 🔹 Ajoute une clé secrète pour activer les sessions et flash()
   
    # 🔹 Enregistrer les handlers d'erreur
    register_error_handlers(app)  

    # Initialisation de la base de données
    init_db()

    # Enregistrement des blueprints
    app.register_blueprint(web_ui)

    return app
