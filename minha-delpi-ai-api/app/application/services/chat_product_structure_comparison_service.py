from __future__ import annotations

from app.domain.services.chat_product_structure_presentation_service import (
    ChatProductStructurePresentationService,
    ProductStructureModel,
    StructureNode,
)


class ChatProductStructureComparisonService:
    """Comparativo determinístico entre duas estruturas (estilo análise técnica)."""

    @classmethod
    def render(cls, left: ProductStructureModel, right: ProductStructureModel) -> str:
        left_mps = left.all_mp_nodes()
        right_mps = right.all_mp_nodes()
        left_mp_codes = {node.code for _, node in left_mps}
        right_mp_codes = {node.code for _, node in right_mps}
        common = sorted(left_mp_codes & right_mp_codes)
        only_left = sorted(left_mp_codes - right_mp_codes)
        only_right = sorted(right_mp_codes - left_mp_codes)

        left_level1 = {node.code for node in left.level1}
        right_level1 = {node.code for node in right.level1}
        left_has_terminal = cls._has_faston_or_isolator(left_mps)
        right_has_terminal = cls._has_faston_or_isolator(right_mps)

        parts = [
            f"**Comparativo das estruturas — {left.product_code} × {right.product_code}**",
            "",
            cls._summary_table(
                left,
                right,
                left_level1=len(left_level1),
                right_level1=len(right_level1),
                left_has_terminal=left_has_terminal,
                right_has_terminal=right_has_terminal,
            ),
            "",
            f"### 1. Estrutura do {left.product_code}",
            "",
            f"**Produto:** {left.root.description}",
            "",
            cls._intermediate_summary_table(left),
            "",
            f"### 2. Estrutura do {right.product_code}",
            "",
            f"**Produto:** {right.root.description}",
            "",
            cls._intermediate_summary_table(right),
            "",
            "### 3. Componentes (MP) em comum",
            "",
        ]

        if common:
            parts.append(cls._mp_table(left, right, common))
            parts.append("")
            parts.append(
                "**Insight:** há matéria-prima compartilhada entre os dois produtos — "
                "avaliar padronização de compra e estoque."
            )
        else:
            parts.append("- Nenhuma MP em comum nas estruturas retornadas.")

        parts.extend(["", f"### 4. MPs exclusivas do {left.product_code}", ""])

        if only_left:
            parts.append(cls._exclusive_mp_list(left, only_left))
        else:
            parts.append("- Nenhuma MP exclusiva.")

        parts.extend(["", f"### 5. MPs exclusivas do {right.product_code}", ""])

        if only_right:
            parts.append(cls._exclusive_mp_list(right, only_right))
        else:
            parts.append("- Nenhuma MP exclusiva.")

        length_issues = cls._length_discrepancies(left, right)

        if length_issues:
            parts.extend(["", "### 6. Possíveis divergências código × quantidade", ""])

            for severity, product_code, intermediate, code_len, cable_qty in length_issues:
                parts.append(
                    f"- **{severity}** — {product_code} / `{intermediate}`: "
                    f"comprimento no código **{code_len}**, quantidade do cabo **{cable_qty}**."
                )

        parts.extend(
            [
                "",
                "### Conclusão executiva",
                "",
                cls._executive_conclusion(
                    left,
                    right,
                    common_count=len(common),
                    left_has_terminal=left_has_terminal,
                    right_has_terminal=right_has_terminal,
                ),
                "",
                f"_Fonte: API DELPI — /products/{left.product_code}/structure e "
                f"/products/{right.product_code}/structure_",
                "_Status: comparação concluída com base nos retornos reais da API._",
            ]
        )

        return "\n".join(parts)

    @classmethod
    def _summary_table(
        cls,
        left: ProductStructureModel,
        right: ProductStructureModel,
        *,
        left_level1: int,
        right_level1: int,
        left_has_terminal: bool,
        right_has_terminal: bool,
    ) -> str:
        terminal_insight = "Mesmo perfil de montagem."

        if left_has_terminal and not right_has_terminal:
            terminal_insight = (
                f"{left.product_code} possui terminal/isolador; "
                f"{right.product_code} não na estrutura retornada."
            )
        elif right_has_terminal and not left_has_terminal:
            terminal_insight = (
                f"{right.product_code} possui terminal/isolador; "
                f"{left.product_code} não na estrutura retornada."
            )

        level_insight = "Mesma quantidade de intermediários."

        if left_level1 < right_level1:
            level_insight = f"{right.product_code} tem mais itens nível 1 ({right_level1} vs {left_level1})."
        elif left_level1 > right_level1:
            level_insight = f"{left.product_code} tem mais itens nível 1 ({left_level1} vs {right_level1})."

        desc_insight = (
            "Descrições de produto pai distintas — perfis de aplicação provavelmente diferentes."
            if left.root.description != right.root.description
            else "Mesma descrição de produto pai."
        )

        rows = [
            ["Descrição pai", left.root.description, right.root.description, desc_insight],
            ["Tipo", left.root.item_type, right.root.item_type, "Ambos produto acabado." if left.root.item_type == right.root.item_type else "Tipos distintos."],
            ["Intermediários nível 1", str(left_level1), str(right_level1), level_insight],
            [
                "Família intermediários",
                cls._family_prefix(left.level1),
                cls._family_prefix(right.level1),
                "Famílias de código diferentes." if cls._family_prefix(left.level1) != cls._family_prefix(right.level1) else "Mesma família.",
            ],
            [
                "Usa terminal/isolador",
                "Sim" if left_has_terminal else "Não",
                "Sim" if right_has_terminal else "Não",
                terminal_insight,
            ],
            [
                "MPs únicas",
                str(len(left.unique_mp_codes())),
                str(len(right.unique_mp_codes())),
                "Detalhes nas seções de exclusivos.",
            ],
        ]

        return ChatProductStructurePresentationService._table(
            ["Item", left.product_code, right.product_code, "Insight"],
            rows,
        )

    @classmethod
    def _intermediate_summary_table(cls, model: ProductStructureModel) -> str:
        rows = []

        for intermediate in model.level1:
            mps = intermediate.components or []
            cable = next((c for c in mps if model._is_mp(c)), None)
            terminal = next(
                (c for c in mps if "FASTON" in c.description.upper() or "TERM." in c.description.upper()),
                None,
            )
            isolator = next(
                (c for c in mps if "ISOLADOR" in c.description.upper()),
                None,
            )

            rows.append(
                [
                    intermediate.code,
                    intermediate.description,
                    cable.code if cable else "—",
                    terminal.code if terminal else "—",
                    isolator.code if isolator else "—",
                ]
            )

        return ChatProductStructurePresentationService._table(
            ["Intermediário", "Descrição", "Cabo", "Terminal", "Isolador"],
            rows,
        )

    @classmethod
    def _mp_table(
        cls,
        left: ProductStructureModel,
        right: ProductStructureModel,
        codes: list[str],
    ) -> str:
        left_map = {node.code: node for _, node in left.all_mp_nodes()}
        right_map = {node.code: node for _, node in right.all_mp_nodes()}
        rows = []

        for code in codes:
            left_node = left_map.get(code)
            right_node = right_map.get(code)
            rows.append(
                [
                    code,
                    (left_node.description if left_node else "—"),
                    (right_node.description if right_node else "—"),
                ]
            )

        return ChatProductStructurePresentationService._table(
            ["Código", f"Descrição ({left.product_code})", f"Descrição ({right.product_code})"],
            rows,
        )

    @classmethod
    def _exclusive_mp_list(cls, model: ProductStructureModel, codes: list[str]) -> str:
        mp_map = {node.code: node for _, node in model.all_mp_nodes()}
        lines = []

        for code in codes:
            node = mp_map.get(code)

            if not node:
                continue

            lines.append(f"- `{code}` — {node.description}")

        return "\n".join(lines) if lines else "- —"

    @classmethod
    def _length_discrepancies(
        cls,
        left: ProductStructureModel,
        right: ProductStructureModel,
    ) -> list[tuple[str, str, str, int, float | int]]:
        issues: list[tuple[str, str, str, int, float | int]] = []

        for model in (left, right):
            for intermediate in model.level1:
                code_len = ChatProductStructurePresentationService.extract_length_from_intermediate(
                    intermediate.description
                )

                if code_len is None:
                    continue

                for child in intermediate.components or []:
                    if not model._is_mp(child) or child.quantity is None:
                        continue

                    qty = child.quantity

                    if float(qty) != float(code_len):
                        delta = abs(float(qty) - float(code_len))
                        severity = "Alta" if delta >= 10 else "Média"

                        issues.append(
                            (
                                severity,
                                model.product_code,
                                intermediate.code,
                                code_len,
                                int(qty) if float(qty).is_integer() else qty,
                            )
                        )

        return issues

    @classmethod
    def _executive_conclusion(
        cls,
        left: ProductStructureModel,
        right: ProductStructureModel,
        *,
        common_count: int,
        left_has_terminal: bool,
        right_has_terminal: bool,
    ) -> str:
        lines = [
            f"- **{left.product_code}** ({left.root.description}): "
            f"{len(left.level1)} intermediário(s), "
            f"{'com' if left_has_terminal else 'sem'} terminal/isolador na estrutura, "
            f"{len(left.unique_mp_codes())} MP(s) distinta(s).",
            f"- **{right.product_code}** ({right.root.description}): "
            f"{len(right.level1)} intermediário(s), "
            f"{'com' if right_has_terminal else 'sem'} terminal/isolador na estrutura, "
            f"{len(right.unique_mp_codes())} MP(s) distinta(s).",
        ]

        if common_count:
            lines.append(
                f"- Compartilham **{common_count}** MP(s) — oportunidade de padronização."
            )

        return "\n".join(lines)

    @classmethod
    def _has_faston_or_isolator(cls, mp_rows: list[tuple[str | None, StructureNode]]) -> bool:
        for _, node in mp_rows:
            text = node.description.upper()

            if "FASTON" in text or "ISOLADOR" in text or "TERM." in text:
                return True

        return False

    @classmethod
    def _family_prefix(cls, level1: list[StructureNode]) -> str:
        prefixes: set[str] = set()

        for node in level1:
            code = str(node.code or "")

            if len(code) >= 4:
                prefixes.add(code[:4])

        if not prefixes:
            return "—"

        return ", ".join(sorted(prefixes))
