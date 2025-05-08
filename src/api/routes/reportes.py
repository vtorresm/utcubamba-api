from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import Optional, List, Dict
from src.db.database import get_db
from src.models.database_models import Medicamento as MedicamentoModel, Categoria as CategoriaModel
from src.api.dependencies import get_current_user, require_role
import logging
from datetime import date
import pandas as pd
import io
import csv

router = APIRouter()
logger = logging.getLogger(__name__)

class ReporteInventarioItem(BaseModel):
    id: int
    nombre_comercial: str
    nombre_generico: Optional[str]
    categoria: str
    stock: int
    precio_unitario: float
    valor_total: float
    estado: str

class ReporteInventario(BaseModel):
    encabezado: Dict[str, str]
    datos: List[ReporteInventarioItem]
    resumen: Dict[str, float]

def generate_report_data(
    categoria: Optional[str],
    estado: Optional[str],
    stock_min: Optional[int],
    stock_max: Optional[int],
    precio_min: Optional[float],
    precio_max: Optional[float],
    fecha_vencimiento_antes: Optional[date],
    fecha_vencimiento_despues: Optional[date],
    laboratorio: Optional[str],
    requiere_receta: Optional[bool],
    db: Session
):
    # Construir filtros aplicados para el encabezado
    filtros_aplicados = []
    if categoria:
        filtros_aplicados.append(f"Categoría: {categoria}")
    if estado:
        filtros_aplicados.append(f"Estado: {estado}")
    if stock_min is not None:
        filtros_aplicados.append(f"Stock Mínimo: {stock_min}")
    if stock_max is not None:
        filtros_aplicados.append(f"Stock Máximo: {stock_max}")
    if precio_min is not None:
        filtros_aplicados.append(f"Precio Mínimo: {precio_min}")
    if precio_max is not None:
        filtros_aplicados.append(f"Precio Máximo: {precio_max}")
    if fecha_vencimiento_antes:
        filtros_aplicados.append(f"Fecha Vencimiento Antes: {fecha_vencimiento_antes}")
    if fecha_vencimiento_despues:
        filtros_aplicados.append(f"Fecha Vencimiento Después: {fecha_vencimiento_despues}")
    if laboratorio:
        filtros_aplicados.append(f"Laboratorio: {laboratorio}")
    if requiere_receta is not None:
        filtros_aplicados.append(f"Requiere Receta: {requiere_receta}")
    filtros_str = ", ".join(filtros_aplicados) if filtros_aplicados else "Ninguno"

    # Encabezado del reporte
    encabezado = {
        "titulo": "Reporte de Inventario",
        "fecha": str(date.today()),
        "filtros_aplicados": filtros_str
    }

    # Consultar medicamentos con filtros
    query = db.query(MedicamentoModel).join(CategoriaModel)

    filters = []
    if categoria:
        filters.append(CategoriaModel.nombre.ilike(f"%{categoria}%"))
    if stock_min is not None:
        filters.append(MedicamentoModel.stock_actual >= stock_min)
    if stock_max is not None:
        filters.append(MedicamentoModel.stock_actual <= stock_max)
    if precio_min is not None:
        filters.append(MedicamentoModel.precio_unitario >= precio_min)
    if precio_max is not None:
        filters.append(MedicamentoModel.precio_unitario <= precio_max)
    if fecha_vencimiento_antes:
        filters.append(MedicamentoModel.fecha_vencimiento <= fecha_vencimiento_antes)
    if fecha_vencimiento_despues:
        filters.append(MedicamentoModel.fecha_vencimiento >= fecha_vencimiento_despues)
    if laboratorio:
        filters.append(MedicamentoModel.laboratorio.ilike(f"%{laboratorio}%"))
    if requiere_receta is not None:
        filters.append(MedicamentoModel.requiere_receta == requiere_receta)

    if filters:
        query = query.filter(and_(*filters))

    medicamentos = query.all()

    # Procesar datos para la tabla
    datos = []
    total_medicamentos = 0
    valor_total_inventario = 0.0

    for med in medicamentos:
        # Determinar estado dinámicamente
        if med.stock_actual == 0:
            estado_med = "Agotado"
        elif med.stock_actual <= 10:
            estado_med = "Stock Bajo"
        else:
            estado_med = "En Stock"

        # Aplicar filtro de estado si se especificó
        if estado and estado_med != estado:
            continue

        valor_total = med.stock_actual * med.precio_unitario
        item = {
            "id": med.medicamento_id,
            "nombre_comercial": med.nombre_comercial,
            "nombre_generico": med.nombre_generico,
            "categoria": med.categoria.nombre,
            "stock": med.stock_actual,
            "precio_unitario": float(med.precio_unitario),
            "valor_total": float(valor_total),
            "estado": estado_med
        }
        datos.append(item)

        total_medicamentos += 1
        valor_total_inventario += valor_total

    # Resumen
    resumen = {
        "total_medicamentos": total_medicamentos,
        "valor_total_inventario": float(valor_total_inventario)
    }

    return encabezado, datos, resumen

