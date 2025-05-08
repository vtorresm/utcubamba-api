from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from typing import Optional, List, Dict
from src.db.database import get_db
from src.models.database_models import Medicamento as MedicamentoModel, Categoria as CategoriaModel, Movimiento as MovimientoModel
from src.models.schemas import ReporteInventario, ReporteInventarioItem, ReporteMovimientos, ReporteMovimientosItem, ReporteMovimientos
from src.api.dependencies import get_current_user, require_role
import logging
from datetime import date, datetime
import pandas as pd
import io
import csv

router = APIRouter()
logger = logging.getLogger(__name__)

# Reporte de Inventario
def generate_inventory_report_data(
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

    encabezado = {
        "titulo": "Reporte de Inventario",
        "fecha": str(date.today()),
        "filtros_aplicados": filtros_str
    }

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

    datos = []
    total_medicamentos = 0
    valor_total_inventario = 0.0

    for med in medicamentos:
        if med.stock_actual == 0:
            estado_med = "Agotado"
        elif med.stock_actual <= 10:
            estado_med = "Stock Bajo"
        else:
            estado_med = "En Stock"

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

    encabezado, datos, resumen = generate_inventory_report_data(
        categoria, estado, stock_min, stock_max, precio_min, precio_max,
        fecha_vencimiento_antes, fecha_vencimiento_despues, laboratorio, requiere_receta, db
    )

    if formato.lower() == "json":
        logger.info(f"Inventory report generated in JSON: {resumen['total_medicamentos']} medicamentos")
        return {
            "encabezado": encabezado,
            "datos": datos,
            "resumen": resumen
        }

    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "nombre_comercial", "nombre_generico", "categoria", "stock", "precio_unitario", "valor_total", "estado"]
        )

        output.write(f"# {encabezado['titulo']}\n")
        output.write(f"# Fecha: {encabezado['fecha']}\n")
        output.write(f"# Filtros Aplicados: {encabezado['filtros_aplicados']}\n")
        output.write("\n")

        writer.writeheader()
        for item in datos:
            writer.writerow(item)

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

    elif formato.lower() == "excel":
        output = io.BytesIO()
        df = pd.DataFrame(datos)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([[
                f"{encabezado['titulo']}",
                f"Fecha: {encabezado['fecha']}",
                f"Filtros Aplicados: {encabezado['filtros_aplicados']}"
            ]]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=0)

            df.to_excel(writer, sheet_name='Reporte', index=False, startrow=4)

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

        \begin{center}
            \textbf{\LARGE Reporte de Inventario} \\
            \vspace{0.5cm}
            \textbf{Fecha:} """ + str(encabezado["fecha"]) + r""" \\
            \textbf{Filtros Aplicados:} """ + (encabezado["filtros_aplicados"] if encabezado["filtros_aplicados"] != "Ninguno" else "Ninguno") + r"""
        \end{center}
        \vspace{1cm}

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

        \section*{Resumen}
        \begin{itemize}
            \item \textbf{Total Medicamentos:} """ + str(resumen["total_medicamentos"]) + r"""
            \item \textbf{Valor Total Inventario:} """ + f"{resumen['valor_total_inventario']:.2f}" + r"""
        \end{itemize}

        \end{document}
        """

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

# Reporte de Movimientos
def generate_movements_report_data(
    tipo_movimiento: Optional[str],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    medicamento: Optional[str],
    db: Session
):
    filtros_aplicados = []
    if tipo_movimiento:
        filtros_aplicados.append(f"Tipo de Movimiento: {tipo_movimiento}")
    if fecha_desde:
        filtros_aplicados.append(f"Fecha Desde: {fecha_desde}")
    if fecha_hasta:
        filtros_aplicados.append(f"Fecha Hasta: {fecha_hasta}")
    if medicamento:
        filtros_aplicados.append(f"Medicamento: {medicamento}")
    filtros_str = ", ".join(filtros_aplicados) if filtros_aplicados else "Ninguno"

    encabezado = {
        "titulo": "Reporte de Movimientos",
        "fecha": str(date.today()),
        "filtros_aplicados": filtros_str
    }

    query = db.query(MovimientoModel).join(MedicamentoModel)

    filters = []
    if tipo_movimiento:
        filters.append(MovimientoModel.tipo_movimiento == tipo_movimiento)
    if fecha_desde:
        filters.append(MovimientoModel.fecha >= fecha_desde)
    if fecha_hasta:
        filters.append(MovimientoModel.fecha <= fecha_hasta)
    if medicamento:
        filters.append(MedicamentoModel.nombre_comercial.ilike(f"%{medicamento}%"))

    if filters:
        query = query.filter(and_(*filters))

    movimientos = query.all()

    datos = []
    total_movimientos = 0

    for mov in movimientos:
        item = {
            "id": mov.movimiento_id,
            "fecha": mov.fecha,
            "tipo_movimiento": mov.tipo_movimiento.value,
            "medicamento": mov.medicamento.nombre_comercial,
            "cantidad": mov.cantidad,
            "observaciones": mov.observaciones if mov.observaciones else "-"
        }
        datos.append(item)
        total_movimientos += 1

    resumen = {
        "total_movimientos": total_movimientos
    }

    return encabezado, datos, resumen

@router.get("/movimientos")
def generate_movements_report(
    tipo_movimiento: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    medicamento: Optional[str] = None,
    formato: str = "json",
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Generating movements report by admin: {current_user.email} in format: {formato}")

    encabezado, datos, resumen = generate_movements_report_data(tipo_movimiento, fecha_desde, fecha_hasta, medicamento, db)

    if formato.lower() == "json":
        logger.info(f"Movements report generated in JSON: {resumen['total_movimientos']} movimientos")
        return {
            "encabezado": encabezado,
            "datos": datos,
            "resumen": resumen
        }

    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["id", "fecha", "tipo_movimiento", "medicamento", "cantidad", "observaciones"]
        )

        output.write(f"# {encabezado['titulo']}\n")
        output.write(f"# Fecha: {encabezado['fecha']}\n")
        output.write(f"# Filtros Aplicados: {encabezado['filtros_aplicados']}\n")
        output.write("\n")

        writer.writeheader()
        for item in datos:
            writer.writerow(item)

        output.write("\n")
        output.write(f"# Total Movimientos: {resumen['total_movimientos']}\n")

        headers = {
            "Content-Disposition": "attachment; filename=reporte_movimientos.csv",
            "Content-Type": "text/csv",
        }
        logger.info(f"Movements report generated in CSV: {resumen['total_movimientos']} movimientos")
        return StreamingResponse(
            iter([output.getvalue()]),
            headers=headers,
            media_type="text/csv"
        )

    elif formato.lower() == "excel":
        output = io.BytesIO()
        df = pd.DataFrame(datos)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([[
                f"{encabezado['titulo']}",
                f"Fecha: {encabezado['fecha']}",
                f"Filtros Aplicados: {encabezado['filtros_aplicados']}"
            ]]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=0)

            df.to_excel(writer, sheet_name='Reporte', index=False, startrow=4)

            pd.DataFrame([
                ["Total Movimientos", resumen['total_movimientos']]
            ]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=len(datos) + 6)

        headers = {
            "Content-Disposition": "attachment; filename=reporte_movimientos.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        output.seek(0)
        logger.info(f"Movements report generated in Excel: {resumen['total_movimientos']} movimientos")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

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

        \begin{center}
            \textbf{\LARGE Reporte de Movimientos} \\
            \vspace{0.5cm}
            \textbf{Fecha:} """ + str(encabezado["fecha"]) + r""" \\
            \textbf{Filtros Aplicados:} """ + (encabezado["filtros_aplicados"] if encabezado["filtros_aplicados"] != "Ninguno" else "Ninguno") + r"""
        \end{center}
        \vspace{1cm}

        \begin{landscape}
        \begin{longtable}{@{} l l l l r l @{}}
            \toprule
            \textbf{ID} & \textbf{Fecha} & \textbf{Tipo de Movimiento} & \textbf{Medicamento} & \textbf{Cantidad} & \textbf{Observaciones} \\
            \midrule
            \endhead
        """
        for item in datos:
            fecha_str = item["fecha"].strftime("%Y-%m-%d %H:%M:%S")
            observaciones = item["observaciones"] if item["observaciones"] != "-" else "-"
            latex_content += f"{item['id']} & {fecha_str} & {item['tipo_movimiento']} & {item['medicamento']} & {item['cantidad']} & {observaciones} \\\\\n"

        latex_content += r"""
            \bottomrule
        \end{longtable}
        \end{landscape}

        \section*{Resumen}
        \begin{itemize}
            \item \textbf{Total Movimientos:} """ + str(resumen["total_movimientos"]) + r"""
        \end{itemize}

        \end{document}
        """

        output = io.BytesIO(latex_content.encode('utf-8'))
        headers = {
            "Content-Disposition": "attachment; filename=reporte_movimientos.pdf",
            "Content-Type": "application/pdf",
        }
        logger.info(f"Movements report generated in PDF: {resumen['total_movimientos']} movimientos")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/pdf"
        )

    else:
        logger.error(f"Invalid format requested: {formato}")
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json', 'csv', 'excel', or 'pdf'.")

