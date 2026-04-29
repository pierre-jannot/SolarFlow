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
    if not csv_df.empty:
        csv_df["timestamp"] = pd.to_datetime(csv_df["timestamp"], utc=True).dt.floor("h")

    # Filtrage régional
    target_region = getattr(config, "SOLAR_REGION", "Occitanie")
    if not csv_df.empty:
        csv_df = csv_df[csv_df["region"] == target_region]

    # Agrégation des puissances sur 15 min -> 1h
    # Remarque : on utilise sum car le brief le demande explicitement bien que ce soit une puissance.
    # Pour la correction du facteur 4, on devrait utiliser mean. Le prompt indique "somme des solar_production_mw et consumption_mw".
    # Je vais utiliser 'sum' tel que demandé dans le prompt pour cette tâche ("somme des...").
    if not csv_df.empty:
        csv_agg = csv_df.groupby("timestamp").agg(
            solar_production_mw_csv=("solar_production_mw", "sum"),
            consumption_mw=("consumption_mw", "sum"),
        ).reset_index()
    else:
        csv_agg = pd.DataFrame(columns=["timestamp", "solar_production_mw_csv", "consumption_mw"])

    # Jointures LEFT pour garder la référence sur les dates RTE/Météo demandées
    merged = pd.merge(rte_df, meteo_df, on="timestamp", how="left")
    merged = pd.merge(merged, csv_agg, on="timestamp", how="left")

    merged = merged.sort_values("timestamp").reset_index(drop=True)

    validate_dataframe(merged, ["timestamp"], start_date, end_date)
    
    logger.info("Agrégation terminée : %d lignes résultantes.", len(merged))
    return merged
