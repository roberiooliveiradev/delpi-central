"""Análise de entradas: criação idempotente, execução por filial, consulta e status."""

from __future__ import annotations

import hashlib
from dataclasses import replace
from datetime import date, datetime, timedelta
from typing import Protocol

from controllership_finance_app.application.entry_audit.errors import EntryAuditError, XmlSourceUnavailable
from controllership_finance_app.application.entry_audit.vocabulary import (
    book_word,
    field_code,
    stable_occurrence_key,
    yes_no,
)
from controllership_finance_app.domain.entry_audit.engine import audit
from controllership_finance_app.domain.entry_audit.models import (
    AuditConfig,
    FiscalBookLine,
    ProtheusHeader,
    ProtheusItem,
    TesRecord,
)
from controllership_finance_app.infrastructure.entry_audit.xml_reader import read_xml_payloads

ENGINE_VERSION = "entry-audit-t5"
DOCUMENT_TYPES = ("nfe", "cte")
BRANCHES = ("01", "02")
SPECIES = {"nfe": "SPED", "cte": "CTE"}
TYPE_LABELS = {"nfe": "NF-e", "cte": "CT-e"}


class ProtheusEntriesPort(Protocol):
    def documents(self, *, branch: str, received_from: date, received_to: date, species: list[str]) -> list[dict]: ...

    def documents_by_access_keys(self, *, branch: str, access_keys: list[str]) -> list[dict]: ...
    def items(self, *, branch: str, received_from: date, received_to: date, species: list[str]) -> list[dict]: ...
    def fiscal_book(self, *, branch: str, received_from: date, received_to: date, species: list[str]) -> list[dict]: ...
    def tes(self) -> list[dict]: ...
    def branches(self) -> list[dict]: ...


class FiscalXmlPort(Protocol):
    def download_by_key(self, *, branch: str, access_key: str, document_type: str) -> bytes | None: ...
    def list_issued(self, *, branch: str, document_type: str, issued_from: date, issued_to: date) -> list[str]: ...


class InvoicePostingLookupPort(Protocol):
    def find_open(self, *, branch: str, access_key: str, document_number: str, series: str, supplier_code: str) -> dict | None: ...


