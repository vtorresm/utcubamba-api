"""
Patrón Factory — ForecastModelFactory.

Centraliza la creación de funciones de forecasting, desacoplando
el endpoint de los detalles de implementación de cada modelo.
En lugar de un diccionario suelto, la factory es una clase con un
classmethod `create()` que valida y devuelve la función correcta.

Uso
---
    fn = ForecastModelFactory.create("arima")
    result = fn(db, medication_id, horizon_days, months_back)
"""

from __future__ import annotations

from typing import Callable

from sqlmodel import Session


# Tipo de las funciones de forecasting
ForecastFn = Callable[..., dict]


class ForecastModelFactory:
    """
    Fábrica de modelos de forecasting.

    Implementa el patrón Factory como clase con classmethod estático,
    lo que permite extender fácilmente el catálogo de modelos sin
    modificar los endpoints que los consumen.

    Modelos disponibles
    -------------------
    - ``"arima"``    : Auto-ARIMA con selección por AIC (pmdarima)
    - ``"prophet"``  : Facebook Prophet con estacionalidad semanal/anual
    - ``"ensemble"`` : Promedio ponderado por 1/RMSE de ARIMA + Prophet

    Raises
    ------
    ValueError
        Si se solicita un modelo no registrado.
    """

    # Registro de modelos (se puebla al final para evitar importación circular)
    _registry: dict[str, ForecastFn] = {}

    @classmethod
    def create(cls, model_type: str) -> ForecastFn:
        """
        Devuelve la función de forecasting correspondiente al modelo solicitado.

        Parameters
        ----------
        model_type : str
            Identificador del modelo: ``"arima"``, ``"prophet"`` o ``"ensemble"``.

        Returns
        -------
        ForecastFn
            Función con firma ``(db, medication_id, horizon_days, months_back) -> dict``.

        Raises
        ------
        ValueError
            Si ``model_type`` no está en el registro.
        """
        # Inicialización diferida para evitar importaciones circulares
        if not cls._registry:
            cls._init_registry()

        fn = cls._registry.get(model_type)
        if fn is None:
            available = list(cls._registry.keys())
            raise ValueError(
                f"Modelo '{model_type}' no registrado. "
                f"Opciones disponibles: {available}"
            )
        return fn

    @classmethod
    def available_models(cls) -> list[str]:
        """Devuelve la lista de modelos registrados."""
        if not cls._registry:
            cls._init_registry()
        return list(cls._registry.keys())

    @classmethod
    def _init_registry(cls) -> None:
        """Registra los modelos disponibles (importación diferida)."""
        from src.services.forecast_service import (
            run_arima_forecast,
            run_prophet_forecast,
            run_ensemble_forecast,
        )
        cls._registry = {
            "arima":    run_arima_forecast,
            "prophet":  run_prophet_forecast,
            "ensemble": run_ensemble_forecast,
        }

    @classmethod
    def register(cls, name: str, fn: ForecastFn) -> None:
        """
        Registra un modelo personalizado en tiempo de ejecución.

        Útil para añadir modelos experimentales sin modificar la factory.

        Parameters
        ----------
        name : str
            Identificador único del modelo.
        fn : ForecastFn
            Función de forecasting con la firma estándar.
        """
        cls._registry[name] = fn