@router.get("/inventario")
def generate_inventory_report(
    categoria: Optional[str] = None,
    estado: Optional[str] = None,
    stock_min: Optional[int] = None,
    stock_max: Optional[int] = None,
    precio_min: Optional[float] = None,
    precio_max: Optional[float] = None,
    fecha_vencimiento_antes: Optional[date] = None,
    fecha_vencimiento_despues: Optional[date] = None,
    laboratorio: Optional[str] = None,
    requiere_receta: Optional[bool] = None,
    formato: str = "json",
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Generating inventory report by admin: {current_user.email} in format: {formato}")

    # Generar datos del reporte
    encabezado, datos, resumen = generate_report_data(
        categoria, estado, stock_min, stock_max, precio_min, precio_max,
        fecha_vencimiento_antes, fecha_vencimiento_despues, laboratorio, requiere_receta, db
    )

    # Formato JSON
    if formato.lower() == "json":
        logger.info(f"Inventory report generated in JSON: {resumen['total_medicamentos']} medicamentos, total value: {resumen['valor_total_inventario']}")
        return {
            "encabezado": encabezado,
            "datos": datos,
            "resumen": resumen
        }

    # Formato CSV
    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "nombre_comercial", "nombre_generico", "categoria", "stock", "precio_unitario", "valor_total", "estado"]
        )

        # Escribir encabezado como comentarios
        output.write(f"# {encabezado['titulo']}\n")
        output.write(f"# Fecha: {encabezado['fecha']}\n")
        output.write(f"# Filtros Aplicados: {encabezado['filtros_aplicados']}\n")
        output.write("\n")

        # Escribir tabla
        writer.writeheader()
        for item in datos:
            writer.writerow(item)

        # Escribir resumen como comentarios
        output.write("\n")
        output.write(f"# Total Medicamentos: {resumen['total_medicamentos']}\n")
        output.write(f"# Valor Total Inventario: {resumen['valor_total_inventario']}\n")

        headers = {
            "Content-Disposition": "attachment; filename=reporte_inventario.csv",
            "Content-Type": "text/csv",
        }
        logger.info(f"Inventory report generated in CSV: {resumen['total_medicamentos']} medicamentos")
        return StreamingResponse(
            iter([output.getvalue()]),
            headers=headers,
            media_type="text/csv"
        )

    # Formato Excel
    elif formato.lower() == "excel":
        output = io.BytesIO()
        df = pd.DataFrame(datos)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Escribir encabezado
            pd.DataFrame([[
                f"{encabezado['titulo']}",
                f"Fecha: {encabezado['fecha']}",
                f"Filtros Aplicados: {encabezado['filtros_aplicados']}"
            ]]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=0)

            # Escribir tabla
            df.to_excel(writer, sheet_name='Reporte', index=False, startrow=4)

            # Escribir resumen
            pd.DataFrame([
                ["Total Medicamentos", resumen['total_medicamentos']],
                ["Valor Total Inventario", resumen['valor_total_inventario']]
            ]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=len(datos) + 6)

        headers = {
            "Content-Disposition": "attachment; filename=reporte_inventario.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        output.seek(0)
        logger.info(f"Inventory report generated in Excel: {resumen['total_medicamentos']} medicamentos")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    # Formato PDF (usando LaTeX)
    elif formato.lower() == "pdf":
        latex_content = r"""
        \documentclass[a4paper,12pt]{article}
        \usepackage[utf8]{inputenc}
        \usepackage{geometry}
        \geometry{margin=1in}
        \usepackage{booktabs}
        \usepackage{longtable}
        \usepackage{pdflscape}
        \usepackage{enumitem}
        \setlist[itemize]{leftmargin=*}
        \usepackage{times}
        \begin{document}

        % Encabezado
        \begin{center}
            \textbf{\LARGE Reporte de Inventario} \\
            \vspace{0.5cm}
            \textbf{Fecha:} """ + str(encabezado["fecha"]) + r""" \\
            \textbf{Filtros Aplicados:} """ + (encabezado["filtros_aplicados"] if encabezado["filtros_aplicados"] != "Ninguno" else "Ninguno") + r"""
        \end{center}
        \vspace{1cm}

        % Tabla
        \begin{landscape}
        \begin{longtable}{@{} l l l l r r r l @{}}
            \toprule
            \textbf{ID} & \textbf{Nombre Comercial} & \textbf{Nombre Genérico} & \textbf{Categoría} & \textbf{Stock} & \textbf{Precio Unitario} & \textbf{Valor Total} & \textbf{Estado} \\
            \midrule
            \endhead
        """
        for item in datos:
            nombre_generico = item["nombre_generico"] if item["nombre_generico"] else "-"
            latex_content += f"{item['id']} & {item['nombre_comercial']} & {nombre_generico} & {item['categoria']} & {item['stock']} & {item['precio_unitario']} & {item['valor_total']} & {item['estado']} \\\\\n"

        latex_content += r"""
            \bottomrule
        \end{longtable}
        \end{landscape}

        % Resumen
        \section*{Resumen}
        \begin{itemize}
            \item \textbf{Total Medicamentos:} """ + str(resumen["total_medicamentos"]) + r"""
            \item \textbf{Valor Total Inventario:} """ + f"{resumen['valor_total_inventario']:.2f}" + r"""
        \end{itemize}

        \end{document}
        """

        # Generar el archivo LaTeX temporal
        output = io.BytesIO(latex_content.encode('utf-8'))
        headers = {
            "Content-Disposition": "attachment; filename=reporte_inventario.pdf",
            "Content-Type": "application/pdf",
        }
        logger.info(f"Inventory report generated in PDF: {resumen['total_medicamentos']} medicamentos")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/pdf"
        )

    else:
        logger.error(f"Invalid format requested: {formato}")
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json', 'csv', 'excel', or 'pdf'.")