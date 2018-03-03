from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, ForeignKey, Integer, String, Boolean
from passlib.apps import custom_app_context as pwd_context
from itsdangerous import (TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
from config import app

Base = declarative_base()

class Player(Base):
    __tablename__ = 'tb_player'
    user_id = Column('user_id', Integer, primary_key=True)
    email = Column('email', String(128))
    password = Column('password', String(128))
    display_name = Column('display_name', String(128))
    likes = Column('likes', Integer)
    bio = Column('bio', String(255))
    is_searching = Column('is_searching', Boolean, default=False)

    def __init__(self, email):
        self.email = email

    def __repr__(self):
        return "<Player(email=%s)>" % (self.email)

    def as_dict(self):
        return {
            'email' : self.email
        }

    def hash_password(self, password):
        self.password = str(pwd_context.encrypt(password))

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        player = session.query(Player).get(data['id'])

        return player




