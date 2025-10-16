import boto3
from botocore.config import Config
from sqlalchemy import create_engine, Table, MetaData, select, update
from sqlalchemy.orm import sessionmaker, declarative_base
import json
import csv

# --- AWS clients configuration ---
boto_config = Config(connect_timeout=5, read_timeout=15, retries={"max_attempts": 1, "mode": "standard"})
ssm_client = boto3.client("ssm", config=boto_config)
secrets_client = boto3.client("secretsmanager", config=boto_config)

# --- Helpers ---
def get_parameter(name: str, with_decryption: bool = True) -> str:
    response = ssm_client.get_parameter(Name=name, WithDecryption=with_decryption)
    return response["Parameter"]["Value"]

def get_secret(secret_name: str) -> dict:
    response = secrets_client.get_secret_value(SecretId=secret_name)
    secret_string = response.get("SecretString")
    if secret_string:
        return json.loads(secret_string)
    raise ValueError(f"No SecretString found for {secret_name}")

def get_db_credentials():
    db_host = get_parameter("db-endpoint-tenant-dev")  
    db_secret = get_secret("rds!cluster-496992e7-8e6e-4c59-800d-78abd6468aef") 

    print(db_secret["password"])

    return {
        "host": db_host,
        "username": db_secret["username"],
        "password": db_secret["password"],
        "port": 5432,
        "database": "postgres",
    }

# --- SQLAlchemy Base ---
Base = declarative_base()

# --- Initialize engine and session at startup ---
creds = get_db_credentials()
DB_URL = f"postgresql+psycopg2://{creds['username']}:{creds['password']}@{creds['host']}:{creds['port']}/{creds['database']}"
engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
session = SessionLocal()

metadata = MetaData()
shelves_table = Table("shelves", metadata, autoload_with=engine)

def get_shelf_position(shelf_id: str):

    shelf_position = {}

    stmt = select(
        shelves_table.c.position_x,
        shelves_table.c.position_y,
        shelves_table.c.position_z
    ).where(shelves_table.c.id == shelf_id)

    result = session.execute(stmt).first()
    if result:
        shelf_position = {
            "position_x": result.position_x,
            "position_y": result.position_y,
            "position_z": result.position_z
        }
        return shelf_position
    else:
        return None
    
def validate_shelf_id(shelf_id: str) -> dict:
    """
    Validates a shelf ID and extracts its components.

    Args:
        shelf_id: The shelf ID to validate.

    Returns:
        A dictionary containing the passage, column, level, and subcolumn.

    Raises:
        ValueError: If the shelf ID is invalid.
    """
    if not isinstance(shelf_id, str) or not shelf_id.isdigit() or len(shelf_id) != 7:
        raise ValueError("Invalid shelf ID: Must be a 7-digit string.")

    return {
        "passage": shelf_id[0:2],
        "column": shelf_id[2:4],
        "level": shelf_id[4:6],
        "subcolumn": shelf_id[6],
    }

def set_shelf_x_for_passage(passage: str, new_x: float) -> int:
    """
    Update the position_x value for all shelves belonging to a given passage.

    Args:
        passage: Two-digit passage string (e.g., "01").
        new_x: The new X position to set.

    Returns:
        The number of rows updated.
    """
    if not isinstance(passage, str) or not passage.isdigit() or len(passage) != 2:
        raise ValueError("Invalid passage: must be a 2-digit string.")

    # Update query - filter where shelf_id starts with passage
    stmt = (
        update(shelves_table)
        .where(shelves_table.c.id.like(f"{passage}%"))
        .values(position_x=new_x)
    )

    result = session.execute(stmt)
    session.commit()

    return result.rowcount

def set_shelf_z_for_passage_level(passage: str, level: str, new_z: float) -> int:
    """
    Update the position_z value for all shelves belonging to a given passage and level.

    Args:
        passage: Two-digit passage string (e.g., "01").
        level: Two-digit level string (e.g., "03").
        new_z: The new Z position to set.

    Returns:
        The number of rows updated.
    """
    # Validate inputs
    if not (isinstance(passage, str) and passage.isdigit() and len(passage) == 2):
        raise ValueError("Invalid passage: must be a 2-digit string.")
    if not (isinstance(level, str) and level.isdigit() and len(level) == 2):
        raise ValueError("Invalid level: must be a 2-digit string.")

    # LIKE pattern: passage (2 digits) + any column (2 chars) + level (2 digits) + any subcolumn (1 char)
    pattern = f"{passage}__{level}%"

    stmt = (
        update(shelves_table)
        .where(shelves_table.c.id.like(pattern))
        .values(position_z=new_z)
    )

    result = session.execute(stmt)
    session.commit()

    return result.rowcount

