# Utilisation d’un LLM pour enrichir les règles de validation

## 1. Contexte

Dans le cadre du projet **SolarFlow** pour la startup **GreenWatt**, nous développons un pipeline de données industriel pour collecter, nettoyer et agréger des flux d'informations météorologiques et réseau. L'objectif final de ce pipeline est d'alimenter de façon robuste un modèle de machine learning de prévision de production solaire photovoltaïque à J+1.

Le pipeline intègre trois sources hétérogènes de données :
*   **RTE API** : Production solaire nationale réalisée (pas de temps horaire).
*   **Open-Meteo API** : Simulations d'irradiance solaire (GHI, DNI, DHI) pour une grille nationale.
*   **éCO2mix** : Fichiers d'historiques régionaux de consommation et de production électrique (pas de temps de 15 minutes).

La cible à prédire par nos modèles est la variable **`solar_production_mw`**. Le pipeline s'appuie principalement sur les variables météorologiques d'irradiance : **`ghi`**, **`dni`**, et **`dhi`**.

---

## 2. Schéma des données transmis au LLM

Le schéma de données consolidé soumis à l'analyse et à la validation active se compose des variables suivantes :
*   **`timestamp`** : Date et heure unifiées en UTC (Timezone Aware).
*   **`solar_production_mw`** : Production solaire nationale réalisée (MW, variable cible).
*   **`ghi`** (Global Horizontal Irradiance) : Rayonnement global reçu sur une surface horizontale ($W/m^2$).
*   **`dni`** (Direct Normal Irradiance) : Rayonnement direct perpendiculaire aux rayons solaires ($W/m^2$).
*   **`dhi`** (Diffuse Horizontal Irradiance) : Rayonnement diffus (ciel, nuages) reçu sur une surface horizontale ($W/m^2$).
*   **`solar_production_mw_csv`** : Production solaire estimée issue d'éCO2mix (MW).
*   **`consumption_mw`** : Consommation électrique nationale issue d'éCO2mix (MW).

---

## 3. Anomalies identifiées à l’étape 2

Lors de la phase préliminaire d'audit et d'exploration des données brutes, les anomalies et bruits de mesure suivants sont à identifier et nettoyer dans notre pipeline :
1.  **Doublons temporels** : Plages temporelles qui se chevauchent lors des requêtes d'API successives ou des recalages d'historiques.
2.  **Valeurs manquantes (NaN)** : Trous de collecte ponctuels dus à des interruptions temporaires de service des API.
3.  **Production solaire négative** : Bruits de mesure réseau rapportés par RTE (valeurs légèrement négatives non physiques pour du solaire).
4.  **Production solaire aberrante** : Valeurs de production dépassant le seuil maximal physique et historique en France (~22 000 MW installés en 2026).
5.  **Incohérences physiques d'irradiance** : Valeurs d'irradiance négatives ou hors-bornes atmosphériques.
6.  **Trous horaires entre sources** : Désalignements ou différences de fuseaux horaires empêchant une jointure immédiate.
7.  **Bug de merge d'éCO2mix** : Anomalie de fusion spatio-temporelle causant une multiplication artificielle par 4 des consommations et productions nationales lors de l'agrégation régionale (consommation nationale calculée à ~200 GW au lieu de ~50 GW).

---

## 4. Prompt envoyé au LLM

Le prompt suivant a été formulé de manière structurée et soumis à l'assistant IA afin d'étendre nos filtres physiques et de consolider notre approche de validation active :

