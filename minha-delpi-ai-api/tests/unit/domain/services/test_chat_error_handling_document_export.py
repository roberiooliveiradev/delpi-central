"""downloadArtifacts é evidência de resultado — nunca classificar como empty_result."""

from app.domain.services.chat_error_handling_classifier import (
    ChatErrorHandlingClassifier,
)


def _document_export_tool_call() -> dict:
    return {
        "name": "execute_external_action",
        "metadata": {
            "ok": True,
            "statusCode": 200,
            "path": "/products/90261757/structure/excel",
            "apiDelpiResponseMeta": {
                "operationId": "get_product_structure_excel",
                "entity": "product_structure_excel",
                "shape": "document_export",
            },
            "downloadArtifacts": [
                {
                    "href": "/apps/api-delpi/products/90261757/structure/excel?format=xlsx",
                    "filename": "Estrutura_90261757.xlsx",
                    "label": "Baixar Estrutura_90261757.xlsx",
                }
            ],
        },
    }


def test_download_artifact_prevents_empty_result_classification():
    classification = ChatErrorHandlingClassifier.classify(
        message="Baixe a estrutura em Excel do produto 90261757.",
        answer="A consulta não retornou registros.",
        tool_calls=[_document_export_tool_call()],
    )

    assert classification is None


def test_download_artifact_counts_as_presentation_evidence():
    assert ChatErrorHandlingClassifier._tool_calls_have_presentation_evidence(
        [_document_export_tool_call()]
    )
