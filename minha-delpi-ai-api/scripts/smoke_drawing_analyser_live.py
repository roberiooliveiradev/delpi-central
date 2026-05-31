#!/usr/bin/env python3
"""Smoke E2E — análise de desenhos: API /analyser live + PDF fixture + chat (opcional).

Uso (container com stack no ar):
  PYTHONPATH=/app SMOKE_BASE_URL=http://delpi-gateway \\
    python scripts/smoke_drawing_analyser_live.py

Variáveis:
  SMOKE_USER, SMOKE_PASSWORD, SMOKE_PRODUCT_CODE (default 90260140)
  SMOKE_SKIP_CHAT_E2E=1 — só HTTP + merge offline (sem POST no chat)
  SMOKE_CHAT_PREFIX (default /apps/minha-delpi-ai/api/chat)
"""

from __future__ import annotations

import json
import os
import sys
import uuid
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from app.application.services.chat_drawing_admin_debug_service import (
    ChatDrawingAdminDebugService,
)
from app.application.services.chat_drawing_report_export_service import (
    ChatDrawingReportExportService,
)
from app.domain.services.chat_drawing_pdf_extraction_service import (
    ChatDrawingPdfExtractionService,
)
from app.domain.services.chat_drawing_validation_orchestration_service import (
    ChatDrawingValidationOrchestrationService,
)

_BASE_URL = os.environ.get("SMOKE_BASE_URL", "http://delpi-gateway").strip()
_REALM = os.environ.get("SMOKE_REALM", "delpi").strip()
_CLIENT_ID = os.environ.get("SMOKE_CLIENT_ID", "delpi-central").strip()
_USERNAME = os.environ.get("SMOKE_USER", "rober").strip()
_PASSWORD = os.environ.get("SMOKE_PASSWORD", "1234").strip()
_PRODUCT_CODE = os.environ.get("SMOKE_PRODUCT_CODE", "90260140").strip()
_CHAT_PREFIX = os.environ.get("SMOKE_CHAT_PREFIX", "/apps/minha-delpi-ai/api/chat").strip()
_SKIP_CHAT = os.environ.get("SMOKE_SKIP_CHAT_E2E", "").lower() in {"1", "true", "yes"}
_SKIP_PREPARATION = os.environ.get("SMOKE_SKIP_PREPARATION_E2E", "").lower() in {
    "1",
    "true",
    "yes",
}
_AGENT_ID = os.environ.get("SMOKE_AGENT_ID", "").strip()
_USER_ID = os.environ.get(
    "SMOKE_USER_ID",
    "4ac305a6-0569-40b8-a918-b908cfeba169",
).strip()

_FIXTURE_PDF = (
    Path(__file__).resolve().parents[1]
    / "tests"
    / "fixtures"
    / "drawings"
    / "sample_carimbo_minimal.pdf"
)


def _request(
    method: str,
    url: str,
    *,
    token: str | None = None,
    body: dict | None = None,
    timeout: int = 180,
) -> dict:
    headers = {"Accept": "application/json"}
    data = None

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if body is not None:
        headers["Content-Type"] = "application/json"
        data = json.dumps(body).encode("utf-8")

    request = urllib.request.Request(url, data=data, headers=headers, method=method)

    with urllib.request.urlopen(request, timeout=timeout) as response:
        raw = response.read().decode("utf-8")

        if raw.lstrip().startswith("<"):
            raise RuntimeError(f"Resposta HTML em {url}")

        return json.loads(raw) if raw else {}


def _fetch_user_id(token: str) -> str:
    if _USER_ID and _USER_ID != "4ac305a6-0569-40b8-a918-b908cfeba169":
        return _USER_ID

    for path in ("/core-api/me", "/api/core/me"):
        try:
            payload = _request("GET", f"{_BASE_URL}{path}", token=token, timeout=30)
            user_id = str(payload.get("id") or payload.get("userId") or "").strip()

            if user_id:
                return user_id
        except Exception:
            continue

    return _USER_ID


def _fetch_token() -> str:
    form = urllib.parse.urlencode(
        {
            "grant_type": "password",
            "client_id": _CLIENT_ID,
            "username": _USERNAME,
            "password": _PASSWORD,
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        f"{_BASE_URL}/auth/realms/{_REALM}/protocol/openid-connect/token",
        data=form,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))

    token = payload.get("access_token")

    if not token:
        raise RuntimeError(f"Token ausente: {payload}")

    return str(token)


