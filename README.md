# Utcubamba CRUD API with Authentication and Medicamentos

A FastAPI backend for user management and medicamentos inventory with JWT authentication, role-based access, refresh tokens, database migrations using Alembic, logging, and advanced features like filtering, CSV/Excel import/export, and CSV validation.

## Features

- User registration, login, and CRUD operations.
- Medicamentos CRUD operations (create, read, update, delete).
- Advanced filtering for medicamentos (by name, laboratory, stock, price, etc.).
- Export medicamentos to CSV.
- Import medicamentos from CSV or Excel (.csv, .xlsx, .xls).
- Validate CSV files before importing.
- Role-based access (`admin` and `user`).
- Refresh tokens with a limit of 5 per user.
- Secure configuration with `.env`.
- SQLAlchemy for database management.
- Alembic for database migrations.
- Logging for application and migration operations.
- Script to populate medicamentos with sample data.

## Requirements

- Python 3.8+
- PostgreSQL
- Dependencies listed in `requirements.txt`

## Setup

1. **Clone the repository**:

   ```bash
   git clone <repository-url>
   cd project
   ```

2. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure PostgreSQL**:

   - Create a database named `users_db`:

     ```bash
     createdb users_db
     ```

4. **Configure environment variables**:

   - Create a `.env` file in the project root:

     ```env
     SECRET_KEY=your-secure-key-here
     DB_NAME=users_db
     DB_USER=postgres
     DB_PASSWORD=your_password
     DB_HOST=localhost
     DB_PORT=5432
     ```
   - Generate a secure `SECRET_KEY`:

     ```bash
     openssl rand -hex 32
     ```

5. **Initialize Alembic migrations**:

   - Initialize Alembic:

     ```bash
     alembic init migrations
     ```
   - Update `migrations/env.py` to include `target_metadata` from `src.models.database_models`.
   - Generate the initial migration:

     ```bash
     alembic revision --autogenerate -m "Initial migration"
     ```
   - Generate the medicamentos migration:

     ```bash
     alembic revision --autogenerate -m "Add medicamentos table"
     ```
   - Apply migrations:

     ```bash
     alembic upgrade head
     ```

6. **Populate medicamentos table**:

   - Run the population script:

     ```bash
     python populate_medicamentos.py
     ```

7. **Create an initial admin user**:

   - Generate a password hash:

     ```python
     from passlib.context import CryptContext
     pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
     print(pwd_context.hash("Secure123"))
     ```
   - Insert the admin user into the database:

     ```sql
     INSERT INTO users (name, email, password, role)
     VALUES ('Admin User', 'admin@example.com', '$2b$12$<hashed_password>', 'admin');
     ```

8. **Run the application**:

   ```bash
   python main.py
   ```

   The server will run at `http://127.0.0.1:8000`.

## Database Migrations

- **Generate a new migration** (after modifying models):

  ```bash
  alembic revision --autogenerate -m "Description of changes"
  ```
- **Apply migrations**:

  ```bash
  alembic upgrade head
  ```
- **Revert migrations**:

  ```bash
  alembic downgrade -1
  ```
- **View migration history**:

  ```bash
  alembic history
  ```

## Logging

- Logs are stored in `logs/app.log` and displayed in the console.
- Key events logged:
  - Application startup and shutdown.
  - Database migrations (start, success, errors).
  - User operations (login, registration, token refresh, revocation, etc.).
  - Medicamentos operations (create, read, update, delete, filtering, CSV/Excel import/export, CSV validation).
- Log format: `YYYY-MM-DD HH:MM:SS [LEVEL] [MODULE] MESSAGE`
- Logs rotate automatically when reach 10MB, keeping 5 backups.

## Testing

