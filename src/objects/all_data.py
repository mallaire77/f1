from objects.gridrival_data import GridRivalData
from objects.previous_sessions_data import PreviousSessionsData
from objects.practice_sessions_data import PracticeSessionsData
from objects.strategy_data import StrategyData
from objects.f1_fantasy_data import F1FantasyData

class AllData:
    def __init__(
            self, 
            year, 
            gp_name,
            gp_round, 
            gp_timezone, 
            gp_is_upcoming,
            strategy_data: StrategyData, 
            practice_session_data: PracticeSessionsData, 
            previous_sessions_data: PreviousSessionsData, 
            gridrival_data: GridRivalData,
            f1_fantasy_data: F1FantasyData | None
        ):
        self.year = year
        self.gp_name = gp_name
        self.gp_round = gp_round
        self.gp_timezone = gp_timezone
        self.gp_is_upcoming = gp_is_upcoming
        self.strategy_data = strategy_data
        self.practice_session_data = practice_session_data
        self.previous_sessions_data = previous_sessions_data
        self.gridrival_data = gridrival_data
        self.f1_fantasy_data = f1_fantasy_data
        return