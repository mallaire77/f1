from sessions_data import PracticeSessionData, PracticeSessionsData
from historical_data import HistoricalData

import fastf1 as f1

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import datetime as dt
from typing import List

f1.Cache.enable_cache('./.cache')
# f1.Cache.offline_mode(True)

year = 2024

calendar = [
    {'name': 'Bahrain Grand Prix', 'city': 'Sakhir', 'timezone': 'Etc/GMT+3', 'date': '2024-03-02'},
    {'name': 'Saudi Arabian Grand Prix', 'city': 'Jeddah', 'timezone': 'Etc/GMT+3', 'date': '2024-03-09'},
    {'name': 'Australian Grand Prix', 'city': 'Melbourne', 'timezone': 'Etc/GMT+11', 'date': '2024-03-24'},
    {'name': 'Japanese Grand Prix', 'city': 'Suzuka', 'timezone': 'Etc/GMT+9', 'date': '2024-04-07'},
    {'name': 'Chinese Grand Prix', 'city': 'Shanghai', 'timezone': 'Etc/GMT+8', 'date': '2024-04-21'},
    {'name': 'Miami Grand Prix', 'city': 'Miami', 'timezone': 'Etc/GMT-5', 'date': '2024-05-05'},
    {'name': 'Emilia Romagna Grand Prix', 'city': 'Imola', 'timezone': 'Etc/GMT+1', 'date': '2024-05-19'},
    {'name': 'Monaco Grand Prix', 'city': 'Monaco', 'timezone': 'Etc/GMT+1', 'date': '2024-05-26'},
    {'name': 'Canadian Grand Prix', 'city': 'Montreal', 'timezone': 'Etc/GMT-5', 'date': '2024-06-09'},
    {'name': 'Spanish Grand Prix', 'city': 'Barcelona-Catalunya', 'timezone': 'Etc/GMT+1', 'date': '2024-06-23'},
    {'name': 'Austrian Grand Prix', 'city': 'Spielberg', 'timezone': 'Etc/GMT+1', 'date': '2024-06-30'},
    {'name': 'British Grand Prix', 'city': 'Silverstone', 'timezone': 'Etc/GMT', 'date': '2024-07-07'},
    {'name': 'Hungarian Grand Prix', 'city': 'Budapest', 'timezone': 'Etc/GMT+1', 'date': '2024-07-21'},
    {'name': 'Belgium Grand Prix', 'city': 'Spa', 'timezone': 'Etc/GMT+1', 'date': '2024-07-28'},
    {'name': 'Dutch Grand Prix', 'city': 'Zandvoort', 'timezone': 'Etc/GMT+1', 'date': '2024-08-25'},
    {'name': 'Italian Grand Prix', 'city': 'Monza', 'timezone': 'Etc/GMT+1', 'date': '2024-09-01'},
    {'name': 'Azerbaijan Grand Prix', 'city': 'Baku', 'timezone': 'Etc/GMT+4', 'date': '2024-09-15'}, 
    {'name': 'Singapore Grand Prix', 'city': 'Singapore', 'timezone': 'Etc/GMT+8', 'date': '2024-09-22'},
    {'name': 'United States Grand Prix', 'city': 'Austin', 'timezone': 'Etc/GMT-6', 'date': '2024-10-20'},
    {'name': 'Mexican Grand Prix', 'city': 'Mexico City', 'timezone': 'Etc/GMT-6', 'date': '2024-10-27'},
    {'name': 'Brazilian Grand Prix', 'city': 'Sao Paulo', 'timezone': 'Etc/GMT-3', 'date': '2024-11-03'},
    {'name': 'Las Vegas Grand Prix', 'city': 'Las Vegas', 'timezone': 'Etc/GMT-8', 'date': '2024-11-24'},
    {'name': 'Qatar Grand Prix', 'city': 'Lusail', 'timezone': 'Etc/GMT+3', 'date': '2024-12-01'},
    {'name': 'Abu Dhabi Grand Prix', 'city': 'Yas Marina', 'timezone': 'Etc/GMT+4', 'date': '2024-12-08'}
]

gps = []
for gp in calendar: 
    gps.append(gp['name'])

clusters = {
    'adventure_trio': ['azerbaijan-grand-prix','las-vegas-grand-prix','saudi-arabian-grand-prix'],
    'spicy_mix': ['bahrain-grand-prix','chinese-grand-prix','hungarian-grand-prix','mexican-grand-prix','singapore-grand-prix'],
    'global_tour': ['abu-dhabi-grand-prix','canadian-grand-prix','qatar-grand-prix','united-states-grand-prix'],
    'european_delights': ['austrian-grand-prix','brazilian-grand-prix','italian-grand-prix'],
    'down_under_and_beyond': ['australian-grand-prix','emilia-romagna-grand-prix'],
    'racing_jewel': ['monaco-grand-prix'],
    'classic_curcuits': ['belgium-grand-prix','british-grand-prix','japanese-grand-prix','miami-grand-prix'],
    'lowlands_and_iberian_peninsula': ['dutch-grand-prix','spanish-grand-prix']
}