- Access the interactive API docs at `http://127.0.0.1:8000/docs`.
- Example requests:
  - Login:

    ```bash
    curl -X POST "http://127.0.0.1:8000/auth/token" -H "Content-Type: application/x-www-form-urlencoded" -d "username=admin@example.com&password=Secure123"
    ```
  - Create a medicamento (admin):

    ```bash
    curl -X POST "http://127.0.0.1:8000/medicamentos/" -H "Content-Type: application/json" -H "Authorization: Bearer <admin_access_token>" -d '{"nombre_comercial":"Panadol","nombre_generico":"Paracetamol","presentacion":"Tabletas","concentracion":"500mg","laboratorio":"Genfar","precio_unitario":5.50,"stock_actual":150,"fecha_vencimiento":"2026-03-15","codigo_barras":"7702031000012","requiere_receta":false,"unidad_empaque":10,"via_administracion":"Oral"}'
    ```
  - List medicamentos with filters (admin):

    ```bash
    curl -X GET "http://127.0.0.1:8000/medicamentos/?nombre_comercial=Panadol&laboratorio=Genfar&requiere_receta=false&stock_min=100" -H "Authorization: Bearer <admin_access_token>"
    ```
  - Export medicamentos to CSV (admin):

    ```bash
    curl -X GET "http://127.0.0.1:8000/medicamentos/export/csv?laboratorio=Bayer" -H "Authorization: Bearer <admin_access_token>" -o medicamentos.csv
    ```
  - Validate CSV (admin):

    ```bash
    curl -X POST "http://127.0.0.1:8000/medicamentos/validate/csv" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.csv"
    ```
  - Import medicamentos from CSV or Excel (admin):

    ```bash
    curl -X POST "http://127.0.0.1:8000/medicamentos/import" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.csv"
    curl -X POST "http://127.0.0.1:8000/medicamentos/import" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.xlsx"
    ```
  - Get a medicamento (authenticated user):

    ```bash
    curl -X GET "http://127.0.0.1:8000/medicamentos/1" -H "Authorization: Bearer <access_token>"
    ```

## Endpoints

- **Auth**:
  - `POST /auth/register`: Register a user (requires authentication).
  - `POST /auth/token`: Login to obtain access and refresh tokens.
  - `POST /auth/refresh`: Refresh tokens.
  - `POST /auth/logout`: Invalidate a refresh token.
- **Users**:
  - `POST /users/`: Create a user (admins only).
  - `GET /users/`: List users (admins only).
  - `GET /users/{user_id}`: Get a user (admins or self).
  - `PUT /users/{user_id}`: Update a user (admins or self; revokes tokens on password change).
  - `DELETE /users/{user_id}`: Delete a user (admins only).
  - `POST /users/me/revoke-refresh-tokens`: Revoke own refresh tokens.
  - `GET /users/{user_id}/refresh-tokens`: View active refresh tokens (admins only).
  - `POST /users/{user_id}/revoke-refresh-tokens`: Revoke all refresh tokens for a user (admins only).
- **Medicamentos**:
  - `POST /medicamentos/`: Create a medicamento (admins only).
  - `GET /medicamentos/`: List medicamentos (admins only, with pagination and advanced filters).
  - `GET /medicamentos/{medicamento_id}`: Get a medicamento (authenticated users).
  - `PUT /medicamentos/{medicamento_id}`: Update a medicamento (admins only).
  - `DELETE /medicamentos/{medicamento_id}`: Delete a medicamento (admins only).
  - `GET /medicamentos/export/csv`: Export medicamentos to CSV (admins only, with filters).
  - `POST /medicamentos/import`: Import medicamentos from CSV or Excel (admins only).
  - `POST /medicamentos/validate/csv`: Validate a CSV file before importing (admins only).

## Populate Medicamentos

- Run the script to populate the `medicamentos` table with sample data:

  ```bash
  python populate_medicamentos.py
  ```
- This adds 10 realistic medicamentos to the database, logged in `logs/app.log`.

## Import Medicamentos from CSV or Excel

- Prepare a CSV or Excel file with the following columns:

  ```csv
  medicamento_id,nombre_comercial,nombre_generico,presentacion,concentracion,laboratorio,precio_unitario,stock_actual,fecha_vencimiento,codigo_barras,requiere_receta,unidad_empaque,via_administracion
  ,Metformina,Metformina,Tabletas,850mg,Genfar,7.80,100,2026-06-30,7702031000111,True,30,Oral
  ```
- Notes:
  - `medicamento_id` can be empty (auto-incremented by the database).
  - `codigo_barras` can be empty (optional).
  - `requiere_receta` accepts `True`, `False`, `1`, `0`, `yes`, `no` (case-insensitive).
  - `fecha_vencimiento` must be in `YYYY-MM-DD` format or a valid date in Excel.
- Upload the file using the import endpoint:

  ```bash
  curl -X POST "http://127.0.0.1:8000/medicamentos/import" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.csv"
  curl -X POST "http://127.0.0.1:8000/medicamentos/import" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.xlsx"
  ```
- Check `logs/app.log` for import results.

## Validate CSV

- Validate a CSV file before importing to ensure it has the correct format and data:

  ```bash
  curl -X POST "http://127.0.0.1:8000/medicamentos/validate/csv" -H "Authorization: Bearer <admin_access_token>" -F "file=@medicamentos_import.csv"
  ```
- Response example:

  ```json
  {
    "message": "Successfully validated 3 rows"
  }
  ```

  Or with errors:

  ```json
  {
    "message": "Validated 2 valid rows with 1 errors",
    "errors": ["Row 3: Field cannot be empty"]
  }
  ```
- Check `logs/app.log` for validation results.