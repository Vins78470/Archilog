from flask import Flask, render_template, request, send_file
import uuid
import os
import archilog.models as models
import archilog.services as services
from archilog.models import create_entry,delete_entry,init_db,update_entry
from archilog.services import export_to_csv,import_from_csv
import click

"""
app = Flask(__name__)
init_db() #Initialisation de la bd


# Route pour afficher la page d'accueil avec les options
@app.route('/')
def index():
    
    return render_template('index.html')

@app.route('/display_create_user')
def display_create_user():
    return render_template('form.html')


# Route pour traiter la soumission du formulaire
@app.route('/creer_user', methods=['POST'])
def creer_user():
    if request.method == 'POST':
        # Récupérer les données du formulaire
        name = request.form.get('name')
        amount = request.form.get('amount')
        category = request.form.get('category')
        
        # Vérifier si les données sont présentes
        print(f"Nom: {name}, Montant: {amount}, Catégorie: {category}")
        
        # Logique pour créer un utilisateur (fonction `create_entry` de ton modèle)
        create_entry(name, amount, category)
        return "Importation réussie"
        # Rediriger vers la page d'accueil après avoir créé l'utilisateur
        #return redirect(url_for('index'))
    
    # Si la méthode n'est pas POST, afficher le formulaire
    return render_template('form.html')

# Route pour afficher le formulaire de création d'utilisateur
@app.route('/display_delete_user_page', methods=['GET'])
def display_delete_user_page():
    
    return render_template('delete.html')

# Route pour supprimer un utilisateur

@app.route('/delete_user', methods=['POST'])
def delete_user():
    user_id = request.form.get('id')  # Récupère l'ID du formulaire
    
    if not user_id:  
        return "ID manquant", 400  # Vérifie si un ID est fourni
    
    try:
        uid = uuid.UUID(user_id)  #  Convertit l'ID en UUID valide
    except ValueError:
        return "ID invalide", 400  # Gère le cas où l'ID n'est pas un UUID valide
    
    delete_entry(uid)  #  Passe l'UUID à la fonction delete_entry
    return "Suppression réussie"
  



# Route pour afficher la page de mise à jour d'un utilisateur
@app.route('/display_update_user_page', methods=['GET'])
def display_update_user_page():
    return render_template('update_user.html')

# Route pour traiter la mise à jour d'un utilisateur
@app.route('/update_user', methods=['POST'])
def update_user():
    user_id = request.form.get('id')
    new_user_id =  uuid.UUID(user_id)    #  Convertit l'ID en UUID valide
    new_name = request.form.get('name')
    new_amount = request.form.get('amount')
    new_category = request.form.get('category')

    update_entry(new_user_id,new_name,new_amount,new_category)

    return "Importation réussie" # Redirection après mise à jour



@app.route('/import_csv', methods=['POST'])
def import_csv():
     
    file = request.files.get('csv_file')

    if not file:
        return "Aucun fichier envoyé", 400  # Retourne une erreur si aucun fichier n'est envoyé

    import_from_csv(file,True)  # Traitement du fichier

    return "Importation réussie", 200  # Retourne une réponse HTTP valide

@app.route('/export_csv')
def export_csv():
    Génère le CSV et permet le téléchargement
    filename = "exported_users.csv"
    filepath = os.path.join(os.getcwd(), filename)

    # Récupérer le CSV généré sous forme de StringIO
    csv_content = services.export_to_csv()

    # Écrire ce contenu dans un vrai fichier
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        f.write(csv_content.getvalue())

    # Vérifier que le fichier a bien été écrit
    if not os.path.exists(filepath):
        return "Erreur : Le fichier CSV n'a pas été généré.", 404

    # Envoyer le fichier en téléchargement
    return send_file(filepath, as_attachment=True, download_name=filename, mimetype="text/csv")


if __name__ == '__main__':
    app.run(debug=True)

"""

@click.group()
def cli():
    pass


@cli.command()
def init_db():
    models.init_db()


@cli.command()
@click.option("-n", "--name", prompt="Name")
@click.option("-a", "--amount", type=float, prompt="Amount")
@click.option("-c", "--category", prompt="Category")
def create(name: str, amount: float, category: str | None):
    models.create_entry(name, amount, category)


@cli.command()
@click.option("--id", required=True, type=click.UUID)
def get(id: uuid.UUID):
    click.echo(models.get_entry(id))


@cli.command()
@click.option("--as-csv", is_flag=True, help="Ouput a CSV string.")
def get_all(as_csv: bool):
    if as_csv:
        click.echo(services.export_to_csv().getvalue())
    else:
        click.echo(models.get_all_entries())


@cli.command()
@click.argument("csv_file", type=click.File("r"))
def import_csv(csv_file):
    services.import_from_csv(csv_file)


@cli.command()
def export_to_csv():
    services.export_to_csv(True)


@cli.command()
@click.option("--id", type=click.UUID, required=True)
@click.option("-n", "--name", required=True)
@click.option("-a", "--amount", type=float, required=True)
@click.option("-c", "--category", default=None)
def update(id: uuid.UUID, name: str, amount: float, category: str | None):
    models.update_entry(id, name, amount, category)


@cli.command()
@click.option("--id", required=True, type=click.UUID)
def delete(id: uuid.UUID):
    models.delete_entry(id)
