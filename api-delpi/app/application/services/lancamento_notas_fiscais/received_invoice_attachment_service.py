"""Cria a solicitação e, quando a origem é uma NF-e, anexa o DANFE já baixado."""
from __future__ import annotations

from typing import Any

from app.application.services.lancamento_notas_fiscais.danfe_storage import (
    LancamentoDanfeStorage,
    LancamentoDanfeStorageError,
)
from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
    CreateInvoicePostingRequestUseCase,
)
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    InvoicePostingUpstreamError,
    InvoicePostingValidationError,
)
from app.infrastructure.gateways.financial_received_invoice_gateway import (
    FinancialReceivedInvoiceGateway,
    FinancialReceivedInvoiceGatewayError,
)
from app.utils.logger import log_error


class ReceivedInvoiceAttachmentService:
    def __init__(
        self,
        *,
        create_request: CreateInvoicePostingRequestUseCase,
        gateway: FinancialReceivedInvoiceGateway,
        storage: LancamentoDanfeStorage,
        requests: Any,
    ) -> None:
        self._create_request = create_request
        self._gateway = gateway
        self._storage = storage
        self._requests = requests

    def execute(
        self,
        payload: dict[str, Any],
        actor: Actor,
        *,
        authorization: str,
    ) -> dict[str, Any]:
        source = str(payload.get("source") or "manual").strip() or "manual"
        if source == "manual":
            return self._create_request.execute(payload, actor)
        if source != "received_nfe":
            raise InvoicePostingValidationError("Origem da solicitação inválida.")
        fiscal_model = str(payload.get("fiscal_model") or "").strip().lower().replace(" ", "")
        if fiscal_model in {"cte", "ct-e"}:
            raise InvoicePostingValidationError("CT-e não anexa o DANFE de uma NF-e.")

        document_id = str(payload.get("document_id") or "").strip()
        access_key = str(payload.get("access_key") or "").strip()
        source_branch = str(payload.get("source_branch") or "").strip()
        request_branch = str(payload.get("branch_code") or payload.get("branch") or "").strip()
        if source_branch not in {"01", "02"}:
            raise InvoicePostingValidationError("Informe a filial de origem da nota fiscal.")
        if source_branch != request_branch:
            raise InvoicePostingValidationError(
                "A nota fiscal pertence a outra filial e não pode ser lançada nesta solicitação."
            )
        content, filename = self._gateway.download_danfe(
            authorization=authorization,
            document_id=document_id,
            access_key=access_key,
            branch=source_branch,
        )
        created = self._create_request.execute(payload, actor)
        request_id = str(created.get("id") or "")
        stored_name: str | None = None
        try:
            stored_name = self._storage.save(request_id=request_id, content=content)
            self._requests.insert_danfe_attachment(
                request_id=request_id,
                document_id=document_id.lower(),
                access_key=access_key,
                stored_name=stored_name,
                original_name=filename,
                size_bytes=len(content),
            )
        except (LancamentoDanfeStorageError, FinancialReceivedInvoiceGatewayError, OSError) as exc:
            self._compensate(request_id, stored_name)
            raise InvoicePostingUpstreamError("Não foi possível anexar o DANFE.") from exc
        except Exception as exc:
            self._compensate(request_id, stored_name)
            log_error(f"Falha ao anexar DANFE da solicitação {request_id}: {type(exc).__name__}")
            raise InvoicePostingUpstreamError("Não foi possível anexar o DANFE.") from exc
        created["danfe"] = {
            "available": True,
            "document_id": document_id.lower(),
            "access_key": access_key,
            "file_name": filename,
            "size_bytes": len(content),
        }
        return created

    def _compensate(self, request_id: str, stored_name: str | None) -> None:
        if stored_name:
            try:
                self._storage.delete(stored_name)
            except OSError:
                log_error(f"Falha ao remover DANFE órfão da solicitação {request_id}.")
        try:
            self._requests.delete_request(request_id)
        except Exception as exc:  # noqa: BLE001
            log_error(
                f"Falha ao desfazer solicitação {request_id} sem DANFE: {type(exc).__name__}"
            )