class EntryAuditService:
    def __init__(self, store, protheus: ProtheusEntriesPort, fiscal_xml: FiscalXmlPort, posting: InvoicePostingLookupPort, config: AuditConfig, lookback_days: int = 30) -> None:
        self._store = store
        self._protheus = protheus
        self._fiscal_xml = fiscal_xml
        self._posting = posting
        self._config = config
        self._lookback_days = lookback_days

    def create(self, *, date_from: date, date_to: date, document_types: list[str] | None, branches: list[str] | None, user_id: str, user_name: str, via: str) -> dict:
        types, branch_codes = _filters(document_types, branches)
        if via not in {"user", "clara"}:
            raise EntryAuditError("Origem do pedido inválida.", status_code=422, code="INVALID_VIA")
        if date_from > date_to:
            raise EntryAuditError("Período inválido.", status_code=422, code="INVALID_PERIOD")
        existing = self._store.find_open(date_from, date_to, types, branch_codes)
        if existing:
            return {"id": existing["id"], "status": existing["status"], "created": False}
        analysis = self._store.insert_analysis({
            "date_from": date_from,
            "date_to": date_to,
            "document_types": types,
            "branches": branch_codes,
            "config_snapshot": _snapshot(self._config, self._lookback_days),
            "status": "queued",
            "requested_by_user_id": user_id,
            "requested_by_name": _requested_name(user_name, via),
            "requested_via": via,
        })
        self._store.insert_runs(analysis["id"], branch_codes)
        return {"id": analysis["id"], "status": "queued", "created": True}

    def options(self) -> dict:
        branches = []
        for row in self._protheus.branches():
            if row.get("code") in BRANCHES:
                branches.append({"code": row.get("code"), "name": row.get("name") or "", "state": row.get("state") or "", "tax_id": row.get("tax_id") or ""})
        return {
            "branches": branches,
            "document_types": [
                {"code": code, "label": TYPE_LABELS[code], "species": SPECIES[code], "default": True}
                for code in DOCUMENT_TYPES
            ],
        }

    def list_analyses(self, *, date_from, date_to, branch, status, page, page_size) -> dict:
        rows, total = self._store.list_analyses(date_from=date_from, date_to=date_to, branch=branch, status=status, page=page, page_size=page_size)
        return {"items": [_public_analysis(row) for row in rows], "page": page, "page_size": page_size, "total": total}

    def get_analysis(self, analysis_id: str) -> dict:
        analysis = self._require(analysis_id)
        runs = self._store.runs_of(analysis_id)
        counts = {}
        for run in runs:
            if run["status"] in {"done", "partial"}:
                for key, value in (run.get("counts") or {}).items():
                    if isinstance(value, int):
                        counts[key] = counts.get(key, 0) + value
        return {
            "id": analysis["id"],
            "status": analysis["status"],
            "date_from": analysis["date_from"].isoformat(),
            "date_to": analysis["date_to"].isoformat(),
            "document_types": analysis["document_types"],
            "branches": analysis["branches"],
            "runs": [
                {
                    "branch": run["branch_code"],
                    "status": run["status"],
                    "stage": run["stage"],
                    "documents_read": run["documents_read"],
                    "xml_downloaded": run["xml_downloaded"],
                    "counts": {key: value for key, value in (run.get("counts") or {}).items() if isinstance(value, int)},
                    "error": run["error_message"],
                }
                for run in runs
            ],
            "counts": counts,
            "config": analysis["config_snapshot"],
        }

    def rerun(self, analysis_id: str, branches: list[str] | None, *, user_id: str = "", user_name: str = "", via: str = "user") -> dict:
        analysis = self._require(analysis_id)
        selected = branches or list(analysis["branches"])
        unknown = [code for code in selected if code not in analysis["branches"]]
        if unknown or not selected:
            raise EntryAuditError("Filial fora da análise.", status_code=422, code="INVALID_BRANCH")
        if via not in {"user", "clara"}:
            raise EntryAuditError("Origem do pedido inválida.", status_code=422, code="INVALID_VIA")
        runs = self._store.runs_for_branches(analysis_id, selected)
        if any(run["status"] in {"queued", "running"} for run in runs):
            raise EntryAuditError("A filial pedida já está na fila.", status_code=409, code="RUN_IN_PROGRESS")
        self._store.note_requester(analysis_id, user_id=user_id, user_name=_requested_name(user_name, via), via=via)
        for run in runs:
            self._store.clear_output(run["id"])
            self._store.queue_run(run["id"])
        return {"id": analysis_id, "status": "queued", "branches": selected}

    def recover_orphans(self) -> int:
        return self._store.requeue_running()

    def claim_and_execute(self) -> bool:
        claimed = self._store.claim_next_queued()
        if claimed is None:
            return False
        self.execute(claimed["id"])
        return True

    def execute(self, run_id: str) -> None:
        run = self._store.get_run(run_id)
        analysis = self._require(run["analysis_id"])
        config = replace(_config_from(analysis["config_snapshot"]), period_end=analysis["date_to"])
        species = [SPECIES[code] for code in analysis["document_types"]]
        try:
            self._store.mark_run(run_id, stage="reading_protheus")
            headers = self._protheus.documents(branch=run["branch_code"], received_from=analysis["date_from"], received_to=analysis["date_to"], species=species)
            items = self._protheus.items(branch=run["branch_code"], received_from=analysis["date_from"], received_to=analysis["date_to"], species=species)
            book = self._protheus.fiscal_book(branch=run["branch_code"], received_from=analysis["date_from"], received_to=analysis["date_to"], species=species)
            tes_rows = self._protheus.tes()
            branch_row = next((row for row in self._protheus.branches() if row.get("code") == run["branch_code"]), {})
            self._store.mark_run(run_id, stage="reading_xml", documents_read=len(headers))
            payloads, downloaded, unavailable = self._xml_payloads(analysis, run["branch_code"], headers)
            blocked_keys = {str(row.get("access_key") or "") for row in unavailable if row.get("access_key")}
            blocked_docs = {_composite(row) for row in headers if str(row.get("access_key") or "") in blocked_keys}
            auditable_headers = [row for row in headers if _composite(row) not in blocked_docs]
            auditable_items = [row for row in items if _composite(row) not in blocked_docs]
            invoices, ctes, _ignored = read_xml_payloads(payloads)
            self._store.mark_run(run_id, stage="auditing", xml_downloaded=downloaded)
            result = audit(
                branch=run["branch_code"],
                company_tax_id=str(branch_row.get("tax_id") or ""),
                company_state=str(branch_row.get("state") or ""),
                headers=[_header(row) for row in auditable_headers],
                items=[_item(row) for row in auditable_items],
                tes_records=[_tes(row) for row in tes_rows],
                invoices=invoices,
                ctes=ctes,
                config=config,
                fiscal_book=[_book(row) for row in book if _composite(row) not in blocked_docs],
            )
            posted_outside = self._posted_outside(run["branch_code"], result) if config.improvements_enabled else []
            lnf = self._lnf_matches(result, run["branch_code"], auditable_headers)
            output = _persistable(
                analysis["id"], run_id, run["branch_code"], result, auditable_headers, auditable_items, tes_rows, lnf, unavailable,
                xml_by_key={**invoices, **ctes},
                posted_outside=posted_outside,
            )
            self._store.mark_run(run_id, stage="saving")
            self._store.replace_output(run_id, **output)
            digest = hashlib.sha256(",".join(sorted(row.get("access_key") or "" for row in headers)).encode()).hexdigest()
            counts = dict(result.summary)
            counts["unmatched"] = len(result.unmatched)
            counts["posted_outside_period"] = len(posted_outside)
            counts["occurrences"] = len(result.occurrences)
            counts["excluded"] = len(result.excluded)
            for key, value in result.not_reported.items():
                counts[f"not_reported:{key}"] = value
            counts["xml_unavailable_count"] = len(unavailable)
            status = "partial" if unavailable else "done"
            self._store.mark_run(
                run_id,
                status=status,
                stage=status,
                counts=counts,
                engine_version=ENGINE_VERSION,
                sources_hash=digest,
                error_message="XML_UNAVAILABLE" if unavailable else "",
            )
        except XmlSourceUnavailable as exc:
            code = "XML_LISTING_UNAVAILABLE" if exc.scope == "listing" else "XML_UNAVAILABLE"
            self._store.mark_run(run_id, status="failed", stage="failed", error_message=code)
        except EntryAuditError:
            raise
        except Exception as exc:
            self._store.mark_run(run_id, status="failed", stage="failed", error_message=type(exc).__name__)

    def summary(self, analysis_id: str, filters: dict) -> dict:
        analysis, ready = self._ready(analysis_id)
        occurrences = _dedupe(self._filtered("occurrences", analysis_id, filters))
        document_rows = self._filtered("documents", analysis_id, filters)
        documents = [row for row in document_rows if row.get("situation") not in {"xml_unavailable", "posted_outside_period"}]
        unavailable = [row for row in document_rows if row.get("situation") == "xml_unavailable"]
        outside = [row for row in document_rows if row.get("situation") == "posted_outside_period"]
        unmatched = self._filtered("unmatched", analysis_id, filters)
        divergent_keys = {_document_identity(row) for row in occurrences}
        clean = sum(1 for row in documents if _document_identity(row) not in divergent_keys)
        explained = sum(1 for row in unmatched if _explained(row))
        current = {
            "documents": len(documents),
            "occurrences": len(occurrences),
            "high": sum(1 for row in occurrences if row["severity"] == "Alta"),
            "pending": sum(1 for row in occurrences if _status(self._store, row) == "pending"),
            "xml_unavailable": len(unavailable),
        }
        return {
            "kpis": current,
            "previous": self._previous_kpis(analysis, filters),
            "conformity": {
                "clean": clean,
                "divergent": len(documents) - clean,
                "unmatched_open": len(unmatched) - explained,
                "unmatched_explained": explained,
                "posted_outside_period": {
                    "count": len(outside),
                    "received_dates": [str(row.get("received_date") or "") for row in outside if row.get("received_date")],
                },
            },
            "branches_unavailable": ready,
        }

    def daily(self, analysis_id: str, filters: dict) -> dict:
        analysis, ready = self._ready(analysis_id)
        return {"series": _by_day(self._filtered("occurrences", analysis_id, filters)), "previous": [], "branches_unavailable": ready, "period": [analysis["date_from"].isoformat(), analysis["date_to"].isoformat()]}

    def breakdowns(self, analysis_id: str, filters: dict) -> dict:
        _analysis, ready = self._ready(analysis_id)
        rows = self._filtered("occurrences", analysis_id, filters)
        return {
            "by_severity": _count(rows, "severity"),
            "by_theme": _count(rows, "theme"),
            "suppliers": _count(rows, "supplier_name")[:10],
            "tes": _count(rows, "tes")[:10],
            "branches_unavailable": ready,
        }

    def facets(self, analysis_id: str, filters: dict) -> dict:
        _analysis, ready = self._ready(analysis_id)
        rows = self._filtered("occurrences", analysis_id, filters)
        return {
            "suppliers": _count(rows, "supplier_name"),
            "themes": _count(rows, "theme"),
            "tes": _count(rows, "tes"),
            "severities": _count(rows, "severity"),
            "branches_unavailable": ready,
        }

    def trend(self, *, branch, date_from, date_to) -> dict:
        rows, _total = self._store.list_analyses(date_from=date_from, date_to=date_to, branch=branch, status="done", page=1, page_size=200)
        points = []
        for analysis in rows:
            occurrences = self._store.rows("occurrences", analysis["id"])
            if branch:
                occurrences = [row for row in occurrences if row["branch"] == branch]
            points.append({
                "month": analysis["date_from"].strftime("%Y-%m"),
                "analysis_id": analysis["id"],
                "pending": sum(1 for row in occurrences if _status(self._store, row) == "pending"),
                "high": sum(1 for row in occurrences if row["severity"] == "Alta"),
            })
        return {"points": points}

    def occurrences(self, analysis_id: str, filters: dict, *, page: int, page_size: int, sort: str) -> dict:
        _analysis, ready = self._ready(analysis_id)
        rows = self._filtered("occurrences", analysis_id, filters)
        rows.sort(key=lambda row: _sort_key(row, sort))
        start = (page - 1) * page_size
        page_rows = [_public_occurrence(row, self._store.status_of(row["stable_key"])) for row in rows[start : start + page_size]]
        return {"items": page_rows, "page": page, "page_size": page_size, "total": len(rows), "branches_unavailable": ready}

    def occurrence(self, analysis_id: str, stable_key: str) -> dict:
        self._ready(analysis_id)
        found = next((row for row in self._store.rows("occurrences", analysis_id) if row["stable_key"] == stable_key), None)
        if found is None:
            found = next((row for row in self._store.rows("unmatched", analysis_id) if row["stable_key"] == stable_key), None)
        if found is None:
            raise EntryAuditError("Ocorrência não encontrada.", status_code=404, code="NOT_FOUND")
        status = self._store.status_of(stable_key)
        detail = _public_occurrence(found, status)
        detail["history"] = _history(status)
        detail["links"] = _links(found)
        return detail

    def documents(self, analysis_id: str, filters: dict, *, page: int, page_size: int) -> dict:
        return self._page("documents", analysis_id, filters, page, page_size)

    def unmatched_documents(self, analysis_id: str, filters: dict, *, page: int, page_size: int) -> dict:
        return self._page("unmatched", analysis_id, filters, page, page_size)

    def ctes(self, analysis_id: str, filters: dict, *, page: int, page_size: int) -> dict:
        return self._page("ctes", analysis_id, filters, page, page_size)

    def tes_used(self, analysis_id: str, filters: dict) -> dict:
        _analysis, ready = self._ready(analysis_id)
        rows = self._filtered("tes", analysis_id, filters)
        return {"items": rows, "branches_unavailable": ready}

    def occurrence_state(self, stable_key: str) -> dict | None:
        if not self._store.has_stable_key(stable_key):
            return None
        current = self._store.status_of(stable_key) or {}
        return {"occurrence": {"status": current.get("status") or "pending", "stable_key": stable_key}}

    def resolve(self, stable_key: str, *, kind: str, user_id: str, user_name: str) -> dict:
        return self._set_status(stable_key, kind=kind, status="resolved", user_id=user_id, user_name=user_name)

    def reopen(self, stable_key: str, *, kind: str, user_id: str, user_name: str) -> dict:
        return self._set_status(stable_key, kind=kind, status="pending", user_id=user_id, user_name=user_name)

    def export_rows(self, analysis_id: str) -> dict:
        analysis, ready = self._ready(analysis_id)
        return {
            "analysis": analysis,
            "occurrences": _dedupe(self._store.rows("occurrences", analysis_id)),
            "documents": self._store.rows("documents", analysis_id),
            "unmatched": _dedupe(self._store.rows("unmatched", analysis_id)),
            "ctes": self._store.rows("ctes", analysis_id),
            "tes": self._store.rows("tes", analysis_id),
            "branches_unavailable": ready,
        }

    def _page(self, kind: str, analysis_id: str, filters: dict, page: int, page_size: int) -> dict:
        _analysis, ready = self._ready(analysis_id)
        rows = self._filtered(kind, analysis_id, filters)
        start = (page - 1) * page_size
        return {"items": rows[start : start + page_size], "page": page, "page_size": page_size, "total": len(rows), "branches_unavailable": ready}

    def _set_status(self, stable_key: str, *, kind: str, status: str, user_id: str, user_name: str) -> dict:
        if not self._store.has_stable_key(stable_key):
            raise EntryAuditError("Ocorrência não encontrada.", status_code=404, code="NOT_FOUND")
        current = self._store.upsert_status(stable_key, kind=kind, status=status, user_id=user_id, user_name=user_name)
        return {"stable_key": stable_key, "kind": kind, "status": current["status"], "status_id": str(current.get("id") or "")}

    def _require(self, analysis_id: str) -> dict:
        analysis = self._store.get_analysis(analysis_id)
        if analysis is None:
            raise EntryAuditError("Análise não encontrada.", status_code=404, code="NOT_FOUND")
        return analysis

    def _ready(self, analysis_id: str) -> tuple[dict, list[str]]:
        analysis = self._require(analysis_id)
        runs = self._store.runs_of(analysis_id)
        if not any(run["status"] in {"done", "partial"} for run in runs):
            raise EntryAuditError("A análise ainda não tem filial concluída.", status_code=409, code="ANALYSIS_NOT_READY")
        unavailable = [run["branch_code"] for run in runs if run["status"] == "failed"]
        return analysis, unavailable

    def _filtered(self, kind: str, analysis_id: str, filters: dict) -> list[dict]:
        rows = _dedupe(self._store.rows(kind, analysis_id))
        failed = {run["branch_code"] for run in self._store.runs_of(analysis_id) if run["status"] == "failed"}
        rows = [row for row in rows if row.get("branch") not in failed]
        for name in ("branch", "severity", "theme", "supplier", "tes", "document_type", "day", "status"):
            value = filters.get(name)
            if not value:
                continue
            if name == "supplier":
                rows = [row for row in rows if value.lower() in str(row.get("supplier_name") or "").lower()]
            elif name == "day":
                rows = [row for row in rows if str(row.get("received_date") or row.get("issue_date") or "") == value]
            elif name == "status":
                rows = [row for row in rows if _status(self._store, row) == value]
            elif name == "document_type":
                rows = [row for row in rows if row.get("document_type") == value]
            else:
                column = {"branch": "branch", "severity": "severity", "theme": "theme", "tes": "tes"}[name]
                rows = [row for row in rows if str(row.get(column) or "") == value]
        query = (filters.get("q") or "").lower()
        if query:
            rows = [row for row in rows if query in " ".join(str(row.get(key) or "") for key in ("title", "document_number", "supplier_name", "reason")).lower()]
        return rows

    def _previous_kpis(self, analysis: dict, filters: dict) -> dict:
        span = (analysis["date_to"] - analysis["date_from"]).days + 1
        previous_to = analysis["date_from"] - timedelta(days=1)
        previous_from = previous_to - timedelta(days=span - 1)
        rows, _total = self._store.list_analyses(date_from=previous_from, date_to=previous_to, branch=None, status="done", page=1, page_size=20)
        if not rows:
            return {"documents": 0, "occurrences": 0, "high": 0, "pending": 0}
        previous = rows[0]
        occurrences = self._filtered("occurrences", previous["id"], filters)
        documents = self._filtered("documents", previous["id"], filters)
        return {
            "documents": len(documents),
            "occurrences": len(occurrences),
            "high": sum(1 for row in occurrences if row["severity"] == "Alta"),
            "pending": sum(1 for row in occurrences if _status(self._store, row) == "pending"),
        }

    def _xml_payloads(self, analysis: dict, branch: str, headers: list[dict]) -> tuple[list[bytes], int, list[dict]]:
        payloads: list[bytes] = []
        seen: set[str] = set()
        unavailable: list[dict] = []
        downloaded = 0
        for header in headers:
            key = str(header.get("access_key") or "").strip()
            if len(key) != 44:
                continue
            kind = "cte" if str(header.get("species") or "").upper() == "CTE" else "nfe"
            try:
                payload = self._fiscal_xml.download_by_key(branch=branch, access_key=key, document_type=kind)
            except XmlSourceUnavailable as exc:
                if exc.scope == "listing":
                    raise
                unavailable.append(header)
                seen.add(key)
                continue
            if payload:
                payloads.append(payload)
                seen.add(key)
                downloaded += 1
        issued_from = analysis["date_from"] - timedelta(days=_lookback(analysis))
        for document_type in analysis["document_types"]:
            for key in self._fiscal_xml.list_issued(branch=branch, document_type=document_type, issued_from=issued_from, issued_to=analysis["date_to"]):
                if key in seen:
                    continue
                try:
                    payload = self._fiscal_xml.download_by_key(branch=branch, access_key=key, document_type=document_type)
                except XmlSourceUnavailable as exc:
                    if exc.scope == "listing":
                        raise
                    unavailable.append({
                        "branch": branch,
                        "access_key": key,
                        "document_number": "",
                        "series": "",
                        "supplier_name": "",
                        "species": "CTE" if document_type == "cte" else "SPED",
                    })
                    seen.add(key)
                    continue
                if payload:
                    payloads.append(payload)
                    seen.add(key)
                    downloaded += 1
        return payloads, downloaded, unavailable

    def _posted_outside(self, branch: str, result) -> list[dict]:
        """D11: XML da folga que já está na SF1, em qualquer data, não é sem par."""
        keys: list[str] = []
        seen: set[str] = set()
        for row in result.unmatched:
            key = str(row.access_key or "")
            if row.side == "xml" and len(key) == 44 and key not in seen:
                seen.add(key)
                keys.append(key)
        if not keys:
            return []
        found = self._protheus.documents_by_access_keys(branch=branch, access_keys=keys)
        by_key = {str(row.get("access_key") or ""): row for row in found if row.get("access_key")}
        kept = []
        outside = []
        for row in result.unmatched:
            hit = by_key.get(str(row.access_key or ""))
            if hit is not None and row.side == "xml":
                outside.append(hit)
                continue
            kept.append(row)
        result.unmatched = kept
        return outside

    def _lnf_matches(self, result, branch: str, headers: list[dict]) -> dict:
        by_key = {str(row.get("access_key") or ""): row for row in headers if row.get("access_key")}
        found_by_key = {}
        for row in result.unmatched:
            if row.side != "xml":
                continue
            header = by_key.get(row.access_key, {})
            found = self._posting.find_open(
                branch=branch,
                access_key=row.access_key,
                document_number=row.document_number,
                series=str(getattr(row, "series", "") or header.get("series") or ""),
                supplier_code=str(header.get("supplier_code") or ""),
            )
            if found:
                found_by_key[row.access_key or row.document_number] = found
        return found_by_key


