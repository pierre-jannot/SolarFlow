import pandas as pd
from datetime import date

import logging

logger = logging.getLogger(__name__)


def validate_timestamps(start_date, end_date):
    """Vérifie que les dates du pipeline sont cohérentes avant tout appel API.

    Args:
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD
    """
    today = date.today()
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)

    # Vérifier que start_date est antérieure à end_date
    if start > end:
        raise ValueError(f"start_date ({start_date}) est postérieure à end_date ({end_date})")

    # Vérifier que les dates ne sont pas dans le futur
    if start > today:
        logger.warning("start_date [%s] est dans le futur — aucune donnée réelle disponible", start_date)
    if end > today:
        logger.warning("end_date [%s] est dans le futur — aucune donnée réelle disponible", end_date)


def validate_dataframe(df, source, expected_columns, start_date=None, end_date=None):
    """Valide un DataFrame en vérifiant les colonnes attendues et les plages de dates.

    Args:
        df: DataFrame à valider
        source: nom de la source de données (pour les messages d'erreur)
        expected_columns: liste des noms de colonnes attendues (ex: ["timestamp", "solar_production_mw"])
        start_date: date de début minimale (optionnel)
        end_date: date de fin maximale (optionnel)
    """

    # Vérifier que le DataFrame n'est pas vide
    if df.empty:
        raise ValueError(f"DataFrame vide pour la source {source}")

    # Vérifier les colonnes attendues
    for col in expected_columns:
        if col not in df.columns:
            raise ValueError(f"Colonne '{col}' manquante dans {source}")

    # Vérifier que les timestamps sont dans la plage attendue (si start_date et end_date sont fournis)
    if start_date is not None and end_date is not None and "timestamp" in df.columns:
        ts_min = df["timestamp"].min()
        ts_max = df["timestamp"].max()
        if ts_min > pd.Timestamp(end_date, tz="UTC") or ts_max < pd.Timestamp(start_date, tz="UTC"):
            logger.warning("Timestamps de [%s] hors plage [%s, %s] : [%s, %s]", source, start_date, end_date, ts_min, ts_max)
