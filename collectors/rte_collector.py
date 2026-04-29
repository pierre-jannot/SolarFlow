import base64
import json
import os
import requests
import pandas as pd

import config
import logging

_CACHE_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "cache")

logger = logging.getLogger(__name__)


def _cache_path(key):
    os.makedirs(_CACHE_DIR, exist_ok=True)
    return os.path.join(_CACHE_DIR, f"{key}.json")


def _get_token():
    credentials = base64.b64encode(
        f"{config.RTE_CLIENT_ID}:{config.RTE_CLIENT_SECRET}".encode()
    ).decode()
    headers = {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.post(
        config.RTE_TOKEN_URL,
        headers=headers,
        data={"grant_type": "client_credentials"},
    )
    token_data = response.json()
    return token_data["access_token"]


def fetch_rte_production(start_date, end_date):
    """Récupère la production solaire réalisée depuis l'API RTE.

    Args:
        start_date: date de début au format YYYY-MM-DD
        end_date: date de fin au format YYYY-MM-DD

    Returns:
        DataFrame avec les colonnes timestamp, solar_production_mw
    """
    logger.info("Récupération production RTE du %s au %s ...", start_date, end_date)

    cache_key = f"rte_{start_date}_{end_date}"
    cache_file = _cache_path(cache_key)

    if os.path.exists(cache_file):
        logger.debug("Chargement depuis le cache local : %s", cache_file)
        with open(cache_file, "r") as f:
            data = json.load(f)
    else:
        url = f"{config.RTE_BASE_URL}/actual_generation/v1/actual_generations_per_production_type"

        headers = {
            "Authorization": f"Bearer {_get_token()}",
            "Accept": "application/json",
        }

        params = {
            "start_date": f"{start_date}T00:00:00+02:00",
            "end_date": f"{end_date}T23:59:59+02:00",
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        with open(cache_file, "w") as f:
            json.dump(data, f)

    records = []
    for entry in data["actual_generations_per_production_type"]:
        if entry["production_type"] == "SOLAR":
            for value in entry["values"]:
                records.append({
                    "timestamp": value["start_date"],
                    "solar_production_mw": value["value"],
                })

    if not records:
        logger.warning("Aucune donnée SOLAR trouvée dans la réponse RTE (%s → %s)", start_date, end_date)

    df = pd.DataFrame(records)
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

    logger.info("RTE : %d enregistrements récupérés", len(df))
    return df