def _requested_name(user_name: str, via: str) -> str:
    if via == "clara":
        return f"CLARA em nome de {user_name}"
    return user_name


def _filters(document_types: list[str] | None, branches: list[str] | None) -> tuple[list[str], list[str]]:
    types = sorted(set(document_types or list(DOCUMENT_TYPES)))
    branch_codes = sorted(set(branches or list(BRANCHES)))
    if not types or any(code not in DOCUMENT_TYPES for code in types):
        raise EntryAuditError("Tipo de documento inválido.", status_code=422, code="INVALID_DOCUMENT_TYPE")
    if not branch_codes or any(code not in BRANCHES for code in branch_codes):
        raise EntryAuditError("Filial inválida.", status_code=422, code="INVALID_BRANCH")
    return types, branch_codes


def _snapshot(config: AuditConfig, lookback_days: int) -> dict:
    return {
        "presumed_credit_tes": config.presumed_credit_tes,
        "freight_cfop_suffix": config.freight_cfop_suffix,
        "xml_lookback_days": lookback_days,
        "unmatched_grace_days": config.unmatched_grace_days,
        "tolerance": config.tolerance,
    }


def _config_from(snapshot: dict) -> AuditConfig:
    return AuditConfig(
        presumed_credit_tes=str(snapshot.get("presumed_credit_tes") or "004"),
        freight_cfop_suffix=str(snapshot.get("freight_cfop_suffix") or "352"),
        tolerance=float(snapshot.get("tolerance") or 0.05),
        unmatched_grace_days=int(snapshot.get("unmatched_grace_days") or 3),
        improvements_enabled=True,
    )


