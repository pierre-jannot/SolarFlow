import pandas as pd
import logging
from utils import validate_dataframe

logger = logging.getLogger(__name__)


def load_eco2mix(filepath, start_date=None, end_date=None):
    """Charge un fichier CSV éCO2mix et retourne un DataFrame normalisé.

    Args:
        filepath: chemin vers le fichier CSV éCO2mix
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD

    Returns:
        DataFrame avec les colonnes timestamp, region, solar_production_mw, consumption_mw
    """
    logger.info("Chargement CSV éCO2mix : %s", filepath)
    empty_df = pd.DataFrame(columns=["timestamp", "region", "solar_production_mw", "consumption_mw"])

    try:
        df = pd.read_csv(
            filepath,
            sep=";",
            encoding="utf-8",
            na_values=["N/A", "-", "ND", ""],
            on_bad_lines="skip",
        )
    except Exception as e:
        logger.error("Erreur lors de la lecture du fichier CSV %s : %s", filepath, e)
        return empty_df

    # Supprimer les lignes d'en-tête dupliquées insérées dans le fichier
    df = df[df["Date"] != "Date"]

    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], format="%Y-%m-%d %H:%M", utc=True)
    df = df.rename(columns={
        "Région": "region",
        "Solaire (MW)": "solar_production_mw",
        "Consommation (MW)": "consumption_mw",
    })

    df = df[["timestamp", "region", "solar_production_mw", "consumption_mw"]]

    if start_date and end_date:
        start_dt = pd.to_datetime(start_date, utc=True)
        end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)
        df = df[(df["timestamp"] >= start_dt) & (df["timestamp"] < end_dt)]

    validate_dataframe(df, ["timestamp", "region", "solar_production_mw", "consumption_mw"], start_date, end_date)

    logger.info("CSV éCO2mix : %d enregistrements récupérés (après filtrage temporel)", len(df))

    return df
