.PHONY: test migrate-up migrate-status

test:
	PYTHONPATH=. pytest tests/ -q

migrate-up:
	PYTHONPATH=. python -m maint_app.infrastructure.persistence.plugins.migrations_runner up

migrate-status:
	PYTHONPATH=. python -m maint_app.infrastructure.persistence.plugins.migrations_runner status
