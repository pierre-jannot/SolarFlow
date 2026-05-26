import logging
import sys
import os
import pandas as pd

# Ajout du chemin racine pour l'import des modules locaux
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from collectors.meteo_collector import fetch_irradiance, fetch_irradiance_point

# Configuration du logging pour voir les messages internes du collecteur
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_meteo_modes():
    # Période de test courte (1 jour en avril pour avoir du soleil)
    start_date = "2026-04-15"
    end_date = "2026-04-15"
    
    # 1. Test MODE NATIONAL
    logger.info("--- TEST : MODE NATIONAL (GRILLE FRANCE) ---")
    config.USE_NATIONAL_IRRADIANCE = True
    df_national = fetch_irradiance(config.SOLAR_PARK_LAT, config.SOLAR_PARK_LON, start_date, end_date)
    
    # 2. Test MODE POINT UNIQUE (Montpellier)
    logger.info("\n--- TEST : MODE POINT UNIQUE (MONTPELLIER) ---")
    config.USE_NATIONAL_IRRADIANCE = False
    df_montpellier = fetch_irradiance_point(config.SOLAR_PARK_LAT, config.SOLAR_PARK_LON, start_date, end_date)
    
    # AFFICHAGE DES RÉSULTATS
    print("\n" + "="*50)
    print("RÉSULTATS DE LA COMPARAISON (GHI)")
    print("="*50)
    
    # On compare les valeurs à midi (12:00 UTC)
    target_time = f"{start_date} 12:00:00+00:00"
    val_nat = df_national[df_national['timestamp'].astype(str).str.contains("12:00:00")]['ghi'].values[0]
    val_mtp = df_montpellier[df_montpellier['timestamp'].astype(str).str.contains("12:00:00")]['ghi'].values[0]
    
    print(f"Heure analysée : {target_time}")
    print(f"GHI Moyenne Nationale : {val_nat:.2f} W/m²")
    print(f"GHI Montpellier seul   : {val_mtp:.2f} W/m²")
    
    if abs(val_nat - val_mtp) > 1:
        print("\nCONFIRMATION : Les valeurs sont différentes. Le mode national fonctionne.")
        print(f"Écart constaté : {abs(val_nat - val_mtp):.2f} W/m²")
    else:
        print("\nATTENTION : Les valeurs sont identiques. Vérifiez la configuration.")

if __name__ == "__main__":
    test_meteo_modes()
