import os
import logging
from dataclasses import dataclass

# Configurer le logging
logging.basicConfig(
    level=logging.DEBUG,  # Niveau de log global, ici on garde DEBUG pour enregistrer toutes les informations
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),  # Afficher les logs dans la console
        logging.FileHandler("app_config.log")  # Enregistrer les logs dans un fichier 'app_config.log'
    ]
)

# Créer un logger spécifique pour la console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # N'afficher que les logs INFO et plus dans la console

# Créer un formatter pour les logs
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
console_handler.setFormatter(formatter)

# Ajouter le handler de la console au logger
logging.getLogger().addHandler(console_handler)

@dataclass
class Config:
    DATABASE_URL: str
    DEBUG: bool

# Charger les variables d'environnement
DATABASE_URL = os.getenv('ARCHILOG_DATABASE_URL')
DEBUG = os.getenv('ARCHILOG_DEBUG')

# Log des variables d'environnement chargées
logging.debug(f"Chargement de la configuration - DATABASE_URL: {DATABASE_URL}, DEBUG: {DEBUG}")

# Convertir DEBUG en booléen
DEBUG = DEBUG == 'True'  # Si ARCHILOG_DEBUG est 'True', alors DEBUG sera True, sinon False

# Log de la conversion du DEBUG
logging.debug(f"Valeur de DEBUG après conversion : {DEBUG}")

# Configurer la classe
config = Config(
    DATABASE_URL=DATABASE_URL,
    DEBUG=DEBUG
)

# Log de la configuration finale
logging.info(f"Configuration chargée : {config}")

# Optionnel : Log de la base de données si elle est vide
if not DATABASE_URL:
    logging.warning("La variable d'environnement DATABASE_URL est vide ou manquante.")
