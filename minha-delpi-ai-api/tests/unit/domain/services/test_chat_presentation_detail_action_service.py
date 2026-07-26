from app.composition.content_composer import configure_domain_infrastructure_ports

configure_domain_infrastructure_ports()

from app.domain.services.chat_presentation_detail_action_service import (
    ChatPresentationDetailActionService,
)
from app.domain.services.chat_presentation_supplier_display_service import (
    ChatPresentationSupplierDisplayService,
)


def test_supplier_display_formats_name_and_store():
    label = ChatPresentationSupplierDisplayService.format_supplier_label(
        supplier_code="000002",
        supplier_name="TE CONNECTIVITY BRASIL IND DE ELET LTDA",
        supplier_store="01",
    )

    assert "000002" in label
    assert "TE CONNECTIVITY" in label
    assert "loja 01" in label


def test_detect_supplier_detail_plan():
    plan = ChatPresentationDetailActionService.detect_plan(
        "detalhe fornecedor 000002 loja 01 do produto 10080001",
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "arguments": {
                                "parameters": {
                                    "code": "10080001",
                                    "start_date": "20250101",
                                    "date_end_exclusive": "20260701",
                                }
                            },
                            "metadata": {
                                "ok": True,
                                "path": "/products/10080001/purchase-budget-history",
                            },
                        }
                    ]
                },
            }
        ],
    )

    assert plan is not None
    assert plan.kind == "supplier_detail"
    assert plan.product_code == "10080001"
    assert plan.path_fragment == "/suppliers"
    assert plan.detail_filter == {
        "supplier_code": "000002",
        "supplier_store": "01",
    }


def test_detect_purchase_record_detail_plan():
    plan = ChatPresentationDetailActionService.detect_plan(
        "detalhe documento 041446 origem SC1010 do produto 10080001",
        previous_messages=[
            {
                "role": "assistant",
                "metadata": {
                    "toolCalls": [
                        {
                            "name": "execute_external_action",
                            "metadata": {
                                "ok": True,
                                "path": "/products/10080001/purchase-budget-history",
                            },
                        }
                    ]
                },
            }
        ],
    )

    assert plan is not None
    assert plan.kind == "purchase_record_detail"
    assert plan.path_fragment == "/purchase-budget-history"
    assert plan.detail_filter == {
        "document_number": "041446",
        "source": "sc1010",
    }
