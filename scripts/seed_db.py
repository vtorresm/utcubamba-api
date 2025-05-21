from datetime import datetime, timedelta
import random
from typing import List, Optional, Type, TypeVar, Any

from sqlmodel import Session, select
from sqlalchemy.orm import joinedload
from src.core.database import engine, create_db_and_tables
from src.models import (
    Category,
    Condition,
    IntakeType,
    Medication,
    Movement,
    Prediction,
    User,
    UserStatus,
    Role,
    MedicationConditionLink
)
from src.core.security import get_password_hash

# Type variable for SQLModel classes
T = TypeVar('T')

def get_or_create(session: Session, model: Type[T], **kwargs: Any) -> T:
    """Get or create a model instance."""
    # Handle special case for User model (password hashing)
    if model == User and 'password' in kwargs:
        kwargs['hashed_password'] = get_password_hash(kwargs.pop('password'))
    
    # For User model, always try to find by email first
    if model == User and 'email' in kwargs:
        stmt = select(model).where(model.email == kwargs['email'])
        instance = session.exec(stmt).first()
        if instance:
            return instance
    
    # For other models, try to find by all provided attributes
    filter_conditions = []
    for key, value in kwargs.items():
        if hasattr(model, key):  # Only include attributes that exist in the model
            filter_conditions.append(getattr(model, key) == value)
    
    if filter_conditions:  # If we have valid filter conditions
        stmt = select(model).where(*filter_conditions)
        instance = session.exec(stmt).first()
        if instance:
            return instance
    
    # Create new instance if not found
    try:
        # Only include attributes that exist in the model
        model_attrs = {k: v for k, v in kwargs.items() if hasattr(model, k)}
        instance = model(**model_attrs)
        session.add(instance)
        session.commit()
        session.refresh(instance)
        return instance
    except Exception as e:
        session.rollback()
        # If there was an error, try to get the existing instance again
        if 'email' in kwargs and hasattr(model, 'email'):
            stmt = select(model).where(model.email == kwargs['email'])
            instance = session.exec(stmt).first()
            if instance:
                return instance
        
        # If we still can't find it, re-raise the exception
        print(f"Error in get_or_create: {e}")
        raise

