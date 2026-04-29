import pandas as pd

import logging

logger = logging.getLogger(__name__)


def aggregate(rte_df, meteo_df, csv_df):
    """Agrège les données des trois sources sur le timestamp.

    Args:
        rte_df: DataFrame production RTE (timestamp, solar_production_mw)
        meteo_df: DataFrame irradiance Open-Meteo (timestamp, ghi, dni, dhi)
        csv_df: DataFrame éCO2mix (timestamp, region, solar_production_mw, consumption_mw)

    Returns:
        DataFrame unifié avec toutes les colonnes fusionnées sur le timestamp
    """
    # Normalisation des timestamps en UTC avant merge
    rte_df["timestamp"] = pd.to_datetime(rte_df["timestamp"], utc=True).dt.floor("h")
    meteo_df["timestamp"] = pd.to_datetime(meteo_df["timestamp"], utc=True).dt.floor("h")
    csv_df["timestamp"] = pd.to_datetime(csv_df["timestamp"], utc=True).dt.floor("h")

    csv_agg = csv_df.groupby("timestamp").agg(
        solar_production_mw_csv=("solar_production_mw", "sum"),
        consumption_mw=("consumption_mw", "sum"),
    ).reset_index()

    # TODO: nettoyer les données avant le merge ?
    merged = pd.merge(rte_df, meteo_df, on="timestamp", how="outer")
    merged = pd.merge(merged, csv_agg, on="timestamp", how="outer")
    """
    Un outer merge conserve tous les timestamps de toutes les sources, même ceux qui n'existent pas dans les autres.
    -   RTE a des timestamps que Open-Meteo n'a pas → lignes créées avec NaN
    -   éCO2mix après floor("h") a des timestamps qui ne matchent pas RTE/Meteo → encore des lignes fantômes

    """

    merged = merged.sort_values("timestamp").reset_index(drop=True)

    for col in merged.columns:
        n_nan = merged[col].isna().sum()
        if n_nan > 0:
            logger.warning("colonne '%s' contient %d NaN", col, n_nan)

    return merged
