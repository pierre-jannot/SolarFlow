import pytest
import pandas as pd
from processing.aggregator import aggregate

def test_aggregator_outer_join_preservation() -> None:
    """Valide que le outer join conserve tous les timestamps même si l'une des sources a un trou."""
    # Source RTE (1h avec une valeur)
    rte_df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    
    # Source Meteo vide (trou complet pour cette heure)
    meteo_df = pd.DataFrame(columns=["timestamp", "ghi", "dni", "dhi"])
    
    # Source éCO2mix vide
    csv_df = pd.DataFrame(columns=["timestamp", "region", "solar_production_mw", "consumption_mw"])
    
    # Exécution de l'agrégation
    merged = aggregate(rte_df, meteo_df, csv_df, "2026-04-15", "2026-04-15")
    
    # Le timestamp RTE doit être conservé grâce au outer merge
    assert not merged.empty
    assert len(merged) == 1
    assert merged["timestamp"].iloc[0] == pd.Timestamp("2026-04-15 12:00:00", tz="UTC")
    assert merged["solar_production_mw"].iloc[0] == 1500.0
    assert pd.isna(merged["ghi"].iloc[0])  # Doit être NaN car meteo vide

def test_aggregator_anti_gonflement_x4() -> None:
    """Valide que l'agrégation d'éCO2mix au pas de 15 min de plusieurs régions ne multiplie pas artificiellement la production nationale."""
    # 2 régions avec 4 quarts d'heure de production de 100 MW et de consommation de 5000 MW chacun.
    # Production nationale attendue sur l'heure : 
    # Somme des 2 régions pour chaque quart d'heure = 200 MW.
    # Moyenne horaire des quarts d'heure = 200 MW.
    # Consommation nationale attendue :
    # Somme des 2 régions pour chaque quart d'heure = 10000 MW.
    # Moyenne horaire = 10000 MW.
    
    csv_df = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2026-04-15 12:00:00+02:00"),
            pd.Timestamp("2026-04-15 12:15:00+02:00"),
            pd.Timestamp("2026-04-15 12:30:00+02:00"),
            pd.Timestamp("2026-04-15 12:45:00+02:00"),
            pd.Timestamp("2026-04-15 12:00:00+02:00"),
            pd.Timestamp("2026-04-15 12:15:00+02:00"),
            pd.Timestamp("2026-04-15 12:30:00+02:00"),
            pd.Timestamp("2026-04-15 12:45:00+02:00")
        ],
        "region": ["RegionA", "RegionA", "RegionA", "RegionA", "RegionB", "RegionB", "RegionB", "RegionB"],
        "solar_production_mw": [100.0] * 8,
        "consumption_mw": [5000.0] * 8
    })
    
    # Normalisation UTC dans le test
    csv_df["timestamp"] = csv_df["timestamp"].dt.tz_convert("UTC")
    
    # Sources RTE et Meteo vides
    rte_df = pd.DataFrame(columns=["timestamp", "solar_production_mw"])
    meteo_df = pd.DataFrame(columns=["timestamp", "ghi", "dni", "dhi"])
    
    # Exécution de l'agrégation
    merged = aggregate(rte_df, meteo_df, csv_df, "2026-04-15", "2026-04-15")
    
    assert not merged.empty
    assert len(merged) == 1
    
    # Vérification anti-gonflement : production = 200 MW, consommation = 10000 MW
    assert merged["solar_production_mw_csv"].iloc[0] == 200.0
    assert merged["consumption_mw"].iloc[0] == 10000.0
