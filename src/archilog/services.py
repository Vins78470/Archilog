import csv
import dataclasses
import sys
from io import StringIO

from archilog.models import create_entry, get_all_entries, Entry
from dataclasses import dataclass



def export_to_csv(write_to_file=False):
    """ Exporte les entrées en CSV. 
        - Si `write_to_file=True` → Écrit dans un fichier.
        - Sinon → Retourne un `StringIO` pour flask. """
    
    filename = 'exported_users.csv'
    entries = get_all_entries()
    fieldnames = [f.name for f in dataclasses.fields(Entry)]

    output = StringIO()
    csv_writer = csv.DictWriter(output, fieldnames=["id", "name", "amount", "category"], extrasaction='raise')

    csv_writer.writeheader()
    for entry in entries:
        row = entry.to_dict()
        filtered_row = {key: row.get(key, "") for key in csv_writer.fieldnames}
        csv_writer.writerow(filtered_row)


    output.seek(0)  # Revenir au début pour lecture

    if write_to_file:
        with open(filename, "w", newline="", encoding="utf-8") as f:
            f.write(output.getvalue())
        return filename  # Retourne le nom du fichier

    return output  # Retourne l'objet `StringIO` pour Flask


def import_from_csv(csv_file, is_flask=False) -> None:
    """ Importe des entrées depuis un fichier CSV. """

    # Lire le fichier CSV selon la source (Flask ou standard)
    content = csv_file.read().decode("utf-8-sig").splitlines() if is_flask else csv_file.read().splitlines()
    
    csv_reader = csv.DictReader(content)

    for row in csv_reader:
        if "amount" not in row:
            print(f"⚠️ 'amount' absent ! Clés détectées : {list(row.keys())}", file=sys.stderr)
            continue
        
        create_entry(
            name=row.get("name", "").strip(),
            amount=float(row["amount"].strip()) if row["amount"].strip() else 0,
            category=row.get("category", "").strip(),
        )
