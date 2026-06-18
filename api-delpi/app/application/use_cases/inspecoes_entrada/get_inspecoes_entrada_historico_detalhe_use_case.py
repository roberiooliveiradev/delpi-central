from __future__ import annotations

from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_detalhe_response import (
    InspecoesEntradaHistoricoDetalheResponse,
    InspecoesEntradaHistoricoDetalheSummaryResponse,
    InspecoesEntradaHistoricoDetalheTestResponse,
    InspecoesEntradaHistoricoDetalheTotalsResponse,
)
from app.application.use_cases.inspecoes_entrada.list_inspecoes_entrada_historico_use_case import (
    _as_int,
    _as_str,
    _format_date,
    _format_time,
    _normalize_item,
)
from app.domain.ports.inspecoes_entrada.inspecoes_entrada_repository_port import (
    InspecoesEntradaRepositoryPort,
)

VALID_BRANCHES = frozenset({"01", "02"})

TEST_RESULT_LABELS = {
    "A": "APROVADO",
    "R": "REPROVADO",
}


def _optional_str(value: object) -> str | None:
    text = _as_str(value)
    return text or None


def _optional_int(value: object) -> int | None:
    if value is None or value == "":
        return None
    return _as_int(value)


def _map_test_result(result_code: str) -> tuple[str, str]:
    normalized = result_code.strip().upper()
    if not normalized:
        return "", "NAO_IDENTIFICADO"
    label = TEST_RESULT_LABELS.get(normalized, "NAO_IDENTIFICADO")
    return normalized, label


def _normalize_test(row: dict) -> InspecoesEntradaHistoricoDetalheTestResponse:
    result_code, result = _map_test_result(_as_str(row.get("Codigo_Resultado")))
    return InspecoesEntradaHistoricoDetalheTestResponse(
        test_code=_as_str(row.get("Codigo_Ensaio")),
        test_name=_optional_str(row.get("Nome_Ensaio")),
        expected_specification=_optional_str(row.get("Especificacao_Esperada")),
        text_specification=_optional_str(row.get("Especificacao_Textual")),
        nominal_value=_optional_str(row.get("Valor_Nominal")),
        lower_spec_limit=_optional_str(row.get("Limite_Inferior_Espec")),
        upper_spec_limit=_optional_str(row.get("Limite_Superior_Espec")),
        lower_control_limit=_optional_str(row.get("Limite_Inferior_Controle")),
        upper_control_limit=_optional_str(row.get("Limite_Superior_Controle")),
        min_max_rule=_optional_str(row.get("Regra_Min_Max")),
        specification_unit=_optional_str(row.get("Unidade_Especificacao")),
        text_measured_value=_optional_str(row.get("Medicao_Textual")),
        numeric_measured_value=_optional_str(row.get("Medicao_Numerica")),
        numeric_measurement_indicator=_optional_str(row.get("Indicador_Medicao_Numerica")),
        measured_value=_optional_str(row.get("Valor_Medido")),
        measurement_source=_optional_str(row.get("Fonte_Medicao")),
        result_code=result_code,
        result=result,
        measurement_date=_format_date(row.get("Data_Medicao")),
        measurement_time=_format_time(row.get("Hora_Medicao")),
        sample_number=_optional_int(row.get("Numero_Amostra")),
        laboratory=_optional_str(row.get("Laboratorio")),
        qer_key=_optional_str(row.get("Chave_Qer")),
        sequence_number=_optional_str(row.get("Numero_Sequencia")),
        inspector_registration=_as_str(row.get("Matricula_Ensaiador")),
        inspector_name=_as_str(row.get("Nome_Ensaiador")),
        inspector_login=_as_str(row.get("Login_Ensaiador")),
    )


def _build_totals(
    tests: list[InspecoesEntradaHistoricoDetalheTestResponse],
) -> InspecoesEntradaHistoricoDetalheTotalsResponse:
    approved_tests_count = sum(1 for test in tests if test.result_code == "A")
    failed_tests_count = sum(1 for test in tests if test.result_code == "R")
    return InspecoesEntradaHistoricoDetalheTotalsResponse(
        tests_count=len(tests),
        approved_tests_count=approved_tests_count,
        failed_tests_count=failed_tests_count,
    )


class GetInspecoesEntradaHistoricoDetalheUseCase:
    def __init__(self, repository: InspecoesEntradaRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        branch: str,
        inspection_id: str,
    ) -> InspecoesEntradaHistoricoDetalheResponse | None:
        normalized_branch = str(branch or "").strip()
        if normalized_branch not in VALID_BRANCHES:
            raise ValueError("branch inválida. Use 01 ou 02.")

        normalized_inspection_id = str(inspection_id or "").strip()
        if not normalized_inspection_id:
            raise ValueError("inspection_id é obrigatório.")

        header_row = self._repository.get_historico_header_by_inspection_id(
            normalized_branch,
            normalized_inspection_id,
        )
        if header_row is None:
            return None

        test_rows = self._repository.list_tests_by_inspection_header(
            normalized_branch,
            header_row,
        )
        item = _normalize_item(header_row, normalized_branch)
        tests = [_normalize_test(row) for row in test_rows]

        return InspecoesEntradaHistoricoDetalheResponse(
            branch=normalized_branch,
            inspection_id=item.inspection_id or normalized_inspection_id,
            summary=InspecoesEntradaHistoricoDetalheSummaryResponse.from_item(item),
            tests=tests,
            totals=_build_totals(tests),
        )
