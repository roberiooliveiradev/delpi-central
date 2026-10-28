"""Caso de uso DRE-019 — projeção documental do destinatário externo.

Cadeia de autorização por request (capability AND vínculo AND release —
fail-closed em qualquer elo):

1. rota exige `controllership-finance.closing-documents.read` efetivo
   (Core = authority; rbac_unavailable = 503 — ver `authz`);
2. vínculo: `closing_review_assignment` role='RECIPIENT' ativo do ator
   no pacote da competência+área destinataria;
3. liberação: versão SUBMITTED mais alta do pacote — o snapshot
   `content.items[].document_version_id` é o conjunto autorizado;
4. recurso: documento/versão pertencente ao conjunto liberado — fora
   dele é 404 (existência nunca vaza: nem do documento, nem do pacote,
   nem da competência de terceiros).

A projeção NUNCA retorna p3/p4, decisões, required_areas, ids de
pacote/version internos nem storage físico. Download usa o mesmo
storage + auditoria `DOCUMENT_DOWNLOADED` do contrato interno — a
decisão registrada é a de autorização (AUTHORIZED/DENIED/FAILED),
nunca a entrega concluída.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from controllership_finance_app.domain.closing_checklist.errors import (
    AdjustmentRequestNotFound,
    DocumentNotFound,
    InvalidMessage,
)
from controllership_finance_app.application.services.closing_document_service import (
    MESSAGE_AUDIENCE_SHARED,
    MESSAGE_MAX_CHARS,
)
from controllership_finance_app.infrastructure.persistence.closing_document_repository import (
    ClosingDocumentRepository,
)
from controllership_finance_app.infrastructure.persistence.closing_recipient_repository import (
    ClosingRecipientRepository,
)
from controllership_finance_app.infrastructure.storage.closing_document_storage import (
    ClosingDocumentStorage,
)


def _request_body_hash(*, body: str) -> str:
    canonical = json.dumps(
        {"body": body}, sort_keys=True, separators=(",", ":")
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ReceivedDocumentsService:
    """Superfície read+interação do destinatário externo (boundary DRE)."""

    def __init__(
        self,
        recipients: ClosingRecipientRepository | None = None,
        documents: ClosingDocumentRepository | None = None,
        storage: ClosingDocumentStorage | None = None,
    ) -> None:
        self._recipients = recipients or ClosingRecipientRepository()
        self._documents = documents or ClosingDocumentRepository()
        self._storage = storage or ClosingDocumentStorage()

    # -- cadeia de autorização ------------------------------------------

    def _bound_packages(self, period: str, actor: str) -> list[dict]:
        """Pacotes vinculados com entrega corrente — vínculo
        inexistente OU sem SUBMITTED = 404 (sem vazamento de
        competência/pacote alheio)."""
        packages = self._recipients.bound_packages(period, actor)
        if not packages:
            raise DocumentNotFound(
                "Nenhum fechamento disponibilizado nesta competência."
            )
        return packages

    def _released_document(
        self, period: str, document_id: str, actor: str
    ) -> tuple[str, list[dict], dict]:
        """(competence_id, bound_packages, documento_liberado) — o
        documento precisa constar do conjunto liberado CORRENTE e estar
        ATTACHED; qualquer outro caso é 404."""
        packages = self._bound_packages(period, actor)
        competence_id = str(packages[0]["competence_id"])
        document = self._recipients.released_document(
            competence_id, packages, document_id
        )
        if document is None:
            raise DocumentNotFound("Documento não encontrado.")
        return competence_id, packages, document

    @staticmethod
    def _package_ids(packages: list[dict]) -> list[str]:
        return [str(p["package_id"]) for p in packages]

    # -- leitura ---------------------------------------------------------

    def list_deliveries(self, *, actor: str) -> list[dict]:
        """«Fechamentos recebidos» — entregas correntes do ator."""
        rows = self._recipients.list_deliveries(actor)
        return [
            {
                "period": row["period"],
                "recipient_area": row["recipient_area"],
                "version_no": row["version_no"],
                "submitted_at": row["submitted_at"].isoformat()
                if row["submitted_at"]
                else None,
                "document_count": row["document_count"],
            }
            for row in rows
        ]

    def get_delivery(self, *, period: str, actor: str) -> dict:
        """Entrega da competência: metadados do envio + projeção
        documental + solicitações do próprio ator."""
        packages = self._bound_packages(period, actor)
        competence_id = str(packages[0]["competence_id"])
        documents = self._recipients.released_documents(
            competence_id, packages
        )
        requests = self._documents.list_adjustment_requests(
            competence_id,
            requester_subject=actor,
        )
        released_ids = {str(d["document_id"]) for d in documents}
        return {
            "period": period,
            "deliveries": [
                {
                    "recipient_area": p["recipient_area"],
                    "version_no": p["version_no"],
                    "submitted_at": p["submitted_at"].isoformat()
                    if p["submitted_at"]
                    else None,
                }
                for p in packages
            ],
            "documents": [
                self._document_view(row) for row in documents
            ],
            "requests": [
                self._request_view(row)
                for row in requests
                if str(row["document_id"]) in released_ids
            ],
        }

    def get_document(
        self, *, period: str, document_id: str, actor: str
    ) -> dict:
        """Detalhe do documento liberado + versões autorizadas."""
        _competence_id, packages, document = self._released_document(
            period, document_id, actor
        )
        versions = self._recipients.released_versions(
            self._package_ids(packages), document_id
        )
        return {
            "document": self._document_view(document),
            "versions": [
                {
                    "version_no": v["version_no"],
                    "state": v["state"],
                    "original_name": v["original_name"],
                    "mime_type": v["mime_type"],
                    "size_bytes": v["size_bytes"],
                    "created_at": v["created_at"].isoformat()
                    if v["created_at"]
                    else None,
                }
                for v in versions
            ],
        }

    def resolve_download(
        self,
        *,
        period: str,
        document_id: str,
        version_no: int,
        actor: str,
    ) -> tuple[Path, dict]:
        """Download de versão liberada — membership no conjunto
        autorizado é o único critério (nunca posse de ids).

        Auditoria idêntica à do contrato interno (`DOCUMENT_DOWNLOADED`
        com result AUTHORIZED/DENIED/FAILED + phase) — a decisão de
        autorização é registrada, não a entrega."""
        packages = self._bound_packages(period, actor)
        competence_id = str(packages[0]["competence_id"])
        version_file = self._recipients.version_file_if_released(
            competence_id,
            self._package_ids(packages),
            document_id,
            version_no,
        )
        if version_file is None:
            # Recurso fora do conjunto liberado OU versão inexistente:
            # mesmo 404 — DENIED só é auditável quando o documento
            # existe na competência (autorização é o motivo da recusa;
            # recurso inexistente não gera trilha de negação falsa).
            try:
                self._documents.get_document_by_id(
                    competence_id, document_id
                )
                exists_in_competence = True
            except DocumentNotFound:
                exists_in_competence = False
            if exists_in_competence:
                self._documents.audit_download(
                    competence_id=competence_id,
                    document_id=document_id,
                    version_no=version_no,
                    actor=actor,
                    result="DENIED",
                )
            raise DocumentNotFound("Documento não encontrado.")
        path = self._storage.resolve(version_file["storage_key"])
        self._documents.audit_download(
            competence_id=competence_id,
            document_id=document_id,
            version_no=version_no,
            actor=actor,
            result="AUTHORIZED",
        )
        return path, version_file

    # -- interação ---------------------------------------------------------

    def list_messages(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
        limit: int,
        offset: int,
    ) -> dict:
        """Conversa compartilhada do documento liberado — SOMENTE
        `SHARED`; INTERNAL nunca sai nesta superfície (boundary DRE)."""
        competence_id, _packages, _doc = self._released_document(
            period, document_id, actor
        )
        result = self._documents.list_document_messages(
            competence_id,
            document_id,
            audience=MESSAGE_AUDIENCE_SHARED,
            limit=limit,
            offset=offset,
        )
        for item in result["items"]:
            item["mine"] = str(item["author_subject"]) == actor
        return result

    def post_message(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
        author_name: str | None,
        body: str,
        idempotency_key: str,
    ) -> tuple[dict, bool]:
        """Mensagem do destinatário — sempre `SHARED` (a conversa do
        destinatário é, por contrato, visível à Controladoria e a outros
        destinatários do mesmo documento). Documento liberado corrente
        é pré-condição; mensagem não altera documento, pacote nem
        fechamento. Mesmo envelope idempotente de U9."""
        competence_id, _packages, document = self._released_document(
            period, document_id, actor
        )
        text = (body or "").strip()
        if not 1 <= len(text) <= MESSAGE_MAX_CHARS:
            raise InvalidMessage(
                "A mensagem deve ter entre 1 e 4000 caracteres."
            )
        key = (idempotency_key or "").strip()
        if not 1 <= len(key) <= 128:
            raise InvalidMessage(
                "idempotency_key deve ter entre 1 e 128 caracteres."
            )
        name = (author_name or "").strip()[:255] or None
        return self._documents.create_document_message(
            competence_id=competence_id,
            document_id=str(document["document_id"]),
            version_no=document["version_no"],
            audience=MESSAGE_AUDIENCE_SHARED,
            body=text,
            author_subject=actor,
            author_name=name,
            idempotency_key=key,
            request_hash=_request_body_hash(body=text),
        )

    def list_requests(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
    ) -> list[dict]:
        """Solicitações DO PRÓPRIO ator no documento liberado —
        pedidos de outros destinatários nunca são listados."""
        competence_id, _packages, _doc = self._released_document(
            period, document_id, actor
        )
        rows = self._documents.list_adjustment_requests(
            competence_id,
            document_id=document_id,
            requester_subject=actor,
        )
        return [self._request_view(row) for row in rows]

    def create_request(
        self,
        *,
        period: str,
        document_id: str,
        actor: str,
        author_name: str | None,
        body: str,
        idempotency_key: str,
    ) -> tuple[dict, bool]:
        """Solicitação de esclarecimento/revisão — registra autor,
        data, motivo e versão contextual (carimbo da versão liberada
        corrente). Abre como OPEN; a resposta interna NÃO encerra —
        conclusão somente pela confirmação do requerente."""
        competence_id, _packages, document = self._released_document(
            period, document_id, actor
        )
        text = (body or "").strip()
        if not 1 <= len(text) <= MESSAGE_MAX_CHARS:
            raise InvalidMessage(
                "A solicitação deve ter entre 1 e 4000 caracteres."
            )
        key = (idempotency_key or "").strip()
        if not 1 <= len(key) <= 128:
            raise InvalidMessage(
                "idempotency_key deve ter entre 1 e 128 caracteres."
            )
        name = (author_name or "").strip()[:255] or None
        row, created = self._documents.create_adjustment_request(
            competence_id=competence_id,
            document_id=str(document["document_id"]),
            version_no=document["version_no"],
            body=text,
            requester_subject=actor,
            requester_name=name,
            idempotency_key=key,
            request_hash=_request_body_hash(body=text),
        )
        return self._request_view(row), created

    def confirm_request(
        self,
        *,
        period: str,
        document_id: str,
        request_id: str,
        actor: str,
    ) -> dict:
        """Conclusão pelo requerente — ANSWERED → CONFIRMED (somente o
        autor; UPDATE condicional — confirmar pedido de outro ator é
        404, estado inválido é 409)."""
        competence_id, _packages, document = self._released_document(
            period, document_id, actor
        )
        request = self._documents.get_adjustment_request(
            competence_id, request_id
        )
        if request is None or str(request["document_id"]) != str(
            document["document_id"]
        ):
            raise AdjustmentRequestNotFound(
                "Solicitação não encontrada."
            )
        row = self._documents.confirm_adjustment_request(
            competence_id, request_id, confirmed_by=actor
        )
        return self._request_view(row)

    # -- views de contrato --------------------------------------------------

    @staticmethod
    def _document_view(row: dict) -> dict:
        """Contrato público do documento liberado — sem storage_key,
        idempotência, uploaded_by nem metadados internos."""
        return {
            "document_id": str(row["document_id"]),
            "item_key": row.get("item_key"),
            "item_name": row.get("item_name"),
            "recipient_area": row.get("recipient_area"),
            "title": row.get("title"),
            "link_kind": row.get("link_kind"),
            "original_name": row.get("original_name"),
            "mime_type": row.get("mime_type"),
            "size_bytes": row.get("size_bytes"),
            "version_no": row.get("version_no"),
            "released_at": row["released_at"].isoformat()
            if row.get("released_at")
            else None,
        }

    @staticmethod
    def _request_view(row: dict) -> dict:
        """Contrato público da solicitação — autoria/data do servidor,
        ciclo OPEN → ANSWERED → CONFIRMED."""
        return {
            "request_id": str(row["request_id"]),
            "document_id": str(row["document_id"]),
            "version_no": row.get("version_no"),
            "state": row["state"],
            "body": row["body"],
            "requester_subject": str(row["requester_subject"]),
            "requester_name": row.get("requester_name"),
            "answer_body": row.get("answer_body"),
            "answered_name": row.get("answered_name"),
            "answered_at": row["answered_at"].isoformat()
            if row.get("answered_at")
            else None,
            "confirmed_at": row["confirmed_at"].isoformat()
            if row.get("confirmed_at")
            else None,
            "created_at": row["created_at"].isoformat()
            if row.get("created_at")
            else None,
        }
