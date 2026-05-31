#!/usr/bin/env python3
"""Smoke — skill document-vision-delpi (Onda 13).

Uso:
  PYTHONPATH=/app python scripts/smoke_document_vision.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import patch

from app.application.services.chat_document_vision_service import ChatDocumentVisionService
from app.domain.services.chat_drawing_pdf_extraction_service import ChatDrawingPdfExtractionService
from app.domain.skills.chat_skill_registry import ChatSkillRegistry
from app.infrastructure.config.settings import Settings


def main() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed

        if ok:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}", file=sys.stderr)
            failed += 1

    Settings.CHAT_DOCUMENT_VISION_ENABLED = True
    Settings.CHAT_DOCUMENT_VISION_AUTO_WITH_DRAWING = True

    flags = ChatSkillRegistry.resolve_runtime_flags(
        agent_metadata=None,
        allowed_action_ids=["get_product_analyser"],
        has_agent=True,
    )
    check("skill documentVision com drawing", flags.get("documentVision") is True)

    from app.application.services.chat_document_vision_metrics_service import (
        ChatDocumentVisionMetricsService,
    )

    metrics_meta: dict = {}
    ChatDocumentVisionMetricsService.attach_to_assistant_metadata(
        metrics_meta,
        tool_context={
            "drawingAnalysisMode": True,
            "documentVision": {"engine": "tesseract", "stages": ["tesseract"]},
            "drawingPdfExtractSummary": {"legible": True, "charCount": 64},
        },
    )
    check("documentVisionMetrics", bool(metrics_meta.get("documentVisionMetrics")))

    with patch.object(
        ChatDocumentVisionService,
        "_resolve_first_document_attachment",
        return_value=type(
            "Att",
            (),
            {
                "status": "indexed",
                "storage_path": "/tmp/smoke.pdf",
                "original_filename": "smoke.pdf",
                "content_type": "application/pdf",
            },
        )(),
    ):
        with patch.object(
            ChatDocumentVisionService,
            "_stage_native",
            return_value={"fullText": "TEXTO LEGIVEL " * 20, "engine": "pypdf", "metadata": {}},
        ):
            meta_indexed = ChatDocumentVisionService.build_attachment_vision_metadata(
                user_id="u",
                session_id="s",
                attachment_ids=["a"],
                skills={"documentVision": True},
            )
    check("attachment vision metadata indexed", meta_indexed and meta_indexed.get("stages") == ["native"])

    text = "DESENHO 90260140 REV.01\nCOD. CLIENTE TESTE"
    parsed = ChatDrawingPdfExtractionService.parse_from_text(text)
    vision = ChatDocumentVisionService._build_from_text(
        text,
        engine="native",
        stages=["native"],
    )
    merged = ChatDocumentVisionService.merge_into_drawing_parse(parsed, vision)
    check("merge código produto", merged.get("productCode") == "90260140")
    check("merge revision", merged.get("revision") == "01")

    fixture = Path(__file__).resolve().parents[1] / "tests/fixtures/drawings/sample_carimbo_minimal.pdf"
    with patch.object(
        ChatDocumentVisionService,
        "_stage_tesseract_image",
        return_value={
            "fullText": "DESENHO 90260155 REV.03",
            "engine": "tesseract",
            "warnings": [],
        },
    ):
        img_result = ChatDocumentVisionService.extract_from_storage_path(
            "/tmp/smoke-drawing.png",
            filename="drawing.png",
            content_type="image/png",
        )
        check("imagem PNG OCR", img_result.get("productCode") == "90260155")
        check("imagem stages tesseract", "tesseract_image" in (img_result.get("stages") or []))

    if fixture.is_file():
        result = ChatDocumentVisionService.extract_from_storage_path(
            str(fixture),
            filename=fixture.name,
            content_type="application/pdf",
        )
        check("fixture PDF schema", result.get("schemaVersion") == "1.0")
        check("fixture PDF stages", bool(result.get("stages")))
    else:
        print("SKIP fixture PDF (ausente)")

    api_root = Path(__file__).resolve().parents[1]
    pytest_env = {**os.environ, "PYTHONPATH": os.environ.get("PYTHONPATH", str(api_root))}
    import subprocess

    pytest_result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/unit/application/services/test_chat_document_vision_service.py",
            "tests/unit/application/services/test_chat_document_vision_metrics_service.py",
            "tests/unit/application/services/test_chat_document_vision_attachment_metadata.py",
            "tests/unit/application/services/test_chat_document_vision_neural_backend.py",
            "tests/unit/domain/services/test_chat_attachment_document_intent_service.py",
            "-q",
        ],
        cwd=str(api_root),
        env=pytest_env,
        check=False,
    )
    check("pytest document vision", pytest_result.returncode == 0)

    if failed:
        print("\nSmoke document vision: falhou.", file=sys.stderr)
        return 1

    print("\nSmoke document vision: todas as verificações passaram.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
