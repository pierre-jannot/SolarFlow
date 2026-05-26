import pytest
import pandas as pd
import numpy as np
from processing.data_cleaning import clean_dataset

def test_clean_dataset_deduplication() -> None:
    """Valide que les lignes avec des timestamps dupliqués sont correctement dédupliquées."""
    ts = pd.Timestamp("2026-04-15 12:00:00", tz="UTC")
    df = pd.DataFrame({
        "timestamp": [ts, ts],
        "solar_production_mw": [100.0, 100.0],
        "ghi": [500.0, 500.0],
        "dni": [300.0, 300.0],
        "dhi": [200.0, 200.0]
    })
    cleaned = clean_dataset(df)
    assert len(cleaned) == 1

def test_clean_dataset_negative_production() -> None:
    """Valide que les valeurs de production négatives sont ramenées à 0 (nulles)."""
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [-50.0],
        "ghi": [100.0],
        "dni": [50.0],
        "dhi": [50.0]
    })
    cleaned = clean_dataset(df)
    assert cleaned["solar_production_mw"].iloc[0] == 0.0

def test_clean_dataset_aberrant_production() -> None:
    """Valide que les productions aberrantes (> 20000 MW) sont supprimées du dataset."""
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [25000.0],
        "ghi": [500.0],
        "dni": [300.0],
        "dhi": [200.0]
    })
    cleaned = clean_dataset(df)
    # La ligne contenant la valeur > 20000 MW doit être supprimée car jugée aberrante
    assert len(cleaned) == 0

def test_clean_dataset_interpolation_and_imputation() -> None:
    """Valide l'interpolation météo pour les petits trous et l'imputation à 0 de la production solaire."""
    # Création d'une série temporelle de 3 heures avec un NaN au milieu
    timestamps = [
        pd.Timestamp("2026-04-15 12:00:00", tz="UTC"),
        pd.Timestamp("2026-04-15 13:00:00", tz="UTC"),
        pd.Timestamp("2026-04-15 14:00:00", tz="UTC")
    ]
    df = pd.DataFrame({
        "timestamp": timestamps,
        "solar_production_mw": [100.0, np.nan, 200.0],
        "ghi": [500.0, np.nan, 700.0],
        "dni": [300.0, np.nan, 500.0],
        "dhi": [200.0, np.nan, 200.0]
    })
    cleaned = clean_dataset(df)
    
    # 1. La météo à 13h00 doit être interpolée linéairement entre 12h00 et 14h00
    assert cleaned["ghi"].iloc[1] == 600.0
    assert cleaned["dni"].iloc[1] == 400.0
    assert cleaned["dhi"].iloc[1] == 200.0
    
    # 2. Le NaN de production solaire doit être imputé à 0 MW (règle documentée par défaut)
    assert cleaned["solar_production_mw"].iloc[1] == 0.0

def test_clean_dataset_physical_inconsistencies() -> None:
    """Valide les règles d'incohérences physiques météo.
    
    Règles appliquées :
    - DHI > GHI est physiquement impossible (DHI est une fraction du GHI). La ligne doit être supprimée.
    - DNI > GHI est tolérée (possible sous certains angles solaires rasants). La ligne doit être conservée (règle assouplie).
    """
    # 1. Cas DHI > GHI (Incohérence forte -> suppression)
    df_dhi_invalid = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [100.0],
        "ghi": [200.0],
        "dni": [50.0],
        "dhi": [300.0]  # DHI (300) > GHI (200) -> Impossible
    })
    cleaned_dhi = clean_dataset(df_dhi_invalid)
    assert len(cleaned_dhi) == 0
    
    # 2. Cas DNI > GHI (Règle assouplie -> conservation)
    df_dni_valid = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [100.0],
        "ghi": [300.0],
        "dni": [400.0],  # DNI (400) > GHI (300) -> Conservé (angle rasant, etc.)
        "dhi": [100.0]
    })
    cleaned_dni = clean_dataset(df_dni_valid)
    assert len(cleaned_dni) == 1
    assert cleaned_dni["dni"].iloc[0] == 400.0
