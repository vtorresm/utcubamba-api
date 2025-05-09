import pandas as pd
import joblib
from typing import Dict, List, Union

# Cargar el modelo una vez al importar el módulo
try:
    model = joblib.load("random_forest_model_optimized.joblib")  # Ajustar ruta si es necesario
    MODEL_COLUMNS = model.feature_names_in_  # Columnas esperadas por el modelo
except Exception as e:
    raise Exception(f"Error al cargar el modelo: {str(e)}")

def predict_usage(data: Dict[str, Union[int, str, float]]) -> float:
    """
    Realiza una predicción del uso real de un medicamento utilizando el modelo Random Forest.

    Args:
        data (Dict[str, Union[int, str, float]]): Diccionario con los datos de entrada para la predicción.
            Ejemplo: {
                "medicamento_id": "Med_1",
                "mes": 5,
                "anio": 2025,
                "region": "Norte",
                "temporada": "Primavera",
                "uso_previsto": 90,
                "uso_prev_dif": 0
            }

    Returns:
        float: Uso predicho para el medicamento.
    """
    # Convertir el diccionario a un DataFrame
    df = pd.DataFrame([data])

    # Codificar variables categóricas
    df = pd.get_dummies(df, columns=["medicamento_id", "region", "temporada"], drop_first=True)

    # Alinear columnas con las esperadas por el modelo
    df = df.reindex(columns=MODEL_COLUMNS, fill_value=0)

    # Realizar la predicción
    prediction = model.predict(df)[0]
    return float(prediction)

def batch_predict_usage(data_list: List[Dict[str, Union[int, str, float]]]) -> List[float]:
    """
    Realiza predicciones en lote para múltiples entradas.

    Args:
        data_list (List[Dict[str, Union[int, str, float]]]): Lista de diccionarios con datos de entrada.

    Returns:
        List[float]: Lista de usos predichos.
    """
    # Convertir la lista de diccionarios a un DataFrame
    df = pd.DataFrame(data_list)

    # Codificar variables categóricas
    df = pd.get_dummies(df, columns=["medicamento_id", "region", "temporada"], drop_first=True)

    # Alinear columnas con las esperadas por el modelo
    df = df.reindex(columns=MODEL_COLUMNS, fill_value=0)

    # Realizar predicciones
    predictions = model.predict(df)
    return predictions.tolist()