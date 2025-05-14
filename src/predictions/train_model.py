import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

# Cargar datos
df = pd.read_csv("data_entrenamiento.csv")

# Codificar variables categóricas
df = pd.get_dummies(df, columns=["medicamento_id", "region", "temporada"], drop_first=True)

# Características y objetivo
X = df.drop(["uso_real", "uso_real_dif"], axis=1)
y = df["uso_real"]

# Dividir datos
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entrenar modelo Random Forest
model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Predicciones
y_pred = model.predict(X_test)

# Evaluar modelo
mse = mean_squared_error(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"MSE: {mse:.2f}")
print(f"MAE: {mae:.2f}")
print(f"R²: {r2:.2f}")

# Guardar modelo (opcional)
import joblib
joblib.dump(model, "random_forest_model.joblib")