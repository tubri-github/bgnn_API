from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import configparser

config = configparser.ConfigParser()
config.read('./config.ini')

db_user = config.get('database', 'user')
db_password = config.get('database', 'password')
db_host = config.get('database', 'localhost')
db_name = config.get('database', 'dbname')

SQLALCHEMY_DATABASE_URL = (
   "postgresql+psycopg2://" + db_user + ":" + db_password + "@" + db_host + "/" + db_name
)

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
