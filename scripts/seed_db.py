from sqlalchemy.orm import Session
from src.core.database import SessionLocal, Base, engine
from src.models import Categoria, Condicion, TipoDeToma, Medicamento, Movimiento, Prediction
from datetime import datetime, timedelta
import random

def seed_db():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # Semillas para tablas de referencia
    categorias = [
        Categoria(nombre="Analgésicos"),
        Categoria(nombre="Antibióticos"),
        Categoria(nombre="Antipiréticos"),
        Categoria(nombre="Antihistamínicos"),
        Categoria(nombre="Antiinflamatorios"),
        Categoria(nombre="Vitaminas"),
        Categoria(nombre="Antidepresivos"),
        Categoria(nombre="Antihipertensivos"),
        Categoria(nombre="Antidiabéticos"),
        Categoria(nombre="Broncodilatadores")
    ]
    db.add_all(categorias)
    db.commit()

    condiciones = [
        Condicion(nombre="Dolor"),
        Condicion(nombre="Infección"),
        Condicion(nombre="Fiebre"),
        Condicion(nombre="Alergia"),
        Condicion(nombre="Inflamación"),
        Condicion(nombre="Fatiga"),
        Condicion(nombre="Ansiedad"),
        Condicion(nombre="Depresión"),
        Condicion(nombre="Hipertensión"),
        Condicion(nombre="Diabetes"),
        Condicion(nombre="Asma"),
        Condicion(nombre="Migraña"),
        Condicion(nombre="Artritis"),
        Condicion(nombre="Insomnio"),
        Condicion(nombre="Gastritis")
    ]
    db.add_all(condiciones)
    db.commit()

    tipos_de_toma = [
        TipoDeToma(nombre="Oral"),
        TipoDeToma(nombre="Intravenoso"),
        TipoDeToma(nombre="Tópico"),
        TipoDeToma(nombre="Inhalado"),
        TipoDeToma(nombre="Sublingual"),
        TipoDeToma(nombre="Intramuscular"),
        TipoDeToma(nombre="Oftálmico"),
        TipoDeToma(nombre="Rectal")
    ]
    db.add_all(tipos_de_toma)
    db.commit()

    # Crear 75 medicamentos
    medicamentos = [
        # Analgésicos (10)
        Medicamento(nombre="Paracetamol 500mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0], condiciones[2]]),
        Medicamento(nombre="Ibuprofeno 400mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Aspirina 100mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Tramadol 50mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Ketorolaco 10mg", categoria_id=1, tipo_toma_id=2, condiciones=[condiciones[0]]),
        Medicamento(nombre="Diclofenaco 50mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Naproxeno 250mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Codeína 30mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        Medicamento(nombre="Morfina 10mg", categoria_id=1, tipo_toma_id=2, condiciones=[condiciones[0]]),
        Medicamento(nombre="Celecoxib 200mg", categoria_id=1, tipo_toma_id=1, condiciones=[condiciones[0]]),
        # Antibióticos (10)
        Medicamento(nombre="Amoxicilina 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Azitromicina 250mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Ciprofloxacino 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Levofloxacino 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Clindamicina 300mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Doxiciclina 100mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Eritromicina 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Cefalexina 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Metronidazol 500mg", categoria_id=2, tipo_toma_id=1, condiciones=[condiciones[1]]),
        Medicamento(nombre="Vancomicina 1g", categoria_id=2, tipo_toma_id=2, condiciones=[condiciones[1]]),
        # Antipiréticos (10)
        Medicamento(nombre="Paracetamol 1g", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Acetaminofén 650mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Ibuprofeno 200mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Aspirina 500mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Dipirona 500mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Nimesulida 100mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Paracetamol IV 1g", categoria_id=3, tipo_toma_id=2, condiciones=[condiciones[2]]),
        Medicamento(nombre="Ketoprofeno 100mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Piroxicam 20mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        Medicamento(nombre="Meloxicam 15mg", categoria_id=3, tipo_toma_id=1, condiciones=[condiciones[2]]),
        # Antihistamínicos (10)
        Medicamento(nombre="Loratadina 10mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Cetirizina 10mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Desloratadina 5mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Fexofenadina 120mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Clorfenamina 4mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Levocetirizina 5mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Hidroxizina 25mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Ebastina 10mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Rupatadina 10mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        Medicamento(nombre="Bilastina 20mg", categoria_id=4, tipo_toma_id=1, condiciones=[condiciones[3]]),
        # Antiinflamatorios (5)
        Medicamento(nombre="Diclofenaco 75mg", categoria_id=5, tipo_toma_id=1, condiciones=[condiciones[4], condiciones[12]]),
        Medicamento(nombre="Naproxeno 500mg", categoria_id=5, tipo_toma_id=1, condiciones=[condiciones[4]]),
        Medicamento(nombre="Ketoprofeno 150mg", categoria_id=5, tipo_toma_id=1, condiciones=[condiciones[4]]),
        Medicamento(nombre="Piroxicam 20mg", categoria_id=5, tipo_toma_id=1, condiciones=[condiciones[4]]),
        Medicamento(nombre="Meloxicam 7.5mg", categoria_id=5, tipo_toma_id=1, condiciones=[condiciones[4], condiciones[12]]),
        # Vitaminas (5)
        Medicamento(nombre="Vitamina C 500mg", categoria_id=6, tipo_toma_id=1, condiciones=[condiciones[5]]),
        Medicamento(nombre="Vitamina D 1000UI", categoria_id=6, tipo_toma_id=1, condiciones=[condiciones[5]]),
        Medicamento(nombre="Complejo B", categoria_id=6, tipo_toma_id=1, condiciones=[condiciones[5]]),
        Medicamento(nombre="Vitamina E 400UI", categoria_id=6, tipo_toma_id=1, condiciones=[condiciones[5]]),
        Medicamento(nombre="Multivitamínico", categoria_id=6, tipo_toma_id=1, condiciones=[condiciones[5]]),
        # Antidepresivos (5)
        Medicamento(nombre="Sertralina 50mg", categoria_id=7, tipo_toma_id=1, condiciones=[condiciones[7], condiciones[6]]),
        Medicamento(nombre="Fluoxetina 20mg", categoria_id=7, tipo_toma_id=1, condiciones=[condiciones[7]]),
        Medicamento(nombre="Escitalopram 10mg", categoria_id=7, tipo_toma_id=1, condiciones=[condiciones[7], condiciones[6]]),
        Medicamento(nombre="Venlafaxina 75mg", categoria_id=7, tipo_toma_id=1, condiciones=[condiciones[7]]),
        Medicamento(nombre="Amitriptilina 25mg", categoria_id=7, tipo_toma_id=1, condiciones=[condiciones[7], condiciones[13]]),
        # Antihipertensivos (5)
        Medicamento(nombre="Losartán 50mg", categoria_id=8, tipo_toma_id=1, condiciones=[condiciones[8]]),
        Medicamento(nombre="Amlodipino 5mg", categoria_id=8, tipo_toma_id=1, condiciones=[condiciones[8]]),
        Medicamento(nombre="Enalapril 10mg", categoria_id=8, tipo_toma_id=1, condiciones=[condiciones[8]]),
        Medicamento(nombre="Bisoprolol 5mg", categoria_id=8, tipo_toma_id=1, condiciones=[condiciones[8]]),
        Medicamento(nombre="Hidroclorotiazida 25mg", categoria_id=8, tipo_toma_id=1, condiciones=[condiciones[8]]),
        # Antidiabéticos (5)
        Medicamento(nombre="Metformina 500mg", categoria_id=9, tipo_toma_id=1, condiciones=[condiciones[9]]),
        Medicamento(nombre="Glimepirida 2mg", categoria_id=9, tipo_toma_id=1, condiciones=[condiciones[9]]),
        Medicamento(nombre="Insulina Glargina 100UI", categoria_id=9, tipo_toma_id=6, condiciones=[condiciones[9]]),
        Medicamento(nombre="Sitagliptina 100mg", categoria_id=9, tipo_toma_id=1, condiciones=[condiciones[9]]),
        Medicamento(nombre="Dapagliflozina 10mg", categoria_id=9, tipo_toma_id=1, condiciones=[condiciones[9]]),
        # Broncodilatadores (5)
        Medicamento(nombre="Salbutamol Inhalador", categoria_id=10, tipo_toma_id=4, condiciones=[condiciones[10]]),
        Medicamento(nombre="Budesonida Inhalador", categoria_id=10, tipo_toma_id=4, condiciones=[condiciones[10]]),
        Medicamento(nombre="Ipratropio Bromuro", categoria_id=10, tipo_toma_id=4, condiciones=[condiciones[10]]),
        Medicamento(nombre="Formoterol Inhalador", categoria_id=10, tipo_toma_id=4, condiciones=[condiciones[10]]),
        Medicamento(nombre="Tiotropio Inhalador", categoria_id=10, tipo_toma_id=4, condiciones=[condiciones[10]])
    ]
    db.add_all(medicamentos)
    db.commit()

    # Generar 36 meses de datos (enero 2022 a diciembre 2024)
    start_date = datetime(2022, 1, 1)
    for medicamento in medicamentos:
        stock = 100.0  # Stock inicial
        categoria_id = medicamento.categoria_id

        for i in range(36):
            date = start_date + timedelta(days=30 * i)
            month_of_year = date.month

            # Definir patrones estacionales según la categoría
            if categoria_id == 1:  # Analgésicos: pico en invierno
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
            elif categoria_id == 2:  # Antibióticos: pico en otoño
                seasonal_factor = 1.0 + 0.3 if month_of_year in [9, 10, 11] else 1.0
            elif categoria_id == 3:  # Antipiréticos: pico en invierno
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
            elif categoria_id == 4:  # Antihistamínicos: pico en primavera
                seasonal_factor = 1.0 + 0.5 if month_of_year in [3, 4, 5] else 1.0
            elif categoria_id == 5:  # Antiinflamatorios: pico en verano
                seasonal_factor = 1.0 + 0.2 if month_of_year in [6, 7, 8] else 1.0
            elif categoria_id == 6:  # Vitaminas: pico ligero en invierno
                seasonal_factor = 1.0 + 0.1 if month_of_year in [1, 2, 12] else 1.0
            elif categoria_id == 7:  # Antidepresivos: pico en invierno
                seasonal_factor = 1.0 + 0.3 if month_of_year in [1, 2, 12] else 1.0
            elif categoria_id == 8:  # Antihipertensivos: pico ligero en fin de año
                seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
            elif categoria_id == 9:  # Antidiabéticos: pico ligero en fin de año
                seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
            elif categoria_id == 10:  # Broncodilatadores: pico en invierno y primavera
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 3, 4, 12] else 1.0

            # Simular uso real y previsto
            base_usage = random.uniform(50, 100)  # Uso base
            real_usage = base_usage * seasonal_factor
            predicted_usage = real_usage * random.uniform(0.9, 1.1)  # Variación del 10%
            stock -= real_usage
            if stock < 0:
                stock = 0
            desabastecimiento = 1 if stock == 0 else 0
            regional_demand = random.uniform(300, 700) * seasonal_factor
            restock_time = random.uniform(5, 15) if desabastecimiento else None

            # Crear movimiento asociado
            movimiento = Movimiento(
                medicamento_id=medicamento.id,
                fecha=date,
                tipo="salida" if real_usage > 0 else "entrada",
                cantidad=real_usage if real_usage > 0 else -stock
            )
            db.add(movimiento)

            # Crear predicción
            prediction = Prediction(
                medicamento_id=medicamento.id,
                fecha=date,
                real_usage=real_usage,
                predicted_usage=predicted_usage,
                stock=stock,
                month_of_year=month_of_year,
                regional_demand=regional_demand,
                restock_time=restock_time,
                desabastecimiento=desabastecimiento,
                movimiento_id=movimiento.id
            )
            db.add(prediction)

            # Simular reabastecimiento cada 4 meses
            if i % 4 == 0 and i > 0:
                restock_amount = random.uniform(100, 200)
                stock += restock_amount
                movimiento_restock = Movimiento(
                    medicamento_id=medicamento.id,
                    fecha=date,
                    tipo="entrada",
                    cantidad=restock_amount
                )
                db.add(movimiento_restock)

    db.commit()
    db.close()

if __name__ == "__main__":
    seed_db()
    print("Base de datos poblada con éxito.")