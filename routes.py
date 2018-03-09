import requests
from collections import Counter
from models import *
from flask import json
from flask import Flask, Response, jsonify, abort, make_response, request, g, send_from_directory
from flask_restful import Resource, Api, reqparse, inputs
from flask_httpauth import HTTPBasicAuth
from config import app, session, port_num, riot_key
from werkzeug.exceptions import Unauthorized

auth = HTTPBasicAuth()
my_api = Api(app)

class User(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        # required user parameters
        self.reqparse.add_argument('email', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')

        # reserved for filtering GET requests only
        self.reqparse.add_argument('id', type=str, location='json')
        self.reqparse.add_argument('likes', type=int, location='json')

        # for updating (PUT doesn't exist yet)
        self.reqparse.add_argument('display_name', type=str, location='json')
        self.reqparse.add_argument('is_searching', type=bool, location='json')
        self.reqparse.add_argument('bio', type=str, location='json')

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
        params = {}

        # show all players if no id specified
        if 'user_id' not in params:
            # insert possible filter parameters here
            all_players = session.query(Player).all()
            return map(lambda p: p.as_dict(), all_players)
        # otherwise, show specified player
        else:
            target_player = session.query(Player).filter_by(user_id = params['user_id']).first()
            if not target_player:
                abort(400, "No player with id " + str(params['user_id']))
            return jsonify({'email': target_player.email})

class Skill(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        # required user parameters
        self.reqparse.add_argument('gameTitle',required=True, type=str, location='args')
        self.reqparse.add_argument('displayName', required=True, type=str, location='args')
        self.reqparse.add_argument('role', required=True, type=str, location='args')

    def get(self):
        params = self.reqparse.parse_args()
        display_name = params['displayName']
        game_title = params['gameTitle']
        role = params['role'].lower()

        #input_game = session.query(Game).filter_by(title = game_title).first()
        # just league for now
        if game_title == 'League of Legends':
            return self.handle_league(display_name, role)
        else:
            abort(400, 'Input game is invalid!')

    def handle_league(self, summoner_name, role):
        base_url = 'https://na1.api.riotgames.com/lol'

        # get summoner id
        query_string = str('%s/summoner/v3/summoners/by-name/%s?api_key=%s' % (base_url, summoner_name, riot_key))
        account_info = requests.get(query_string).json()
        account_id = account_info['accountId']
        summoner_id = account_info['id']

        # get win loss and recent win loss by role
        query_string = str('%s/match/v3/matchlists/by-account/%s/recent?api_key=%s' % (base_url, account_id, riot_key))
        r = requests.get(query_string).json()

        wins = losses = role_wins = role_losses = 0
        champs = []
        for game in r['matches']:
            game_id = game['gameId']
            query_string = str('%s/match/v3/matches/%s?api_key=%s' % (base_url, game_id, riot_key))
            game_data = requests.get(query_string).json()
            participant_id = [p['participantId'] for p in game_data['participantIdentities'] if p['player']['accountId'] == account_id][0]
            result = game_data['participants'][participant_id - 1]['stats']['win']
            if result:
                wins += 1
                if game['lane'].lower() == role:
                    role_wins += 1
            else:
                losses += 1
                if game['lane'].lower() == role:
                    role_losses += 1
            champs.append(game_data['participants'][participant_id - 1]['championId'])

        # get summoner rank info
        query_string = str('%s/league/v3/positions/by-summoner/%s?api_key=%s' % (base_url, summoner_id, riot_key))
        summoner_data = requests.get(query_string).json()
        tier = 'Unranked'
        rank = 'Unranked'
        if len(summoner_data) > 0:
            tier = summoner_data[0]['tier']
            rank = summoner_data[0]['rank']

        # get champion name
        role_champ = Counter(champs).most_common(1)[0][0]
        query_string = str('%s/static-data/v3/champions/%s?api_key=%s' % (base_url, role_champ, riot_key))
        role_champ = requests.get(query_string).json()['name']
        return jsonify({ 'wins': wins, 'losses' : losses, 'role_wins' : role_wins, 'role_losses' : role_losses, 'role_champ' : role_champ, 'tier' : tier, 'rank' : rank})


# Define resource-based routes here
my_api.add_resource(User, '/api/player', endpoint = 'player')
my_api.add_resource(Skill, '/api/skill', endpoint = 'skill')

# Methods for authenticating via tokens
@auth.verify_password
def verify_password(email_or_token, password):
    # first try to authenticate by token
    verified_player = Player.verify_auth_token(email_or_token)
    if not verified_player:
        # try to authenticate with email/password
        verified_player = session.query(Player).filter_by(email=email_or_token).first()
        if not verified_player or not verified_player.verify_password(password):
	    abort(401, 'Unauthorized')
            return False
    g.user = verified_player
    return True


@app.errorhandler(401)
def custom_401(error):
    return Response(json.dumps({'message' : 'Unauthorized'}), 401)

@app.route('/api/token')
@auth.login_required
def get_auth_token():
    token = g.user.generate_auth_token()
    return jsonify({ 'token': token.decode('ascii') })

# main server run line
if __name__ == '__main__':
    app.run(debug=True, port = port_num, host = '0.0.0.0')

