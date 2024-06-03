import pandas as pd

class F1FantasyData:
    def __init__(self, response):
        df = pd.DataFrame.from_records(response['drivers'], columns=["abbreviation", "simulation_rhter_2024_8_2"])
        df.columns = ["Driver", "Points"]
        self._df = df
        self.has_any_results = response['next_race']['has_any_results']
        return
    
    def to_df(self):
        return self._df