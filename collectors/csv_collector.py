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
            sep="\t",
            encoding="latin1",
            na_values=["N/A", "-", "ND", ""],
            on_bad_lines="skip",
        )
    except Exception as e:
        logger.error("Erreur lors de la lecture du fichier CSV %s : %s", filepath, e)
        return empty_df

    # Filtrage sur la Nature des données pour éviter les doublons (temps réel vs définitives)
    if "Nature" in df.columns:
        # On ne garde que les données temps réel pour la cohérence de l'échantillon
        df = df[df["Nature"].astype(str).str.contains("temps r", case=False, na=False)]

    # Nettoyage des colonnes temporelles
    df["Date"] = df["Date"].astype(str).str.strip()
    df["Heure"] = df["Heure"].astype(str).str.strip()

    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], format="%d/%m/%Y %H:%M")
    df["timestamp"] = df["timestamp"].dt.tz_localize("Europe/Paris", ambiguous="infer", nonexistent="shift_forward")
    df["timestamp"] = df["timestamp"].dt.tz_convert("UTC")
    # Détection robuste des colonnes (MW uniquement, exclure %)
    col_map = {}
    for col in df.columns:
        c_low = col.lower()
        if "mw" in c_low and "%" not in c_low:
            if "solaire" in c_low: col_map[col] = "solar_production_mw"
            elif "conso" in c_low: col_map[col] = "consumption_mw"
        if "gion" in c_low and "code" not in c_low: col_map[col] = "region"

    df = df.rename(columns=col_map)

    # Sécurité : éliminer les colonnes dupliquées après normalisation
    if df.columns.duplicated().any():
        logger.warning("Colonnes dupliquées détectées après renommage : %s. Suppression.", df.columns[df.columns.duplicated()].tolist())
        df = df.loc[:, ~df.columns.duplicated()]

    # S'assurer que les colonnes sont présentes, sinon créer des colonnes vides
    for c in ["solar_production_mw", "consumption_mw", "region"]:
        if c not in df.columns:
            df[c] = 0.0

    df = df[["timestamp", "region", "solar_production_mw", "consumption_mw"]]

    validate_dataframe(df, ["timestamp", "region", "solar_production_mw", "consumption_mw"], None, None)

    logger.info("CSV éCO2mix : %d enregistrements récupérés (chargement total sans filtre)", len(df))

    return df