def _lookback(analysis: dict) -> int:
    return int((analysis.get("config_snapshot") or {}).get("xml_lookback_days") or 30)


def _header(row: dict) -> ProtheusHeader:
    return ProtheusHeader(
        branch=str(row.get("branch") or ""),
        number=str(row.get("document_number") or ""),
        series=str(row.get("series") or ""),
        supplier_code=str(row.get("supplier_code") or ""),
        supplier_store=str(row.get("supplier_store") or ""),
        supplier_name=str(row.get("supplier_name") or ""),
        supplier_state=str(row.get("supplier_state") or ""),
        supplier_tax_id=str(row.get("supplier_tax_id") or ""),
        species=str(row.get("species") or ""),
        own_form=str(row.get("own_form") or ""),
        access_key=str(row.get("access_key") or ""),
        issue_date=_as_date(row.get("issue_date")),
        received_date=_as_date(row.get("received_date")),
        freight_amount=_num(row.get("freight_amount")),
        expense_amount=_num(row.get("expense_amount")),
        icms_base=_num(row.get("icms_base")),
        icms_amount=_num(row.get("icms_amount")),
        ipi_base=_num(row.get("ipi_base")),
        ipi_amount=_num(row.get("ipi_amount")),
        goods_amount=_num(row.get("goods_amount")),
        gross_amount=_num(row.get("gross_amount")),
        discount_amount=_num(row.get("discount_amount")),
        st_base=_num(row.get("st_base")),
        st_amount=_num(row.get("st_amount")),
        insurance_amount=_num(row.get("insurance_amount")),
    )


