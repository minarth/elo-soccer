from collections import defaultdict
from datetime import datetime
from math import log, log2

## MATCH DATA
## {
##    match_date: "",    
##    home_team: "",
##    visiting_team: "",
##    score: "",
##    phase: "",
## }

HOME_COURT_ADV = 100
K = 20
SEASON_COEFF = 2/3

def parse_score(score):
	if type(score) == str:
		score = score.split(":")
		h_s, v_s = int(score[0]),  int(score[1])
	else:
		h_s, v_s = int(score[0]),  int(score[2])
	h_win = h_s > v_s
	tie = h_s == v_s
	v_win = h_s < v_s
	return h_s, v_s, h_win, tie, v_win

##
# Margin of Victory Multiplier = LN(ABS(PD)+1) * (2.2/((ELOW-ELOL)*.001+2.2))
# https://model284.com/model-284-nfl-elo-ratings-methodology/
# https://fivethirtyeight.com/features/introducing-nfl-elo-ratings/
##

def elo_update(match, elos, methodology="583"):
	# h_ is for home team
	# v_ is for visiting team
	h_s, v_s, h_win, tie, v_win = parse_score(match["score"])
	if tie: return elos
	h_elo, v_elo = elos[match["home_team"]], elos[match["visiting_team"]]

	h_exp_s = 1/(1 + 10**((h_elo - v_elo)/400))
	v_exp_s = 1/(1 + 10**((v_elo - h_elo)/400))

	h_pts, v_pts = (1, 0) if h_win else (0, 1)
	winner_elo, looser_elo = (h_elo, v_elo) if h_win else (v_elo, h_elo)

	# 538 methodology
	if methodology == "538":
		# original implementation
		margin_of_victory_multiplier = log(abs(h_s-v_s)+1) * (2.2/((winner_elo-looser_elo)*.001 + 2.2))

	elif methodology == "stuart":
		margin_of_victory_multiplier = log2(1.7*abs(h_s - v_s)) * 2/(2+0.001 * (winner_elo-looser_elo+HOME_COURT_ADV))
	else:
		# STANDARD ELO METHODOLOGY
		margin_of_victory_multiplier = 1.0

	h_upd_elo = h_elo + K*(h_pts - h_exp_s) * margin_of_victory_multiplier
	v_upd_elo = v_elo + K*(v_pts - v_exp_s) * margin_of_victory_multiplier


	elos[match["home_team"]], elos[match["visiting_team"]] = h_upd_elo, v_upd_elo

	return h_elo, v_elo, h_exp_s, v_exp_s, h_upd_elo, v_upd_elo

def update_between_seasons(elos):
	updated = defaultdict(lambda:1500)
	for k, v in elos.items():
		updated[k] = SEASON_COEFF * v + (1-SEASON_COEFF) * 1500
	return updated

def predict(home_team, visiting_team, elos, debug=False):
	if debug: print("H ELO:", elos[home_team], "V ELO:", elos[visiting_team])
	elo_diff = (elos[home_team] + HOME_COURT_ADV) - elos[visiting_team]
	home_pr = 1 / (10**(-elo_diff/400) + 1)
	elo_diff = elos[visiting_team] - (elos[home_team] + HOME_COURT_ADV)
	visiting_pr = 1 / (10**(-elo_diff/400) + 1)

	if debug: print({"home": home_team, "home_elo": elos[home_team], "visitor": visiting_team, "visitor_elo": elos[visiting_team], "home_pr": home_pr})

	return home_pr, visiting_pr
