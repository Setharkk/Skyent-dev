.PHONY: setup backend-deps frontend-deps run-api test migrate migration-new migration-autogen migration-history migration-current

setup: backend-deps frontend-deps

backend-deps:
	@echo "Installing backend dependencies with Poetry..."
	@cd backend && poetry install --no-root

frontend-deps:
	@echo "Installing frontend dependencies..."
	@cd frontend && pnpm install

run-api:
	@echo "Starting FastAPI server in development mode..."
	@cd backend && poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8080

# Database migration commands
migrate:
	@echo "Running database migrations..."
	@cd backend && DATABASE_URL=$$(poetry run python -c "from app.config import settings; print(settings.database_url)") poetry run alembic upgrade head

migration-new:
	@echo "Creating new database migration..."
	@if [ -z "$(MSG)" ]; then echo "MSG variable is not set. Usage: make migration-new MSG=\"Your migration message\""; exit 1; fi
	@cd backend && DATABASE_URL=$$(poetry run python -c "from app.config import settings; print(settings.database_url)") poetry run alembic revision -m "$(MSG)"

migration-autogen:
	@echo "Autogenerating database migration..."
	@if [ -z "$(MSG)" ]; then echo "MSG variable is not set. Usage: make migration-autogen MSG=\"Your migration message\""; exit 1; fi
	@cd backend && DATABASE_URL=$$(poetry run python -c "from app.config import settings; print(settings.database_url)") poetry run alembic revision --autogenerate -m "$(MSG)"

migration-history:
	@echo "Showing migration history..."
	@cd backend && ALAMBIC_CONTEXT=SYNC DATABASE_URL=$$(poetry run python -c "from app.config import settings; print(settings.database_url)") poetry run alembic history

migration-current:
	@echo "Showing current migration..."
	@cd backend && ALAMBIC_CONTEXT=SYNC DATABASE_URL=$$(poetry run python -c "from app.config import settings; print(settings.database_url)") poetry run alembic current

test:
	@echo "Running backend tests..."
	@cd backend && poetry run pytest
