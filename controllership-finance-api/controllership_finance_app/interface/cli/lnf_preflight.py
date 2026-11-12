"""CLI: python -m controllership_finance_app.interface.cli.lnf_preflight

Não monta rotas HTTP. Não depende de LNF_HOSTED_ENABLED.
"""

from __future__ import annotations

import sys

from controllership_finance_app.application.invoice_posting.preflight import (
    exit_code,
    format_report,
    run_lnf_preflight,
)


def main(argv: list[str] | None = None) -> int:
    _ = argv  # reserved for future flags
    items = run_lnf_preflight()
    print(format_report(items))
    return exit_code(items)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