def set_shelf_y_for_passage_column(passage: str, column: str, new_y: float) -> int:
    """
    Update the position_y value for all shelves belonging to a given passage and column.

    Args:
        passage: Two-digit passage string (e.g., "01").
        column: Two-digit column string (e.g., "02").
        new_y: The new Y position to set.

    Returns:
        The number of rows updated.
    """
    # Validate inputs
    if not (isinstance(passage, str) and passage.isdigit() and len(passage) == 2):
        raise ValueError("Invalid passage: must be a 2-digit string.")
    if not (isinstance(column, str) and column.isdigit() and len(column) == 2):
        raise ValueError("Invalid column: must be a 2-digit string.")

    # LIKE pattern: passage (2 digits) + column (2 digits) + anything (level+subcolumn)
    pattern = f"{passage}{column}%"

    stmt = (
        update(shelves_table)
        .where(shelves_table.c.id.like(pattern))
        .values(position_y=new_y)
    )

    result = session.execute(stmt)
    session.commit()

    return result.rowcount

def update_x_from_csv(file_path: str):
    """
    Reads a CSV file and updates the shelf_x position for each passage.

    Args:
        file_path: The path to the CSV file.
    """
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            passage = row['passage']
            x_val = float(row['x_val'])
            
            # Ensure passage is a 2-digit string
            if len(passage) == 1:
                passage = f"0{passage}"

            updated_rows = set_shelf_x_for_passage(passage, x_val)
            print(f"Updated {updated_rows} shelves in passage {passage} with x_val {x_val}.")

def update_y_from_csv(file_path: str):
    """
    Reads a CSV file and updates the shelf_y position for each passage and column.

    Args:
        file_path: The path to the CSV file.
    """
    with open(file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for passage_num in range(13, 39):
            passage = str(passage_num)
            if len(passage) == 1:
                passage = f"0{passage}"
            
            # Reset file pointer to the beginning of the file for each passage
            csvfile.seek(0)
            next(reader) # Skip header

            for row in reader:
                column = row['column']
                y_val = float(row['distance'])

                if len(column) == 1:
                    column = f"0{column}"

                updated_rows = set_shelf_y_for_passage_column(passage, column, y_val)
                print(f"Updated {updated_rows} shelves in passage {passage}, column {column} with y_val {y_val}.")

if __name__ == "__main__":

    # === test 1 ===
    shelf_id_input = input("Enter shelf ID: ")
    print(validate_shelf_id(shelf_id_input))
    position = get_shelf_position(shelf_id_input)
    print(position)

    # === test 2 ===
    # passage = input("Enter passage (2 digits): ")
    # new_x = float(input("Enter new X value: "))
    # updated_rows = set_shelf_x_for_passage(passage, new_x)
    # print(f"Updated {updated_rows} shelves in passage {passage}.")

    # === test 3 ===
    # passage = input("Enter passage (2 digits): ")
    # level = input("Enter level (2 digits): ")
    # new_z = float(input("Enter new Z value: "))
    # updated_rows = set_shelf_z_for_passage_level(passage, level, new_z)
    # print(f"Updated {updated_rows} shelves in passage {passage}, level {level}.")

    # === test 4 ===
    # passage = input("Enter passage (2 digits): ")
    # column = input("Enter column (2 digits): ")
    # new_y = float(input("Enter new Y value: "))
    # updated_rows = set_shelf_y_for_passage_column(passage, column, new_y)
    # print(f"Updated {updated_rows} shelves in passage {passage}, column {column}.")
    
    # === test 5 ===
    # update_x_from_csv("preflight_dynamic_path/warehouse_metadata/passage_x.csv")
    
    # === test 6 ===
    # update_y_from_csv("preflight_dynamic_path/warehouse_metadata/passage_y.csv")
