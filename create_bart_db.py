import sqlite3
import pandas as pd
import numpy as np

conn = sqlite3.connect('bart.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS etd')
c.execute('CREATE TABLE etd (dest text, dir text, station text, etd integer, minute_of_day integer)')


def parse_time(timestamp):
    try:
        dt = pd.to_datetime(float(timestamp), unit='s')
        return dt.tz_localize('UTC').tz_convert('US/Pacific')
    except (AttributeError, ValueError):
        return pd.NaT


def define_weekday(obs_time):
    if obs_time.weekday() < 5:
        return 0
    elif obs_time.weekday() == 5:
        return 1
    elif obs_time.weekday() == 6:
        return 2
    return -1


def parse_data(file_name):
    return pd.read_csv(file_name, parse_dates=['time'], date_parser=parse_time)

df_list = []
for sta_file in ['plza.csv', 'mont.csv']:
    df = parse_data(sta_file)
    df['station'] = sta_file.split('.')[0]
    df_list.append(df)
full_data_df = pd.concat(df_list).reset_index(drop=True)
full_data_df['day_of_week'] = full_data_df['time'].apply(lambda x: define_weekday(x))
full_data_df['etd'] = full_data_df['etd'].replace('Leaving', 0).dropna().astype(np.int)
full_data_df['minute_of_day'] = full_data_df['time'].apply(lambda x: x.time().hour + 60 * x.time().minute)
print full_data_df.head()
full_data_df[['dest', 'dir', 'etd', 'station', 'minute_of_day', 'day_of_week']].to_sql(
    'etd', conn, index=False, if_exists='replace'
)
conn.cursor().execute('CREATE INDEX idx1 ON etd(station, dest, minute_of_day, day_of_week)')
conn.commit()
conn.close()