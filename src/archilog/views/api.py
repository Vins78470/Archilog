import os
import uuid
import io
import logging
from flask import (
    Blueprint, request,
    jsonify, abort
)
from flask_httpauth import HTTPTokenAuth
from functools import wraps

from spectree import SpecTree, Response, SecurityScheme
from pydantic import BaseModel, ValidationError
from archilog.models import (
    create_entry, delete_entry, update_entry, get_entry,get_all_entries
)
from archilog.services import export_to_csv, import_from_csv

from spectree.models import BaseFile

# --- Blueprints ---
api = Blueprint('api', __name__, url_prefix='/api')

# --- Auth Setup ---
token_auth = HTTPTokenAuth(scheme='Bearer')

# Dictionnaire de tokens : token -> rôle
valid_tokens = {
    "admin_token": "admin",
    "user_token": "user"
}

@token_auth.verify_token
def verify_token(token):
    return valid_tokens.get(token)

# Décorateur pour vérifier les rôles
def role_required(role):
    def wrapper(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            current_role = token_auth.current_user()
            logging.info(f"Rôle actuel : {current_role}, rôle requis : {role}")  # Log ajouté
            if current_role != role:
                logging.error(f"Accès interdit, rôle requis : {role}, rôle actuel : {current_role}")
                abort(403, description=f"Accès interdit, rôle requis : {role}")
            return func(*args, **kwargs)
        return decorated
    return wrapper


# --- Swagger / Spectree ---
spec = SpecTree(
    "flask",
    security_schemes=[SecurityScheme(name="bearer_token", data={"type": "http", "scheme": "bearer"})],
    security=[{"bearer_token": []}]
)

# --- Modèles ---
class UserData(BaseModel):
    id: uuid.UUID
    name: str
    amount: float
    category: str | None

class CSVFileUpload(BaseModel):
    file: BaseFile  # pour validation spectree

# --- Routes API Utilisateurs ---

@api.route("/users", methods=["POST"])
@spec.validate(json=UserData, tags=["api"])  # Validation du JSON via Pydantic
@token_auth.login_required  # Vérification que l'utilisateur est authentifié
@role_required("admin")  # Vérification que l'utilisateur est un admin
def create_user():
    try:
        user_data = UserData(**request.json)  # Valide et crée un objet UserData
        user_id = create_entry(user_data.name, user_data.amount, user_data.category)  # Appel à la fonction de création
        return jsonify({"message": "Utilisateur créé avec succès", "user_id": str(user_id)}), 201
    except ValidationError as e:
        # Si la validation échoue, on retourne une erreur avec les détails
        return jsonify({"error": "Données invalides", "details": e.errors()}), 422
    except Exception as e:
        # Gestion des erreurs générales
        return jsonify({"error": "Erreur interne", "message": str(e)}), 500


# Cette route est accessible aux admin et aux users (lecture uniquement)
@api.route("/users", methods=["GET"])
@spec.validate(tags=["api"])
@token_auth.login_required
@role_required("admin")
def get_users():
    try:
        users_list = get_all_entries()
        return jsonify([user.to_dict() for user in users_list]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Cette route est accessible aux admin et aux users (lecture uniquement)
@api.route("/users/<user_id>", methods=["GET"])
@spec.validate(tags=["api"])
@token_auth.login_required
@role_required("admin")
def get_user(user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
        user = get_entry(user_uuid)
        if not user:
            return jsonify({"error": "Utilisateur non trouvé"}), 404
        return jsonify(user.to_dict()), 200
    except ValueError:
        return jsonify({"error": "UUID invalide"}), 400

# Cette route est réservée à l'admin
@api.route("/users/<user_id>", methods=["PUT"])
@spec.validate(json=UserData, resp=Response(HTTP_200=UserData), tags=["api"])
@token_auth.login_required
@role_required("admin")
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

# Cette route est réservée à l'admin
@api.route("/users/<user_id>", methods=["DELETE"])
@spec.validate(tags=["api"])
@token_auth.login_required
@role_required("admin")
def delete_user(user_id: str):
    try:
        user_uuid = uuid.UUID(user_id)
        success = delete_entry(user_uuid)
        return jsonify({"message": "Utilisateur supprimé"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Routes Export / Import CSV ---
from flask import Response
# Route d'export, accessible par tous les utilisateurs (admin et user)
@api.route("/export_csv", methods=["GET"])
@spec.validate(tags=["csv"])
def export_csv_api():
    try:
        # Appelle la fonction pour générer le CSV
        output = export_to_csv(False)

        if not output:
            return jsonify({"error": "Aucune donnée à exporter"}), 500

        # Assure-toi que le contenu est prêt pour être envoyé
        csv_content = output.getvalue()

        return Response(
        csv_content,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=entries.csv"}
)
    except Exception as e:
        # Capture l'exception et log l'erreur
        logging.exception("Erreur lors de l'export CSV")
        return jsonify({"error": "Erreur lors de l'export"}), 500

# Route d'import, réservée à l'admin
@api.route("/import_csv", methods=["POST"])
@spec.validate(form=CSVFileUpload, tags=["csv"])
@token_auth.login_required
@role_required("admin")
def import_csv_api():
    try:
        file = request.files.get("file")
        if not file:
            return jsonify({"error": "Fichier manquant"}), 400
        import_from_csv(file.stream, True)
        return jsonify({"message": "Import réussi"}), 200
    except Exception as e:
        logging.exception("Erreur lors de l'import CSV")
        return jsonify({"error": "Erreur lors de l'import"}), 500
 