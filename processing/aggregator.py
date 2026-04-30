import pandas as pd
import logging
import config
from utils import validate_dataframe

logger = logging.getLogger(__name__)


def aggregate(rte_df, meteo_df, csv_df, start_date=None, end_date=None):
    """Agrège les données des trois sources sur le timestamp.

    Args:
        rte_df: DataFrame production RTE (timestamp, solar_production_mw)
        meteo_df: DataFrame irradiance Open-Meteo (timestamp, ghi, dni, dhi)
        csv_df: DataFrame éCO2mix (timestamp, region, solar_production_mw, consumption_mw)

    Returns:
        DataFrame unifié avec toutes les colonnes fusionnées sur le timestamp
    """
    logger.info("Début de l'agrégation des données...")
    
    # Normalisation des timestamps en UTC avant merge
    if not rte_df.empty:
        rte_df["timestamp"] = pd.to_datetime(rte_df["timestamp"], utc=True).dt.floor("h")
    if not meteo_df.empty:
        meteo_df["timestamp"] = pd.to_datetime(meteo_df["timestamp"], utc=True).dt.floor("h")
    # On ne floor pas csv_df ici, on le fait après la somme des régions


    # Agrégation nationale : somme de toutes les régions pour chaque timestamp (15 min)
    if not csv_df.empty:
        # 1. On somme les 12 régions pour chaque pas de temps réel (15 min)
        # On ne floor pas encore l'heure ici pour ne pas mélanger les quarts d'heure avant la somme
        csv_national = csv_df.groupby("timestamp").agg(
            solar_production_mw_csv=("solar_production_mw", "sum"),
            consumption_mw=("consumption_mw", "sum"),
        ).reset_index()

        # 2. On passe maintenant à l'échelle horaire (moyenne des 4 quarts d'heure)
        csv_national["timestamp"] = csv_national["timestamp"].dt.floor("h")
        csv_agg = csv_national.groupby("timestamp").agg(
            solar_production_mw_csv=("solar_production_mw_csv", "mean"),
            consumption_mw=("consumption_mw", "mean"),
        ).reset_index()
    else:
        csv_agg = pd.DataFrame(columns=["timestamp", "solar_production_mw_csv", "consumption_mw"])
    # Jointures OUTER pour ne perdre aucune donnée même si une source est vide (ex: RTE)
    merged = pd.merge(rte_df, meteo_df, on="timestamp", how="outer")
    merged = pd.merge(merged, csv_agg, on="timestamp", how="outer")

    merged = merged.sort_values("timestamp").reset_index(drop=True)

    validate_dataframe(merged, ["timestamp"], start_date, end_date)
    
    logger.info("Agrégation terminée : %d lignes résultantes.", len(merged))
    return merged
