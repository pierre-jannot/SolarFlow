import pandas as pd
import numpy as np
import os

df = pd.read_csv("output/solarflow_2026-01-01_2026-04-27.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])

# 1. Stats
numeric_cols = ['solar_production_mw', 'ghi', 'dni', 'dhi', 'solar_production_mw_csv', 'consumption_mw']
stats = df[numeric_cols].describe().T
stats['count_non_null'] = df[numeric_cols].count()
print("--- Statistics ---")
print(stats[['count_non_null', 'min', 'max', 'mean', 'std']])

# 2. Inconsistencies
print("\n--- Inconsistencies ---")
# Negative or too high
neg_prod = df[df['solar_production_mw'] < 0]
high_prod = df[df['solar_production_mw'] > 20000]
print(f"Negative production: {len(neg_prod)} lines")
print(f"Production > 20000: {len(high_prod)} lines")

# NaNs
print("\nNaN counts:")
print(df[numeric_cols].isna().sum())

# Missing hours
all_hours = pd.date_range(start=df['timestamp'].min(), end=df['timestamp'].max(), freq='h')
missing_hours = all_hours.difference(df['timestamp'])
print(f"\nMissing hours: {len(missing_hours)}")

# Low prod vs high GHI (daytime)
# Exclude night (GHI > 0)
daytime = df[df['ghi'] > 100]
# Correlation
corr = daytime['ghi'].corr(daytime['solar_production_mw'])
print(f"Correlation (GHI > 100): {corr}")

# Low prod threshold: if GHI > 500 and prod < 500
anomaly_low = daytime[(daytime['ghi'] > 500) & (daytime['solar_production_mw'] < 500)]
print(f"Low production vs High GHI (>500): {len(anomaly_low)} instances")
if not anomaly_low.empty:
    print(anomaly_low[['timestamp', 'solar_production_mw', 'ghi']].head())
