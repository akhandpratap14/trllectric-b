## 1. Create a `.env` File

Create a `.env` file in the project root and add the following content:

```env
DB_USER=glosys
DB_PASSWORD=apple
DB_HOST=localhost
DB_PORT=5432
DB_NAME=trillectric
DB_SCHEMA=trillectric
database_url=postgresql+asyncpg://glosys:apple@localhost:5432/trillectric

REDIS_CACHE_ENABLED=true
REDIS_HOST=localhost 
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_CACHE_EXPIRATION_SECONDS=1800
REDIS_DB=0
```

## 2. Install Dependencies

Run the following command to install required packages:

```sh
pip install -r requirements.txt
```

## 3. Setup the Database

Ensure PostgreSQL is running, then create the database:

```sh
psql -U user-name -c "CREATE DATABASE trillectric;"
```

Run migrations using Alembic:

```sh
alembic upgrade head
```

## 4. Start FastAPI Server

Run the FastAPI project using Uvicorn:

```sh
uvicorn src.main:app --reload
```

The server will be available at `http://127.0.0.1:8000`

## 5. API Documentation

Access the interactive API docs at:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
