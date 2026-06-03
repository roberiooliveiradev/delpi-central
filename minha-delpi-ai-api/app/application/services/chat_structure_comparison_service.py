from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from app.application.services.chat_product_structure_comparison_service import (
    ChatProductStructureComparisonService,
)
from app.domain.services.chat_analysis_intent_service import ChatAnalysisIntentService
from app.domain.services.chat_product_query_intent_service import (
    ChatProductQueryIntentService,
)
from app.domain.services.chat_reference_resolution_service import (
    ChatReferenceResolutionService,
)
from app.domain.services.chat_product_structure_presentation_service import (
    ChatProductStructurePresentationService,
    ProductStructureModel,
)


@dataclass(frozen=True)
class BomComponentLine:
    code: str
    description: str
    item_type: str
    unit: str
    quantity: float | None


@dataclass
class ProductStructureSnapshot:
    product_code: str
    model: ProductStructureModel | None = None
    lines: list[BomComponentLine] = field(default_factory=list)
    profile_lines: list[str] = field(default_factory=list)


class ChatStructureComparisonService:
    """Compara estruturas (BOM) do histórico e das consultas da rodada atual."""

    _STRUCTURE_USER_RE = re.compile(
        r"\bestrutur[a]?\b.*?\b(\d{5,8})\b",
        re.IGNORECASE,
    )
    _BOM_LINE_RE = re.compile(
        r"\*{0,2}(?P<code>\d{5,8})\*{0,2}\s*[—–\-|]\s*(?P<rest>.+)$",
        re.IGNORECASE,
    )
    _QTY_RE = re.compile(r"Qtd:\s*(?P<qty>[\d.,]+)", re.IGNORECASE)
    _TYPE_UNIT_RE = re.compile(r"\((?P<tipo>[^)]+)\)\s*(?:\[(?P<unit>[^\]]+)\])?")

    @classmethod
    def build_comparison_answer(
        cls,
        message: str,
        previous_messages: list | None,
        *,
        current_tool_calls: list | None = None,
    ) -> str | None:
        if not ChatAnalysisIntentService.is_comparison_or_insight_request(message):
            return None

        if cls._is_conversational_previous_compare(message):
            return None

        snapshots, snapshot_order = cls.collect_structure_snapshots(
            previous_messages or [],
            current_tool_calls=current_tool_calls,
        )

        if len(snapshots) < 2:
            codes = ChatAnalysisIntentService.extract_all_product_codes(
                message,
                *[
                    cls._message_field(item, "content")
                    for item in (previous_messages or [])
                ],
            )
            if len(codes) >= 2:
                return cls._insufficient_data_answer(codes, found=len(snapshots))

            return None

        selected_keys = [key for key in snapshot_order if key in snapshots][-2:]

        if len(selected_keys) < 2:
            selected_keys = list(snapshots.keys())[:2]

        selected = [snapshots[key] for key in selected_keys]

        if len(selected) >= 2 and selected[0].model and selected[1].model:
            return ChatProductStructureComparisonService.render(
                selected[0].model,
                selected[1].model,
            )

        if (
            len(selected) >= 2
            and selected[0].profile_lines
            and selected[1].profile_lines
        ):
            return cls._render_profile_comparison(selected[0], selected[1])

        return cls._render_comparison(selected)

    @classmethod
    def _is_conversational_previous_compare(cls, message: str) -> bool:
        normalized = (message or "").strip()

        if not ChatReferenceResolutionService._COMPARE_PREVIOUS_RE.search(normalized):
            return False

        explicit_codes = ChatAnalysisIntentService.extract_all_product_codes(normalized)

        return len(explicit_codes) < 2

    @classmethod
    def _insufficient_data_answer(cls, codes: list[str], *, found: int) -> str:
        missing = ", ".join(codes[:4])
        return (
            f"Para comparar com precisão, preciso da **ficha completa** ou da **estrutura (BOM)** "
            f"de **{missing}** nesta conversa. Encontrei dados utilizáveis de {found} produto(s) "
            "no histórico. Consulte cada código (ex.: «ficha completa do 10080047») e peça a "
            "comparação novamente."
        )

    @classmethod
    def collect_structure_snapshots(
        cls,
        previous_messages: list,
        *,
        current_tool_calls: list | None = None,
    ) -> tuple[dict[str, ProductStructureSnapshot], list[str]]:
        snapshots: dict[str, ProductStructureSnapshot] = {}
        snapshot_order: list[str] = []
        pending_product_code: str | None = None

        if current_tool_calls:
            cls._merge_tool_calls_into_snapshots(
                snapshots,
                snapshot_order,
                current_tool_calls,
            )

        for message in previous_messages:
            role = cls._message_field(message, "role", "user")

            if role == "user":
                pending_product_code = cls._product_code_from_user_message(
                    cls._message_field(message, "content")
                ) or pending_product_code
                continue

            if role != "assistant":
                continue

            for product_code, model, lines, profile_lines in cls._extract_from_assistant_message(
                message,
                pending_product_code,
            ):
                key = ChatProductQueryIntentService.normalize_product_code(product_code)

                if not key or (not model and not lines and not profile_lines):
                    continue

                previous = snapshots.get(key)

                if previous:
                    if not model and previous.model:
                        model = previous.model

                    if not lines and previous.lines:
                        lines = previous.lines

                    if not profile_lines and previous.profile_lines:
                        profile_lines = previous.profile_lines

                snapshots[key] = ProductStructureSnapshot(
                    product_code=key,
                    model=model,
                    lines=lines,
                    profile_lines=profile_lines,
                )

                if key not in snapshot_order:
                    snapshot_order.append(key)

            pending_product_code = None

        return snapshots, snapshot_order

    @classmethod
    def _merge_tool_calls_into_snapshots(
        cls,
        snapshots: dict[str, ProductStructureSnapshot],
        snapshot_order: list[str],
        tool_calls: list,
    ) -> None:
        for tool_call in tool_calls:
            if not isinstance(tool_call, dict):
                continue

            if str(tool_call.get("name") or "") != "execute_external_action":
                continue

            tool_meta = tool_call.get("metadata")

            if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                continue

            path = str(tool_meta.get("path") or "").lower()

            if "/structure" not in path and "/analyser" not in path:
                continue

            product_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

            if not product_code:
                continue

            model = cls._model_from_tool_metadata(tool_meta) if "/structure" in path else None
            lines = cls._lines_from_tool_metadata(tool_meta) if "/structure" in path else []
            profile_lines = (
                cls._profile_lines_from_tool_metadata(tool_meta)
                if "/analyser" in path
                else []
            )

            if not model and not lines and not profile_lines:
                continue

            key = ChatProductQueryIntentService.normalize_product_code(product_code)
            previous = snapshots.get(key)

            if previous:
                if not model and previous.model:
                    model = previous.model

                if not lines and previous.lines:
                    lines = previous.lines

                if not profile_lines and previous.profile_lines:
                    profile_lines = previous.profile_lines

            snapshots[key] = ProductStructureSnapshot(
                product_code=key,
                model=model,
                lines=lines,
                profile_lines=profile_lines,
            )

            if key not in snapshot_order:
                snapshot_order.append(key)

    @classmethod
    def _extract_from_assistant_message(
        cls,
        message,
        pending_product_code: str | None = None,
    ) -> list[tuple[str, ProductStructureModel | None, list[BomComponentLine], list[str]]]:
        results: list[
            tuple[str, ProductStructureModel | None, list[BomComponentLine], list[str]]
        ] = []
        metadata = cls._message_metadata(message)
        tool_calls = metadata.get("toolCalls") or []

        if isinstance(tool_calls, list):
            for tool_call in tool_calls:
                if not isinstance(tool_call, dict):
                    continue

                if str(tool_call.get("name") or "") != "execute_external_action":
                    continue

                tool_meta = tool_call.get("metadata")

                if not isinstance(tool_meta, dict) or not tool_meta.get("ok"):
                    continue

                path = str(tool_meta.get("path") or "")
                product_code = ChatAnalysisIntentService.extract_product_code_from_tool_path(path)

                path_lower = path.lower()

                if not product_code or (
                    "/structure" not in path_lower and "/analyser" not in path_lower
                ):
                    continue

                model = cls._model_from_tool_metadata(tool_meta) if "/structure" in path_lower else None
                lines = cls._lines_from_tool_metadata(tool_meta) if "/structure" in path_lower else []
                profile_lines = (
                    cls._profile_lines_from_tool_metadata(tool_meta)
                    if "/analyser" in path_lower
                    else []
                )

                if model or lines or profile_lines:
                    results.append((product_code, model, lines, profile_lines))

        content = cls._message_field(message, "content")

        if content and cls._looks_like_structure_content(content):
            lines = cls._lines_from_text(content)

            if lines:
                product_code = pending_product_code

                if not product_code:
                    user_codes = ChatAnalysisIntentService.extract_all_product_codes(content)
                    product_code = user_codes[0] if len(user_codes) == 1 else None

                if product_code:
                    results.append((product_code, None, lines, []))

        return results

    @classmethod
    def _profile_lines_from_tool_metadata(cls, metadata: dict) -> list[str]:
        humanized = metadata.get("humanizedSummary")

        if isinstance(humanized, dict):
            title = str(humanized.get("titulo") or "").strip()
            lines = [
                str(line).strip()
                for line in (humanized.get("linhas") or [])
                if str(line).strip()
            ]

            if title:
                return [title, *lines]

            if lines:
                return lines

        preview = str(metadata.get("responsePreview") or "").strip()

        if preview and not preview.startswith("{"):
            return [line.strip() for line in preview.splitlines() if line.strip()]

        return []

    @classmethod
    def _render_profile_comparison(
        cls,
        left: ProductStructureSnapshot,
        right: ProductStructureSnapshot,
    ) -> str:
        parts = [
            "## Comparação entre produtos",
            "",
            f"### Produto {left.product_code}",
            *[f"- {line}" for line in left.profile_lines[:12]],
            "",
            f"### Produto {right.product_code}",
            *[f"- {line}" for line in right.profile_lines[:12]],
            "",
            "### Destaques",
        ]

        left_text = " ".join(left.profile_lines).lower()
        right_text = " ".join(right.profile_lines).lower()

        if left.product_code != right.product_code:
            parts.append(
                f"- Códigos comparados: **{left.product_code}** e **{right.product_code}**."
            )

        for label, token in (
            ("Tipo", "tipo "),
            ("Unidade", "unidade "),
            ("Grupo", "grupo "),
            ("Custo", "custo"),
            ("Preço de compra", "preço de compra"),
        ):
            if token in left_text and token in right_text:
                parts.append(f"- Ambos trazem informação de **{label}** na ficha.")

        parts.append(
            "\n_Comparação gerada a partir das fichas completas já consultadas nesta conversa._"
        )

        return "\n".join(parts)

    @classmethod
    def _model_from_tool_metadata(cls, metadata: dict) -> ProductStructureModel | None:
        preview = str(metadata.get("responsePreview") or "").strip()

        if preview:
            try:
                payload = json.loads(preview)
            except json.JSONDecodeError:
                payload = None

            if model := ChatProductStructurePresentationService.parse_payload(payload):
                return model

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            raw = presentation.get("rawData") or presentation.get("data")

            if model := ChatProductStructurePresentationService.parse_payload(raw):
                return model

        return None

    @classmethod
    def _lines_from_tool_metadata(cls, metadata: dict) -> list[BomComponentLine]:
        preview = str(metadata.get("responsePreview") or "").strip()

        if preview:
            try:
                payload = json.loads(preview)
            except json.JSONDecodeError:
                payload = None

            if isinstance(payload, dict):
                items = payload.get("items")

                if isinstance(items, list):
                    parsed = cls._lines_from_items(items)

                    if parsed:
                        return parsed

        presentation = metadata.get("presentation")

        if isinstance(presentation, dict):
            rows = presentation.get("rows")

            if isinstance(rows, list):
                parsed = cls._lines_from_items(rows)

                if parsed:
                    return parsed

        return []

    @classmethod
    def _lines_from_items(cls, items: list) -> list[BomComponentLine]:
        lines: list[BomComponentLine] = []

        for raw in items:
            if not isinstance(raw, dict):
                continue

            code = str(raw.get("code") or raw.get("component_code") or "").strip()

            if not code or not code.isdigit():
                continue

            description = str(raw.get("description") or raw.get("name") or "").strip()
            item_type = str(raw.get("type") or raw.get("item_type") or "").strip()
            unit = str(raw.get("unit") or "").strip()
            quantity = cls._parse_quantity(raw.get("quantity"))

            lines.append(
                BomComponentLine(
                    code=code,
                    description=description,
                    item_type=item_type,
                    unit=unit,
                    quantity=quantity,
                )
            )

        return lines

    @classmethod
    def _lines_from_text(cls, text: str) -> list[BomComponentLine]:
        lines: list[BomComponentLine] = []

        for raw_line in text.splitlines():
            line = raw_line.strip().lstrip("-•").strip()

            if not line:
                continue

            match = cls._BOM_LINE_RE.search(line)

            if not match:
                continue

            code = match.group("code")
            rest = match.group("rest").strip()
            qty_match = cls._QTY_RE.search(rest)
            quantity = cls._parse_quantity(qty_match.group("qty")) if qty_match else None

            if qty_match:
                rest = rest[: qty_match.start()].strip().rstrip("|,")

            tipo = ""
            unit = ""
            type_match = cls._TYPE_UNIT_RE.search(rest)

            if type_match:
                tipo = str(type_match.group("tipo") or "").strip()
                unit = str(type_match.group("unit") or "").strip()
                rest = rest[: type_match.start()].strip()

            description = rest.strip(" —-|")

            lines.append(
                BomComponentLine(
                    code=code,
                    description=description,
                    item_type=tipo,
                    unit=unit,
                    quantity=quantity,
                )
            )

        return lines

    @classmethod
    def _render_comparison(cls, snapshots: list[ProductStructureSnapshot]) -> str:
        if len(snapshots) < 2:
            return ""

        left, right = snapshots[0], snapshots[1]
        left_codes = {line.code for line in left.lines}
        right_codes = {line.code for line in right.lines}
        common = left_codes & right_codes
        only_left = sorted(left_codes - right_codes)
        only_right = sorted(right_codes - left_codes)
        qty_diffs = cls._quantity_differences(left, right, common)

        parts = [
            f"**Resumo:** Comparei as estruturas (BOM) dos produtos **{left.product_code}** "
            f"({len(left.lines)} componente(s)) e **{right.product_code}** "
            f"({len(right.lines)} componente(s)). "
            f"Há {len(common)} componente(s) em comum, {len(only_left)} exclusivo(s) do primeiro "
            f"e {len(only_right)} exclusivo(s) do segundo.",
            "",
            "**Semelhanças**",
            f"- {len(common)} código(s) de componente aparecem nas duas estruturas.",
        ]

        if common:
            sample = ", ".join(sorted(common)[:8])
            suffix = "…" if len(common) > 8 else ""
            parts.append(f"- Exemplos em comum: {sample}{suffix}.")

        parts.extend(["", f"**Só em {left.product_code}**"])

        if only_left:
            parts.extend(f"- `{code}`" for code in only_left[:15])

            if len(only_left) > 15:
                parts.append(f"- … e mais {len(only_left) - 15} componente(s).")
        else:
            parts.append("- Nenhum componente exclusivo.")

        parts.extend(["", f"**Só em {right.product_code}**"])

        if only_right:
            parts.extend(f"- `{code}`" for code in only_right[:15])

            if len(only_right) > 15:
                parts.append(f"- … e mais {len(only_right) - 15} componente(s).")
        else:
            parts.append("- Nenhum componente exclusivo.")

        parts.extend(["", "**Diferenças de quantidade (mesmo código)**"])

        if qty_diffs:
            for code, left_qty, right_qty in qty_diffs[:12]:
                parts.append(f"- `{code}`: {left.product_code} = {left_qty} | {right.product_code} = {right_qty}")

            if len(qty_diffs) > 12:
                parts.append(f"- … e mais {len(qty_diffs) - 12} divergência(s) de quantidade.")
        else:
            parts.append("- Nenhuma diferença de quantidade nos componentes em comum.")

        parts.extend(
            [
                "",
                "**Apontamentos**",
                "- Revise componentes exclusivos antes de equalizar BOM entre plantas ou versões.",
                "- Valide unidades (MI/UN) e tipos (PI/MP) quando o mesmo código aparece com quantidades distintas.",
                "",
                "**Insights**",
                "- Priorize harmonizar os exclusivos que impactam custo ou processo crítico.",
                "- Se precisar da tabela completa lado a lado, peça «coloque na lousa» após esta análise.",
            ]
        )

        if len(snapshots) > 2:
            extras = ", ".join(snapshot.product_code for snapshot in snapshots[2:])
            parts.append(f"- Há mais produtos no histórico ({extras}); comparei os dois mais recentes.")

        return "\n".join(parts)

    @classmethod
    def _quantity_differences(
        cls,
        left: ProductStructureSnapshot,
        right: ProductStructureSnapshot,
        common: set[str],
    ) -> list[tuple[str, str, str]]:
        diffs: list[tuple[str, str, str]] = []
        left_map = {line.code: line for line in left.lines}
        right_map = {line.code: line for line in right.lines}

        for code in sorted(common):
            left_line = left_map.get(code)
            right_line = right_map.get(code)

            if not left_line or not right_line:
                continue

            left_qty = left_line.quantity
            right_qty = right_line.quantity

            if left_qty is None and right_qty is None:
                continue

            if left_qty != right_qty:
                diffs.append(
                    (
                        code,
                        cls._format_qty(left_qty),
                        cls._format_qty(right_qty),
                    )
                )

        return diffs

    @classmethod
    def _format_qty(cls, value: float | None) -> str:
        if value is None:
            return "—"

        if float(value).is_integer():
            return str(int(value))

        return str(value)

    @classmethod
    def _parse_quantity(cls, value) -> float | None:
        if value is None or value == "":
            return None

        try:
            normalized = str(value).strip().replace(",", ".")

            return float(normalized)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _looks_like_structure_content(cls, content: str) -> bool:
        lowered = content.lower()

        if "estrutura" in lowered and cls._BOM_LINE_RE.search(content):
            return True

        return bool(cls._BOM_LINE_RE.search(content))

    @classmethod
    def _product_code_from_user_message(cls, content: str) -> str | None:
        match = cls._STRUCTURE_USER_RE.search(content or "")

        if match:
            return ChatProductQueryIntentService.normalize_product_code(match.group(1))

        codes = ChatAnalysisIntentService.extract_all_product_codes(content)

        if len(codes) == 1:
            return codes[0]

        return None

    @classmethod
    def _message_field(cls, message, name: str, default: str = "") -> str:
        if isinstance(message, dict):
            return str(message.get(name) or default).strip()

        return str(getattr(message, name, default) or default).strip()

    @classmethod
    def _message_metadata(cls, message) -> dict:
        if isinstance(message, dict):
            metadata = message.get("metadata")

            return metadata if isinstance(metadata, dict) else {}

        metadata = getattr(message, "metadata", None)

        return metadata if isinstance(metadata, dict) else {}
