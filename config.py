from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sys


app = Flask(__name__)

try:
    lines = [line.rstrip('\n') for line in open('.secret_key')]
    secret_key = lines[0]

except Exception as exception:
    sys.exit("Couldn't get secret key. Does .secret_key exist?")

app.secret_key = secret_key


engine = create_engine("postgresql://jatin1:password@localhost/player2")
Session = sessionmaker(bind=engine)
session = Session()