def _item(row: dict) -> ProtheusItem:
    return ProtheusItem(
        branch=str(row.get("branch") or ""),
        number=str(row.get("document_number") or ""),
        series=str(row.get("series") or ""),
        supplier_code=str(row.get("supplier_code") or ""),
        supplier_store=str(row.get("supplier_store") or ""),
        item=str(row.get("item") or ""),
        product_code=str(row.get("product_code") or ""),
        cfop=str(row.get("cfop") or ""),
        tax_situation=str(row.get("tax_situation") or ""),
        tes=str(row.get("tes") or ""),
        total_amount=_num(row.get("total_amount")),
        icms_base=_num(row.get("icms_base")),
        icms_rate=_num(row.get("icms_rate")),
        icms_amount=_num(row.get("icms_amount")),
        ipi_base=_num(row.get("ipi_base")),
        ipi_rate=_num(row.get("ipi_rate")),
        ipi_amount=_num(row.get("ipi_amount")),
        st_amount=_num(row.get("st_amount")),
    )


def _book(row: dict) -> FiscalBookLine:
    return FiscalBookLine(
        number=str(row.get("document_number") or ""),
        series=str(row.get("series") or ""),
        supplier_code=str(row.get("supplier_code") or ""),
        supplier_store=str(row.get("supplier_store") or ""),
        item=str(row.get("item") or ""),
        icms_amount=_num(row.get("icms_amount")),
        other_icms=_num(row.get("icms_other_amount")),
        exempt_icms=_num(row.get("icms_exempt_amount")),
        ipi_amount=_num(row.get("ipi_amount")),
        branch=str(row.get("branch") or ""),
        movement=str(row.get("movement_type") or "E"),
        cancelled=bool(str(row.get("cancelled_on") or "").strip()),
    )


