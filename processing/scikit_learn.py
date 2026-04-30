from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error

import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def load_csv(filepath):
    df = pd.read_csv(
    filepath,
    sep=",",
    encoding="utf-8",
    na_values=["N/A", "-", "ND", ""],
    on_bad_lines="skip",
    )
    return(df)

def main():
    df = load_csv("output/solarflow_2026-01-01_2026-04-27.csv")
    df = df.dropna()
    X = df[["ghi","dni","dhi"]]
    y = df["solar_production_mw"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = GradientBoostingRegressor()
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    print("MAE:", mae)

    r2 = r2_score(y_test, y_pred)
    print("R²:", r2)

    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    print("RMSE:", rmse)

    plt.scatter(y_test, y_pred, alpha=0.3)
    plt.xlabel("Valeurs réelles")
    plt.ylabel("Prédictions")
    plt.title("Test du modèle de prédicition")
    plt.show()

if __name__ == "__main__":
    main()