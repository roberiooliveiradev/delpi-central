"""Catálogos fechados do domínio — valores técnicos estáveis (labels ficam na UI)."""

from __future__ import annotations

# Unidades operacionais canônicas da DELPI (mesmos códigos TOTVS de
# OPERATIONAL_UNIT_OPTIONS do @delpi/plugin-ui).
UNIT_CODES = ("01", "02")

ENVIRONMENTS = ("production", "staging", "development")
SERVER_TYPES = ("physical", "virtual", "cloud")
CRITICALITIES = ("low", "medium", "high", "critical")
ADMINISTRATIVE_STATUSES = (
    "planned",
    "in_operation",
    "maintenance",
    "decommissioning",
)

ACTION_PRIORITIES = ("low", "medium", "high", "urgent")
ACTION_STATUSES = ("pending", "in_progress", "done", "cancelled")
OPEN_ACTION_STATUSES = ("pending", "in_progress")

# Aplicação lógica de negócio × serviço de plataforma instalado. A instância em
# execução (container, processo) é a hospedagem, não um novo serviço.
SERVICE_KINDS = ("business_application", "platform_service")
SERVICE_TYPES = (
    "web_application",
    "api",
    "identity_access",
    "reverse_proxy",
    "cache",
    "messaging",
    "file_storage",
    "scheduler",
    "monitoring",
    "erp",
    "other",
)
HOSTING_RUNTIMES = ("container", "native_process", "os_service", "virtual_machine", "other")
DBMS_ENGINES = (
    "postgresql",
    "sql_server",
    "mysql",
    "mariadb",
    "oracle",
    "mongodb",
    "sqlite",
    "other",
)

# Redes internas de runtime de containers (bridge do Docker etc.) não são redes
# corporativas permanentes: a classificação é sempre explícita no cadastro.
NETWORK_SCOPES = ("corporate", "container_runtime")
INTEGRATION_PROTOCOLS = (
    "http_api",
    "soap",
    "grpc",
    "smb",
    "nfs",
    "file_transfer",
    "email_smtp",
    "ldap",
    "message_queue",
    "webhook",
    "other",
)
INTEGRATION_DIRECTIONS = ("source_to_target", "bidirectional")

HIGH_CRITICALITIES = ("high", "critical")

CRITICALITY_RANK = {value: index for index, value in enumerate(CRITICALITIES)}
PRIORITY_RANK = {value: index for index, value in enumerate(ACTION_PRIORITIES)}
