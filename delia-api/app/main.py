from app.create_app import create_app
from app.infrastructure.config.settings import Settings

settings = Settings()
app = create_app()


if __name__ == "__main__":
    app.run(
        host=settings.host,
        port=settings.port,
        debug=settings.debug,
        threaded=True,
    )
