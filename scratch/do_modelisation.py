import nbformat
import subprocess
import os

nb_path = '../notebooks/modelisation.ipynb'

# 1. Chargement du notebook
with open(nb_path, 'r', encoding='utf-8') as f:
    nb = nbformat.read(f, as_version=4)

# 2. Ajout des cellules
cells_to_add = [
    nbformat.v4.new_markdown_cell("## 1. Feature Engineering\n\nAjout de variables cycliques pour l'heure (afin de capter le cycle jour/nuit) et de variables décalées (lags) pour capter l'inertie de la production."),
    nbformat.v4.new_code_cell("""
# Copie du dataset propre
df_fe = df_clean.copy()

# On s'assure que time est bien un datetime
df_fe['time'] = pd.to_datetime(df_fe['time'], utc=True)

# Variables cycliques (heure)
df_fe['hour_sin'] = np.sin(2 * np.pi * df_fe['time'].dt.hour / 24)
df_fe['hour_cos'] = np.cos(2 * np.pi * df_fe['time'].dt.hour / 24)

# Variables décalées (Lags)
df_fe = df_fe.sort_values('time')
df_fe['prod_lag_1h'] = df_fe['solar_production_mw'].shift(1)
df_fe['prod_lag_24h'] = df_fe['solar_production_mw'].shift(24)

# Suppression des NaN induits par le shift
df_fe = df_fe.dropna()

print(f"Dataset après Feature Engineering : {df_fe.shape[0]} lignes")
"""),
    nbformat.v4.new_markdown_cell("## 2. Entraînement sur données Nettoyées & Enrichies"),
    nbformat.v4.new_code_cell("""
# Nouvelles features
new_features = features + ['hour_sin', 'hour_cos', 'prod_lag_1h', 'prod_lag_24h']

X_clean_fe = df_fe[new_features]
y_clean_fe = df_fe[target]

X_train_clean, X_test_clean, y_train_clean, y_test_clean = train_test_split(
    X_clean_fe, y_clean_fe, test_size=0.2, random_state=42, shuffle=False # Pas de shuffle car séries temporelles
)

print("Entraînement du modèle amélioré...")
model_clean = RandomForestRegressor(n_estimators=100, random_state=42)
model_clean.fit(X_train_clean, y_train_clean)

y_pred_clean = model_clean.predict(X_test_clean)

rmse_clean = np.sqrt(mean_squared_error(y_test_clean, y_pred_clean))
mae_clean = mean_absolute_error(y_test_clean, y_pred_clean)
r2_clean = r2_score(y_test_clean, y_pred_clean)

print(f"\\n[RÉSULTATS NETTOYÉS & ENRICHIS]")
print(f"RMSE : {rmse_clean:.2f} MW")
print(f"MAE  : {mae_clean:.2f} MW")
print(f"R²   : {r2_clean:.4f}")
"""),
    nbformat.v4.new_markdown_cell("## 3. Visualisation des Performances"),
    nbformat.v4.new_code_cell("""
plt.figure(figsize=(10, 6))
plt.scatter(y_test_clean, y_pred_clean, alpha=0.5, color='royalblue')
plt.plot([y_test_clean.min(), y_test_clean.max()], [y_test_clean.min(), y_test_clean.max()], 'r--', lw=2)
plt.title("Prédictions vs Valeurs Réelles (Modèle sur données enrichies)")
plt.xlabel("Production Réelle (MW)")
plt.ylabel("Production Prédite (MW)")
plt.tight_layout()
plt.show()

# Graphique de la série temporelle (réel vs prédit sur un sous-échantillon test)
test_dates = df_fe['time'].iloc[-len(y_test_clean):]

plt.figure(figsize=(14, 5))
plt.plot(test_dates[:150], y_test_clean[:150].values, label="Réel", color='darkorange', marker='.')
plt.plot(test_dates[:150], y_pred_clean[:150], label="Prédit", color='royalblue', linestyle='--', marker='.')
plt.title("Série temporelle : Réel vs Prédit (Zoom sur les 150 premières heures du test)")
plt.xlabel("Date")
plt.ylabel("Production (MW)")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()
""")
]

nb.cells.extend(cells_to_add)

# 3. Sauvegarde
with open(nb_path, 'w', encoding='utf-8') as f:
    nbformat.write(nb, f)

print("Mise à jour du notebook terminée.")

# 4. Exécution du notebook
print("Exécution du notebook (nbconvert)...")
subprocess.run(['python', '-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--inplace', nb_path], check=True)
print("Notebook exécuté avec succès.")

# 5. Conversion en PDF
print("Conversion en PDF...")
from convert_to_pdf import convert_to_pdf
import asyncio

out_pdf = '../notebooks/modelisation.pdf'
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
asyncio.run(convert_to_pdf(nb_path, out_pdf))
print(f"PDF généré à l'emplacement : {out_pdf}")
