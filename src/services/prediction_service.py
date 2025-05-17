from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc
import numpy as np
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from src.models.prediction import Prediction
from src.models import Medicamento, MedicamentoCondicion
from datetime import datetime
import matplotlib.pyplot as plt

class PredictionService:
    @staticmethod
    def calculate_icum(real_usage: List[float], predicted_usage: List[float]) -> float:
        """
        Calcula el ICUM (Índice de Consumo de Uso Mensual).
        """
        if not real_usage or not predicted_usage or len(real_usage) != len(predicted_usage):
            raise ValueError("Las listas de uso real y previsto deben tener el mismo tamaño y no estar vacías.")
        
        n = len(real_usage)
        sum_real = sum(real_usage)
        if sum_real == 0:
            return 0.0
        
        sum_abs_diff = sum(abs(r - p) for r, p in zip(real_usage, predicted_usage))
        icum = (1 / n) * sum_real * (1 - (sum_abs_diff / sum_real))
        return icum

    @staticmethod
    def calculate_moving_average(data: List[float], window: int) -> float:
        """
        Calcula el promedio móvil de una lista de datos.
        """
        if len(data) < window:
            return 0.0
        return sum(data[-window:]) / window

    @staticmethod
    def get_conditions_vector(db: Session, medicamento_id: int, total_conditions: int = 15) -> List[int]:
        """
        Obtiene un vector binario de condiciones para un medicamento (one-hot encoding).
        """
        condition_ids = [
            mc.condicion_id for mc in db.query(MedicamentoCondicion)
            .filter(MedicamentoCondicion.medicamento_id == medicamento_id)
            .all()
        ]
        conditions_vector = [1 if i + 1 in condition_ids else 0 for i in range(total_conditions)]
        return conditions_vector

    @staticmethod
    def get_categories_vector(categoria_id: int, total_categories: int = 10) -> List[int]:
        """
        Obtiene un vector binario de categorías para un medicamento (one-hot encoding).
        """
        categories_vector = [1 if i + 1 == categoria_id else 0 for i in range(total_categories)]
        return categories_vector

    @staticmethod
    def get_tipos_toma_vector(tipo_toma_id: int, total_tipos_toma: int = 8) -> List[int]:
        """
        Obtiene un vector binario de tipos de toma para un medicamento (one-hot encoding).
        """
        tipos_toma_vector = [1 if i + 1 == tipo_toma_id else 0 for i in range(total_tipos_toma)]
        return tipos_toma_vector

    @staticmethod
    def prepare_data(db: Session, medicamento_id: int, months: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara los datos históricos para entrenar el modelo Random Forest, incluyendo condiciones, categorías y tipos de toma.
        
        Args:
            db (Session): Sesión de la base de datos.
            medicamento_id (int): ID del medicamento.
            months (int): Número de meses de datos históricos a considerar.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (X, y) donde X son las características y y es el target.
        """
        # Obtener datos históricos
        historical_data = (
            db.query(Prediction)
            .filter(Prediction.medicamento_id == medicamento_id)
            .order_by(Prediction.fecha.asc())
            .limit(months)
            .all()
        )

        if len(historical_data) < 4:  # Necesitamos al menos 4 meses para características avanzadas
            raise ValueError("Se necesitan al menos 4 meses de datos históricos.")

        # Obtener información del medicamento (para categoría y tipo de toma)
        medicamento = db.query(Medicamento).filter(Medicamento.id == medicamento_id).first()
        if not medicamento:
            raise ValueError("Medicamento no encontrado.")

        # Obtener vectores de características categóricas
        conditions_vector = PredictionService.get_conditions_vector(db, medicamento_id)
        categories_vector = PredictionService.get_categories_vector(medicamento.categoria_id)
        tipos_toma_vector = PredictionService.get_tipos_toma_vector(medicamento.tipo_toma_id)

        X = []  # Características
        y = []  # Target (desabastecimiento: 1 o 0)

        # Listas para calcular características históricas
        real_usages = [record.real_usage for record in historical_data]
        predicted_usages = [record.predicted_usage for record in historical_data]
        icums = []

        # Calcular ICUM para cada mes
        for i in range(len(historical_data)):
            icum = PredictionService.calculate_icum([real_usages[i]], [predicted_usages[i]])
            icums.append(icum)

        # Construir características para cada mes
        for i in range(3, len(historical_data) - 1):  # Empezamos en el mes 3 para tener datos históricos
            # Características básicas
            real_usage = historical_data[i].real_usage
            predicted_usage = historical_data[i].predicted_usage
            icum = icums[i]
            month_of_year = historical_data[i].month_of_year
            regional_demand = historical_data[i].regional_demand
            restock_time = historical_data[i].restock_time or 0

            # Características derivadas
            usage_diff = real_usage - predicted_usage
            moving_avg_3m = PredictionService.calculate_moving_average(real_usages[:i+1], 3)
            moving_avg_6m = PredictionService.calculate_moving_average(real_usages[:i+1], 6)
            usage_change = (real_usage - real_usages[i-1]) / real_usages[i-1] if real_usages[i-1] != 0 else 0
            icum_change = (icum - icums[i-1]) / icums[i-1] if icums[i-1] != 0 else 0

            # Vector de características: básicas + derivadas + condiciones + categorías + tipos de toma
            features = [
                real_usage,           # Uso real
                predicted_usage,      # Uso previsto
                icum,                 # ICUM
                usage_diff,           # Diferencia entre real y previsto
                moving_avg_3m,        # Promedio móvil 3 meses
                moving_avg_6m,        # Promedio móvil 6 meses
                usage_change,         # Tasa de cambio del uso
                icum_change,          # Tasa de cambio del ICUM
                month_of_year,        # Mes del año
                regional_demand,      # Demanda regional
                restock_time          # Tiempo de reabastecimiento
            ] + conditions_vector + categories_vector + tipos_toma_vector  # Añadir vectores categóricos

            X.append(features)

            # Target: ¿Hubo desabastecimiento en el siguiente mes?
            y.append(1 if historical_data[i + 1].stock <= 0 else 0)

        return np.array(X), np.array(y)

    @staticmethod
    def evaluate_model(db: Session, medicamento_id: int, months: int = 24) -> Dict:
        """
        Evalúa el modelo Random Forest con métricas detalladas.
        
        Args:
            db (Session): Sesión de la base de datos.
            medicamento_id (int): ID del medicamento.
            months (int): Número de meses de datos históricos a usar.
        
        Returns:
            Dict: Resultados de la evaluación (métricas, matriz de confusión, importancia de características, etc.).
        """
        # Preparar datos
        X, y = PredictionService.prepare_data(db, medicamento_id, months)
        if len(X) == 0 or len(y) == 0:
            raise ValueError("No hay suficientes datos históricos para evaluar el modelo.")

        # Dividir datos en entrenamiento y prueba
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Entrenar modelo
        model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
        model.fit(X_train, y_train)

        # Predicciones
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]  # Probabilidad de la clase positiva

        # Calcular métricas
        report = classification_report(y_test, y_pred, output_dict=True)
        conf_matrix = confusion_matrix(y_test, y_pred).tolist()

        # Validación cruzada (5-fold)
        cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1_weighted')
        cv_results = {
            "mean_f1_weighted": float(np.mean(cv_scores)),
            "std_f1_weighted": float(np.std(cv_scores))
        }

        # Curva ROC y AUC
        fpr, tpr, _ = roc_curve(y_test, y_prob)
        roc_auc = auc(fpr, tpr)

        # Guardar curva ROC
        plt.figure()
        plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
        plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
        plt.xlim([0.0, 1.0])
        plt.ylim([0.0, 1.05])
        plt.xlabel('False Positive Rate')
        plt.ylabel('True Positive Rate')
        plt.title('Receiver Operating Characteristic')
        plt.legend(loc="lower right")
        plt.savefig('roc_curve.png')

        # Importancia de características
        feature_names = [
            "real_usage", "predicted_usage", "icum", "usage_diff", "moving_avg_3m", "moving_avg_6m",
            "usage_change", "icum_change", "month_of_year", "regional_demand", "restock_time"
        ] + [f"condition_{i+1}" for i in range(15)] + [f"category_{i+1}" for i in range(10)] + [f"tipo_toma_{i+1}" for i in range(8)]
        feature_importances = dict(zip(feature_names, model.feature_importances_))

        return {
            "classification_report": report,
            "confusion_matrix": conf_matrix,
            "cross_validation": cv_results,
            "roc_auc": float(roc_auc),
            "feature_importances": feature_importances,
            "roc_curve": "Saved as roc_curve.png"
        }

    @staticmethod
    def predict_shortages(db: Session, medicamento_id: int, months: int = 24) -> Dict:
        """
        Predice desabastecimientos futuros usando Random Forest, incluyendo condiciones, categorías y tipos de toma.
        """
        # Preparar datos históricos
        X, y = PredictionService.prepare_data(db, medicamento_id, months)
        
        if len(X) == 0 or len(y) == 0:
            raise ValueError("No hay suficientes datos históricos para entrenar el modelo.")

        # Entrenar modelo Random Forest
        model = RandomForestClassifier(n_estimators=100, random_state=42, class_weight="balanced")
        model.fit(X, y)

        # Preparar datos para predicción (último mes disponible)
        historical_data = (
            db.query(Prediction)
            .filter(Prediction.medicamento_id == medicamento_id)
            .order_by(Prediction.fecha.asc())
            .limit(months)
            .all()
        )
        latest = historical_data[-1]
        
        # Obtener información del medicamento
        medicamento = db.query(Medicamento).filter(Medicamento.id == medicamento_id).first()

        # Calcular características para el último mes
        real_usages = [record.real_usage for record in historical_data]
        predicted_usages = [record.predicted_usage for record in historical_data]
        icums = [PredictionService.calculate_icum([r], [p]) for r, p in zip(real_usages, predicted_usages)]

        real_usage = latest.real_usage
        predicted_usage = latest.predicted_usage
        icum = icums[-1]
        usage_diff = real_usage - predicted_usage
        moving_avg_3m = PredictionService.calculate_moving_average(real_usages, 3)
        moving_avg_6m = PredictionService.calculate_moving_average(real_usages, 6)
        usage_change = (real_usage - real_usages[-2]) / real_usages[-2] if real_usages[-2] != 0 else 0
        icum_change = (icum - icums[-2]) / icums[-2] if icums[-2] != 0 else 0
        month_of_year = latest.month_of_year
        regional_demand = latest.regional_demand
        restock_time = latest.restock_time or 0

        # Obtener vectores de características categóricas
        conditions_vector = PredictionService.get_conditions_vector(db, medicamento_id)
        categories_vector = PredictionService.get_categories_vector(medicamento.categoria_id)
        tipos_toma_vector = PredictionService.get_tipos_toma_vector(medicamento.tipo_toma_id)

        # Características para predicción
        features = np.array([[
            real_usage,
            predicted_usage,
            icum,
            usage_diff,
            moving_avg_3m,
            moving_avg_6m,
            usage_change,
            icum_change,
            month_of_year,
            regional_demand,
            restock_time
        ] + conditions_vector + categories_vector + tipos_toma_vector])

        # Predecir desabastecimiento
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0][1]

        # Guardar predicción
        db_prediction = Prediction(
            medicamento_id=medicamento_id,
            fecha=datetime.now(),
            real_usage=real_usage,
            predicted_usage=predicted_usage,
            stock=latest.stock,
            month_of_year=(datetime.now().month),
            regional_demand=regional_demand,
            restock_time=restock_time,
            desabastecimiento=prediction,
            probability=probability
        )
        db.add(db_prediction)
        db.commit()

        return {
            "medicamento_id": medicamento_id,
            "prediction": "Desabastecimiento" if prediction == 1 else "No desabastecimiento",
            "probability": probability,
            "features_used": features.tolist()
        }