import uuid
import io
from flask import (
     Blueprint, render_template, send_file,
    redirect, url_for, flash,
)
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, FileField
from wtforms.validators import DataRequired, Optional
from archilog.models import (
    create_entry, delete_entry, update_entry,
      
)
from archilog.services import export_to_csv, import_from_csv

#WTF Forms :

class CreateUserForm(FlaskForm):
    class Meta:
        csrf = False  # Désactive la protection CSRF
    name = StringField('Nom', validators=[DataRequired()])
    amount = FloatField('Montant', validators=[DataRequired()])
    category = StringField('Catégorie', validators=[Optional()])

    
class DeleteUserForm(FlaskForm):
    class Meta:
        csrf = False  # Désactive la protection CSRF
    user_id = StringField('ID Utilisateur', validators=[DataRequired()])

class UpdateUserForm(FlaskForm):
    class Meta:
        csrf = False  # Désactive la protection CSRF
    id = StringField('ID de l\'utilisateur', validators=[DataRequired()])
    name = StringField('Nouveau nom', validators=[DataRequired()])
    amount = FloatField('Nouveau montant', validators=[DataRequired()])
    category = StringField('Nouvelle catégorie', validators=[DataRequired()])


class ImportCSVForm(FlaskForm):
    class Meta:
        csrf = False  # Désactive la protection CSRF
    csv_file = FileField('Fichier CSV', validators=[DataRequired()])




# --- Auth config ---
auth = HTTPBasicAuth()

users = {
    "vns": {"password": generate_password_hash("vns"), "role": "admin"},
    "susan": {"password": generate_password_hash("susan"), "role": "visitor"},
}

def check_admin():
    user = users.get(auth.current_user())
    return user and user["role"] == "admin"

@auth.verify_password
def verify_password(username, password):
    user = users.get(username)
    if user and check_password_hash(user["password"], password):
        return True
    return False

@auth.get_user_roles
def get_user_roles(username):
    user = users.get(username)
    return user["role"] if user else []


# --- Blueprint ---
web_ui = Blueprint('web_ui', __name__, url_prefix='/', template_folder='../templates')


# --- Web UI Routes ---
@web_ui.route('/')
@auth.login_required
def index():
    user = users.get(auth.current_user())
    if user["role"] == "admin":
        return redirect(url_for('web_ui.admin'))
    elif user["role"] == "visitor":
        return redirect(url_for('web_ui.visitor'))
    return "Accès refusé", 403

@web_ui.route('/admin')
@auth.login_required
def admin():
    if check_admin():
        return render_template('index.html')
    return "Accès refusé", 403

@web_ui.route('/visitor')
@auth.login_required
def visitor():
    user = users.get(auth.current_user())
    if user and user["role"] in ["visitor", "admin"]:
        flash("⚠️ Vous êtes connecté en tant que visiteur. Certaines fonctionnalités sont restreintes.", "warning")
        return render_template('index.html')
    return "Accès refusé", 403

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
    if form.validate_on_submit():
        try:
            user_id = uuid.UUID(form.user_id.data)
            delete_entry(user_id)
            return redirect(url_for('web_ui.index'))
        except ValueError:
            return "ID invalide", 400
    return render_template('delete.html', form=form)

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
    return render_template('update_user.html', form=form)

@web_ui.route('/import_csv', methods=['POST'])
@auth.login_required
def import_csv():
    if not check_admin():
        return "Accès refusé - Réservé aux administrateurs", 403
    form = ImportCSVForm()
    if form.validate_on_submit():
        try:
            import_from_csv(form.csv_file.data, True)
            flash("Importation réussie !", "success")
        except Exception as e:
            flash(f"Erreur : {str(e)}", "danger")
    else:
        flash("Erreur dans le formulaire.", "danger")
    return redirect(url_for('web_ui.admin'))



@web_ui.route('/export_csv')
def export_csv():
    """Génère le CSV et l'envoie directement en téléchargement sans l'écrire sur disque."""

    # Récupérer le CSV sous forme de StringIO
    csv_content = export_to_csv()

    # Convertir StringIO en BytesIO pour send_file
    output = io.BytesIO(csv_content.getvalue().encode("utf-8"))
    output.seek(0)  # Remettre le curseur au début du fichier

    return send_file(
        output,
        as_attachment=True,
        download_name="exported_users.csv",
        mimetype="text/csv"
    )