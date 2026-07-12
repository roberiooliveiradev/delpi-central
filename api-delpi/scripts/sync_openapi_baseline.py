#!/usr/bin/env python3
"""Gera/atualiza app/content/openapi_baseline.json a partir do OpenAPI da aplicação.

Uso local (com deps):
  python scripts/sync_openapi_baseline.py

A partir de spec já exportada (ex.: container):
  python scripts/sync_openapi_baseline.py --from-json /tmp/openapi_full.json

Via Docker (recomendado no monorepo):
  docker exec delpi-api-delpi python -c "from app.main import app; import json; open('/tmp/o.json','w').write(json.dumps(app.openapi()))"
  docker cp delpi-api-delpi:/tmp/o.json /tmp/openapi_full.json
  python scripts/sync_openapi_baseline.py --from-json /tmp/openapi_full.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.domain.services.openapi_baseline_service import save_openapi_baseline  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--from-json",
        type=Path,
        help="OpenAPI completo já serializado (evita importar app.main)",
    )
    args = parser.parse_args()

    if args.from_json:
        if not args.from_json.is_file():
            print(f"Arquivo ausente: {args.from_json}", file=sys.stderr)
            return 1
        spec = json.loads(args.from_json.read_text(encoding="utf-8"))
    else:
        from app.main import app  # noqa: WPS433

        spec = app.openapi()

    target = save_openapi_baseline(spec)
    print(f"Baseline OpenAPI atualizado: {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
