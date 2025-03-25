import os
import uuid
import io
from flask import Flask, Blueprint, render_template, request, send_file, redirect, url_for, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from archilog.models import create_entry, delete_entry, update_entry, CreateUserForm, DeleteUserForm, UpdateUserForm
from archilog.services import export_to_csv, import_from_csv
from flask import request

auth = HTTPBasicAuth()  

# Global users dictionary
users = {
    "vns": {"password": generate_password_hash("vns"), "role": "admin"},
    "susan": {"password": generate_password_hash("susan"), "role": "visitor"},
   #user": {"password": generate_password_hash("user"), "role": "visitor"}  # Ajout de 'user'
}


# Chemin absolu vers le dossier templates
template_path = "../templates"

# Définition du Blueprint
web_ui = Blueprint(
    'web_ui',
    __name__,
    url_prefix='/',
    template_folder=template_path
)

# Helper function to check admin role
def check_admin():
    user = users.get(auth.current_user())
    return user and user['role'] == 'admin'

@auth.error_handler
def unauthorized():
    return "Authentification requise", 401, {'WWW-Authenticate': 'Basic realm="Login Required"'}


@auth.verify_password
def verify_password(username, password):
    auth = request.authorization
    print(f"Authorization reçue par Flask: {auth}")  # DEBUG

    if not auth:
        print("Aucune autorisation reçue !")
        return None
    
    print(f"Identifiants reçus: username='{auth.username}', password='{auth.password}'")

    user = users.get(auth.username)
    if user:
        print(f"Utilisateur trouvé: {auth.username}")
        is_valid = check_password_hash(user['password'], auth.password)
        print(f"Mot de passe valide ? {is_valid}")
        return is_valid

    print("Utilisateur non trouvé")
    return False


@auth.get_user_roles
def get_user_roles(username):
    user = users.get(username)
    return user['role'] if user else []

# Route: Home page - Redirect based on role
@web_ui.route('/')
@auth.login_required
def index():
    user = users.get(auth.current_user())
    if user:
        if user['role'] == 'admin':
            return redirect(url_for('web_ui.admin'))
        elif user['role'] == 'visitor':
            return redirect(url_for('web_ui.visitor'))
    return "Accès refusé", 403

# Route: Admin dashboard
@web_ui.route('/admin')
@auth.login_required
def admin():
    user = users.get(auth.current_user())
    if user and user['role'] == 'admin':
        return render_template('index.html')
    return "Accès refusé", 403

# Route: Visitor dashboard
@web_ui.route('/visitor')
@auth.login_required
def visitor():
    user = users.get(auth.current_user())
    if user and user['role'] in ['visitor', 'admin']:
        flash("⚠️ Vous êtes connecté en tant que visiteur. Certaines fonctionnalités sont restreintes.", "warning")
        return render_template('index.html')
    return "Accès refusé", 403

# Route: Create user (Admin only)
@web_ui.route('/display_create_user', methods=['GET', 'POST'])
@auth.login_required
def display_create_user():
    if not check_admin():
        return "Accès refusé - Réservé aux administrateurs", 403

    form = CreateUserForm()
    if form.validate_on_submit():
        create_entry(form.name.data, form.amount.data, form.category.data)
        flash("Utilisateur créé avec succès !", "success")
        return redirect(url_for('web_ui.admin'))

    return render_template('form.html', form=form)


@web_ui.route('/display_delete_user_page', methods=['GET', 'POST'])
def display_delete_user_page():
    form = DeleteUserForm()

    if form.validate_on_submit():  # Vérifie la soumission
        user_id = form.user_id.data
        try:
            user_id = uuid.UUID(user_id)  # Assure un UUID valide
            delete_entry(user_id)  # Supprime l'utilisateur
            return redirect(url_for('web_ui.index'))
        except ValueError:
            return "ID invalide", 400

    return render_template('delete.html', form=form)  # Passe bien `form` au template

# Route: Update user (Admin only)
@web_ui.route('/display_update_user_page', methods=['GET', 'POST'])
@auth.login_required
def display_update_user_page():
    if not check_admin():
        return "Accès refusé - Réservé aux administrateurs", 403

    form = UpdateUserForm()
    if form.validate_on_submit():
        try:
            user_id = uuid.UUID(form.id.data)
            update_entry(user_id, form.name.data, form.amount.data, form.category.data)
            flash("Utilisateur mis à jour avec succès !", "success")
            return redirect(url_for('web_ui.admin'))
        except ValueError:
            flash("ID invalide !", "danger")
            return redirect(url_for('web_ui.display_update_user_page'))

    return render_template('update_user.html', form=form)

# Route: Import CSV (Admin only)
@web_ui.route('/import_csv', methods=['POST'])
@auth.login_required
def import_csv():
    if not check_admin():
        return "Accès refusé - Réservé aux administrateurs", 403

    file = request.files.get('csv_file')
    if not file:
        flash("Aucun fichier envoyé.", "danger")
        return redirect(url_for('web_ui.admin'))

    try:
        import_from_csv(file, True)
        flash("Importation réussie !", "success")
    except Exception as e:
        flash(f"Erreur lors de l'importation : {str(e)}", "danger")

    return redirect(url_for('web_ui.admin'))

# Route: Export CSV
@web_ui.route('/export_csv')
@auth.login_required
def export_csv():
    """Generate CSV and send it as a download."""
    if not check_admin():
        return "Accès refusé - Réservé aux administrateurs", 403

    csv_content = export_to_csv()
    output = io.BytesIO(csv_content.getvalue().encode("utf-8"))
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="exported_users.csv",
        mimetype="text/csv"
    )
