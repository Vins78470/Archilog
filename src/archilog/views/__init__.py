from flask import Flask
from archilog.views.web_ui import web_ui
from archilog.views.error_handler import register_error_handlers
from archilog.models import init_db
from archilog.__init__ import config  # Assure-toi d'importer la bonne config
from archilog.cli import cli  # 🔹 Ajout de l'import du CLI

def create_app():
    # Création de l'instance de l'application Flask
    app = Flask(__name__)
    app.config['SECRET_KEY'] = config.SECRET_KEY 

    # 🔹 Enregistrer les handlers d'erreur
    register_error_handlers(app)  
    
    # Initialisation de la base de données
    init_db()

    # Enregistrement des blueprints
    app.register_blueprint(web_ui)

    return app
