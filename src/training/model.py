import keras

import pandas as pd
import numpy as np

from data import year, get_data
from train_data import DriverData
from objects.all_data import AllData

import pickle

def to_driver_data(data: AllData):
    driver_data = []
    for _, entry in data.gridrival_data.df.iterrows(): # type: ignore
        driver_data.append(
            DriverData(
                data.year,
                data.gp_name,
                data.gp_round,
                data.gp_timezone,
                entry['Driver'],
                data.practice_session_data.sessions,
                data.previous_sessions_data.sessions
            )
        )
    return driver_data

def preprocess_rnn(features_to_drop, ohe_gp, ohe_session, df: pd.DataFrame):
    # One-hot encode gp, driver, and session
    gp_onehot = ohe_gp.transform(df['Gp'].values.reshape(-1, 1)).toarray()   # type: ignore
    session_onehot = ohe_session.transform(df['Session'].values.reshape(-1, 1)).toarray()   # type: ignore
    
    # Get column names from the one-hot encoders
    gp_columns = ohe_gp.get_feature_names_out(['Gp'])
    session_columns = ohe_session.get_feature_names_out(['Session'])

    # Create DataFrames from one-hot encoded arrays
    gp_onehot_df = pd.DataFrame(gp_onehot, columns=gp_columns)
    session_onehot_df = pd.DataFrame(session_onehot, columns=session_columns)

    # Concatenate the one-hot encoded DataFrames
    df = pd.concat([df, gp_onehot_df, session_onehot_df], axis=1)

    # Self explanatory
    df.drop(columns=features_to_drop, errors='ignore', inplace=True)

    return df

def normalize_rnn(len, list): 
    return np.array(keras.utils.pad_sequences(list, maxlen=len, padding='pre', value=-1.0))

def predict(data: DriverData):
    with open('./models/f1_model.pkl', 'rb') as file:
        loaded = pickle.load(file)
        features_to_drop = loaded['training_features_drop']
        model = loaded['model']
        predictions = model.predict(data.to_df().drop(columns=features_to_drop, axis=1))
        return predictions
    
def predict_all(data: AllData):
    predictions = pd.DataFrame(columns=['Driver', 'Position'])
    all_driver_data = to_driver_data(data)
    for driver_data in all_driver_data:
        inner_predictions = predict(driver_data)
        predictions.loc[len(predictions)] = {'Driver': driver_data.driver, 'Position': np.mean(inner_predictions) } # type: ignore
    return predictions

def test_me():
    data = to_driver_data(get_data(year, 'Monaco Grand Prix'))

    with open('./models/ohe_gp.pkl', 'rb') as f:
        ohe_gp = pickle.load(f)
    with open('./models/ohe_session.pkl', 'rb') as f:
        ohe_session = pickle.load(f)
    with open(f'./models/rnn.pkl', 'rb') as file:
        loaded = pickle.load(file)

        features_to_drop = loaded['training_features_drop']
        max_sequence_length = loaded['training_max_sequence_length']
        model = loaded['model']

        df = pd.DataFrame()
        for driver_data in data:            
            df = pd.concat([df, driver_data.to_df()], ignore_index=True)
        df.dropna(inplace=True, how='any')

        X = []
        y = []
        for _, group in df.groupby(by=['Driver']):
            X.append(preprocess_rnn(features_to_drop, ohe_gp, ohe_session, group.reset_index().copy()).values)
            y.append(group['Driver'].iloc[0])

        predictions = []
        X = [subarray[0] for subarray in model.predict(normalize_rnn(max_sequence_length, X))]
        for idx, driver in enumerate(y):
            predictions.append({'Driver': driver, 'Prediction': X[idx]})
            
        print(sorted(predictions, key=lambda x: x['Prediction']))