def _tes(row: dict) -> TesRecord:
    return TesRecord(
        code=str(row.get("code") or ""),
        description=str(row.get("description") or ""),
        calculates_icms=yes_no(str(row.get("calculates_icms") or "")),
        credits_icms=yes_no(str(row.get("credits_icms") or "")),
        icms_book=book_word(str(row.get("icms_book") or "")),
        calculates_ipi=yes_no(str(row.get("calculates_ipi") or "")),
        credits_ipi=yes_no(str(row.get("credits_ipi") or "")),
        ipi_book=book_word(str(row.get("ipi_book") or "")),
        consumption_material=yes_no(str(row.get("consumption_material") or "")),
        tes_type=str(row.get("tes_type") or ""),
        fiscal_code=str(row.get("fiscal_code") or ""),
    )


def _as_date(value) -> date | None:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value or "").strip()
    if len(text) >= 10 and text[4] == "-":
        return date.fromisoformat(text[:10])
    if len(text) == 8 and text.isdigit():
        return date(int(text[0:4]), int(text[4:6]), int(text[6:8]))
    return None


def _num(value) -> float:
    if value is None or value == "":
        return 0.0
    return float(value)


def _composite(row: dict) -> tuple:
    return (
        str(row.get("branch") or row.get("branch_code") or ""),
        str(row.get("supplier_code") or ""),
        str(row.get("supplier_store") or ""),
        str(row.get("document_number") or ""),
        str(row.get("series") or ""),
    )


def _document_identity(row: dict) -> tuple:
    key = str(row.get("access_key") or "")
    if key:
        return ("key", key)
    return ("doc", *_composite(row))


def _dedupe(rows: list[dict]) -> list[dict]:
    seen: set[str] = set()
    unique = []
    for row in rows:
        key = str(row.get("stable_key") or "")
        if key:
            if key in seen:
                continue
            seen.add(key)
        unique.append(row)
    return unique


def _same_header(item: dict, header: dict) -> bool:
    return _composite(item) == _composite(header)


def _tes_codes(header: dict, items: list[dict], item_number: str) -> str:
    related = [item for item in items if _same_header(item, header)]
    if item_number:
        exact = [item for item in related if str(item.get("item") or "") == item_number]
        related = exact or related
    return ", ".join(sorted({str(item.get("tes") or "") for item in related if item.get("tes")}))


