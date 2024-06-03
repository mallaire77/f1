import fastf1 as f1

import keras

import numpy as np
import pandas as pd

from sklearn.preprocessing import OneHotEncoder

from training.model import preprocess_rnn, normalize_rnn
from train_data import load

import os
import pickle

predictor = 'DriverFinishTime'

predictor1 = 'DriverFinishPosition'

features_to_drop = [
    # 'Gp',
    'Driver',
    'DriverAvgStart',
    'DriverAvgFinish',
    'DriverNoDnfStreak',
    'DriverDnfs',
    # 'NumLapsCompound',
    # 'NumQuickLapsCompound',
    # 'LapTime',
    # 'LapTyreCompound',
    # 'LapTyreLife',
    # 'LapSector1Time',
    # 'LapSector2Time',
    # 'LapSector3Time',
    # 'LapDistance',
    # 'LapIsRaining',
    # 'LapAirTemp',
    # 'LapTrackTemp',
    # 'LapWindDirection',
    # 'LapWindSpeed',
    # 'LapAtmosphericPressure',
    # 'LapTrapSpeed',
    # 'LapFinishLineSpeed',
    # 'LapIsPersonalBest',
    # 'LapIsAccurate',
    # 'LapIsDeleted',
    # 'LapTrackStatus',
]

def impute_with_gp_max(group):
    max_time = group[group[predictor] != -1][predictor].max() * 1.1
    group[predictor] = np.where(group[predictor] == -1, max_time, group[predictor])
    return group

if (not os.path.isfile(f'./models/rnn.pkl')):
    print(f"-- Preparing data  --")
    revised_features_to_drop = features_to_drop + list([predictor, predictor1]) + list(['Gp', 'Session'])

    data = load(2022, 2023)
    data = data.groupby(['Year', 'Gp']).apply(impute_with_gp_max, include_groups=True).reset_index(drop=True)

    ohe_gp = OneHotEncoder(handle_unknown='ignore')
    ohe_gp.fit(data['Gp'].values.reshape(-1, 1))

    ohe_session = OneHotEncoder(handle_unknown='ignore')
    ohe_session.fit(data['Session'].values.reshape(-1, 1))

    grouped_gp_X_train = []
    grouped_gp_y_train = []

    for _, group in data.groupby(by=['Year', 'Gp', 'Driver']):
        processed_group = preprocess_rnn(revised_features_to_drop, ohe_gp, ohe_session, group.reset_index().copy())
        grouped_gp_X_train.append(processed_group.values)
        grouped_gp_y_train.append(group[predictor].iloc[0])

    print(f"-- Saving encoders --")
    with open(f'./models/ohe_gp.pkl', 'wb') as f:
        pickle.dump(ohe_gp, f)
    with open(f'./models/ohe_session.pkl', 'wb') as f:
        pickle.dump(ohe_session, f)

    if (len(grouped_gp_X_train) > 0):
        print(f"-- Normalizing data --")
        max_X_sequence_length = max(len(seq) for seq in grouped_gp_X_train)

        local_X_train = normalize_rnn(max_X_sequence_length, grouped_gp_X_train)
        local_Y_train = np.array(grouped_gp_y_train)

        print(f"-- Training RNN --")
        model = keras.Sequential([
            keras.layers.Masking(mask_value=-1, input_shape=(max_X_sequence_length, local_X_train.shape[2])),
            keras.layers.GRU(128, return_sequences=True),
            keras.layers.Dropout(0.2), 
            keras.layers.GRU(64),   
            keras.layers.Dense(1, activation='linear')
        ])
        model.compile(loss=keras.losses.MeanAbsoluteError(), optimizer='adam')
        model.fit(local_X_train, np.log(local_Y_train), epochs=3, batch_size=16, validation_split=0.2)
        
        print(f"-- Saving RNN --")
        with open(f'./models/rnn.pkl', 'wb') as f:
            pickle.dump({'training_features_drop': revised_features_to_drop, 'training_max_sequence_length': max_X_sequence_length, 'model': model}, f)