# Rapport d'Exploitation et d'Analyse Critique du LLM — Projet SolarFlow

Ce document formalise l'intégration d'un grand modèle de langage (LLM) comme assistant d'ingénierie et de validation de données chez GreenWatt pour le projet SolarFlow, ainsi que notre analyse critique et physique des règles suggérées.

---

## 1. Contexte du brief
Le brief de SolarFlow impose de mettre en place un pipeline robuste pour alimenter un modèle de prévision de production solaire. L'Étape 3 exige d'utiliser un LLM pour enrichir la stratégie de nettoyage en lui soumettant le schéma de données et les premières anomalies détectées, puis d'évaluer de manière critique ses propositions physiques.

---

## 2. Schéma des données utilisées
Le dataset unifié en sortie de pipeline possède la structure temporelle et physique suivante :
* **`timestamp`** : date et heure unifiées en UTC (Timezone Aware).
* **`solar_production_mw`** : production solaire nationale réalisée en temps réel (RTE).
* **`ghi`** (Global Horizontal Irradiance) : irradiance globale reçue sur une surface horizontale ($W/m^2$).
* **`dni`** (Direct Normal Irradiance) : irradiance directe reçue sur une surface perpendiculaire aux rayons du soleil ($W/m^2$).
* **`dhi`** (Diffuse Horizontal Irradiance) : irradiance diffuse reçue sur une surface horizontale ($W/m^2$).
* **`solar_production_mw_csv`** : production solaire estimée issue d'éCO2mix.
* **`consumption_mw`** : consommation électrique nationale (éCO2mix).

---

## 3. Prompt envoyé au LLM
Voici l'instruction soumise à l'assistant IA pour guider sa réflexion :
```text
Tu es un expert senior en physique de l'atmosphère, météorologie et énergie solaire.
Dans le cadre de la prévision de production photovoltaïque pour GreenWatt, nous construisons un dataset contenant les variables suivantes :
- timestamp (UTC)
- solar_production_mw (RTE, production nationale)
- ghi (irradiance globale horizontale en W/m²)
- dni (irradiance directe normale en W/m²)
- dhi (irradiance diffuse horizontale en W/m²)

Nous avons déjà nettoyé les valeurs négatives et les productions absurdes (> 22 000 MW).
Quelles règles physiques strictes de cohérence mutuelle entre GHI, DNI, et DHI suggères-tu pour détecter d'éventuelles anomalies de capteurs ou de simulation météo ?
```

---

## 4. Synthèse des règles proposées par le LLM
Le LLM a suggéré plusieurs règles de cohérence :
1. **Borne physique absolue** : $GHI$, $DNI$, $DHI$ ne peuvent pas dépasser la constante solaire extraterrestre (~1361 $W/m^2$).
2. **Relation de sommation stricte** : L'irradiance globale est liée aux composantes directe et diffuse par la relation :
   $$GHI = DHI + DNI \times \cos(\theta_z)$$
   Où $\theta_z$ est l'angle zénithal du soleil.
3. **Incohérence directe** : $DHI > GHI$ ou $DNI > GHI$ doivent être traitées comme des anomalies physiques menant à la suppression de la ligne.

---

## 5. Analyse critique de l'auditeur senior

Une confrontation rigoureuse de ces propositions avec la physique solaire révèle une nuance majeure indispensable pour éviter des suppressions abusives de données :

### A. Règle $DHI > GHI$ : 🟢 **Retenue comme incohérence physique forte**
* **Justification** : Le rayonnement global horizontal ($GHI$) est par définition la somme de la composante diffuse reçue horizontalement ($DHI$) et de la composante directe projetée sur l'horizontale ($DNI \times \cos(\theta_z)$). Étant donné que les irradiances sont strictement positives ou nulles en journée, il est physiquement impossible que la composante diffuse dépasse le rayonnement global ($DHI > GHI$).
* **Décision** : Implémentée de manière stricte avec une tolérance numérique de $10^{-6}$ pour absorber les bruits de calcul. Toute ligne violant cette règle est supprimée.

### B. Règle $DNI > GHI$ : 🔴 **Rejetée comme anomalie certaine (Règle assouplie)**
* **Justification** : Le $DNI$ est mesuré sur un plan **perpendiculaire (normal)** au rayonnement solaire incident, alors que le $GHI$ est mesuré sur un plan **horizontal**. Lorsque le soleil est très bas sur l'horizon (angle zénithal $\theta_z$ proche de $90^\circ$ au lever/coucher du soleil ou en hiver), le facteur de projection $\cos(\theta_z)$ tend vers $0$.
* Dans ces conditions géométriques, le rayonnement direct projeté contribue très peu au plan horizontal, et on peut fréquemment observer des situations réelles où le rayonnement normal incident dépasse de loin le rayonnement horizontal ($DNI > GHI$).
* Présenter $DNI > GHI$ comme une anomalie certaine mènerait à éliminer de nombreuses données valides de début et fin de journée.
* **Décision** : Règle rejetée en tant que filtre d'exclusion stricte. Elle est tolérée dans le code de nettoyage pour préserver la richesse du dataset.

---

## 6. Règles de nettoyage et d'imputation retenues

Suite à l'analyse, la stratégie finale de nettoyage intègre :
1. **Élimination de $DHI > GHI$** : Filtrage strict (physiquement impossible).
2. **Tolérance de $DNI > GHI$** : Règle assouplie (physiquement possible).
3. **Imputation de la production** : Les valeurs manquantes (`NaN`) de production solaire sont imputées à $0$ MW (choix conservateur et physique pour les heures de nuit et de non-collecte).
4. **Interpolation linéaire météo** : Les petits trous d'irradiance ($\le 2$ heures consécutives) sont comblés par interpolation linéaire, puis par un mécanisme de propagation avant/arrière (`ffill`/`bfill`) pour garantir un dataset exempt de NaN sans perte de lignes.

---

## 7. Impact sur le projet
Les règles retenues ont été intégrées à la stratégie de nettoyage globale, dont l’impact est évalué via la comparaison données brutes vs données nettoyées. Cette démarche a permis de fiabiliser les données d'apprentissage sans introduire de biais de sur-nettoyage.
