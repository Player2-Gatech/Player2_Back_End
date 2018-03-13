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
    image_url = Column('image_url', String(255))
    likes = Column('likes', Integer)
    bio = Column('bio', String(255))

    def __init__(self, email):
        self.email = email

    def as_dict(self):
        return {
            'user_id' : self.user_id,
            'email' : self.email,
            'display_name' : self.display_name,
            'image_url' : self.image_url,
            'likes' : self.likes,
            'bio' : self.bio
        }

    def hash_password(self, password):
        self.password = str(pwd_context.encrypt(password))

    def verify_password(self, password):
        return pwd_context.verify(password, self.password)

    def generate_auth_token(self, expiration = 600):
        s = Serializer(app.config['SECRET_KEY'], expires_in = expiration)
        return s.dumps({ 'id': self.user_id })

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

class Game(Base):
    __tablename__ = 'tb_game'
    game_id = Column('game_id', Integer, primary_key=True)
    title = Column('title', String(128))
    ign_descriptor = Column('ign_descriptor', String(128))

    def as_dict(self):
        return {
            'game_id' : self.game_id,
            'title' : self.title,
            'ign_descriptor' : self.ign_descriptor,
        }

class GameRole(Base):
    __tablename__ = 'tb_game_role'
    game_role_id = Column('game_role_id', Integer, primary_key=True)
    game_id = Column('game_id', Integer, ForeignKey("tb_game.game_id"))
    role = Column('role', String(128))

    def as_dict(self):
        return {
            'role' : self.role
        }

class PlayerGame(Base):
    __tablename__ = 'tb_player_game'
    player_game_id = Column('player_game_id', Integer, primary_key=True)
    game_id = Column('game_id', Integer, ForeignKey("tb_game.game_id"))
    user_id = Column('user_id', Integer, ForeignKey("tb_player.user_id"))
    display_name = Column('display_name', String(128))
    role = Column('role', String(128))
    partner_role = Column('partner_role', String(128))

    def __init__(self, game_id, user_id, display_name, role, partner_role):
        self.game_id = game_id
        self.user_id = user_id
        self.display_name = display_name
        self.role = role
        self.partner_role = partner_role

    def as_dict(self):
        return {
            'user_id' : self.user_id,
            'game_id' : self.game_id,
            'display_name' : self.display_name,
            'role' : self.role,
            'partner_role' : self.partner_role
        }

class PlayerSkill(Base):
    __tablename__ = 'tb_player_skill'
    skill_id = Column('skill_id', Integer, primary_key=True)
    player_game_id = Column('player_game_id', Integer, ForeignKey("tb_player_game.player_game_id"))
    user_id = Column('user_id', Integer, ForeignKey("tb_player.user_id"))
    role = Column('role', String(128))
    role_pick = Column('role_pick', String(128))
    rank = Column('rank', String(128))
    tier = Column('tier', String(128))
    role_wins = Column('role_wins', Integer)
    role_losses = Column('role_losses', Integer)
    wins = Column('wins', Integer)
    losses = Column('losses', Integer)

    def __init__(self, player_game_id, user_id, role, role_pick, rank, tier, role_wins, role_losses, wins, losses):
        self.player_game_id = player_game_id
        self.user_id = user_id
        self.role = role
        self.role_pick = role_pick
        self.rank = rank
        self.tier = tier
        self.role_wins = role_wins
        self.role_losses = role_losses
        self.wins = wins
        self.losses = losses

    def as_dict(self):
        return {
            'player_game_id' : self.player_game_id,
            'user_id' : self.user_id,
            'role' : self.role,
            'role_pick' : self.role_pick,
            'rank' : self.rank,
            'tier' : self.tier,
            'role_wins' : self.role_wins,
            'role_losses' : self.role_losses,
            'wins' : self.wins,
            'losses' : self.losses
        }




