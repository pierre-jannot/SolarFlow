import pytest
import pandas as pd
from utils import validate_dataframe, DataValidationError

def test_validate_dataframe_nominal() -> None:
    """Valide qu'un DataFrame correct passe sans lever d'exception."""
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    # Ne doit pas lever d'exception
    assert validate_dataframe(df, ["timestamp", "solar_production_mw"], "2026-04-15", "2026-04-15") is True

def test_validate_dataframe_none_or_empty() -> None:
    """Valide qu'un DataFrame None ou vide lève une DataValidationError."""
    with pytest.raises(DataValidationError, match="vide ou None"):
        validate_dataframe(None, ["timestamp"])
        
    with pytest.raises(DataValidationError, match="vide ou None"):
        validate_dataframe(pd.DataFrame(), ["timestamp"])

def test_validate_dataframe_missing_columns() -> None:
    """Valide qu'une colonne obligatoire manquante lève une DataValidationError."""
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")]
    })
    with pytest.raises(DataValidationError, match="Colonnes obligatoires manquantes"):
        validate_dataframe(df, ["timestamp", "solar_production_mw"])

def test_validate_dataframe_invalid_timestamp() -> None:
    """Valide qu'une colonne timestamp avec des valeurs NaT ou non convertibles lève une DataValidationError."""
    # Cas NaT (valeur manquante)
    df_nat = pd.DataFrame({
        "timestamp": [pd.NaT],
        "solar_production_mw": [1500.0]
    })
    with pytest.raises(DataValidationError, match="La colonne 'timestamp' contient des valeurs NaT"):
        validate_dataframe(df_nat, ["timestamp", "solar_production_mw"])
        
    # Cas non convertible (si type objet et valeurs impossibles à parser)
    df_invalid = pd.DataFrame({
        "timestamp": ["impossible_to_parse_date"],
        "solar_production_mw": [1500.0]
    })
    with pytest.raises(DataValidationError, match="La colonne 'timestamp' ne peut pas être convertie"):
        validate_dataframe(df_invalid, ["timestamp", "solar_production_mw"])

def test_validate_dataframe_out_of_bounds_minor() -> None:
    """Valide que des timestamps légèrement hors plage stricte (battement de moins de 3 jours) ne lèvent pas d'exception."""
    # start_date = 2026-04-15 (00:00:00 UTC)
    # end_date = 2026-04-15 (23:59:59 UTC, + 1 jour de battement strict)
    
    # 1 jour de décalage (hors plage stricte, mais sous la limite des 3 jours de tolérance majeure)
    df = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-13 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    # Ne doit pas lever d'exception (génère un simple Warning)
    assert validate_dataframe(df, ["timestamp", "solar_production_mw"], "2026-04-15", "2026-04-15") is True

def test_validate_dataframe_out_of_bounds_major() -> None:
    """Valide que des timestamps franchement hors plage (plus de 3 jours de battement) lèvent une DataValidationError."""
    # 5 jours de décalage avant start_date
    df_too_old = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-09 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    with pytest.raises(DataValidationError, match="Timestamps franchement hors de la plage autorisée"):
        validate_dataframe(df_too_old, ["timestamp", "solar_production_mw"], "2026-04-15", "2026-04-15")
        
    # 5 jours de décalage après end_date
    df_too_new = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-21 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    with pytest.raises(DataValidationError, match="Timestamps franchement hors de la plage autorisée"):
        validate_dataframe(df_too_new, ["timestamp", "solar_production_mw"], "2026-04-15", "2026-04-15")
