import pytest
import pandas as pd
from unittest.mock import MagicMock
from main import main
import main as main_module

def test_pipeline_integration_nominal(mocker) -> None:
    """Valide l'exécution complète du pipeline avec des mocks de collecte réseau."""
    start_date = "2026-04-15"
    end_date = "2026-04-15"
    
    # 1. Mock de l'analyse des arguments CLI
    mock_args = MagicMock()
    mock_args.start_date = start_date
    mock_args.end_date = end_date
    mock_args.output_format = "csv"
    mocker.patch("main.parse_args", return_value=mock_args)
    
    # 2. Mock des collecteurs pour éviter les requêtes réseau
    # Données RTE simulées (1h en UTC)
    mock_rte = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "solar_production_mw": [1500.0]
    })
    mocker.patch("main.fetch_rte_production", return_value=mock_rte)
    
    # Données Meteo simulées
    mock_meteo = pd.DataFrame({
        "timestamp": [pd.Timestamp("2026-04-15 12:00:00", tz="UTC")],
        "ghi": [600.0],
        "dni": [400.0],
        "dhi": [200.0]
    })
    mocker.patch("main.fetch_irradiance", return_value=mock_meteo)
    
    # Données CSV éCO2mix simulées (Région unique, 4 quarts d'heure pour faire la moyenne)
    mock_csv = pd.DataFrame({
        "timestamp": [
            pd.Timestamp("2026-04-15 12:00:00+02:00"),
            pd.Timestamp("2026-04-15 12:15:00+02:00"),
            pd.Timestamp("2026-04-15 12:30:00+02:00"),
            pd.Timestamp("2026-04-15 12:45:00+02:00")
        ],
        "region": ["Occitanie"] * 4,
        "solar_production_mw": [10.0, 12.0, 14.0, 16.0],
        "consumption_mw": [5000.0, 5100.0, 5200.0, 5300.0]
    })
    # Normalisation UTC dans le mock comme le fait le vrai csv_collector
    mock_csv["timestamp"] = mock_csv["timestamp"].dt.tz_convert("UTC")
    mocker.patch("main.load_eco2mix", return_value=mock_csv)
    
    # 3. Espion pour capturer le DataFrame self passé à to_csv et empêcher l'écriture sur disque
    called_dfs = []
    called_paths = []
    def spy_to_csv(self, path_or_buf, *args, **kwargs):
        called_dfs.append(self)
        called_paths.append(path_or_buf)
        return None
        
    mocker.patch("pandas.DataFrame.to_csv", new=spy_to_csv)
    
    # 4. Exécution de main()
    main()
    
    # 5. Vérification des appels
    assert len(called_dfs) == 1
    assert "solarflow_2026-04-15_2026-04-15.csv" in str(called_paths[0])
    
    called_df = called_dfs[0]
    assert isinstance(called_df, pd.DataFrame)
    assert not called_df.empty
    
    # Vérifier l'unification des données
    assert "solar_production_mw" in called_df.columns
    assert "ghi" in called_df.columns
    assert "solar_production_mw_csv" in called_df.columns
    assert "consumption_mw" in called_df.columns
    
    # Vérifier le calcul de la moyenne éCO2mix sur les quarts d'heures de 12h UTC
    # La moyenne des quarts d'heure de solar_production_mw (10, 12, 14, 16) = 13.0
    assert called_df["solar_production_mw_csv"].iloc[0] == 13.0
    assert called_df["consumption_mw"].iloc[0] == 5150.0
