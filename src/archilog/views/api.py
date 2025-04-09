import os
import uuid
import io
import logging
from flask import (
    Flask, Blueprint, render_template, request, send_file,
    redirect, url_for, flash, jsonify
)
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import CSRFProtect
from spectree import SpecTree, Response, SecurityScheme
from pydantic import BaseModel, ValidationError
from archilog.models import (
    create_entry, delete_entry, update_entry, get_entry,
   
)
from archilog.services import export_to_csv, import_from_csv

# --- Blueprints ---
api = Blueprint('api', __name__, url_prefix='/api')

# --- API Routes ---
class UserData(BaseModel):
    id: uuid.UUID
    name: str
    amount: float
    category: str | None

spec = SpecTree("flask", security_schemes=[SecurityScheme(name="bearer_token", data={"type": "http", "scheme": "bearer"})], security=[{"bearer_token": []}])

# Route pour créer un utilisateur
@api.route("/users", methods=["POST"])
@spec.validate(json=UserData, resp=Response(HTTP_201=UserData), tags=["api"])
def create_user():
    try:
        user_data = UserData(**request.json)
        user_id = create_entry(user_data.name, user_data.amount, user_data.category)
        return jsonify({"message": "Utilisateur créé avec succès", "user_id": str(user_id)}), 201
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route pour récupérer tous les utilisateurs
@api.route("/users", methods=["GET"])
@spec.validate(tags=["api"])
def get_users():
    try:
        users_list = get_entry()
        return jsonify([user.to_dict() for user in users_list]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route pour récupérer un utilisateur spécifique
@api.route("/users/<user_id>", methods=["GET"])
@spec.validate(tags=["api"])
def get_user(user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
        user = get_entry(user_uuid)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        return jsonify(user.to_dict()), 200
    except ValueError:
        return jsonify({"error": "UUID invalide"}), 400

# Route pour mettre à jour un utilisateur
@api.route("/users/<user_id>", methods=["PUT"])
@spec.validate(json=UserData, resp=Response(HTTP_200=UserData), tags=["api"])
def update_user(user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
        user = get_entry(user_uuid)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        update_data = UserData(**request.json)
        update_entry(user_uuid, update_data.name, update_data.amount, update_data.category)
        return jsonify({"message": "Utilisateur mis à jour", "user": update_data.dict()}), 200
    except ValueError:
        return jsonify({"error": "UUID invalide"}), 400
    except ValidationError as e:
        return jsonify({"error": e.errors()}), 400

# Route pour supprimer un utilisateur
@api.route("/users/<user_id>", methods=["DELETE"])
@spec.validate(tags=["api"])
def delete_user(user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
        success = delete_entry(user_uuid)
        if not success:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        return jsonify({"message": "Utilisateur supprimé"}), 200
    except ValueError:
        return jsonify({"error": "UUID invalide"}), 400


# --- Routes pour Exporter et Importer des CSV --- #

# Route pour exporter un fichier CSV
@api.route("/export_csv", methods=["GET"])
@spec.validate(tags=["csv"])
def export_csv_api():
    try:
        output = export_to_csv()

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=entries.csv"
            }
        )
    except Exception as e:
        return jsonify({"error": "Erreur lors de l'export"}), 500

from spectree.models import BaseFile

# Modèle de validation pour l'importation de fichier CSV
class CSVFileUpload(BaseModel):
    file: BaseFile  # Remplace BaseFile() par str car c'est plus adapté pour l'upload de fichiers

# Route pour importer un fichier CSV
@api.route("/import_csv", methods=["POST"])
@spec.validate(form=CSVFileUpload, tags=["csv"])
def import_csv_api():
    try:
        # Récupération du fichier via request.files
        file = request.files.get("file")

        if not file:
            return jsonify({"error": "Fichier manquant"}), 400

        # Traitement du fichier CSV
        import_from_csv(file.stream)
        return jsonify({"message": "Import réussi"}), 200
    except Exception as e:
        logging.exception("Erreur lors de l'import CSV")
        return jsonify({"error": "Erreur lors de l'import"}), 500
