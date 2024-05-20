
import fastf1 as f1
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import DBSCAN, KMeans, AgglomerativeClustering

f1.Cache.enable_cache('./.cache')
# f1.Cache.offline_mode(True)

current_year = 2024

min_year = 2022

calendar = [
    {'name': 'Bahrain Grand Prix', 'city': 'Sakhir', 'date': '2024-03-02'},
    {'name': 'Saudi Arabian Grand Prix', 'city': 'Jeddah', 'date': '2024-03-09'},
    {'name': 'Australian Grand Prix', 'city': 'Melbourne', 'date': '2024-03-24'},
    {'name': 'Japanese Grand Prix', 'city': 'Suzuka', 'date': '2024-04-07'},
    {'name': 'Chinese Grand Prix', 'city': 'Shanghai', 'date': '2024-04-21'},
    {'name': 'Miami Grand Prix', 'city': 'Miami', 'date': '2024-05-05'},
    {'name': 'Emilia Romagna Grand Prix', 'city': 'Imola', 'date': '2024-05-19'},
    {'name': 'Monaco Grand Prix', 'city': 'Monaco', 'date': '2024-05-26'},
    {'name': 'Canadian Grand Prix', 'city': 'Montreal', 'date': '2024-06-09'},
    {'name': 'Spanish Grand Prix', 'city': 'Barcelona-Catalunya', 'date': '2024-06-23'},
    {'name': 'Austrian Grand Prix', 'city': 'Spielberg', 'date': '2024-06-30'},
    {'name': 'British Grand Prix', 'city': 'Silverstone', 'date': '2024-07-07'},
    {'name': 'Hungarian Grand Prix', 'city': 'Budapest', 'date': '2024-07-21'},
    {'name': 'Belgium Grand Prix', 'city': 'Spa', 'date': '2024-07-28'},
    {'name': 'Dutch Grand Prix', 'city': 'Zandvoort', 'date': '2024-08-25'},
    {'name': 'Italian Grand Prix', 'city': 'Monza', 'date': '2024-09-01'},
    {'name': 'Azerbaijan Grand Prix', 'city': 'Baku', 'date': '2024-09-15'}, 
    {'name': 'Singapore Grand Prix', 'city': 'Singapore', 'date': '2024-09-22'},
    {'name': 'United States Grand Prix', 'city': 'Austin', 'date': '2024-10-20'},
    {'name': 'Mexican Grand Prix', 'city': 'Mexico City', 'date': '2024-10-27'},
    {'name': 'Brazilian Grand Prix', 'city': 'Interlagos', 'date': '2024-11-03'},
    {'name': 'Las Vegas Grand Prix', 'city': 'Las Vegas', 'date': '2024-11-24'},
    {'name': 'Qatar Grand Prix', 'city': 'Lusail', 'date': '2024-12-01'},
    {'name': 'Abu Dhabi Grand Prix', 'city': 'Yas Marina', 'date': '2024-12-08'}
]

def get_dry_session(year, gp):
    if (year < 2022):
        session = f1.get_session(current_year - 1, gp, 'race')
        session.load(laps=True, telemetry=True, weather=False, messages=False)
        return current_year, session
    else:
        session = f1.get_session(year, gp, 'race')
        session.load(laps=True, telemetry=True, weather=True, messages=False)

        weather_data = session.weather_data
        assert weather_data is not None
        if (weather_data['Rainfall'].eq(True).any()):
            return get_dry_session(year - 1, gp)
        else:
            return year, session

def key_friendly_str(value):
    return value.lower().replace(" ", "-")

