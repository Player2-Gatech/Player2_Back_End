import random

def sort_matches(target_player, elligible_players):

     scored_players = map(lambda p: compute_similarity(target_player, p), elligible_players)
     scored_players.sort(key = lambda p: p['score'], reverse = True)
     return scored_players

# player_other will have an additional field called 'score' post method-call
def compute_similarity(player_target, player_other):
    player_other['score'] = random.uniform(0, 1)
    return player_other



