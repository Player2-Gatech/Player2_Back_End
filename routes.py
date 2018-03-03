from models import *
from flask import Flask
from flask import Flask, jsonify, abort, make_response, request, g, send_from_directory
from flask_restful import Resource, Api, reqparse, inputs
from flask_httpauth import HTTPBasicAuth
from config import app, session, port_num

auth = HTTPBasicAuth()
my_api = Api(app)

class User(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        # required user parameters
        self.reqparse.add_argument('email', type=str, location='args')
        self.reqparse.add_argument('password', type=str, location='args')

        # reserved for filtering GET requests only
        self.reqparse.add_argument('id', type=str, location='args')
        self.reqparse.add_argument('likes', type=int, location='args')

        # for updating (PUT doesn't exist yet)
        self.reqparse.add_argument('display_name', type=str, location='args')
        self.reqparse.add_argument('is_searching', type=bool, location='args')
        self.reqparse.add_argument('bio', type=str, location='args')

    # registering a new user
    def post(self):
        params = self.reqparse.parse_args()
        if session.query(Player).filter_by(email = params['email']).first() is not None:
            abort(400, "That email already exists!")
        new_player = Player(
            params['email']
        )
        new_player.hash_password(params['password'])

        session.add(new_player)
        session.commit()
        return new_player.as_dict()

    # getting a user via id (expand this later as necessary)
    @auth.login_required
    def get(self):
        params = self.reqparse.parse_args()
        target_id = params['user_id']

        # show all players if no id specified
        if target_id is None:
            # insert possible filter parameters here
            all_players = session.query(Player).all()
            return map(lambda p: p.as_dict(), all_players)
        # otherwise, show specified player
        else:
            target_player = session.query(Player).filter_by(user_id = params['user_id']).first()
            if not target_player:
                abort(400, "No player with id " + str(params['user_id']))
            return jsonify({'email': target_player.email})

# Define resource-based routes here
my_api.add_resource(User, '/api/player', endpoint = 'player')

# Methods for authenticating via tokens
@auth.verify_password
def verify_password(email_or_token, password):
    print email_or_token, password
    # first try to authenticate by token
    verified_player = Player.verify_auth_token(email_or_token)
    if not verified_player:
        # try to authenticate with email/password
        verified_player = session.query(Player).filter_by(email=email_or_token).first()
        if not verified_player or not verified_player.verify_password(password):
            return False
    g.user = verified_player
    return True

@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })

# main server run line
if __name__ == '__main__':
    app.run(debug=True, port = port_num, host = '0.0.0.0')

