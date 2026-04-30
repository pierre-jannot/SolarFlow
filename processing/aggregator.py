import pandas as pd

import logging

from processing.get_duplicates import aggregate_duplicates_auto
from processing.cleaner import clean_dataframe

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
    csv_df = csv_df.sort_values(["region", "timestamp"])

    csv_df = (
        csv_df
        .set_index("timestamp")
        .groupby("region")
        .apply(lambda g: (
            g
            # gérer les doublons intra-région
            .groupby(level=0).mean()
            # resample horaire
            .resample("1h").mean()
            # interpolation temporelle
            .interpolate(method="time")
        ))
        .reset_index()
    )

    # Normalisation des timestamps en UTC avant merge
    rte_df["timestamp"] = pd.to_datetime(rte_df["timestamp"], utc=True).dt.floor("h")
    meteo_df["timestamp"] = pd.to_datetime(meteo_df["timestamp"], utc=True).dt.floor("h")
    csv_df["timestamp"] = pd.to_datetime(csv_df["timestamp"], utc=True).dt.floor("h")

    # Agrégation des doublons restants (ex: RTE a parfois 2 enregistrements à la même heure)
    rte_df = aggregate_duplicates_auto(rte_df, ["timestamp"])
    meteo_df = aggregate_duplicates_auto(meteo_df, ["timestamp"])
    csv_df = aggregate_duplicates_auto(csv_df, ["timestamp", "region"])

    csv_agg = csv_df.groupby("timestamp").agg(
        solar_production_mw_csv=("solar_production_mw", "sum"),
        consumption_mw=("consumption_mw", "sum"),
    ).reset_index()

    # Nettoyage des valeurs aberrantes avant le merge
    rte_df = clean_dataframe(rte_df, "RTE", ["solar_production_mw"])
    meteo_df = clean_dataframe(meteo_df, "Open-Meteo", ["ghi", "dni", "dhi"])
    csv_agg = clean_dataframe(csv_agg, "éCO2mix", ["solar_production_mw_csv", "consumption_mw"])

    merged = pd.merge(rte_df, meteo_df, on="timestamp", how="inner")
    merged = pd.merge(merged, csv_agg, on="timestamp", how="inner")
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

def aggregate_meteo_regions(data):
    """Agrège les données de open météo

    Args:
        data: les données open météo récupérées par l'appel API

    Returns:
        dictionnaire hourly avec les différentes zones moyennées
    """
    dfs = []
    for region in data:
        df = pd.DataFrame(region["hourly"])
        dfs.append(df)

    full = pd.concat(dfs)

    grouped = full.groupby("time").mean().reset_index()

    return {"hourly": grouped}