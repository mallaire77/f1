import dash
import dash_core_components as dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

import numpy as np
import pandas as pd

from data import year, gps, constructors, drivers, driver_salaries_baseline, get_previous_gp, get_upcoming_gp, get_data
from objects.all_data import AllData

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

def _get_constructors_colour(team: str):
    return next((inner_constructor for inner_constructor in constructors if inner_constructor['name'] == team))['colour'] 

def _get_driver_colour(driver: str):
    inner_driver = next((inner_driver for inner_driver in drivers if inner_driver['abv'] == driver))
    return _get_constructors_colour(inner_driver['team'])

def _get_compound_colour(compound: str):
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

def _convert_strategy_to_html(strategy: str):
    strategy_html = []
    for compound in strategy:
        if compound.lower() == 's':
            strategy_html.append(dash.html.Img(src="/assets/soft.png", width="46", height="46"))
        elif compound.lower() == 'm':
            strategy_html.append(dash.html.Img(src="/assets/medium.png", width="46", height="46"))
        elif compound.lower() == 'h':
            strategy_html.append(dash.html.Img(src="/assets/hard.png", width="46", height="46"))
        elif compound.lower() == 'i':
            strategy_html.append(dash.html.Img(src="/assets/intermediate.png", width="46", height="46"))
        elif compound.lower() == 'w':
            strategy_html.append(dash.html.Img(src="/assets/wet.png", width="46", height="46"))
        else:
            pass
    return strategy_html

