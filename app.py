import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import datetime
import fastf1
import flask
import flask_caching
import pandas

ordinal = lambda n: "%d%s" % (n,"tsnrhtdd"[(n//10%10!=1)*(n%10<4)*n%10::4])

def format_ms(ms): 
    seconds, milliseconds = divmod(int(ms * 1000), 1000)
    minutes, seconds = divmod(seconds, 60)
    return f'{minutes:02d}:{seconds:02d}:{milliseconds:03d}'

fastf1.Cache.enable_cache('./f1-cache')

cache = flask_caching.Cache(config={'CACHE_TYPE': 'SimpleCache'})

app = flask.Flask(__name__)

cache.init_app(app)

years = [
    2023,
    2022,
]

# Weather: https://weatherwidget.io/
calendar_2023 = [
    {'name': 'Bahrain Grand Prix', 'city': 'Jeddah', 'date': '2023-03-05', 'weather': '/21d2939d24/jeddah/' },
    {'name': 'Saudi Arabian Grand Prix', 'city': 'Jeddah', 'date': '2023-03-19', 'weather': '/21d2939d24/jeddah/'},
    {'name': 'Australian Grand Prix', 'city': 'Melbourne', 'date': '2023-04-02', 'weather': '/n37d81144d96/melbourne/'},
    {'name': 'Azerbaijan Grand Prix', 'city': 'Baku', 'date': '2023-04-30', 'weather': '/40d4149d87/baku/'},
    {'name': 'Miami Grand Prix', 'city': 'Miami', 'date': '2023-05-07', 'weather': '/25d94n80d25/miami-gardens/'},
    {'name': 'Emilia Romagna Grand Prix', 'city': 'Imola', 'date': '2023-05-21', 'weather': '/44d3611d71/imola/'},
    {'name': 'Monaco Grand Prix', 'city': 'Monaco City', 'date': '2023-05-28', 'weather': '/43d737d42/monaco-city/'},
    {'name': 'Spanish Grand Prix', 'city': 'Barcelona-Catalunya', 'date': '2023-06-04', 'weather': '/41d392d17/barcelona/'},
    {'name': 'Canadian Grand Prix', 'city': 'Montreal', 'date': '2023-06-18', 'weather': '/45d50n73d57/montreal/'},
    {'name': 'Austrian Grand Prix', 'city': 'Spielberg', 'date': '2023-07-02', 'weather': '/47d2114d80/spielberg/'},
    {'name': 'British Grand Prix', 'city': 'Silverstone', 'date': '2023-07-09', 'weather': '/52d09n1d03/silverstone/'},
    {'name': 'Hungarian Grand Prix', 'city': 'Mogyorod', 'date': '2023-07-23', 'weather': '/47d6019d24/mogyorod/'},
    {'name': 'Belgian Grand Prix', 'city': 'Spa', 'date': '2023-08-30', 'weather': '/50d455d95/francorchamps/'},
    {'name': 'Dutch Grand Prix', 'city': 'Zandvoort', 'date': '2023-08-27', 'weather': '/52d374d53/zandvoort/'},
    {'name': 'Italian Grand Prix', 'city': 'Monza', 'date': '2023-09-03', 'weather': '/45d589d27/monza/'},
    {'name': 'Singapore Grand Prix', 'city': 'Singapore', 'date': '2023-09-17', 'weather': '/1d35103d82/singapore/'},
    {'name': 'Japanese Grand Prix', 'city': 'Suzuka', 'date': '2023-09-24', 'weather': '/34d88136d58/suzuka/'},
    {'name': 'Qatar Grand Prix', 'city': 'Lusail', 'date': '2023-10-08', 'weather': '/25d4351d50/lusail/'},
    {'name': 'United States Grand Prix', 'city': 'Austin', 'date': '2023-10-22', 'weather': '/30d27n97d74/austin/'},
    {'name': 'Mexican Grand Prix', 'city': 'Mexico City', 'date': '2023-10-29', 'weather': '/19d25n99d10/mexico-city/'},
    {'name': 'Brazilian Grand Prix', 'city': 'Interlagos', 'date': '2023-11-05', 'weather': '/n23d70n46d70/interlagos/'},
    {'name': 'Las Vegas Grand Prix', 'city': 'Las Vegas', 'date': '2023-11-18', 'weather': '/36d17n115d14/las-vegas/'},
    {'name': 'Abu Dhabi Grand Prix', 'city': 'Yas Marina', 'date': '2023-11-26', 'weather': '/24d5054d62/yas-island/'}
]

calendar_2024 = [
    {'name': 'Bahrain Grand Prix', 'date': '2023-03-05'},
    {'name': 'Saudi Arabian Grand Prix', 'date': '2023-03-19'},
    {'name': 'Australian Grand Prix', 'date': '2023-04-02'},
    {'name': 'Azerbaijan Grand Prix' , 'date': '2023-04-30'},
    {'name': 'Miami', 'date': '2023-05-07'},
    {'name': 'Emilia Romagna Grand Prix', 'date': '2023-05-21'},
    {'name': 'Monaco Grand Prix', 'date': '2023-05-28'},
    {'name': 'Spanish Grand Prix', 'date': '2023-06-04'},
    {'name': 'Canadian Grand Prix', 'date': '2023-06-18'},
    {'name': 'Austrian Grand Prix', 'date': '2023-07-02'},
    {'name': 'British Grand Prix', 'date': '2023-07-09'},
    {'name': 'Hungarian Grand Prix', 'date': '2023-07-23'},
    {'name': 'Belgian Grand Prix', 'date': '2023-08-30'},
    {'name': 'Dutch Grand Prix', 'date': '2023-08-27'},
    {'name': 'Italian Grand Prix', 'date': '2023-09-03'},
    {'name': 'Singapore Grand Prix', 'date': '2023-09-17'},
    {'name': 'Japanese Grand Prix', 'date': '2023-09-24'},
    {'name': 'Qatar Grand Prix', 'date': '2023-10-08'},
    {'name': 'United States Grand Prix', 'date': '2023-10-22'},
    {'name': 'Mexican Grand Prix', 'date': '2023-10-29'},
    {'name': 'Brazilian Grand Prix', 'date': '2023-11-05'},
    {'name': 'Las Vegas', 'date': '2023-11-18'},
    {'name': 'Abu Dhabi Grand Prix', 'date': '2023-11-26'}
]

practice_sessions = [
    'fp1',
    'fp2',
    'fp3'
]

session_groups = [
    'Practice',
    'Qualifying',
    'Race',
    'Results'
]

@cache.memoize(timeout=None)
def get_tyre_strategy_data(year, gp):
    strategy_data = {}
    winner = ""
    driver_stint_data = {}
    strategies = {}
    session = fastf1.get_session(int(year), gp, 'race')
    session.load()
    for _, result_data in session.results.iterrows():
        if result_data['Position'] == 1.0:
            winner = result_data['Abbreviation']
        driver_stint_data[result_data['Abbreviation']] = get_driver_stint_data(result_data['Abbreviation'], year, gp, [session.name])
    for driver in driver_stint_data:
        strategy = ""
        for stint in driver_stint_data[driver]:
            strategy = strategy + (driver_stint_data[driver][stint]['compound'][0])
        if strategy not in strategies:
            strategies[strategy] = 0
        if driver == winner:
            strategy_data['winning_strategy'] = strategy
        strategies[strategy] = strategies[strategy] + 1
    if strategies:
        strategy_data['popular_strategy'] = sorted(strategies.items(), key=lambda x: x[1], reverse=True)[0][0]
    return strategy_data

@cache.memoize(timeout=None)
def get_session_data(year, gp):
    session_data = {}
    race_session = fastf1.get_session(int(year), gp, 'race')
    race_session.load()
    qualifying_session = fastf1.get_session(int(year), gp, 'qualifying')
    qualifying_session.load()
    for _, result_data in race_session.results.iterrows():
        driver = result_data['Abbreviation']
        driver_full_name = result_data['FullName']
        if not qualifying_session.results[qualifying_session.results['Abbreviation'] == result_data['Abbreviation']].empty:
            qualifying = qualifying_session.results[qualifying_session.results['Abbreviation'] == result_data['Abbreviation']].iloc[0]['Position']
        else:
            qualifying = 'N/A'
        start = result_data['GridPosition']
        finish = result_data['Position']
        status = result_data['Status']
        session_data[driver] = {
            'driver': driver,
            'driver_full_name': driver_full_name,
            'ordinal_qualifying': qualifying,
            'qualifying': qualifying,
            'ordinal_start': ordinal(int(start)),
            'start': int(start),
            'ordinal_finish': ordinal(int(finish)),
            'finish': int(finish),
            'status': status
        }
    return session_data

@cache.memoize(timeout=None)
def get_driver_stint_data(driver, year, gp, sessions):
    ff1_sessions = []
    for session in sessions:
        try:
            ff1_session = fastf1.get_session(int(year), gp, session)
            ff1_session.load()
            ff1_sessions.append({ 'name': ff1_session.name, 'laps': ff1_session.laps })
        except Exception as e:
            print(e)
            pass
    stint_data = {}
    for ff1_session in ff1_sessions:
        sessions_laps = ff1_session['laps']
        filtered_session_laps = sessions_laps[(sessions_laps['Driver'] == driver) & (sessions_laps['Compound'].notnull())]
        for _, lap_data in filtered_session_laps.iterrows():
            stint = f"Stint {lap_data['Stint']} ({ff1_session['name']})"
            compound = lap_data['Compound']
            status = lap_data['TrackStatus']
            lap_time = lap_data['LapTime']
            lap_num = lap_data['LapNumber']
            is_personal_best = lap_data['IsPersonalBest']
            if lap_time is not pandas.NaT:
                if stint not in stint_data:
                    stint_data[stint] = {
                        'stint': stint,
                        'compound': compound,
                        'status': status,
                        'laps': []
                    }
                stint_data[stint]['laps'].append({
                    'lap_time': round(lap_time.total_seconds() * 1000),
                    'lap_num': lap_num,
                    'is_personal_best': is_personal_best
                })
    return stint_data

@cache.memoize(timeout=None)
def get_lap_data_by_driver_by_compound(year, gp, sessions):
    ff1_session_laps = []
    for session in sessions:
        try:
            ff1_session = fastf1.get_session(int(year), gp, session)
            ff1_session.load()
            ff1_session_laps.append(ff1_session.laps)
        except Exception as e:
            print(e)
            pass
    if not ff1_session_laps:
        return {}
    else:
        all_laps = pandas.concat(ff1_session_laps)
        lap_data_by_compound = {}
        filtered_laps = all_laps[all_laps['Compound'].notnull()]
        driver_compound_lap_data = filtered_laps.groupby(['Driver', 'Compound']).agg({'LapTime': ['count', 'mean', 'min']})
        driver_compound_lap_data.columns = ['num_laps', 'avg_lap_time', 'fastest_lap_time']
        driver_compound_lap_data = driver_compound_lap_data.reset_index().to_dict('records')    
        for compound_lap_data in driver_compound_lap_data:
            driver = compound_lap_data['Driver']
            compound = compound_lap_data['Compound']
            num_laps = compound_lap_data['num_laps']
            fastest_lap_time = compound_lap_data['fastest_lap_time']
            lap_times = filtered_laps[(filtered_laps['Driver'] == driver) & (filtered_laps['Compound'] == compound)]['LapTime']
            lap_times_below_quantile = lap_times[lap_times < fastest_lap_time + datetime.timedelta(seconds=7)]
            avg_lap_time = lap_times_below_quantile.mean()
            slowest_lap_time = lap_times_below_quantile.max()
            if avg_lap_time is not pandas.NaT:
                if driver not in lap_data_by_compound:
                    lap_data_by_compound[driver] = {}
                lap_data_by_compound[driver][compound] = {
                    'driver': driver,
                    'compound': compound,
                    'avg_lap_time': format_ms(avg_lap_time.total_seconds()),
                    'fastest_lap_time': format_ms(fastest_lap_time.total_seconds()),
                    'slowest_lap_time': format_ms(slowest_lap_time.total_seconds()),
                    'num_laps': num_laps
                }
        return lap_data_by_compound


@cache.memoize(timeout=None)
def get_driver_race_results(driver, year, gp):
    ff1_race1 = fastf1.get_session(int(year), gp, 'race')
    ff1_race1.load()
    race_results = 'N/A'
    driver_race_results = ff1_race1.results[ff1_race1.results['Abbreviation'] == driver]
    if not driver_race_results.empty:
        race_results = ordinal(int(driver_race_results.iloc[0]['Position']))
    return race_results

@cache.memoize(timeout=None)
def get_driver_qualifying_results(driver, year, gp):
    ff1_qualifying = fastf1.get_session(int(year), gp, 'qualifying')
    ff1_qualifying.load()
    qualifying_results = 'N/A'
    driver_qualifying_result1 = ff1_qualifying.results[ff1_qualifying.results['Abbreviation'] == driver]
    if not driver_qualifying_result1.empty:
        qualifying_results = ordinal(int(driver_qualifying_result1.iloc[0]['Position']))
    return qualifying_results

@cache.memoize(timeout=None)
def get_drivers(gp):
    drivers = {}
    ff1_session0 = fastf1.get_session(years[0], gp, 'fp1')
    ff1_session0.load()
    for driver in ff1_session0.drivers:
        inner_driver = ff1_session0.get_driver(driver)
        drivers[inner_driver['Abbreviation']] = inner_driver
    ff1_session1 = fastf1.get_session(years[1], gp, 'fp1')
    ff1_session1.load()
    for driver in ff1_session1.drivers:
        inner_driver = ff1_session1.get_driver(driver)
        drivers[inner_driver['Abbreviation']] = inner_driver
    return drivers

def get_upcoming_gp():
    datetime_array = [datetime.datetime.fromisoformat(event['date']) for event in calendar_2023]
    today = datetime.datetime.today()
    future_dates = [date for date in datetime_array if date > today]
    future_dates.sort()
    return calendar_2023[datetime_array.index(future_dates[0])]

def find_previous_gp(gp):
    for i in range(len(calendar_2023)):
        if calendar_2023[i]['name'] == gp:
            if i - 1 > -1:
                return calendar_2023[i - 1]['name']
    return None

def find_next_gp(gp):
    for i in range(len(calendar_2023)):
        if calendar_2023[i]['name'] == gp:
            if i + 1 < len(calendar_2023):
                return calendar_2023[i + 1]['name']
    return None

@app.route("/gps/<gp>/drivers/<driver1>/<year1>/<session1>/compare/<driver2>/<year2>/<session2>")
def driver(gp, driver1, year1, session1, driver2, year2, session2):
    if session1.lower() == 'practice':
        lap_data_by_compound1 = get_lap_data_by_driver_by_compound(year1, gp, practice_sessions)
        driver_stint_data1 = get_driver_stint_data(driver1, year1, gp, practice_sessions)
    else:
        lap_data_by_compound1 = get_lap_data_by_driver_by_compound(year1, gp, [session1.lower()])
        driver_stint_data1 = get_driver_stint_data(driver1, year1, gp, [session1.lower()])
    if driver1 in lap_data_by_compound1:
        lap_data_by_compound1 = lap_data_by_compound1[driver1]
    else:
        lap_data_by_compound1 = {}

    if session2.lower() == 'practice':
        lap_data_by_compound2 = get_lap_data_by_driver_by_compound(year2, gp, practice_sessions)
        driver_stint_data2 = get_driver_stint_data(driver2, year2, gp, practice_sessions)
    else:
        lap_data_by_compound2 = get_lap_data_by_driver_by_compound(year2, gp, [session2.lower()])
        driver_stint_data2 = get_driver_stint_data(driver2, year2, gp, [session2.lower()])
    if driver2 in lap_data_by_compound2:
        lap_data_by_compound2 = lap_data_by_compound2[driver2]
    else:
        lap_data_by_compound2 = {}

    drivers = get_drivers(gp).values()

    driver_full_name1 = ''
    driver_full_name2 = ''
    for driver in drivers:
        if driver['Abbreviation'] == driver1:
            driver_full_name1 = driver['FullName']
        if driver['Abbreviation'] == driver2:
            driver_full_name2 = driver['FullName']

    ff1_session0 = fastf1.get_session(years[0], gp, 'fp1')
    ff1_session0.load()
    current_gp = ff1_session0.event['EventName']

    data = {
        'current_gp': current_gp,
        'gps': calendar_2023,
        'years': years,
        'sessions': session_groups,
        'upcoming_gp': get_upcoming_gp(),
        'drivers': drivers,
        'driver1': driver1,
        'driver2': driver2,
        'driver_full_name1': driver_full_name1,
        'driver_full_name2': driver_full_name2,
        'year1': year1,
        'year2': year2,
        'session1': session1,
        'session2': session2,
        'qualifying_results1': get_driver_qualifying_results(driver1, year1, gp),
        'qualifying_results2': get_driver_qualifying_results(driver2, year2, gp),
        'race_results1': get_driver_race_results(driver1, year1, gp),
        'race_results2': get_driver_race_results(driver2, year2, gp),
        'driver_stint_data1': driver_stint_data1,
        'driver_stint_data2': driver_stint_data2,
        'lap_data_by_compound1': lap_data_by_compound1,
        'lap_data_by_compound2': lap_data_by_compound2
    }
    return flask.render_template("driver.html", data=data)

# Add something like http://davidor.github.io/formula1-lap-charts/#/
@app.route("/gps/<gp>/results")
def results(gp):
    session_result_data = {}
    for year in years:
        try:
            session_result_data[year] = get_session_data(year, gp)
        except Exception as e:
            print(e)
            pass

    tyre_strategy_data = {}
    for year in years:
        try:
            tyre_strategy_data[year] = get_tyre_strategy_data(year, gp)
        except Exception as e:
            print(e)
            pass

    current_ff1_session = fastf1.get_session(years[0], gp, 'race')
    current_ff1_session.load()
    current_gp = current_ff1_session.event['EventName']
    
    data = {
        'current_gp': current_gp,
        'gps': calendar_2023,
        'years': years,
        'sessions': session_groups,
        'upcoming_gp': get_upcoming_gp(),
        'session_result_data': session_result_data,
        'tyre_strategy_data': tyre_strategy_data
    }

    return flask.render_template("results.html", data=data)

# Add table for constructor
@app.route("/gps/<gp>/race")
def race(gp):
    lap_data_by_driver_by_compound = {}
    for year in years:
        lap_data_by_driver_by_compound[year] = get_lap_data_by_driver_by_compound(year, gp, ['race'])

    current_ff1_session = fastf1.get_session(years[0], gp, 'fp1')
    current_ff1_session.load()
    current_gp = current_ff1_session.event['EventName']
    
    data = {
        'current_gp': current_gp,
        'gps': calendar_2023,
        'years': years,
        'sessions': session_groups,
        'upcoming_gp': get_upcoming_gp(),
        'lap_data_by_driver_by_compound': lap_data_by_driver_by_compound
    }

    return flask.render_template("race.html", data=data)

# Break up by qualifying round
# Add table for constructor
@app.route("/gps/<gp>/qualifying")
def qualifying(gp):
    lap_data_by_driver_by_compound = {}
    for year in years:
        lap_data_by_driver_by_compound[year] = get_lap_data_by_driver_by_compound(year, gp, ['qualifying'])

    current_ff1_session = fastf1.get_session(years[0], gp, 'fp1')
    current_ff1_session.load()
    current_gp = current_ff1_session.event['EventName']

    data = {
        'current_gp': current_gp,
        'gps': calendar_2023,
        'years': years,
        'sessions': session_groups,
        'upcoming_gp': get_upcoming_gp(),
        'lap_data_by_driver_by_compound': lap_data_by_driver_by_compound
    }

    return flask.render_template("qualifying.html", data=data)

# Add table for constructor
@app.route("/gps/<gp>/practice")
def practice(gp):
    lap_data_by_driver_by_compound = {}
    for year in years:
        lap_data_by_driver_by_compound[year] = get_lap_data_by_driver_by_compound(year, gp, practice_sessions)

    current_ff1_practice_session = fastf1.get_session(years[0], gp, 'fp1')
    current_ff1_practice_session.load()
    current_gp = current_ff1_practice_session.event['EventName']

    data = {
        'current_gp': current_gp,
        'gps': calendar_2023,
        'years': years,
        'sessions': session_groups,
        'upcoming_gp': get_upcoming_gp(),
        'lap_data_by_driver_by_compound': lap_data_by_driver_by_compound
    }

    return flask.render_template("practice.html", data=data)

@app.route("/gps/upcoming/predictions")
def predictions():
    return flask.redirect(flask.url_for('practice',gp=get_upcoming_gp()['name']))

@app.route("/gps/upcoming")
def upcoming():
    return flask.redirect(flask.url_for('practice',gp=get_upcoming_gp()['name']))

@app.route("/")
def index():
    return flask.redirect(flask.url_for('upcoming'))

@app.route('/images/<file>')
def serve_image(file):
    return flask.send_from_directory('images', file)

@app.route('/scripts/<file>')
def serve_scripts(file):
    return flask.send_from_directory('scripts', file)

@app.route('/bust/gps/<gp>/practice')
def bust_practice(gp):
    print("Busting memoized functions for: /gps/<gp>/practice")
    cache.delete_memoized(get_lap_data_by_driver_by_compound)
    return flask.redirect(flask.request.url_root + f"gps/{gp}/practice")

@app.route('/bust/gps/<gp>/qualifying')
def bust_qualifying(gp):
    print("Busting memoized functions for: /gps/<gp>/qualifying")
    cache.delete_memoized(get_lap_data_by_driver_by_compound)
    return flask.redirect(flask.request.url_root + f"gps/{gp}/qualifying")

@app.route('/bust/gps/<gp>/race')
def bust_race(gp):
    print("Busting memoized functions for: /gps/<gp>/race")
    cache.delete_memoized(get_lap_data_by_driver_by_compound)
    return flask.redirect(flask.request.url_root + f"gps/{gp}/race")

@app.route('/bust/gps/<gp>/results')
def bust_results(gp):
    print("Busting memoized functions for: /gps/<gp>/practice")
    cache.delete_memoized(get_session_data)
    cache.delete_memoized(get_tyre_strategy_data)
    cache.delete_memoized(get_driver_stint_data)
    return flask.redirect(flask.request.url_root + f"gps/{gp}/results")

@app.route('/bust/gps/<gp>/drivers/<driver1>/<year1>/<session1>/compare/<driver2>/<year2>/<session2>')
def bust_driver(gp, driver1, year1, session1, driver2, year2, session2):
    print("Busting memoized function: /gps/<gp>/drivers/<driver1>/<year1>/<session1>/compare/<driver2>/<year2>/<session2>")
    cache.delete_memoized(get_lap_data_by_driver_by_compound)
    cache.delete_memoized(get_driver_stint_data)
    cache.delete_memoized(get_drivers)
    cache.delete_memoized(get_driver_qualifying_results)
    cache.delete_memoized(get_driver_race_results)
    return flask.redirect(flask.request.url_root + f"gps/{gp}/drivers/{driver1}/{year1}/{session1}/compare/{driver2}/{year2}/{session2}")

if __name__ == "__main__":
    app.run()