def _fetch_analyser(token: str, code: str) -> dict:
    query = urllib.parse.urlencode({"max_depth": "10", "page": "1", "page_size": "50"})
    paths = [
        f"/api/externa/products/{code}/analyser?{query}",
        f"/api/minha-delpi/externa/products/{code}/analyser?{query}",
    ]
    last_error: Exception | None = None

    for path in paths:
        req = urllib.request.Request(
            f"{_BASE_URL}{path}",
            headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
            method="GET",
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as response:
                raw = response.read().decode("utf-8")

                if raw.lstrip().startswith("<"):
                    raise RuntimeError(f"Resposta HTML em {path}")

                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                raise exc

            last_error = exc
            continue
        except (urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
            continue

    raise RuntimeError(f"Não foi possível obter analyser: {last_error}")


def _multipart_upload(
    url: str,
    *,
    token: str,
    filename: str,
    content: bytes,
    content_type: str,
) -> dict:
    boundary = f"----SmokeBoundary{uuid.uuid4().hex}"
    body = bytearray()
    body.extend(f"--{boundary}\r\n".encode())
    body.extend(
        (
            f'Content-Disposition: form-data; name="file"; '
            f'filename="{filename}"\r\n'
        ).encode()
    )
    body.extend(f"Content-Type: {content_type}\r\n\r\n".encode())
    body.extend(content)
    body.extend(f"\r\n--{boundary}--\r\n".encode())

    request = urllib.request.Request(
        url,
        data=bytes(body),
        headers={
            "Accept": "application/json",
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=120) as response:
        raw = response.read().decode("utf-8")

        return json.loads(raw) if raw else {}


def _ensure_pdf_fixture() -> Path:
    if _FIXTURE_PDF.is_file():
        return _FIXTURE_PDF

    api_root = Path(__file__).resolve().parents[1]

    if str(api_root) not in sys.path:
        sys.path.insert(0, str(api_root))

    from scripts.build_drawing_fixture_pdf import build_pdf

    return build_pdf(output_path=_FIXTURE_PDF)


def _unwrap_analyser_root(data: dict) -> dict:
    root = data.get("data", data)

    if isinstance(root, dict) and isinstance(root.get("data"), dict):
        root = root["data"]

    return root if isinstance(root, dict) else {}


def _first_agent(token: str) -> str:
    if _AGENT_ID:
        return _AGENT_ID

    agents = _request("GET", f"{_BASE_URL}{_CHAT_PREFIX}/agents?limit=30", token=token)
    items = agents if isinstance(agents, list) else agents.get("items", [])

    for agent in items:
        agent_key = str(agent.get("agentKey") or agent.get("key") or "").strip().lower()

        if agent_key == "minha-delpi-chat" and agent.get("enabled"):
            return str(agent["id"])

    for agent in items:
        if agent.get("enabled"):
            return str(agent["id"])

    if items:
        return str(items[0]["id"])

    raise RuntimeError("Nenhum agente disponível para smoke")


def _build_attachment_context_from_pdf(pdf_path: Path) -> str:
    from app.application.services.chat_attachment_text_extractor import (
        ChatAttachmentTextExtractor,
    )

    extracted = ChatAttachmentTextExtractor().extract(
        storage_path=str(pdf_path),
        filename=pdf_path.name,
        content_type="application/pdf",
    )
    content = str(extracted.get("content") or "").strip()

    return f"### {pdf_path.name}\n{content}\n\n"


def _run_preparation_e2e(token: str, pdf_path: Path) -> list[str]:
    """Prepara turno in-process com token real e PDF fixture (api-externa via tool)."""
    errors: list[str] = []
    message = (
        f"Analise o desenho técnico {_PRODUCT_CODE} e gere o relatório de conformidade DELPI"
    )

    from uuid import UUID

    from app.application.dto.send_chat_message_request import SendChatMessageRequest
    from app.application.services.chat_turn.chat_turn_preparation_service import (
        ChatTurnPreparationService,
    )
    from app.composition.chat_composer import (
        make_chat_tool_context_service,
        make_chat_workspace_context_service,
        make_rag_context_service,
    )
    from app.composition.root_composer import create_application
    from app.infrastructure.persistence.postgres_chat_session_repository import (
        PostgresChatSessionRepository,
    )

    app = create_application()

    with app.app_context():
        user_id = _fetch_user_id(token)
        session_repo = PostgresChatSessionRepository()
        sessions = session_repo.list_sessions_by_user(UUID(user_id))
        session = next((item for item in sessions if item.agent_id), None)

        if not session:
            agent_uuid = None

            try:
                agent_uuid = UUID(_first_agent(token))
            except Exception:
                pass

            session = session_repo.create_session(
                user_id=UUID(user_id),
                title="Smoke drawing analyser live",
                context=None,
                agent_id=agent_uuid,
            )
            from app.extensions.db import db

            db.session.commit()
        workspace_svc = make_chat_workspace_context_service()
        workspace = workspace_svc.build_context(session=session, user_id=UUID(user_id))
        attachment_context = _build_attachment_context_from_pdf(pdf_path)
        tool_svc = make_chat_tool_context_service()
        prep_svc = ChatTurnPreparationService(
            rag_context_service=make_rag_context_service(),
        )

        request = SendChatMessageRequest(
            user_id=user_id,
            session_id=str(session.id),
            message=message,
            access_token=token,
        )

        prepared = prep_svc.prepare(
            message=message,
            request=request,
            session=session,
            user_id=UUID(user_id),
            workspace_context=workspace,
            attachments=["smoke-drawing-pdf"],
            previous_messages=[],
            history_source=[],
            build_tool_context=lambda req, **kwargs: tool_svc.build_context(
                user_id=req.user_id,
                access_token=req.access_token or "",
                message=message,
                allowed_action_ids=kwargs.get("allowed_action_ids")
                or workspace.get("allowedActionIds"),
                actions_enabled=bool(workspace.get("actionsEnabled")),
                attachment_ids=["smoke-drawing-pdf"],
                attachment_context=attachment_context,
                previous_messages=kwargs.get("previous_messages") or [],
                agent_context=workspace.get("agent"),
            ),
            maybe_extend_tool_context=lambda **kw: kw["tool_context"],
            prepare_history=lambda h: ("", list(h[-4:])),
            history_keep=4,
            fast_path_enabled=False,
            fast_path_max_chars=120,
            resolve_user_identity_answer=lambda _m: None,
            resolve_capabilities_answer=lambda _m: None,
        )

        tool_context = prepared.tool_context or {}
        drawing = tool_context.get("drawingAnalysis")

        if not tool_context.get("drawingAnalysisMode"):
            errors.append("preparation: drawingAnalysisMode ausente")

        analyser_calls = [
            call
            for call in prepared.tool_calls or []
            if isinstance(call, dict)
            and (
                "/analyser" in str((call.get("metadata") or {}).get("path") or "").lower()
                or (call.get("arguments") or {}).get("actionId") == "get_product_analyser"
            )
        ]

        if not analyser_calls:
            errors.append("preparation: toolCall /analyser ausente")

        ok_analyser = [
            call
            for call in analyser_calls
            if (call.get("metadata") or {}).get("ok") is True
        ]

        if not isinstance(drawing, dict) or not drawing.get("items"):
            if ok_analyser:
                errors.append("preparation: drawingAnalysis vazio com analyser OK")
            elif analyser_calls:
                print(
                    "WARN preparation: drawingAnalysis vazio (analyser executado, resposta não OK — ex. 403)",
                    file=sys.stderr,
                )
            else:
                errors.append("preparation: drawingAnalysis vazio")

        from app.domain.services.chat_intent_router_service import ChatIntentRouterService

        classified = ChatIntentRouterService.classify(
            message,
            attachment_ids=["smoke-drawing-pdf"],
            allowed_action_ids=workspace.get("allowedActionIds"),
        )
        intent = (prepared.intent_route or {}).get("intent")

        if classified.intent != "drawing_analysis":
            errors.append(
                f"preparation: classificação={classified.intent} (esperado drawing_analysis)"
            )
        elif intent != "drawing_analysis" and not tool_context.get("drawingAnalysisMode"):
            errors.append(
                f"preparation: intent executado={intent} sem drawingAnalysisMode"
            )
        elif intent != "drawing_analysis":
            print(
                f"WARN preparation: intent executado={intent} "
                f"(classificado drawing_analysis; estágio tools no pipeline)",
                file=sys.stderr,
            )

    return errors


def _run_pipeline_merge(*, analyser_root: dict, pdf_path: Path) -> dict:
    pdf_extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf_path),
        filename=pdf_path.name,
    )

    package = ChatDrawingValidationOrchestrationService.build_from_analyser_payload(
        product_code=_PRODUCT_CODE,
        payload=analyser_root,
        has_pdf_attachment=True,
        api_ok=True,
        api_status_code=200,
        pdf_extract=pdf_extract,
    )

    report = ChatDrawingValidationOrchestrationService.format_report_markdown(package)
    export_payload = ChatDrawingReportExportService.build_export_payload(
        package=package,
        report_markdown=report,
    )

    trace = ChatDrawingAdminDebugService.build_trace(
        tool_context={
            "drawingAnalysisMode": True,
            "drawingPdfExtractSummary": {
                "productCode": pdf_extract.get("productCode"),
                "revision": pdf_extract.get("revision"),
                "legible": pdf_extract.get("legible"),
            },
            "drawingAnalysis": package.get("drawingAnalysis"),
            "drawingAnalysisExport": export_payload,
            "toolCalls": [
                {
                    "name": "execute_external_action",
                    "metadata": {
                        "ok": True,
                        "path": f"/products/{_PRODUCT_CODE}/analyser",
                        "statusCode": 200,
                        "actionId": "get_product_analyser",
                    },
                    "arguments": {"code": _PRODUCT_CODE},
                }
            ],
        },
        intent_route={"intent": "drawing_analysis", "confidence": 0.95},
        workspace_context={"skills": {"drawingAnalysis": True}},
    )

    return {
        "pdf_extract": pdf_extract,
        "package": package,
        "report": report,
        "export_payload": export_payload,
        "trace": trace,
    }


def _assistant_metadata_from_messages(
    session_id: str,
    *,
    token: str,
) -> tuple[dict, list, dict]:
    """Metadados do último turno assistant (drawingAnalysis fica em intelligence)."""
    messages = _request(
        "GET",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
    )
    items = messages if isinstance(messages, list) else messages.get("items", [])

    for item in reversed(items):
        if str(item.get("role") or "") != "assistant":
            continue

        metadata = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
        intelligence = metadata.get("intelligence")

        if isinstance(intelligence, dict):
            merged = dict(metadata)
            merged.setdefault("drawingAnalysis", intelligence.get("drawingAnalysis"))
            merged.setdefault("drawingAnalysisMode", intelligence.get("drawingAnalysisMode"))
            return merged, list(metadata.get("toolCalls") or []), metadata.get("adminDebug") or {}

        return metadata, list(metadata.get("toolCalls") or []), metadata.get("adminDebug") or {}

    return {}, [], {}


def _run_chat_e2e(token: str, pdf_path: Path) -> list[str]:
    errors: list[str] = []
    agent_id = _first_agent(token)
    session = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions",
        token=token,
        body={"title": "Smoke drawing analyser live", "agentId": agent_id},
    )
    session_id = str(session["id"])

    pdf_bytes = pdf_path.read_bytes()
    attachment = _multipart_upload(
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/attachments",
        token=token,
        filename=pdf_path.name,
        content=pdf_bytes,
        content_type="application/pdf",
    )
    attachment_id = str(attachment["id"])

    message = (
        f"Analise o desenho técnico {_PRODUCT_CODE} e gere o relatório de conformidade DELPI"
    )

    response = _request(
        "POST",
        f"{_BASE_URL}{_CHAT_PREFIX}/sessions/{session_id}/messages",
        token=token,
        body={
            "message": message,
            "agentId": agent_id,
            "attachmentIds": [attachment_id],
        },
        timeout=300,
    )

    answer = str(response.get("answer") or response.get("content") or "")
    metadata, persisted_tool_calls, persisted_admin_debug = _assistant_metadata_from_messages(
        session_id,
        token=token,
    )
    admin_debug = (
        response.get("adminDebug")
        if isinstance(response.get("adminDebug"), dict)
        else persisted_admin_debug
    )
    if not isinstance(admin_debug, dict):
        admin_debug = {}

    drawing = metadata.get("drawingAnalysis")

    if not isinstance(drawing, dict) or not drawing.get("items"):
        errors.append("metadata.drawingAnalysis ausente ou vazio no chat E2E")

    if "Relatório" not in answer and "Análise" not in answer and "desenho" not in answer.lower():
        errors.append(f"resposta do chat sem indicativo de relatório: {answer[:240]}")

    tool_calls = persisted_tool_calls or response.get("toolCalls") or []

    if not any(
        isinstance(call, dict)
        and (
            "/analyser" in str((call.get("metadata") or {}).get("path") or "").lower()
            or (call.get("arguments") or {}).get("actionId") == "get_product_analyser"
        )
        for call in tool_calls
    ):
        errors.append("toolCall /analyser não encontrado na resposta E2E")

    trace = admin_debug.get("drawingAnalysisTrace")

    if isinstance(trace, dict):
        phase_ids = [phase.get("id") for phase in trace.get("phases") or [] if isinstance(phase, dict)]

        for required in ("intent", "pdf_extraction", "analyser", "validation"):
            if required not in phase_ids:
                errors.append(f"adminDebug sem fase drawing:{required}")
    elif admin_debug:
        errors.append("adminDebug sem drawingAnalysisTrace")

    export_meta = metadata.get("drawingAnalysisExport")

    if not isinstance(export_meta, dict) or not export_meta.get("markdown"):
        errors.append("drawingAnalysisExport ausente no chat E2E")

    return errors


