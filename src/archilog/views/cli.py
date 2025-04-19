import uuid
import archilog.models as models
import archilog.services as services
import click


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
@click.option("--id", "entry_id", required=True, help="ID de l'entrée à récupérer")
def get(entry_id: str):
    
    try:
        entry = models.get_entry(uuid.UUID(entry_id))
        click.echo(f"ID: {entry.id}, Name: {entry.name}, Amount: {entry.amount}, Category: {entry.category}")
    except Exception as e:
        click.echo(f"Erreur lors de la récupération de l'entrée : {str(e)}")
        
        


@cli.command()
def get_all():
    try:
        entries = models.get_all_entries()
        for entry in entries:
            click.echo(f"ID: {entry.id}, Name: {entry.name}, Amount: {entry.amount}, Category: {entry.category}")
    except Exception as e:
        click.echo(f"Erreur lors de la récupération des entrées : {str(e)}")


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
