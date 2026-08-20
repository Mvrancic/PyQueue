# PyQueue

**Un sistema de colas de tareas y procesamiento de jobs, liviano y autoalojado**, construido con FastAPI, Redis y PostgreSQL.

PyQueue permite encolar jobs en background a través de una API REST, procesarlos de forma asíncrona con un worker desacoplado, y hacer seguimiento de su estado, resultados y errores — con reintentos automáticos incluidos.

## Funcionalidades

- **API de gestión de jobs** — crear, consultar, listar, cancelar y reintentar jobs vía REST.
- **Procesamiento asíncrono en background** — un worker independiente consume jobs de una cola en Redis, desacoplado del proceso de la API.
- **Persistencia** — el estado, payload, resultados y errores de cada job se guardan en PostgreSQL.
- **Reintentos automáticos** — los jobs fallidos se vuelven a encolar hasta un `max_retries` configurable, con el conteo de reintentos registrado por job.
- **Tipos de job extensibles** — los handlers se registran en un task registry, así que agregar un nuevo tipo de job es escribir una función.
- **Dockerizado** — API, worker, PostgreSQL y Redis levantan todos con un solo `docker-compose up`.

## Arquitectura

```
        POST /jobs                 BRPOP
Cliente ────────────► API ──────► Redis ──────► Worker ──────► Handler
                        │ (FastAPI)  (cola)                (sleep/csv_stats/...)
                        │
                        ▼
                  PostgreSQL
              (estado y resultados)
```

| Componente | Responsabilidad                                                          |
|------------|----------------------------------------------------------------------------|
| API        | App FastAPI que recibe solicitudes de jobs y expone endpoints de estado    |
| Redis      | Cola liviana que transporta IDs de jobs entre la API y el worker           |
| Worker     | Proceso de larga duración que desencola jobs (`BRPOP`) y los ejecuta       |
| PostgreSQL | Fuente de verdad del estado, payloads, resultados y errores de cada job    |

## Stack Tecnológico

Python 3.11 · FastAPI · SQLAlchemy · Alembic · Redis · PostgreSQL · Docker Compose · Pytest

## Decisiones técnicas y limitaciones conocidas

**Redis como buffer, PostgreSQL como fuente de verdad.** La cola solo transporta
job IDs; todo el estado vive en Postgres. Esto permite reconstruir el estado del
sistema aunque se pierda Redis, a costa de una consulta extra por job.

**Semántica at-most-once (limitación conocida).** El worker hace `BRPOP` y luego
actualiza el estado en la base. Si el proceso cae entre esas dos operaciones, el
job se pierde: no hay ack ni visibility timeout. Para at-least-once haría falta
una cola intermedia de "in-flight" (patrón `BRPOPLPUSH`) con un reaper que
devuelva los jobs huérfanos.

**Cancelación cooperativa.** Cancelar un job en estado RUNNING marca la base pero
no interrumpe el handler en curso. Interrumpirlo requeriría que los handlers
chequeen periódicamente una señal de cancelación.

**Sin prioridades ni scheduling.** Una sola cola FIFO. Prioridades exigirían
múltiples listas de Redis; jobs diferidos, un sorted set por timestamp.

## Cómo empezar

### Requisitos previos

- Docker & Docker Compose

### Levantar el sistema

1. Copiá el archivo de entorno de ejemplo y ajustalo si hace falta:
   ```bash
   cp .env.example .env
   ```

2. Levantá todo (API, worker, PostgreSQL, Redis):
   ```bash
   docker-compose up --build
   ```

3. Explorá la API:
   - URL base: `http://localhost:8000/api/v1`
   - Documentación interactiva (Swagger UI): `http://localhost:8000/docs`

### Referencia de la API

| Método | Endpoint                       | Descripción                              |
|--------|---------------------------------|--------------------------------------------|
| POST   | `/api/v1/jobs`                  | Crea y encola un nuevo job                 |
| GET    | `/api/v1/jobs`                  | Lista jobs (filtrable por `status`)        |
| GET    | `/api/v1/jobs/{job_id}`         | Obtiene un job puntual                     |
| POST   | `/api/v1/jobs/{job_id}/cancel`  | Cancela un job en cola o en ejecución      |
| POST   | `/api/v1/jobs/{job_id}/retry`   | Vuelve a encolar un job fallido o cancelado|
| GET    | `/health`                       | Chequeo de disponibilidad                  |

### Tipos de job

| Tipo        | Payload                    | Descripción                                              |
|-------------|-----------------------------|-------------------------------------------------------------|
| `sleep`     | `{ "seconds": 3 }`          | Simula una tarea lenta durmiendo N segundos                 |
| `csv_stats` | `{ "csv_text": "..." }`     | Parsea texto CSV y devuelve estadísticas de filas/columnas  |
| `fail`      | `{}`                        | Siempre falla — útil para probar el pipeline de reintentos  |

### Ejemplos de uso

**Crear un job:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "csv_stats",
    "payload": { "csv_text": "id,name,score\n1,Alice,90\n2,Bob,85" },
    "max_retries": 2
  }'
```

**Consultar estado** (reemplazá `JOB_ID` con el id devuelto arriba):
```bash
curl "http://localhost:8000/api/v1/jobs/JOB_ID"
```

**Cancelar un job:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/JOB_ID/cancel"
```

**Reintentar un job fallido:**
```bash
curl -X POST "http://localhost:8000/api/v1/jobs/JOB_ID/retry"
```

## Estructura del proyecto

```
src/pyqueue/
├── api/                # Rutas de FastAPI, schemas de request/response
├── domain/              # Enums centrales (JobStatus, JobType)
├── infra/
│   ├── db/              # Modelos SQLAlchemy, sesión, migraciones Alembic
│   └── queue/            # Cliente de la cola en Redis
├── services/            # Lógica de negocio (JobService, task registry)
├── workers/              # Entry point del worker + handlers de jobs
├── config.py             # Configuración basada en variables de entorno
└── main.py                # Entry point de la app FastAPI
```

## Desarrollo

Correr el test suite localmente sin Docker:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
PYTHONPATH=. pytest tests/
```

### Migraciones de base de datos

Las migraciones se manejan con Alembic:

```bash
alembic upgrade head        # aplica migraciones
alembic revision --autogenerate -m "mensaje"   # crea una nueva migración
```

## Licencia

Este proyecto se provee tal cual, con fines educativos y de portfolio.
