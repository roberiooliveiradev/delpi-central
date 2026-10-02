"""Cria a solicitação e, quando a origem é uma NF-e, anexa o DANFE já baixado."""
from __future__ import annotations

from typing import Any

from app.application.services.lancamento_notas_fiscais.danfe_storage import (
    LancamentoDanfeStorage,
    LancamentoDanfeStorageError,
)
from app.application.services.lancamento_notas_fiscais.fiscal_attachment_storage import (
    LancamentoFiscalAttachmentStorage,
    LancamentoFiscalAttachmentStorageError,
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
        fiscal_storage: LancamentoFiscalAttachmentStorage | None = None,
    ) -> None:
        self._create_request = create_request
        self._gateway = gateway
        self._storage = storage
        self._requests = requests
        self._fiscal_storage = fiscal_storage or LancamentoFiscalAttachmentStorage(str(storage.base_dir))

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
        if source == "received_nfe":
            return self._attach_received_nfe(payload, actor, authorization=authorization)
        if source == "questor":
            return self._attach_questor_nfse(payload, actor, authorization=authorization)
        raise InvoicePostingValidationError("Origem da solicitação inválida.")

    def _attach_received_nfe(
        self,
        payload: dict[str, Any],
        actor: Actor,
        *,
        authorization: str,
    ) -> dict[str, Any]:
        fiscal_model = _normalized_model(payload.get("fiscal_model"))
        if fiscal_model in {"cte", "ct-e"}:
            raise InvoicePostingValidationError("CT-e não anexa o DANFE de uma NF-e.")
        if fiscal_model == "nfse":
            raise InvoicePostingValidationError("NFS-e não usa o anexo de DANFE.")
        declared = _normalized_model(payload.get("source_document_type"))
        if declared and declared != "nfe":
            raise InvoicePostingValidationError("O tipo do documento de origem não confere com a solicitação.")
        if fiscal_model and fiscal_model != "nfe":
            raise InvoicePostingValidationError("O tipo do documento de origem não confere com a solicitação.")
        document_id = str(payload.get("document_id") or "").strip()
        access_key = str(payload.get("access_key") or "").strip()
        source_branch = _matching_branch(payload)
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
            self._compensate_danfe(request_id, stored_name)
            raise InvoicePostingUpstreamError("Não foi possível anexar o DANFE.") from exc
        except Exception as exc:
            self._compensate_danfe(request_id, stored_name)
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

    def _attach_questor_nfse(
        self,
        payload: dict[str, Any],
        actor: Actor,
        *,
        authorization: str,
    ) -> dict[str, Any]:
        fiscal_model = _normalized_model(payload.get("fiscal_model"))
        source_type = _normalized_model(payload.get("source_document_type")) or "nfse"
        if fiscal_model != "nfse" or source_type != "nfse":
            raise InvoicePostingValidationError("O tipo do documento de origem não confere com a solicitação.")
        document_id = str(payload.get("document_id") or payload.get("source_document_id") or "").strip()
        source_branch = _matching_branch(payload)
        provider_number = str(payload.get("provider_document_number") or "").strip()
        original, original_name = self._gateway.download_nfse_xml(
            authorization=authorization,
            document_id=document_id,
            variant="original",
            branch=source_branch,
        )
        standard, standard_name = self._gateway.download_nfse_xml(
            authorization=authorization,
            document_id=document_id,
            variant="standard",
            branch=source_branch,
        )
        created = self._create_request.execute(payload, actor)
        request_id = str(created.get("id") or "")
        stored: list[str] = []
        public: list[dict[str, Any]] = []
        try:
            for attachment_type, content, filename in (
                ("xml_original", original, original_name),
                ("xml_standard", standard, standard_name),
            ):
                stored_name = self._fiscal_storage.save(
                    request_id=request_id,
                    attachment_type=attachment_type,
                    content=content,
                )
                stored.append(stored_name)
                self._requests.insert_fiscal_attachment(
                    request_id=request_id,
                    document_type="nfse",
                    attachment_type=attachment_type,
                    provider_document_id=document_id.lower(),
                    provider_document_number=provider_number,
                    provider_document_key=None,
                    branch_code=source_branch,
                    stored_name=stored_name,
                    original_name=filename,
                    content_type="text/xml",
                    size_bytes=len(content),
                )
                public.append(
                    {
                        "document_type": "nfse",
                        "attachment_type": attachment_type,
                        "provider_document_id": document_id.lower(),
                        "provider_document_number": provider_number,
                        "branch_code": source_branch,
                        "file_name": filename,
                        "content_type": "text/xml",
                        "size_bytes": len(content),
                    }
                )
        except (
            LancamentoFiscalAttachmentStorageError,
            FinancialReceivedInvoiceGatewayError,
            OSError,
        ) as exc:
            self._compensate_fiscal(request_id, stored)
            raise InvoicePostingUpstreamError("Não foi possível anexar o XML da NFS-e.") from exc
        except Exception as exc:
            self._compensate_fiscal(request_id, stored)
            log_error(f"Falha ao anexar XML da solicitação {request_id}: {type(exc).__name__}")
            raise InvoicePostingUpstreamError("Não foi possível anexar o XML da NFS-e.") from exc
        created["fiscal_attachments"] = public
        return created

    def _compensate_danfe(self, request_id: str, stored_name: str | None) -> None:
        if stored_name:
            try:
                self._storage.delete(stored_name)
            except OSError:
                log_error(f"Falha ao remover DANFE órfão da solicitação {request_id}.")
        self._delete_request(request_id)

    def _compensate_fiscal(self, request_id: str, stored_names: list[str]) -> None:
        for stored_name in stored_names:
            try:
                self._fiscal_storage.delete(stored_name)
            except OSError:
                log_error(f"Falha ao remover XML órfão da solicitação {request_id}.")
        self._delete_request(request_id)

    def _delete_request(self, request_id: str) -> None:
        try:
            self._requests.delete_request(request_id)
        except Exception as exc:  # noqa: BLE001
            log_error(f"Falha ao desfazer solicitação {request_id} sem anexo: {type(exc).__name__}")


def _normalized_model(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "").replace("-", "")


def _matching_branch(payload: dict[str, Any]) -> str:
    source_branch = str(payload.get("source_branch") or "").strip()
    request_branch = str(payload.get("branch_code") or payload.get("branch") or "").strip()
    if source_branch not in {"01", "02"}:
        raise InvoicePostingValidationError("Informe a filial de origem da nota fiscal.")
    if source_branch != request_branch:
        raise InvoicePostingValidationError(
            "A nota fiscal pertence a outra filial e não pode ser lançada nesta solicitação."
        )
    return source_branch
