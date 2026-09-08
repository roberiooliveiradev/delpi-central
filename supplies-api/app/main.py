from app.create_app import create_app
from app.startup.run_migrations_on_startup import run_migrations_on_startup

try:
    run_migrations_on_startup()
except Exception:
    pass

app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=False, threaded=True)
