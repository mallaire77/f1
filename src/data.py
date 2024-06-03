
import fastf1 as f1

import numpy as np
import pandas as pd

from objects.all_data import AllData
from objects.previous_sessions_data import PreviousSessionsData
from objects.gridrival_data import GridRivalData
from objects.strategy_data import StrategyData
from objects.practice_sessions_data import PracticeSessionsData, PracticeSessionData
from objects.f1_fantasy_data import F1FantasyData

from datetime import datetime, timezone
from typing import List
from functools import lru_cache

import traceback
import requests

f1.Cache.enable_cache('./.cache')
f1.Cache.offline_mode(True)

year = 2024

schedule = f1.get_event_schedule(year).iloc[1:]

gps = []
for _, gp in schedule.iterrows(): 
    gps.append(gp['EventName'])

constructors = [
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

driver_salaries_baseline = [
    33,
    31.3,
    29.6,
    27.9,
    26.2,
    24.5,
    22.8,
    21.1,
    19.4,
    17.7,
    16,
    14.3,
    12.6,
    10.9,
    9.2,
    7.5,
    5.8,
    4.1,
    2.4,
    0.7
]

def extract_timezone(value):
    dt = datetime.strptime(value.strftime('%Y-%m-%d %H:%M:%S%z'), "%Y-%m-%d %H:%M:%S%z")
    tz_offset = dt.utcoffset()
    hours_offset = tz_offset.total_seconds() // 3600 # type: ignore

    if tz_offset.total_seconds() % 3600 != 0: # type: ignore
        sign = "+" if hours_offset >= 0 else "-"
        formatted_timezone = f"Etc/GMT{sign}{int(abs(hours_offset)) + 1}"
    else:
        sign = "+" if hours_offset >= 0 else "-"
        formatted_timezone = f"Etc/GMT{sign}{int(abs(hours_offset))}"

    return formatted_timezone

def get_gp(gp: str, inner_year = year):
    if (inner_year == year):
        return _convert_gp(next((inner_gp for _, inner_gp in schedule.iterrows() if inner_gp['EventName'] == gp)))
    else:
        return _convert_gp(next((inner_gp for _, inner_gp in f1.get_event_schedule(inner_year).iloc[1:].iterrows() if inner_gp['EventName'] == gp)))
    
def get_previous_gp(gp: str, inner_year = year):
    return get_previous_gps(gp, inner_year)[-1]

def get_previous_gps(gp: str, inner_year = year):
    if (inner_year == year):
        gp_idx, _ = next(((gp_idx, inner_gp) for gp_idx, inner_gp in enumerate(gps) if inner_gp == gp))
        return [_convert_gp(inner_gp) for _, inner_gp in schedule.iloc[:gp_idx].iterrows()]
    else:
        inner_schedule = f1.get_event_schedule(inner_year).iloc[1:]
        inner_gps = []
        for _, inner_gp in inner_schedule.iterrows(): 
            inner_gps.append(inner_gp['EventName'])
        gp_idx, _ = next(((gp_idx, inner_gp) for gp_idx, inner_gp in enumerate(inner_gps) if inner_gp == gp))
        return [_convert_gp(inner_gp) for _, inner_gp in inner_schedule.iloc[:gp_idx].iterrows()]

def get_last_gp():
    return get_previous_gp(get_upcoming_gp()['EventName'])

def get_upcoming_gp():
    millis_array = [event['Session5DateUtc'].timestamp() * 1000 for _, event in schedule.iterrows()]
    today_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    future_millis = [date for date in millis_array if date > today_millis]
    future_millis.sort()
    next_gp = schedule.iloc[millis_array.index(future_millis[0])]
    return _convert_gp(next_gp)

def clearable_cache(func):
    def wrapper(*args, clear_cache=False, **kwargs):
        if clear_cache:
            func.cache_clear()
        return func(*args, **kwargs)
    return wrapper

@clearable_cache
@lru_cache
def get_data(inner_year: int, gp: str) -> AllData:
    inner_gp = get_gp(gp, inner_year)
    upcoming_gp = get_upcoming_gp()
    is_upcoming_gp = inner_year == year and upcoming_gp['EventName'] == gp
    return AllData(
        year,
        inner_gp['EventName'],
        inner_gp['RoundNumber'],
        inner_gp['Timezone'],
        is_upcoming_gp,
        _get_strategy_data(year, inner_gp),
        _get_practice_session_data(year, inner_gp),
        _get_past_results_data(year, inner_gp),
        _get_gridrival_data(),
        _get_f1_fantasy_data() if is_upcoming_gp else None
    )
    
def _get_strategy_data(year: int, gp: pd.Series) -> StrategyData:
    strategy_data = {'winning_strategy': '', 'popular_strategy': '', 'strategies': {}}

    try:
        previous_year_session = f1.get_session(year - 1, gp['EventName'], 'race')
        if (gp['EventName'] == previous_year_session.event['EventName']):
            previous_year_session.load(laps=True, telemetry=False, weather=False, messages=False)
            previous_year_results = previous_year_session.results
            previous_year_laps = previous_year_session.laps

            previous_year_winner = previous_year_results[previous_year_results['Position'] == 1].iloc[0]['Abbreviation']
            previous_year_stint_data = previous_year_laps.drop_duplicates(subset=['Driver', 'Stint'])
            
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
    except ValueError:
        pass

    return StrategyData(strategy_data['winning_strategy'], strategy_data['popular_strategy'])

def _get_practice_session_data(year: int, gp: pd.Series) -> PracticeSessionsData:
    sessions: List[PracticeSessionData] = []

    try:
        for practice_session in practice_sessions:
            ff1_session = f1.get_session(year, gp['EventName'], practice_session)
            ff1_session.load(laps=True, weather=True, telemetry=True, messages=True)
            sessions.append(PracticeSessionData(gp['EventName'], gp['Timezone'], practice_session, ff1_session))
    except Exception as e:
        print(e)
        pass

    return PracticeSessionsData(sessions)

def _get_past_results_data(year: int, gp: pd.Series) -> PreviousSessionsData:
    results: PreviousSessionsData = PreviousSessionsData()
    previous_gps = get_previous_gps(gp['EventName'], year)
    
    try:
        for inner_gp in previous_gps:
            print(year, inner_gp['EventName'], 'Race')
            ff1_session = f1.get_session(year, inner_gp['EventName'], 'Race')
            ff1_session.load(laps=False, weather=False, telemetry=False, messages=False)
            results.add(ff1_session)
    except Exception:
        print(traceback.format_exc()) 
        pass

    return results

def _get_gridrival_data(key: str = '1fN_qiOoQd0qV79QMKOF1DdiDg22E3Vp5_lJjST1vUX8') -> GridRivalData:
    return GridRivalData(pd.read_csv(f"https://docs.google.com/spreadsheets/d/{key}/export?format=csv"))

def _get_f1_fantasy_data():
    url = "https://f1fantasytoolsapi-szumjzgxfa-ew.a.run.app/team-calculator/init"
    headers = {
        "content-type": "application/json",
    }
    data = {
        "include":[],
        "exclude":[],
        "custom_points":{},
        "points_type":"",
        "current_budget":1000,
        "remaining_budget":1000,
        "alpha_value":90,
        "include_dnf_scores":True,
        "mega_driver_option":False,
        "sort_by":"points",
        "swaps_left":7,
        "no_penalties":False,
        "current_team":{"id":-1,"drivers":[],"constructors":[]}
    }
    response = requests.post(url, headers=headers, json=data)
    return F1FantasyData(response.json())
    
def _convert_gp(gp: pd.Series):
    gp_copy = gp.copy()
    today_millis = int(datetime.now(timezone.utc).timestamp() * 1000)
    if (not pd.isnull(gp_copy['Session5DateUtc'])):
        next_session_millis = np.nan_to_num(gp_copy['Session5DateUtc'].timestamp(), nan=0) * 1000
        for i in reversed(range(4)):
            if (next_session_millis > today_millis):
                next_session_millis = gp_copy[f'Session{i+1}DateUtc'].timestamp() * 1000
            else:
                break
    else:
        next_session_millis = 0
    gp_copy['NextSession'] = int(next_session_millis)
    gp_copy['Timezone'] = 'Etc/GMT' if gp_copy['Session5Date'] == None or pd.isnull(gp_copy['Session5Date'])  else extract_timezone(gp_copy['Session5Date'])
    return gp_copy