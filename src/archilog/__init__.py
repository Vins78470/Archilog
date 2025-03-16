import os
import logging
from dataclasses import dataclass

# Configurer le logging
logging.basicConfig(
    level=logging.INFO,  # On affiche au minimum les messages INFO
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("app_config.log"),  # Enregistre dans un fichier
        logging.StreamHandler()  # Affiche dans la console
    ]
)

@dataclass
class Config:
    DATABASE_URL: str = os.getenv('ARCHILOG_DATABASE_URL', 'sqlite:///default.db')
    DEBUG: bool = os.getenv('ARCHILOG_DEBUG', 'False').lower() in ('true', '1', 'yes')
    SECRET_KEY: str = os.getenv('ARCHILOG_SECRET_KEY', 'ma_super_cle_secrete')  # Ajout de la clé secrète


# Instancier la configuration
config = Config()

# Log de la configuration
logging.info(f"Configuration chargée : {config}")

# Vérifier la présence de DATABASE_URL et forcer une erreur pour test
if not config.DATABASE_URL or config.DATABASE_URL == 'sqlite:///default.db':
    logging.error("DATABASE_URL est manquant ou par défaut ! Vérifiez vos variables d'environnement.")