def _persistable(analysis_id: str, run_id: str, branch: str, result, headers: list[dict], items: list[dict], tes_rows: list[dict], lnf: dict | None = None, unavailable: list[dict] | None = None, xml_by_key: dict | None = None, posted_outside: list[dict] | None = None) -> dict:
    by_key = {str(row.get("access_key") or ""): row for row in headers if row.get("access_key")}
    xml_docs = xml_by_key or {}
    occurrence_rows = []
    for row in result.occurrences:
        header = by_key.get(row.access_key, {})
        xml = xml_docs.get(row.access_key)
        code = field_code(row.field)
        supplier_name = str(header.get("supplier_name") or "") or (getattr(xml, "issuer_name", "") if xml is not None else "")
        occurrence_rows.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "stable_key": stable_occurrence_key(branch=branch, access_key=row.access_key, rule_id=row.rule_id, field=row.field, item=row.item, number=row.document_number, series=str(header.get("series") or ""), supplier=str(header.get("supplier_code") or ""), store=str(header.get("supplier_store") or "")),
            "rule_id": row.rule_id,
            "severity": row.severity,
            "theme": row.rule_id.split(".", 1)[0],
            "title": row.title,
            "document_number": row.document_number,
            "series": str(header.get("series") or ""),
            "supplier_name": supplier_name,
            "supplier_code": str(header.get("supplier_code") or ""),
            "supplier_store": str(header.get("supplier_store") or ""),
            "item": row.item,
            "field": code,
            "field_label": row.field,
            "protheus_value": row.protheus_value,
            "xml_value": row.xml_value,
            "difference": _difference(row.protheus_value, row.xml_value),
            "tes": _tes_codes(header, items, row.item),
            "why": row.why,
            "action": row.action,
            "access_key": row.access_key,
            "document_type": "cte" if str(header.get("species") or "").upper() == "CTE" or row.rule_id.startswith("cte.") else "nfe",
            "received_date": str(header.get("received_date") or ""),
            "issue_date": str(header.get("issue_date") or ""),
        })
    occurrence_identities = {_document_identity({"access_key": row.access_key, "branch": branch, "document_number": row.document_number, "series": ""}) for row in result.occurrences}
    unmatched_rows = []
    notes = lnf or {}
    for row in result.unmatched:
        header = by_key.get(row.access_key, {})
        xml = xml_docs.get(row.access_key)
        posted = notes.get(row.access_key) if row.access_key else None
        reason = row.reason
        severity = row.severity
        if posted:
            reason = f"{reason} Em lançamento (LNF): {posted.get('status') or 'aberta'}."
            severity = "Info"
        party = str(getattr(row, "party_name", "") or header.get("supplier_name") or (getattr(xml, "issuer_name", "") if xml is not None else ""))
        series = str(getattr(row, "series", "") or header.get("series") or (getattr(xml, "series", "") if xml is not None else ""))
        issued = str(getattr(row, "issue_date", "") or header.get("issue_date") or "")
        amount = getattr(row, "amount", None)
        if amount is None and header:
            amount = header.get("gross_amount")
        unmatched_rows.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "stable_key": stable_occurrence_key(branch=branch, access_key=row.access_key, rule_id=f"unmatched.{row.side}_only", field="Chave", item="", number=row.document_number, series=series, supplier=str(header.get("supplier_code") or ""), store=str(header.get("supplier_store") or "")),
            "side": row.side,
            "rule_id": f"unmatched.{row.side}_only",
            "severity": severity,
            "reason": reason,
            "situation": reason,
            "title": reason,
            "lnf_request_id": str((posted or {}).get("request_id") or ""),
            "lnf_status": str((posted or {}).get("status") or ""),
            "access_key": row.access_key,
            "document_number": row.document_number,
            "series": series,
            "party_name": party,
            "supplier_name": party,
            "party_tax_id": str(getattr(row, "party_tax_id", "") or header.get("supplier_tax_id") or (getattr(xml, "issuer_tax_id", "") if xml is not None else "")),
            "party_state": str(getattr(row, "party_state", "") or header.get("supplier_state") or (getattr(xml, "issuer_state", "") if xml is not None else "")),
            "issue_date": issued,
            "amount": amount if amount is not None else (getattr(xml, "total_amount", None) if xml is not None else None),
            "icms_base": getattr(row, "icms_base", None) if getattr(row, "icms_base", None) is not None else (getattr(xml, "icms_base", None) if xml is not None else header.get("icms_base")),
            "icms_amount": getattr(row, "icms_amount", None) if getattr(row, "icms_amount", None) is not None else (getattr(xml, "icms_amount", None) if xml is not None else header.get("icms_amount")),
            "ipi_amount": getattr(row, "ipi_amount", None) if getattr(row, "ipi_amount", None) is not None else (getattr(xml, "ipi_amount", None) if xml is not None else header.get("ipi_amount")),
            "cfop": str(getattr(row, "cfop", "") or (getattr(xml, "cfop", "") if xml is not None else "")),
            "cst": str(getattr(row, "cst", "") or (getattr(xml, "cst", "") if xml is not None else "")),
            "nature": str(getattr(row, "nature", "") or ""),
            "document_type": "cte" if str(getattr(row, "species", "") or header.get("species") or "").upper() == "CTE" else "nfe",
            "field": "key",
            "theme": "unmatched",
            "item": "",
            "tes": "",
        })
    documents = []
    for header in headers:
        identity = _document_identity(header)
        count = sum(1 for row in result.occurrences if _document_identity({"access_key": row.access_key, "branch": branch, "document_number": row.document_number}) == identity)
        xml = xml_docs.get(str(header.get("access_key") or ""))
        supplier_name = str(header.get("supplier_name") or "") or (getattr(xml, "issuer_name", "") if xml is not None else "")
        documents.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "access_key": str(header.get("access_key") or ""),
            "document_number": str(header.get("document_number") or ""),
            "series": str(header.get("series") or ""),
            "supplier_code": str(header.get("supplier_code") or ""),
            "supplier_store": str(header.get("supplier_store") or ""),
            "supplier_name": supplier_name,
            "issue_date": str(header.get("issue_date") or ""),
            "received_date": str(header.get("received_date") or ""),
            "situation": "divergent" if identity in occurrence_identities else "clean",
            "divergence_count": count,
            "document_type": "cte" if str(header.get("species") or "").upper() == "CTE" else "nfe",
            "comparison": {
                "species": header.get("species"),
                "gross": header.get("gross_amount"),
                "icms": header.get("icms_amount"),
                "ipi": header.get("ipi_amount"),
            },
        })
    for row in unavailable or []:
        documents.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "access_key": str(row.get("access_key") or ""),
            "document_number": str(row.get("document_number") or ""),
            "series": str(row.get("series") or ""),
            "supplier_code": str(row.get("supplier_code") or ""),
            "supplier_store": str(row.get("supplier_store") or ""),
            "supplier_name": str(row.get("supplier_name") or ""),
            "issue_date": str(row.get("issue_date") or ""),
            "received_date": str(row.get("received_date") or ""),
            "situation": "xml_unavailable",
            "divergence_count": 0,
            "document_type": "cte" if str(row.get("species") or "").upper() == "CTE" else "nfe",
            "comparison": {},
        })
    for row in posted_outside or []:
        documents.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "access_key": str(row.get("access_key") or ""),
            "document_number": str(row.get("document_number") or ""),
            "series": str(row.get("series") or ""),
            "supplier_code": str(row.get("supplier_code") or ""),
            "supplier_store": str(row.get("supplier_store") or ""),
            "supplier_name": str(row.get("supplier_name") or ""),
            "issue_date": str(row.get("issue_date") or ""),
            "received_date": str(row.get("received_date") or ""),
            "situation": "posted_outside_period",
            "divergence_count": 0,
            "document_type": "cte" if str(row.get("species") or "").upper() == "CTE" else "nfe",
            "comparison": {"species": row.get("species")},
        })
    ctes = [
        {
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "access_key": str(header.get("access_key") or ""),
            "document_type": "cte",
            "document_number": str(header.get("document_number") or ""),
            "comparison": {"gross": header.get("gross_amount"), "icms": header.get("icms_amount"), "fiscal_code": ""},
        }
        for header in headers
        if str(header.get("species") or "").upper() == "CTE"
    ]
    used_codes = sorted({str(row.get("tes") or "") for row in items if row.get("tes")})
    tes_by_code = {str(row.get("code") or ""): row for row in tes_rows}
    tes_used = []
    for code in used_codes:
        record = tes_by_code.get(code, {})
        tes_used.append({
            "analysis_id": analysis_id,
            "run_id": run_id,
            "branch": branch,
            "tes_code": code,
            "document_type": "nfe",
            "sf4": {
                "description": record.get("description") or "",
                "tes_type": record.get("tes_type") or "",
                "fiscal_code": record.get("fiscal_code") or "",
                "calculates_icms": yes_no(str(record.get("calculates_icms") or "")),
                "credits_icms": yes_no(str(record.get("credits_icms") or "")),
                "icms_book": book_word(str(record.get("icms_book") or "")),
                "calculates_ipi": yes_no(str(record.get("calculates_ipi") or "")),
                "credits_ipi": yes_no(str(record.get("credits_ipi") or "")),
                "ipi_book": book_word(str(record.get("ipi_book") or "")),
                "consumption_material": yes_no(str(record.get("consumption_material") or "")),
                "items": sum(1 for row in items if str(row.get("tes") or "") == code),
            },
        })
    return {"documents": documents, "occurrences": occurrence_rows, "unmatched": unmatched_rows, "ctes": ctes, "tes_used": tes_used}