clusters_by_track = {}
for cluster in clusters:
    for circuit in clusters[cluster]:
        clusters_by_track[circuit] = cluster

teams = [
    {'name':'redbull','colour':'#3671C6'},
    {'name':'mercedes','colour':'#27F4D2'},
    {'name':'ferrari','colour':'#E8002D'},
    {'name':'mclaren','colour':'#FF8000'},
    {'name':'astonmartin','colour':'#229971'},
    {'name':'alpine','colour':'#FF87BC'},
    {'name':'williams','colour':'#65C4FF'},
    {'name':'rb','colour':'#6692FF'},
    {'name':'sauber','colour':'#51e253'},
    {'name':'haas','colour':'#B6BABD'},
]

drivers = [
    {'name':'MAX VERSTAPPEN','abv':'VER','team':'redbull'},
    {'name':'SERGIO PEREZ','abv':'PER','team':'redbull'},
    {'name':'LEWIS HAMILTON','abv':'HAM','team':'mercedes'},
    {'name':'GEORGE RUSSELL','abv':'RUS','team':'mercedes'},
    {'name':'CHARLES LECLERC','abv':'LEC','team':'ferrari'},
    {'name':'CARLOS SAINZ','abv':'SAI','team':'ferrari'},
    {'name':'LANDO NORRIS','abv':'NOR','team':'mclaren'},
    {'name':'OSCAR PIASTRI','abv':'PIA','team':'mclaren'},
    {'name':'FERNANDO ALONSO','abv':'ALO','team':'astonmartin'},
    {'name':'LANCE STROLL','abv':'STR','team':'astonmartin'},
    {'name':'ESTEBAN OCON','abv':'OCO','team':'alpine'},
    {'name':'PIERRE GASLY','abv':'GAS','team':'alpine'},
    {'name':'ALEX ALBON','abv':'ALB','team':'williams'},
    {'name':'LOGAN SARGENT','abv':'SAR','team':'williams'},
    {'name':'DANIEL RICCIARDO','abv':'RIC','team':'rb'},
    {'name':'YUKI TSUNODA','abv':'TSU','team':'rb'},
    {'name':'VALTTERI BOTTAS','abv':'BOT','team':'sauber'},
    {'name':'GUANYU ZHOU','abv':'ZHO','team':'sauber'},
    {'name':'KEVIN MAGNUSSEN','abv':'MAG','team':'haas'},
    {'name':'NICO HULKENBERG','abv':'HUL','team':'haas'},
    {'name':'AYUMU IWASA','abv':'IWA','team':'rb'},
    {'name':'OLIVER BEARMAN','abv':'BEA','team':'haas'}
]

practice_sessions = [
    'FP1',
    'FP2',
    'FP3'
]

