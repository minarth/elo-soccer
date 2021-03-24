from elo_lib import elo_update, update_between_seasons, predict, parse_score
from collections import defaultdict
import json, pickle
from datetime import datetime
from copy import deepcopy

def translate(team_name):

    translate = {}
    translate["Dukla"] = 'FK Dukla Praha'
    translate["Plzeň"] = 'FC Viktoria Plzeň'
    translate["Zlín"] = 'FC Fastav Zlín'
    translate["Mladá Boleslav"] = 'FK Mladá Boleslav'
    translate["Liberec"] = 'FC Slovan Liberec'
    translate["Karviná"] = 'MFK Karviná'
    translate["Sparta"] = 'AC Sparta Praha'
    translate["Opava"] = 'SFC Opava'
    translate["Bohemians 1905"] = 'Bohemians 1905'
    translate["Slovácko"] = '1. FC Slovácko'
    translate["Olomouc"] = 'SK Sigma Olomouc'
    translate["Slavia"] = 'SK Slavia Praha'
    translate["Ostrava"] = 'FC Baník Ostrava'
    translate["Jablonec"] = 'FK Jablonec'
    translate["Příbram"] = '1. FK Příbram'
    translate["Teplice"] = 'FK Teplice'
    translate["Jihlava"] = 'FC Vysočina Jihlava'
    translate["Č. Budějovice"] = 'SK České Budějovice'
    translate["Brno"] = 'FC Zbrojovka Brno'
    translate["Pardubice"] = 'FK Pardubice'
    return translate[team_name]

def historical_prep():
    starting_elos = defaultdict(lambda:1500)

    with open("../data/2018-19.json", "r") as f_in:
        first_season = json.load(f_in)
        for dato in first_season:
            dato["match_date"] = datetime.strptime(dato["match_date"], '%Y-%m-%d %H:%M:%S')
        first_season = sorted(first_season, key=lambda k: k['match_date']) 

    with open("../data/2019-20.json", "r") as f_in:
        second_season = json.load(f_in)
        for dato in second_season:
            dato["match_date"] = datetime.strptime(dato["match_date"], '%Y-%m-%d %H:%M:%S')
        second_season = sorted(second_season, key=lambda k: k['match_date']) 

    all_matches = first_season + second_season

    for match in first_season:
        elo_update(match, starting_elos)

    elos = update_between_seasons(starting_elos)

    for match in second_season:
        elo_update(match, elos)

    elos = update_between_seasons(elos)

    return elos


def calculate_round(elos, rnd):
    #rnd = data[0]
    # Predict whole round
    successes, predictions, ties = 0, 0, 0
    for match in rnd["matches"]:
        home_pr, visiting_pr = predict(translate(match["home"]), translate(match["visitor"]), elos)
        match["home_elo"], match["visiting_elo"] = elos[translate(match["home"])], elos[translate(match["visitor"])]
        match["home_pr"], match["visiting_pr"] = home_pr, visiting_pr
        match["prediction"] = "HOME" if home_pr > visiting_pr else "VISITOR"
        match["success"], match["home_score"], match["visiting_score"], match["home_win"], match["visiting_win"] = None, "", "", False, False
        if "result" in match:
            h_s, v_s, h_win, tie, v_win = parse_score(match["result"])
            match["home_score"] = h_s
            match["home_win"] = h_win
            match["visiting_score"] = v_s
            match["visiting_win"] = v_win
            match["success"] = False
            match["success"] = (h_win and home_pr > visiting_pr) or (v_win and home_pr < visiting_pr)
            successes += 1 if (h_win and home_pr > visiting_pr) or (v_win and home_pr < visiting_pr) else 0
            predictions += 1
            ties += 1 if tie else 0
            match["success_emoji"] = "✅" if match["success"] else "❌" 
            match["success_emoji"] = "~" if tie else match["success_emoji"]
    rnd["successes"] = successes
    rnd["predictions"] = predictions
    rnd["ties"] = ties
    # Update elo for whole round
    # (if possible)
    for match in rnd["matches"]:
        if "result" in match:
            elo_update({"home_team": translate(match["home"]), "visiting_team": translate(match["visitor"]), "score": match["result"]}, elos)

def prettify_data(data):
    for rnd in data:
        
        for match in rnd["matches"]:
            match["home_elo"] = round(match["home_elo"], 0)
            match["visiting_elo"] = round(match["visiting_elo"], 0)
            match["home_pr"] = round(match["home_pr"], 2)
            match["visiting_pr"] = round(match["visiting_pr"], 2)

    return data

def get_current_season_teams(data):
    teams = []
    for rnd in data:
        for match in rnd["matches"]:
            teams.append(translate(match["home"]))
            teams.append(translate(match["visitor"]))

    return set(teams)


def calculate_this_season(elos, filename="../data/parsed-data.pickle", get_elo_history=False):
    with open(filename, "rb") as f:
        data = pickle.load(f)
    
    hist_elos = []
    if get_elo_history:    
        hist_elos.append(deepcopy(elos))
    for rnd in data:
        calculate_round(elos, rnd)
        if rnd["predictions"] > 0 and get_elo_history: hist_elos.append(deepcopy(elos))

    return prettify_data(data), hist_elos, get_current_season_teams(data)

if __name__ == '__main__':
    historical_prep()