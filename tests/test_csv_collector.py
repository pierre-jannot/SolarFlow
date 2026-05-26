import pytest
import pandas as pd
from collectors.csv_collector import load_eco2mix

def test_load_eco2mix_nominal() -> None:
    """Valide le chargement nominal du fichier éCO2mix de test."""
    filepath = "data/eco2mix_sample.csv"
    
    # On charge le fichier avec notre collecteur
    df = load_eco2mix(filepath)
    
    # Vérifications structurelles
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    
    # Vérifier les colonnes attendues
    expected_cols = ["timestamp", "region", "solar_production_mw", "consumption_mw"]
    for col in expected_cols:
        assert col in df.columns
        
    # Vérifier le type des colonnes et s'assurer qu'il n'y a pas de colonnes dupliquées
    assert not df.columns.duplicated().any()
    assert isinstance(df["region"], pd.Series)
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
    assert pd.api.types.is_string_dtype(df["region"])
    assert pd.api.types.is_numeric_dtype(df["solar_production_mw"])
    assert pd.api.types.is_numeric_dtype(df["consumption_mw"])

def test_load_eco2mix_invalid_path() -> None:
    """Valide que le collecteur gère proprement un fichier inexistant en retournant un DataFrame vide."""
    df = load_eco2mix("unexisting_file_path.csv")
    assert isinstance(df, pd.DataFrame)
    assert df.empty
    assert list(df.columns) == ["timestamp", "region", "solar_production_mw", "consumption_mw"]
