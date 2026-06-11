#!/usr/bin/env python3
"""Alinha runtime admin + reindex de embeddings das external actions (dev local)."""

from __future__ import annotations

import argparse
import json
import sys

from app.composition.admin_composer import (
    make_reindex_external_action_embeddings_use_case,
)
from app.composition.chat_composer import make_chat_intelligence_settings_service
from app.composition.root_composer import create_application
from app.extensions.db import db


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--skip-save",
        action="store_true",
        help="Não grava chat_intelligence_settings no admin runtime.",
    )
    parser.add_argument(
        "--skip-reindex",
        action="store_true",
        help="Não reindexa embeddings das external actions.",
    )
    parser.add_argument(
        "--provider-key",
        default=None,
        help="Filtra reindex por provider (opcional).",
    )
    args = parser.parse_args()

    app = create_application()
    report: dict = {}

    with app.app_context():
        if not args.skip_save:
            service = make_chat_intelligence_settings_service()
            saved = service.sync_from_environment()
            db.session.commit()
            report["savedSettings"] = {
                k: v
                for k, v in saved.items()
                if k not in {"defaults", "source"}
            }

        if not args.skip_reindex:
            report["reindex"] = make_reindex_external_action_embeddings_use_case().execute(
                provider_key=args.provider_key
            )
            db.session.commit()

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