def format_lap_time(milliseconds):
    minutes = int(milliseconds // 60000)
    seconds = int((milliseconds % 60000) // 1000)
    milliseconds = milliseconds % 1000
    return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

def key(gp: str): 
    return gp.lower().replace(" ", "-")

def sanitize_key(gp: str): 
    return gp.replace("_", " ").replace("-", " ").title()

def get_gp(gp: str):
    return next(((gp_idx, inner_gp) for gp_idx, inner_gp in enumerate(calendar) if inner_gp['name'] == sanitize_key(gp)))

def get_gp_cluster(gp: str):
    return clusters_by_track[key(gp)]

def get_similar_gps(gp: str):
    gp_cluster = get_gp_cluster(gp)
    similar_gps = []
    for similar_gp in clusters[gp_cluster]:
        similar_gp_idx, similar_gp = get_gp(similar_gp)
        similar_gps.append((similar_gp_idx, similar_gp['name']))
    return similar_gps

def get_team_colour(team: str):
    return next((inner_team for inner_team in teams if inner_team['name'] == team))['colour']

def get_driver_colour(driver: str):
    inner_driver = next((inner_driver for inner_driver in drivers if inner_driver['abv'] == driver))
    return get_team_colour(inner_driver['team'])

def get_compound_colour(compound: str):
    if (compound == 'SOFT'):
        return '#ed919a'
    elif (compound == 'MEDIUM'):
        return '#e8d695'
    elif (compound == 'HARD'):
        return '#dcdadb'
    elif (compound == 'INTERMEDIATE'):
        return '#97bda2'
    elif (compound == 'WET'):
        return '#809dd1'
    else:
        return '#fffff'
    
def convert_strategy_to_html(strategy: str):
    strategy_html = []
    for compound in strategy:
        if compound.lower() == 's':
            strategy_html.append(html.Img(src="/assets/soft.png", width="46", height="46"))
        elif compound.lower() == 'm':
            strategy_html.append(html.Img(src="/assets/medium.png", width="46", height="46"))
        elif compound.lower() == 'h':
            strategy_html.append(html.Img(src="/assets/hard.png", width="46", height="46"))
        elif compound.lower() == 'i':
            strategy_html.append(html.Img(src="/assets/intermediate.png", width="46", height="46"))
        elif compound.lower() == 'w':
            strategy_html.append(html.Img(src="/assets/wet.png", width="46", height="46"))
        else:
            pass
    return strategy_html

def get_upcoming_gp():
    datetime_array = [dt.datetime.fromisoformat(event['date']) for event in calendar]
    today = dt.datetime.today()
    future_dates = [date for date in datetime_array if date > today]
    future_dates.sort()
    return datetime_array.index(future_dates[0]), calendar[datetime_array.index(future_dates[0])]

def get_historical_data(gp) -> HistoricalData:
    previous_results = []
    # similar_results_current_year = []
    # similar_results_previous_year = []

    # gp_idx, gp = get_gp(gp)
    # similar_gps = get_similar_gps(gp['name'])

    #Previous GPs
    # for i in range(gp_idx):
    #     previous_gp = calendar[i]['name']
    #     previous_gp_session = f1.get_session(year, previous_gp, 'race')
    #     previous_gp_session.load(laps=False, telemetry=False, weather=False, messages=False)
    #     previous_gp_session_results = previous_gp_session.results
    #     previous_gp_session_results['GrandPrix'] = previous_gp
    #     previous_results.append(previous_gp_session_results)

    #Similar Tracks Results (current year)
    # for similar_gp_idx, similar_gp in similar_gps:
    #     if (similar_gp_idx < gp_idx):
    #         similar_gp_session = f1.get_session(year, similar_gp, 'race')
    #         similar_gp_session.load(laps=False, telemetry=False, weather=False, messages=False)
    #         similar_gp_session_results = similar_gp_session.results
    #         similar_gp_session_results['GrandPrix'] = similar_gp
    #         similar_results_current_year.append(similar_gp_session_results)
    
    #Similar Tracks Results (previous year)
    # for similar_gp_idx, similar_gp in similar_gps:
    #     similar_gp_session = f1.get_session(year - 1, similar_gp, 'race')
    #     similar_gp_session.load(laps=False, telemetry=False, weather=False, messages=False)
    #     similar_gp_session_results = similar_gp_session.results
    #     similar_gp_session_results['GrandPrix'] = similar_gp
    #     similar_results_previous_year.append(similar_gp_session_results)

    #Session (previous year)
    previous_year_session = f1.get_session(year - 1, gp['name'], 'race')
    previous_year_session.load(laps=True, telemetry=False, weather=False, messages=False)
    previous_year_results = previous_year_session.results
    previous_year_laps = previous_year_session.laps

    #Strategy (previous year)
    previous_year_winner = previous_year_results[previous_year_results['Position'] == 1].iloc[0]['Abbreviation']
    previous_year_stint_data = previous_year_laps.drop_duplicates(subset=['Driver', 'Stint'])
    strategy_data = {'winning_strategy': '', 'popular_strategy': '', 'strategies': {}}
    for driver, driver_group in previous_year_stint_data.groupby(by='Driver'):
        previous_year_driver_stint_data = driver_group[driver_group['Driver'] == driver]
        previous_year_driver_stint_data = previous_year_driver_stint_data.sort_values(by='Stint', ascending=True)
        strategy = ""
        for _, stint in previous_year_driver_stint_data.iterrows():
            strategy = strategy + (stint['Compound'][0])
        if strategy not in strategy_data['strategies']:
            strategy_data['strategies'][strategy] = 0
        if driver == previous_year_winner:
            strategy_data['winning_strategy'] = strategy
        strategy_data['strategies'][strategy] = strategy_data['strategies'][strategy] + 1
    
    if strategy_data['strategies']:
        strategy_data['popular_strategy'] = sorted(strategy_data['strategies'].items(), key=lambda x: x[1], reverse=True)[0][0]
    
    return HistoricalData(strategy_data['winning_strategy'], strategy_data['popular_strategy'], previous_results)

def get_practice_session_data(gp) -> PracticeSessionsData:
    sessions: List[PracticeSessionData] = []

    gp_idx, gp = get_gp(gp)

    try:
        for practice_session in practice_sessions:
            ff1_session = f1.get_session(year, gp['name'], practice_session)
            ff1_session.load(laps=True, weather=True, telemetry=False, messages=False)
            sessions.append(PracticeSessionData(gp['name'], practice_session, ff1_session.date, gp['timezone'], ff1_session.results, ff1_session.laps, ff1_session.weather_data)) # type: ignore
    except Exception as e:
        print(e)
        pass
    return PracticeSessionsData(sessions)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

@app.callback(
    dash.Output('gp', 'children'),
    dash.Input('gp-selection', 'value')
)
def update_title(selected_gp):
    return selected_gp

@app.callback(
    dash.Output('session-selection', 'options'),
    dash.Output('session-selection', 'value'),
    dash.Output('driver-selection', 'options'),
    dash.Output('driver-selection', 'value'),
    dash.Output('compound-selection', 'options'),
    dash.Output('compound-selection', 'value'),
    dash.Input('gp-selection', 'value')
)
def update_session_and_driver_and_compound_dropdown(selected_gp):
    sessions = get_practice_session_data(selected_gp)
    sessions_laps = sessions.get_laps('all', 'all', 'all', False)
    session_options = [] if sessions_laps.empty else sorted(sessions_laps['Session'].unique())
    driver_options = [] if sessions_laps.empty else sorted(sessions_laps['Driver'].unique())
    compound_options = [] if sessions_laps.empty else sorted(sessions_laps['Compound'].unique())
    return session_options, session_options, driver_options, driver_options, compound_options, compound_options

@app.callback(
    dash.Output('winning-strategy', 'children'),
    dash.Output('popular-strategy', 'children'),
    dash.Input('gp-selection', 'value')
)
def update_strategy(selected_gp):
    historical_data = get_historical_data(selected_gp)
    return convert_strategy_to_html(historical_data.winning_strategy), convert_strategy_to_html(historical_data.popular_strategy)

@app.callback(
    dash.Output('driver-table', 'figure'),
    dash.Input('gp-selection', 'value'),
    dash.Input('session-selection', 'value'),
    dash.Input('driver-selection', 'value'),
    dash.Input('compound-selection', 'value'),
    dash.Input('pick-quicklaps', 'value'),
    dash.Input('sort-by', 'value'),
)
def update_driver_table(selected_gp, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps, sort_by):
    if (not selected_sessions or not selected_drivers or not selected_compounds):
        return go.Figure()
    else:
        driver_figure = go.Figure()

        sorted_sessions = sorted(selected_sessions)
        sorted_drivers = sorted(selected_drivers)
        sorted_compounds = sorted(selected_compounds)

        sessions = get_practice_session_data(selected_gp)
        aggregagated_session_laps = sessions.aggregate_laps(sorted_sessions, sorted_drivers, sorted_compounds, not not pick_quicklaps)

        aggregated_session_laps_by_driver_by_compound = aggregagated_session_laps[(aggregagated_session_laps['Driver'].isin(sorted_drivers)) & (aggregagated_session_laps['Compound'].isin(sorted_compounds))]
        aggregated_session_laps_by_driver_by_compound = aggregated_session_laps_by_driver_by_compound.sort_values(by='BestTimeMilliseconds', ascending=True) if sort_by == 'Best Lap Time' else aggregated_session_laps_by_driver_by_compound.sort_values(by='AvgTimeMilliseconds', ascending=True)
        aggregated_session_laps_by_driver_by_compound['BestTimeMilliseconds'] = aggregated_session_laps_by_driver_by_compound['BestTimeMilliseconds'].apply(format_lap_time)
        aggregated_session_laps_by_driver_by_compound['AvgTimeMilliseconds'] = aggregated_session_laps_by_driver_by_compound['AvgTimeMilliseconds'].apply(format_lap_time)

        drivers = aggregated_session_laps_by_driver_by_compound['Driver'].values
        compounds = aggregated_session_laps_by_driver_by_compound['Compound'].values
        # num_laps = all_practice_session_data_by_driver_by_compounds
        best_times = aggregated_session_laps_by_driver_by_compound['BestTimeMilliseconds'].values
        avg_times = aggregated_session_laps_by_driver_by_compound['AvgTimeMilliseconds'].values

        driver_table = go.Table(
            header=dict(
                values=['Driver', 'Compound', 'Best Lap Time', 'Avg. Lap Time'],
                fill_color='#eff6ff',
                font_color='#007eff',
                align='left',
            ),
            cells=dict(
                values=[drivers, compounds, best_times, avg_times],
                fill=dict(color=[[get_compound_colour(compound) for compound in compounds]]),
                align='left'
            ),
        )
        driver_figure.add_trace(driver_table)

        driver_figure.update_layout(
            title='Driver Aggregate Session Data',
        )

        return driver_figure

@app.callback(
    dash.Output('driver-lap-times', 'figure'),
    dash.Input('gp-selection', 'value'),
    dash.Input('session-selection', 'value'),
    dash.Input('driver-selection', 'value'),
    dash.Input('compound-selection', 'value'),
    dash.Input('pick-quicklaps', 'value')
)
def update_driver_lap_times(selected_gp, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps):
    if (not selected_sessions or not selected_drivers or not selected_compounds):
        return go.Figure()
    else:
        lap_times_figure = go.Figure()
        
        sorted_sessions = sorted(selected_sessions)
        sorted_drivers = sorted(selected_drivers)
        sorted_compounds = sorted(selected_compounds)

        sessions = get_practice_session_data(selected_gp)
        session_laps = sessions.get_laps(sorted_sessions, sorted_drivers, sorted_compounds, not not pick_quicklaps)
        
        for driver in sorted_drivers:
            session_laps_by_driver_by_compound = session_laps[(session_laps['Driver'] == driver) & (session_laps['Compound'].isin(sorted_compounds))]
            for compound, compound_group in session_laps_by_driver_by_compound.groupby(by='Compound'):
                hover_text = ['<b>Driver:</b> {}<br><b>Lap Time:</b> {}<br><b>Compound:</b> {}<br><b>Tyre Life:</b> {}<br><b>Session:</b> {}<br><b>Time:</b> {}<br><b>Air Temperature:</b> {}<br><b>Track Temperature:</b> {}<br><b>Wind Speed:</b> {}<br><b>Pressure:</b> {}<br><b>Is Raining?:</b> {}<extra></extra>'.format(driver, lap_time, compound, int(tyre_life), session, time.strftime('%Y-%m-%d %H:%M'), air_temp, track_temp, wind_speed, pressure, is_raining)
                    for driver, lap_time, compound, tyre_life, session, time, air_temp, track_temp, wind_speed, pressure, is_raining in zip(compound_group['Driver'], compound_group['LapTimeMilliseconds'].apply(format_lap_time), compound_group['Compound'], compound_group['TyreLife'], compound_group['Session'].str.upper(), compound_group['AdjustedTime'], compound_group['AirTemp'], compound_group['TrackTemp'], compound_group['WindSpeed'], compound_group['Pressure'], compound_group['Rainfall'])]
                driver_lap_times_scatter = go.Box(
                    boxpoints='all',
                    customdata=hover_text,
                    fillcolor='rgba(255,255,255,0)',
                    hoverinfo='none',
                    hovertemplate='%{customdata}',
                    line={'color':'rgba(255,255,255,0)'},
                    marker=dict(color=get_compound_colour(compound)),
                    pointpos=0,
                    showlegend=False,
                    x=compound_group['Driver'], 
                    y=compound_group['LapTimeMilliseconds']
                )
                lap_times_figure.add_trace(driver_lap_times_scatter)
            driver_lap_times_violin = go.Violin(
                hoverinfo='none',
                marker=dict(color=get_driver_colour(driver)),
                showlegend=False,
                x=session_laps_by_driver_by_compound['Driver'], 
                y=session_laps_by_driver_by_compound['LapTimeMilliseconds']
            )
            lap_times_figure.add_trace(driver_lap_times_violin)

        min_time = min(session_laps['LapTimeMilliseconds'])
        max_time = max(session_laps['LapTimeMilliseconds'])
        time_range = max_time - min_time

        num_ticks = 5

        step = time_range / (num_ticks - 1)

        tick_values = [int(min_time + step * i) for i in range(num_ticks)]
        tick_labels = [format_lap_time(time) for time in tick_values]

        lap_times_figure.update_layout(
            yaxis=dict(
                spikecolor="black",
                spikedash="dash",
                spikemode="across",
                spikesnap="cursor",
                spikethickness=0.5,
                tickvals=tick_values, 
                ticktext=tick_labels,
            ),
            title='Driver Session Lap Time Distribution',
            xaxis_title='Driver',
            yaxis_title='Lap Time(s)'
        )
        return lap_times_figure

@app.callback(
    dash.Output('driver-lap-times-progression', 'figure'),
    dash.Input('gp-selection', 'value'),
    dash.Input('session-selection', 'value'),
    dash.Input('driver-selection', 'value'),
    dash.Input('compound-selection', 'value'),
    dash.Input('pick-quicklaps', 'value')
)
def update_driver_lap_times_progression(selected_gp, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps):
    if (not selected_sessions or not selected_drivers or not selected_compounds):
        return go.Figure()
    else:
        lap_times_progression_figure = go.Figure()
        
        sorted_sessions = sorted(selected_sessions)
        sorted_drivers = sorted(selected_drivers)
        sorted_compounds = sorted(selected_compounds)

        sessions = get_practice_session_data(selected_gp)
        session_laps = sessions.get_laps(sorted_sessions, sorted_drivers, sorted_compounds, not not pick_quicklaps)

        for driver in sorted_drivers:
            driver_laps = session_laps[session_laps['Driver'] == driver]
            driver_laps = driver_laps.sort_values(by='AdjustedTime')
            hover_text = ['<b>Driver:</b> {}<br><b>Lap Time:</b> {}<br><b>Compound:</b> {}<br><b>Tyre Life:</b> {}<br><b>Session:</b> {}<br><b>Time:</b> {}<br><b>Air Temperature:</b> {}<br><b>Track Temperature:</b> {}<br><b>Wind Speed:</b> {}<br><b>Pressure:</b> {}<br><b>Is Raining?:</b> {}<extra></extra>'.format(driver, lap_time, compound, int(tyre_life), session, time.strftime('%Y-%m-%d %H:%M'), air_temp, track_temp, wind_speed, pressure, is_raining)
                    for driver, lap_time, compound, tyre_life, session, time, air_temp, track_temp, wind_speed, pressure, is_raining in zip(driver_laps['Driver'], driver_laps['LapTimeMilliseconds'].apply(format_lap_time), driver_laps['Compound'], driver_laps['TyreLife'], driver_laps['Session'].str.upper(), driver_laps['AdjustedTime'], driver_laps['AirTemp'], driver_laps['TrackTemp'], driver_laps['WindSpeed'], driver_laps['Pressure'], driver_laps['Rainfall'])]
            scatter = go.Scatter(
                customdata=hover_text,
                hovertemplate='%{customdata}',
                line=dict(color=get_driver_colour(driver)),
                mode='markers+lines', 
                name=driver, 
                showlegend=False,
                x=driver_laps['TimeSeriesTime'], 
                y=driver_laps['LapTimeMilliseconds'],
            )
            lap_times_progression_figure.add_trace(scatter)

        min_time = min(session_laps['LapTimeMilliseconds'])
        max_time = max(session_laps['LapTimeMilliseconds'])
        time_range = max_time - min_time

        num_ticks = 5

        step = time_range / (num_ticks - 1)

        tick_values = [int(min_time + step * i) for i in range(num_ticks)]
        tick_labels = [format_lap_time(time) for time in tick_values]

        lap_times_progression_figure.update_layout(
            yaxis=dict(
                spikecolor="black",
                spikedash="dash",
                spikemode="across",
                spikesnap="cursor",
                spikethickness=0.5,
                tickvals=tick_values, 
                ticktext=tick_labels,
            ),
            title='Driver Lap Time Progression',
            xaxis_title='Date & Time',
            yaxis_title='Lap Time(s)',
        )

        return lap_times_progression_figure

# @app.callback(
#     dash.Output('driver-season-performance', 'figure'),
#     dash.Input('gp-selection', 'value'),
#     dash.Input('driver-selection', 'value'),
# )
# def update_driver_season_performance(selected_gp, selected_drivers):
#     if (not selected_drivers):
#         return go.Figure()
#     else:
#         gp_idx, gp = get_gp(selected_gp)
#         if (gp_idx > 0):
#             driver_performance_figure = go.Figure()

#             sorted_drivers = sorted(selected_drivers)
                
#             historical_data = get_historical_data(selected_gp)

#             previous_results = historical_data.get_aggregated_previous_results()

#             for driver in sorted_drivers:
#                 driver_result = previous_results[previous_results['Abbreviation'] == driver]
#                 hover_text = ['<b>Driver:</b> {}<br><b>Grand Prix:</b> {}<br><b>Finish Position:</b> {}<extra></extra>'.format(driver, grand_prix.title(), int(finish)) 
#                     for driver, grand_prix, finish in zip(driver_result['Abbreviation'], driver_result['GrandPrix'].str.upper(), driver_result['Position'])]
#                 scatter = go.Scatter(
#                     customdata=hover_text,
#                     hovertemplate='%{customdata}',
#                     line=dict(color=get_driver_colour(driver)),
#                     mode='markers+lines', 
#                     name=driver, 
#                     showlegend=False,
#                     x=driver_result['GrandPrix'], 
#                     y=driver_result['Position'],
#                 )
#                 driver_performance_figure.add_trace(scatter)

#             driver_performance_figure.update_layout(title='Driver Performance',
#                         xaxis_title='Grand Prix',
#                         yaxis_title='Finish Position',
#                         legend_title='Driver')
                
#             return driver_performance_figure
#         else:
#             return go.Figure()

# @app.callback(
#     dash.Output('driver-dnfs', 'figure'),
#     dash.Input('gp-selection', 'value'),
#     dash.Input('driver-selection', 'value'),
# )
# def update_driver_dnfs(selected_gp, selected_drivers):
#     if (not selected_drivers):
#         return go.Figure()
#     else:
#         gp_idx, gp = get_gp(selected_gp)
#         if (gp_idx > 0):
#             driver_dnfs_figure = go.Figure()

#             sorted_drivers = sorted(selected_drivers)
                
#             historical_data = get_historical_data(selected_gp)

#             previous_results = historical_data.get_aggregated_previous_results()
#             condition = (previous_results['Status'] == 'Finished') | (previous_results['Status'] == '+ 1 Lap') | (previous_results['Status'] == '+ 2 Lap')
#             previous_results['Dnf'] = np.where(condition, 0, 1)
#             grouped_previous_results_by_driver = previous_results.groupby(['Abbreviation','GrandPrix'])
#             previous_results['CummulativeDnf'] = grouped_previous_results_by_driver['Dnf'].cumsum()

#             for driver in sorted_drivers:
#                 driver_result = previous_results[previous_results['Abbreviation'] == driver]
#                 hover_text = ['<b>Driver:</b> {}<br><b>Grand Prix:</b> {}<br><b>Cummulative DNFs:</b> {}<extra></extra>'.format(driver, grand_prix.title(), int(dnfs))
#                     for driver, grand_prix, dnfs in zip(driver_result['Abbreviation'], driver_result['GrandPrix'].str.upper(), driver_result['CummulativeDnf'])]
#                 scatter = go.Scatter(
#                     customdata=hover_text,
#                     hovertemplate='%{customdata}',
#                     line=dict(color=get_driver_colour(driver)),
#                     mode='markers+lines', 
#                     name=driver, 
#                     showlegend=False,
#                     x=driver_result['GrandPrix'], 
#                     y=driver_result['CummulativeDnf'],
#                 )
#                 driver_dnfs_figure.add_trace(scatter)

#             driver_dnfs_figure.update_layout(title='Cumulative DNFs for Each Driver',
#                         xaxis_title='Grand Prix',
#                         yaxis_title='Cumulative DNFs',
#                         legend_title='Driver')
                
#             return driver_dnfs_figure
#         else:
#             return go.Figure()

# @app.callback(
#     dash.Output('driver-track-performance-current', 'figure'),
#     dash.Input('gp-selection', 'value'),
#     dash.Input('driver-selection', 'value'),
# )
# def update_driver_track_performance_current(selected_gp, selected_drivers):
#     if (not selected_drivers):
#         return go.Figure()
#     else:
#         driver_track_performance_figure = go.Figure()
        
#         sorted_drivers = sorted(selected_drivers)

#         historical_data = get_historical_data(selected_gp)
#         similar_gps = get_similar_gps(selected_gp)

#         for result in historical_data.similar_results_current_year:
#             for driver in sorted_drivers:
#                 driver_result = result[result['Abbreviation'] == driver]
#                 hover_text = ['<b>Driver:</b> {}<br><b>Grand Prix:</b> {}<br><b>Start:</b> {}<br><b>Finish:</b> {}<extra></extra>'.format(driver, grand_prix.title(), int(start), int(finish))
#                     for driver, grand_prix, start, finish in zip(driver_result['Abbreviation'], driver_result['GrandPrix'].str.upper(), driver_result['GridPosition'],driver_result['Position'])]
#                 scatter = go.Scatter(
#                     customdata=hover_text,
#                     hovertemplate='%{customdata}',
#                     marker=dict(color=get_driver_colour(driver)),
#                     showlegend=False,
#                     x=driver_result['GridPosition'], 
#                     y=driver_result['Position'],
#                 )
#                 driver_track_performance_figure.add_trace(scatter)

#         driver_track_performance_figure.add_annotation(x=20, y=-1, text=f"{selected_gp} is categorized as a {sanitize_key(get_gp_cluster(selected_gp))} circuit", showarrow=False)
#         driver_track_performance_figure.add_annotation(x=20, y=-3, text=f"Other tracks with this classification shown in this graph are", showarrow=False)
#         for idx, (similar_gp_idx, similar_gp) in enumerate(similar_gps):
#             driver_track_performance_figure.add_annotation(x=20, y=((idx+1)*-3)-3, text=similar_gp, showarrow=False)

#         driver_track_performance_figure.update_layout(
#             title='Driver Performance On Similar Tracks (Current Year)',
#             xaxis_title='Grid Position',
#             yaxis_title='Finish Position'
#         )
        
#         return driver_track_performance_figure

# @app.callback(
#     dash.Output('driver-track-performance-previous', 'figure'),
#     dash.Input('gp-selection', 'value'),
#     dash.Input('driver-selection', 'value'),
# )
# def update_driver_track_performance_previous(selected_gp, selected_drivers):
#     if (not selected_drivers):
#         return go.Figure()
#     else:
#         driver_track_performance_figure = go.Figure()
        
#         sorted_drivers = sorted(selected_drivers)

#         historical_data = get_historical_data(selected_gp)
#         similar_gps = get_similar_gps(selected_gp)

#         for result in historical_data.similar_results_previous_year:
#             for driver in sorted_drivers:
#                 driver_result = result[result['Abbreviation'] == driver]
#                 hover_text = ['<b>Driver:</b> {}<br><b>Grand Prix:</b> {}<br><b>Start:</b> {}<br><b>Finish:</b> {}<extra></extra>'.format(driver, grand_prix.title(), int(start), int(finish))
#                     for driver, grand_prix, start, finish in zip(driver_result['Abbreviation'], driver_result['GrandPrix'].str.upper(), driver_result['GridPosition'],driver_result['Position'])]
#                 scatter = go.Scatter(
#                     customdata=hover_text,
#                     hovertemplate='%{customdata}',
#                     marker=dict(color=get_driver_colour(driver)),
#                     showlegend=False,
#                     x=driver_result['GridPosition'], 
#                     y=driver_result['Position'],
#                 )
#                 driver_track_performance_figure.add_trace(scatter)

#         driver_track_performance_figure.add_annotation(x=20, y=-1, text=f"{selected_gp} is categorized as a {sanitize_key(get_gp_cluster(selected_gp))} circuit", showarrow=False)
#         driver_track_performance_figure.add_annotation(x=20, y=-3, text=f"Other tracks with this classification shown in this graph are", showarrow=False)
#         for idx, (similar_gp_idx, similar_gp) in enumerate(similar_gps):
#             driver_track_performance_figure.add_annotation(x=20, y=((idx+1)*-3)-3, text=similar_gp, showarrow=False)

#         driver_track_performance_figure.update_layout(
#             title='Driver Performance On Similar Tracks (Previous Year)',
#             xaxis_title='Grid Position',
#             yaxis_title='Finish Position'
#         )

#         return driver_track_performance_figure

gp_idx, gp = get_upcoming_gp()
app.layout = html.Div(children=[
    dbc.Container(
        children=[
            html.H1(id='gp', style={'textAlign':'left'}),
            html.Div([], className='m-1'),
            dbc.Row([
                dcc.Dropdown(
                    id='gp-selection',
                    options=gps,
                    value=gp['name'],
                ),
                html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='session-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='driver-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='compound-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='sort-by',
                    options=['Best Lap Time', 'Avg. Lap Time'],
                    value='Best Lap Time',
                    multi=False
                ),
                html.Div([], className='m-1'),
                dcc.Checklist(
                    id='pick-quicklaps',
                    options=[
                        {'label': '  Only pick quick laps?  ', 'value': True},
                    ],
                    value=[True]
                ),
            ]),
            html.Div([], className='m-5'),
            dbc.Row([
                dbc.Col(children=[
                    dbc.Card(children=[
                        dbc.CardHeader(children=[
                            html.H4(children='Winning Strategy')
                        ]),
                        dbc.CardBody(children=[
                            html.Div(id='winning-strategy', className='text-center')
                        ])
                    ]),
                ]),
                dbc.Col(children=[
                    dbc.Card(children=[
                        dbc.CardHeader(children=[
                            html.H4(children='Popular Strategy')
                        ]),
                        dbc.CardBody(children=[
                            html.Div(id='popular-strategy', className='text-center')
                        ])
                    ]),
                ])
            ]),
        ],
    ),
    dbc.Row([
        dcc.Graph(id='driver-table')
    ]),
    dbc.Row([
        dcc.Graph(id='driver-lap-times')
    ]),
    dbc.Row([
        dcc.Graph(id='driver-lap-times-progression')
    ]),
    # dbc.Row([
    #     dcc.Graph(id='driver-season-performance')
    # ]),
    # dbc.Row([
    #     dcc.Graph(id='driver-dnfs')
    # ]),
    # dbc.Row([
    #     dcc.Graph(id='driver-track-performance-current')
    # ]),
    # dbc.Row([
    #     dcc.Graph(id='driver-track-performance-previous')
    # ]),
])

if __name__ == '__main__':
    app.run(port='8080', debug=True)