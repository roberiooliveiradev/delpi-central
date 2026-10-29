"""Node subprocess adapter for the canonical BPMN auto-layout bundle.

Runs `node /app/vendor/bpmn-layout/organize.cjs` — the esbuild artifact
compiled at image build from plugins/bpmn-editor/src/layout (the same
code the Portal editor executes in the browser). stdin carries the JSON
payload; stdout returns the JSON result. One-shot process per call,
bounded by timeout.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any

from tm_app.application.ports.bpmn_layout_port import (
    BpmnLayoutError,
    BpmnLayoutResult,
)

BUNDLE_PATH = os.environ.get(
    "TM_BPMN_LAYOUT_BUNDLE", "/app/vendor/bpmn-layout/organize.cjs"
)
NODE_BIN = os.environ.get("TM_BPMN_LAYOUT_NODE", "node")
# Layout profile caps ELK at 15 s; the subprocess budget adds startup
# and stdin/stdout overhead.
TIMEOUT_SECONDS = int(os.environ.get("TM_BPMN_LAYOUT_TIMEOUT", "30"))


class NodeBpmnLayoutService:
    """Executes the canonical layout pipeline via the Node bundle."""

    def __init__(self, bundle_path: str = BUNDLE_PATH) -> None:
        self._bundle = bundle_path

    def organize(self, xml: str) -> BpmnLayoutResult:
        if shutil.which(NODE_BIN) is None or not os.path.exists(self._bundle):
            raise BpmnLayoutError(
                "BPMN layout runtime indisponível (bundle/node ausente)."
            )
        try:
            proc = subprocess.run(
                [NODE_BIN, self._bundle],
                input=json.dumps({"xml": xml}),
                capture_output=True,
                text=True,
                timeout=TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired as exc:
            raise BpmnLayoutError(
                "Tempo limite excedido na organização do layout BPMN."
            ) from exc
        except OSError as exc:
            raise BpmnLayoutError(
                f"Falha ao executar o runtime de layout: {exc}"
            ) from exc

        if proc.returncode != 0:
            raise BpmnLayoutError(
                "Falha no runtime de layout BPMN "
                f"(exit {proc.returncode}): {(proc.stderr or '')[:300]}"
            )
        try:
            payload: dict[str, Any] = json.loads(proc.stdout or "{}")
        except json.JSONDecodeError as exc:
            raise BpmnLayoutError(
                "Resposta inválida do runtime de layout BPMN."
            ) from exc

        if not payload.get("ok"):
            err = payload.get("error") or {}
            raise BpmnLayoutError(
                f"Organização BPMN falhou "
                f"[{err.get('code', 'LAYOUT_FAILED')}]: "
                f"{err.get('message', 'erro desconhecido')}"
            )
        return BpmnLayoutResult(
            xml=str(payload["xml"]),
            changed=bool(payload.get("changed")),
            moved_elements=int(payload.get("movedElements") or 0),
        )
