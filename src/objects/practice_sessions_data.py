from fastf1.core import Session
import pandas as pd

from typing import List

class PracticeSessionData:
    def __init__(self, gp_name: str, gp_timezone: str, session_name: str, session: Session):
        self.gp_name = gp_name
        self.gp_timezone = gp_timezone
        self.session_name = session_name
        self.session = session

    def get_laps(self, drivers, compounds, pick_quicklaps: bool) -> pd.DataFrame:
        df = self.session.laps.pick_quicklaps() if pick_quicklaps else self.session.laps
        df = df.dropna(subset=['LapTime'])
        df = df.dropna(subset=['TyreLife'])
        df = df[~df['Compound'].isin(['UNKNOWN'])]
        if (drivers != 'all'):
            df = df[df['Driver'].isin(drivers)]
        if (compounds != 'all'):
            df = df[df['Compound'].isin(compounds)]
        df['LapTimeMilliseconds'] = df['LapTime'].dt.total_seconds() * 1000
        df['LapTimeMilliseconds'] = df['LapTimeMilliseconds'].astype(int)
        df = df.sort_values(by='Time')
        weather = self.session.weather_data.sort_values(by='Time') # type: ignore
        df = pd.merge_asof(df, weather, on='Time')
        return df
    
class PracticeSessionsData:
    def __init__(self, practice_sessions: List[PracticeSessionData]):
        self.practice_sessions = practice_sessions
        self.sessions = [x.session for x in practice_sessions]

    def aggregate_laps(self, sessions, drivers, compounds, pick_quicklaps) -> pd.DataFrame:
        index=0
        columns=['Driver', 'Compound', 'BestTimeMilliseconds', 'AvgTimeMilliseconds', 'NumLaps']
        df=pd.DataFrame(columns=columns)
        for driver, driver_group in self.get_laps(sessions, drivers, compounds, pick_quicklaps).groupby(by='Driver'):
            for compound, driver_compound_group in driver_group.groupby(by='Compound'):
                driver_compound_session = driver_compound_group[driver_compound_group['Compound'] == compound]
                df.loc[index] = [driver, compound, min(driver_compound_session['LapTimeMilliseconds']), int(driver_compound_session['LapTimeMilliseconds'].mean()), len(driver_compound_session)]
                index=index+1
        return df

    def get_laps(self, sessions, drivers, compounds, pick_quicklaps) -> pd.DataFrame:
        df = pd.DataFrame()
        for idx, session in enumerate(self.practice_sessions):
            if (sessions == 'all' or session.session_name in sessions):
                laps = session.get_laps(drivers, compounds, pick_quicklaps)
                laps['Session'] = session.session_name
                laps['TimeSeriesTime'] = laps['Time'] + pd.Timestamp('1970-01-01') + pd.Timedelta(hours=idx*1)
                laps['AdjustedTime'] = laps['Time'] + session.session.date.tz_localize(session.gp_timezone).tz_convert('UTC')
                df = pd.concat([df, laps], ignore_index=True)
        return df