"""P5 — recipient packages, PackageVersion, review e conclusão mensal
(docs 12/37/104; contrato C2/P5-A..J/DEC-01..04).

Invariantes do bounded context:

- recipient package por área destinataria com itens aplicáveis no
  snapshot — pacotes independentes entre si (RQ-P5-04);
- FINALIZE != SUBMIT_FOR_REVIEW: finalizar cria PackageVersion imutável
  com snapshot de composição; submeter congela `required_areas` (P5-H)
  e emite notification outbox — nunca e-mail com pacote (RQ-P5-05/07);
- decisões de área são append-only (P5-B/G): aceite irreversível por
  UI e API; `CHANGES_REQUESTED`/`REJECTED` admitem nova decisão futura
  do mesmo ator elegível;
- authZ de review: ator autenticado com `access` + assignment ativo de
  REVIEWER para o pacote/área (P5-C); `manage` não substitui `access`
  nem concede voto de área sem assignment;
- rejeição terminal é da competência e exige COORDINATOR ativo (DEC-01);
- conclusão mensal é derivada, nunca persistida nem forçável: C2 —
  todos os pacotes aplicáveis com versão vigente SUBMITTED, aceite
  humano real por área obrigatória da versão vigente, zero clarification
  aberta, zero rejeição terminal — + controle B/C: todo domínio P3
  aplicável com proveniência OFFICIAL (conciliação registrada !=
  resultado oficial comprovado);
- conjunto vazio de áreas/revisores nunca satisfaz C2 (D-FINAL-02).
"""

from __future__ import annotations

import hashlib
import json
from decimal import Decimal
from typing import Any

import psycopg
from psycopg.rows import dict_row