# Reporte de Tendencias (nuevo)
def generate_trends_report_data(
    mes: Optional[str],
    medicamento: Optional[str],
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    db: Session
):
    filtros_aplicados = []
    month_map = {
        "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
        "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
    }
    if mes:
        filtros_aplicados.append(f"Mes: {mes}")
    if medicamento:
        filtros_aplicados.append(f"Medicamento: {medicamento}")
    if fecha_desde:
        filtros_aplicados.append(f"Fecha Desde: {fecha_desde}")
    if fecha_hasta:
        filtros_aplicados.append(f"Fecha Hasta: {fecha_hasta}")
    filtros_str = ", ".join(filtros_aplicados) if filtros_aplicados else "Ninguno"

    encabezado = {
        "titulo": "Reporte de Tendencias",
        "fecha": str(date.today()),
        "filtros_aplicados": filtros_str
    }

    # Consulta para calcular demanda (salidas agrupadas por mes y medicamento)
    query = (
        db.query(
            func.extract('month', MovimientoModel.fecha).label('month'),
            MedicamentoModel.nombre_comercial,
            func.sum(MovimientoModel.cantidad).label('demanda')
        )
        .join(MedicamentoModel)
        .filter(MovimientoModel.tipo_movimiento == "Salida")
        .group_by(func.extract('month', MovimientoModel.fecha), MedicamentoModel.nombre_comercial)
    )

    filters = []
    if mes:
        month_num = month_map.get(mes)
        if month_num:
            filters.append(func.extract('month', MovimientoModel.fecha) == month_num)
    if medicamento:
        filters.append(MedicamentoModel.nombre_comercial.ilike(f"%{medicamento}%"))
    if fecha_desde:
        filters.append(MovimientoModel.fecha >= fecha_desde)
    if fecha_hasta:
        filters.append(MovimientoModel.fecha <= fecha_hasta)

    if filters:
        query = query.filter(and_(*filters))

    results = query.all()

    datos = []
    total_demanda = 0

    for result in results:
        mes_nombre = list(month_map.keys())[int(result.month) - 1]
        item = {
            "mes": mes_nombre,
            "medicamento": result.nombre_comercial,
            "demanda": int(result.demanda)
        }
        datos.append(item)
        total_demanda += int(result.demanda)

    resumen = {
        "total_demanda": total_demanda
    }

    return encabezado, datos, resumen

