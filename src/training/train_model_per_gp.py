from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

from scipy.stats import spearmanr

from hyperopt import Trials, tpe, hp, fmin
import xgboost as xgb

from data import year, schedule, get_last_gp
from train_data import load

import pickle
import os.path

predictor = 'DriverFinishPosition'

features_to_drop = [
    'Gp',
    'Driver',
    'DriverAvgStart',
    'DriverAvgFinish',
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
    'CornerNumber',
    'Completion',
    'Distance', 
    'Speed', 
    'Throttle', 
    'Brake', 
    'DRS',
    'Gear'
]

def xgb_train(
    n_estimators, 
    max_depth,
    learning_rate,
    colsample_bytree,
    min_child_weight,
    X_train,
    y_train
):
    model = xgb.XGBRegressor(
        n_estimators = n_estimators, 
        max_depth = max_depth,
        learning_rate = learning_rate,
        colsample_bytree = colsample_bytree,
        min_child_weight = min_child_weight,
        seed = 42
    )
    model.fit(X_train, y_train)
    return model

def xgb_train_parameters(params, X_train, y_train):
    return xgb_train(
        int(params['n_estimators']), 
        int(params['max_depth']),
        params['learning_rate'],
        int(params['colsample_bytree']),
        int(params['min_child_weight']),
        X_train,
        y_train
    )
    
def xgb_exploratory_train(space, X_train, y_train):
    trials = Trials()
    def objective(X_train, y_train, params):
        model = xgb_train(
            int(params['n_estimators']), 
            int(params['max_depth']),
            params['learning_rate'],
            int(params['colsample_bytree']),
            int(params['min_child_weight']),
            X_train,
            y_train
        )

        # Get predicted finishing order
        predicted_finishing_order = model.predict(X_train)

        # Get actual finishing order from your labels (assuming y_train is the true ranking)
        actual_finishing_order = y_train

        # Calculate Spearman rank correlation
        correlation, _ = spearmanr(predicted_finishing_order, actual_finishing_order)

        print(f"score: {correlation}, n_estimators: {int(params['n_estimators'])}, max_depth: {int(params['max_depth'])}, learning_rate: {params['learning_rate']}, min_child_weight: {int(params['min_child_weight'])}")

        # Return negative correlation for minimization (Hyperopt minimizes the objective function)
        return -correlation 
    best_hyperparams = fmin(fn = lambda params: objective(X_train, y_train, params), space = space, algo = tpe.suggest, max_evals = 100, trials = trials)
    return best_hyperparams

data = load(2022, 2023)

_training_practice_sessions = ['Practice 1', 'Practice 2', 'Practice 3']
_categorical_features = ['Gp', 'Session', 'Driver']

_revised_features = [x for x in data.columns if x not in features_to_drop] 
_revised_categorical_features = [x for x in _categorical_features if x not in features_to_drop]

_numerical_features = [feature for feature in data.columns if feature != predictor and feature not in _revised_categorical_features]
_revised_numerical_features = [x for x in _numerical_features if x not in features_to_drop]

print("-- Splitting data in to target & feature sets --")
X = data.drop('DriverFinishPosition', axis=1)
y = data['DriverFinishPosition']

print("-- Splitting data in to train & test sets --")
last_gp = get_last_gp()
last_gp_name = last_gp['EventName']
print(f"Using previous Grand Prix ({last_gp_name}) as test set")
print(f"Categorical features: {_revised_categorical_features};")
print(f"Numerical features: {_revised_numerical_features};")
condition1 = X['Gp'] == last_gp_name
condition2 = X['Year'] == year
X_test = X[condition1 & condition2]
X_train = X[~(condition1 & condition2)]
y_test = y[X_test.index]
y_train = y[X_train.index]

print("-- Filtering down practice session telemetry ONLY for test set --")
X_test = X_test[X_test['Session'].isin(_training_practice_sessions)]
y_test = y_test[X_test.index]

for _, inner_gp in schedule.iterrows():
    gp_name = inner_gp['EventName']
    file_name = f'{gp_name}_model.pkl'
    if (not os.path.isfile(f'../models/{file_name}')):
        gp_X_train = X_train[X_train['Gp'] == gp_name]
        gp_X_train = gp_X_train[list(set(X_train.columns) - set(features_to_drop))]
        gp_y_train = y_train[gp_X_train.index]

        print(f"-- Normalizing training & test sets ({gp_name}) --")
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', StandardScaler(), _revised_numerical_features),
                ('cat', OneHotEncoder(handle_unknown='ignore'), _revised_categorical_features)
            ])
                
        if (not gp_X_train.empty):
            gp_X_train_transformed = preprocessor.fit_transform(gp_X_train)
            # XGBoost
            print(f"-- Exploring XGB model ({gp_name}) --")
            optimized_hyperparameters = xgb_exploratory_train(
                {
                    'n_estimators': hp.quniform('n_estimators', 100, 250, 10),
                    'max_depth': hp.quniform('max_depth', 3, 15, 1),
                    'learning_rate': hp.loguniform('learning_rate', -3, -1),
                    'colsample_bytree': hp.uniform('colsample_bytree', 0.5, 1),
                    'min_child_weight': hp.quniform('min_child_weight', 0, 10, 1),
                },
                gp_X_train_transformed,
                gp_y_train
            )

            print(f"-- Training XGB model ({gp_name}) --")
            print(f"Using hyperparameters: {optimized_hyperparameters}")
            model = xgb_train_parameters(optimized_hyperparameters, gp_X_train_transformed, gp_y_train)

            print(f"-- Saving the model ({gp_name}) --")
            with open(f'../models/{file_name}', 'wb') as f:
                pickle.dump({'training_features': _revised_features, 'training_features_drop': features_to_drop, 'preprocessor': preprocessor, 'model': model}, f)