def seed_db():
    # Create database tables if they don't exist
    create_db_and_tables()
    
    with Session(engine) as session:  # Use context manager for session
        # Create categories if they don't exist
        category_names = [
            "Analgésicos", "Antibióticos", "Antipiréticos", "Antihistamínicos",
            "Antiinflamatorios", "Vitaminas", "Antidepresivos", "Antihipertensivos",
            "Antidiabéticos", "Broncodilatadores"
        ]
        categories = []
        for name in category_names:
            category = get_or_create(session, Category, name=name)
            categories.append(category)

        # Create conditions if they don't exist
        condition_names = [
            "Dolor", "Infección", "Fiebre", "Alergia", "Inflamación",
            "Fatiga", "Ansiedad", "Depresión", "Hipertensión", "Diabetes",
            "Asma", "Migraña", "Artritis", "Insomnio", "Gastritis"
        ]
        conditions = []
        for name in condition_names:
            condition = get_or_create(session, Condition, name=name)
            conditions.append(condition)
        
        # Refresh all conditions to ensure they're in the session
        conditions = [session.get(Condition, c.id) for c in conditions]

        # Create intake types if they don't exist
        intake_type_names = [
            "Oral", "Intravenoso", "Tópico", "Inhalado",
            "Sublingual", "Intramuscular", "Oftálmico", "Rectal"
        ]
        intake_types = []
        for name in intake_type_names:
            intake_type = get_or_create(session, IntakeType, name=name)
            intake_types.append(intake_type)

        # Create test users
        users = [
            {
                "email": "admin@example.com",
                "nombre": "Admin User",
                "cargo": "Administrador del Sistema",
                "departamento": "TI",
                "contacto": "123456789",
                "password": "admin123",
                "role": Role.ADMIN,
                "estado": UserStatus.ACTIVO
            },
            {
                "email": "farmacia@example.com",
                "nombre": "Farmacia User",
                "cargo": "Farmacéutico",
                "departamento": "Farmacia",
                "contacto": "987654321",
                "password": "farmacia123",
                "role": Role.FARMACIA,
                "estado": UserStatus.ACTIVO
            },
            {
                "email": "enfermeria@example.com",
                "nombre": "Enfermería User",
                "cargo": "Enfermero/a",
                "departamento": "Enfermería",
                "contacto": "456789123",
                "password": "enfermeria123",
                "role": Role.ENFERMERIA,
                "estado": UserStatus.ACTIVO
            }
        ]
        
        created_users = []
        for user_data in users:
            user = get_or_create(session, User, **user_data)
            created_users.append(user)
            print(f"Usuario creado/actualizado: {user.email} con rol {user.role}")
        
        # Get the admin user for later use
        admin_user = next((u for u in created_users if u.role == Role.ADMIN), None)
        
        if admin_user:
            print(f"Usuario administrador creado: {admin_user.email} con contraseña: admin123")
        else:
            print("Error: No se pudo crear el usuario administrador")
            return

        # Check if medications already exist
        stmt = select(Medication)
        existing_meds = session.exec(stmt).all()
        existing_meds_count = len(existing_meds)
        
        if existing_meds_count > 0:
            print(f"Ya existen {existing_meds_count} medicamentos en la base de datos. Saltando creación de medicamentos.")
        else:
            print("Creando 75 medicamentos...")
            # Define medication data with 75 medications
            medication_data = [
                # Analgésicos (10)
                ("Paracetamol 500mg", 1, 1, ["Dolor", "Fiebre"]),
                ("Ibuprofeno 400mg", 1, 1, ["Dolor", "Inflamación", "Fiebre"]),
                ("Aspirina 100mg", 1, 1, ["Dolor", "Fiebre"]),
                ("Tramadol 50mg", 1, 1, ["Dolor"]),
                ("Ketorolaco 10mg", 1, 2, ["Dolor"]),
                ("Diclofenaco 50mg", 1, 1, ["Dolor", "Inflamación"]),
                ("Naproxeno 250mg", 1, 1, ["Dolor", "Inflamación"]),
                ("Codeína 30mg", 1, 1, ["Dolor"]),
                ("Morfina 10mg", 1, 2, ["Dolor"]),
                ("Celecoxib 200mg", 1, 1, ["Dolor", "Artritis"]),
                # Antibióticos (10)
                ("Amoxicilina 500mg", 2, 1, ["Infección"]),
                ("Azitromicina 250mg", 2, 1, ["Infección"]),
                ("Ciprofloxacino 500mg", 2, 1, ["Infección"]),
                ("Levofloxacino 500mg", 2, 1, ["Infección"]),
                ("Clindamicina 300mg", 2, 1, ["Infección"]),
                ("Doxiciclina 100mg", 2, 1, ["Infección"]),
                ("Eritromicina 500mg", 2, 1, ["Infección"]),
                ("Cefalexina 500mg", 2, 1, ["Infección"]),
                ("Metronidazol 500mg", 2, 1, ["Infección"]),
                ("Vancomicina 1g", 2, 2, ["Infección"]),
                # Antipiréticos (10)
                ("Paracetamol 1g", 3, 1, ["Fiebre", "Dolor"]),
                ("Acetaminofén 650mg", 3, 1, ["Fiebre", "Dolor"]),
                ("Ibuprofeno 200mg", 3, 1, ["Fiebre", "Dolor"]),
                ("Aspirina 500mg", 3, 1, ["Fiebre", "Dolor"]),
                ("Dipirona 500mg", 3, 1, ["Fiebre"]),
                ("Nimesulida 100mg", 3, 1, ["Fiebre"]),
                ("Paracetamol IV 1g", 3, 2, ["Fiebre"]),
                ("Ketoprofeno 100mg", 3, 1, ["Fiebre", "Dolor"]),
                ("Piroxicam 20mg", 3, 1, ["Fiebre", "Inflamación"]),
                ("Meloxicam 15mg", 3, 1, ["Fiebre", "Inflamación"]),
                # Antihistamínicos (10)
                ("Loratadina 10mg", 4, 1, ["Alergia"]),
                ("Cetirizina 10mg", 4, 1, ["Alergia"]),
                ("Desloratadina 5mg", 4, 1, ["Alergia"]),
                ("Fexofenadina 120mg", 4, 1, ["Alergia"]),
                ("Clorfenamina 4mg", 4, 1, ["Alergia"]),
                ("Levocetirizina 5mg", 4, 1, ["Alergia"]),
                ("Hidroxizina 25mg", 4, 1, ["Alergia"]),
                ("Ebastina 10mg", 4, 1, ["Alergia"]),
                ("Rupatadina 10mg", 4, 1, ["Alergia"]),
                ("Bilastina 20mg", 4, 1, ["Alergia"]),
                # Antiinflamatorios (10)
                ("Diclofenaco 75mg", 5, 1, ["Dolor", "Inflamación", "Artritis"]),
                ("Naproxeno 500mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Ketoprofeno 150mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Piroxicam 20mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Meloxicam 7.5mg", 5, 1, ["Dolor", "Inflamación", "Artritis"]),
                ("Ibuprofeno 600mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Dexketoprofeno 25mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Nabumetona 500mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Etoricoxib 60mg", 5, 1, ["Dolor", "Inflamación"]),
                ("Celecoxib 200mg", 5, 1, ["Dolor", "Inflamación"]),
                # Vitaminas (10)
                ("Vitamina C 500mg", 6, 1, ["Fatiga"]),
                ("Vitamina D 1000UI", 6, 1, ["Fatiga"]),
                ("Complejo B", 6, 1, ["Fatiga"]),
                ("Vitamina E 400UI", 6, 1, ["Fatiga"]),
                ("Multivitamínico", 6, 1, ["Fatiga"]),
                ("Ácido Fólico 5mg", 6, 1, ["Fatiga"]),
                ("Vitamina B12 1000mcg", 6, 1, ["Fatiga"]),
                ("Vitamina A 25000UI", 6, 1, ["Fatiga"]),
                ("Vitamina K 10mg", 6, 1, ["Fatiga"]),
                ("Vitamina D3 5000UI", 6, 1, ["Fatiga"]),
                # Antidepresivos (10)
                ("Sertralina 50mg", 7, 1, ["Depresión", "Ansiedad"]),
                ("Fluoxetina 20mg", 7, 1, ["Depresión"]),
                ("Escitalopram 10mg", 7, 1, ["Depresión", "Ansiedad"]),
                ("Venlafaxina 75mg", 7, 1, ["Depresión"]),
                ("Amitriptilina 25mg", 7, 1, ["Depresión", "Insomnio"]),
                ("Duloxetina 60mg", 7, 1, ["Depresión"]),
                ("Paroxetina 20mg", 7, 1, ["Depresión"]),
                ("Mirtazapina 30mg", 7, 1, ["Depresión", "Insomnio"]),
                ("Bupropión 150mg", 7, 1, ["Depresión"]),
                ("Trazodona 100mg", 7, 1, ["Depresión", "Insomnio"]),
                # Antihipertensivos (10)
                ("Losartán 50mg", 8, 1, ["Hipertensión"]),
                ("Amlodipino 5mg", 8, 1, ["Hipertensión"]),
                ("Enalapril 10mg", 8, 1, ["Hipertensión"]),
                ("Bisoprolol 5mg", 8, 1, ["Hipertensión"]),
                ("Hidroclorotiazida 25mg", 8, 1, ["Hipertensión"]),
                ("Valsartán 160mg", 8, 1, ["Hipertensión"]),
                ("Carvedilol 25mg", 8, 1, ["Hipertensión"]),
                ("Ramipril 5mg", 8, 1, ["Hipertensión"]),
                ("Atenolol 50mg", 8, 1, ["Hipertensión"]),
                ("Candesartán 8mg", 8, 1, ["Hipertensión"]),
                # Antidiabéticos (10)
                ("Metformina 500mg", 9, 1, ["Diabetes"]),
                ("Glimepirida 2mg", 9, 1, ["Diabetes"]),
                ("Insulina Glargina 100UI", 9, 6, ["Diabetes"]),
                ("Sitagliptina 100mg", 9, 1, ["Diabetes"]),
                ("Dapagliflozina 10mg", 9, 1, ["Diabetes"]),
                ("Empagliflozina 10mg", 9, 1, ["Diabetes"]),
                ("Pioglitazona 15mg", 9, 1, ["Diabetes"]),
                ("Repaglinida 1mg", 9, 1, ["Diabetes"]),
                ("Saxagliptina 5mg", 9, 1, ["Diabetes"]),
                ("Linagliptina 5mg", 9, 1, ["Diabetes"]),
                # Broncodilatadores (10)
                ("Salbutamol Inhalador", 10, 4, ["Asma"]),
                ("Budesonida Inhalador", 10, 4, ["Asma"]),
                ("Ipratropio Bromuro", 10, 4, ["Asma"]),
                ("Formoterol Inhalador", 10, 4, ["Asma"]),
                ("Tiotropio Inhalador", 10, 4, ["Asma"]),
                ("Salmeterol/Fluticasona", 10, 4, ["Asma"]),
                ("Indacaterol 150mcg", 10, 4, ["Asma"]),
                ("Aclidinio/Formoterol", 10, 4, ["Asma"]),
                ("Umeclidinio/Vilanterol", 10, 4, ["Asma"]),
                ("Olodaterol 2.5mcg", 10, 4, ["Asma"])
            ]
            
            for name, category_id, intake_type_id, condition_names in medication_data:
                # Create medication
                medication = Medication(
                    name=name,
                    category_id=category_id,
                    intake_type_id=intake_type_id,
                    stock=100.0,  # Stock inicial
                    min_stock=20.0  # Stock mínimo
                )
                
                # Add to session
                session.add(medication)
                session.commit()
                session.refresh(medication)
                
                # Add conditions
                for cond_name in condition_names:
                    condition = next((c for c in conditions if c.name == cond_name), None)
                    if condition:
                        link = MedicationConditionLink(
                            medication_id=medication.id,
                            condition_id=condition.id
                        )
                        session.add(link)
                
                session.commit()
            
            print(f"Se han creado {len(medication_data)} medicamentos con sus condiciones.")

        # Generate movement and prediction data for 36 months (January 2022 to December 2024)
        if admin_user:
            print("\nGenerando datos de movimientos y predicciones para 36 meses...")
            start_date = datetime(2022, 1, 1)
            medications = session.exec(select(Medication)).all()
            
            for medication in medications:
                stock = medication.stock or 100.0  # Start with current stock
                category_id = medication.category_id
                
                for i in range(36):  # 36 months
                    date = start_date + timedelta(days=30 * i)
                    month_of_year = date.month
                    
                    # Define seasonal patterns based on category
                    if category_id == 1:  # Analgésicos: pico en invierno
                        seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
                    elif category_id == 2:  # Antibióticos: pico en otoño
                        seasonal_factor = 1.0 + 0.3 if month_of_year in [9, 10, 11] else 1.0
                    elif category_id == 3:  # Antipiréticos: pico en invierno
                        seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 12] else 1.0
                    elif category_id == 4:  # Antihistamínicos: pico en primavera
                        seasonal_factor = 1.0 + 0.5 if month_of_year in [3, 4, 5] else 1.0
                    elif category_id == 5:  # Antiinflamatorios: pico en verano
                        seasonal_factor = 1.0 + 0.2 if month_of_year in [6, 7, 8] else 1.0
                    elif category_id == 6:  # Vitaminas: pico ligero en invierno
                        seasonal_factor = 1.0 + 0.1 if month_of_year in [1, 2, 12] else 1.0
                    elif category_id == 7:  # Antidepresivos: pico en invierno
                        seasonal_factor = 1.0 + 0.3 if month_of_year in [1, 2, 12] else 1.0
                    elif category_id == 8:  # Antihipertensivos: pico ligero en fin de año
                        seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
                    elif category_id == 9:  # Antidiabéticos: pico ligero en fin de año
                        seasonal_factor = 1.0 + 0.1 if month_of_year in [11, 12] else 1.0
                    elif category_id == 10:  # Broncodilatadores: pico en invierno y primavera
                        seasonal_factor = 1.0 + 0.4 if month_of_year in [1, 2, 3, 4, 12] else 1.0
                    
                    # Simulate real usage and predicted usage
                    base_usage = random.uniform(50, 100)  # Base usage
                    real_usage = base_usage * seasonal_factor
                    predicted_usage = real_usage * random.uniform(0.9, 1.1)  # Variation of 10%
                    stock -= real_usage
                    if stock < 0:
                        stock = 0
                    desabastecimiento = 1 if stock <= 0 else 0
                    regional_demand = random.uniform(300, 700) * seasonal_factor
                    restock_time = random.uniform(5, 15) if desabastecimiento else None
                    
                    # Create movement
                    movement = Movement(
                        date=date,
                        type="OUT" if real_usage > 0 else "IN",
                        quantity=real_usage if real_usage > 0 else -stock,
                        notes=f"Movimiento automático para {medication.name}",
                        medication_id=medication.id
                    )
                    session.add(movement)
                    session.commit()
                    session.refresh(movement)
                    
                    # Update medication stock
                    medication.stock = stock
                    session.add(medication)
                    
                    # Create prediction
                    prediction = Prediction(
                        date=date,
                        real_usage=real_usage,
                        predicted_usage=predicted_usage,  # Corregido de predicted_quantity
                        stock=stock,
                        month_of_year=month_of_year,
                        regional_demand=regional_demand,
                        restock_time=restock_time,
                        shortage=bool(desabastecimiento),  # Corregido de desabastecimiento a shortage
                        medication_id=medication.id
                    )
                    session.add(prediction)
                    
                    # Simulate restocking every 4 months
                    if i % 4 == 0 and i > 0:
                        restock_amount = random.uniform(100, 200)
                        stock += restock_amount
                        restock_movement = Movement(
                            date=date,
                            type="IN",
                            quantity=restock_amount,
                            notes=f"Reabastecimiento automático para {medication.name}",
                            medication_id=medication.id
                        )
                        session.add(restock_movement)
                        medication.stock = stock
                        session.add(medication)
                    
                    # Commit periodically to avoid large transactions
                    if i % 4 == 0:
                        session.commit()
                
                session.commit()
                print(f"Datos generados para medicamento: {medication.name}")
            
            session.commit()
        
        print("Datos de movimientos y predicciones generados exitosamente.")
        print("¡Base de datos poblada exitosamente!")

if __name__ == "__main__":
    seed_db()