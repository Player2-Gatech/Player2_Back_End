import random

lol_tiers = {
        'unranked': 0,
        'bronze': 2,
        'silver': 3,
        'gold': 4,
        'platinum': 5,
        'diamond': 6,
        'master': 7,
        'challenger': 8
        }
lol_ranks = {
        'I' : 1,
        'II' : 2,
        'III' : 3,
        'IV' : 4,
        'V' : 5
        }


def sort_matches(target_player, elligible_players):
    scored_players = map(lambda p: compute_similarity(target_player, p), elligible_players)
    #filter out inelligible players
    scored_players = [x for x in scored_players if x['score'] > 0]
    scored_players.sort(key = lambda p: p['score'], reverse = True)
    return scored_players

# player_other will have an additional field called 'score' post method-call
def compute_similarity(player_target, player_other):
    score = 0
    skill_modifier = .7
    role_modifier = .299
    like_modifier = .001

    target_tier = lol_tiers[player_target['playerSkill'][0]['tier'].lower()]
    other_tier = lol_tiers[player_other['playerSkill'][0]['tier'].lower()]
    tier_diff = abs(target_tier - other_tier)

    target_rank = player_target['playerSkill'][0]['rank']
    other_rank = player_target['playerSkill'][0]['rank']

    #filter out players with the same role
    league_game_role_target = [game for game in player_target['playerGameRole'] if game['gameTitle'] == "League of Legends"][0]
    league_game_role_other = [game for game in player_other['playerGameRole'] if game['gameTitle'] == "League of Legends"][0]
    if league_game_role_target['role'] == league_game_role_other['role']:
        player_other['score'] = 0
        return player_other

    #filter out players who are unable to queue together
    if target_tier < 5:
        if tier_diff > 1:
            player_other['score'] = 0
            return player_other
    if target_tier > 4:
        if skill_diff(target_tier, target_rank, other_tier, other_rank) > .75:
            player_other['score'] = 0
            return player_other

    #add skill difference to score
    skill_score = 1 - (skill_diff(target_tier, target_rank, other_tier, other_rank) / 2.0)
    score += skill_score * skill_modifier
    #role preference
    role_score = league_game_role_target['partnerRole'] == league_game_role_other['role']
    score += role_score * role_modifier
    #likeability score
    like_score = player_other['likes'] if player_other['likes'] else 0
    score += like_score * like_modifier

    player_other['score'] = score
    return player_other

def skill_diff(this_tier, this_rank, other_tier, other_rank):
    if this_tier == '':
        this_rank = 5
    else:
        this_rank = lol_ranks[this_rank]
    if other_tier == '':
        other_rank = 5
    else:
        other_rank = lol_ranks[other_rank]

    return abs((this_tier + (1 - this_rank *.2)) - (other_tier + (1 - other_rank *.2)))
