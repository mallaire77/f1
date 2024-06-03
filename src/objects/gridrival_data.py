import pandas as pd

class GridRivalData:
    def __init__(self, df: pd.DataFrame):
        inner_df = pd.melt(df, id_vars=['Driver'], var_name='Gp')
        inner_df[['Salary', 'Points']] = inner_df['value'].str.split(';', expand=True)
        inner_df['Salary'] = inner_df['Salary'].astype(float)
        inner_df['Points'] = inner_df['Points'].astype(float)
        inner_df.drop('value', axis=1, inplace=True)
        inner_df = inner_df.rename(columns={'variable': 'Gp'})
        self._df = inner_df
        return
    
    def to_df(self):
        return self._df