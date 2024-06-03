from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler

from scipy.stats import spearmanr

from hyperopt import Trials, tpe, hp, fmin
import xgboost as xgb

from data import year, get_last_gp
from train_data import load

import pickle

predictor = 'DriverFinishPosition'

features_to_drop = [
    # 'Gp',
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

def random_forest_train(
    n_estimators,
    max_depth,
    max_features,
    min_samples_split,
    min_samples_leaf,
    max_leaf_nodes,
    X_train,
    y_train
):
    model = RandomForestRegressor(
        # n_estimators = n_estimators, 
        max_depth = max_depth,
        max_features = max_features,
        min_samples_split = min_samples_split,
        min_samples_leaf = min_samples_leaf,
        max_leaf_nodes = max_leaf_nodes,
        random_state = 42
    )
    model.fit(X_train, y_train)
    return model
    
def random_forest_exploratory_train(space):
    trials = Trials()
    def objective(X_train, y_train, params):
        model = random_forest_train(
            int(params['n_estimators']), 
            int(params['max_depth']),
            int(params['max_features']),
            int(params['min_samples_split']),
            int(params['min_samples_leaf']),
            int(params['max_leaf_nodes']),
            X_train,
            y_train
        )

        # Get predicted finishing order
        predicted_finishing_order = model.predict(X_train)

        # Get actual finishing order from your labels (assuming y_train is the true ranking)
        actual_finishing_order = y_train

        # Calculate Spearman rank correlation
        correlation, _ = spearmanr(predicted_finishing_order, actual_finishing_order)

        print(f"score: {correlation}, n_estimators: {int(params['n_estimators'])}, max_depth: {int(params['max_depth'])}, max_features: {params['max_features']}, min_samples_split: {int(params['min_samples_split'])}, min_samples_leaf: {int(params['min_samples_leaf'])}, max_leaf_nodes: {int(params['max_leaf_nodes'])}")

        # Return negative correlation for minimization (Hyperopt minimizes the objective function)
        return -correlation 
    best_hyperparams = fmin(fn = lambda params: objective(X_train_transformed, y_train, params), space = space, algo = tpe.suggest, max_evals = 25, trials = trials)
    return best_hyperparams

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
    
def xgb_exploratory_train(space):
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
    best_hyperparams = fmin(fn = lambda params: objective(X_train_transformed, y_train, params), space = space, algo = tpe.suggest, max_evals = 100, trials = trials)
    return best_hyperparams

data = load(2022, 2024)

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

print("-- Normalizing training & test sets --")
preprocessor = ColumnTransformer(
    transformers=[
        ('num', StandardScaler(), _revised_numerical_features),
        ('cat', OneHotEncoder(handle_unknown='ignore'), _revised_categorical_features)
    ])
X_train = X_train[list(set(X_train.columns) - set(features_to_drop))]
X_train_transformed = preprocessor.fit_transform(X_train)

X_test_1 = X_test[X_test['Session'] == 'Practice 1']
X_test_1 = X_test_1[list(set(X_test.columns) - set(features_to_drop))]
y_test_1 = y_test[X_test_1.index]
X_test_1_transformed = preprocessor.transform(X_test_1)

X_test_2 = X_test[X_test['Session'] == 'Practice 2']
X_test_2 = X_test_2[list(set(X_test.columns) - set(features_to_drop))]
y_test_2 = y_test[X_test_2.index]
X_test_2_transformed = preprocessor.transform(X_test_2)

X_test_3 = X_test[X_test['Session'] == 'Practice 3']
X_test_3 = X_test_3[list(set(X_test.columns) - set(features_to_drop))]
y_test_3 = y_test[X_test_3.index]
X_test_3_transformed = preprocessor.transform(X_test_3)

# XGBoost
print("-- Exploring XGB model --")
print(
    xgb_exploratory_train({
        'n_estimators': hp.quniform('n_estimators', 100, 1000, 10),
        'max_depth': hp.quniform('max_depth', 3, 15, 1),
        'learning_rate': hp.loguniform('learning_rate', -3, -1),
        'colsample_bytree': hp.uniform('colsample_bytree', 0.5, 1),
        'min_child_weight': hp.quniform('min_child_weight', 0, 10, 1),
    })
)

print("-- Training XGB model --")
model = xgb_train(1000, 15, 0.36, 0.75, 0, X_train_transformed, y_train)

#RandomForestRegressor
# print("-- Exploring RandomForestRegressor model --")
# print(
#     random_forest_exploratory_train({
#         "n_estimators": hp.choice("n_estimators", range(100, 500, 100)),
#         "max_depth": hp.choice("max_depth", range(1, 21)),
#         "max_features": hp.choice("max_features", range(1, 21, 3)),
#         "min_samples_split": hp.uniform("min_samples_split", 2, 10),
#         "min_samples_leaf": hp.uniform("min_samples_leaf", 1, 5),
#         "max_leaf_nodes": hp.choice("max_leaf_nodes", range(1, 51, 10)),
#     })
# )

# print("-- Training RandomForestRegressor model --")
# # model = random_forest_train(1, 1, 1, 1, 1, 1, X_train_transformed, y_train)
# model = RandomForestRegressor(random_state=42)
# model.fit(X_train_transformed, y_train)

# -----------------------------
print("-- Saving the model --")
with open('../models/f1_model.pkl', 'wb') as f:
    pickle.dump({'training_features': _revised_features, 'training_features_drop': features_to_drop, 'preprocessor': preprocessor, 'model': model}, f)