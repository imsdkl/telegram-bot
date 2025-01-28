from peewee import *
import os
import datetime
from playhouse.db_url import connect
from collections import defaultdict
from playhouse.pool import PooledPostgresqlExtDatabase
import uuid

DB_NAME = os.environ.get('DB_NAME', '')
DB_USER = os.environ.get('DB_USER', '')
DB_PASSWORD = os.environ.get('DB_PASSWORD', '')
DB_HOST = os.environ.get('DB_HOST', '')

db = PostgresqlDatabase(DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=5432)
db.connection()

class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def ensure_connection(cls):
        """
        Ensures the database connection is active. Reconnects if it is closed.
        """
        try:
            db.connect(True)
            print("Database connection reestablished.")
        except Exception as e:
            print(f"Failed to reconnect to the database: {e}")
            raise

    @classmethod
    def close_connection(cls):
        """
        Ensures the database connection is active. Reconnects if it is closed.
        """
        try:
            db.close()
            print("Database connection closed.")
        except Exception as e:
            print(f"Failed to reconnect to the database: {e}")
            raise


class Bot(BaseModel):
    number = CharField(unique=True)
    session_string = TextField(null=True)
    name = CharField(null=True)
    telegram_id = CharField(null=True)
    state = CharField(null=True)
    token = CharField(null=True)
    platform = CharField(unique=True)

    class Meta:
        table_name = 'phone_numbers'

def create_tables():
    with db:
        db.create_tables([Bot])


def drop_tables():
    with db:
        db.drop_tables([Bot])
