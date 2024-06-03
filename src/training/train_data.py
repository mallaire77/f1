
import fastf1 as f1
from fastf1.core import Session

import numpy as np
import pandas as pd

from data import year, schedule, get_previous_gps

from datetime import datetime, timezone
from typing import List

import traceback

features = [
    'Year',
    'Gp',
    'GpRound',
    'Session',
    'Driver',
    'DriverAvgStart',
    'DriverAvgFinish',
    # 'DriverFinishPosition', #Y train
    'DriverNoDnfStreak',
    'DriverDnfs',
    'DayOfYear',
    'HourOfDay',
    'Timestamp',
    'NumLaps',
    'NumQuickLaps',
    'NumLapsCompound',
    'NumQuickLapsCompound',
    'LapTime',
    'LapDistance',
    'LapNumber',
    'LapIsRaining',
    'LapAirTemp',
    'LapTrackTemp',
    'LapWindDirection',
    'LapWindSpeed',
    'LapAtmosphericPressure',
    'LapTyreCompound',
    'LapTyreLife',
    'LapTopSpeed',
    'LapAvgSpeed',
    'LapAvgThrottle',
    'LapFullThrottlePercent',
    'LapBrakePercent',
    'LapTrapSpeed',
    'LapFinishLineSpeed',
    'LapSector1Time',
    'LapSector2Time',
    'LapSector3Time',
    'LapIsPersonalBest',
    'LapIsAccurate',
    'LapIsDeleted',
    'LapTrackStatus',
    'CircuitCorners',
]

categorical_features = ['Gp', 'Session', 'Driver']

