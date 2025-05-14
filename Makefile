.PHONY: setup backend-deps frontend-deps

setup: backend-deps frontend-deps

backend-deps:
	@echo "Installing backend dependencies with Poetry..."
	@cd backend && poetry install --no-root

frontend-deps:
	@echo "Installing frontend dependencies..."
	@cd frontend && pnpm install
