import pandas as pd


def load_eco2mix(filepath):
    """Charge un fichier CSV éCO2mix et retourne un DataFrame normalisé.

    Args:
        filepath: chemin vers le fichier CSV éCO2mix

    Returns:
        DataFrame avec les colonnes timestamp, region, solar_production_mw, consumption_mw
    """
    df = pd.read_csv(
        filepath,
        sep=";",
        encoding="utf-8",
        na_values=["N/A", "-", "ND", ""],
        on_bad_lines="skip",
    )

    # Supprimer les lignes d'en-tête dupliquées insérées dans le fichier
    df = df[df["Date"] != "Date"]

    df["timestamp"] = pd.to_datetime(df["Date"] + " " + df["Heure"], format="%Y-%m-%d %H:%M")
    df = df.rename(columns={
        "Région": "region",
        "Solaire (MW)": "solar_production_mw",
        "Consommation (MW)": "consumption_mw",
<<<<<<< HEAD
        ## penser à ajouter le start dat end date à envoyer en requete API
=======
>>>>>>> 671a12d070bc43f5acf8b3127acbfc933a7b28eb
    })

    df = df[["timestamp", "region", "solar_production_mw", "consumption_mw"]]

    return df
