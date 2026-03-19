"""
Infraestrutura de persistência do contexto plugins.

Este pacote centraliza o acesso ao datasource PostgreSQL usado pelos
módulos plugáveis da DELPI Central, como o produto Qualidade DELPI.
"""

from .plugin_base_repository import (
    PluginBaseRepository,
    PluginsRepositoryError,
)
from .plugin_healthcheck import get_plugins_db_health
from app.infrastructure.providers.databse.plugins_postgres_connection import (
    PluginsDatabaseConfigError,
    PluginsDatabaseConnectionError,
    check_plugins_connection,
    close_plugins_connection,
    get_plugins_connection,
    get_plugins_connection_settings,
)

__all__ = [
    "PluginBaseRepository",
    "PluginsRepositoryError",
    "PluginsDatabaseConfigError",
    "PluginsDatabaseConnectionError",
    "get_plugins_connection",
    "close_plugins_connection",
    "check_plugins_connection",
    "get_plugins_connection_settings",
    "get_plugins_db_health",
]