class DriverData:
    def __init__(self, year: int, gp_name: str, gp_round: int, gp_timezone: str, driver: str, sessions: List[Session], previous_sessions: List[Session]):
        self.year = year
        self.gp_name = gp_name
        self.gp_round = gp_round
        self.gp_timezone = gp_timezone
        self.driver = driver
        self.sessions = sessions
        self.previous_sessions = previous_sessions

    def to_df(self):
        def convert_compound_to_numerical(compound: str):
            if (compound == 'SOFT'):
                return 0
            elif (compound == 'MEDIUM'):
                return 1
            elif (compound == 'HARD'):
                return 2
            elif (compound == 'INTERMEDIATE'):
                return 3
            elif (compound == 'WET'):
                return 4
            else:
                return 5

        df = pd.DataFrame(columns=features)
        
        # Gp info
        year = self.year
        driver = self.driver
        gp_name = self.gp_name
        gp_round = self.gp_round
        timezone = self.gp_timezone  # type: ignore

        # Circuit info
        circuit_info = None
        corners = None
        num_corners = 0
        for session in self.sessions:
            if (circuit_info is None or corners is None):
                try:
                    circuit_info = session.get_circuit_info()
                    assert circuit_info is not None
                    corners = circuit_info.corners
                    num_corners = corners.iloc[-1]['Number']
                except Exception as e:
                    print(e)

        if (circuit_info is None or corners is None):
            return df
        else:
            for session in self.sessions:
                # Setup
                try:
                    local_df = pd.DataFrame(columns=features)
                    session_name = session.name
                    laps = session.laps.pick_drivers(driver)
                    quick_laps = laps.pick_quicklaps()
                    telemetries = laps.get_telemetry(frequency=4)
                    laps = laps.dropna(subset=['LapTime'])
                    laps = laps.dropna(subset=['TyreLife'])
                    laps = laps[~laps['Compound'].isin(['TEST_UNKNOWN','UNKNOWN'])]
                    laps = pd.merge_asof(laps, session._weather_data, on='Time')
                
                    # Driver info
                    avg_start = 0
                    avg_finish = 0
                    num_laps = laps.shape[0]
                    num_quick_laps = quick_laps.shape[0]
                    dnfs = 0
                    no_dnf_streak = 0
                
                    if (len(self.previous_sessions) > 0):
                        previous_results = pd.DataFrame()

                        for previous_session in reversed(self.previous_sessions):
                            previous_results = pd.concat([previous_results, previous_session.results], ignore_index=True)

                        driver_previous_results = previous_results[previous_results['Abbreviation'] == driver]
                        valid_finish = ['Finished', '+1 Lap', '+2 Laps']
                        avg_start = int(np.nan_to_num(np.mean(driver_previous_results['GridPosition']), nan=-1))
                        avg_finish = int(np.nan_to_num(np.mean(driver_previous_results['Position']), nan=-1))
                        dnfs = (~driver_previous_results['Status'].isin(valid_finish)).sum()
                        
                        for _, result in driver_previous_results.iterrows():
                            if result['Status'] in valid_finish:
                                no_dnf_streak += 1
                            else:
                                break
                    
                    for _, lap in laps.iterrows():
                        # Lap Telemetry
                        lap_start = lap['LapStartDate']
                        lap_time = lap['LapTime']
                        lap_end = lap_start + lap_time
                        localized = lap_start.tz_localize(timezone)
                        epoch = round(localized.timestamp())
                        lap_telemetries = telemetries[(telemetries['Date'] >= lap_start) & (telemetries['Date'] <= lap_end)].sort_values(by='Date')
                        
                        # Lap info
                        lap_time_milliseconds = lap_time.total_seconds() * 1000
                        lap_number = int(lap['LapNumber'])
                        distance_lap_start = max(0, lap_telemetries.iloc[0]['Distance'])
                        distance_lap_finish = max(0, lap_telemetries.iloc[-1]['Distance'])
                        lap_distance = round(distance_lap_finish - distance_lap_start)
                        is_raining = int(np.nan_to_num(lap['Rainfall'], nan=False))
                        air_temp = lap['AirTemp']
                        track_temp = lap['TrackTemp']
                        wind_direction = lap['WindDirection']
                        wind_speed = lap['WindSpeed']
                        atmospheric_pressure = lap['Pressure']
                        compound = lap['Compound']
                        numerical_compound = convert_compound_to_numerical(compound)
                        tyre_life = int(lap['TyreLife'])
                        trap_speed = int(np.nan_to_num(lap['SpeedST'], nan=0))
                        finish_speed = int(np.nan_to_num(lap['SpeedFL'], nan=0))
                        sector1_time = lap['Sector1Time'].total_seconds() * 1000
                        sector2_time = lap['Sector2Time'].total_seconds() * 1000
                        sector3_time = lap['Sector3Time'].total_seconds() * 1000
                        is_deleted = int(np.nan_to_num(lap['Deleted'], nan=False))
                        is_accurate = int(lap['IsAccurate'])
                        is_personal_best = int(lap['IsPersonalBest'])
                        status = lap['TrackStatus']
                        num_laps_compound = laps[laps['Compound'] == compound].shape[0]
                        num_quick_laps_compound = quick_laps[quick_laps['Compound'] == compound].shape[0]

                        # Aggregate Speed info
                        lap_top_speed = round(lap_telemetries['Speed'].max())
                        lap_avg_speed = round(lap_telemetries['Speed'].mean())

                        # Aggregate Throttle info
                        lap_avg_throttle = round(lap_telemetries['Throttle'].mean())
                        lap_full_throttle_percent = round((len(lap_telemetries[lap_telemetries['Throttle'] == 100]) / len(lap_telemetries)) * 100)

                        # Aggregate Brake info
                        lap_brake_percent = round((len(lap_telemetries[lap_telemetries['Brake'] == True]) / len(lap_telemetries)) * 100)

                        row = {
                            # Session
                            'Year': year,
                            'Gp': gp_name,
                            'GpRound': gp_round,
                            'Session': session_name,          
                            'DayOfYear': localized.dayofyear, 
                            'HourOfDay': localized.hour, 
                            'Timestamp': epoch,
                            'CircuitCorners': num_corners,

                            # Driver
                            'Driver': driver,
                            'DriverAvgStart': avg_start,
                            'DriverAvgFinish': avg_finish,
                            # 'DriverFinishPosition': finish_position, #Y train
                            'DriverNoDnfStreak': no_dnf_streak,
                            'DriverDnfs': dnfs,

                            # Lap
                            'Timestamp': epoch,
                            'NumLaps': num_laps,
                            'NumQuickLaps': num_quick_laps,
                            'NumLapsCompound': num_laps_compound,
                            'NumQuickLapsCompound': num_quick_laps_compound,
                            'LapTime': lap_time_milliseconds,
                            'LapDistance': lap_distance,
                            'LapNumber': lap_number,
                            'LapIsRaining': is_raining,
                            'LapAirTemp': air_temp,
                            'LapTrackTemp': track_temp,
                            'LapWindDirection': wind_direction,
                            'LapWindSpeed': wind_speed,
                            'LapAtmosphericPressure': atmospheric_pressure,
                            'LapTyreCompound': numerical_compound,
                            'LapTyreLife': tyre_life,
                            'LapTopSpeed': lap_top_speed,
                            'LapAvgSpeed': lap_avg_speed,
                            'LapAvgThrottle': lap_avg_throttle,
                            'LapFullThrottlePercent': lap_full_throttle_percent,
                            'LapBrakePercent': lap_brake_percent,
                            'LapTrapSpeed': trap_speed,
                            'LapFinishLineSpeed': finish_speed,
                            'LapSector1Time': sector1_time,
                            'LapSector2Time': sector2_time,
                            'LapSector3Time': sector3_time,
                            'LapIsPersonalBest': is_personal_best,
                            'LapIsAccurate': is_accurate,
                            'LapIsDeleted': is_deleted,
                            'LapTrackStatus': status,
                        }
                        local_df.loc[len(local_df)] = row # type: ignore

                        # for _, corner in corners.iterrows():
                        #     # Target distance 25 meters before the corner
                        #     closest_index =  ((lap_telemetries['Distance'] - distance_lap_start) - (corner['Distance'] - 25)).abs().idxmin()
                            
                        #     if (closest_index >= 0 and closest_index < telemetries.shape[0]):
                        #         # Corner Telemetry
                        #         telemetry = telemetries.iloc[closest_index]
                        #         lap_time_seconds = lap_time.total_seconds()
                        #         time = telemetry['Date']
                        #         distance = round(telemetry['Distance'] - distance_lap_start)
                        #         speed = telemetry['Speed']
                        #         throttle = telemetry['Throttle']
                        #         brake = telemetry['Brake']
                        #         drs = telemetry['DRS']
                        #         gear = telemetry['nGear']
                        #         completion = round(((time - lap_start).total_seconds() / lap_time_seconds) * 100)
                    df = pd.concat([df.dropna(axis=1, how='all'), local_df.dropna(axis=1, how='all')], ignore_index=True)
                except Exception as e:
                    print(e)
                    pass
            return df

