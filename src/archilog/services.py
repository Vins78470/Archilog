
import sys
from archilog.models import create_entry, get_all_entries, Entry
import csv
import dataclasses
from io import StringIO


def export_to_csv() -> StringIO:
    # Nom du fichier de sortie
    filename = "output.csv"

    # Récupérer toutes les entrées
    entries = get_all_entries()

    # Préparer les données pour CSV
    fieldnames = [f.name for f in dataclasses.fields(Entry)]

    # Création de l'objet StringIO pour garder une version en mémoire du CSV
    output = StringIO()

    # Écrire dans le fichier et dans le StringIO
    with open(filename, mode='w', newline='', encoding='utf-8') as output_file:
        csv_writer = csv.DictWriter(output_file, fieldnames=fieldnames)
        csv_writer.writeheader()
        for entry in entries:
            csv_writer.writerow(dataclasses.asdict(entry))

        # Réécriture dans StringIO pour le retour
        csv_writer = csv.DictWriter(output, fieldnames=fieldnames)
        output.seek(0)  # Revenir au début du StringIO
        csv_writer.writeheader()
        for entry in entries:
            csv_writer.writerow(dataclasses.asdict(entry))

    output.seek(0)  # Retourner le pointeur au début avant de retourner l'objet StringIO
    return output



def import_from_csv(csv_file,isFlask = False) -> None:
    # Si le fichier provient de Flask (l'encodage UTF-8-SIG est nécessaire pour gérer le BOM si présent)
    if isFlask:
        csv_content = csv_file.read().decode("utf-8-sig").splitlines()  # Lire et décoder le fichier
    else:
        csv_content = csv_file.read().splitlines()  # Updated line
 
    csv_reader = csv.DictReader(csv_content, delimiter=',')

    for row in csv_reader:
        if "amount" not in row:
            print(f"⚠️ 'amount' absent ! Clés détectées : {row.keys()}", file=sys.stderr)
            continue
        create_entry(
            name=row.get("name", "").strip(),
            amount=float(row["amount"].strip()) if row["amount"].strip() else 0,
            category=row.get("category", "").strip(),
        )

