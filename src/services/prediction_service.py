
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    mean_absolute_error, mean_squared_error, r2_score
)
from sqlmodel import Session, select, func, and_
import logging

from src.models.prediction import (
    Prediction, PredictionCreate, PredictionUpdate, PredictionInDB,
    PredictionMetrics, PredictionMetricsCreate
)
from src.models.medication import Medication
from src.models.movement import Movement, MovementType

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración del modelo
MODEL_CONFIG = {
    'n_estimators': 100,
    'random_state': 42,
    'n_jobs': -1,
    'min_samples_leaf': 3,
    'max_depth': 10
}

def get_historical_data(db: Session, medication_id: int, months_back: int = 12) -> pd.DataFrame:
    """Obtiene datos históricos de movimientos para un medicamento."""
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=30 * months_back)
    
    # Obtener movimientos históricos
    stmt = select(Movement).where(
        and_(
            Movement.medication_id == medication_id,
            Movement.date >= start_date,
            Movement.date <= end_date
        )
    )
    movements = db.exec(stmt).all()
    
    if not movements:
        return pd.DataFrame()
    
    # Convertir a DataFrame
    data = [{
        'date': m.date,
        'type': m.type,
        'quantity': m.quantity,
        'day_of_week': m.date.weekday(),
        'month': m.date.month,
        'day_of_month': m.date.day,
        'is_weekend': m.date.weekday() >= 5
    } for m in movements]
    
    return pd.DataFrame(data)

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
    """Prepara las características para el modelo."""
    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=float)
    
    # Agregar características de series de tiempo
    df = df.sort_values('date')
    
    # Crear características de tendencia
    df['quantity_ma7'] = df['quantity'].rolling(window=7).mean()
    df['quantity_ma30'] = df['quantity'].rolling(window=30).mean()
    
    # Características de estacionalidad
    df['month_sin'] = np.sin(2 * np.pi * df['month']/12.0)
    df['month_cos'] = np.cos(2 * np.pi * df['month']/12.0)
    
    # Características de día de la semana
    df = pd.get_dummies(df, columns=['day_of_week'], prefix='dow')
    
    # Eliminar filas con valores nulos
    df = df.dropna()
    
    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=float)
    
    # Definir características y objetivo
    feature_cols = [
        'quantity_ma7', 'quantity_ma30',
        'month_sin', 'month_cos',
        'is_weekend'
    ]
    
    # Añadir columnas de día de la semana
    feature_cols.extend([col for col in df.columns if col.startswith('dow_')])
    
    X = df[feature_cols]
    y = df['quantity']
    
    return X, y

def train_random_forest(X: pd.DataFrame, y: pd.Series) -> Tuple[RandomForestRegressor, dict]:
    """Entrena un modelo de Random Forest y devuelve el modelo y las métricas."""
    if X.empty or y.empty:
        raise ValueError("No hay suficientes datos para entrenar el modelo")
    
    # Dividir datos
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )
    
    # Entrenar modelo
    model = RandomForestRegressor(**MODEL_CONFIG)
    model.fit(X_train, y_train)
    
    # Evaluar modelo
    y_pred = model.predict(X_test)
    
    # Calcular métricas
    metrics = {
        'mae': mean_absolute_error(y_test, y_pred),
        'mse': mean_squared_error(y_test, y_pred),
        'r2': r2_score(y_test, y_pred),
        'feature_importances': dict(zip(X.columns, model.feature_importances_))
    }
    
    return model, metrics

