import os
from dotenv import load_dotenv

load_dotenv()

RTE_CLIENT_ID = os.getenv("RTE_CLIENT_ID")
RTE_CLIENT_SECRET = os.getenv("RTE_CLIENT_SECRET")

SOLAR_PARK_LAT = os.getenv("SOLAR_PARK_LAT", 43.6115).split(",")
SOLAR_PARK_LON = os.getenv("SOLAR_PARK_LON", 3.8772).split(",")

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")

RTE_TOKEN_URL = "https://digital.iservices.rte-france.com/token/oauth/"
RTE_BASE_URL = "https://digital.iservices.rte-france.com/open_api"
METEO_BASE_URL = "https://api.open-meteo.com/v1/forecast"
