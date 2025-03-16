import uuid
from dataclasses import dataclass
from archilog import config
from sqlalchemy import create_engine, Column, String, Float, MetaData, Table, insert, update, delete
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, SelectField
from wtforms.validators import DataRequired, Optional
# Initialize global metadata
metadata = MetaData()

# Define the table
profile_table = Table(
    "profile",
    metadata,
    Column("id", String, primary_key=True),
    Column("name", String),
    Column("amount", Float),
    Column("category", String, nullable=True),
)

# Global engine for reuse
engine = create_engine(config.DATABASE_URL, echo=config.DEBUG)

# Function to create tables in the database
def init_db():
    metadata.create_all(engine)

@dataclass
class Entry:
    id: uuid.UUID
    name: str
    amount: float
    category: str

    @classmethod
    def from_db(cls, id: str, name: str, amount: float, category: str):
        # Ensure to convert id back to UUID
        return cls(uuid.UUID(id), name, amount, category)

def create_entry(name: str, amount: float, category: str) -> None:
    new_entry = {
        "id": uuid.uuid4().hex,
        "name": name,
        "amount": amount,
        "category": category,
    }
    stmt = insert(profile_table).values(new_entry)
    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()

def get_entry(id: uuid.UUID) -> Entry:
    with engine.connect() as conn:
        result = conn.execute(profile_table.select().where(profile_table.c.id == id.hex)).fetchone()
        if result:
            return Entry.from_db(*result)
        else:
            raise Exception("Entry not found")

def get_all_entries() -> list[Entry]:
    with engine.connect() as conn:
        results = conn.execute(profile_table.select()).fetchall()
        return [Entry.from_db(*r) for r in results]

def update_entry(id: uuid.UUID, name: str, amount: float, category: str | None) -> None:
    stmt = (
        update(profile_table)
        .where(profile_table.c.id == id.hex)
        .values(name=name, amount=amount, category=category)
    )
    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()

def delete_entry(id: uuid.UUID) -> None:
    stmt = delete(profile_table).where(profile_table.c.id == id.hex)
    with engine.connect() as conn:
        conn.execute(stmt)
        conn.commit()




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
