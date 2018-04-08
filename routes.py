import requests
from collections import Counter
from models import *
from flask import json
from flask import Flask, Response, jsonify, abort, make_response, request, g, send_from_directory
from flask_restful import Resource, Api, reqparse, inputs
from flask_httpauth import HTTPBasicAuth
from config import app, session, port_num, riot_key
from werkzeug.exceptions import Unauthorized
from matching import sort_matches

auth = HTTPBasicAuth()
my_api = Api(app)

class User(Resource):
    def __init__(self):
        # used for auth
        self.reqparse = reqparse.RequestParser()

        self.reqparse.add_argument('email', type=str, location='json')
        self.reqparse.add_argument('password', type=str, location='json')

        # used for updating user porfile info
        self.profile_put_reqparse = reqparse.RequestParser()

        self.profile_put_reqparse.add_argument('displayName', type=str, location='json', required=False)
        self.profile_put_reqparse.add_argument('profilePhoto', type=str, location='json', required=False)
        self.profile_put_reqparse.add_argument('bio', type=str, location='json', required=False)
        self.profile_put_reqparse.add_argument('playerGameRole', type=dict, location='json', required=False)

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
        target_player = g.user
        return target_player.as_dict()

    @auth.login_required
    def put(self):
        params = self.profile_put_reqparse.parse_args()
        target_player = g.user
        # update user if appropriate info exists
        if params['bio'] is not None:
            target_player.bio = params['bio']
        if params['profilePhoto'] is not None:
            target_player.profile_photo = params['profilePhoto']
        if params['displayName'] is not None:
            target_player.display_name = params['displayName']
        target_id = target_player.user_id
        updated_player_games = []
        if params['playerGameRole'] is not None:
            game = params['playerGameRole']
            target_game_id = session.query(Game).filter_by(title = game['gameTitle'])
            target_player_game = session.query(PlayerGame).filter(PlayerGame.user_id == target_id and PlayerGame.game_id == target_game_id).first()
            if target_player_game is None:
                abort(400, 'The user is currently not associated with one of the games you are trying to update. Add that game for the user first!')
            target_player_game.display_name = game['displayName']
            target_player_game.role = game['role']
            target_player_game.partner_role = game['partnerRole']
            updated_player_games.append(target_player_game.as_dict())

        session.commit()
        return jsonify({'updatedPlayer' : target_player.as_dict(), 'updatedGames' : updated_player_games})


class Games(Resource):

    def get(self):
        games = session.query(Game).all()
        all_games = []
        for i, game in enumerate(games):
            game = game.as_dict()
            roles = session.query(Game, GameRole).filter(Game.title == game['title']).filter(Game.game_id == GameRole.game_id).all()
            roles_list = map(lambda r: r[1].as_dict()['role'], roles)
            game['roles'] = roles_list
            all_games.append(game)
        return jsonify({'games': all_games})


