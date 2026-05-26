import pandas as pd
import numpy as np
import logging

# Configuration du logger pour le nettoyage
logger = logging.getLogger("DataCleaning")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter('[%(asctime)s] %(levelname)s - %(name)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

def clean_dataset(df: pd.DataFrame, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    Nettoie le dataset selon les règles définies pour le projet SolarFlow.
    """
    initial_len = len(df)
    logger.info("Début du nettoyage. Lignes initiales : %d", initial_len)

    # Copie de travail
    df_clean = df.copy()

    # S'assurer que le timestamp est datetime et trié
    df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], utc=True)
    df_clean = df_clean.sort_values("timestamp")

    # a) Déduplication
    df_clean = df_clean.drop_duplicates(subset=["timestamp"])
    logger.info("Après déduplication : %d lignes (-%d)", len(df_clean), initial_len - len(df_clean))

    # c) Gestion des valeurs manquantes (Grille horaire)
    # Création d'un index complet si les dates sont fournies, ou basées sur les bornes du dataset
    if start_date and end_date:
        full_index = pd.date_range(start=pd.to_datetime(start_date, utc=True),
                                   end=pd.to_datetime(end_date, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(hours=1),
                                   freq="h")
    else:
        full_index = pd.date_range(start=df_clean["timestamp"].min(), end=df_clean["timestamp"].max(), freq="h")

    df_clean = df_clean.set_index("timestamp").reindex(full_index).rename_axis("timestamp").reset_index()
    logger.info("Après réindexation (grille complète) : %d lignes", len(df_clean))

    # b) Filtrage des valeurs aberrantes
    # Production négative -> 0
    neg_count = (df_clean["solar_production_mw"] < 0).sum()
    df_clean["solar_production_mw"] = df_clean["solar_production_mw"].clip(lower=0)
    logger.info("Mise à zéro des productions négatives : %d cas corrigés", neg_count)

    # Production > 20000 MW (impossible historique)
    high_count = (df_clean["solar_production_mw"] > 20000).sum()
    df_clean = df_clean[(df_clean["solar_production_mw"] <= 20000) | df_clean["solar_production_mw"].isna()]
    logger.info("Suppression des productions > 20000 MW : %d lignes supprimées", high_count)

    # Incohérence Météo : DHI supérieur au GHI (physiquement impossible car DHI est une fraction du GHI)
    # Note : DNI > GHI est suspect mais possible selon l'angle solaire (assouplissement de la règle stricte)
    tolerance = 1e-6
    invalid_meteo = (df_clean["dhi"] > df_clean["ghi"] + tolerance).sum()
    df_clean = df_clean[~(df_clean["dhi"] > df_clean["ghi"] + tolerance)]
    logger.info("Suppression des incohérences DHI > GHI : %d lignes supprimées (DNI > GHI toléré)", invalid_meteo)

    # c) Interpolation et Imputation
    # Météo : interpolation linéaire (limit 2h), puis ffill/bfill
    meteo_cols = ["ghi", "dni", "dhi"]
    for col in meteo_cols:
        nan_before = df_clean[col].isna().sum()
        df_clean[col] = df_clean[col].interpolate(method="linear", limit=2)
        df_clean[col] = df_clean[col].ffill().bfill()
        nan_after = df_clean[col].isna().sum()
        logger.info("Imputation %s : %d valeurs traitées", col, nan_before - nan_after)

    # Production : NaN remplacés par 0 (nuit)
    prod_nans = df_clean["solar_production_mw"].isna().sum()
    df_clean["solar_production_mw"] = df_clean["solar_production_mw"].fillna(0)
    logger.info("Imputation Production Solaire (NaN -> 0) : %d valeurs traitées", prod_nans)

    # Contrôle final
    critical_cols = ["timestamp", "solar_production_mw", "ghi", "dni", "dhi"]
    remaining_nans = df_clean[critical_cols].isna().sum()
    if remaining_nans.sum() > 0:
        logger.error("ALERTE : Il reste des NaN dans les colonnes critiques après nettoyage :\\n%s", remaining_nans[remaining_nans > 0])
    else:
        logger.info("Contrôle final réussi : Aucun NaN dans les colonnes critiques.")

    logger.info("Nettoyage terminé. Lignes finales : %d", len(df_clean))
    return df_clean

if __name__ == "__main__":
    import os

    # Fichier d'entrée/sortie
    input_file = "output/solarflow_2026-01-01_2026-04-27.csv"
    output_file = "output/solarflow_cleaned_2026-01-01_2026-04-27.csv"

    if os.path.exists(input_file):
        logger.info("Chargement du fichier brut : %s", input_file)
        df_raw = pd.read_csv(input_file)

        # On passe start_date et end_date connus du nom de fichier
        df_cleaned = clean_dataset(df_raw, start_date="2026-01-01", end_date="2026-04-27")

        df_cleaned.to_csv(output_file, index=False)
        logger.info("Fichier nettoyé sauvegardé sous : %s", output_file)
    else:
        logger.error("Le fichier d'entrée n'existe pas : %s", input_file)
