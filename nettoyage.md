# Rapport de Nettoyage et d'Exploration - Projet SolarFlow

## État Civil du Dataset
* **Période** : 01/01/2026 au 27/04/2026
* **Échelle** : 100% Nationale (France Métropolitaine)
* **Sources** : RTE (API), Open-Meteo (API), éCO2mix (CSV)

## Journal des Obstacles Techniques et Solutions (Étape 2)

| Problème | Cause Racine | Solution Apportée | Impact |
| :--- | :--- | :--- | :--- |
| **Erreur Export PDF (500)** | Bug `asyncio` sur Windows avec Python 3.13 (moteur Playwright). | Création d'un script de conversion forçant le `ProactorEventLoop`. | Export PDF fonctionnel via `WebPDF`. |
| **Données CSV vides (0 lignes)** | Encodage `latin1` et séparateur `\t` (Tab) non standards. | Correction des paramètres de `pd.read_csv` dans `csv_collector.py`. | Chargement complet des 99 000 lignes du CSV. |
| **Dates CSV invalides (NaT)** | Format de date français `%d/%m/%Y` non reconnu par défaut. | Correction du masque de format dans `pd.to_datetime`. | Synchronisation temporelle rétablie. |
| **Plantage Heure d'été** | Heures inexistantes le 29/03/2026 (DST jump) lors de la localisation. | Ajout de `nonexistent='shift_forward'` dans `tz_localize`. | Stabilité du pipeline sur toute l'année. |
| **Données CSV gonflées (x4)** | Arrondi à l'heure pile avant la somme des régions dans l'agrégateur. | Déplacement de l'arrondi temporel *après* la somme nationale. | Consommation ramenée de 200 GW à ~50 GW (réel). |
| **Incohérence des échelles** | Filtrage régional (Occitanie) vs Production Nationale (RTE). | Suppression du filtre régional et agrégation des 12 régions métropolitaines. | Dataset 100% cohérent à l'échelle de la France. |
| **Erreur API RTE (400)** | Fuseau horaire `+02:00` écrit en dur pour des dates d'hiver. | Passage au format UTC (`Z`) pour toutes les requêtes API RTE. | Fin des erreurs de collecte RTE. |

## Règles de Nettoyage Appliquées (Qualité)
1. **Imputation** : Les trous de collecte sont imputés à `0 MW` pour la production solaire (choix conservateur).
2. **Filtrage** : Les valeurs de production négatives ou aberrantes (> 20 000 MW) sont supprimées.
3. **Double Agrégation** : Pour éCO2mix, calcul de la `Somme(Régions)` par 15min, puis `Moyenne(Heure)` pour l'alignement.
4. **Validation des types** : Tous les timestamps sont unifiés en UTC (Timezone Aware).

## Bilan Final
* **Taille finale nettoyée** : 2 808 lignes.
* **Fichier final** : `output/solarflow_cleaned_2026-01-01_2026-04-27.csv`
* **Verdict** : Le dataset est prêt pour la phase de modélisation (Étape 3).