def predict_shortage_risk(
    db: Session,
    medication_id: int,
    days_ahead: int = 30
) -> Dict[str, any]:
    """Predice el riesgo de desabastecimiento para un medicamento."""
    try:
        # Obtener datos históricos
        df = get_historical_data(db, medication_id)
        
        if df.empty:
            raise ValueError("No hay suficientes datos históricos")
        
        # Preparar características
        X, y = prepare_features(df)
        
        if X.empty or y.empty:
            raise ValueError("No se pudieron extraer características válidas")
        
        # Entrenar modelo
        model, metrics = train_random_forest(X, y)
        
        # Predecir para los próximos días
        future_dates = pd.date_range(
            start=datetime.utcnow(),
            periods=days_ahead,
            freq='D'
        )
        
        future_data = pd.DataFrame({
            'date': future_dates,
            'month': future_dates.month,
            'day_of_week': future_dates.weekday,
            'is_weekend': future_dates.weekday >= 5
        })
        
        # Preparar características para predicción
        X_future, _ = prepare_features(future_data)
        
        if X_future.empty:
            raise ValueError("No se pudieron preparar características para la predicción")
        
        # Hacer predicciones
        predictions = model.predict(X_future)
        
        # Calcular métricas de riesgo
        avg_prediction = np.mean(predictions)
        risk_level = calculate_risk_level(avg_prediction, metrics['mae'])
        
        # Obtener el medicamento para ver el stock actual
        medication = db.get(Medication, medication_id)
        if not medication:
            raise ValueError(f"Medicamento con ID {medication_id} no encontrado")
        
        # Calcular días hasta desabastecimiento
        days_until_shortage = calculate_days_until_shortage(
            current_stock=medication.stock,
            daily_consumption=avg_prediction,
            min_stock=medication.min_stock
        )
        
        # Crear respuesta
        result = {
            'medication_id': medication_id,
            'predicted_usage': float(avg_prediction),
            'current_stock': medication.stock,
            'min_stock': medication.min_stock,
            'days_until_shortage': days_until_shortage,
            'risk_level': risk_level,
            'confidence': 1 - (metrics['mae'] / avg_prediction if avg_prediction > 0 else 0.5),
            'metrics': metrics,
            'prediction_date': datetime.utcnow().isoformat(),
            'prediction_horizon_days': days_ahead
        }
        
        # Guardar predicción en la base de datos
        save_prediction(db, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Error en predict_shortage_risk: {str(e)}", exc_info=True)
        raise

def calculate_risk_level(daily_consumption: float, mae: float) -> str:
    """Calcula el nivel de riesgo basado en el consumo diario y el error del modelo."""
    if daily_consumption <= 0:
        return 'low'
    
    # Ajustar el consumo por el margen de error
    adjusted_consumption = daily_consumption + mae
    
    if adjusted_consumption < 5:
        return 'low'
    elif adjusted_consumption < 15:
        return 'medium'
    else:
        return 'high'

def calculate_days_until_shortage(
    current_stock: float,
    daily_consumption: float,
    min_stock: float = 0,
    buffer_days: int = 7
) -> Optional[int]:
    """Calcula los días hasta el desabastecimiento."""
    if daily_consumption <= 0:
        return None
    
    available_stock = max(0, current_stock - min_stock)
    if available_stock <= 0:
        return 0
    
    days = int(available_stock / daily_consumption) - buffer_days
    return max(0, days)

def save_prediction(db: Session, prediction_data: dict) -> Prediction:
    """Guarda una predicción en la base de datos."""
    try:
        # Crear métricas del modelo
        metrics = PredictionMetricsCreate(
            model_version='1.0.0',
            mae=prediction_data['metrics']['mae'],
            mse=prediction_data['metrics']['mse'],
            r2_score=prediction_data['metrics']['r2'],
            parameters=MODEL_CONFIG,
            features_used=list(prediction_data['metrics']['feature_importances'].keys())
        )
        
        db_metrics = PredictionMetrics.from_orm(metrics)
        db.add(db_metrics)
        db.commit()
        db.refresh(db_metrics)
        
        # Crear predicción
        prediction = PredictionCreate(
            medication_id=prediction_data['medication_id'],
            date=datetime.utcnow(),
            real_usage=0,  # Se actualizará cuando haya datos reales
            predicted_usage=prediction_data['predicted_usage'],
            stock=prediction_data['current_stock'],
            month_of_year=datetime.utcnow().month,
            regional_demand=0,  # Se puede obtener de datos externos
            shortage=prediction_data['days_until_shortage'] is not None and prediction_data['days_until_shortage'] <= 7,
            probability=prediction_data['confidence'],
            alert_level=prediction_data['risk_level'],
            trend='up' if prediction_data['predicted_usage'] > 0 else 'down',
            prediction_metrics_id=db_metrics.id
        )
        
        db_prediction = Prediction.from_orm(prediction)
        db.add(db_prediction)
        db.commit()
        db.refresh(db_prediction)
        
        return db_prediction
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error al guardar la predicción: {str(e)}", exc_info=True)
        raise

def get_predictions(
    db: Session,
    medication_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    limit: int = 100,
    offset: int = 0
) -> List[Prediction]:
    """Obtiene predicciones con filtros opcionales."""
    query = db.query(Prediction)
    
    if medication_id is not None:
        query = query.filter(Prediction.medication_id == medication_id)
        
    if start_date is not None:
        query = query.filter(Prediction.date >= start_date)
        
    if end_date is not None:
        query = query.filter(Prediction.date <= end_date)
    
    return query.order_by(Prediction.date.desc()).offset(offset).limit(limit).all()