```text
Tu es un ingénieur de données senior et un expert en physique de l'atmosphère appliquée à l'énergie solaire.
Nous développons le pipeline de données SolarFlow pour GreenWatt. Le but est de prédire la production photovoltaïque nationale "solar_production_mw" (cible) à partir d'irradiances météo : GHI, DNI, DHI (en W/m²).

Voici le schéma simplifié de nos données consolidées :
- timestamp (datetime, UTC)
- solar_production_mw (RTE, production nationale réelle en MW)
- ghi (Global Horizontal Irradiance en W/m²)
- dni (Direct Normal Irradiance en W/m²)
- dhi (Diffuse Horizontal Irradiance en W/m²)

Nous nettoyons déjà les doublons temporels, les valeurs négatives, les valeurs manquantes basiques (NaN) et la production > 22 000 MW.

Propose un ensemble de règles de validation physiques ou statistiques supplémentaires pour détecter des anomalies de capteurs solaires ou de simulation météo.
Pour chaque règle proposée, tu dois obligatoirement détailler :
1. Sa pertinence métier et son réalisme physique.
2. La logique mathématique ou le seuil d'implémentation.
3. Les risques de faux positifs (données saines rejetées à tort).
4. La sévérité recommandée : Validation bloquante (exception), Warning (log simple), ou Nettoyage passif (remplacement/imputation).
```

---

## 5. Synthèse de la réponse du LLM

*   **LLM utilisé** : ChatGPT (GPT-4o)
*   **Réponse obtenue** : Synthèse des propositions structurées par l'assistant IA :

1.  **Contrôle de sommation d'irradiance ($DHI \le GHI$)** :
    *   *Description* : Le rayonnement global ($GHI$) est composé de la lumière directe projetée et de la lumière diffuse ($DHI$). L'irradiance diffuse ne peut donc pas dépasser l'irradiance totale reçue sur une même surface horizontale.
    *   *Proposition* : Supprimer les lignes où $DHI > GHI$.
2.  **Prudence sur l'incohérence directe normale ($DNI > GHI$)** :
    *   *Description* : Le $DNI$ mesure le flux solaire sur un plan perpendiculaire (normal) aux rayons, tandis que le $GHI$ est mesuré sur un plan horizontal.
    *   *Proposition* : Lever un warning si $DNI > GHI$, mais ne pas exclure automatiquement la donnée car cette situation survient naturellement lors d'angles solaires rasants (lever/coucher de soleil ou hiver).
3.  **Contrôles sur les heures de nuit** :
    *   *Description* : En l'absence de soleil ($GHI \approx 0$), la production d'énergie photovoltaïque est physiquement impossible.
    *   *Proposition* : Si $GHI < 5\ W/m^2$, forcer la production solaire (`solar_production_mw`) à $0$ MW pour éliminer le bruit de mesure de fond du réseau.
4.  **Loi trigonométrique de sommation complète** :
    *   *Description* : Liaison géométrique stricte entre les trois composantes via l'angle zénithal solaire $\theta_z$ :
        $$GHI = DHI + DNI \times \cos(\theta_z)$$
    *   *Proposition* : Lever une exception bloquante si l'écart dépasse $\pm 10\%$ lorsque le soleil est levé.
5.  **Bornes physiques sur la météo** :
    *   *Description* : L'irradiance reçue au sol ne peut pas dépasser la constante solaire atmosphérique externe (~1361 $W/m^2$).
    *   *Proposition* : Configurer un seuil maximal strict de $1400\ W/m^2$ sur $GHI$, $DNI$ et $DHI$.

---

## 6. Analyse critique des règles proposées