def _difference(left: str, right: str) -> str:
    try:
        return f"{float(left) - float(right):.2f}"
    except (TypeError, ValueError):
        return ""


def _public_analysis(row: dict) -> dict:
    return {
        "id": row["id"],
        "date_from": row["date_from"].isoformat(),
        "date_to": row["date_to"].isoformat(),
        "document_types": row["document_types"],
        "branches": row["branches"],
        "status": row["status"],
        "requested_via": row["requested_via"],
        "created_at": row["created_at"].isoformat(),
        "finished_at": row["finished_at"].isoformat() if row.get("finished_at") else None,
    }


def _public_occurrence(row: dict, status: dict | None) -> dict:
    return {
        "stable_key": row["stable_key"],
        "rule_id": row.get("rule_id"),
        "rule_name": row.get("title") or row.get("reason"),
        "severity": row.get("severity"),
        "theme": row.get("theme"),
        "title": row.get("title") or row.get("reason"),
        "document_number": row.get("document_number"),
        "item": row.get("item") or "",
        "field": row.get("field"),
        "field_label": row.get("field_label") or row.get("field"),
        "protheus_value": row.get("protheus_value"),
        "xml_value": row.get("xml_value"),
        "why": row.get("why") or "",
        "action": row.get("action") or "",
        "access_key": row.get("access_key") or "",
        "status": (status or {}).get("status", "pending"),
    }


def _history(status: dict | None) -> list[dict]:
    if not status:
        return [{"status": "pending"}]
    return [{
        "status": status.get("status"),
        "resolved_at": status.get("resolved_at").isoformat() if status.get("resolved_at") else None,
        "reopened_at": status.get("reopened_at").isoformat() if status.get("reopened_at") else None,
        "resolved_by_name": status.get("resolved_by_name") or "",
    }]


def _links(row: dict) -> dict:
    request_id = row.get("lnf_request_id") or ""
    return {
        "danfe": f"/lancamento-notas-fiscais/requests/{request_id}/danfe" if request_id else None,
        "dacte": None,
        "xml": f"/lancamento-notas-fiscais/requests/{request_id}/xml" if request_id else None,
    }


def _status(store, row: dict) -> str:
    found = store.status_of(row["stable_key"])
    return (found or {}).get("status", "pending")


def _explained(row: dict) -> bool:
    text = str(row.get("situation") or row.get("reason") or "")
    return row.get("severity") == "Info" or "trânsito" in text or "Em lançamento (LNF)" in text or "Cancelada" in text


def _count(rows: list[dict], column: str) -> list[dict]:
    totals: dict[str, int] = {}
    for row in rows:
        key = str(row.get(column) or "")
        if not key:
            continue
        totals[key] = totals.get(key, 0) + 1
    return [{"name": key, "count": count} for key, count in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]


def _by_day(rows: list[dict]) -> list[dict]:
    return _count([{**row, "day": str(row.get("received_date") or "")[:10]} for row in rows], "day")


def _sort_key(row: dict, sort: str):
    if sort == "supplier":
        return (row.get("supplier_name") or "", row.get("document_number") or "")
    if sort == "document":
        return (row.get("document_number") or "", row.get("item") or "")
    if sort == "day":
        return (row.get("received_date") or "", row.get("document_number") or "")
    order = {"Alta": 0, "Depende da TES": 1, "Média": 2, "Baixa": 3, "Info": 4}
    return (order.get(row.get("severity"), 9), row.get("document_number") or "")