def _format_lap_time(milliseconds):
    minutes = int(milliseconds // 60000)
    seconds = int((milliseconds % 60000) // 1000)
    milliseconds = milliseconds % 1000
    return f"{minutes}:{seconds:02d}.{milliseconds:03d}"

def _build_driver_table_figure(data: AllData, sessions, drivers, compounds, pick_quicklaps, include_prediction, include_laps):
    if (not drivers):
        return dash.html.Div()
    else:
        valid_finish = ['Finished', '+1 Lap', '+2 Laps']

        previous_sessions_data = data.previous_sessions_data.to_df()
        aggregate_data = data.practice_session_data.aggregate_laps(sessions, drivers, compounds, pick_quicklaps)
        gridrival_data = data.gridrival_data.to_df()
        f1_fantasy_data = data.f1_fantasy_data.to_df() if data.f1_fantasy_data != None else None
        
        should_load_prediction = include_prediction and f1_fantasy_data != None and f1_fantasy_data.has_any_results
        should_load_laps = include_laps
        has_previous_sessions = not previous_sessions_data.empty

        columns = ['Driver', 'Salary', 'Avg. Salary', 'Avg. Points', 'Avg. Points (4)', 'DNF Streak', 'No DNF Streak', 'Prediction', 'Value Delta to Avg. Points', 'Value Delta to Prediction'] if should_load_prediction else ['Driver', 'Salary', 'Avg. Salary', 'Avg. Points', 'Avg. Points (4)', 'DNF Streak', 'No DNF Streak', 'Value Delta to Avg. Points']
        df = pd.DataFrame(columns=columns)

        for driver in gridrival_data['Driver'].unique():
            driver_gridrival_data = gridrival_data[gridrival_data['Driver'] == driver]

            driver_salary = 0
            driver_dnf_streak = 0
            driver_no_dnf_streak = 0
            driver_average_salary = 0
            driver_average_points = 0
            driver_average_poinst_4 = 0
            if (has_previous_sessions):
                driver_all_gp_results = previous_sessions_data[previous_sessions_data['Abbreviation'] == driver]
                driver_finished_gp_results = driver_all_gp_results.loc[driver_all_gp_results['Status'].isin(valid_finish)]
                driver_gridrival_results = driver_gridrival_data[driver_gridrival_data['Gp'].isin(driver_finished_gp_results['Gp'].unique())]
                driver_salary = driver_gridrival_data[driver_gridrival_data['Gp'] == driver_all_gp_results['Gp'].iloc[-1]]['Salary'].iloc[0]
                driver_average_salary = round(np.mean(driver_gridrival_results['Salary']),1)
                driver_average_points = round(np.mean(driver_gridrival_results['Points']),1)
                driver_average_poinst_4 = round(np.mean(driver_gridrival_results.tail(min(len(driver_gridrival_results), 4))['Points'].values),1)
                for _, row in driver_all_gp_results.iloc[::-1].iterrows():
                    if row['Status'] not in valid_finish:
                        driver_dnf_streak += 1
                    else:
                        break
                for _, row in driver_all_gp_results.iloc[::-1].iterrows():
                    if row['Status'] in valid_finish:
                        driver_no_dnf_streak += 1
                    else:
                        break
                # driver_std_dev_qualifying_pos = statistics.pstdev(driver_all_gp_results['GridPosition'])
                # driver_std_dev_finish_pos = statistics.pstdev(driver_all_gp_results['Position'])
                # driver_last_four_race_average = round(np.mean(driver_all_gp_results.tail(min(len(driver_all_gp_results), 4))['Position'].values))
                # driver_last_eight_race_average = round(np.mean(driver_all_gp_results.tail(min(len(driver_all_gp_results), 8))['Position'].values))

            prediction = 0
            if (should_load_prediction):
                f1_fantasy_data = data.f1_fantasy_data.to_df() # type: ignore
                prediction = f1_fantasy_data[f1_fantasy_data['Driver'] == driver]['Points'].iloc[0]

            row = {
                'Driver': driver,
                'Salary': driver_salary,
                'Avg. Salary': driver_average_salary,
                'Avg. Points': driver_average_points,
                'Avg. Points (4)': driver_average_poinst_4,
                'DNF Streak': driver_dnf_streak,
                'No DNF Streak': driver_no_dnf_streak,
                'Prediction': prediction
            }
            df.loc[len(df)] = row # type: ignore

        if (has_previous_sessions and not df.empty):
            driver_points_ranking = df.sort_values(by='Avg. Points', ascending=False)
            driver_points_ranking['AvgPointsRank'] = range(1, len(driver_points_ranking) + 1)
            df['Value Delta to Avg. Points'] = df.apply(
                lambda row: row['Salary'] - driver_salaries_baseline[driver_points_ranking[driver_points_ranking['Driver'] == row['Driver']]['AvgPointsRank'].iloc[0] - 1],
                axis=1
            ).round(1)

        if (should_load_prediction and not df.empty):
            driver_prediction_ranking = df.sort_values(by='Prediction', ascending=False)
            driver_prediction_ranking['PredictedPointsRank'] = range(1, len(driver_points_ranking) + 1)
            df['Value Delta to Prediction'] = df.apply(
                lambda row: row['Salary'] - driver_salaries_baseline[driver_prediction_ranking[driver_prediction_ranking['Driver'] == row['Driver']]['PredictedPointsRank'].iloc[0] - 1],
                axis=1
            ).round(1)

        style_data_conditional = [
            {'if': {'filter_query': '{No DNF Streak} >= 12', 'column_id': 'No DNF Streak'},
            'backgroundColor': '#ed919a', 'color': 'black'},
            {'if': {'filter_query': '{No DNF Streak} >= 9 && {No DNF Streak} <= 11', 'column_id': 'No DNF Streak'},
            'backgroundColor': '#e8d695', 'color': 'black'},
            {'if': {'filter_query': '{Compound} = "SOFT"', 'column_id': 'Compound'},
            'backgroundColor': '#ed919a', 'color': 'black'},
            {'if': {'filter_query': '{Compound} = "MEDIUM"', 'column_id': 'Compound'},
            'backgroundColor': '#e8d695', 'color': 'black'},
            {'if': {'filter_query': '{Compound} = "HARD"', 'column_id': 'Compound'},
            'backgroundColor': '#dcdadb', 'color': 'black'},
            {'if': {'filter_query': '{Compound} = "INTERMEDIATE"', 'column_id': 'Compound'},
            'backgroundColor': '#97bda2', 'color': 'black'},
            {'if': {'filter_query': '{Compound} = "WET"', 'column_id': 'Compound'},
            'backgroundColor': '#809dd1', 'color': 'black'},
        ]

        if (should_load_laps):
            additional_columns = ['Fastest Time', 'Avg. Time', '# Laps', 'Compound']
            all_columns = columns + additional_columns

            aggregate_data['# Laps'] = aggregate_data['NumLaps']
            aggregate_data['Fastest Time'] = aggregate_data['BestTimeMilliseconds'].apply(_format_lap_time)
            aggregate_data['Avg. Time'] = aggregate_data['AvgTimeMilliseconds'].apply(_format_lap_time)

            merged_df = pd.merge(aggregate_data, df, on='Driver')
            merged_df = merged_df[merged_df['Driver'].isin(drivers)]
            merged_df = merged_df[all_columns]

            return dash.dash_table.DataTable(
                id='driver-table',
                columns=[
                    {"name": i, "id": i} for i in all_columns
                ],
                data= merged_df.to_dict('records'),
                fixed_rows={'headers': True},
                sort_action="native",
                sort_mode="single",
                style_table={'height': '300px', 'overflowY': 'auto', 'overflowX': 'auto', 'width': '100%'},
                style_data_conditional=style_data_conditional,
            )
        else:
            return dash.dash_table.DataTable(
                id='driver-table',
                columns=[
                    {"name": i, "id": i} for i in columns
                ],
                data= df.to_dict('records'),
                fixed_rows={'headers': True},
                sort_action="native",
                sort_mode="single",
                style_table={'height': '300px', 'overflowY': 'auto', 'overflowX': 'auto', 'width': '100%'},
                style_data_conditional=style_data_conditional,
            )

def _build_driver_lap_distribution_figure(data: AllData, sessions, drivers, compounds, pick_quicklaps):
    if (not sessions or not drivers or not compounds):
        return go.Figure()
    else:
        lap_times_figure = go.Figure()
        
        sorted_sessions = sorted(sessions)
        sorted_drivers = sorted(drivers)
        sorted_compounds = sorted(compounds)

        session_laps = data.practice_session_data.get_laps(sorted_sessions, sorted_drivers, sorted_compounds, not not pick_quicklaps)
        
        for driver in sorted_drivers:
            driver_laps = session_laps[(session_laps['Driver'] == driver)]
            for compound, compound_group in driver_laps.groupby(by='Compound'):
                hover_text = ['<b>Driver:</b> {}<br><b>Lap Time:</b> {}<br><b>Compound:</b> {}<br><b>Tyre Life:</b> {}<br><b>Session:</b> {}<br><b>Time:</b> {}<br><b>Air Temperature:</b> {}<br><b>Track Temperature:</b> {}<br><b>Wind Speed:</b> {}<br><b>Pressure:</b> {}<br><b>Is Raining?:</b> {}<extra></extra>'.format(driver, lap_time, compound, int(tyre_life), session, time.strftime('%Y-%m-%d %H:%M'), air_temp, track_temp, wind_speed, pressure, is_raining)
                    for driver, lap_time, compound, tyre_life, session, time, air_temp, track_temp, wind_speed, pressure, is_raining in zip(compound_group['Driver'], compound_group['LapTimeMilliseconds'].apply(_format_lap_time), compound_group['Compound'], compound_group['TyreLife'], compound_group['Session'].str.upper(), compound_group['AdjustedTime'], compound_group['AirTemp'], compound_group['TrackTemp'], compound_group['WindSpeed'], compound_group['Pressure'], compound_group['Rainfall'])]
                driver_lap_times_scatter = go.Box(
                    boxpoints='all',
                    customdata=hover_text,
                    fillcolor='rgba(255,255,255,0)',
                    hoverinfo='none',
                    hovertemplate='%{customdata}',
                    line={'color':'rgba(255,255,255,0)'},
                    marker=dict(color=_get_compound_colour(compound)),
                    pointpos=0,
                    showlegend=False,
                    x=compound_group['Driver'], 
                    y=compound_group['LapTimeMilliseconds']
                )
                lap_times_figure.add_trace(driver_lap_times_scatter)
            driver_lap_times_violin = go.Violin(
                hoverinfo='none',
                marker=dict(color=_get_driver_colour(driver)),
                showlegend=False,
                x=driver_laps['Driver'], 
                y=driver_laps['LapTimeMilliseconds']
            )
            lap_times_figure.add_trace(driver_lap_times_violin)

        min_time = min(session_laps['LapTimeMilliseconds'])
        max_time = max(session_laps['LapTimeMilliseconds'])
        time_range = max_time - min_time

        num_ticks = 5

        step = time_range / (num_ticks - 1)

        tick_values = [int(min_time + step * i) for i in range(num_ticks)]
        tick_labels = [_format_lap_time(time) for time in tick_values]

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

def _build_driver_lap_progression_figure(data: AllData, sessions, drivers, compounds, pick_quicklaps):
    if (not sessions or not drivers or not compounds):
        return go.Figure()
    else:
        lap_times_progression_figure = go.Figure()

        sorted_sessions = sorted(sessions)
        sorted_drivers = sorted(drivers)
        sorted_compounds = sorted(compounds)

        session_laps = data.practice_session_data.get_laps(sorted_sessions, sorted_drivers, sorted_compounds, not not pick_quicklaps)

        for driver in sorted_drivers:
            driver_laps = session_laps[session_laps['Driver'] == driver]
            driver_laps = driver_laps.sort_values(by='AdjustedTime')
            hover_text = ['<b>Driver:</b> {}<br><b>Lap Time:</b> {}<br><b>Compound:</b> {}<br><b>Tyre Life:</b> {}<br><b>Session:</b> {}<br><b>Time:</b> {}<br><b>Air Temperature:</b> {}<br><b>Track Temperature:</b> {}<br><b>Wind Speed:</b> {}<br><b>Pressure:</b> {}<br><b>Is Raining?:</b> {}<extra></extra>'.format(driver, lap_time, compound, int(tyre_life), session, time.strftime('%Y-%m-%d %H:%M'), air_temp, track_temp, wind_speed, pressure, is_raining)
                    for driver, lap_time, compound, tyre_life, session, time, air_temp, track_temp, wind_speed, pressure, is_raining in zip(driver_laps['Driver'], driver_laps['LapTimeMilliseconds'].apply(_format_lap_time), driver_laps['Compound'], driver_laps['TyreLife'], driver_laps['Session'].str.upper(), driver_laps['AdjustedTime'], driver_laps['AirTemp'], driver_laps['TrackTemp'], driver_laps['WindSpeed'], driver_laps['Pressure'], driver_laps['Rainfall'])]
            scatter = go.Scatter(
                customdata=hover_text,
                hovertemplate='%{customdata}',
                line=dict(color=_get_driver_colour(driver)),
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
        tick_labels = [_format_lap_time(time) for time in tick_values]

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
    
def _build_driver_salary_progression_figure(data: AllData, drivers):
    salary_progression_figure = go.Figure()

    sorted_drivers = sorted(drivers)

    gridrival_data = data.gridrival_data.to_df()
    previous_gps = [session for session in data.previous_sessions_data.to_df()['Gp'].unique()]

    for driver in sorted_drivers:
        driver_data = gridrival_data[(gridrival_data['Driver'] == driver) & (gridrival_data['Gp'].isin(previous_gps))]
        scatter = go.Scatter(
            line=dict(color=_get_driver_colour(driver)),
            mode='markers+lines', 
            name=driver, 
            showlegend=False,
            x=driver_data['Gp'], 
            y=driver_data['Salary'],
        )
        salary_progression_figure.add_trace(scatter)

    min_salary = min(gridrival_data['Salary'])
    max_salary = max(gridrival_data['Salary'])
    salary_range = max_salary - min_salary

    num_ticks = 10
    step = salary_range / (num_ticks - 1)

    tick_values = [int(min_salary + step * i) for i in range(num_ticks)]

    salary_progression_figure.update_layout(
        yaxis=dict(
            spikecolor="black",
            spikedash="dash",
            spikemode="across",
            spikesnap="cursor",
            spikethickness=0.5,
            tickvals=tick_values, 
        ),
        title='Driver Salary Progression',
        xaxis_title='Event',
        yaxis_title='Salary',
    )
    return salary_progression_figure

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
    try:
        sessions_laps = get_data(year, selected_gp).practice_session_data.get_laps('all', 'all', 'all', False)
        session_options = [] if sessions_laps.empty else sorted(sessions_laps['Session'].unique())
        driver_options = [] if sessions_laps.empty else sorted(sessions_laps['Driver'].unique())
        compound_options = [] if sessions_laps.empty else sorted(sessions_laps['Compound'].unique())
        return session_options, session_options, driver_options, driver_options, compound_options, compound_options
    except Exception:
        return [], [], [], [], [], []

@app.callback(
    dash.Output('winning-strategy', 'children'),
    dash.Output('popular-strategy', 'children'),
    dash.Output('driver-table-container', 'children'),
    dash.Output('driver-lap-times', 'figure'),
    dash.Output('driver-lap-times-progression', 'figure'),
    # dash.Output('driver-salary-progression', 'figure'),
    dash.Input('gp-selection', 'value'),
    dash.Input('session-selection', 'value'),
    dash.Input('driver-selection', 'value'),
    dash.Input('compound-selection', 'value'),
    dash.Input('pick-quicklaps', 'value'),
    dash.Input('include-predictions', 'value'),
    dash.Input('include-laps', 'value'),
)
def update_all(selected_gp, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps, include_predictions, include_laps):
    data = get_data(year, selected_gp)
    return _convert_strategy_to_html(data.strategy_data.winning_strategy), _convert_strategy_to_html(data.strategy_data.popular_strategy), _build_driver_table_figure(data, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps, include_predictions, include_laps), _build_driver_lap_distribution_figure(data, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps), _build_driver_lap_progression_figure(data, selected_sessions, selected_drivers, selected_compounds, pick_quicklaps)

gp = get_upcoming_gp()
app.layout = dash.html.Div(children=[
    dbc.Container(
        children=[
            dash.html.H1(id='gp', style={'textAlign':'left'}),
            dash.html.Div([], className='m-1'),
            dbc.Row([
                dcc.Dropdown(
                    id='gp-selection',
                    options=gps,
                    value=gp['EventName'],
                ),
                dash.html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='session-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                dash.html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='driver-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                dash.html.Div([], className='m-1'),
                dcc.Dropdown(
                    id='compound-selection',
                    options=[],
                    value='',
                    multi=True
                ),
                dash.html.Div([], className='m-1'),
                dcc.Checklist(
                    id='pick-quicklaps',
                    options=[
                        {'label': '  Only pick quick laps?  ', 'value': True},
                    ],
                    value=[True]
                ),
                dash.html.Div([], className='m-1'),
                dcc.Checklist(
                    id='include-predictions',
                    options=[
                        {'label': '  Include predictions in driver table?  ', 'value': True},
                    ],
                    value=[True]
                ),
                dash.html.Div([], className='m-1'),
                dcc.Checklist(
                    id='include-laps',
                    options=[
                        {'label': '  Include lap data in driver table?  ', 'value': True},
                    ],
                    value=[True]
                ),
            ]),
            dbc.Row([
                dash.html.Div([], className='m-3'),
                dbc.Col(children=[
                    dbc.Card(children=[
                        dbc.CardHeader(children=[
                            dash.html.H4(children='Winning Strategy')
                        ]),
                        dbc.CardBody(children=[
                            dash.html.Div(id='winning-strategy', className='text-center')
                        ])
                    ]),
                ]),
                dbc.Col(children=[
                    dbc.Card(children=[
                        dbc.CardHeader(children=[
                            dash.html.H4(children='Popular Strategy')
                        ]),
                        dbc.CardBody(children=[
                            dash.html.Div(id='popular-strategy', className='text-center')
                        ])
                    ]),
                ]),
                dash.html.Div([], className='m-3'),
            ]),
        ],
    ),
    dash.html.Div( 
        children=[
            dbc.Row([
                dash.html.Div([], className='m-3'),
                dash.html.Div(id='driver-table-container'),
                dash.html.Div([], className='m-3'),
            ]),
            dbc.Row([
                dcc.Graph(id='driver-lap-times')
            ]),
            dbc.Row([
                dcc.Graph(id='driver-lap-times-progression')
            ]),
            # dbc.Row([
            #     dcc.Graph(id='driver-salary-progression')
            # ]),    
        ],
        style={'width': '88vw', 'margin': '0 auto'}
    ),
])

if __name__ == '__main__':
    app.run(port='8080', debug=True)