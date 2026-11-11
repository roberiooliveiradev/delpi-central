"""CLI: python -m collectors.linux_host diagnose|submit."""

from __future__ import annotations

import argparse
import sys

from .diagnose import diagnose_json
from .submit import main as submit_main


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="collectors.linux_host",
        description="Coletor Linux read-only do Portal de TI (E4.S1).",
    )
    parser.add_argument(
        "command",
        choices=("diagnose", "submit"),
        help="diagnose: JSON local; submit: envia via S2S para a API.",
    )
    args = parser.parse_args(argv)
    if args.command == "diagnose":
        print(diagnose_json())
        return 0
    return submit_main([])


if __name__ == "__main__":
    sys.exit(main())
