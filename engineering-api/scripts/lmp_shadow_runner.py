"""G4.B — real shadow runner: legado api-delpi × Engineering API (facts).

Comparação read-only e reproduzível, tolerância zero nos campos
determinísticos (`engineering_app.domain.lmp.parity`).

Caminhos comparados (mesmos filtros/janela):
  legado:   GET /apps/api-delpi/engineering/lmps/dashboard/items|summary
  novo:     GET /apps/engineering-api/v1/lmps|/v1/lmps/summary
  facts:    GET /apps/api-delpi/engineering/lmps/facts  (humano+S2S)

Segurança: nunca imprime/persiste tokens, secrets ou payloads completos.
Relatório agrega contagens/latências e divergências por chave de registro
(branch|ov|revisão|ciclo) — sem `sale_description` nem dados pessoais.

Uso:
  python -m scripts.lmp_shadow_runner --token-file /tmp/devtoken.txt \
      --env-file ../infra/.env --windows 12 --out /tmp/lmp_shadow.json
"""

from __future__ import annotations

import argparse
import calendar
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from engineering_app.domain.lmp.parity import (  # noqa: E402
    compare_items,
    compare_summary,
)

PAGE_SIZE = 500
REQUEST_TIMEOUT = 180

# classificação da missão §5 — rule id → categoria de divergência
RULE_CATEGORY = {
    "R02": "SLA_MISMATCH",
    "R01": "SLA_MISMATCH",
    "R01+R03": "PERIOD_POLICY_MISMATCH",
    "R05": "LEAD_TIME_MISMATCH",
    "R04": "STATUS_RULE_MISMATCH",
    "S05": "CLASSIFICATION_MISMATCH",
    "SOURCE": "SOURCE_DATA_MISMATCH",
    "R09": "ROUNDING_MISMATCH",
    "R10": "LEAD_TIME_MISMATCH",
    "COUNT": "CONTRACT_MISMATCH",
}


def _load_dotenv(path: Path) -> dict[str, str]:
    """Parse .env com segurança — sem `source` (valores com espaços)."""
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _request(
    url: str,
    *,
    human_token: str | None = None,
    service_token: str | None = None,
) -> tuple[int, dict[str, Any], float, int]:
    """HTTP GET read-only. Retorna (status, body, elapsed_s, bytes)."""
    headers = {"Accept": "application/json"}
    if human_token:
        headers["Authorization"] = f"Bearer {human_token}"
    if service_token:
        headers["X-Delpi-Service-Authorization"] = f"Bearer {service_token}"
    req = urllib.request.Request(url, headers=headers)
    started = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
            raw = resp.read()
            return resp.status, json.loads(raw), time.monotonic() - started, len(raw)
    except urllib.error.HTTPError as exc:
        raw = exc.read() or b""
        try:
            body = json.loads(raw)
        except ValueError:
            body = {"raw": raw[:200].decode("utf-8", "replace")}
        return exc.code, body, time.monotonic() - started, len(raw)
    except Exception as exc:  # timeout/conexão — honesto no relatório
        return 0, {"error": f"{type(exc).__name__}: {exc}"}, time.monotonic() - started, 0


def _mint_service_token(env: dict[str, str], base_url: str) -> str | None:
    """Client credentials via Keycloak — token NUNCA logado/persistido."""
    client_id = env.get("ENG_S2S_CLIENT_ID")
    secret = env.get("ENG_S2S_CLIENT_SECRET")
    if not client_id or not secret:
        return None
    token_url = (
        env.get("ENG_S2S_TOKEN_URL")
        or "http://localhost/auth/realms/delpi/protocol/openid-connect/token"
    )
    # URLs internas de container não resolvem no host.
    token_url = token_url.replace("delpi-gateway", base_url.split("//")[-1].strip("/"))
    token_url = token_url.replace("keycloak:8080", base_url.split("//")[-1].strip("/"))
    body = (
        f"grant_type=client_credentials&client_id={client_id}"
        f"&client_secret={secret}"
    ).encode()
    req = urllib.request.Request(
        token_url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read()).get("access_token")
    except Exception:
        return None


def _month_windows(count: int) -> list[tuple[str, str]]:
    """Últimas N competências completas (YYYY-MM-01 → último dia)."""
    today = date.today()
    year, month = today.year, today.month - 1  # competência corrente excluída
    if month == 0:
        year, month = year - 1, 12
    windows: list[tuple[str, str]] = []
    for _ in range(count):
        last = calendar.monthrange(year, month)[1]
        windows.append((f"{year}-{month:02d}-01", f"{year}-{month:02d}-{last:02d}"))
        month -= 1
        if month == 0:
            year, month = year - 1, 12
    return windows