| Règle proposée | Pertinence | Réalisme physique/statistique | Implémentabilité | Risque de faux positif | Décision | Justification |
| :--- | :--- | :--- | :--- | :--- | :---: | :--- |
| **1. Incohérence $DHI > GHI$** | **Maximale** | Absolu (100% physiquement vrai en journée) | Très simple (`dhi > ghi`) | **Nul** | **Retenue** | L'irradiance diffuse étant une sous-composante de l'irradiance globale reçue horizontalement, elle ne peut mathématiquement pas la dépasser. C'est une anomalie de capteur ou d'interpolation évidente. |
| **2. Prudence $DNI > GHI$** | Élevée | Élevé | Très simple | **Extrêmement élevé** | **Rejetée (Filtre strict) / Assouplie** | **Erreur physique classique du LLM.** Le $DNI$ est mesuré sur un plan perpendiculaire et le $GHI$ sur un plan horizontal. Au lever/coucher du soleil, le facteur de projection horizontale tend vers 0 ($\cos(\theta_z) \to 0$), faisant dépasser de loin le $DNI$ par rapport au $GHI$. Un filtrage strict éliminerait des données parfaitement valides du matin et du soir. Elle doit être tolérée. |
| **3. Relation trigonométrique complète** | Moyenne | Élevé théoriquement | Complexe (nécessite de calculer l'angle de position solaire en direct dans le code) | **Élevé** (micro-décalages de simulation d'Open-Meteo) | **Rejetée** | Trop lourde pour notre pipeline et génératrice de faux positifs par simple imprécision géométrique ou décalage temporel des modèles de réanalyse météo. |
| **4. Forçage production nocturne à 0** | Élevée | Absolu (pas de lumière = pas d'électricité) | Très simple | **Faible** (bruits réseau de quelques MW) | **Ajustée (Warning / Imputation passive)** | Le forçage passif est plus adapté et moins destructeur que la levée d'exceptions bloquantes. C'est une correction de propreté utile pour l'apprentissage. |

---

## 7. Règles retenues

Dans le cadre d'une collaboration propre avec le groupe de travail, les décisions d'implémentation de la validation active ont été classées comme suit :

*   **Déjà implémentées dans le code existant du groupe** :
    *   Le filtrage des valeurs de production négatives (remplacées par 0) et le plafonnement des valeurs aberrantes de production solaires ($> 20\ 000$ MW) et météo sont déjà gérés de manière passive dans `processing/cleaner.py` sur `main`.
*   **Recommandées et proposées au groupe de travail (Non implémentées par moi)** :
    *   **Règle $DHI \le GHI$** : Règle physique absolue identifiée par l'audit LLM. Elle est formellement proposée au groupe pour être intégrée dans la prochaine version du module `cleaner.py` sous la forme :
        ```python
        # Règle d'irradiance mutuelle recommandée (DHI ne peut pas dépasser GHI)
        tolerance = 1e-6
        df_clean = df_clean[~(df_clean["dhi"] > df_clean["ghi"] + tolerance)]
        ```
    *   **Validation Active active sur DataFrame** : Proposition de création d'une classe d'exception de validation bloquante `DataValidationError` en cas de DataFrame vide ou de colonnes manquantes critiques, à intégrer dans `utils.py`.
*   **À discuter avec le groupe** :
    *   Forçage de la production solaire à $0$ MW en dessous d'un seuil minimal de $GHI < 5\ W/m^2$ pour éliminer le bruit de mesure de fond de l'API RTE pendant les heures de nuit.

---

## 8. Règles rejetées ou assouplies

*   **Filtre strict $DNI \le GHI$ (Rejeté)** : Formellement rejeté pour éviter de détruire les mesures de début et fin de journée où le soleil est bas sur l'horizon.
*   **Règle trigonométrique complète (Rejetée)** : Écartée en raison de la complexité d'implémentation géométrique et du risque de faux positifs élevés.
*   **Règles de suppression trop agressives sur warnings temporels (Rejetées)** : Toutes les anomalies mineures de décalage temporel sont conservées sous forme de logs (warnings) plutôt que de déclencher des pannes bloquantes du pipeline.

---

## 9. Impact sur les métriques

« Les règles issues de l’analyse LLM n’ont pas été mesurées isolément. Elles sont intégrées ou proposées dans la stratégie globale de nettoyage. L’impact global du nettoyage est évalué dans le notebook de modélisation du projet. »

---

## 10. Limites

1.  **Limites d'un LLM** : L'assistant IA n'a pas de conscience géométrique intrinsèque. Sa suggestion d'appliquer une règle d'exclusion stricte sur $DNI > GHI$ prouve qu'il confond les plans de projection physique sans expertise humaine pour le corriger.
2.  **Besoin d'expertise métier** : Toutes les règles issues de l'IA doivent obligatoirement faire l'objet d'un audit de cohérence physique et météorologique sous peine d'éliminer des données saines et d'introduire des biais d'apprentissage.
3.  **Absence de mesure isolée** : L'impact de chaque règle de validation n'est pas mesurable individuellement sur les scores ML, mais fait partie d'une approche globale de fiabilisation du dataset.
