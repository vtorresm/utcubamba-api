from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import cross_val_score, train_test_split, TimeSeriesSplit
from sklearn.metrics import classification_report, confusion_matrix, roc_curve, auc, mean_squared_error
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.tsa.stattools import adfuller
import numpy as np
from typing import List, Dict, Tuple, Optional, Literal
from sqlalchemy.orm import Session
from src.models.prediction import Prediction, TrendDirection, AlertLevel
from src.models import Medication, Condition
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
from scipy import stats
import json

class PredictionService:
    MODEL_VERSION = "1.1.0"
    
    @staticmethod
    def _calculate_seasonality(usages: List[float], period: int = 12) -> float:
        """
        Calcula el coeficiente de estacionalidad de una serie temporal.
        
        Args:
            usages: Lista de valores de uso históricos
            period: Período de estacionalidad (por defecto 12 meses)
            
        Returns:
            float: Coeficiente de estacionalidad (0-1)
        """
        if len(usages) < 2 * period:
            return 0.0
            
        try:
            # Usar seasonal_decompose para obtener el componente estacional
            result = seasonal_decompose(usages, period=period, extrapolate_trend='freq')
            seasonal = result.seasonal[-period:]  # Último período completo
            
            # Calcular la fuerza de la estacionalidad (0-1)
            if np.var(usages) > 0:
                return float(np.var(seasonal) / np.var(usages))
            return 0.0
        except:
            return 0.0
    
    @staticmethod
    def _determine_trend(usages: List[float], threshold: float = 0.1) -> TrendDirection:
        """
        Determina la dirección de la tendencia basada en regresión lineal.
        
        Args:
            usages: Lista de valores de uso históricos
            threshold: Umbral para considerar la pendiente como significativa
            
        Returns:
            TrendDirection: Dirección de la tendencia (UP, DOWN o STABLE)
        """
        if len(usages) < 3:
            return TrendDirection.STABLE
            
        x = np.arange(len(usages)).reshape(-1, 1)
        y = np.array(usages)
        
        # Ajustar regresión lineal
        slope, intercept, r_value, p_value, std_err = stats.linregress(x.ravel(), y)
        
        # Determinar dirección basada en la pendiente
        if abs(slope) < threshold:
            return TrendDirection.STABLE
        return TrendDirection.UP if slope > 0 else TrendDirection.DOWN
    
    @staticmethod
    def _determine_alert_level(probability: float, stock_days: float) -> AlertLevel:
        """
        Determina el nivel de alerta basado en la probabilidad y días de stock.
        
        Args:
            probability: Probabilidad de desabastecimiento (0-1)
            stock_days: Días de stock disponibles
            
        Returns:
            AlertLevel: Nivel de alerta (LOW, MEDIUM, HIGH)
        """
        if stock_days < 7 or probability > 0.7:
            return AlertLevel.HIGH
        elif stock_days < 14 or probability > 0.4:
            return AlertLevel.MEDIUM
        return AlertLevel.LOW
    
    @staticmethod
    def _generate_alert_message(
        prediction: bool, 
        probability: float, 
        stock: float,
        trend: TrendDirection
    ) -> str:
        """Genera un mensaje de alerta descriptivo."""
        if prediction:
            if stock <= 0:
                return f"¡Desabastecimiento inminente! Stock agotado."
            return (
                f"Riesgo alto de desabastecimiento en {stock:.0f} días. "
                f"Tendencia: {trend.value.upper()}. "
                f"Probabilidad: {probability*100:.1f}%"
            )
        return "Sin riesgo de desabastecimiento en el corto plazo"
    
    @staticmethod
    def _calculate_confidence_intervals(
        model: RandomForestRegressor, 
        X: np.ndarray, 
        confidence: float = 0.95
    ) -> Tuple[float, float]:
        """
        Calcula intervalos de confianza para predicciones de Random Forest.
        
        Args:
            model: Modelo Random Forest entrenado
            X: Características para predicción
            confidence: Nivel de confianza (0-1)
            
        Returns:
            Tuple[float, float]: Límites inferior y superior del intervalo
        """
        predictions = []
        for tree in model.estimators_:
            predictions.append(tree.predict(X.reshape(1, -1))[0])
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        z_score = stats.norm.ppf((1 + confidence) / 2)
        margin = z_score * std
        
        return float(mean - margin), float(mean + margin)
    
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
    def get_conditions_vector(db: Session, medication_id: int, total_conditions: int = 15) -> List[int]:
        """
        Obtiene un vector binario de condiciones para un medicamento (one-hot encoding).
        """
        # Obtener las condiciones directamente desde la relación del medicamento
        medication = db.query(Medication).filter(Medication.id == medication_id).first()
        if not medication:
            return [0] * total_conditions
            
        # Usar las condiciones ya cargadas en la relación
        condition_ids = [cond.id for cond in medication.conditions]
        conditions_vector = [1 if i + 1 in condition_ids else 0 for i in range(total_conditions)]
        return conditions_vector

    @staticmethod
    def get_categories_vector(category_id: int, total_categories: int = 10) -> List[int]:
        """
        Obtiene un vector binario de categorías para un medicamento (one-hot encoding).
        """
        categories_vector = [1 if i + 1 == category_id else 0 for i in range(total_categories)]
        return categories_vector

    @staticmethod
    def get_intake_type_vector(intake_type_id: int, total_intake_types: int = 8) -> List[int]:
        """
        Obtiene un vector binario de tipos de ingesta para un medicamento (one-hot encoding).
        """
        intake_type_vector = [1 if i + 1 == intake_type_id else 0 for i in range(total_intake_types)]
        return intake_type_vector

    @staticmethod
    def prepare_data(db: Session, medication_id: int, months: int = 24) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepara los datos históricos para entrenar el modelo Random Forest, incluyendo condiciones, categorías y tipos de ingesta.
        
        Args:
            db (Session): Sesión de la base de datos.
            medication_id (int): ID del medicamento.
            months (int): Número de meses de datos históricos a considerar.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: (X, y) donde X son las características y y es el target.
        """
        # Obtener datos históricos
        historical_data = (
            db.query(Prediction)
            .filter(Prediction.medication_id == medication_id)
            .order_by(Prediction.date.asc())
            .limit(months)
            .all()
        )

        if len(historical_data) < 4:  # Necesitamos al menos 4 meses para características avanzadas
            raise ValueError("Se necesitan al menos 4 meses de datos históricos.")

        # Obtener información del medicamento (para categoría y tipo de ingesta)
        medication = db.query(Medication).filter(Medication.id == medication_id).first()
        if not medication:
            raise ValueError("Medicamento no encontrado.")

        # Obtener vectores de características categóricas
        conditions_vector = PredictionService.get_conditions_vector(db, medication_id)
        categories_vector = PredictionService.get_categories_vector(medication.category_id)
        intake_type_vector = PredictionService.get_intake_type_vector(medication.intake_type_id)

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

            # Vector de características: básicas + derivadas + condiciones + categorías + tipos de ingesta
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
            ] + conditions_vector + categories_vector + intake_type_vector  # Añadir vectores categóricos

            X.append(features)

            # Target: ¿Hubo desabastecimiento en el siguiente mes?
            y.append(1 if historical_data[i + 1].stock <= 0 else 0)

        return np.array(X), np.array(y)

    @staticmethod
    def evaluate_model(db: Session, medication_id: int, months: int = 24) -> Dict:
        """
        Evalúa el modelo Random Forest con métricas detalladas.
        
        Args:
            db (Session): Sesión de la base de datos.
            medication_id (int): ID del medicamento.
            months (int): Número de meses de datos históricos a usar.
        
        Returns:
            Dict: Resultados de la evaluación (métricas, matriz de confusión, importancia de características, etc.).
        """
        # Preparar datos
        X, y = PredictionService.prepare_data(db, medication_id, months)
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
        feature_importances = model.feature_importances_
        feature_names = [
            'real_usage', 'predicted_usage', 'icum', 'usage_diff',
            'moving_avg_3m', 'moving_avg_6m', 'usage_change', 'icum_change',
            'month_of_year', 'regional_demand', 'restock_time'
        ] + [f'condition_{i+1}' for i in range(15)] + \
            [f'category_{i+1}' for i in range(10)] + \
            [f'intake_type_{i+1}' for i in range(8)]

        # Obtener las 10 características más importantes
        top_n = 10
        top_indices = np.argsort(feature_importances)[-top_n:][::-1]
        top_features = [{
            'name': feature_names[i],
            'importance': float(feature_importances[i])
        } for i in top_indices]

        # Resultados finales
        results = {
            'model_type': 'RandomForestClassifier',
            'parameters': {
                'n_estimators': 100,
                'random_state': 42,
                'class_weight': 'balanced'
            },
            'metrics': {
                'accuracy': report['accuracy'],
                'precision': report['weighted avg']['precision'],
                'recall': report['weighted avg']['recall'],
                'f1_score': report['weighted avg']['f1-score'],
                'roc_auc': roc_auc,
                'confusion_matrix': conf_matrix,
                'cv_scores': cv_results
            },
            'feature_importance': top_features,
            'roc_curve': 'roc_curve.png',
            'training_samples': len(X_train),
            'test_samples': len(X_test),
            'timestamp': datetime.now().isoformat()
        }

        return results

    @classmethod
    def predict_shortages(
        cls, 
        db: Session, 
        medication_id: int, 
        months: int = 24
    ) -> Dict:
        """
        Predice desabastecimientos futuros usando Random Forest con características avanzadas.
        
        Args:
            db: Sesión de la base de datos
            medication_id: ID del medicamento a predecir
            months: Número de meses de datos históricos a considerar
            
        Returns:
            Dict con la predicción y metadatos
        """
        # Obtener datos históricos
        historical_data = (
            db.query(Prediction)
            .filter(Prediction.medication_id == medication_id)
            .order_by(Prediction.date.desc())
            .limit(months + 6)  # Tomar meses adicionales para análisis de tendencia
            .all()
        )
        historical_data = list(reversed(historical_data))  # Ordenar de más antiguo a más reciente
        
        if len(historical_data) < 4:
            raise ValueError("Se necesitan al menos 4 meses de datos históricos.")
            
        # Obtener información del medicamento
        medication = db.query(Medication).filter(Medication.id == medication_id).first()
        if not medication:
            raise ValueError("Medicamento no encontrado")
            
        # Preparar datos para análisis
        real_usages = [record.real_usage for record in historical_data]
        predicted_usages = [record.predicted_usage for record in historical_data]
        stocks = [record.stock for record in historical_data]
        dates = [record.date for record in historical_data]
        
        # Calcular métricas avanzadas
        seasonality_coeff = cls._calculate_seasonality(real_usages)
        trend = cls._determine_trend(real_usages)
        avg_consumption = np.mean(real_usages[-6:])  # Consumo promedio de los últimos 6 meses
        stock_days = (stocks[-1] / avg_consumption * 30) if avg_consumption > 0 else 0  # Días de stock restantes
        
        # Preparar características para el modelo
        latest = historical_data[-1]
        
        # Calcular características avanzadas
        usage_diff = latest.real_usage - latest.predicted_usage
        moving_avg_3m = cls.calculate_moving_average(real_usages, 3)
        moving_avg_6m = cls.calculate_moving_average(real_usages, 6)
        
        # Obtener vectores de características categóricas
        conditions_vector = cls.get_conditions_vector(db, medication_id)
        categories_vector = cls.get_categories_vector(medication.category_id)
        intake_type_vector = cls.get_intake_type_vector(medication.intake_type_id)
        
        # Preparar características para el modelo
        features = np.array([[
            latest.real_usage,           # Uso real
            latest.predicted_usage,      # Uso previsto
            usage_diff,                  # Diferencia entre real y previsto
            moving_avg_3m,               # Promedio móvil 3 meses
            moving_avg_6m,               # Promedio móvil 6 meses
            seasonality_coeff,           # Coeficiente de estacionalidad
            trend.value,                 # Tendencia (0=STABLE, 1=UP, 2=DOWN)
            latest.month_of_year,        # Mes del año (estacionalidad)
            latest.regional_demand,      # Demanda regional
            latest.restock_time or 0,    # Tiempo de reabastecimiento
            stock_days,                  # Días de stock restantes
        ] + conditions_vector + categories_vector + intake_type_vector])
        
        # Entrenar modelo con datos históricos
        X, y = cls.prepare_data(db, medication_id, months)
        if len(X) == 0 or len(y) == 0:
            raise ValueError("No hay suficientes datos para entrenar el modelo.")
            
        model = RandomForestClassifier(
            n_estimators=100, 
            random_state=42, 
            class_weight="balanced",
            n_jobs=-1
        )
        model.fit(X, y)
        
        # Hacer predicción
        prediction = model.predict(features)[0]
        probability = model.predict_proba(features)[0][1]
        
        # Calcular intervalos de confianza
        lower_bound, upper_bound = cls._calculate_confidence_intervals(
            model, features[0], confidence=0.95
        )
        
        # Determinar nivel y mensaje de alerta
        alert_level = cls._determine_alert_level(probability, stock_days)
        alert_message = cls._generate_alert_message(
            prediction=bool(prediction),
            probability=probability,
            stock=stock_days,
            trend=trend
        )
        
        # Preparar metadatos adicionales
        metadata = {
            "model_version": cls.MODEL_VERSION,
            "features_used": [
                "real_usage", "predicted_usage", "usage_diff", "moving_avg_3m",
                "moving_avg_6m", "seasonality_coeff", "trend", "month_of_year",
                "regional_demand", "restock_time", "stock_days"
            ],
            "seasonality": {
                "coefficient": seasonality_coeff,
                "period": 12,  # Mensual
                "type": "multiplicative" if seasonality_coeff > 0.1 else "none"
            },
            "trend": {
                "direction": trend.value,
                "slope": float(np.polyfit(range(len(real_usages)), real_usages, 1)[0])
            },
            "stock_analysis": {
                "current_stock": latest.stock,
                "avg_consumption": avg_consumption,
                "stock_days": stock_days,
                "alert_level": alert_level.value
            }
        }
        
        # Crear y guardar la predicción
        db_prediction = Prediction(
            medication_id=medication_id,
            date=datetime.now(),
            real_usage=latest.real_usage,
            predicted_usage=latest.predicted_usage,
            stock=latest.stock,
            month_of_year=datetime.now().month,
            regional_demand=latest.regional_demand,
            restock_time=latest.restock_time or 0,
            shortage=bool(prediction),
            probability=float(probability),
            seasonality_coefficient=seasonality_coeff,
            trend=trend.value,
            alert_level=alert_level.value,
            alert_message=alert_message,
            confidence_interval_lower=lower_bound,
            confidence_interval_upper=upper_bound,
            metadata_=json.dumps(metadata)
        )
        
        db.add(db_prediction)
        db.commit()
        
        return {
            "medication_id": medication_id,
            "prediction": "Shortage" if prediction == 1 else "No shortage",
            "probability": float(probability),
            "alert_level": alert_level.value,
            "alert_message": alert_message,
            "stock_days": stock_days,
            "trend": trend.value,
            "seasonality_coefficient": seasonality_coeff,
            "confidence_interval": [lower_bound, upper_bound],
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }