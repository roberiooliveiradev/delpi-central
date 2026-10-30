"""``POST /closing/analysis/report-comparison`` orchestration engine.

Owner approved by D-03: this BFF orchestrates the governed producer
contracts — it never recalculates financial rules, never runs SQL and
never fabricates a reconciliation. Every subject value comes verbatim
from the api-delpi responses through the same S2S + delegated-bearer
chain the Portal routes use.

Execution order (GATE F — fail-closed):

1. validate the request (kind, 2..6 subjects, measure, grain, limits);
2. resolve each subject's report capability — unknown/unimplemented
   reports degrade to ``unsupported`` subjects, never to zero;
3. fetch each subject through the governed gateway — authorization
   failures mark the subject ``denied`` and strip every value; source
   failures mark it ``unavailable``/``empty`` with explicit reasons;
4. classify semantic compatibility per the curated matrix (pairwise);
5. apply ONLY the authorized normalizations (aggregation by
   competence/branch/cost-center/product/document, absolute delta,
   percentage delta with a non-zero baseline guard) — and only for
   pairs whose verdict permits a numeric delta;
6. assemble the typed result — ``PARTIAL`` declares exactly what is
   missing; it never circumvents a denied subject.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Any

from controllership_finance_app.domain.report_comparison import (
    catalog as catalog_mod,
)
from controllership_finance_app.domain.report_comparison import (
    compatibility as compat_mod,
)
from controllership_finance_app.infrastructure.api_delpi_gateway import (
    ApiDelpiSettlementsGateway,
    DelpiApiGatewayError,
)

logger = logging.getLogger(__name__)

OPERATION_ID = "post_closing_analysis_report_comparison"

COMPARISON_KINDS = frozenset(
    {"PERIOD", "BRANCH", "REPORT", "DOCUMENT", "TREND", "EXPLAIN"}
)

MAX_SUBJECTS = 6
MIN_SUBJECTS = 2
MAX_DIFFS = 500
SUBJECT_TIMEOUT_SECONDS = 30.0
ITEM_PAGE_SIZE = 200
ITEM_MAX_PAGES = 5  # bounded document fetch — 1000 items/subject

STATUS_OK = "ok"
STATUS_EMPTY = "empty"
STATUS_UNAVAILABLE = "unavailable"
STATUS_DENIED = "denied"
STATUS_UNSUPPORTED = "unsupported"

_PRODUCER_OK = "available"
_PRODUCER_EMPTY = {"no_matching_items"}

# list endpoints return paged items next to the full summary — one
# item page is enough for totals (document kind fetches items
# separately, bounded by ITEM_MAX_PAGES).
_ITEM_ENDPOINTS = frozenset(
    {
        "/financeiro/stock-inventory",
        "/financeiro/work-in-process",
        "/financeiro/cost-center-expenses",
        "/financeiro/billing-exclusion-roster",
    }
)

_PERIOD_RE = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


class ComparisonValidationError(ValueError):
    def __init__(self, message: str, *, code: str = "validation_error"):
        self.code = code
        super().__init__(message)


def _dec(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _dig(data: Any, path: str) -> Any:
    node = data
    for part in path.split("."):
        if not isinstance(node, dict):
            return None
        node = node.get(part)
    return node


def _period_window(period: str) -> tuple[str, str]:
    year, month = (int(p) for p in period.split("-"))
    last = (
        31
        if month in (1, 3, 5, 7, 8, 10, 12)
        else 30
        if month != 2
        else 29
        if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)
        else 28
    )
    return f"{period}-01", f"{period}-{last:02d}"


class ReportComparisonUseCase:
    def __init__(self, gateway: ApiDelpiSettlementsGateway | None = None):
        self._gateway = gateway or ApiDelpiSettlementsGateway()

    # ----------------------------------------------------------
    # entry point
    # ----------------------------------------------------------

    def execute(
        self, body: dict[str, Any], *, access_token: str
    ) -> dict[str, Any]:
        (
            kind,
            requested_measure,
            grain,
            baseline,
            subjects,
            diff_page,
            diff_size,
        ) = self._validate(body)

        resolved = [
            self._resolve_subject(idx, s, access_token=access_token)
            for idx, s in enumerate(subjects)
        ]

        # measure resolution — request measure wins, else the report's
        # canonical default (cross-report comparisons can't share ids).
        for s in resolved:
            cap = s.get("capability")
            if cap is None:
                continue
            s["measure"] = (
                requested_measure
                if requested_measure
                else cap.default_measure
            )

        missing = [
            {
                "index": s["index"],
                "status": s["status"],
                "code": s.get("errorCode"),
                "message": s.get("errorMessage"),
            }
            for s in resolved
            if s["status"] != STATUS_OK
        ]

        ok_subjects = [s for s in resolved if s["status"] == STATUS_OK]

        document_result: dict[str, Any] | None = None
        if kind == "DOCUMENT":
            document_result = self._document_comparison(
                resolved, access_token=access_token
            )
            missing.extend(document_result.get("missing") or [])

        # pairwise verdicts: {(i,j): verdict} for i<j — same-report
        # pairs get the same-report verdict once.
        pair_verdicts, unsupported_measure_idx = self._classify(
            resolved, ok_subjects
        )
        grain_unsupported = grain != "total" and bool(
            ok_subjects
        ) and any(
            grain not in s["capability"].grains
            or s.get("measure") not in s["capability"].grains[grain].value_fields
            for s in ok_subjects
        )

        # effective baseline — a failed/denied baseline subject can
        # never anchor diffs; the shift is declared in the response.
        ok_indices = {s["index"] for s in ok_subjects}
        effective_baseline = (
            baseline
            if baseline in ok_indices
            else (ok_subjects[0]["index"] if ok_subjects else baseline)
        )
        if effective_baseline != baseline:
            missing.append(
                {
                    "index": baseline,
                    "status": "baseline_shifted",
                    "code": "baseline_subject_unavailable",
                    "message": (
                        f"baselineIndex {baseline} indisponível — "
                        f"deltas recalculados sobre o sujeito "
                        f"{effective_baseline}."
                    ),
                }
            )

        diffs, total_diff_count, delta_pairs = self._build_diffs(
            resolved,
            pair_verdicts=pair_verdicts,
            unsupported_measure_idx=unsupported_measure_idx,
            grain=grain if not grain_unsupported else "total",
            grain_unsupported=grain_unsupported,
            baseline=effective_baseline,
            diff_page=diff_page,
            diff_page_size=diff_size,
            kind=kind,
        )

        if grain_unsupported:
            missing.append(
                {
                    "index": None,
                    "status": "unsupported_grain",
                    "code": "grain_not_supported",
                    "message": (
                        f"O grão '{grain}' não possui agregação "
                        "completa em todos os sujeitos — apenas "
                        "totais foram comparados."
                    ),
                }
            )

        status, status_reason = self._overall_status(
            kind=kind,
            resolved=resolved,
            ok_subjects=ok_subjects,
            pair_verdicts=pair_verdicts,
            unsupported_measure_idx=unsupported_measure_idx,
            diffs=diffs,
            delta_pairs=delta_pairs,
            document_result=document_result,
        )

        result = {
            "report": "report-comparison",
            "comparisonKind": kind,
            "status": status,
            "statusReason": status_reason,
            "measure": requested_measure,
            "grain": "total" if grain_unsupported else grain,
            "requestedGrain": grain,
            "baselineIndex": baseline,
            "effectiveBaselineIndex": effective_baseline,
            "subjects": [self._subject_view(s) for s in resolved],
            "compatibility": [
                {
                    "between": list(pair),
                    "classification": v.classification,
                    "reason": v.reason,
                    "explanation": v.explanation,
                    "evidenceRefs": list(v.evidence_refs),
                    "deltaSemantics": v.delta_semantics,
                }
                for pair, v in sorted(pair_verdicts.items())
            ],
            "measureNotes": [
                {
                    "index": idx,
                    "code": "measure_not_supported",
                    "message": (
                        "A medida solicitada não faz parte do "
                        "contrato deste sujeito."
                    ),
                }
                for idx in sorted(unsupported_measure_idx)
            ],
            "diffs": diffs,
            "diffCount": total_diff_count,
            "diffTruncated": total_diff_count > len(diffs),
            "documentAnalysis": document_result,
            "normalizations": self._normalizations(
                kind, bool(delta_pairs)
            ),
            "missingData": missing,
            "limits": {
                "subjects": {"min": MIN_SUBJECTS, "max": MAX_SUBJECTS},
                "diffsMax": MAX_DIFFS,
                "diffPage": diff_page,
                "diffPageSize": diff_size,
                "subjectTimeoutSeconds": SUBJECT_TIMEOUT_SECONDS,
                "documentItemsPerSubjectMax": (
                    ITEM_PAGE_SIZE * ITEM_MAX_PAGES
                ),
            },
            "security": {
                "authorization": (
                    "per-subject governed contract — denied subjects "
                    "never contribute values or existence"
                ),
                "subjectsAuthorized": len(ok_subjects),
                "subjectsDenied": sum(
                    1
                    for s in resolved
                    if s["status"] == STATUS_DENIED
                ),
            },
            "provenance": {
                "owner": "controllership-finance-api",
                "engine": "report-comparison-v1",
                "contracts": sorted(
                    {
                        s["capability"].endpoint
                        for s in resolved
                        if s.get("capability")
                    }
                ),
                "officialParity": "PENDING",
                "note": (
                    "Comparação operacional — não infere paridade "
                    "oficial dos relatórios envolvidos."
                ),
            },
        }
        digest = hashlib.sha256(
            json.dumps(result, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        result["audit"] = {
            "event": "COMPARISON_PERFORMED",
            "comparisonId": digest,
        }
        logger.info(
            "comparison_performed kind=%s status=%s subjects=%s "
            "sha=%s",
            kind,
            status,
            len(resolved),
            digest,
        )
        return result

    # ----------------------------------------------------------
    # validation
    # ----------------------------------------------------------

    def _validate(self, body: dict[str, Any]):
        if not isinstance(body, dict):
            raise ComparisonValidationError("Body inválido.")
        kind = str(body.get("comparisonKind") or "").upper()
        if kind not in COMPARISON_KINDS:
            raise ComparisonValidationError(
                "comparisonKind inválido — use "
                + "|".join(sorted(COMPARISON_KINDS))
                + "."
            )
        raw_subjects = body.get("subjects")
        if not isinstance(raw_subjects, list):
            raise ComparisonValidationError(
                "subjects deve ser uma lista de 2 a 6 sujeitos."
            )
        if not (MIN_SUBJECTS <= len(raw_subjects) <= MAX_SUBJECTS):
            raise ComparisonValidationError(
                f"subjects deve conter entre {MIN_SUBJECTS} e "
                f"{MAX_SUBJECTS} sujeitos."
            )
        measure = body.get("measure") or None
        if measure is not None and not isinstance(measure, str):
            raise ComparisonValidationError(
                "measure deve ser uma string."
            )
        grain = body.get("grain") or "total"
        baseline = body.get("baselineIndex")
        if baseline is None:
            baseline = 0
        if not isinstance(baseline, int) or isinstance(
            baseline, bool
        ) or not (0 <= baseline < len(raw_subjects)):
            raise ComparisonValidationError(
                "baselineIndex deve referenciar um sujeito válido."
            )
        try:
            diff_page = int(body.get("diffPage") or 1)
            diff_size = int(body.get("diffPageSize") or 100)
        except (TypeError, ValueError):
            raise ComparisonValidationError(
                "diffPage/diffPageSize devem ser inteiros."
            )
        if diff_page < 1 or diff_size < 1:
            raise ComparisonValidationError(
                "diffPage/diffPageSize devem ser positivos."
            )
        if diff_size > MAX_DIFFS:
            raise ComparisonValidationError(
                f"diffPageSize máximo: {MAX_DIFFS}."
            )

        subjects: list[dict[str, Any]] = []
        for i, raw in enumerate(raw_subjects):
            if not isinstance(raw, dict):
                raise ComparisonValidationError(
                    f"subjects[{i}] deve ser um objeto."
                )
            rid = str(raw.get("reportId") or "").strip().upper()
            if not rid:
                raise ComparisonValidationError(
                    f"subjects[{i}].reportId é obrigatório."
                )
            period = raw.get("period")
            if period is not None and not _PERIOD_RE.match(
                str(period)
            ):
                raise ComparisonValidationError(
                    f"subjects[{i}].period deve ser YYYY-MM."
                )
            filters = raw.get("filters") or {}
            if not isinstance(filters, dict):
                raise ComparisonValidationError(
                    f"subjects[{i}].filters deve ser um objeto."
                )
            subjects.append(
                {
                    "index": i,
                    "reportId": rid,
                    "period": period,
                    "branch": raw.get("branch"),
                    "filters": dict(filters),
                }
            )

        if kind in ("PERIOD", "BRANCH", "TREND"):
            rids = {s["reportId"] for s in subjects}
            if len(rids) != 1:
                raise ComparisonValidationError(
                    f"{kind} exige o mesmo reportId em todos os "
                    "sujeitos — use REPORT para relatórios "
                    "distintos."
                )
            if not measure:
                raise ComparisonValidationError(
                    "measure é obrigatória neste tipo de comparação."
                )
            if kind == "PERIOD":
                contexts = {
                    (s["period"], s["branch"], s["reportId"])
                    for s in subjects
                }
                periods = {s["period"] for s in subjects}
                if len(periods) < 2 or len(contexts) != len(subjects):
                    raise ComparisonValidationError(
                        "PERIOD exige competências distintas em "
                        "contexto idêntico.",
                        code="duplicate_subject",
                    )
            if kind == "BRANCH":
                branches = {s["branch"] for s in subjects}
                if len(branches) < 2:
                    raise ComparisonValidationError(
                        "BRANCH exige ao menos duas filiais "
                        "distintas."
                    )
        return (
            kind,
            measure,
            grain,
            baseline,
            subjects,
            diff_page,
            diff_size,
        )

    # ----------------------------------------------------------
    # subject resolution — governed fetch, fail-closed
    # ----------------------------------------------------------

    def _resolve_subject(
        self, idx: int, subject: dict, *, access_token: str
    ) -> dict:
        rid = subject["reportId"]
        cap = catalog_mod.REPORT_CATALOG.get(rid)
        out = {
            "index": idx,
            "reportId": rid,
            "period": subject.get("period"),
            "branch": subject.get("branch"),
            "filters": subject.get("filters") or {},
            "capability": cap,
            "status": STATUS_OK,
            "errorCode": None,
            "errorMessage": None,
            "data": None,
            "provenance": None,
        }
        if cap is None:
            reason = catalog_mod.UNIMPLEMENTED_REPORTS.get(rid)
            out["status"] = STATUS_UNSUPPORTED
            out["errorCode"] = (
                "report_not_implemented" if reason else "unknown_report"
            )
            out["errorMessage"] = reason or (
                "Relatório sem contrato governado implementado."
            )
            return out

        bad_filters = sorted(
            set(out["filters"]) - set(cap.allowed_filters)
        )
        if bad_filters:
            out["status"] = STATUS_UNSUPPORTED
            out["errorCode"] = "unsupported_filter"
            out["errorMessage"] = (
                f"Filtros não suportados para {rid}: {bad_filters}."
            )
            return out

        if not subject.get("period"):
            out["status"] = STATUS_UNSUPPORTED
            out["errorCode"] = "period_required"
            out["errorMessage"] = "period (YYYY-MM) é obrigatório."
            return out

        params: dict[str, Any] = {}
        if cap.endpoint in _ITEM_ENDPOINTS:
            params["page"] = 1
            params["page_size"] = 1

        if rid in ("R01", "R02"):
            start, end = _period_window(str(subject["period"]))
            params["start_date"] = start
            params["end_date"] = end
            declared_side = cap.extra_params.get("side")
            asked_side = out["filters"].get("side")
            if asked_side and asked_side != declared_side:
                out["status"] = STATUS_UNSUPPORTED
                out["errorCode"] = "conflicting_side"
                out["errorMessage"] = (
                    f"side='{asked_side}' conflita com o relatório "
                    f"{rid} ({declared_side})."
                )
                return out
            params["side"] = declared_side
        else:
            params["period"] = subject["period"]
            params["branch"] = subject.get("branch") or "all"

        for key, mapped in cap.extra_params.items():
            params.setdefault(key, mapped)
        for key, value in out["filters"].items():
            if key != "side":
                params[key] = value

        try:
            body = self._gateway.get(
                cap.endpoint,
                access_token=access_token,
                params=params,
                timeout_seconds=SUBJECT_TIMEOUT_SECONDS,
            )
        except DelpiApiGatewayError as exc:
            if exc.status_code in (401, 403):
                # Fail-closed: the denied subject contributes no data
                # and no existence detail beyond its own request echo.
                out["status"] = STATUS_DENIED
                out["errorCode"] = exc.error_code or "subject_forbidden"
                out["errorMessage"] = (
                    "Sujeito fora do escopo autorizado."
                )
                return out
            out["status"] = STATUS_UNAVAILABLE
            out["errorCode"] = exc.error_code or "upstream_error"
            out["errorMessage"] = (
                "Origem do relatório indisponível para este sujeito."
            )
            return out

        if not isinstance(body, dict) or body.get("success") is not True:
            out["status"] = STATUS_UNAVAILABLE
            out["errorCode"] = "upstream_error"
            out["errorMessage"] = (
                "Resposta inesperada da origem do relatório."
            )
            return out

        data = body.get("data") or {}
        producer_status = str(data.get("status") or "").lower()
        if producer_status and producer_status != _PRODUCER_OK:
            out["status"] = (
                STATUS_EMPTY
                if producer_status in _PRODUCER_EMPTY
                else STATUS_UNAVAILABLE
            )
            out["errorCode"] = producer_status
            out["errorMessage"] = (
                "Sujeito sem dados para o contexto solicitado."
                if out["status"] == STATUS_EMPTY
                else "Origem do relatório indisponível/incompleta."
            )
            return out

        out["data"] = data
        prov = data.get("provenance") or {}
        out["provenance"] = {
            "engine": prov.get("engine"),
            "parityStatus": data.get("parityStatus"),
            "dataAsOf": data.get("dataAsOf"),
            "referenceDate": data.get("referenceDate"),
            "asOfConvention": prov.get("asOfConvention")
            or data.get("asOfConvention"),
            "source": data.get("source"),
        }
        return out

    def _subject_view(self, s: dict) -> dict:
        cap = s.get("capability")
        view = {
            "index": s["index"],
            "reportId": s["reportId"],
            "label": cap.label if cap else None,
            "period": s.get("period"),
            "branch": s.get("branch"),
            "filters": s.get("filters") or {},
            "measure": s.get("measure"),
            "status": s["status"],
            "errorCode": s.get("errorCode"),
            "errorMessage": s.get("errorMessage"),
            "provenance": s.get("provenance"),
        }
        if s["status"] == STATUS_OK and s.get("measure"):
            spec = cap.measures.get(s["measure"])
            if spec is not None:
                value = self._measure_value(s, s["measure"])
                view["measureValue"] = (
                    None if value is None else str(value)
                )
                view["measureUnit"] = spec.unit
        return view

    # ----------------------------------------------------------
    # compatibility — pairwise verdicts + measure support
    # ----------------------------------------------------------

    def _classify(
        self,
        resolved: list[dict],
        ok_subjects: list[dict],
    ) -> tuple[dict[tuple[int, int], Any], set[int]]:
        pair_verdicts: dict[tuple[int, int], Any] = {}
        unsupported_measure_idx: set[int] = set()

        for s in ok_subjects:
            measure = s.get("measure")
            if measure and measure not in s["capability"].measures:
                unsupported_measure_idx.add(s["index"])

        for i in range(len(ok_subjects)):
            for j in range(i + 1, len(ok_subjects)):
                a, b = ok_subjects[i], ok_subjects[j]
                verdict = compat_mod.classify_pair(
                    a["reportId"],
                    b["reportId"],
                    subject_filters_a=a["filters"],
                    subject_filters_b=b["filters"],
                )
                pair_verdicts[(a["index"], b["index"])] = verdict
        return pair_verdicts, unsupported_measure_idx

    def _pair_verdict(
        self,
        pair_verdicts: dict[tuple[int, int], Any],
        idx_a: int,
        idx_b: int,
    ):
        if idx_a == idx_b:
            return None
        key = (min(idx_a, idx_b), max(idx_a, idx_b))
        return pair_verdicts.get(key)

    # ----------------------------------------------------------
    # measure extraction + diffs (authorized normalizations only)
    # ----------------------------------------------------------

    def _measure_value(self, s: dict, measure: str) -> Decimal | None:
        cap = s["capability"]
        spec = cap.measures.get(measure)
        if spec is None:
            return None
        data = s["data"] or {}
        if spec.groups_sum is not None:
            groups = _dig(data, "groups") or []
            total = Decimal("0")
            found = False
            for g in groups:
                if not isinstance(g, dict):
                    continue
                value = _dec(g.get(spec.groups_sum))
                if value is not None:
                    total += value
                    found = True
            return total if found else None
        if spec.path:
            return _dec(_dig(data, spec.path))
        return None

    def _grain_map(
        self, s: dict, measure: str, grain: str
    ) -> dict[str, Decimal | None] | None:
        """Complete producer-side breakdown for the grain — or None
        when the producer offers no complete aggregation."""
        cap = s["capability"]
        spec = cap.grains.get(grain)
        if spec is None:
            return None
        value_field = spec.value_fields.get(measure)
        if value_field is None:
            return None  # grain exists but not for this measure
        rows = _dig(s["data"] or {}, spec.list_path) or []
        out: dict[str, Decimal | None] = {}
        for row in rows:
            if not isinstance(row, dict):
                continue
            key = row.get(spec.key_field)
            key = str(key).strip() if key is not None else "(vazio)"
            out[key] = _dec(row.get(value_field))
        return out

    def _build_diffs(
        self,
        resolved: list[dict],
        *,
        pair_verdicts: dict[tuple[int, int], Any],
        unsupported_measure_idx: set[int],
        grain: str,
        grain_unsupported: bool,
        baseline: int,
        diff_page: int,
        diff_page_size: int,
        kind: str,
    ) -> tuple[list[dict], int, bool]:
        if kind in ("DOCUMENT", "EXPLAIN") or grain_unsupported:
            return [], 0, False
        ok_subjects = [
            s
            for s in resolved
            if s["status"] == STATUS_OK
            and s["index"] not in unsupported_measure_idx
        ]
        if len(ok_subjects) < 2:
            return [], 0, False

        base_subject = next(
            (s for s in ok_subjects if s["index"] == baseline),
            None,
        )
        if base_subject is None:
            base_subject = ok_subjects[0]
            baseline = base_subject["index"]
        base_rid = base_subject["reportId"]

        # which targets allow a numeric delta against the baseline?
        eligible: dict[int, Any] = {}
        for s in ok_subjects:
            if s["index"] == baseline:
                continue
            if s["reportId"] == base_rid:
                verdict = compat_mod.classify_pair(
                    base_rid,
                    base_rid,
                    subject_filters_a=base_subject["filters"],
                    subject_filters_b=s["filters"],
                )
                if verdict.numeric_delta_allowed:
                    eligible[s["index"]] = verdict
            else:
                verdict = self._pair_verdict(
                    pair_verdicts, baseline, s["index"]
                )
                if verdict is not None and (
                    verdict.numeric_delta_allowed
                ):
                    eligible[s["index"]] = verdict
        if not eligible:
            return [], 0, False

        if grain == "total":
            keys = ["total"]
            # each subject resolves its own measure — cross-report
            # pairs can't share ids (outputValue × cpvTotal); the
            # deltaSemantics flags related-not-equivalent deltas.
            series = {
                s["index"]: {
                    "total": self._measure_value(
                        s, s.get("measure") or ""
                    )
                }
                for s in ok_subjects
            }
        else:
            measure = base_subject.get("measure") or ""
            maps = {}
            for s in ok_subjects:
                maps[s["index"]] = self._grain_map(s, measure, grain)
            if any(m is None for m in maps.values()):
                return [], 0, False
            keys = sorted(set().union(*[set(m) for m in maps.values()]))
            series = maps

        base_series = series.get(baseline) or {}
        all_diffs: list[dict] = []
        for key in keys:
            base_value = base_series.get(key)
            for target_idx, verdict in eligible.items():
                target_value = series.get(target_idx, {}).get(key)
                delta = (
                    None
                    if base_value is None or target_value is None
                    else target_value - base_value
                )
                delta_pct = None
                delta_pct_reason = None
                if delta is not None:
                    if base_value == 0:
                        delta_pct_reason = (
                            "zero_baseline — percentual indefinido "
                            "sobre denominador zero"
                        )
                    else:
                        delta_pct = delta / abs(
                            base_value
                        ) * Decimal("100")
                all_diffs.append(
                    {
                        "grainKey": key,
                        "base": {
                            "index": baseline,
                            "value": (
                                None
                                if base_value is None
                                else str(base_value)
                            ),
                        },
                        "target": {
                            "index": target_idx,
                            "value": (
                                None
                                if target_value is None
                                else str(target_value)
                            ),
                        },
                        "delta": (
                            None if delta is None else str(delta)
                        ),
                        "deltaPct": (
                            None
                            if delta_pct is None
                            else str(
                                delta_pct.quantize(Decimal("0.01"))
                            )
                        ),
                        "deltaPctReason": delta_pct_reason,
                        "deltaSemantics": (
                            verdict.delta_semantics or "direct"
                        ),
                        "missingSides": (
                            ["base"]
                            if base_value is None
                            else ["target"]
                            if target_value is None
                            else []
                        ),
                    }
                )
        total = len(all_diffs)
        start = (diff_page - 1) * diff_page_size
        return (
            all_diffs[start : start + diff_page_size],
            total,
            True,
        )

    # ----------------------------------------------------------
    # DOCUMENT kind — cross-report document identity
    # ----------------------------------------------------------

    def _document_comparison(
        self, subjects: list[dict], *, access_token: str
    ) -> dict[str, Any] | None:
        ok_subjects = [
            s
            for s in subjects
            if s["status"] == STATUS_OK
            and s["capability"].document_key_fields
        ]
        missing: list[dict] = []
        if len(ok_subjects) < 2:
            return {
                "status": "INSUFFICIENT_EVIDENCE",
                "explanation": (
                    "Comparação documental exige ao menos dois "
                    "sujeitos com chave documental confiável "
                    "(filial+documento+série)."
                ),
                "missing": missing,
            }

        doc_sets: dict[int, dict] = {}
        incomplete_items: dict[int, list] = {}
        truncated_flags: dict[int, bool] = {}
        for s in ok_subjects:
            docs, incomplete, truncated = (
                self._subject_document_index(
                    s, access_token=access_token
                )
            )
            doc_sets[s["index"]] = docs
            incomplete_items[s["index"]] = incomplete
            truncated_flags[s["index"]] = truncated
            if truncated:
                missing.append(
                    {
                        "index": s["index"],
                        "status": "truncated",
                        "code": "item_cap_reached",
                        "message": (
                            "Sujeito excedeu o limite de itens — "
                            "cobertura documental parcial."
                        ),
                    }
                )

        keys = list(doc_sets)
        matches: list[dict] = []
        for i, a in enumerate(keys):
            for b in keys[i + 1 :]:
                common = set(doc_sets[a]) & set(doc_sets[b])
                for key in sorted(common):
                    item_a = doc_sets[a][key]
                    item_b = doc_sets[b][key]
                    products_common = sorted(
                        set(item_a["products"])
                        & set(item_b["products"])
                    )
                    matches.append(
                        {
                            "document": key[1],
                            "series": key[2],
                            "branch": key[0],
                            "between": [a, b],
                            "items": [
                                item_a["count"], item_b["count"]
                            ],
                            "productsCommon": products_common,
                            "productsOnlyA": sorted(
                                set(item_a["products"])
                                - set(item_b["products"])
                            ),
                            "productsOnlyB": sorted(
                                set(item_b["products"])
                                - set(item_a["products"])
                            ),
                            "dateAxisNote": (
                                "Eixos de data podem diferir por "
                                "relatório (ex.: R10 usa D1_DTDIGIT; "
                                "R11 usa D2_EMISSAO) — a mesma NF "
                                "pode cair em competências distintas."
                            ),
                        }
                    )
        return {
            "status": "OK" if matches else "NO_MATCHES",
            "keyDefinition": (
                "branchCode+document+series — identidade confiável; "
                "número de documento isolado nunca é suficiente "
                "(doc 126 §7, tarefa §8.3)"
            ),
            "subjectTruncated": truncated_flags,
            "incompleteKeys": {
                idx: items
                for idx, items in incomplete_items.items()
                if items
            },
            "matchedDocuments": matches,
            "matchCount": len(matches),
            "missing": missing,
        }

    def _subject_document_index(
        self, s: dict, *, access_token: str
    ) -> tuple[dict, list, bool]:
        """Bounded item fetch → {(branch, doc, series): {...}}.

        Items lacking a complete key are collected separately — never
        silently matched by document number alone."""
        cap = s["capability"]
        params: dict[str, Any] = {
            "period": s.get("period"),
            "branch": s.get("branch") or "all",
            "page_size": ITEM_PAGE_SIZE,
        }
        for key, mapped in cap.extra_params.items():
            params.setdefault(key, mapped)
        params.update(s.get("filters") or {})
        params.pop("view", None)  # document cross covers all views

        index: dict[tuple, dict] = {}
        incomplete: list[dict] = []
        truncated = False
        for page in range(1, ITEM_MAX_PAGES + 1):
            params["page"] = page
            try:
                body = self._gateway.get(
                    cap.endpoint,
                    access_token=access_token,
                    params=params,
                    timeout_seconds=SUBJECT_TIMEOUT_SECONDS,
                )
            except DelpiApiGatewayError:
                break
            if (
                not isinstance(body, dict)
                or body.get("success") is not True
            ):
                break
            data = body.get("data") or {}
            items = data.get("items") or []
            for item in items:
                if not isinstance(item, dict):
                    continue
                doc = str(item.get("document") or "").strip()
                series = str(item.get("series") or "").strip()
                branch = str(item.get("branchCode") or "").strip()
                if not doc or not series or not branch:
                    incomplete.append(
                        {
                            "lineId": item.get("lineId"),
                            "document": doc or None,
                            "series": series or None,
                            "branch": branch or None,
                        }
                    )
                    continue
                entry = index.setdefault(
                    (branch, doc, series),
                    {"products": set(), "count": 0},
                )
                entry["count"] += 1
                if item.get("productCode"):
                    entry["products"].add(
                        str(item["productCode"]).strip()
                    )
            total_items = int(
                (data.get("pagination") or {}).get("total_items")
                or 0
            )
            if page * ITEM_PAGE_SIZE >= total_items:
                break
            if page == ITEM_MAX_PAGES:
                truncated = True
        return index, incomplete[:50], truncated

    # ----------------------------------------------------------
    # overall status + normalizations
    # ----------------------------------------------------------

    def _overall_status(
        self,
        *,
        kind: str,
        resolved: list[dict],
        ok_subjects: list[dict],
        pair_verdicts: dict[tuple[int, int], Any],
        unsupported_measure_idx: set[int],
        diffs: list[dict],
        delta_pairs: bool,
        document_result: dict | None,
    ) -> tuple[str, str | None]:
        if len(ok_subjects) < 2:
            return (
                "INSUFFICIENT_EVIDENCE",
                "Menos de dois sujeitos autorizados/disponíveis — "
                "nenhuma comparação produzida.",
            )

        classes = {v.classification for v in pair_verdicts.values()}
        partial = len(ok_subjects) < len(resolved)

        if kind == "EXPLAIN":
            if compat_mod.NOT_COMPARABLE in classes:
                return "INCOMPATIBLE", None
            if compat_mod.INSUFFICIENT_EVIDENCE in classes:
                return "INSUFFICIENT_EVIDENCE", None
            if compat_mod.RELATED_REQUIRES_EXPLANATION in classes:
                return (
                    "DIFFERENT",
                    "Medidas relacionadas porém não equivalentes — "
                    "explicação nas entradas de compatibilidade.",
                )
            return (
                "EQUAL",
                "Medidas semanticamente equivalentes — "
                "comparação direta autorizada.",
            )

        if kind == "DOCUMENT":
            assert document_result is not None
            if partial:
                return "PARTIAL", (
                    "Um ou mais sujeitos indisponíveis — "
                    "cruzamento documental incompleto."
                )
            if document_result.get("status") == "OK":
                return "DIFFERENT", (
                    "Documentos correspondentes encontrados — "
                    "relação documental, não equivalência de "
                    "totais."
                )
            return "EQUAL", (
                "Nenhum documento em comum entre os sujeitos "
                "autorizados."
            )

        all_not_comparable = classes == {compat_mod.NOT_COMPARABLE}
        if all_not_comparable:
            return (
                "INCOMPATIBLE",
                "Nenhum par possui medida comum — delta "
                "financeiro indevido não é produzido.",
            )
        if compat_mod.NOT_COMPARABLE in classes or (
            compat_mod.INSUFFICIENT_EVIDENCE in classes
            and not delta_pairs
        ):
            return (
                "INSUFFICIENT_EVIDENCE",
                "Par não classificado/incompatível — "
                "explicação disponível, sem delta financeiro "
                "para os pares afetados.",
            )

        nonzero = any(
            d.get("delta") is not None
            and Decimal(str(d["delta"])) != 0
            for d in diffs
        )
        related_only = (
            not delta_pairs
            or classes <= {compat_mod.RELATED_REQUIRES_EXPLANATION}
        )
        if related_only and diffs:
            status = "PARTIAL" if partial else "DIFFERENT"
            return status, (
                "Medidas relacionadas porém não equivalentes — "
                "a diferença exibida não é divergência financeira "
                "comprovada."
            )
        if partial or (
            compat_mod.INSUFFICIENT_EVIDENCE in classes
        ) or unsupported_measure_idx:
            return "PARTIAL", (
                "Um ou mais sujeitos/pares indisponíveis ou "
                "não classificados — diferenças computadas "
                "apenas onde a compatibilidade autoriza."
            )
        return ("DIFFERENT" if nonzero else "EQUAL"), None

    def _normalizations(
        self, kind: str, deltas_computed: bool
    ) -> list[dict]:
        rules = [
            {
                "rule": "competence_aggregation",
                "applied": True,
                "detail": (
                    "Totais por competência/filial agregados pelo "
                    "produtor — nunca recomputados pelo motor."
                ),
            },
            {
                "rule": "absolute_delta",
                "applied": deltas_computed,
                "detail": (
                    "Diferença absoluta target−baseline apenas "
                    "quando a compatibilidade autoriza delta "
                    "numérico."
                ),
            },
            {
                "rule": "percentage_delta",
                "applied": deltas_computed,
                "detail": (
                    "Variação percentual somente sobre "
                    "denominador não nulo — 'zero_baseline' é "
                    "declarado, nunca inventado."
                ),
            },
        ]
        if kind == "DOCUMENT":
            rules.append(
                {
                    "rule": "document_identity",
                    "applied": True,
                    "detail": (
                        "Correspondência por chave completa "
                        "(filial+documento+série); itens sem "
                        "chave completa são declarados em "
                        "incompleteKeys e não participam do "
                        "cruzamento."
                    ),
                }
            )
        return rules
