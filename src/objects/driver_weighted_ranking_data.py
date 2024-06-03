class DriverWeightedRankingData:
    def __init__(self, driver, avg_points, ppd, value_delta, four_to_eight_delta, no_dnf_streak, quali_dev, finish_dev):
        self.driver = driver
        self.avg_points = avg_points
        self.ppd = ppd
        self.value_delta = value_delta
        self.four_to_eight_delta = four_to_eight_delta
        self.no_dnf_streak = no_dnf_streak
        self.quali_dev = quali_dev
        self.finish_dev = finish_dev
        return