from controllership_finance_app.domain.closing_checklist.errors import (
    AreaDecisionTerminal,
    AssignmentNotFound,
    ChecklistDomainError,
    ClarificationNotFound,
    ClarificationResolved,
    CompetenceNotOpened,
    Forbidden,
    InvalidPackageTransition,
    MissingReason,
    PackageNotFound,
    PackageVersionNotFound,
    PendencyOwnershipRequired,
    PersistenceUnavailable,
    ReviewerNotAssigned,
    ReviewerNotEligible,
    StaleRevision,
    TerminalRejectionActive,
    TerminalRejectionNotFound,
    CoordinatorRequired,
)
from controllership_finance_app.infrastructure.persistence.closing_catalog_repository import (
    ClosingCatalogRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_p3_repository import (
    ClosingP3Repository,
)
from controllership_finance_app.infrastructure.persistence.plugins_db import (
    SCHEMA_NAME,
    plugins_db_connect,
    plugins_db_configured,
)

_SCHEMA = SCHEMA_NAME

RECIPIENT_AREAS = ("CONTABIL", "FISCAL")
PACKAGE_ROLES = frozenset({"REVIEWER", "COORDINATOR"})
REVIEW_OUTCOMES = frozenset(
    {"ACCEPTED", "CHANGES_REQUESTED", "REJECTED"}
)
RECONCILIATION_DOMAINS = ("ENTRADAS_SAIDAS", "P7", "H02")
OPEN_PENDENCY_STATES = ("OPEN", "IN_ANALYSIS", "WAITING_EXTERNAL")
ZERO = Decimal("0.00")

_DECISION_EVENTS = {
    "ACCEPTED": "PACKAGE_REVIEW_ACCEPTED",
    "CHANGES_REQUESTED": "PACKAGE_REVIEW_CHANGES_REQUESTED",
    "REJECTED": "PACKAGE_REVIEW_REJECTED",
}


def _q(table: str) -> str:
    return f"{_SCHEMA}.{table}"


def lock_competence_row(cur, competence_id) -> None:
    """R-105-04: ponto de serialização competência-level entre a
    submissão de pacote (marca versão SUBMITTED → congela evidências)
    e mutações de evidência/validação. Ordem canônica de locks:
    competência → versão de pacote → documento/item. Quem detém a
    competência nunca solicita lock de item/documento — sem ciclo."""
    cur.execute(
        f"SELECT competence_id FROM {_q('monthly_competence')} "
        "WHERE competence_id = %s FOR UPDATE",
        (competence_id,),
    )


def locked_item_keys_in(cur, competence_id) -> set[str]:
    """item_keys das versões vigentes SUBMITTED de cada pacote —
    mesma leitura de `locked_item_keys`, executada no cursor da
    transação chamadora (garantia transacional compartilhada)."""
    cur.execute(
        f"""
        SELECT DISTINCT ON (v.package_id)
               v.status, v.content
          FROM {_q('closing_package_version')} v
          JOIN {_q('closing_package')} p
            ON p.package_id = v.package_id
         WHERE p.competence_id = %s
         ORDER BY v.package_id, v.version_no DESC
        """,
        (competence_id,),
    )
    locked: set[str] = set()
    for row in cur.fetchall():
        if row["status"] != "SUBMITTED":
            continue
        content = row["content"] or {}
        if isinstance(content, str):
            content = json.loads(content)
        for item in content.get("items") or []:
            if item.get("item_key"):
                locked.add(item["item_key"])
    return locked


class ClosingPackageRepository:
    """Repository/port implementation — psycopg connection-per-call."""

    def _conn(self) -> psycopg.Connection:
        if not plugins_db_configured():
            raise PersistenceUnavailable(
                "Persistência do workflow não configurada."
            )
        try:
            return plugins_db_connect()
        except psycopg.Error as exc:
            raise PersistenceUnavailable(
                "Persistência do workflow indisponível."
            ) from exc

    def _competence_id(self, cur, period: str) -> str:
        cur.execute(
            f"SELECT competence_id FROM {_q('monthly_competence')}"
            " WHERE period = %s",
            (period,),
        )
        row = cur.fetchone()
        if row is None:
            raise CompetenceNotOpened(
                f"Competência {period} não está aberta."
            )
        return row["competence_id"]

    def _audit(
        self,
        cur,
        *,
        entity_type: str,
        entity_id: Any,
        event_type: str,
        actor: str,
        detail: dict[str, Any],
        competence_id: Any = None,
    ) -> None:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_audit_event')}
                (entity_type, entity_id, competence_id, event_type,
                 actor_subject, detail)
            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                entity_id,
                competence_id,
                event_type,
                actor,
                json.dumps(detail),
            ),
        )

    def _emit_outbox(
        self,
        cur,
        competence_id: str,
        *,
        event_type: str,
        recipients: Any,
        payload: dict[str, Any],
        actor: str,
    ) -> None:
        """Outbox atômico com a mutação (RQ-P5-05/07).

        A emissão é registrada na mesma transação — prova de emissão;
        a entrega pertence ao Core Notifications e nunca vira critério
        de negócio. O ator não se notifica do próprio ato.
        """
        for recipient in sorted({str(r) for r in recipients if r}):
            if recipient == str(actor):
                continue
            cur.execute(
                f"""
                INSERT INTO {_q('closing_notification_event')}
                    (competence_id, event_type, recipient_subject,
                     payload, emitted_by)
                VALUES (%s, %s, %s, %s::jsonb, %s)
                """,
                (
                    competence_id,
                    event_type,
                    recipient,
                    json.dumps(payload),
                    actor,
                ),
            )

    def _competence_recipients(
        self, cur, competence_id: str
    ) -> set[str]:
        """Destinatários operacionais da competência: assignments ativos
        + quem submeteu versões de pacote (vínculos reais, nunca listas
        estáticas)."""
        cur.execute(
            f"""
            SELECT DISTINCT subject FROM {_q('closing_review_assignment')}
             WHERE competence_id = %s AND active
            UNION
            SELECT DISTINCT v.submitted_by
              FROM {_q('closing_package_version')} v
              JOIN {_q('closing_package')} p
                ON p.package_id = v.package_id
             WHERE p.competence_id = %s AND v.submitted_by IS NOT NULL
            """,
            (competence_id, competence_id),
        )
        return {str(r["subject"]) for r in cur.fetchall()}

    # -- leituras base -------------------------------------------------

    def _applicable_areas(self, cur, competence_id: str) -> list[str]:
        """Áreas destinatárias com >= 1 item não cancelado no snapshot."""
        cur.execute(
            f"""
            SELECT DISTINCT recipient_area
              FROM {_q('competence_checklist_item')}
             WHERE competence_id = %s
               AND recipient_area IS NOT NULL
               AND state <> 'CANCELLED'
             ORDER BY recipient_area
            """,
            (competence_id,),
        )
        return [r["recipient_area"] for r in cur.fetchall()]

    def _package_rows(self, cur, competence_id: str) -> dict[str, dict]:
        cur.execute(
            f"""
            SELECT package_id, competence_id, recipient_area, revision,
                   created_by, created_at
              FROM {_q('closing_package')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        return {r["recipient_area"]: r for r in cur.fetchall()}

    def _versions(self, cur, package_id: str) -> list[dict]:
        cur.execute(
            f"""
            SELECT package_version_id, package_id, version_no, status,
                   content, required_areas, previous_version_id,
                   change_reason, finalized_by, finalized_at,
                   submitted_by, submitted_at, revision,
                   created_by, created_at
              FROM {_q('closing_package_version')}
             WHERE package_id = %s
             ORDER BY version_no DESC
            """,
            (package_id,),
        )
        return cur.fetchall()

    def _latest_version(self, cur, package_id: str) -> dict | None:
        versions = self._versions(cur, package_id)
        return versions[0] if versions else None

    def _decisions(self, cur, package_version_id: str) -> dict[str, dict]:
        """Decisão vigente por área = mais recente (append-only)."""
        cur.execute(
            f"""
            SELECT DISTINCT ON (area)
                   decision_id, area, outcome, actor_subject, note,
                   created_at
              FROM {_q('closing_review_decision')}
             WHERE package_version_id = %s
             ORDER BY area, created_at DESC, decision_id DESC
            """,
            (package_version_id,),
        )
        return {r["area"]: r for r in cur.fetchall()}

    def _all_decisions(self, cur, package_version_id: str) -> list[dict]:
        cur.execute(
            f"""
            SELECT decision_id, area, outcome, actor_subject, note,
                   created_at
              FROM {_q('closing_review_decision')}
             WHERE package_version_id = %s
             ORDER BY created_at, decision_id
            """,
            (package_version_id,),
        )
        return cur.fetchall()

    def _clarifications(self, cur, package_version_id: str) -> list[dict]:
        cur.execute(
            f"""
            SELECT clarification_id, area, state, question, response,
                   opened_by, opened_at, resolved_by, resolved_at
              FROM {_q('closing_clarification')}
             WHERE package_version_id = %s
             ORDER BY opened_at, clarification_id
            """,
            (package_version_id,),
        )
        return cur.fetchall()

    def _assignments(
        self, cur, competence_id: str, *, package_id: str | None = None,
        subject: str | None = None, active_only: bool = True,
    ) -> list[dict]:
        clauses = ["competence_id = %s"]
        params: list[Any] = [competence_id]
        if package_id is not None:
            clauses.append("package_id = %s")
            params.append(package_id)
        if subject is not None:
            clauses.append("subject = %s")
            params.append(subject)
        if active_only:
            clauses.append("active")
        cur.execute(
            f"""
            SELECT assignment_id, competence_id, package_id, role, area,
                   subject, active, assigned_by, assigned_at,
                   deactivated_by, deactivated_at, deactivate_reason
              FROM {_q('closing_review_assignment')}
             WHERE {' AND '.join(clauses)}
             ORDER BY assigned_at, assignment_id
            """,
            params,
        )
        return cur.fetchall()

    def _terminal_rejection(
        self, cur, competence_id: str
    ) -> dict | None:
        cur.execute(
            f"""
            SELECT rejection_id, state, reason, confirmed_by,
                   confirmed_at, reverted_by, reverted_at, revert_reason
              FROM {_q('closing_terminal_rejection')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        return cur.fetchone()

    def _require_no_terminal_rejection(
        self, cur, competence_id: str
    ) -> None:
        """P5-J / RQ-P5-TERM-02: rejeicao terminal ACTIVE congela o
        fluxo de revisao da competencia — submissao, inicio de review,
        decisoes, esclarecimentos e novas versoes ficam bloqueados ate
        reversao autorizada por COORDINATOR (DEC-01). Historico e
        decisoes anteriores sao preservados."""
        rejection = self._terminal_rejection(cur, competence_id)
        if rejection and rejection["state"] == "ACTIVE":
            raise TerminalRejectionActive(
                "Competência com rejeição terminal ativa."
            )

    def _review_state(
        self,
        version: dict | None,
        decisions: dict[str, dict],
        clarifications: list[dict],
    ) -> str:
        """Estado de review derivado da versão vigente (doc 37 §7)."""
        if version is None or version["status"] == "DRAFT":
            return "REVIEW_PENDING"
        if version["status"] == "FINALIZED":
            return "REVIEW_PENDING"
        required = version.get("required_areas") or []
        open_clarif = any(
            c["state"] == "OPEN" for c in clarifications
        )
        if not required:
            # Sem áreas obrigatórias: pendente até aceite humano real
            # (D-FINAL-02) — nunca completa por vacuidade.
            return "REVIEW_PENDING"
        latest = {a: d["outcome"] for a, d in decisions.items()}
        if any(latest.get(a) == "REJECTED" for a in required):
            return "REVIEW_REJECTED"
        if open_clarif or any(
            latest.get(a) == "CHANGES_REQUESTED" for a in required
        ):
            if open_clarif:
                return "WAITING_FOR_CLARIFICATION"
            return "CHANGES_REQUESTED"
        if all(latest.get(a) == "ACCEPTED" for a in required):
            return "REVIEW_ACCEPTED"
        if decisions:
            return "REVIEW_IN_PROGRESS"
        return "REVIEW_PENDING"

    def _package_view(
        self,
        cur,
        competence_id: str,
        package: dict | None,
        area: str,
        *,
        include_history: bool = False,
    ) -> dict[str, Any]:
        versions = (
            self._versions(cur, package["package_id"])
            if package
            else []
        )
        latest = versions[0] if versions else None
        decisions = (
            self._decisions(cur, latest["package_version_id"])
            if latest
            else {}
        )
        clarifications = (
            self._clarifications(cur, latest["package_version_id"])
            if latest
            else []
        )
        assignments = (
            self._assignments(
                cur, competence_id, package_id=package["package_id"]
            )
            if package
            else []
        )
        required = (
            (latest.get("required_areas") or [])
            if latest and latest["status"] == "SUBMITTED"
            else [a["area"] for a in assignments if a["role"] == "REVIEWER"]
        )
        if latest is None:
            state = "PACKAGE_INCOMPLETE"
        elif latest["status"] == "DRAFT":
            state = "PACKAGE_INCOMPLETE"
        elif latest["status"] == "FINALIZED":
            state = "PACKAGE_FINALIZED"
        else:
            state = "PACKAGE_SUBMITTED_FOR_REVIEW"
        view: dict[str, Any] = {
            "package_id": package["package_id"] if package else None,
            "recipient_area": area,
            "state": state,
            "review_state": self._review_state(
                latest, decisions, clarifications
            ),
            "current_version": latest,
            "required_areas": required,
            "area_decisions": decisions,
            "open_clarifications": sum(
                1 for c in clarifications if c["state"] == "OPEN"
            ),
            "assignments": assignments,
            "revision": package["revision"] if package else 0,
        }
        if include_history:
            view["versions"] = [
                {
                    **v,
                    "area_decisions": self._decisions(
                        cur, v["package_version_id"]
                    ),
                    "clarifications": self._clarifications(
                        cur, v["package_version_id"]
                    ),
                }
                for v in versions
            ]
        else:
            view["version_count"] = len(versions)
        return view

    def _visible_areas(
        self,
        cur,
        competence_id: str,
        areas: list[str],
        packages: dict[str, dict],
        *,
        viewer: str,
        is_manage: bool,
    ) -> list[str]:
        """Manage vê todos; demais veem apenas pacotes com assignment
        ativo — reviewer nunca enxerga pacote de sibling (P5 §10)."""
        if is_manage:
            return areas
        mine = {
            a["package_id"]
            for a in self._assignments(
                cur, competence_id, subject=viewer
            )
            if a["package_id"] is not None
        }
        return [
            area
            for area in areas
            if area in packages
            and packages[area]["package_id"] in mine
        ]

    # -- readiness / blockers (RQ-P5-01) --------------------------------

    def _readiness_blockers(
        self, cur, competence_id: str, area: str, period: str
    ) -> list[str]:
        """Composição honesta: checklist P2 + fila P4 + prontidão P3.

        `p3_declared_only` é informativo para finalização (o pacote
        registra a força da evidência), mas é bloqueio duro da conclusão
        mensal — ver `derive_closing_state`.
        """
        blockers: list[str] = []
        cur.execute(
            f"""
            SELECT COUNT(*) AS n
              FROM {_q('competence_checklist_item')}
             WHERE competence_id = %s
               AND recipient_area = %s
               AND state = 'EXPECTED'
            """,
            (competence_id, area),
        )
        if cur.fetchone()["n"]:
            blockers.append("checklist_items_pending")
        cur.execute(
            f"""
            SELECT COUNT(*) AS n
              FROM {_q('closing_pendency')}
             WHERE competence_id = %s
               AND state = ANY(%s)
            """,
            (competence_id, list(OPEN_PENDENCY_STATES)),
        )
        if cur.fetchone()["n"]:
            blockers.append("open_pendencies")
        # STOCK_CLOSED canónico não mascara inputs obsoletos — usar
        # blockers do P3 (cutoff, revalidação vigente, disponibilidade,
        # divergência) em vez do estado derivado.
        p3 = ClosingP3Repository().get_p3_state(period)
        if p3["blockers"]:
            blockers.append("p3_not_ready:" + ",".join(p3["blockers"]))
        rejection = self._terminal_rejection(cur, competence_id)
        if rejection is not None and rejection["state"] == "ACTIVE":
            blockers.append("terminal_rejection_active")
        return blockers

    # -- listagem / detalhe ---------------------------------------------

    def list_packages(
        self,
        period: str,
        *,
        viewer: str,
        is_manage: bool,
    ) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            areas = self._applicable_areas(cur, competence_id)
            packages = self._package_rows(cur, competence_id)
            visible = self._visible_areas(
                cur, competence_id, areas, packages,
                viewer=viewer, is_manage=is_manage,
            )
            result = []
            for area in visible:
                view = self._package_view(
                    cur, competence_id, packages.get(area), area
                )
                if is_manage:
                    view["blockers"] = self._readiness_blockers(
                        cur, competence_id, area, period
                    )
                result.append(view)
            return {
                "period": period,
                "applicable_areas": areas,
                "packages": result,
            }

    def get_package(
        self,
        period: str,
        package_id: str,
        *,
        viewer: str,
        is_manage: bool,
    ) -> dict[str, Any]:
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            packages = self._package_rows(cur, competence_id)
            package = next(
                (p for p in packages.values()
                 if str(p["package_id"]) == str(package_id)),
                None,
            )
            if package is None:
                raise PackageNotFound("Pacote não encontrado.")
            visible = self._visible_areas(
                cur,
                competence_id,
                [package["recipient_area"]],
                packages,
                viewer=viewer,
                is_manage=is_manage,
            )
            if not visible:
                raise PackageNotFound("Pacote não encontrado.")
            view = self._package_view(
                cur,
                competence_id,
                package,
                package["recipient_area"],
                include_history=True,
            )
            view["blockers"] = self._readiness_blockers(
                cur, competence_id, package["recipient_area"],
                period,
            )
            return view

    # -- mutações governadas ---------------------------------------------

    def _ensure_package(
        self, cur, competence_id: str, area: str, actor: str
    ) -> dict:
        packages = self._package_rows(cur, competence_id)
        if area in packages:
            return packages[area]
        if area not in self._applicable_areas(cur, competence_id):
            raise PackageNotFound(
                f"Área {area} não possui pacote aplicável."
            )
        cur.execute(
            f"""
            INSERT INTO {_q('closing_package')}
                (competence_id, recipient_area, created_by)
            VALUES (%s, %s, %s)
            RETURNING package_id, competence_id, recipient_area,
                      revision, created_by, created_at
            """,
            (competence_id, area, actor),
        )
        row = cur.fetchone()
        self._audit(
            cur,
            entity_type="closing_package",
            entity_id=row["package_id"],
            competence_id=competence_id,
            event_type="PACKAGE_CREATED",
            actor=actor,
            detail={"recipient_area": area},
        )
        return row

    def _composition_snapshot(
        self, cur, competence_id: str, area: str
    ) -> dict[str, Any]:
        """Conteúdo imutável da PackageVersion: itens aceitos da área +
        versões correntes das evidências + resumo P3/P4 (doc 12 §Contratos)."""
        cur.execute(
            f"""
            SELECT i.item_key, i.state,
                   d.document_id, d.current_version_no,
                   dv.document_version_id
              FROM {_q('competence_checklist_item')} i
              LEFT JOIN {_q('closing_document')} d
                     ON d.snapshot_item_id = i.snapshot_item_id
                    AND d.competence_id = i.competence_id
                    AND d.state = 'ATTACHED'
              LEFT JOIN {_q('document_version')} dv
                     ON dv.document_id = d.document_id
                    AND dv.version_no = d.current_version_no
             WHERE i.competence_id = %s
               AND i.recipient_area = %s
               AND i.state IN ('ACCEPTED', 'NOT_APPLICABLE')
             ORDER BY i.item_key
            """,
            (competence_id, area),
        )
        items = [
            {
                "item_key": r["item_key"],
                "state": r["state"],
                "document_version_id": (
                    str(r["document_version_id"])
                    if r["document_version_id"]
                    else None
                ),
            }
            for r in cur.fetchall()
        ]
        cur.execute(
            f"""
            SELECT domain, source_state, expected_amount::text,
                   reported_amount::text, provenance_kind
              FROM {_q('closing_reconciliation')}
             WHERE competence_id = %s
            """,
            (competence_id,),
        )
        p3 = {r["domain"]: r for r in cur.fetchall()}
        cur.execute(
            f"""
            SELECT state, COUNT(*) AS n
              FROM {_q('closing_pendency')}
             WHERE competence_id = %s
             GROUP BY state
            """,
            (competence_id,),
        )
        p4 = {r["state"]: r["n"] for r in cur.fetchall()}
        return {
            "recipient_area": area,
            "items": items,
            "p3_reconciliation": p3,
            "p4_pendency_counts": p4,
        }

    def locked_item_keys(self, period: str) -> set[str]:
        """item_keys que integram a composição da versão vigente
        SUBMITTED de cada pacote — evidência e validação congeladas
        até uma nova versão (reopen/complement) governar a correção."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            return locked_item_keys_in(cur, competence_id)

    def finalize_package(
        self,
        period: str,
        recipient_area: str,
        *,
        actor: str,
        notes: str | None = None,
    ) -> dict[str, Any]:
        area = (recipient_area or "").strip().upper()
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    blockers = self._readiness_blockers(
                        cur, competence_id, area, period
                    )
                    if blockers:
                        raise InvalidPackageTransition(
                            "Finalização bloqueada: "
                            + ", ".join(blockers)
                            + "."
                        )
                    package = self._ensure_package(
                        cur, competence_id, area, actor
                    )
                    latest = self._latest_version(
                        cur, package["package_id"]
                    )
                    content = self._composition_snapshot(
                        cur, competence_id, area
                    )
                    if latest is not None and latest["status"] == "DRAFT":
                        cur.execute(
                            f"""
                            UPDATE {_q('closing_package_version')}
                               SET status = 'FINALIZED',
                                   content = %s::jsonb,
                                   finalized_by = %s,
                                   finalized_at = now(),
                                   revision = revision + 1
                             WHERE package_version_id = %s
                            """,
                            (
                                json.dumps(content),
                                actor,
                                latest["package_version_id"],
                            ),
                        )
                        version_id = latest["package_version_id"]
                        version_no = latest["version_no"]
                    elif latest is not None and latest["status"] in (
                        "FINALIZED",
                        "SUBMITTED",
                    ):
                        raise InvalidPackageTransition(
                            "Versão vigente já finalizada/submetida; "
                            "use reopen ou complemento."
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO {_q('closing_package_version')}
                                (package_id, version_no, status, content,
                                 finalized_by, finalized_at, created_by)
                            VALUES (%s, 1, 'FINALIZED', %s::jsonb,
                                    %s, now(), %s)
                            RETURNING package_version_id
                            """,
                            (
                                package["package_id"],
                                json.dumps(content),
                                actor,
                                actor,
                            ),
                        )
                        version_id = cur.fetchone()[
                            "package_version_id"
                        ]
                        version_no = 1
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=version_id,
                        competence_id=competence_id,
                        event_type="PACKAGE_FINALIZED",
                        actor=actor,
                        detail={
                            "recipient_area": area,
                            "version_no": version_no,
                            "notes": notes,
                        },
                    )
                    return self._package_view(
                        cur,
                        competence_id,
                        package,
                        package["recipient_area"],
                    )

    def reopen_version(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        """Reabertura pré-submissão: versão finalizada permanece histórica;
        nova working copy DRAFT encadeada (RQ-P5-03)."""
        if not reason or not reason.strip():
            raise MissingReason("Reabertura exige motivo.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    version, latest = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if version["package_version_id"] != latest["package_version_id"] or version[
                        "status"
                    ] != "FINALIZED":
                        raise InvalidPackageTransition(
                            "Somente a versão vigente FINALIZED pode ser "
                            "reaberta antes da submissão."
                        )
                    version_id = self._spawn_next_version(
                        cur,
                        package_id=version["package_id"],
                        version_no=latest["version_no"] + 1,
                        previous=version,
                        status="DRAFT",
                        reason=reason,
                        actor=actor,
                    )
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=version_id,
                        competence_id=competence_id,
                        event_type="PACKAGE_REOPENED",
                        actor=actor,
                        detail={
                            "previous_version_id": str(
                                version["package_version_id"]
                            ),
                            "reason": reason,
                        },
                    )
                    package = self._package_rows(cur, competence_id)[
                        version["recipient_area"]
                    ]
                    return self._package_view(
                        cur,
                        competence_id,
                        package,
                        version["recipient_area"],
                    )

    def create_complement(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        """Correção pós-submissão: V1 submetida permanece imutável; nova
        versão DRAFT encadeada exige novos aceites de todas as áreas
        (P5-E/RQ-P5-10)."""
        if not reason or not reason.strip():
            raise MissingReason("Complemento exige motivo.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    version, latest = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if version["package_version_id"] != latest["package_version_id"] or version[
                        "status"
                    ] != "SUBMITTED":
                        raise InvalidPackageTransition(
                            "Complemento só parte da versão vigente "
                            "submetida."
                        )
                    version_id = self._spawn_next_version(
                        cur,
                        package_id=version["package_id"],
                        version_no=latest["version_no"] + 1,
                        previous=version,
                        status="DRAFT",
                        reason=reason,
                        actor=actor,
                    )
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=version_id,
                        competence_id=competence_id,
                        event_type="PACKAGE_COMPLEMENT_CREATED",
                        actor=actor,
                        detail={
                            "previous_version_id": str(
                                version["package_version_id"]
                            ),
                            "reason": reason,
                        },
                    )
                    package = self._package_rows(cur, competence_id)[
                        version["recipient_area"]
                    ]
                    return self._package_view(
                        cur,
                        competence_id,
                        package,
                        version["recipient_area"],
                    )

    def _version_for_update(
        self, cur, competence_id: str, package_version_id: str
    ) -> tuple[dict, dict]:
        cur.execute(
            f"""
            SELECT v.*, p.recipient_area, p.competence_id
              FROM {_q('closing_package_version')} v
              JOIN {_q('closing_package')} p
                ON p.package_id = v.package_id
             WHERE v.package_version_id = %s
               AND p.competence_id = %s
             FOR UPDATE OF v
            """,
            (package_version_id, competence_id),
        )
        version = cur.fetchone()
        if version is None:
            raise PackageVersionNotFound("Versão não encontrada.")
        latest = self._latest_version(cur, version["package_id"])
        if latest is None:
            raise PackageVersionNotFound("Versão não encontrada.")
        return version, latest

    def _spawn_next_version(
        self,
        cur,
        *,
        package_id: str,
        version_no: int,
        previous: dict,
        status: str,
        reason: str,
        actor: str,
    ) -> str:
        cur.execute(
            f"""
            INSERT INTO {_q('closing_package_version')}
                (package_id, version_no, status, content,
                 previous_version_id, change_reason, created_by)
            VALUES (%s, %s, %s, %s::jsonb, %s, %s, %s)
            RETURNING package_version_id
            """,
            (
                package_id,
                version_no,
                status,
                json.dumps(previous["content"] or {}),
                previous["package_version_id"],
                reason,
                actor,
            ),
        )
        return cur.fetchone()["package_version_id"]

    def submit_for_review(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        expected_revision: int,
    ) -> dict[str, Any]:
        """Submissão in-portal: congela required_areas por tipo de
        pacote (P5-H) e emite notification outbox (nunca e-mail com
        pacote). Falha de notificação não reverte (RQ-P5-07)."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    lock_competence_row(cur, competence_id)
                    version, latest = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if version["status"] != "FINALIZED" or (
                        version["package_version_id"]
                        != latest["package_version_id"]
                    ):
                        raise InvalidPackageTransition(
                            "Somente a versão vigente FINALIZED pode ser "
                            "submetida."
                        )
                    if version["revision"] != expected_revision:
                        raise StaleRevision(
                            "Revisão desatualizada; recarregue o pacote."
                        )
                    assignments = self._assignments(
                        cur,
                        competence_id,
                        package_id=version["package_id"],
                    )
                    # P5-H: áreas obrigatórias versionadas por tipo de
                    # pacote (catálogo P6 PACKAGE_REQUIRED_AREA); o
                    # snapshot congela nesta versão. Reviewer assignment
                    # é vínculo operacional, NÃO fonte da obrigação.
                    # Catálogo sem entradas para o tipo → fallback
                    # monoárea explícito (DECISION_REQUIRED para seeds
                    # multi-área em G1 — nunca inferência silenciosa).
                    catalog = ClosingCatalogRepository()
                    catalog_areas = catalog.required_areas_for(
                        version["recipient_area"]
                    )
                    if catalog_areas:
                        required_areas = catalog_areas
                        required_source = "catalog:PACKAGE_REQUIRED_AREA"
                    else:
                        required_areas = [version["recipient_area"]]
                        required_source = "fallback_recipient_area"
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_package_version')}
                           SET status = 'SUBMITTED',
                               required_areas = %s::jsonb,
                               submitted_by = %s,
                               submitted_at = now(),
                               revision = revision + 1
                         WHERE package_version_id = %s
                        """,
                        (
                            json.dumps(required_areas),
                            actor,
                            package_version_id,
                        ),
                    )
                    for a in assignments:
                        self._emit_outbox(
                            cur,
                            competence_id,
                            event_type="PACKAGE_SUBMITTED_FOR_REVIEW",
                            recipients={a["subject"]},
                            payload={
                                "package_version_id": str(
                                    package_version_id
                                ),
                                "recipient_area": version[
                                    "recipient_area"
                                ],
                                "period": period,
                                "area": a["area"],
                            },
                            actor=actor,
                        )
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=package_version_id,
                        competence_id=competence_id,
                        event_type="PACKAGE_SUBMITTED_FOR_REVIEW",
                        actor=actor,
                        detail={
                            "recipient_area": version["recipient_area"],
                            "version_no": version["version_no"],
                            "required_areas": required_areas,
                            "required_areas_source": required_source,
                            "notified_subjects": [
                                str(a["subject"]) for a in assignments
                            ],
                        },
                    )
                    package = self._package_rows(cur, competence_id)[
                        version["recipient_area"]
                    ]
                    return self._package_view(
                        cur,
                        competence_id,
                        package,
                        version["recipient_area"],
                    )

    # -- assignments (reviewer / coordinator) ----------------------------

    def assign_actor(
        self,
        period: str,
        *,
        actor: str,
        role: str,
        subject: str,
        recipient_area: str | None = None,
        area: str | None = None,
    ) -> dict[str, Any]:
        role = (role or "").strip().upper()
        if role not in PACKAGE_ROLES:
            raise ChecklistDomainError(
                f"role deve ser um de {sorted(PACKAGE_ROLES)}."
            )
        if not subject or not subject.strip():
            raise ChecklistDomainError("subject é obrigatório.")
        if role == "REVIEWER":
            if not area or not area.strip():
                raise ChecklistDomainError(
                    "REVIEWER exige area."
                )
            if not recipient_area:
                raise ChecklistDomainError(
                    "REVIEWER exige recipient_area."
                )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    package_id = None
                    if role == "REVIEWER":
                        package = self._ensure_package(
                            cur,
                            competence_id,
                            (recipient_area or "").strip().upper(),
                            actor,
                        )
                        package_id = package["package_id"]
                    cur.execute(
                        f"""
                        INSERT INTO {_q('closing_review_assignment')}
                            (competence_id, package_id, role, area,
                             subject, assigned_by)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        RETURNING assignment_id, role, area, subject,
                                  package_id, active, assigned_at
                        """,
                        (
                            competence_id,
                            package_id,
                            role,
                            (area or "").strip() or None,
                            subject,
                            actor,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_review_assignment",
                        entity_id=row["assignment_id"],
                        competence_id=competence_id,
                        event_type="REVIEW_ASSIGNMENT_CREATED",
                        actor=actor,
                        detail={
                            "role": role,
                            "area": area,
                            "subject": subject,
                            "package_id": (
                                str(package_id) if package_id else None
                            ),
                        },
                    )
                    return row

    def deactivate_assignment(
        self,
        period: str,
        assignment_id: str,
        *,
        actor: str,
        reason: str | None = None,
    ) -> dict[str, Any]:
        """Reatribuição: desativa linha — substituto só age futuramente;
        aceites passados preservam autoria (P5-F)."""
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_review_assignment')}
                           SET active = FALSE,
                               deactivated_by = %s,
                               deactivated_at = now(),
                               deactivate_reason = %s
                         WHERE assignment_id = %s
                           AND competence_id = %s
                           AND active
                        RETURNING assignment_id, role, area, subject,
                                  package_id
                        """,
                        (
                            actor,
                            reason,
                            assignment_id,
                            competence_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise AssignmentNotFound(
                            "Assignment não encontrado ou inativo."
                        )
                    self._audit(
                        cur,
                        entity_type="closing_review_assignment",
                        entity_id=row["assignment_id"],
                        competence_id=competence_id,
                        event_type="REVIEW_ASSIGNMENT_DEACTIVATED",
                        actor=actor,
                        detail={
                            "role": row["role"],
                            "area": row["area"],
                            "subject": str(row["subject"]),
                            "reason": reason,
                        },
                    )
                    return row

    # -- review -----------------------------------------------------------

    def _require_reviewer(
        self, cur, competence_id: str, package_id: str, actor: str
    ) -> list[dict]:
        assignments = self._assignments(
            cur,
            competence_id,
            package_id=package_id,
            subject=actor,
        )
        reviewers = [a for a in assignments if a["role"] == "REVIEWER"]
        if not reviewers:
            raise ReviewerNotAssigned(
                "Ator não possui assignment de reviewer neste pacote."
            )
        return reviewers

    @staticmethod
    def _eligibility_mode(
        area: str, user_groups
    ) -> tuple[str, set[str]]:
        """T05/F2 + R-105-03: binding REVIEW_ELIGIBILITY da área vs.
        `user.groups` resolvidos pelo RBAC Core (middleware). Binding
        configurado ⇒ interseção obrigatória (fail-closed). Sem binding
        ⇒ `assignment_only` — vínculo operacional auditado, nunca
        prova de elegibilidade corporativa plena (G1)."""
        binding = ClosingCatalogRepository().eligibility_groups_for(
            area
        )
        matched = set(user_groups or ()) & binding if binding else set()
        if binding:
            return (
                "core_group_binding" if matched else "denied",
                matched,
            )
        return "assignment_only", matched

    def _require_eligible_reviewer(
        self,
        cur,
        competence_id: str,
        package_id: str,
        actor: str,
        user_groups,
        *,
        area: str | None = None,
    ) -> tuple[list[dict], str]:
        """Assignment + elegibilidade Core nas áreas do ator.

        `area` explícita: binding avaliado só nela. Sem área: o ator
        precisa ser elegível em AO MENOS uma das suas áreas atribuídas
        — decisões continuam fail-closed por área em record_decision.
        """
        reviewers = self._require_reviewer(
            cur, competence_id, package_id, actor
        )
        target_areas = (
            [area] if area else [a["area"] for a in reviewers]
        )
        modes: list[str] = []
        for a in target_areas:
            if a is None:
                continue
            mode, _matched = self._eligibility_mode(a, user_groups)
            modes.append(mode)
            if mode == "core_group_binding":
                return reviewers, "core_group_binding"
        if "denied" in modes and "core_group_binding" not in modes:
            raise ReviewerNotEligible(
                "Ator sem grupo/função Core elegível para a área "
                f"{target_areas[0]}."
            )
        return reviewers, "assignment_only"

    def start_review(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        user_groups: Any = (),
    ) -> dict[str, Any]:
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    version, latest = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if version["status"] != "SUBMITTED":
                        raise InvalidPackageTransition(
                            "Review exige versão SUBMITTED."
                        )
                    _reviewers, eligibility_mode = (
                        self._require_eligible_reviewer(
                            cur,
                            competence_id,
                            version["package_id"],
                            actor,
                            user_groups,
                        )
                    )
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=package_version_id,
                        competence_id=competence_id,
                        event_type="PACKAGE_REVIEW_STARTED",
                        actor=actor,
                        detail={
                            "version_no": version["version_no"],
                            "eligibility_mode": eligibility_mode,
                        },
                    )
                    return {"started": True}

    def record_decision(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        area: str,
        outcome: str,
        note: str | None = None,
        user_groups: Any = (),
    ) -> dict[str, Any]:
        outcome = (outcome or "").strip().upper()
        if outcome not in REVIEW_OUTCOMES:
            raise ChecklistDomainError(
                f"outcome deve ser um de {sorted(REVIEW_OUTCOMES)}."
            )
        if outcome != "ACCEPTED" and not (note and note.strip()):
            raise MissingReason(
                f"outcome {outcome} exige motivo (note)."
            )
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    version, latest = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if (
                        version["package_version_id"]
                        != latest["package_version_id"]
                        or version["status"] != "SUBMITTED"
                    ):
                        raise InvalidPackageTransition(
                            "Decisões somente na versão vigente "
                            "submetida."
                        )
                    area_norm = (area or "").strip()
                    reviewers = self._require_reviewer(
                        cur, competence_id, version["package_id"], actor
                    )
                    if not any(
                        a["area"] == area_norm for a in reviewers
                    ):
                        raise ReviewerNotAssigned(
                            f"Ator sem assignment para área {area_norm}."
                        )
                    eligibility_mode, matched = self._eligibility_mode(
                        area_norm, user_groups
                    )
                    if eligibility_mode == "denied":
                        raise ReviewerNotEligible(
                            "Ator sem grupo/função Core elegível "
                            f"para a área {area_norm}."
                        )
                    decisions = self._decisions(
                        cur, package_version_id
                    )
                    current = decisions.get(area_norm)
                    if current and current["outcome"] == "ACCEPTED":
                        raise AreaDecisionTerminal(
                            "Aceite da área é irreversível na V1 "
                            "(P5-B/G)."
                        )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('closing_review_decision')}
                            (package_version_id, area, outcome,
                             actor_subject, note)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING decision_id, area, outcome,
                                  actor_subject, created_at
                        """,
                        (
                            package_version_id,
                            area_norm,
                            outcome,
                            actor,
                            note,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_package_version",
                        entity_id=package_version_id,
                        competence_id=competence_id,
                        event_type=_DECISION_EVENTS[outcome],
                        actor=actor,
                        detail={
                            "area": area_norm,
                            "outcome": outcome,
                            "note": note,
                            "version_no": version["version_no"],
                            "eligibility_mode": eligibility_mode,
                            "matched_eligibility_groups": sorted(matched),
                        },
                    )
                    return row

    def open_clarification(
        self,
        period: str,
        package_version_id: str,
        *,
        actor: str,
        question: str,
        area: str | None = None,
        user_groups: Any = (),
    ) -> dict[str, Any]:
        if not question or not question.strip():
            raise MissingReason("question é obrigatório.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    version, _ = self._version_for_update(
                        cur, competence_id, package_version_id
                    )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    if version["status"] != "SUBMITTED":
                        raise InvalidPackageTransition(
                            "Clarification exige versão SUBMITTED."
                        )
                    self._require_eligible_reviewer(
                        cur,
                        competence_id,
                        version["package_id"],
                        actor,
                        user_groups,
                        area=(area or "").strip() or None,
                    )
                    cur.execute(
                        f"""
                        INSERT INTO {_q('closing_clarification')}
                            (package_version_id, area, question,
                             opened_by)
                        VALUES (%s, %s, %s, %s)
                        RETURNING clarification_id, area, state,
                                  question, opened_by, opened_at
                        """,
                        (
                            package_version_id,
                            (area or "").strip() or None,
                            question,
                            actor,
                        ),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_clarification",
                        entity_id=row["clarification_id"],
                        competence_id=competence_id,
                        event_type="CLARIFICATION_OPENED",
                        actor=actor,
                        detail={
                            "package_version_id": str(
                                package_version_id
                            ),
                            "area": area,
                            "question": question,
                        },
                    )
                    self._emit_outbox(
                        cur,
                        competence_id,
                        event_type="PACKAGE_CLARIFICATION_OPENED",
                        recipients={version["submitted_by"]},
                        payload={
                            "package_version_id": str(
                                package_version_id
                            ),
                            "recipient_area": version[
                                "recipient_area"
                            ],
                            "period": period,
                            "clarification_id": str(
                                row["clarification_id"]
                            ),
                        },
                        actor=actor,
                    )
                    return row

    def resolve_clarification(
        self,
        period: str,
        clarification_id: str,
        *,
        actor: str,
        response: str,
    ) -> dict[str, Any]:
        if not response or not response.strip():
            raise MissingReason("response é obrigatório.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_clarification')} c
                           SET state = 'RESOLVED',
                               response = %s,
                               resolved_by = %s,
                               resolved_at = now()
                          FROM {_q('closing_package_version')} v,
                               {_q('closing_package')} p
                         WHERE c.package_version_id =
                               v.package_version_id
                           AND v.package_id = p.package_id
                           AND c.clarification_id = %s
                           AND p.competence_id = %s
                        RETURNING c.clarification_id, c.state,
                                  c.opened_by, v.package_version_id,
                                  p.recipient_area
                        """,
                        (
                            response,
                            actor,
                            clarification_id,
                            competence_id,
                        ),
                    )
                    row = cur.fetchone()
                    if row is None:
                        raise ClarificationNotFound(
                            "Clarification não encontrada."
                        )
                    self._require_no_terminal_rejection(
                        cur, competence_id
                    )
                    self._audit(
                        cur,
                        entity_type="closing_clarification",
                        entity_id=clarification_id,
                        competence_id=competence_id,
                        event_type="CLARIFICATION_RESOLVED",
                        actor=actor,
                        detail={"response": response},
                    )
                    self._emit_outbox(
                        cur,
                        competence_id,
                        event_type="PACKAGE_CLARIFICATION_RESOLVED",
                        recipients={row["opened_by"]},
                        payload={
                            "package_version_id": str(
                                row["package_version_id"]
                            ),
                            "recipient_area": row["recipient_area"],
                            "period": period,
                            "clarification_id": str(
                                row["clarification_id"]
                            ),
                        },
                        actor=actor,
                    )
                    return row

    # -- rejeição terminal (DEC-01/02) -------------------------------------

    def confirm_terminal_rejection(
        self,
        period: str,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        if not reason or not reason.strip():
            raise MissingReason("Rejeição terminal exige motivo.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    coordinators = [
                        a
                        for a in self._assignments(
                            cur, competence_id, subject=actor
                        )
                        if a["role"] == "COORDINATOR"
                    ]
                    if not coordinators:
                        raise CoordinatorRequired(
                            "Rejeição terminal exige COORDINATOR ativo "
                            "com vínculo operacional (DEC-01)."
                        )
                    existing = self._terminal_rejection(
                        cur, competence_id
                    )
                    if existing and existing["state"] == "ACTIVE":
                        raise TerminalRejectionActive(
                            "Competência já possui rejeição terminal."
                        )
                    if existing:
                        cur.execute(
                            f"""
                            UPDATE {_q('closing_terminal_rejection')}
                               SET state = 'ACTIVE',
                                   reason = %s,
                                   confirmed_by = %s,
                                   confirmed_at = now(),
                                   reverted_by = NULL,
                                   reverted_at = NULL,
                                   revert_reason = NULL
                             WHERE competence_id = %s
                            RETURNING rejection_id, state, reason,
                                      confirmed_by, confirmed_at
                            """,
                            (reason, actor, competence_id),
                        )
                    else:
                        cur.execute(
                            f"""
                            INSERT INTO
                              {_q('closing_terminal_rejection')}
                                (competence_id, reason, confirmed_by)
                            VALUES (%s, %s, %s)
                            RETURNING rejection_id, state, reason,
                                      confirmed_by, confirmed_at
                            """,
                            (competence_id, reason, actor),
                        )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_terminal_rejection",
                        entity_id=row["rejection_id"],
                        competence_id=competence_id,
                        event_type="COMPETENCE_TERMINALLY_REJECTED",
                        actor=actor,
                        detail={"reason": reason},
                    )
                    self._emit_outbox(
                        cur,
                        competence_id,
                        event_type="COMPETENCE_TERMINALLY_REJECTED",
                        recipients=self._competence_recipients(
                            cur, competence_id
                        ),
                        payload={"period": period},
                        actor=actor,
                    )
                    return row

    def revert_terminal_rejection(
        self,
        period: str,
        *,
        actor: str,
        reason: str,
    ) -> dict[str, Any]:
        """Retorno autorizado para correção (DEC-02)."""
        if not reason or not reason.strip():
            raise MissingReason("Reversão exige motivo.")
        with self._conn() as conn:
            with conn.transaction():
                with conn.cursor(row_factory=dict_row) as cur:
                    competence_id = self._competence_id(cur, period)
                    coordinators = [
                        a
                        for a in self._assignments(
                            cur, competence_id, subject=actor
                        )
                        if a["role"] == "COORDINATOR"
                    ]
                    if not coordinators:
                        raise CoordinatorRequired(
                            "Reversão exige COORDINATOR ativo (DEC-01)."
                        )
                    existing = self._terminal_rejection(
                        cur, competence_id
                    )
                    if existing is None or existing["state"] != "ACTIVE":
                        raise TerminalRejectionNotFound(
                            "Sem rejeição terminal ativa."
                        )
                    cur.execute(
                        f"""
                        UPDATE {_q('closing_terminal_rejection')}
                           SET state = 'REVERTED',
                               reverted_by = %s,
                               reverted_at = now(),
                               revert_reason = %s
                         WHERE competence_id = %s
                        RETURNING rejection_id, state
                        """,
                        (actor, reason, competence_id),
                    )
                    row = cur.fetchone()
                    self._audit(
                        cur,
                        entity_type="closing_terminal_rejection",
                        entity_id=row["rejection_id"],
                        competence_id=competence_id,
                        event_type="COMPETENCE_REJECTION_REVERTED",
                        actor=actor,
                        detail={"reason": reason},
                    )
                    self._emit_outbox(
                        cur,
                        competence_id,
                        event_type="COMPETENCE_REJECTION_REVERTED",
                        recipients=self._competence_recipients(
                            cur, competence_id
                        ),
                        payload={"period": period},
                        actor=actor,
                    )
                    return row

    # -- conclusão mensal C2 (derivada — nunca forçável) -------------------

    def derive_closing_state(self, period: str) -> dict[str, Any]:
        """C2 aprovado + controle P3 oficial:

        ALL_APPLICABLE_PACKAGES SUBMITTED
        AND per-package: required_areas non-empty, cada área com aceite
        humano real na versão vigente, zero clarification OPEN
        AND zero rejeição terminal ACTIVE
        AND todo domínio P3 aplicável com proveniência OFFICIAL
        => MONTHLY_CLOSING_COMPLETED (senão PENDING com motivos).
        """
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            blocking: list[str] = []
            rejection = self._terminal_rejection(cur, competence_id)
            if rejection and rejection["state"] == "ACTIVE":
                return {
                    "period": period,
                    "state": "TERMINALLY_REJECTED",
                    "terminal_rejection": rejection,
                    "blocking_reasons": ["terminal_rejection_active"],
                    "packages": [],
                }
            areas = self._applicable_areas(cur, competence_id)
            if not areas:
                # Vacuidade nunca conclui: competência sem nenhum
                # pacote aplicável não fecha por ausência de bloqueios.
                blocking.append("no_applicable_packages")
            packages = self._package_rows(cur, competence_id)
            package_states: list[dict[str, Any]] = []
            for area in areas:
                package = packages.get(area)
                view = self._package_view(
                    cur, competence_id, package, area
                )
                package_states.append(view)
                latest = view["current_version"]
                if latest is None or latest["status"] != "SUBMITTED":
                    blocking.append(f"package_not_submitted:{area}")
                    continue
                required = latest.get("required_areas") or []
                decisions = view["area_decisions"]
                clarif_open = view["open_clarifications"]
                if not required:
                    blocking.append(
                        f"no_required_areas:{area}"
                    )
                for req in required:
                    d = decisions.get(req)
                    if d is None:
                        blocking.append(
                            f"area_not_reviewed:{area}:{req}"
                        )
                    elif d["outcome"] != "ACCEPTED":
                        blocking.append(
                            f"area_not_accepted:{area}:{req}"
                        )
                if clarif_open:
                    blocking.append(
                        f"open_clarification:{area}"
                    )
            # Controle B/C: conclusão exige P3 vigente E oficial.
            # `blockers` do P3 cobrem cutoff, revalidação vigente
            # (fingerprint), disponibilidade de fonte e divergência
            # monetária — `STOCK_CLOSED` canônico não mascara inputs
            # alterados/indisponíveis (estado de estoque != conclusão).
            # `provenance_kind` separa conciliação registrada de
            # resultado oficial comprovado.
            p3_state = ClosingP3Repository().get_p3_state(period)
            for p3_blocker in p3_state["blockers"]:
                blocking.append(f"p3_{p3_blocker}")
            for recon in p3_state["reconciliations"]:
                kind = recon.get("provenance_kind")
                if kind is None:
                    blocking.append(
                        f"p3_reconciliation_missing:{recon['domain']}"
                    )
                elif kind != "OFFICIAL":
                    blocking.append(
                        f"p3_declared_only:{recon['domain']}"
                    )
            return {
                "period": period,
                "state": (
                    "MONTHLY_CLOSING_COMPLETED"
                    if not blocking
                    else "PENDING"
                ),
                "blocking_reasons": blocking,
                "packages": package_states,
                "terminal_rejection": None,
            }

    # -- cockpit agregado (C4) ----------------------------------------------

    def get_cockpit(self, period: str) -> dict[str, Any]:
        """Composição read-only dos estados reais P2/P3/P4/P5 — nunca
        verde falso: fonte indisponível aparece como blocker, não como
        sucesso."""
        with self._conn() as conn, conn.cursor(row_factory=dict_row) as cur:
            competence_id = self._competence_id(cur, period)
            cur.execute(
                f"""
                SELECT state, COUNT(*) AS n
                  FROM {_q('competence_checklist_item')}
                 WHERE competence_id = %s
                 GROUP BY state
                """,
                (competence_id,),
            )
            checklist = {r["state"]: r["n"] for r in cur.fetchall()}
            cutoff = None
            cur.execute(
                f"""
                SELECT cutoff_id, confirmed_at, confirmed_by
                  FROM {_q('closing_cutoff')}
                 WHERE competence_id = %s
                """,
                (competence_id,),
            )
            cutoff = cur.fetchone()
            cur.execute(
                f"""
                SELECT domain, source_state, expected_amount::text,
                       reported_amount::text, provenance_kind,
                       official_document_id
                  FROM {_q('closing_reconciliation')}
                 WHERE competence_id = %s
                """,
                (competence_id,),
            )
            recons = {r["domain"]: r for r in cur.fetchall()}
            p3_domains = []
            for domain in RECONCILIATION_DOMAINS:
                row = recons.get(domain)
                divergence = None
                if (
                    row
                    and row["source_state"] == "AVAILABLE"
                    and row["expected_amount"] is not None
                    and row["reported_amount"] is not None
                ):
                    divergence = str(
                        Decimal(row["reported_amount"])
                        - Decimal(row["expected_amount"])
                    )
                p3_domains.append(
                    {
                        "domain": domain,
                        "source_state": (
                            row["source_state"]
                            if row
                            else "UNAVAILABLE"
                        ),
                        "provenance_kind": (
                            row["provenance_kind"] if row else None
                        ),
                        "divergence": divergence,
                    }
                )
            cur.execute(
                f"""
                SELECT state, COUNT(*) AS n
                  FROM {_q('closing_pendency')}
                 WHERE competence_id = %s
                 GROUP BY state
                """,
                (competence_id,),
            )
            p4 = {r["state"]: r["n"] for r in cur.fetchall()}
        closing = self.derive_closing_state(period)
        return {
            "period": period,
            "checklist": checklist,
            "p3": {
                "cutoff_confirmed": cutoff is not None,
                "domains": p3_domains,
            },
            "p4_pendencies": p4,
            "closing": closing,
        }
