# User CRUD API with Authentication and Medicamentos

A FastAPI backend for user management and medicamentos inventory with JWT authentication, role-based access, refresh tokens, database migrations using Alembic, logging, and advanced features like filtering and CSV export.

## Features
- User registration, login, and CRUD operations.
- Medicamentos CRUD operations (create, read, update, delete).
- Advanced filtering for medicamentos (by name, laboratory, stock, price, etc.).
- Export medicamentos to CSV.
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