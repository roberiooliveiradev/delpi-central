"""Progresso user-facing da prévia de materiais do Alimentador.

Emite eventos monotônicos 0–100 com mensagens em PT-BR (content JSON).
O callback é opcional — POST legado não precisa de progresso.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from production_control_app.application.services.line_feeder_settings import setting_map

ProgressCallback = Callable[[dict[str, Any]], None]

# Fatias do percentual total da prévia de materiais.
_START_END = 5
_HORIZON_END = 50  # 5 → 50
_COMMITMENTS_END = 70  # 50 → 70
_STOCK_END = 90  # 70 → 90
_CONSOLIDATE_END = 100  # 90 → 100


def _progress_texts() -> Mapping[str, Any]:
    raw = setting_map("progress")
    return raw if isinstance(raw, dict) else {}


def _tpl(key: str, default: str, **kwargs: Any) -> str:
    template = str(_progress_texts().get(key) or default)
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError, IndexError):
        return default.format(**kwargs) if kwargs else default


def _label_work_center(code: str, name: str | None = None) -> str:
    center = (code or "").strip() or "?"
    label = (name or "").strip()
    if label and label != center:
        return f"{center} · {label}"
    return center


class MaterialsPreviewProgress:
    """Acumula percentuais monotônicos e formata mensagens naturais."""

    def __init__(
        self,
        on_progress: ProgressCallback | None,
        *,
        work_center_count: int,
    ) -> None:
        self._on_progress = on_progress
        self._wc_total = max(int(work_center_count), 1)
        self._wc_index = 0
        self._last_percent = -1

    def _emit(
        self,
        *,
        step: str,
        percent: int,
        message: str,
        work_center: str | None = None,
        detail: str | None = None,
    ) -> None:
        if self._on_progress is None:
            return
        clamped = max(0, min(100, int(percent)))
        if clamped < self._last_percent:
            clamped = self._last_percent
        self._last_percent = clamped
        event: dict[str, Any] = {
            "type": "progress",
            "step": step,
            "percent": clamped,
            "message": message,
        }
        if work_center:
            event["workCenter"] = work_center
        if detail:
            event["detail"] = detail
        self._on_progress(event)

    def starting(self) -> None:
        self._emit(
            step="start",
            percent=2,
            message=_tpl(
                "starting",
                "Preparando a prévia de materiais…",
            ),
        )

    def reading_publication(self) -> None:
        self._emit(
            step="publication",
            percent=_START_END,
            message=_tpl(
                "readingPublication",
                "Lendo a programação publicada dos postos selecionados…",
            ),
        )

    def horizon_work_center(
        self,
        *,
        work_center: str,
        work_center_name: str | None = None,
    ) -> None:
        """Progresso dentro da fatia de horizonte (5–50%), um CT por vez."""
        label = _label_work_center(work_center, work_center_name)
        # Índice 0..n-1 → percent após concluir o CT atual.
        done = min(self._wc_index + 1, self._wc_total)
        span = _HORIZON_END - _START_END
        percent = _START_END + int(span * done / self._wc_total)
        self._emit(
            step="horizon.work_center",
            percent=percent,
            message=_tpl(
                "horizonWorkCenter",
                "Calculando o horizonte do posto {workCenter}…",
                workCenter=label,
            ),
            work_center=work_center,
        )
        self._wc_index = done

    def horizon_done(self) -> None:
        self._emit(
            step="horizon.done",
            percent=_HORIZON_END,
            message=_tpl(
                "horizonDone",
                "Horizonte calculado. Analisando empenhos das operações contempladas…",
            ),
        )

    def fetching_commitments(self) -> None:
        self._emit(
            step="commitments",
            percent=(_HORIZON_END + _COMMITMENTS_END) // 2,
            message=_tpl(
                "fetchCommitments",
                "Consultando empenhos (SD4) das ordens no horizonte…",
            ),
        )

    def commitments_done(self) -> None:
        self._emit(
            step="commitments.done",
            percent=_COMMITMENTS_END,
            message=_tpl(
                "commitmentsDone",
                "Empenhos carregados. Conferindo saldo no ponto de uso…",
            ),
        )

    def fetching_stock(self) -> None:
        self._emit(
            step="stock",
            percent=(_COMMITMENTS_END + _STOCK_END) // 2,
            message=_tpl(
                "fetchStock",
                "Lendo estoque da bancada e local de retirada…",
            ),
        )

    def stock_done(self) -> None:
        self._emit(
            step="stock.done",
            percent=_STOCK_END,
            message=_tpl(
                "stockDone",
                "Saldos obtidos. Agrupando materiais por produto…",
            ),
        )

    def consolidating(self) -> None:
        self._emit(
            step="consolidate",
            percent=95,
            message=_tpl(
                "consolidate",
                "Consolidando a lista de coleta…",
            ),
        )

    def done(self) -> None:
        self._emit(
            step="done",
            percent=_CONSOLIDATE_END,
            message=_tpl(
                "done",
                "Prévia pronta.",
            ),
        )

    def as_horizon_callback(self) -> ProgressCallback | None:
        """Adapta eventos de horizonte (por CT) para a fatia 5–50%."""
        if self._on_progress is None:
            return None

        def _forward(event: dict[str, Any]) -> None:
            if event.get("type") != "progress":
                return
            step = str(event.get("step") or "")
            if step == "horizon.work_center":
                self.horizon_work_center(
                    work_center=str(event.get("workCenter") or ""),
                    work_center_name=str(event.get("detail") or "") or None,
                )

        return _forward
