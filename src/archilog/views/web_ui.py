import os
from flask import Blueprint, render_template, request, send_file, redirect, url_for
import uuid
from archilog.models import create_entry, delete_entry, update_entry, CreateUserForm, DeleteUserForm, UpdateUserForm
from archilog.services import export_to_csv, import_from_csv
import io

# Flask app and HTTPBasicAuth initialization
from flask import Flask
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Global users dictionary (make sure it's defined)
users = {
    "john": {"password": generate_password_hash("hello"), "role": "admin"},
    "susan": {"password": generate_password_hash("bye"), "role": "visitor"}
}

# Chemin absolu vers le dossier templates
template_path = "../templates"

# Définir le Blueprint avec le bon chemin pour les templates
web_ui = Blueprint(
    'web_ui',
    __name__,
    url_prefix='/',
    template_folder=template_path  # Chemin absolu vers 'templates'
)

# Helper function to ensure admin role
def check_admin():
    user = users.get(auth.current_user())
    return user and user['role'] == 'admin'

# Flask authentication setup
@auth.verify_password
def verify_password(username, password):
    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        return username  # User authenticated
    print(f"Failed authentication for {username}")  # Debugging line
    return None  # Incorrect username or password

@auth.get_user_roles
def get_user_roles(username):
    user = users.get(username)
    if user:
        return user['role']
    return []  # Default to an empty role list if user is not found

# Route for creating a user
@web_ui.route('/display_create_user', methods=['GET', 'POST'])
def display_create_user():
    form = CreateUserForm()
    if check_admin():
        if form.validate_on_submit():  # Form validation
            name = form.name.data
            amount = form.amount.data
            category = form.category.data

            # Create a new user entry
            create_entry(name, amount, category)
            
            return redirect(url_for('web_ui.index'))  # Redirect to index after creation

    return render_template('form.html', form=form)

# Route for deleting a user
@web_ui.route('/display_delete_user_page', methods=['GET', 'POST'])
def display_delete_user_page():
    form = DeleteUserForm()
    if check_admin():
        if form.validate_on_submit():  # Form validation
            user_id = form.user_id.data
            try:
                user_id = uuid.UUID(user_id)  # Ensure valid UUID
                delete_entry(user_id)  # Delete user by ID
                return redirect(url_for('web_ui.index'))  # Redirect after deletion
            except ValueError:
                return "ID invalide", 400  # Handle invalid UUID format

    return render_template('delete.html', form=form)

# Route for updating a user
@web_ui.route('/display_update_user_page', methods=['GET', 'POST'])
def display_update_user_page():
    form = UpdateUserForm()
    if check_admin():
        if form.validate_on_submit():
            try:
                user_id = uuid.UUID(form.id.data)
                name = form.name.data
                amount = form.amount.data
                category = form.category.data

                update_entry(user_id, name, amount, category)  # Update user
                return redirect(url_for('web_ui.index'))  # Redirect after update
            except ValueError:
                return "ID invalide", 400  # Handle invalid UUID format

    return render_template('update_user.html', form=form)

# Route for importing CSV
@web_ui.route('/import_csv', methods=['POST'])
def import_csv():
    if check_admin():
        file = request.files.get('csv_file')
        if not file:
            return "Aucun fichier envoyé", 400  # Return error if no file is sent

        try:
            import_from_csv(file, True)  # Process the file
            return "Importation réussie", 200  # Return success response
        except Exception as e:
            return str(e), 400  # Handle any errors during import

# Route for exporting data to CSV
@web_ui.route('/export_csv')
def export_csv():
    """Generate CSV and send it as a download."""
    csv_content = export_to_csv()

    output = io.BytesIO(csv_content.getvalue().encode("utf-8"))
    output.seek(0)

    return send_file(
        output,
        as_attachment=True,
        download_name="exported_users.csv",
        mimetype="text/csv"
    )


# Route for home page
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

# Admin route
@web_ui.route('/admin')
@auth.login_required
def admin():
    user = users.get(auth.current_user())
    if user and user['role'] == 'admin':
        return render_template('index.html')
    return "Accès refusé", 403

# Visitor route
@web_ui.route('/visitor')
@auth.login_required
def visitor():
    user = users.get(auth.current_user())
    if user and (user['role'] == 'visitor' or user['role'] == 'admin'):
        return render_template('index.html')
    return "Accès refusé", 403