def extract_timezone(value):
    dt = datetime.strptime(value.strftime('%Y-%m-%d %H:%M:%S%z'), "%Y-%m-%d %H:%M:%S%z")
    tz_offset = dt.utcoffset()
    hours_offset = tz_offset.total_seconds() // 3600 # type: ignore

    if tz_offset.total_seconds() % 3600 != 0: # type: ignore
        sign = "+" if hours_offset >= 0 else "-"
        formatted_timezone = f"Etc/GMT{sign}{int(abs(hours_offset)) + 1}"  # Add 1 to the hours
    else:
        sign = "+" if hours_offset >= 0 else "-"
        formatted_timezone = f"Etc/GMT{sign}{int(abs(hours_offset))}"

    return formatted_timezone

def load(start, finish):
    try:
        data = pd.read_csv(f"./data/all.csv")
    except FileNotFoundError:
        data = pd.DataFrame(columns=features)
        for inner_year in range(start, finish + 1):
            for _, inner_gp in schedule.iterrows():
                gp_name = inner_gp['EventName']
                gp_round = inner_gp['RoundNumber']
                gp_timezone = extract_timezone(inner_gp['Session5Date'])
                gp_utc = int(inner_gp['Session5DateUtc'].timestamp() * 1000)
                today = int(datetime.now(timezone.utc).timestamp() * 1000)

                if ((inner_year != year) or (inner_year == year and gp_utc < today)):
                    print(f"-- Loading {gp_name}({inner_year}) --")
                    try:
                        df = pd.read_csv(f"./data/{inner_year}_{gp_name}.csv")
                        data = pd.concat([data.dropna(axis=1, how='all'), df.dropna(axis=1, how='all')], ignore_index=True)
                    except FileNotFoundError:
                        df = pd.DataFrame(columns=features)
                        sessions = []
                        for session in [
                            'FP1',
                            'FP2',
                            'FP3',
                            'Qualifying',
                            'Sprint Qualifying',
                            'Sprint Shootout',
                            'Sprint',
                            'Race'
                        ]:
                            try:
                                inner_session = f1.get_session(inner_year, gp_name, session)
                                inner_session.load(laps=True, weather=True, telemetry=True, messages=True)
                                if (gp_name == inner_session.event['EventName']):
                                    sessions.append(inner_session)
                                else:
                                    break
                            except ValueError as e:
                                print(e)
                            except Exception as e:
                                print(traceback.format_exc()) 
                                
                        if (len(sessions) > 0):
                            previous_sessions = []
                            for inner_gp in reversed(get_previous_gps(gp_name, inner_year)):
                                try:
                                    inner_session = f1.get_session(inner_year, gp_name, 'race')
                                    inner_session.load(laps=False, weather=False, telemetry=False, messages=False)
                                    previous_sessions.append(inner_session)
                                except ValueError as e:
                                    print(e)
                                except Exception as e:
                                    print(traceback.format_exc()) 

                            try:
                                race_session = sessions[-1]
                                winner_time = race_session.results[race_session.results['Position'] == 1]['Time'].iloc[0].total_seconds()*1000
                                for _, result in race_session.results.sort_values(by='Position').iterrows():
                                    driver: str = result['Abbreviation']
                                    position: int = result['Position']
                                    finish_time = result['Time']
                                    if (not np.isnan(position)):
                                        driver_data = DriverData(inner_year, gp_name, gp_round, gp_timezone, driver, sessions, previous_sessions)
                                        gp_session_driver_df = driver_data.to_df()
                                        gp_session_driver_df['DriverFinishPosition'] = int(position) #Y train
                                        if (position == 1):
                                            gp_session_driver_df['DriverFinishTime'] = finish_time.total_seconds()*1000 #Y train
                                        elif (not pd.isnull(finish_time)):
                                            gp_session_driver_df['DriverFinishTime'] = winner_time + finish_time.total_seconds()*1000 #Y train
                                        else:
                                            gp_session_driver_df['DriverFinishTime'] = -1 #Y train
                                        print(f"Completed aggregating {len(gp_session_driver_df)} telemetry entries for {gp_name} - {driver} ({int(position)}/{len(race_session.results)})")
                                        df = pd.concat([df.dropna(axis=1, how='all'), gp_session_driver_df.dropna(axis=1, how='all')], ignore_index=True)
                                print(f"Completed aggregating all telemetry entries for {gp_name} ({len(df)})")
                                data = pd.concat([data.dropna(axis=1, how='all'), df.dropna(axis=1, how='all')], ignore_index=True)
                                df.to_csv(f'./data/{inner_year}_{gp_name}.csv', index=False)
                            except Exception as e:
                                print(traceback.format_exc())
        data.to_csv(f'./data/all.csv', index=False)
    return data