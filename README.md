# SolarFlow

Pipeline de collecte et d'agrégation de données pour la prévision de production solaire.
Développé en interne chez **GreenWatt** pour alimenter le modèle de prévision J+1 des parcs solaires.
Le pipeline collecte des données depuis trois sources (RTE, Open-Meteo, éCO2mix), les agrège et produit un dataset horodaté prêt à l'emploi.

## Schémas d'architecture

![Schémas d'architecture](./assets/schemas_architecture.png)


- **API RTE** : production solaire réalisée et prévisions (données réseau national)
- **API Open-Meteo** : irradiance solaire horaire (GHI, DNI, DHI)
- **CSV éCO2mix** : historique régional de production par filière

## Prérequis

- **Python 3.13**
- **Credentials API RTE** : créer un compte sur [data.rte-france.com](https://data.rte-france.com), puis créer une application pour obtenir un `client_id` et un `client_secret`. L'accès à l'endpoint de production réelle est gratuit mais nécessite une validation du compte.

## Installation

```bash
# Installation de Python 3.13
winget install --id Python.Python.3.13 --exact
# Créer un environnement virtuel
py -3.13 -m venv .venv
source .venv/bin/activate      # Linux/macOS
.venv\Scripts\activate         # Windows

# Installer les dépendances (versions épinglées)
pip install -r requirements.txt

# Configurer les variables d'environnement
cp .env.example .env           # Linux/macOS
copy .env.example .env         # Windows
# Éditer .env et renseigner vos credentials RTE
```

## Utilisation

```bash
python main.py --start-date 2026-01-01 --end-date 2026-04-27
```

Options :
- `--start-date` : date de début (format YYYY-MM-DD, défaut : veille)
- `--end-date` : date de fin (format YYYY-MM-DD, défaut : aujourd'hui)
- `--output-format` : format de sortie `csv` ou `json` (défaut : `csv`)

Le fichier de sortie est généré dans le répertoire `output/`.

## Configuration

Copier `.env.example` vers `.env` et renseigner les variables suivantes :

| Variable | Description |
|---|---|
| `RTE_CLIENT_ID` | Client ID de l'application RTE (portail data.rte-france.com) |
| `RTE_CLIENT_SECRET` | Client Secret associé |
| `SOLAR_PARK_LAT` | Latitude du parc solaire (coordonnées GPS) |
| `SOLAR_PARK_LON` | Longitude du parc solaire |
| `OUTPUT_DIR` | Répertoire de sortie des fichiers générés |

## Sources de données

- **API RTE** : [https://data.rte-france.com](https://data.rte-france.com) — Portail open data de RTE. Nécessite une inscription et la création d'une application pour obtenir les credentials OAuth2.
- **Open-Meteo** : [https://open-meteo.com/en/docs](https://open-meteo.com/en/docs) — API météo ouverte, sans authentification. Données d'irradiance solaire au niveau horaire.
- **éCO2mix** : [https://www.data.gouv.fr](https://www.data.gouv.fr) — Rechercher "éCO2mix" pour télécharger les historiques régionaux de production électrique par filière.

## Données de test

Un fichier d'exemple `data/eco2mix_sample.csv` est fourni pour tester le pipeline sans accès réseau.

## TODO (notes du dev précédent)

- TODO: Le refresh automatique du token RTE n'est pas encore implémenté proprement, pour l'instant on utilise un token fixe (à améliorer).
- TODO: Ajouter de la gestion d'erreur sur le parsing CSV, ça plante parfois sur certains fichiers.
- TODO: Il faudrait ajouter des tests.
