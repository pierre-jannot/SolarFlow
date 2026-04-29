import argparse
import os
import sys
from datetime import date, timedelta

import pandas as pd

import config
from collectors.rte_collector import fetch_rte_production
from collectors.meteo_collector import fetch_irradiance
from collectors.csv_collector import load_eco2mix
from processing.aggregator import aggregate

import logging


# Configuration du logging pour une meilleure visibilité des étapes du pipeline
logging.basicConfig(
    level=logging.INFO,     # filtre: Changer en DEBUG pour plus de détails
    format="%(asctime)s [%(levelname)s] : %(name)s - %(message)s",  # 2026-04-28 14:32:05 [INFO] solarflow — Collecte RTE...
    datefmt="%Y-%m-%d %H:%M:%S",    
)

logger = logging.getLogger(__name__)


def parse_args():
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    today = date.today().strftime("%Y-%m-%d")

    parser = argparse.ArgumentParser(
        description="SolarFlow — pipeline de collecte de données solaires"
    )
    parser.add_argument("--start-date", default=yesterday, help="Date de début YYYY-MM-DD")
    parser.add_argument("--end-date", default=today, help="Date de fin YYYY-MM-DD")
    parser.add_argument(
        "--output-format",
        choices=["csv", "json"],
        default="csv",
        help="Format de sortie (csv ou json)",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    logger.info("SolarFlow démarré — période : %s → %s", args.start_date, args.end_date)

    # Récupérer les données de production solaire réalisée depuis l'API RTE
    logger.info("Collecte RTE...")
    try:
        rte_df = fetch_rte_production(args.start_date, args.end_date)
    except Exception as e:
        logger.error("Erreur lors de la collecte RTE : %s", e)
        sys.exit(1)

    # Récupérer les données d'irradiance pour la même période que RTE, en utilisant les coordonnées du parc solaire
    logger.info("Collecte Open-Meteo...")
    try:
        meteo_df = fetch_irradiance(
            config.SOLAR_PARK_LAT,
            config.SOLAR_PARK_LON,
            args.start_date,
            args.end_date,
        )
    except Exception as e:
        logger.error("Erreur lors de la collecte Open-Meteo : %s", e)
        sys.exit(1)

    # Récupérer les données du fichier CSV éCO2mix
    logger.info("Chargement CSV éCO2mix...")
    try:
        csv_df = load_eco2mix("data/eco2mix_sample.csv")
    except Exception as e:
        logger.error("Erreur lors du chargement du CSV éCO2mix : %s", e)
        sys.exit(1)
    
    # Agréger les données des trois sources sur le timestamp
    logger.info("Agrégation des sources...")
    try:
        result_df = aggregate(rte_df, meteo_df, csv_df)
    except Exception as e:
        logger.error("Erreur lors de l'agrégation des données : %s", e)
        sys.exit(1)

    # Enregistrer le résultat dans le dossier de sortie
    logger.info("Enregistrement des résultats...")
    try:
        os.makedirs(config.OUTPUT_DIR, exist_ok=True)
        output_path = os.path.join(
            config.OUTPUT_DIR,
            f"solarflow_{args.start_date}_{args.end_date}.{args.output_format}",
        )

        if args.output_format == "csv":
            result_df.to_csv(output_path, index=False)
        else:
            result_df.to_json(output_path, orient="records", date_format="iso", indent=2)

        logger.info("Dataset généré : %s (%d lignes)", output_path, len(result_df))
    except Exception as e:
        logger.error("Erreur lors de l'enregistrement des résultats : %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()
