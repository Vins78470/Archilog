import os
from flask import Blueprint, render_template
from flask import Blueprint, request, send_file
import uuid
import os
from archilog.models import create_entry, delete_entry, update_entry,CreateUserForm,DeleteUserForm,UpdateUserForm
from archilog.services import export_to_csv, import_from_csv
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField
from wtforms.validators import DataRequired, Optional


# Chemin absolu vers le dossier templates
# Chemin absolu vers le dossier templates
template_path = "../templates"  # Utilise des barres obliques


# Définir le Blueprint avec le bon chemin pour les templates
web_ui = Blueprint(
    'web_ui',
    __name__,
    url_prefix='/',
    template_folder=template_path  # Chemin absolu vers 'templates'
)

@web_ui.route('/')
def index():
    return render_template('index.html')

@web_ui.route('/display_create_user', methods=['GET', 'POST'])
def display_create_user():
    form = CreateUserForm()

    if form.validate_on_submit():  # Vérifie si le formulaire a été soumis et est valide
        name = form.name.data
        amount = form.amount.data
        category = form.category.data

        # Créer un nouvel utilisateur avec les données du formulaire
        create_entry(name, amount, category)
        
        return render_template('index.html') #Redirige vers la page d'accueil après la création

    return render_template('form.html', form=form)


@web_ui.route('/display_delete_user_page', methods=['GET', 'POST'])
def display_delete_user_page():
    form = DeleteUserForm()

    if form.validate_on_submit():  # Vérifie si le formulaire a été soumis et est valide
        user_id = form.user_id.data

        # Logique de suppression d'utilisateur en utilisant l'ID fourni
        delete_entry(user_id)  # Suppression de l'utilisateur avec `delete_entry`
        
        return render_template('index.html') # Redirige vers la page d'accueil après la suppression

    return render_template('delete.html', form=form)


@web_ui.route('/display_update_user_page', methods=['GET', 'POST'])
def display_update_user_page():
    form = UpdateUserForm()

    if form.validate_on_submit():  # Vérifie si le formulaire a été soumis et est valide
        id = uuid.UUID(form.id.data)
        name = form.name.data
        amount = form.amount.data
        category = form.category.data

        # Logique de mise à jour de l'utilisateur
        update_entry(id, name, amount, category)  # Met à jour l'utilisateur avec `update_entry`

        return render_template('index.html')  # Redirige vers la page d'accueil après la mise à jour

    return render_template('update_user.html', form=form)


# Route pour traiter la soumission du formulaire de création d'utilisateur
@web_ui.route('/creer_user', methods=['POST'])
def creer_user():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.form.get('name')
        amount = request.form.get('amount')
        category = request.form.get('category')
        
        # Logique pour créer un utilisateur
        create_entry(name, amount, category)
        return "Importation réussie"
    return "Erreur de soumission", 400

# Route pour supprimer un utilisateur
@web_ui.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form.get('id')  # Récupère l'ID du formulaire
    
    if not user_id:  
        return "ID manquant", 400  # Vérifie si un ID est fourni
    
    try:
        uid = uuid.UUID(user_id)  # Convertit l'ID en UUID valide
    except ValueError:
        return "ID invalide", 400  # Gère le cas où l'ID n'est pas un UUID valide
    
    delete_entry(uid)  # Supprimer l'utilisateur
    return "Suppression réussie"

# Route pour mettre à jour un utilisateur
@web_ui.route('/update_user', methods=['POST'])
def update_user():
    user_id = request.form.get('id')
    new_user_id = uuid.UUID(user_id)  # Convertit l'ID en UUID valide
    new_name = request.form.get('name')
    new_amount = request.form.get('amount')
    new_category = request.form.get('category')

    update_entry(new_user_id, new_name, new_amount, new_category)

    return "Importation réussie"  # Redirection après mise à jour

# Route pour importer un fichier CSV
@web_ui.route('/import_csv', methods=['POST'])
def import_csv():
    file = request.files.get('csv_file')

    if not file:
        return "Aucun fichier envoyé", 400  # Retourne une erreur si aucun fichier n'est envoyé

    import_from_csv(file, True)  # Traitement du fichier

    return "Importation réussie", 200  # Retourne une réponse HTTP valide

# Route pour exporter les données en CSV
@web_ui.route('/export_csv')
def export_csv():
    """Génère le CSV et permet le téléchargement"""
    filename = "exported_users.csv"
    filepath = os.path.join(os.getcwd(), filename)

    # Récupérer le CSV généré sous forme de StringIO
    csv_content = export_to_csv()

    # Écrire ce contenu dans un vrai fichier
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        f.write(csv_content.getvalue())

    # Vérifier que le fichier a bien été écrit
    if not os.path.exists(filepath):
        return "Erreur : Le fichier CSV n'a pas été généré.", 404

    # Envoyer le fichier en téléchargement
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="text/csv")


class CreateUserForm(FlaskForm):
    name = StringField('Nom', validators=[DataRequired()])
    amount = FloatField('Montant', validators=[DataRequired()])
    category = SelectField('Catégorie', choices=[('cat1', 'Catégorie 1'), ('cat2', 'Catégorie 2')], validators=[Optional()])
    
class DeleteUserForm(FlaskForm):
    user_id = StringField('ID Utilisateur', validators=[DataRequired()])

class UpdateUserForm(FlaskForm):
    id = StringField('ID de l\'utilisateur', validators=[DataRequired()])
    name = StringField('Nouveau nom', validators=[DataRequired()])
    amount = FloatField('Nouveau montant', validators=[DataRequired()])
    category = StringField('Nouvelle catégorie', validators=[DataRequired()])
