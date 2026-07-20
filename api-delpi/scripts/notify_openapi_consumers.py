"""Dispara reimport OpenAPI nos consumidores (chat + TV) após a api-delpi subir.

Uso:
  PYTHONPATH=/app python scripts/notify_openapi_consumers.py
  PYTHONPATH=/app python scripts/notify_openapi_consumers.py --dry-run

Variáveis (também lidas pelo serviço de startup):
  OPENAPI_CONSUMER_NOTIFY_ENABLED=true
  OPENAPI_CONSUMER_CHAT_SYNC_URL=http://delpi-minha-delpi-ai-api:8000/chat/internal/openapi/sync-api-delpi
  OPENAPI_CONSUMER_TV_SYNC_URL=http://delpi-tv-dashboard-api:8000/data/openapi/sync
  OPENAPI_CONSUMER_NOTIFY_TIMEOUT_SECONDS=120
  API_DELPI_INTERNAL_SERVICE_TOKEN=…  (obrigatório para autenticação S2S)
"""

from __future__ import annotations

import argparse
import json
import sys

from app.application.services.openapi_consumer_notify_service import (
    OpenApiConsumerNotifyService,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Só lista alvos configurados, sem HTTP",
    )
    parser.add_argument(
        "--skip-chat",
        action="store_true",
        help="Não notifica o chat",
    )
    parser.add_argument(
        "--skip-tv",
        action="store_true",
        help="Não notifica o TV",
    )
    args = parser.parse_args()

    service = OpenApiConsumerNotifyService()
    if args.dry_run:
        report = {
            "dryRun": True,
            "targets": service.list_targets(skip_chat=args.skip_chat, skip_tv=args.skip_tv),
            "tokenConfigured": service.has_service_token(),
        }
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0

    report = service.notify_all(skip_chat=args.skip_chat, skip_tv=args.skip_tv)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
