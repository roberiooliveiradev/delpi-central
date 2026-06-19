from app.domain.services.chat_pdf_text_fusion_service import ChatPdfTextFusionService


def test_fuse_prefers_embedded_with_annotations():
    fused = ChatPdfTextFusionService.fuse(
        [
            {"name": "pypdf", "text": "short"},
            {
                "name": "fitz_embedded",
                "text": "90262019\n10080591\n10090481",
                "annotationCount": 80,
            },
        ]
    )

    assert fused["primarySource"] == "fitz_embedded"
    assert "90262019" in fused["fullText"]
    assert fused["charCount"] > 20


def test_fuse_merges_non_overlapping_region_text():
    fused = ChatPdfTextFusionService.fuse(
        [
            {"name": "fitz_embedded", "text": "PRODUTO 90261040"},
            {
                "name": "stamp_region",
                "text": "REV.: 03\nCLIENTE ACME",
            },
        ]
    )

    assert "90261040" in fused["fullText"]
    assert "CLIENTE ACME" in fused["fullText"]
