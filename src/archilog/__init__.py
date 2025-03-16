# src/archilog/__init__.py
from dataclasses import dataclass
import os

@dataclass
class Config:
    DATABASE_URL: str
    DEBUG: bool

# Charger les variables d'environnement
DATABASE_URL = os.getenv('ARCHILOG_DATABASE_URL')
DEBUG = os.getenv('ARCHILOG_DEBUG')

# Convertir DEBUG en booléen
DEBUG = DEBUG == 'True'  # Si ARCHILOG_DEBUG est 'True', alors DEBUG sera True, sinon False

# Configurer la classe
config = Config(
    DATABASE_URL=DATABASE_URL,
    DEBUG=DEBUG
)