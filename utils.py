import logging
import pandas as pd
from typing import List, Optional

logger = logging.getLogger(__name__)

class DataValidationError(ValueError):
    """Exception levée en cas d'erreur de validation critique sur un DataFrame."""
    pass

def validate_dataframe(
    df: Optional[pd.DataFrame],
    required_columns: List[str],
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> bool:
    """Valide la cohérence d'un DataFrame de manière active.

    Args:
        df: DataFrame à valider.
        required_columns: Liste des colonnes attendues.
        start_date: Date de début au format YYYY-MM-DD.
        end_date: Date de fin au format YYYY-MM-DD.

    Returns:
        bool: True si le DataFrame est valide.

    Raises:
        DataValidationError: En cas d'erreur de validation bloquante.
    """
    if df is None or df.empty:
        raise DataValidationError("Le DataFrame est vide ou None.")

    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise DataValidationError(f"Colonnes obligatoires manquantes : {missing_cols}")

    if "timestamp" in required_columns:
        # Vérifier que la colonne timestamp n'a pas de valeurs manquantes
        if df["timestamp"].isna().any():
            raise DataValidationError("La colonne 'timestamp' contient des valeurs NaT ou manquantes.")

        # S'assurer que le type est bien datetime
        if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
            try:
                df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            except Exception as e:
                raise DataValidationError(f"La colonne 'timestamp' ne peut pas être convertie en datetime : {e}")

        # Vérification des plages temporelles
        if start_date and end_date:
            start_dt = pd.to_datetime(start_date, utc=True)
            end_dt = pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1)

            # Seuil de tolérance majeure : 3 jours de battement avant/après
            major_tolerance_days = 3
            start_limit = start_dt - pd.Timedelta(days=major_tolerance_days)
            end_limit = end_dt + pd.Timedelta(days=major_tolerance_days)

            ts_min = df["timestamp"].min()
            ts_max = df["timestamp"].max()

            # Hors plage majeure -> Exception bloquante
            if ts_min < start_limit or ts_max > end_limit:
                raise DataValidationError(
                    f"Timestamps franchement hors de la plage autorisée (tolérance {major_tolerance_days} jours). "
                    f"Plage attendue : [{start_date}, {end_date}], Trouvé : [{ts_min}, {ts_max}]"
                )

            # Hors plage mineure -> Simple Warning
            out_of_bounds = df[(df["timestamp"] < start_dt) | (df["timestamp"] >= end_dt)]
            if not out_of_bounds.empty:
                logger.warning(
                    f"Validation : {len(out_of_bounds)} timestamps hors plage stricte [{start_date}, {end_date}], "
                    "mais tolérés dans la limite majeure."
                )

    logger.info(f"Validation active réussie pour le DataFrame ({len(df)} lignes).")
    return True
