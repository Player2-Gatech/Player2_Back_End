from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
import sys


app = Flask(__name__)
port_num = None

try:
    lines = [line.rstrip('\n') for line in open('.secret_key')]
    secret_key = lines[0]
    app.secret_key = secret_key

except Exception as exception:
    sys.exit("Couldn't get secret key. Does .secret_key exist?")

try:
    lines = [line.rstrip('\n') for line in open('.config')]
    user = lines[0]
    password = lines[1]
    port_num = int(lines[2]) # port being served on
    engine = create_engine("postgresql://%s:%s@localhost/player2" % (user, password))
    Session = sessionmaker(bind=engine)
    session = Session()

except Exception as exception:
    sys.exit("Couldn't get connection credentials. Does .config exist?")