def get_gp_features(file):
    try:
        gp_features = pd.read_csv(f'{file}.csv')
    except FileNotFoundError:
        gp_features = pd.DataFrame()

    if (gp_features.empty):
        for gp in calendar:
            df = pd.DataFrame(columns=['gp', 'number', 'top_speed', 'speed', 'throttle', 'throttle_full_percent', 'track_distance', 'lap_time', 'driver_start', 'driver_finish', 'number_corners', 'corner_number', 'corner_speed', 'corner_throttle', 'corner_is_brake_applied'])

            gp = gp['name']
            gp_key = key_friendly_str(gp)
                                    
            # Session
            year, session = get_dry_session(current_year - 1, gp)

            # Static info
            circuit_info = session.get_circuit_info()
            assert circuit_info is not None
            corners = circuit_info.corners
            race_winner = session.results[session.results['Position'] == 1].iloc[0]['DriverNumber']
            laps = session.laps.pick_drivers([race_winner]).pick_quicklaps()
            telemetries = laps.get_telemetry(frequency=10)

            # Dynamic info
            last_corner = corners.iloc[-1]['Number']
            for lidx, lap in laps.iterrows():
                if (lidx != 0):
                    # Pre-process info
                    next_corner = 1
                    lap_number = int(lap['LapNumber'])
                    lap_time = lap['LapTime']
                    lap_start = lap['LapStartDate']
                    lap_end = lap_start + lap_time
                    lap_telemetries = telemetries[(telemetries['Date'] >= lap_start) & (telemetries['Date'] <= lap_end)].sort_values(by='Date')
                    distance_lap_start = max(0, lap_telemetries.iloc[0]['Distance'])

                    # Speed info
                    lap_top_speed = lap_telemetries['Speed'].max()
                    lap_avg_speed = lap_telemetries['Speed'].mean()

                    # Throttle info
                    lap_avg_throttle = lap_telemetries['Throttle'].mean()
                    lap_full_throttle_percent = (len(lap_telemetries[lap_telemetries['Throttle'] == 100]) / len(lap_telemetries)) * 100

                    # Corner info
                    for tidx, telemetry in lap_telemetries.iterrows():
                        if next_corner <= last_corner:
                            lap_distance = telemetry['Distance'] - distance_lap_start
                            next_corner_distance = corners[corners['Number'] == next_corner].iloc[0]['Distance']
                            if lap_distance > next_corner_distance:
                                row = {'gp': gp_key, 'number': lap_number, 'top_speed': lap_top_speed, 'speed': lap_avg_speed, 'throttle': lap_avg_throttle, 'track_distance': round(lap_telemetries.iloc[-1]['Distance']), 'lap_time': lap_time.total_seconds() * 1000, 'throttle_full_percent': lap_full_throttle_percent, 'number_corners': last_corner, 'corner_number': next_corner, 'corner_speed': telemetry['Speed'], 'corner_throttle': telemetry['Throttle'], 'corner_is_brake_applied': telemetry['Brake']}
                                df.loc[len(df)] = row # type: ignore
                                next_corner = next_corner + 1

            gp_features = pd.concat([gp_features, df], ignore_index=True)
        
        gp_features.to_csv(f'{file}.csv', index=False)

        return gp_features
    else:
        return gp_features

features = ['top_speed', 'speed', 'throttle', 'throttle_full_percent', 'track_distance', 'lap_time', 'number_corners',
    'corner_speed_low_speed', 'corner_throttle_low_speed', 'corner_is_brake_applied_low_speed',
    'corner_speed_medium_speed', 'corner_throttle_medium_speed', 'corner_is_brake_applied_medium_speed',
    'corner_speed_high_speed', 'corner_throttle_high_speed', 'corner_is_brake_applied_high_speed']

gp_features = get_gp_features('2024-3-6')

grouped_gp_features = gp_features.groupby(['gp', 'corner_number'])

aggregated_gp_features = grouped_gp_features.agg({
    'corner_speed': 'mean',
    'corner_throttle': 'mean',
    'corner_is_brake_applied': 'mean'
}).reset_index()

aggregated_gp_features['corner_category'] = pd.cut(aggregated_gp_features['corner_speed'], bins=[0, 100, 150, float('inf')], labels=['low_speed', 'medium_speed', 'high_speed'])

grouped_aggregated_gp_features = aggregated_gp_features.groupby(['gp', 'corner_category'])

corner_gp_features = grouped_aggregated_gp_features.mean().reset_index()

lap_gp_features = gp_features.groupby('gp').agg({
    'top_speed': 'mean',
    'speed': 'mean',
    'throttle': 'mean',
    'throttle_full_percent': 'mean',
    'track_distance': 'mean',
    'lap_time': 'mean',
    'number_corners': 'mean'
}).reset_index()

merged_gp_features = pd.merge(corner_gp_features, lap_gp_features, on='gp')

pivot_gp_features = merged_gp_features.pivot_table(index='gp', columns='corner_category', 
                                values=['corner_speed', 'corner_throttle', 'corner_is_brake_applied'],  # type: ignore
                                aggfunc='mean')

pivot_gp_features.columns = [f'{col}_{category}' for col, category in pivot_gp_features.columns]

pivot_gp_features.reset_index(inplace=True)

final_gp_features = pd.merge(merged_gp_features[['gp', 'top_speed', 'speed', 'throttle', 'throttle_full_percent', 'track_distance', 'lap_time', 'number_corners']],
                     pivot_gp_features, on='gp')
final_gp_features.reset_index(inplace=True)
final_gp_features.fillna(0, inplace=True)

scaler = StandardScaler()
final_gp_features_scaled = scaler.fit_transform(final_gp_features[features])

optimal_k = 8

agg_clustering = AgglomerativeClustering(n_clusters=optimal_k)
final_gp_features['cluster'] = agg_clustering.fit_predict(final_gp_features_scaled)

print("=== AgglomerativeClustering ===")
print("{")
for cluster, features in final_gp_features.groupby(by='cluster'):
    print(f"    {cluster}: ", features['gp'].unique())
print("}")

kmeans = KMeans(n_clusters=optimal_k, random_state=42)
final_gp_features['cluster'] = kmeans.fit_predict(final_gp_features_scaled)

print("=== KMeans ===")
print("{")
for cluster, features in final_gp_features.groupby(by='cluster'):
    print(f"    {cluster}: ", features['gp'].unique())
print("}")

dbscan = DBSCAN(eps=3.2, min_samples=5)
final_gp_features['cluster'] = dbscan.fit_predict(final_gp_features_scaled)

print("=== DBSCAN ===")
print("{")
for cluster, features in final_gp_features.groupby(by='cluster'):
    print(f"    {cluster}: ", features['gp'].unique())
print("}")