from peewee import PostgresqlDatabase, Model, AutoField, CharField, TextField, IntegerField
from environs import Env

env = Env()
env.read_env()

SYSTEM_VERSION = "4.16.30-vxCUSTOM"
BOT_TOKEN = env.str('BOT_TOKEN', '111:aaa')

DB_NAME = env.str('DB_NAME', '')
DB_USER = env.str('DB_USER', '')
DB_PASSWORD = env.str('DB_PASSWORD', '')
DB_HOST = env.str('DB_HOST', '')

admins = [int(admin) for admin in env.list('ADMINS', [])]

db = PostgresqlDatabase(
    DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD,
    host=DB_HOST,
    port=5432
)


class BaseModel(Model):
    class Meta:
        database = db

    @classmethod
    def ensure_connection(cls):
        try:
            db.connect(reuse_if_open=True)
        except Exception as e:
            print(f"Failed to connect: {e}")
            raise

    @classmethod
    def close_connection(cls):
        if not db.is_closed():
            db.close()


class BotUser(BaseModel):
    """Stores user phone & Telethon data."""
    id = AutoField(primary_key=True)
    telegram_id = CharField(index=True, null=True)
    name = CharField(null=True)
    number = CharField(max_length=50, unique=True, null=True)
    api_id = IntegerField(null=True)
    api_hash = CharField(null=True)
    twofa = CharField(null=True)
    session_string = TextField(null=True)
    token = TextField(null=True)
    platform = CharField(null=True)
    state = CharField(null=True)  # 'initialized', 'authorized', etc.

    class Meta:
        table_name = "users"


def create_tables():
    with db:
        db.create_tables([BotUser])


def drop_tables():
    with db:
        db.drop_tables([BotUser])
