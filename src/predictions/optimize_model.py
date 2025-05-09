from sklearn.model_selection import GridSearchCV
  from sklearn.ensemble import RandomForestRegressor
  import pandas as pd

  # Cargar datos
  df = pd.read_csv("synthetic_medicine_usage.csv")
  df = pd.get_dummies(df, columns=["medicamento_id", "region", "temporada"], drop_first=True)
  X = df.drop(["uso_real", "uso_real_dif"], axis=1)
  y = df["uso_real"]

  # Definir parámetros para GridSearch
  param_grid = {
      "n_estimators": [50, 100, 200],
      "max_depth": [None, 10, 20],
      "min_samples_split": [2, 5]
  }
  model = RandomForestRegressor(random_state=42)
  grid_search = GridSearchCV(model, param_grid, cv=5, scoring="neg_mean_squared_error")
  grid_search.fit(X, y)

  print(f"Mejores parámetros: {grid_search.best_params_}")
  print(f"Mejor MSE: {-grid_search.best_score_:.2f}")

  # Guardar modelo optimizado
  import joblib
  joblib.dump(grid_search.best_estimator_, "random_forest_model_optimized.joblib")