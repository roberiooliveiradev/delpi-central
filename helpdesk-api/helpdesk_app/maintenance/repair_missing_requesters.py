"""Historical backfill — restore the real GLPI requester TeamMember on
tickets created during the window where POST /tickets never wrote the
requester relation (helpdesk launch 2026-09-21 → corrective deploy
2026-10-09 ~09:05 BRT; tickets 1305/1306 were self-healed by orphan
compensation and are expected absent/trashed).

Gate: authoritative GET TeamMember/requester — never the
requester_display_name fallback (user_recipient masks a missing actor).
Expected identity: the ticket's own historical user_recipient.id —
never the session user running the backfill, never display-name/email
matching, never assignee/observer.

Idempotent: existing requester → ALREADY_CORRECT / EXISTING_REQUESTER_CONFLICT;
missing + recipient id → MISSING_REQUESTER_REPAIRABLE (+apply);
missing + no recipient id → MISSING_REQUESTER_AMBIGUOUS / NO_EXPECTED_IDENTITY.

Run inside the helpdesk-api container:

    python -m helpdesk_app.maintenance.repair_missing_requesters --dry-run
    python -m helpdesk_app.maintenance.repair_missing_requesters --apply
"""

from __future__ import annotations

import argparse
import json
import logging
from dataclasses import dataclass, field

logger = logging.getLogger("helpdesk.backfill.requester")

WINDOW_FROM = "2026-09-21T00:00:00"
WINDOW_TO = "2026-10-09T09:05:00"

ALREADY_CORRECT = "ALREADY_CORRECT"
REPAIRABLE = "MISSING_REQUESTER_REPAIRABLE"
AMBIGUOUS = "MISSING_REQUESTER_AMBIGUOUS"
NO_IDENTITY = "NO_EXPECTED_IDENTITY"
CONFLICT = "EXISTING_REQUESTER_CONFLICT"
OUT_OF_SCOPE = "OUT_OF_SCOPE"
ERROR = "ERROR"


@dataclass
class TicketFinding:
    ticket_id: int
    title: str
    created_at: str
    requester_relation: int | None
    recipient_id: int | None
    recipient_name: str
    classification: str
    detail: str = ""


@dataclass
class BackfillReport:
    scanned: int = 0
    findings: list[TicketFinding] = field(default_factory=list)
    repaired: list[int] = field(default_factory=list)
    failed: list[int] = field(default_factory=list)

    def count(self, classification: str) -> int:
        return sum(1 for f in self.findings if f.classification == classification)


def _recipient_user_id(row: dict) -> int | None:
    recipient = row.get("user_recipient")
    if not isinstance(recipient, dict):
        return None
    try:
        uid = int(recipient.get("id"))
    except (TypeError, ValueError):
        return None
    return uid if uid > 0 else None


def classify_ticket(gateway, token: str, row: dict) -> TicketFinding:
    """Classify one raw ticket row. `gateway` supplies the bounded
    maintenance accessors (list/detail row, requester read/write)."""
    ticket_id = int(row.get("id"))
    title = str(row.get("name") or "")
    created_at = str(row.get("date_creation") or "")
    actual = gateway.ticket_requester(token, ticket_id)
    recipient_id = _recipient_user_id(row)
    recipient = row.get("user_recipient") if isinstance(row.get("user_recipient"), dict) else {}
    recipient_name = str(
        recipient.get("name")
        or recipient.get("display_name")
        or f"{recipient.get('first_name') or ''} {recipient.get('last_name') or ''}".strip()
    )
    if actual is not None:
        if recipient_id is not None and actual == recipient_id:
            classification = ALREADY_CORRECT
        else:
            classification = CONFLICT
    elif recipient_id is not None:
        classification = REPAIRABLE
    elif row.get("user_recipient"):
        classification = AMBIGUOUS
    else:
        classification = NO_IDENTITY
    return TicketFinding(
        ticket_id=ticket_id,
        title=title,
        created_at=created_at,
        requester_relation=actual,
        recipient_id=recipient_id,
        recipient_name=recipient_name,
        classification=classification,
    )