@router.get("/tendencias")
def generate_trends_report(
    mes: Optional[str] = None,
    medicamento: Optional[str] = None,
    fecha_desde: Optional[date] = None,
    fecha_hasta: Optional[date] = None,
    formato: str = "json",
    current_user: MedicamentoModel = Depends(require_role("admin")),
    db: Session = Depends(get_db)
):
    logger.info(f"Generating trends report by admin: {current_user.email} in format: {formato}")

    encabezado, datos, resumen = generate_trends_report_data(mes, medicamento, fecha_desde, fecha_hasta, db)

    if formato.lower() == "json":
        logger.info(f"Trends report generated in JSON: {resumen['total_demanda']} total demanda")
        return {
            "encabezado": encabezado,
            "datos": datos,
            "resumen": resumen
        }

    elif formato.lower() == "csv":
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=["mes", "medicamento", "demanda"]
        )

        output.write(f"# {encabezado['titulo']}\n")
        output.write(f"# Fecha: {encabezado['fecha']}\n")
        output.write(f"# Filtros Aplicados: {encabezado['filtros_aplicados']}\n")
        output.write("\n")

        writer.writeheader()
        for item in datos:
            writer.writerow(item)

        output.write("\n")
        output.write(f"# Total Demanda: {resumen['total_demanda']}\n")

        headers = {
            "Content-Disposition": "attachment; filename=reporte_tendencias.csv",
            "Content-Type": "text/csv",
        }
        logger.info(f"Trends report generated in CSV: {resumen['total_demanda']} total demanda")
        return StreamingResponse(
            iter([output.getvalue()]),
            headers=headers,
            media_type="text/csv"
        )

    elif formato.lower() == "excel":
        output = io.BytesIO()
        df = pd.DataFrame(datos)

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            pd.DataFrame([[
                f"{encabezado['titulo']}",
                f"Fecha: {encabezado['fecha']}",
                f"Filtros Aplicados: {encabezado['filtros_aplicados']}"
            ]]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=0)

            df.to_excel(writer, sheet_name='Reporte', index=False, startrow=4)

            pd.DataFrame([
                ["Total Demanda", resumen['total_demanda']]
            ]).to_excel(writer, sheet_name='Reporte', index=False, header=False, startrow=len(datos) + 6)

        headers = {
            "Content-Disposition": "attachment; filename=reporte_tendencias.xlsx",
            "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }
        output.seek(0)
        logger.info(f"Trends report generated in Excel: {resumen['total_demanda']} total demanda")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

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

        \begin{center}
            \textbf{\LARGE Reporte de Tendencias} \\
            \vspace{0.5cm}
            \textbf{Fecha:} """ + str(encabezado["fecha"]) + r""" \\
            \textbf{Filtros Aplicados:} """ + (encabezado["filtros_aplicados"] if encabezado["filtros_aplicados"] != "Ninguno" else "Ninguno") + r"""
        \end{center}
        \vspace{1cm}

        \begin{landscape}
        \begin{longtable}{@{} l l r @{}}
            \toprule
            \textbf{Mes} & \textbf{Medicamento} & \textbf{Demanda} \\
            \midrule
            \endhead
        """
        for item in datos:
            latex_content += f"{item['mes']} & {item['medicamento']} & {item['demanda']} \\\\\n"

        latex_content += r"""
            \bottomrule
        \end{longtable}
        \end{landscape}

        \section*{Resumen}
        \begin{itemize}
            \item \textbf{Total Demanda:} """ + str(resumen["total_demanda"]) + r"""
        \end{itemize}

        \end{document}
        """

        output = io.BytesIO(latex_content.encode('utf-8'))
        headers = {
            "Content-Disposition": "attachment; filename=reporte_tendencias.pdf",
            "Content-Type": "application/pdf",
        }
        logger.info(f"Trends report generated in PDF: {resumen['total_demanda']} total demanda")
        return StreamingResponse(
            output,
            headers=headers,
            media_type="application/pdf"
        )

    else:
        logger.error(f"Invalid format requested: {formato}")
        raise HTTPException(status_code=400, detail="Invalid format. Use 'json', 'csv', 'excel', or 'pdf'.")