def _fetch_all_items(
    url_fn, human_token: str
) -> tuple[list[dict], int, float, str | None]:
    """Pagina até esgotar `total`. Retorna (items, http_status, elapsed, data_status)."""
    items: list[dict] = []
    page = 1
    total_elapsed = 0.0
    last_status = 0
    data_status: str | None = None
    while True:
        status, body, elapsed, _ = _request(
            url_fn(page), human_token=human_token
        )
        total_elapsed += elapsed
        last_status = status
        if status != 200:
            return items, status, total_elapsed, data_status
        data = body.get("data") or {}
        data_status = data.get("status") or "available"
        if data_status != "available":
            return items, status, total_elapsed, data_status
        items.extend(data.get("items") or [])
        total = int(data.get("total") or 0)
        if len(items) >= total or not data.get("items"):
            return items, status, total_elapsed, data_status
        page += 1


def _percentile(samples: list[float], pct: float) -> float | None:
    if not samples:
        return None
    ordered = sorted(samples)
    idx = max(0, min(len(ordered) - 1, round(pct / 100 * (len(ordered) - 1))))
    return round(ordered[idx], 3)


def main() -> int:
    parser = argparse.ArgumentParser(description="G4.B LMP real shadow runner")
    parser.add_argument("--base-url", default="http://localhost")
    parser.add_argument("--token-file", required=True)
    parser.add_argument("--env-file", default="../infra/.env")
    parser.add_argument("--windows", type=int, default=12)
    parser.add_argument("--max-ovs", type=int, default=200)
    parser.add_argument("--out", default=None)
    parser.add_argument("--git-sha", default="")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    human_token = Path(args.token_file).read_text().strip().splitlines()[-1].strip()
    env = _load_dotenv(Path(args.env_file)) if Path(args.env_file).exists() else {}
    svc_token = _mint_service_token(env, base)

    api_delpi = f"{base}/apps/api-delpi/engineering"
    eng_api = f"{base}/apps/engineering-api/v1"

    report: dict[str, Any] = {
        "git_sha": args.git_sha,
        "environment": base,
        "windows": [],
        "coverage": {
            "unique_ovs": 0,
            "by_listing_kind": {},
            "by_status": {},
            "by_branch": {},
        },
        "divergences": [],
        "benchmark": {"legacy_items_s": [], "facts_items_s": [], "eng_items_s": []},
        "errors": [],
        "summary": {},
    }

    def legacy_items_url(start: str, end: str, page: int) -> str:
        return (
            f"{api_delpi}/lmps/dashboard/items?start_date={start}&end_date={end}"
            f"&status=Todos&listing_type=Todos&page_size={PAGE_SIZE}&page={page}"
        )

    def eng_items_url(start: str, end: str, page: int) -> str:
        return (
            f"{eng_api}/lmps?start_date={start}&end_date={end}"
            f"&status=Todos&listing_type=Todos&page_size={PAGE_SIZE}&page={page}"
        )

    unique_ovs: set[str] = set()
    total_compared = 0
    total_matched = 0
    total_divergences = 0

    for start, end in _month_windows(args.windows):
        window: dict[str, Any] = {"period": f"{start}..{end}"}

        legacy_items, l_status, l_elapsed, l_ds = _fetch_all_items(
            lambda p: legacy_items_url(start, end, p), human_token
        )
        eng_items, e_status, e_elapsed, e_ds = _fetch_all_items(
            lambda p: eng_items_url(start, end, p), human_token
        )

        # facts cru (F-LMP-01) — benchmark + sanidade do canal técnico
        f_status, f_body, f_elapsed, f_bytes = _request(
            f"{api_delpi}/lmps/facts?start_date={start}&end_date={end}"
            f"&listing_type=Todos&page_size={PAGE_SIZE}&page=1",
            human_token=human_token,
            service_token=svc_token,
        )

        report["benchmark"]["legacy_items_s"].append(round(l_elapsed, 3))
        report["benchmark"]["eng_items_s"].append(round(e_elapsed, 3))
        report["benchmark"]["facts_items_s"].append(round(f_elapsed, 3))

        window["legacy_status"] = l_status
        window["eng_status"] = e_status
        window["facts_status"] = f_status
        window["legacy_items"] = len(legacy_items)
        window["eng_items"] = len(eng_items)
        window["facts_bytes"] = f_bytes

        # Degradação honesta (unavailable/forbidden) não é divergência de
        # paridade — a janela é registrada como TEST_NOT_RUN.
        if l_status != 200 or e_status != 200 or l_ds != "available" or e_ds != "available":
            window["error"] = "fetch_failed"
            window["legacy_data_status"] = l_ds
            window["eng_data_status"] = e_ds
            report["errors"].append(
                {
                    "period": window["period"],
                    "legacy": l_status,
                    "eng": e_status,
                    "eng_data_status": e_ds,
                }
            )
            report["windows"].append(window)
            continue

        cmp_report = compare_items(legacy_items, eng_items)
        window["compared"] = cmp_report.compared
        window["matched"] = cmp_report.matched_keys
        window["divergences"] = len(cmp_report.divergences)
        window["missing_in_eng"] = len(cmp_report.missing_in_actual)
        window["missing_in_legacy"] = len(cmp_report.missing_in_expected)
        total_compared += cmp_report.compared
        total_matched += cmp_report.matched_keys
        total_divergences += (
            len(cmp_report.divergences)
            + len(cmp_report.missing_in_actual)
            + len(cmp_report.missing_in_expected)
        )

        for div in cmp_report.divergences:
            report["divergences"].append(
                {
                    "period": window["period"],
                    "rule_id": div.rule_id,
                    "category": RULE_CATEGORY.get(div.rule_id, "UNKNOWN"),
                    "key": div.key,
                    "field": div.field,
                    "legacy_value": div.expected,
                    "engineering_value": div.actual,
                }
            )
        for key in cmp_report.missing_in_actual:
            report["divergences"].append(
                {
                    "period": window["period"],
                    "rule_id": "SOURCE",
                    "category": "SOURCE_DATA_MISMATCH",
                    "key": key,
                    "field": "__missing_in_engineering__",
                    "legacy_value": "present",
                    "engineering_value": None,
                }
            )
        for key in cmp_report.missing_in_expected:
            report["divergences"].append(
                {
                    "period": window["period"],
                    "rule_id": "SOURCE",
                    "category": "SOURCE_DATA_MISMATCH",
                    "key": key,
                    "field": "__missing_in_legacy__",
                    "legacy_value": None,
                    "engineering_value": "present",
                }
            )

        for item in legacy_items:
            key = f"{item.get('branch')}|{item.get('sale_number')}"
            unique_ovs.add(key)
            kind = item.get("listing_kind") or "?"
            status = item.get("status") or "?"
            branch = item.get("branch") or "?"
            report["coverage"]["by_listing_kind"][kind] = (
                report["coverage"]["by_listing_kind"].get(kind, 0) + 1
            )
            report["coverage"]["by_status"][status] = (
                report["coverage"]["by_status"].get(status, 0) + 1
            )
            report["coverage"]["by_branch"][branch] = (
                report["coverage"]["by_branch"].get(branch, 0) + 1
            )

        # summaries (KPIs realizados — mesma janela)
        ls_status, ls_body, _, _ = _request(
            f"{api_delpi}/lmps/dashboard/summary?start_date={start}&end_date={end}"
            f"&status=Todos&listing_type=Todos",
            human_token=human_token,
        )
        es_status, es_body, _, _ = _request(
            f"{eng_api}/lmps/summary?start_date={start}&end_date={end}",
            human_token=human_token,
        )
        window["legacy_summary_status"] = ls_status
        window["eng_summary_status"] = es_status
        if ls_status == 200 and es_status == 200:
            s_report = compare_summary(
                ls_body.get("data") or {}, es_body.get("data") or {}
            )
            window["summary_divergences"] = len(s_report.divergences)
            total_divergences += len(s_report.divergences)
            for div in s_report.divergences:
                report["divergences"].append(
                    {
                        "period": window["period"],
                        "rule_id": div.rule_id,
                        "category": RULE_CATEGORY.get(div.rule_id, "UNKNOWN"),
                        "key": "summary",
                        "field": div.field,
                        "legacy_value": div.expected,
                        "engineering_value": div.actual,
                    }
                )
        report["windows"].append(window)

    report["coverage"]["unique_ovs"] = len(unique_ovs)
    report["summary"] = {
        "items_compared": total_compared,
        "items_matched": total_matched,
        "divergences": total_divergences,
        "parity": total_divergences == 0 and total_compared > 0,
        "benchmark_p50_s": {
            k: _percentile(v, 50) for k, v in report["benchmark"].items()
        },
        "benchmark_p95_s": {
            k: _percentile(v, 95) for k, v in report["benchmark"].items()
        },
        "benchmark_p99_s": {
            k: _percentile(v, 99) for k, v in report["benchmark"].items()
        },
    }

    out = json.dumps(report, ensure_ascii=False, indent=2, default=str)
    if args.out:
        Path(args.out).write_text(out + "\n", encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
