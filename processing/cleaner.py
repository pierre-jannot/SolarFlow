import logging

logger = logging.getLogger(__name__)

# Seuils physiques maximum par colonne
PHYSICAL_MAX = {
    "solar_production_mw": 22000,   # production solaire nationale France (MW)
    "ghi": 1400,                    # irradiance globale horizontale (W/m²)
    "dni": 1000,                    # irradiance directe normale (W/m²)
    "dhi": 600,                     # irradiance diffuse horizontale (W/m²)
    "solar_production_mw_csv": 22000,
    "consumption_mw": 102000,       # consommation nationale max France (MW)
}


def clean_dataframe(df, source, columns):
    """Nettoie le DataFrame en corrigeant les valeurs négatives et hors bornes physiques.

    Args:
        df: DataFrame à nettoyer
        source: nom de la source de données (pour les messages d'erreur)
        columns: liste des noms de colonnes à vérifier (ex: ["solar_production_mw"])
    """
    df = df.copy()  # éviter de modifier le DataFrame original passé en argument

    for col in columns:
        if col not in df.columns:
            continue

        # Valeurs négatives, on les remplace par 0 (null)
        n_negative = (df[col] < 0).sum()    # nombre de valeurs négatives
        if n_negative > 0:
            logger.warning("colonne '%s' de [%s] contient %d valeurs négatives", col, source, n_negative)
            df[col] = df[col].clip(lower=0)

        # Valeurs au-dessus du seuil physique on les remplace par NaN
        if col in PHYSICAL_MAX:
            max_val = PHYSICAL_MAX[col]
            n_above = (df[col] > max_val).sum()
            if n_above > 0:
                logger.warning("colonne '%s' de [%s] contient %d valeurs au-dessus du seuil physique (%s)", col, source, n_above, max_val)
                df.loc[df[col] > max_val, col] = None

    return df
