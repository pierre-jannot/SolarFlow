import os
from dotenv import load_dotenv

load_dotenv()

RTE_CLIENT_ID = os.getenv("RTE_CLIENT_ID")
RTE_CLIENT_SECRET = os.getenv("RTE_CLIENT_SECRET")

SOLAR_PARK_LAT = float(os.getenv("SOLAR_PARK_LAT", 43.6115))
SOLAR_PARK_LON = float(os.getenv("SOLAR_PARK_LON", 3.8772))

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
SOLAR_REGION = os.getenv("SOLAR_REGION", "Occitanie")

USE_NATIONAL_IRRADIANCE = os.getenv("USE_NATIONAL_IRRADIANCE", "true").lower() == "true"
IRRADIANCE_GRID_RESOLUTION = float(os.getenv("IRRADIANCE_GRID_RESOLUTION", 1.0))

RTE_TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
RTE_BASE_URL = "https://digital.iservices.rte-france.com/open_api"
METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