class UserGame(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('gameTitle',required=True, type=str, location='json')
        self.reqparse.add_argument('displayName',required=True, type=str, location='json')
        self.reqparse.add_argument('role',required=True, type=str, location='json')
        self.reqparse.add_argument('partnerRole',required=True, type=str, location='json')

    @auth.login_required
    def get(self):
        user_games = session.query(PlayerGame).filter_by(user_id = g.user.user_id).all()
        user_games = map(lambda p: p.as_dict(), user_games)
        return jsonify({'userGames' : user_games})

    @auth.login_required
    def post(self):
        params = self.reqparse.parse_args()
        user = g.user
        game = session.query(Game).filter_by(title = params['gameTitle']).first()
        if game is None:
            abort(400, "Not a valid game title!")
        user_id = user.user_id
        game_id = game.game_id
        display_name = params['displayName']
        role = params['role']
        partner_role = params['partnerRole']

        try:
            new_player_game = PlayerGame(game_id, user_id, display_name, role, partner_role)
            session.add(new_player_game)
            session.commit()
            return jsonify({'Player_Game': new_player_game.as_dict()})
        except Exception as e:
            print e
            session.rollback()
            # Should not be able to get here
            abort(400, "Something went wrong")


class UserSkill(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()

        # this param should only be used for an update cronjob
        self.reqparse.add_argument('update',required=False, type=bool, location='args')

    @auth.login_required
    def get(self):
        params = self.reqparse.parse_args()
        user_id = g.user.user_id

        player_games = session.query(PlayerGame).filter_by(user_id = user_id).all()
        if player_games is None:
            abort(400, 'This player currently has no games!')
        for player_game in player_games:
            game = session.query(Game).filter_by(game_id = player_game.game_id).first()
            if game.title == 'League of Legends':
                updateable_query = session.query(PlayerSkill).filter_by(player_game_id = player_game.player_game_id)
                existing_skills = updateable_query.first()
                if params['update'] or existing_skills is None:
                    return self.handle_league(player_game.display_name, player_game.role, player_game.player_game_id, user_id, existing_skills is not None and params['update'], updateable_query)
                else:
                    return jsonify({'playerSkill': existing_skills.as_dict()})

    def handle_league(self, summoner_name, role, player_game_id, user_id, shouldUpdate, updateable_query):
        base_url = 'https://na1.api.riotgames.com/lol'

        # get summoner id
        query_string = str('%s/summoner/v3/summoners/by-name/%s?api_key=%s' % (base_url, summoner_name, riot_key))
        account_info = requests.get(query_string).json()
        if 'accountId' not in  account_info.keys():
            abort(500, 'Either the server needs to regenerate its API Key, or the summoner name is invalid')
        account_id = account_info['accountId']
        summoner_id = account_info['id']

        # get win loss and recent win loss by role
        query_string = str('%s/match/v3/matchlists/by-account/%s/recent?api_key=%s' % (base_url, account_id, riot_key))
        r = requests.get(query_string).json()
        if 'matches' not in r.keys():
            abort(500, 'No games found for this user!')

        wins = losses = role_wins = role_losses = 0
        champs = []
        for game in r['matches']:
            game_id = game['gameId']
            query_string = str('%s/match/v3/matches/%s?api_key=%s' % (base_url, game_id, riot_key))
            game_data = requests.get(query_string).json()
            participant_id = [p['participantId'] for p in game_data['participantIdentities'] if p['player']['accountId'] == account_id][0]
            result = game_data['participants'][participant_id - 1]['stats']['win']
            game_role = game['lane'].lower()
            role = role.lower()
            if result:
                wins += 1
                if (game_role == role) or (game_role in role):
                    role_wins += 1
            else:
                losses += 1
                if (game_role == role) or (game_role in role):
                    role_losses += 1
            champs.append(game_data['participants'][participant_id - 1]['championId'])

        # get summoner rank info
        query_string = str('%s/league/v3/positions/by-summoner/%s?api_key=%s' % (base_url, summoner_id, riot_key))
        summoner_data = requests.get(query_string).json()
        tier = 'Unranked'
        rank = ''
        if len(summoner_data) > 0:
            tier = summoner_data[0]['tier']
            rank = summoner_data[0]['rank']

        # get champion name
        champ_map = json.load(open('champion_cache.json'))
        role_champ = Counter(champs).most_common(1)[0][0]
        role_champ = [champ_map['data'][key]['name'] for key in champ_map['data'] if champ_map['data'][key]['id'] == role_champ][0]

        # update or place in database
        retrieved_stats = PlayerSkill(player_game_id, user_id, role, role_champ, rank, tier, role_wins, role_losses, wins, losses)
        if (shouldUpdate):
            updateable_query.update(retrieved_stats.as_update_dict())
        else:
            session.add(retrieved_stats)
        session.commit()

        return jsonify({'playerSkill': retrieved_stats.as_dict()})

class UserMatches(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('gameTitle',required=True, type=str, location='args')

    @auth.login_required
    def get(self):
        params = self.reqparse.parse_args()
        # retrieve other users who play the same game and call similarity function
        all_players = session.query(Player, PlayerGame, Game).filter(Player.user_id != g.user.user_id).filter(Player.user_id == PlayerGame.user_id).filter(PlayerGame.game_id == Game.game_id).filter(Game.title == params['gameTitle']).all()
        player_friends = session.query(PlayerFriend).filter(PlayerFriend.user_id_a == g.user.user_id or PlayerFriend.user_id_b == g.user.user_id).all()
        player_friendsA = list(map(lambda p: p.as_dict()['idA'], player_friends))
        player_friendsB = list(map(lambda p: p.as_dict()['idB'], player_friends))
        player_friends = player_friendsA + player_friendsB

        eligible_players = map(lambda p: p[0].as_dict(), all_players)
        eligible_players = [p for p in eligible_players if len(p['playerSkill']) > 0 and p['user_id'] not in player_friends]
        top_matches = sort_matches(g.user.as_dict(), eligible_players)
        # these matches are a sorted list of players with an additional 'score' field, representing the strength of the matching
        return jsonify({'matches': top_matches})

class UserComment(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('userId', required=True)
        self.reqparse.add_argument('message', required=True)
        self.reqparse.add_argument('rating', required=True)

    @auth.login_required
    def post(self):
        params = self.reqparse.parse_args()
        commenter = g.user.display_name if g.user.display_name else "Anonymous"
        user_id = params['userId']
        message = params['message']
        rating = params['rating']

        new_comment = PlayerComment(user_id, commenter, message, rating)
        session.add(new_comment)
        session.commit()
        return new_comment.as_dict()



class UserVideo(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('videoUrl', required=True, type=str, location='json')

    @auth.login_required
    def put(self):
        params = self.reqparse.parse_args()
        user_id = g.user.user_id
        current_video = session.query(PlayerVideo).filter_by(user_id = user_id).first()
        if current_video:
            current_video.video_url = params['videoUrl']
        else:
            current_video = PlayerVideo(user_id, params['videoUrl'])
            session.add(current_video)
        session.commit()
        return current_video.as_dict()

class UserFriends(Resource):
    def __init__(self):
        self.reqparse = reqparse.RequestParser()
        self.reqparse.add_argument('matchUserId', required=True, type=int, location='json')
        self.reqparse.add_argument('pending', required=True, type=bool, location='json')
        self.reqparse.add_argument('delete', required=False, type=bool, location='json')
        self.reqparse.add_argument('retUpdated', required=False, type=bool, location='json')

    @auth.login_required
    def put(self):
        params = self.reqparse.parse_args()
        user_id_a = None
        user_id_b = None
        new_friendship = None

        if params['matchUserId'] == g.user.user_id:
            abort(400, 'The matchingUserId is the same as the authenticated user id!')
        # Adding a non-pending request should either update the table or add the bidirectional edge
        if params['delete']:
            current_friendship = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, user_id_b = params['matchUserId']).first()
            if current_friendship:
                session.delete(current_friendship)
                session.commit()
                return "Deleted friendship"
            else:
                abort(400, 'Friendship to delete does not exist.')

        if not params['pending']:
            current_friendship = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, user_id_b = params['matchUserId']).first()
            if current_friendship:
                current_friendship.pending = False
            user_id_a = g.user.user_id
            user_id_b = params['matchUserId']
            new_friendship = PlayerFriend(user_id_a, user_id_b, False)
        else:
            user_id_a = params['matchUserId']
            user_id_b = g.user.user_id
            new_friendship = PlayerFriend(user_id_a, user_id_b, True)
        session.add(new_friendship)
        session.commit()

        if params['retUpdated']:
            player_friends = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, pending = False).all()
            player_friends = map(lambda x: x.as_dict(), player_friends)

            pending_friends = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, pending = True).all()
            pending_friends = map(lambda x: x.as_dict(), pending_friends)

            return jsonify({"friends" : player_friends, "pending" : pending_friends})
        else:
            return new_friendship.as_dict()

    @auth.login_required
    def get(self):
        player_friends = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, pending = False).all()
        player_friends = map(lambda x: x.as_dict(), player_friends)

        pending_friends = session.query(PlayerFriend).filter_by(user_id_a = g.user.user_id, pending = True).all()
        pending_friends = map(lambda x: x.as_dict(), pending_friends)

        return jsonify({"friends" : player_friends, "pending" : pending_friends})


# Define resource-based routes here
my_api.add_resource(User, '/api/player', endpoint = 'player')
my_api.add_resource(Games, '/api/games', endpoint = 'games')
my_api.add_resource(UserGame, '/api/playerGame', endpoint = 'playerGame')
my_api.add_resource(UserComment, '/api/playerComment', endpoint = 'playerComment')
my_api.add_resource(UserVideo, '/api/playerVideo', endpoint = 'playerVideo')
my_api.add_resource(UserFriends, '/api/playerFriends', endpoint = 'playerFriends')
my_api.add_resource(UserSkill, '/api/playerSkill', endpoint = 'skill')
my_api.add_resource(UserMatches, '/api/matches', endpoint = 'matches')

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

