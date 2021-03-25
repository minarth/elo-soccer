# -*- coding: utf-8 -*-

# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import colorlover
import dash
import dash_table
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import dash_html_components as html
import plotly.express as px
import pandas as pd

from elo_calc import historical_prep, calculate_this_season


def get_difference_str(starting_elo, current_elo):
    diff = current_elo - starting_elo
    return "+" + str(diff) if diff >= 0 else str(diff)

def generate_data():
    elos = historical_prep()
    
    estimates, hist_elos, teams = calculate_this_season(elos)

    starting_elos = [{"team": k, "starting_elo": round(v), "current_elo": round(elos[k]), "difference": get_difference_str(round(v), round(elos[k]))} 
        for k,v in historical_prep().items() if k in teams]

    return starting_elos, estimates


def get_probability_cell_colors(value, n_bins=9):
    bounds = [i * (1.0 / n_bins) for i in range(n_bins + 1)]
    bounds = [(down, up) for down, up in zip(bounds[:-1], bounds[1:])]

    colors = colorlover.scales[str(n_bins)]['seq']['Blues']

    for i, (down, up) in enumerate(bounds):
        if down <= value < up: return {"backgroundColor": colors[i], "color": "white" if i > n_bins / 2 else "inherit"}

    return {"backgroundColor": colors[-1], "color": "white"}  # it's getting dark


def create_app():
    elos, estimates = generate_data()

    tables = []
    successes, predictions, ties = 0, 0, 0
    for est in estimates:

        match_tables = []
        for match in est["matches"]:
            
            table_header = [
                html.Thead(html.Tr([html.Th("Team", style={"width": "35%"}), html.Th("ELO"), 
                    html.Th("WIN prob."), html.Th("", style={"width": "10%"}), html.Th("Score")], className="text-muted"))
            ]
            home_tick_cell = html.Td("", style={"font-size": "1em"}, className="bi bi-check2") if match["home_win"] else html.Td("")
            home_score_style = "font-weight-bold" if match["home_win"] else ""
            home_row = html.Tr([html.Td(match["home"]), html.Td(match["home_elo"]), html.Td(match["home_pr"], 
                style=get_probability_cell_colors(match["home_pr"])), home_tick_cell, 
            html.Td(match["home_score"], className=home_score_style)])

            visitor_tick_cell = html.Td("", style={"font-size": "1em"}, className="bi bi-check2") if match["visiting_win"] else html.Td("")
            visiting_score_style = "font-weight-bold" if match["visiting_win"] else ""
            visitor_row = html.Tr([html.Td(match["visitor"]), html.Td(match["visiting_elo"]), html.Td(match["visiting_pr"], 
                style=get_probability_cell_colors(match["visiting_pr"])), visitor_tick_cell, 
            html.Td(match["visiting_score"], className=visiting_score_style)])

            table_body = [html.Tbody([home_row, visitor_row])]

            match_tables.append(dbc.Col(dbc.Card(children=[dbc.Table(table_header + table_body, bordered=False, className="mb-0"), 
                html.Span(f"Match date: {match['date']}", className="mr-2 text-muted", style={"alignSelf": "end"})]), md=6, className="mb-2"))


        tables.append(html.Div(children=[
                dbc.Row([
                    dbc.Col(html.H1(est["round"]), align="center")
                ]),
                dbc.Row(
                    match_tables,
                    className="mb-4"
                ),
            ]))

        successes += est["successes"] 
        predictions += est["predictions"]
        ties += est["ties"]
    

    return dbc.Container(children=[
            html.Div(
                children=[
                    html.H1(
                        children="⚽ Czech Football League ELO", className="header-title"
                    ),
                    html.P(
                        children="Calculate the elo for first league teams"
                        " and try to predict upcoming events."
                        " (everything automated). Here is description of the dashboard (TODO LINK).",
                        className="header-description",
                    ),

                    html.P(
                        children=f"ELO prediction capabilities: {successes} successfull predicitons out of {predictions} matches (with {ties} ties) => {round(successes / predictions, 2)} current success rate ({round(successes / (predictions-ties), 2)} without ties)",
                        className="header-description"
                    ),
                ],
                className="header",
            ),

            html.Div(children=[
                dbc.Card(children=
                    
                        dash_table.DataTable(
                            data=elos,
                            columns=[{"id": "team", "name": "Team"}, {"id": "starting_elo", "name": "Start of season ELO"}, 
                                {"id": "current_elo", "name": "Current ELO"},],
                            #css=[{"fontFamily": '"-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans", "Liberation Sans", "sans-serif", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji" !default'}],
                            style_cell={'textAlign': 'left', "paddingLeft": "12px", "font-family": ["-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "Helvetica Neue", "Arial", "Noto Sans", "Liberation Sans", "sans-serif", "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji"]},
                            sort_action="native",
                            sort_by=[{"column_id": "current_elo", "direction": "desc"}],
                            style_data_conditional=[
                                {
                                    'if': {'row_index': 'odd'},
                                    'backgroundColor': 'rgb(248, 248, 248)'
                                }
                            ],
                            style_header={
                                'backgroundColor': 'rgb(230, 230, 230)',
                                'fontWeight': 'bold'
                            },
                            style_as_list_view=True,
                            cell_selectable=False
                        ), 
                    className="mb-3"
                ),
                
                ] + tables,
            ),
        ],
        className="p-5",
    )


#external_stylesheets = ["https://cdn.jsdelivr.net/npm/bootstrap@4.6.0/dist/css/bootstrap.min.css"]
#app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app = dash.Dash(__name__, assets_external_path='https://george.mnch.cz/elo-soccer/',requests_pathname_prefix="/elo-soccer/", external_stylesheets=[dbc.themes.BOOTSTRAP, "https://cdn.jsdelivr.net/npm/bootstrap-icons@1.3.0/font/bootstrap-icons.css"])

app.title = "Czech football league ELO dashboard"

app.layout = create_app

server = app.server

if __name__ == '__main__':
    app.run_server(debug=True, port=6000)
