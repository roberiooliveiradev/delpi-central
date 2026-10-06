"""Histórico de produtos da NF-e sem código Delpi — observação, não validação."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.application.security import api_delpi_permissions as perms
from app.application.services.lancamento_notas_fiscais.danfe_storage import (
    LancamentoDanfeStorage,
)
from app.application.services.lancamento_notas_fiscais.received_invoice_attachment_service import (
    ReceivedInvoiceAttachmentService,
)
from app.application.services.lancamento_notas_fiscais.unmapped_supplier_product_service import (
    UnmappedSupplierProductRecorder,
    unmapped_product_rows,
)
from app.application.use_cases.lancamento_notas_fiscais.invoice_posting_use_cases import (
    Actor,
)
from app.domain.services.lancamento_notas_fiscais.exceptions import (
    InvoicePostingErpQueryError,
)

DOCUMENT_ID = "aabbccddeeff001122334455"
ACCESS_KEY = "3" * 44
PDF = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"

_CONTEXT = {
    "request_id": "req-1",
    "branch_code": "01",
    "supplier_code": "000006",
    "supplier_store": "01",
    "supplier_name": "Tramar",
    "document_number": "000012078",
    "series": "1",
}


def _item(code: str, status: str, **extra):
    return {
        "supplierProductCode": code,
        "supplierProductDescription": extra.get("description", "Parafuso"),
        "quantity": extra.get("quantity", "4"),
        "unit": extra.get("unit", "PC"),
        "mappingStatus": status,
        "internalProductCode": extra.get("internal"),
    }


def _detail(state: str, items: list[dict]) -> dict:
    return {"productMapping": {"state": state}, "items": items}


def test_rows_keep_unmapped_and_ambiguous_and_drop_mapped() -> None:
    rows = unmapped_product_rows(
        _detail(
            "ready",
            [
                _item("REF-1", "unmapped"),
                _item("REF-2", "ambiguous"),
                _item("REF-3", "mapped", internal="10080001"),
                _item("   ", "unmapped"),
            ],
        ),
        **_CONTEXT,
    )
    assert [row["supplier_product_code"] for row in rows] == ["REF-1", "REF-2"]
    assert [row["mapping_status"] for row in rows] == ["unmapped", "ambiguous"]
    assert rows[0]["supplier_code"] == "000006"
    assert rows[0]["quantity"] == 4


def test_rows_ignore_mapping_that_was_not_consulted() -> None:
    for state in ("issuer_mismatch", "supplier_required"):
        assert (
            unmapped_product_rows(
                _detail(state, [_item("REF-1", "unmapped")]),
                **_CONTEXT,
            )
            == []
        )


def test_all_mapped_invoice_records_nothing() -> None:
    requests = SimpleNamespace(insert_unmapped_supplier_products=lambda rows: len(rows))
    items = SimpleNamespace(
        execute=lambda **_kwargs: _detail("ready", [_item("REF-3", "mapped", internal="10080001")])
    )
    with patch(
        "app.application.services.lancamento_notas_fiscais.unmapped_supplier_product_service.notify_unmapped_supplier_products"
    ) as notify:
        UnmappedSupplierProductRecorder(items=items, requests=requests).record(
            authorization="Bearer t",
            document_id=DOCUMENT_ID,
            provider_entity_id="c" * 24,
            access_key=ACCESS_KEY,
            branch="01",
            supplier_code="000006",
            supplier_store="01",
            supplier_name="Tramar",
            document_number="000012078",
            series="1",
            request_id="req-1",
        )
    assert notify.called is False


def test_recorder_persists_unlinked_items_and_notifies_once() -> None:
    saved: list[list[dict]] = []

    def insert(rows):
        saved.append(rows)
        return len(rows)

    items = SimpleNamespace(
        execute=lambda **_kwargs: _detail(
            "ready",
            [
                _item("REF-1", "unmapped"),
                _item("REF-2", "ambiguous", description="Porca"),
                _item("REF-3", "mapped", internal="10080001"),
            ],
        )
    )
    with patch(
        "app.application.services.lancamento_notas_fiscais.unmapped_supplier_product_service.notify_unmapped_supplier_products",
        return_value=True,
    ) as notify:
        UnmappedSupplierProductRecorder(
            items=items,
            requests=SimpleNamespace(insert_unmapped_supplier_products=insert),
        ).record(
            authorization="Bearer t",
            document_id=DOCUMENT_ID,
            provider_entity_id="c" * 24,
            access_key=ACCESS_KEY,
            branch="01",
            supplier_code="000006",
            supplier_store="01",
            supplier_name="Tramar",
            document_number="000012078",
            series="1",
            request_id="req-1",
        )
    assert [row["supplier_product_code"] for row in saved[0]] == ["REF-1", "REF-2"]
    assert notify.call_args.kwargs["product_count"] == 2
    assert notify.call_args.kwargs["request_id"] == "req-1"


def test_sa5_failure_does_not_raise_or_notify() -> None:
    def execute(**_kwargs):
        raise InvoicePostingErpQueryError("Não foi possível consultar a relação Produto x Fornecedor.")

    inserted = []
    with patch(
        "app.application.services.lancamento_notas_fiscais.unmapped_supplier_product_service.notify_unmapped_supplier_products"
    ) as notify:
        UnmappedSupplierProductRecorder(
            items=SimpleNamespace(execute=execute),
            requests=SimpleNamespace(
                insert_unmapped_supplier_products=lambda rows: inserted.append(rows)
            ),
        ).record(
            authorization="Bearer t",
            document_id=DOCUMENT_ID,
            provider_entity_id="c" * 24,
            access_key=ACCESS_KEY,
            branch="01",
            supplier_code="000006",
            supplier_store="01",
            supplier_name="Tramar",
            document_number="000012078",
            series="1",
            request_id="req-1",
        )
    assert inserted == []
    assert notify.called is False


def test_insert_failure_does_not_notify() -> None:
    def insert(_rows):
        raise RuntimeError("db")

    items = SimpleNamespace(execute=lambda **_kwargs: _detail("ready", [_item("REF-1", "unmapped")]))
    with patch(
        "app.application.services.lancamento_notas_fiscais.unmapped_supplier_product_service.notify_unmapped_supplier_products"
    ) as notify:
        UnmappedSupplierProductRecorder(
            items=items,
            requests=SimpleNamespace(insert_unmapped_supplier_products=insert),
        ).record(
            authorization="Bearer t",
            document_id=DOCUMENT_ID,
            provider_entity_id="c" * 24,
            access_key=ACCESS_KEY,
            branch="01",
            supplier_code="000006",
            supplier_store="01",
            supplier_name="Tramar",
            document_number="000012078",
            series="1",
            request_id="req-1",
        )
    assert notify.called is False


class _Requests:
    def __init__(self) -> None:
        self.inserted = None

    def insert_danfe_attachment(self, **kwargs) -> None:
        self.inserted = kwargs


class _Create:
    def execute(self, _payload, _actor):
        return {
            "id": str(uuid4()),
            "document_number": "000012078",
            "series": "1",
            "branch_code": "01",
            "supplier_code": "000006",
            "supplier_store": "01",
            "supplier_name": "Tramar",
        }


class _Recorder:
    def __init__(self, fail: bool = False) -> None:
        self.calls: list[dict] = []
        self.fail = fail

    def record(self, **kwargs) -> None:
        if self.fail:
            raise RuntimeError("observação")
        self.calls.append(kwargs)


def _actor() -> Actor:
    return Actor(user_id="u1", user_name="Ana", has_create=True)


def test_nfe_create_observes_after_success(tmp_path) -> None:
    recorder = _Recorder()
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_danfe=lambda **_kwargs: (PDF, "NFe.pdf")),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=_Requests(),
        unmapped_products=recorder,
    )
    created = service.execute(
        {
            "source": "received_nfe",
            "branch_code": "01",
            "source_branch": "01",
            "document_id": DOCUMENT_ID,
            "access_key": ACCESS_KEY,
            "supplier_code": "000006",
            "supplier_store": "01",
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    assert created["danfe"]["available"] is True
    assert len(recorder.calls) == 1
    assert recorder.calls[0]["supplier_code"] == "000006"
    assert recorder.calls[0]["request_id"] == created["id"]


def test_observation_failure_keeps_the_request(tmp_path) -> None:
    service = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(download_danfe=lambda **_kwargs: (PDF, "NFe.pdf")),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=_Requests(),
        unmapped_products=_Recorder(fail=True),
    )
    created = service.execute(
        {
            "source": "received_nfe",
            "branch_code": "01",
            "source_branch": "01",
            "document_id": DOCUMENT_ID,
            "access_key": ACCESS_KEY,
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    assert created["id"]


def test_manual_nfse_and_cte_do_not_observe(tmp_path) -> None:
    from app.application.services.lancamento_notas_fiscais.fiscal_attachment_storage import (
        LancamentoFiscalAttachmentStorage,
    )
    from tests.test_lancamento_notas_fiscais_received_invoices import (
        CTE_DETAIL,
        CTE_XML,
        NFSE_ID,
        XML,
        _cte_payload,
    )

    recorder = _Recorder()
    requests = _Requests()
    requests.fiscal = []
    requests.insert_fiscal_attachment = lambda **kwargs: requests.fiscal.append(kwargs)
    manual = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(),
        storage=LancamentoDanfeStorage(str(tmp_path)),
        requests=requests,
        unmapped_products=recorder,
    )
    manual.execute({"source": "manual"}, _actor(), authorization="")
    nfse = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(
            download_nfse_xml=lambda **_kwargs: (XML, "NFSe.xml"),
        ),
        storage=LancamentoDanfeStorage(str(tmp_path / "nfse")),
        fiscal_storage=LancamentoFiscalAttachmentStorage(str(tmp_path / "nfse")),
        requests=requests,
        unmapped_products=recorder,
    )
    nfse.execute(
        {
            "source": "questor",
            "source_document_type": "nfse",
            "fiscal_model": "nfse",
            "branch_code": "02",
            "source_branch": "02",
            "document_id": NFSE_ID,
            "provider_document_number": "2600000002224",
            "document_number": "000002224",
        },
        _actor(),
        authorization="Bearer user-jwt",
    )
    cte = ReceivedInvoiceAttachmentService(
        create_request=_Create(),
        gateway=SimpleNamespace(
            get_cte_detail=lambda **_kwargs: CTE_DETAIL,
            download_cte_xml=lambda **_kwargs: (CTE_XML, "CTe.xml"),
            download_dacte=lambda **_kwargs: (PDF, "CTe.pdf"),
        ),
        storage=LancamentoDanfeStorage(str(tmp_path / "cte")),
        fiscal_storage=LancamentoFiscalAttachmentStorage(str(tmp_path / "cte")),
        requests=requests,
        unmapped_products=recorder,
    )
    cte.execute(_cte_payload(), _actor(), authorization="Bearer user-jwt")
    assert recorder.calls == []


def test_list_route_forbidden_without_review_permission() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        list_unmapped_products,
    )

    user = SimpleNamespace(
        id="u1",
        name="Ana",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_MANAGE],
        rbac_unavailable=False,
    )
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user), patch(
        "delpi_auth.authorization.has_permission",
        side_effect=lambda current, code: code in getattr(current, "permissions", []),
    ):
        with pytest.raises(Exception, match="Forbidden"):
            list_unmapped_products(
                supplier=None,
                product_code=None,
                branch=None,
                mapping_status=None,
                request_id=None,
                page=1,
                page_size=20,
            )


def test_list_route_uses_review_permission() -> None:
    from app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router import (
        list_unmapped_products,
    )

    user = SimpleNamespace(
        id="u1",
        name="Ana",
        is_superadmin=False,
        permissions=[perms.LANCAMENTO_NOTAS_FISCAIS_REVIEW_UNMAPPED_PRODUCTS],
        rbac_unavailable=False,
    )
    listed = {
        "items": [{"supplier_product_code": "REF-1"}],
        "page": 1,
        "page_size": 20,
        "total": 1,
        "total_pages": 1,
    }
    with patch("delpi_auth.authorization.resolve_user_context", return_value=user), patch(
        "delpi_auth.authorization.has_permission",
        side_effect=lambda current, code: code in getattr(current, "permissions", []),
    ), patch(
        "app.interface.http.routes.lancamento_notas_fiscais.lancamento_notas_fiscais_router.build_list_unmapped_supplier_products_use_case"
    ) as build:
        build.return_value.execute.return_value = listed
        response = list_unmapped_products(
            supplier="Tramar",
            product_code="REF",
            branch="01",
            mapping_status="unmapped",
            request_id="11111111-1111-1111-1111-111111111111",
            page=1,
            page_size=20,
        )
    assert response.status_code == 200
    filters = build.return_value.execute.call_args.kwargs["filters"]
    assert filters["mapping_status"] == "unmapped"
    assert filters["branch"] == "01"
    assert filters["product_code"] == "REF"
