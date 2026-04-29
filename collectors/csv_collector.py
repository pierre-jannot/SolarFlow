import pandas as pd

import logging

logger = logging.getLogger(__name__)


def load_eco2mix(filepath):
    """Charge un fichier CSV éCO2mix et retourne un DataFrame normalisé.

    Args:
        filepath: chemin vers le fichier CSV éCO2mix

    Returns:
        DataFrame avec les colonnes timestamp, region, solar_production_mw, consumption_mw
    """
    logger.info("Chargement CSV éCO2mix : %s", filepath)

    initial_len = sum(1 for _ in open(filepath, encoding="utf-8")) - 1
    df = pd.read_csv(
        filepath,
        sep=";",
        encoding="utf-8",
        na_values=["N/A", "-", "ND", ""],
        on_bad_lines="skip",
    )
    skipped = initial_len - len(df)
    if skipped > 0:
        logger.warning("%d ligne(s) ignorées (format invalide) dans %s", skipped, filepath)

    # Supprimer les lignes d'en-tête dupliquées insérées dans le fichier
    df = df[df["Date"] != "Date"]

    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], format="%Y-%m-%d %H:%M")
    df = df.rename(columns={
        "Région": "region",
        "Solaire (MW)": "solar_production_mw",
        "Consommation (MW)": "consumption_mw",
        ## penser à ajouter le start dat end date à envoyer en requete API
    })

    df = df[["timestamp", "region", "solar_production_mw", "consumption_mw"]]
    
    logger.info("CSV éCO2mix : %d enregistrements récupérés", len(df))
    
    return df