def scan(gateway, token: str, *, from_iso: str, to_iso: str) -> BackfillReport:
    report = BackfillReport()
    for row in gateway.list_ticket_rows(token, created_from=from_iso, created_to=to_iso):
        report.scanned += 1
        try:
            detail = gateway.ticket_row(token, int(row.get("id")))
            report.findings.append(classify_ticket(gateway, token, detail or row))
        except Exception as exc:
            report.findings.append(
                TicketFinding(
                    ticket_id=int(row.get("id") or 0),
                    title=str(row.get("name") or ""),
                    created_at=str(row.get("date_creation") or ""),
                    requester_relation=None,
                    recipient_id=None,
                    recipient_name="",
                    classification=ERROR,
                    detail=f"{type(exc).__name__}: {exc}"[:160],
                )
            )
    return report


def apply_repairs(gateway, token: str, report: BackfillReport) -> BackfillReport:
    """Repair REPAIRABLE findings: write requester = historical
    user_recipient.id, then prove it with an authoritative read-back."""
    for finding in report.findings:
        if finding.classification != REPAIRABLE:
            continue
        # Re-read immediately before writing — keeps --apply idempotent
        # and protects a ticket that gained a requester between scans.
        actual = gateway.ticket_requester(token, finding.ticket_id)
        if actual is not None:
            finding.classification = (
                ALREADY_CORRECT if actual == finding.recipient_id else CONFLICT
            )
            finding.requester_relation = actual
            continue
        try:
            gateway.add_ticket_requester(token, finding.ticket_id, finding.recipient_id)
            verified = gateway.ticket_requester(token, finding.ticket_id)
        except Exception as exc:
            finding.classification = ERROR
            finding.detail = f"{type(exc).__name__}: {exc}"[:160]
            report.failed.append(finding.ticket_id)
            continue
        if verified == finding.recipient_id:
            finding.requester_relation = verified
            finding.classification = ALREADY_CORRECT
            finding.detail = "repaired"
            report.repaired.append(finding.ticket_id)
        else:
            finding.classification = ERROR
            finding.detail = f"read_back_mismatch expected={finding.recipient_id} got={verified}"
            report.failed.append(finding.ticket_id)
        logger.info(
            "requester_backfill ticket_id=%s expected=%s result=%s",
            finding.ticket_id,
            finding.recipient_id,
            finding.detail,
        )
    return report


def _print_report(report: BackfillReport, *, applied: bool) -> None:
    print(json.dumps({
        "applied": applied,
        "scanned": report.scanned,
        "already_correct": report.count(ALREADY_CORRECT),
        "repairable": report.count(REPAIRABLE),
        "ambiguous": report.count(AMBIGUOUS),
        "no_expected_identity": report.count(NO_IDENTITY),
        "conflicts": report.count(CONFLICT),
        "errors": report.count(ERROR),
        "repaired": report.repaired,
        "failed": report.failed,
    }, indent=2))
    for f in report.findings:
        print(
            f"  #{f.ticket_id} [{f.classification}] recipient={f.recipient_id}"
            f" ({f.recipient_name}) relation={f.requester_relation}"
            f" created={f.created_at} title={f.title[:60]} {f.detail}"
        )


def _session_token() -> tuple[str, int]:
    """First valid linked OAuth session — the same-user token that carries
    the rights to read tickets and write TeamMember. Token never printed."""
    from helpdesk_app.infrastructure.persistence.postgres import connect
    from helpdesk_app.main import build_runtime

    with connect() as conn:
        rows = conn.execute("SELECT subject FROM helpdesk.oauth_sessions").fetchall()
    subjects = [r["subject"] if isinstance(r, dict) else r[0] for r in rows]
    oauth, tickets, _ = build_runtime()
    glpi = tickets._glpi
    for subject in subjects:
        try:
            token = oauth.access_token_for(subject)
            return token, glpi.session_user_id(token), glpi, tickets
        except Exception:
            continue
    raise SystemExit("no valid linked GLPI session found")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--from", dest="from_iso", default=WINDOW_FROM)
    parser.add_argument("--to", dest="to_iso", default=WINDOW_TO)
    args = parser.parse_args()

    token, session_uid, glpi, _ = _session_token()
    print(f"session_user_id={session_uid} window={args.from_iso}..{args.to_iso}")

    report = scan(glpi, token, from_iso=args.from_iso, to_iso=args.to_iso)
    if args.apply:
        apply_repairs(glpi, token, report)
    _print_report(report, applied=args.apply)


if __name__ == "__main__":
    main()
