# Database Documentation

- [Database Design](00-Database-Design.md)

## Implementation

Schema lives in `apps/api`:

- Models: `src/careerpilot/domains/*/models.py`
- Registry: `src/careerpilot/db/models.py`
- Migrations: `apps/api/alembic/versions/`

```bash
make up        # Postgres + pgvector, Redis, MinIO
make migrate   # alembic upgrade head
```
