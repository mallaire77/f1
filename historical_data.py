from fastf1.core import SessionResults
from typing import List
import pandas as pd

class HistoricalData:
    def __init__(self, winning_strategy: str, popular_strategy: str, previous_results: List[SessionResults]):
        self.previous_results = previous_results
        self.winning_strategy = winning_strategy
        self.popular_strategy = popular_strategy
        # self.similar_results_current_year = similar_results_current_year
        # self.similar_results_previous_year = similar_results_previous_year
        return
    
    def get_aggregated_previous_results(self):
        df = pd.DataFrame()
        for result in self.previous_results:
            df = pd.concat([df, result], ignore_index=True)
        return df