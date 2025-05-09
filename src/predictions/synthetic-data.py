import pandas as pd
import numpy as np
from datetime import datetime

# Generar datos sintéticos
np.random.seed(42)
n_samples = 1000
medicamentos = [f"Med_{i}" for i in range(1, 21)]  # 20 medicamentos
meses = range(1, 13)
anios = range(2023, 2025)
regiones = ["Norte", "Sur", "Este", "Oeste"]
temporadas = ["Invierno", "Primavera", "Verano", "Otoño"]

data = {
    "medicamento_id": np.random.choice(medicamentos, n_samples),
    "mes": np.random.choice(meses, n_samples),
    "anio": np.random.choice(anios, n_samples),
    "region": np.random.choice(regiones, n_samples),
    "temporada": np.random.choice(temporadas, n_samples),
    "uso_previsto": np.random.randint(50, 300, n_samples),
    "uso_real": np.random.randint(40, 320, n_samples)
}

df = pd.DataFrame(data)

# Calcular diferencia del período anterior (simplificado)
df = df.sort_values(["medicamento_id", "anio", "mes"])
df["uso_prev_dif"] = df.groupby("medicamento_id")["uso_previsto"].diff().fillna(0)
df["uso_real_dif"] = df.groupby("medicamento_id")["uso_real"].diff().fillna(0)

# Guardar datos
df.to_csv("synthetic_medicine_usage.csv", index=False)