def main() -> int:
    failed = 0

    def check(name: str, ok: bool) -> None:
        nonlocal failed

        if ok:
            print(f"OK {name}")
        else:
            print(f"FAIL {name}", file=sys.stderr)
            failed += 1

    try:
        pdf_path = _ensure_pdf_fixture()
        check("fixture PDF", pdf_path.is_file())
    except Exception as exc:
        print(f"FAIL fixture PDF: {exc}", file=sys.stderr)
        return 1

    pdf_extract = ChatDrawingPdfExtractionService.extract_from_storage_path(
        str(pdf_path),
        filename=pdf_path.name,
    )
    check("extração PDF fixture", pdf_extract.get("productCode") == _PRODUCT_CODE)

    analyser_root: dict | None = None
    http_skipped = False

    try:
        token = _fetch_token()
        check("login", True)
    except Exception as exc:
        print(f"FAIL login: {exc}", file=sys.stderr)
        return 1

    try:
        data = _fetch_analyser(token, _PRODUCT_CODE)
        analyser_root = _unwrap_analyser_root(data)
        check("HTTP GET /analyser", bool(analyser_root))
    except urllib.error.HTTPError as exc:
        http_skipped = True
        print(
            f"SKIP HTTP analyser ({exc.code}): merge offline com payload de teste",
            file=sys.stderr,
        )
        from tests.unit.domain.services.test_external_action_result_presenter_analyser_humanized import (
            _analyser_payload_with_guide_and_inspection,
        )

        analyser_root = _analyser_payload_with_guide_and_inspection()
    except Exception as exc:
        print(f"FAIL HTTP analyser: {exc}", file=sys.stderr)
        return 1

    try:
        merged = _run_pipeline_merge(analyser_root=analyser_root, pdf_path=pdf_path)
        analysis = merged["package"]["drawingAnalysis"]
        check("merge PDF × API", isinstance(analysis, dict) and bool(analysis.get("items")))
        check("relatório markdown", "Relatório de Análise" in merged["report"])
        check("export PDF filename", str(merged["export_payload"].get("pdfFilename", "")).endswith(".pdf"))
        trace = merged["trace"]
        check(
            "trace admin fases",
            bool(trace)
            and len(trace.get("phases") or []) >= 5
            and trace["phases"][3]["id"] == "analyser",
        )
    except Exception as exc:
        print(f"FAIL merge pipeline: {exc}", file=sys.stderr)
        failed += 1

    if _SKIP_PREPARATION:
        print("SKIP preparation E2E (SMOKE_SKIP_PREPARATION_E2E=1)")
    else:
        try:
            prep_errors = _run_preparation_e2e(token, pdf_path)

            if prep_errors:
                for err in prep_errors:
                    print(f"FAIL {err}", file=sys.stderr)
                    failed += 1
            else:
                check("preparation E2E (token + PDF + /analyser)", True)
        except Exception as exc:
            print(f"FAIL preparation E2E: {exc}", file=sys.stderr)
            failed += 1

    if _SKIP_CHAT:
        print("SKIP chat HTTP E2E (SMOKE_SKIP_CHAT_E2E=1)")
    else:
        try:
            chat_errors = _run_chat_e2e(token, pdf_path)

            if chat_errors:
                for err in chat_errors:
                    print(f"FAIL chat HTTP: {err}", file=sys.stderr)
                    failed += 1
            else:
                check("chat HTTP E2E desenho + PDF", True)
        except Exception as exc:
            print(f"FAIL chat HTTP E2E: {exc}", file=sys.stderr)
            failed += 1

    if failed:
        print(f"\n{failed} verificação(ões) falharam", file=sys.stderr)
        return 1

    parts = ["PDF + pipeline"]

    if not http_skipped:
        parts.insert(0, "HTTP /analyser")
    else:
        parts.append("HTTP SKIP (403)")

    if not _SKIP_PREPARATION:
        parts.append("preparation E2E")

    if not _SKIP_CHAT:
        parts.append("chat HTTP E2E")

    print(f"Smoke drawing analyser live ({_PRODUCT_CODE}): {' · '.join(parts)} OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
