from fastf1.core import Laps, SessionResults
from typing import List

import pandas as pd

class PracticeSessionData:
    def __init__(self, gp: str, session: str, date: pd.Timestamp, tz: str, results: SessionResults, laps: Laps, weather: pd.DataFrame):
        self.gp = gp
        self.session = session
        self.date = date
        self.tz = tz
        self.results = results
        self.laps = laps
        self.weather = weather

    def get_laps(self, drivers, compounds, pick_quicklaps: bool) -> pd.DataFrame:
        df = self.laps.pick_quicklaps() if pick_quicklaps else self.laps
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
        weather = self.weather.sort_values(by='Time')
        df = pd.merge_asof(df, weather, on='Time')
        return df
    
class PracticeSessionsData:
    def __init__(self, sessions: List[PracticeSessionData]):
        self.sessions = sessions

    def aggregate_laps(self, sessions, drivers, compounds, pick_quicklaps) -> pd.DataFrame:
        index=0
        columns=['Driver', 'Compound', 'BestTimeMilliseconds', 'AvgTimeMilliseconds']
        df=pd.DataFrame(columns=columns)
        for driver, driver_group in self.get_laps(sessions, drivers, compounds, pick_quicklaps).groupby(by='Driver'):
            for compound, driver_compound_group in driver_group.groupby(by='Compound'):
                driver_compound_session = driver_compound_group[driver_compound_group['Compound'] == compound]
                df.loc[index] = [driver, compound, min(driver_compound_session['LapTimeMilliseconds']), int(driver_compound_session['LapTimeMilliseconds'].mean())]
                index=index+1
        return df

    def get_laps(self, sessions, drivers, compounds, pick_quicklaps) -> pd.DataFrame:
        df = pd.DataFrame()
        for idx, session in enumerate(self.sessions):
            if (sessions == 'all' or session.session in sessions):
                laps = session.get_laps(drivers, compounds, pick_quicklaps)
                laps['Session'] = session.session
                laps['TimeSeriesTime'] = laps['Time'] + pd.Timestamp('1970-01-01') + pd.Timedelta(hours=idx*1)
                laps['AdjustedTime'] = laps['Time'] + session.date.tz_localize(session.tz).tz_convert('UTC')
                df = pd.concat([df, laps], ignore_index=True)
        return df