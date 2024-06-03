from fastf1.core import Session

import pandas as pd

class PreviousSessionsData:
    def __init__(self):
        self._session_names = []
        self.sessions = []
        return
    
    def add(self, session: Session):
        assert not (session.event['EventName'] in self._session_names)
        assert session.name == 'Race'
        self._session_names.append(session.event['EventName'])
        self.sessions.append(session)
        return self
    
    def to_df(self): 
        df = pd.DataFrame()
        for idx, session in enumerate(self.sessions):
            inner_df = session.results
            inner_df['Gp'] = self._session_names[idx]
            df = pd.concat([df, inner_df], ignore_index=True)
        return df