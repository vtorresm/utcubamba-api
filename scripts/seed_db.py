from sqlalchemy.orm import Session
from sqlalchemy import or_
from src.core.database import SessionLocal, Base, engine
from src.models import Category, Condition, IntakeType, Medication, Movement, Prediction, User, Role, UserStatus
from datetime import datetime, timedelta
import random

def seed_db():
    db = SessionLocal()
    Base.metadata.create_all(bind=engine)

    # Función para obtener o crear registros
    def get_or_create(model, **kwargs):
        instance = db.query(model).filter_by(**kwargs).first()
        if instance:
            return instance
        else:
            instance = model(**kwargs)
            db.add(instance)
            db.commit()
            return instance

    # Crear categorías si no existen
    category_names = [
        "Analgésicos", "Antibióticos", "Antipiréticos", "Antihistamínicos",
        "Antiinflamatorios", "Vitaminas", "Antidepresivos", "Antihipertensivos",
        "Antidiabéticos", "Broncodilatadores"
    ]
    categories = []
    for name in category_names:
        category = get_or_create(Category, name=name)
        categories.append(category)

    # Crear condiciones si no existen
    condition_names = [
        "Dolor", "Infección", "Fiebre", "Alergia", "Inflamación",
        "Fatiga", "Ansiedad", "Depresión", "Hipertensión", "Diabetes",
        "Asma", "Migraña", "Artritis", "Insomnio", "Gastritis"
    ]
    conditions = []
    for name in condition_names:
        condition = get_or_create(Condition, name=name)
        conditions.append(condition)

    # Crear tipos de ingreso si no existen
    intake_type_names = [
        "Oral", "Intravenoso", "Tópico", "Inhalado",
        "Sublingual", "Intramuscular", "Oftálmico", "Rectal"
    ]
    intake_types = []
    for name in intake_type_names:
        intake_type = get_or_create(IntakeType, name=name)
        intake_types.append(intake_type)

    # Nombres de medicamentos en español
    medication_names = [
        # Analgésicos
        "Paracetamol 500mg", "Ibuprofeno 400mg", "Aspirina 100mg", "Tramadol 50mg", 
        "Ketorolaco 10mg", "Diclofenaco 50mg", "Naproxeno 250mg", "Codeína 30mg",
        "Morfina 10mg", "Celecoxib 200mg",
        
        # Antibióticos
        "Amoxicilina 500mg", "Azitromicina 250mg", "Ciprofloxacino 500mg", 
        "Levofloxacino 500mg", "Clindamicina 300mg", "Doxiciclina 100mg",
        "Eritromicina 500mg", "Cefalexina 500mg", "Metronidazol 500mg", "Vancomicina 1g",
        
        # Antipiréticos
        "Paracetamol 1g", "Acetaminofén 650mg", "Ibuprofeno 200mg", "Aspirina 500mg",
        "Dipirona 500mg", "Nimesulida 100mg", "Paracetamol IV 1g", "Ketoprofeno 100mg",
        "Piroxicam 20mg", "Meloxicam 15mg",
        
        # Antihistamínicos
        "Loratadina 10mg", "Cetirizina 10mg", "Desloratadina 5mg", "Fexofenadina 120mg",
        "Clorfenamina 4mg", "Levocetirizina 5mg", "Hidroxizina 25mg", "Ebastina 10mg",
        "Rupatadina 10mg", "Bilastina 20mg",
        
        # Antiinflamatorios
        "Diclofenaco 75mg", "Naproxeno 500mg", "Ketoprofeno 150mg", "Piroxicam 20mg",
        "Meloxicam 7.5mg", "Ibuprofeno 600mg", "Dexketoprofeno 25mg", "Nabumetona 500mg",
        "Etoricoxib 60mg", "Celecoxib 200mg",
        
        # Vitaminas
        "Vitamina C 500mg", "Vitamina D 1000UI", "Complejo B", "Vitamina E 400UI",
        "Multivitamínico", "Ácido Fólico 5mg", "Vitamina B12 1000mcg", "Vitamina A 25000UI",
        "Vitamina K 10mg", "Vitamina D3 5000UI",
        
        # Antidepresivos
        "Sertralina 50mg", "Fluoxetina 20mg", "Escitalopram 10mg", "Venlafaxina 75mg",
        "Amitriptilina 25mg", "Duloxetina 60mg", "Paroxetina 20mg", "Mirtazapina 30mg",
        "Bupropión 150mg", "Trazodona 100mg",
        
        # Antihipertensivos
        "Losartán 50mg", "Amlodipino 5mg", "Enalapril 10mg", "Bisoprolol 5mg",
        "Hidroclorotiazida 25mg", "Valsartán 160mg", "Carvedilol 25mg", "Ramipril 5mg",
        "Atenolol 50mg", "Candesartán 8mg",
        
        # Antidiabéticos
        "Metformina 500mg", "Glimepirida 2mg", "Insulina Glargina 100UI", "Sitagliptina 100mg",
        "Dapagliflozina 10mg", "Empagliflozina 10mg", "Pioglitazona 15mg", "Repaglinida 1mg",
        "Saxagliptina 5mg", "Linagliptina 5mg",
        
        # Broncodilatadores
        "Salbutamol Inhalador", "Budesonida Inhalador", "Ipratropio Bromuro", "Formoterol Inhalador",
        "Tiotropio Inhalador", "Salmeterol/Fluticasona", "Indacaterol 150mcg", "Aclidinio/Formoterol",
        "Umeclidinio/Vilanterol", "Olodaterol 2.5mcg"
    ]

    # Crear medicamentos de ejemplo si no existen
    medication_names = [
        # Analgésicos
        "Paracetamol 500mg", "Ibuprofeno 400mg", "Aspirina 100mg", "Tramadol 50mg", 
        "Ketorolaco 10mg", "Diclofenaco 50mg", "Naproxeno 250mg", "Codeína 30mg",
        "Morfina 10mg", "Celecoxib 200mg",
        
        # Antibióticos
        "Amoxicilina 500mg", "Azitromicina 250mg", "Ciprofloxacino 500mg", 
        "Levofloxacino 500mg", "Clindamicina 300mg", "Doxiciclina 100mg",
        "Eritromicina 500mg", "Cefalexina 500mg", "Metronidazol 500mg", "Vancomicina 1g",
        
        # Antipiréticos
        "Paracetamol 1g", "Acetaminofén 650mg", "Ibuprofeno 200mg", "Aspirina 500mg",
        "Dipirona 500mg", "Nimesulida 100mg", "Paracetamol IV 1g", "Ketoprofeno 100mg",
        "Piroxicam 20mg", "Meloxicam 15mg",
        
        # Antihistamínicos
        "Loratadina 10mg", "Cetirizina 10mg", "Desloratadina 5mg", "Fexofenadina 120mg",
        "Clorfenamina 4mg", "Levocetirizina 5mg", "Hidroxizina 25mg", "Ebastina 10mg",
        "Rupatadina 10mg", "Bilastina 20mg",
        
        # Antiinflamatorios
        "Diclofenaco 75mg", "Naproxeno 500mg", "Ketoprofeno 150mg", "Piroxicam 20mg",
        "Meloxicam 7.5mg", "Ibuprofeno 600mg", "Dexketoprofeno 25mg", "Nabumetona 500mg",
        "Etoricoxib 60mg", "Celecoxib 200mg",
        
        # Vitaminas
        "Vitamina C 500mg", "Vitamina D 1000UI", "Complejo B", "Vitamina E 400UI",
        "Multivitamínico", "Ácido Fólico 5mg", "Vitamina B12 1000mcg", "Vitamina A 25000UI",
        "Vitamina K 10mg", "Vitamina D3 5000UI",
        
        # Antidepresivos
        "Sertralina 50mg", "Fluoxetina 20mg", "Escitalopram 10mg", "Venlafaxina 75mg",
        "Amitriptilina 25mg", "Duloxetina 60mg", "Paroxetina 20mg", "Mirtazapina 30mg",
        "Bupropión 150mg", "Trazodona 100mg",
        
        # Antihipertensivos
        "Losartán 50mg", "Amlodipino 5mg", "Enalapril 10mg", "Bisoprolol 5mg",
        "Hidroclorotiazida 25mg", "Valsartán 160mg", "Carvedilol 25mg", "Ramipril 5mg",
        "Atenolol 50mg", "Candesartán 8mg",
        
        # Antidiabéticos
        "Metformina 500mg", "Glimepirida 2mg", "Insulina Glargina 100UI", "Sitagliptina 100mg",
        "Dapagliflozina 10mg", "Empagliflozina 10mg", "Pioglitazona 15mg", "Repaglinida 1mg",
        "Saxagliptina 5mg", "Linagliptina 5mg",
        
        # Broncodilatadores
        "Salbutamol Inhalador", "Budesonida Inhalador", "Ipratropio Bromuro", "Formoterol Inhalador",
        "Tiotropio Inhalador", "Salmeterol/Fluticasona", "Indacaterol 150mcg", "Aclidinio/Formoterol",
        "Umeclidinio/Vilanterol", "Olodaterol 2.5mcg"
    ]

    # Verificar si ya existen medicamentos
    medications = db.query(Medication).all()
    existing_meds_count = len(medications)
    if existing_meds_count == 0:
        # Crear medicamentos de ejemplo
        new_medications = []
        for i, med_name in enumerate(medication_names, 1):
            # Asignar categoría basada en el índice para asegurar distribución
            category_id = ((i-1) // 10) + 1
            if category_id > 10:  # Asegurarse de no exceder el número de categorías
                category_id = 10
                
            medication = Medication(
                name=med_name,
                category_id=category_id,
                intake_type_id=random.randint(1, len(intake_types))
            )
            # Asignar 1 a 3 condiciones aleatorias
            medication_conditions = random.sample(conditions, k=random.randint(1, 3))
            medication.conditions = medication_conditions
            new_medications.append(medication)
        
        db.add_all(new_medications)
        db.commit()
        medications = new_medications  # Actualizar la lista de medicamentos
        print(f"Se han creado {len(new_medications)} medicamentos.")
    else:
        print(f"Ya existen {existing_meds_count} medicamentos en la base de datos.")

    # Generate 36 months of data (January 2022 to December 2024)
    start_date = datetime(2022, 1, 1)
    for medication in medications:
        stock = 100.0  # Initial stock
        category_id = medication.category_id

        for i in range(36):
            date = start_date + timedelta(days=30 * i)
            month_of_year = date.month

            # Define seasonal patterns based on category
            if category_id == 1:  # Analgesics: peak in winter
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
            elif category_id == 2:  # Antibiotics: peak in autumn
                seasonal_factor = 1.0 + 0.3 if month_of_year in [9, 10, 11] else 1.0
            elif category_id == 3:  # Antipyretics: peak in winter
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
            elif category_id == 4:  # Antihistamines: peak in spring
                seasonal_factor = 1.0 + 0.5 if month_of_year in [3, 4, 5] else 1.0
            elif category_id == 5:  # Anti-inflammatories: peak in summer
                seasonal_factor = 1.0 + 0.2 if month_of_year in [6, 7, 8] else 1.0
            elif category_id == 6:  # Vitamins: slight peak in winter
                seasonal_factor = 1.0 + 0.1 if month_of_year in [1, 2, 12] else 1.0
            elif category_id == 7:  # Antidepressants: peak in winter
                seasonal_factor = 1.0 + 0.3 if month_of_year in [1, 2, 12] else 1.0
            elif category_id == 8:  # Antihypertensives: slight peak in end of year
                seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
            elif category_id == 9:  # Antidiabetics: slight peak in end of year
                seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
            elif category_id == 10:  # Bronchodilators: peak in winter and spring
                seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 3, 4, 12] else 1.0

            # Simulate real and predicted usage
            base_usage = random.uniform(50, 100)  # Base usage
            real_usage = base_usage * seasonal_factor
            predicted_usage = real_usage * random.uniform(0.9, 1.1)  # 10% variation
            stock -= real_usage
            if stock < 0:
                stock = 0
            shortage = 1 if stock == 0 else 0
            regional_demand = random.uniform(300, 700) * seasonal_factor
            restock_time = random.uniform(5, 15) if shortage else None

            # Crear movimiento asociado
            movement = Movement(
                medication_id=medication.id,
                date=date,
                type="salida" if real_usage > 0 else "entrada",
                quantity=real_usage if real_usage > 0 else -stock
            )
            db.add(movement)
            db.flush()  # To get the movement ID

            # Create prediction
            prediction = Prediction(
                medication_id=medication.id,
                date=date,
                real_usage=real_usage,
                predicted_usage=predicted_usage,
                stock=stock,
                month_of_year=month_of_year,
                regional_demand=regional_demand,
                restock_time=restock_time,
                shortage=shortage,
                movement_id=movement.id
            )
            db.add(prediction)

            # Simular reabastecimiento cada 4 meses
            if i % 4 == 0 and i > 0:
                restock_amount = random.uniform(100, 200)
                stock += restock_amount
                movement_restock = Movement(
                    medication_id=medication.id,
                    date=date,
                    type="entrada",
                    quantity=restock_amount
                )
                db.add(movement_restock)

    # Crear usuarios de ejemplo
    users = [
        User(
            nombre="Administrador del Sistema",
            email="admin@utcubamba.com",
            hashed_password=User.hash_password("Admin123"),
            cargo="Administrador de Sistema",
            departamento="Tecnologías de la Información",
            contacto="+51987654321",
            fecha_ingreso=datetime(2023, 1, 1),
            estado="activo",
            role="admin"
        ),
        User(
            nombre="Usuario de Prueba",
            email="usuario1@utcubamba.com",
            hashed_password=User.hash_password("Usuario123"),
            cargo="Analista de Farmacia",
            departamento="Farmacia",
            contacto="+51987654322",
            fecha_ingreso=datetime(2023, 2, 15),
            estado="activo",
            role="user"
        ),
        User(
            nombre="Responsable de Farmacia",
            email="farmacia@utcubamba.com",
            hashed_password=User.hash_password("Farmacia123"),
            cargo="Jefe de Farmacia",
            departamento="Farmacia",
            contacto="+51987654323",
            fecha_ingreso=datetime(2023, 3, 1),
            estado="activo",
            role="farmacia"
        ),
        User(
            nombre="Enfermera Jefe",
            email="enfermeria@utcubamba.com",
            hashed_password=User.hash_password("Enfermeria123"),
            cargo="Enfermera Jefe",
            departamento="Enfermería",
            contacto="+51987654324",
            fecha_ingreso=datetime(2023, 1, 15),
            estado="activo",
            role="enfermeria"
        )
    ]
    
    # Verificar si los usuarios ya existen
    existing_users = {user.email: user for user in db.query(User).all()}
    new_users = []
    updated_count = 0
    
    for user in users:
        if user.email in existing_users:
            # Actualizar usuario existente
            db_user = existing_users[user.email]
            update_fields = False
            
            # Verificar si hay campos para actualizar (excluyendo role para evitar problemas con el enum)
            if db_user.nombre != user.nombre or \
               db_user.cargo != user.cargo or \
               db_user.departamento != user.departamento or \
               db_user.contacto != user.contacto or \
               db_user.fecha_ingreso != user.fecha_ingreso or \
               db_user.estado != user.estado:
                
                # Actualizar solo los campos necesarios
                db_user.nombre = user.nombre
                db_user.cargo = user.cargo
                db_user.departamento = user.departamento
                db_user.contacto = user.contacto
                db_user.fecha_ingreso = user.fecha_ingreso
                db_user.estado = user.estado
                update_fields = True
            
            if update_fields:
                updated_count += 1
        else:
            # Para usuarios nuevos, verificar si el rol existe antes de agregar
            try:
                # Intentar convertir el rol al enum para validar
                Role(user.role)
                new_users.append(user)
            except ValueError as e:
                print(f"Advertencia: El rol '{user.role}' no es válido para el usuario {user.email}. Usuario no agregado.")
                continue
    
    # Guardar cambios en la base de datos
    if new_users:
        db.add_all(new_users)
        print(f"Se han creado {len(new_users)} nuevos usuarios.")
    
    if updated_count > 0 or new_users:
        db.commit()
        
    if updated_count > 0:
        print(f"Se actualizaron {updated_count} usuarios existentes.")
    elif not new_users:
        print("No hay usuarios nuevos para crear ni actualizar.")

    db.close()
    print("Base de datos poblada con éxito.")

if __name__ == "__main__":
    seed_db()