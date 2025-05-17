from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from src.core.database import Base

class Prediction(Base):
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, index=True)
    medicamento_id = Column(Integer, ForeignKey("medicamentos.id"))
    fecha = Column(DateTime, nullable=False)
    real_usage = Column(Float, nullable=False)  # Uso real (R_i)
    predicted_usage = Column(Float, nullable=False)  # Uso previsto (P_i)
    stock = Column(Float, nullable=False)  # Stock disponible
    month_of_year = Column(Integer, nullable=False)  # Mes del año (1-12)
    regional_demand = Column(Float, nullable=False)  # Demanda regional
    restock_time = Column(Float, nullable=True)  # Tiempo de reabastecimiento (días)
    desabastecimiento = Column(Boolean, nullable=False)  # 1 si hubo desabastecimiento, 0 si no
    movimiento_id = Column(Integer, ForeignKey("movimientos.id"))
    movimiento = relationship("Movimiento", back_populates="predictions")
    probability = Column(Float, nullable=True)  # Probabilidad de desabastecimiento (para predicciones)