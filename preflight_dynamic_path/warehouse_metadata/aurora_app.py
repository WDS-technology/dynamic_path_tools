import boto3
from botocore.config import Config
from sqlalchemy import create_engine, Table, MetaData, select
from sqlalchemy.orm import sessionmaker, declarative_base
import json

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

if __name__ == "__main__":
    shelf_id_input = input("Enter shelf ID: ")
    get_shelf_position(shelf_id_input)
