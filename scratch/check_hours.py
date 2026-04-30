import pandas as pd
df = pd.read_csv("output/solarflow_cleaned_2026-01-01_2026-04-27.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hour'] = df['timestamp'].dt.hour
for col in ['solar_production_mw', 'ghi', 'solar_production_mw_csv']:
    pos_hours = df[df[col] > 0]['hour'].unique()
    print(f"{col}: {sorted(pos_hours)}")
