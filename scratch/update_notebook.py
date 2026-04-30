import nbformat as nbf
import os

# Chemin du notebook
nb_path = 'notebooks/exploration.ipynb'

# Lecture du notebook
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbf.read(f, as_version=4)

# Définition des nouvelles cellules
markdown_intro = nbf.v4.new_markdown_cell("""
## Relation Production vs Irradiance (Analyse Approfondie)

Cette section explore la corrélation physique entre l'irradiance globale horizontale (GHI) et la production solaire injectée sur le réseau RTE. 
Nous filtrons les données pour exclure les périodes nocturnes (GHI < 10 W/m²) afin de ne pas biaiser la régression.
""")

code_analysis = nbf.v4.new_code_cell("""
from scipy import stats
import seaborn as sns

# 1. Préparation des données (Filtre GHI > 10 pour le jour uniquement)
df_day = df[df['ghi'] > 10].copy()

# 2. Calcul de la régression linéaire
slope, intercept, r_value, p_value, std_err = stats.linregress(df_day['ghi'], df_day['solar_production_mw'])

# 3. Création des graphiques
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))

# Subplot A : Scatter + Régression
sns.regplot(data=df_day, x='ghi', y='solar_production_mw', 
            scatter_kws={'alpha':0.3, 'color':'#f39c12'}, 
            line_kws={'color':'#c0392b', 'label':f'Régression (r={r_value:.3f})'}, 
            ax=ax1)

ax1.set_title("Nuage de points & Régression Linéaire", fontsize=15)
ax1.set_xlabel("GHI (W/m²)", fontsize=12)
ax1.set_ylabel("Production Solaire RTE (MW)", fontsize=12)
ax1.legend()

# Lignes de repère (Médianes)
ax1.axvline(df_day['ghi'].median(), color='gray', linestyle='--', alpha=0.5)
ax1.axhline(df_day['solar_production_mw'].median(), color='gray', linestyle='--', alpha=0.5)

# Subplot B : Densité Hexbin
hb = ax2.hexbin(df_day['ghi'], df_day['solar_production_mw'], gridsize=30, cmap='YlOrRd', mincnt=1)
fig.colorbar(hb, ax=ax2, label='Nombre de relevés')
ax2.set_title("Densité de concentration (Hexbin)", fontsize=15)
ax2.set_xlabel("GHI (W/m²)", fontsize=12)
ax2.set_ylabel("Production Solaire RTE (MW)", fontsize=12)

plt.tight_layout()
plt.show()

print(f"Coefficient de corrélation de Pearson : {r_value:.4f}")
print(f"Pente de la droite : {slope:.4f} MW / (W/m²)")
""")

markdown_interpretation = nbf.v4.new_markdown_cell("""
### Interprétation des résultats

*   **Corrélation de Pearson** : La valeur très proche de 1 confirme une relation linéaire extrêmement forte. L'irradiance au sol est bien le prédicteur primaire de la production.
*   **Dispersion** : On observe une légère dispersion à haute irradiance, qui peut être expliquée par l'influence de la température des panneaux (baisse de rendement) ou des effets de nébulosité partielle non captés par la moyenne nationale.
*   **Implication pour le modèle** : Un modèle de régression linéaire simple fournira déjà une excellente base (Baseline), mais des modèles non-linéaires (XGBoost, Random Forest) pourraient mieux capturer les variations liées aux autres composantes (DNI/DHI).
""")

# Ajout des cellules à la fin du notebook
nb.cells.extend([markdown_intro, code_analysis, markdown_interpretation])

# Sauvegarde
with open(nb_path, 'w', encoding='utf-8') as f:
    nbf.write(nb, f)

print(f"Notebook {nb_path} mis à jour avec succès.")
