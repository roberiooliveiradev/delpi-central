from __future__ import annotations

from typing import Any

from tm_app.core.sheet_parsing import (
    ensure_uuid,
    normalize_filial,
    parse_bool,
    parse_date,
    parse_int,
    parse_number,
    parse_uuid,
)
from tm_app.domain.raw_data import TransformometroRawData
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class ImportPersistence(PluginBaseRepository):
    """Gravação em lote da migração planilha → Postgres (uma transação)."""

    def truncate_cadastro(self) -> None:
        self.execute(
            """
            TRUNCATE TABLE
                transformometro.dashboard_calculos,
                transformometro.audit_logs,
                transformometro.revisao_recursos_compartilhados,
                transformometro.investimentos,
                transformometro.medicoes,
                transformometro.revisoes,
                transformometro.processos,
                transformometro.recursos_compartilhados
            """,
            auto_commit=False,
        )

    def import_all(self, raw: TransformometroRawData, *, replace_existing: bool) -> dict[str, int]:
        try:
            if replace_existing:
                self.truncate_cadastro()

            counts = {
                "processos": self._import_processos(raw.processos),
                "revisoes": self._import_revisoes(raw.revisoes),
                "medicoes": self._import_medicoes(raw.medicoes),
                "investimentos": self._import_investimentos(raw.investimentos),
                "recursos_compartilhados": self._import_recursos(raw.recursos_compartilhados),
                "vinculos": self._import_vinculos(raw.revisao_recursos_compartilhados),
            }
            self._connection.commit()
            return counts
        except Exception:
            self._connection.rollback()
            raise

    def _import_processos(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            pid = row["processo_id"]
            self.execute(
                """
                INSERT INTO transformometro.processos (
                    processo_id, codigo_processo, nome_processo, descricao_processo,
                    filial_id, setor_id, gestor_responsavel, objetivo_processo,
                    status_processo, deletado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (processo_id) DO UPDATE SET
                    codigo_processo = EXCLUDED.codigo_processo,
                    nome_processo = EXCLUDED.nome_processo,
                    descricao_processo = EXCLUDED.descricao_processo,
                    filial_id = EXCLUDED.filial_id,
                    setor_id = EXCLUDED.setor_id,
                    gestor_responsavel = EXCLUDED.gestor_responsavel,
                    objetivo_processo = EXCLUDED.objetivo_processo,
                    status_processo = EXCLUDED.status_processo,
                    deletado = FALSE,
                    updated_at = NOW()
                """,
                (
                    pid,
                    row["codigo_processo"],
                    row["nome_processo"],
                    row.get("descricao_processo"),
                    row["filial_id"],
                    row["setor_id"],
                    row.get("gestor_responsavel"),
                    row.get("objetivo_processo"),
                    row["status_processo"],
                ),
                auto_commit=False,
            )
            count += 1
        return count

    def _import_revisoes(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            rid = row["revisao_id"]
            self.execute(
                """
                INSERT INTO transformometro.revisoes (
                    revisao_id, processo_id, versao_revisao, chave_unica_processo_revisao,
                    descricao_revisao, motivo_revisao, cenario_tipo,
                    data_implantacao, data_inicio_vigencia, data_fim_vigencia,
                    revisao_ativa, observacoes, deletado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (revisao_id) DO UPDATE SET
                    processo_id = EXCLUDED.processo_id,
                    versao_revisao = EXCLUDED.versao_revisao,
                    chave_unica_processo_revisao = EXCLUDED.chave_unica_processo_revisao,
                    descricao_revisao = EXCLUDED.descricao_revisao,
                    motivo_revisao = EXCLUDED.motivo_revisao,
                    cenario_tipo = EXCLUDED.cenario_tipo,
                    data_implantacao = EXCLUDED.data_implantacao,
                    data_inicio_vigencia = EXCLUDED.data_inicio_vigencia,
                    data_fim_vigencia = EXCLUDED.data_fim_vigencia,
                    revisao_ativa = EXCLUDED.revisao_ativa,
                    observacoes = EXCLUDED.observacoes,
                    deletado = FALSE,
                    updated_at = NOW()
                """,
                (
                    rid,
                    row["processo_id"],
                    row["versao_revisao"],
                    row["chave_unica_processo_revisao"],
                    row.get("descricao_revisao"),
                    row.get("motivo_revisao"),
                    row["cenario_tipo"],
                    row.get("data_implantacao"),
                    row["data_inicio_vigencia"],
                    row.get("data_fim_vigencia"),
                    row["revisao_ativa"],
                    row.get("observacoes"),
                ),
                auto_commit=False,
            )
            count += 1
        return count

    def _import_medicoes(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            mid = row.get("medicao_id")
            if mid:
                self.execute(
                    """
                    INSERT INTO transformometro.medicoes (
                        medicao_id, revisao_id, volume_mensal, tempo_medio_execucao_min,
                        tempo_retrabalho_min, percentual_retrabalho, percentual_erro,
                        quantidade_erros_mes, custo_hora_mao_obra, custo_unitario_erro,
                        custo_unitario_retrabalho, custo_outros_desperdicios,
                        base_referencia_mes, observacoes, deletado
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE
                    )
                    ON CONFLICT (revisao_id) DO UPDATE SET
                        volume_mensal = EXCLUDED.volume_mensal,
                        tempo_medio_execucao_min = EXCLUDED.tempo_medio_execucao_min,
                        tempo_retrabalho_min = EXCLUDED.tempo_retrabalho_min,
                        percentual_retrabalho = EXCLUDED.percentual_retrabalho,
                        percentual_erro = EXCLUDED.percentual_erro,
                        quantidade_erros_mes = EXCLUDED.quantidade_erros_mes,
                        custo_hora_mao_obra = EXCLUDED.custo_hora_mao_obra,
                        custo_unitario_erro = EXCLUDED.custo_unitario_erro,
                        custo_unitario_retrabalho = EXCLUDED.custo_unitario_retrabalho,
                        custo_outros_desperdicios = EXCLUDED.custo_outros_desperdicios,
                        base_referencia_mes = EXCLUDED.base_referencia_mes,
                        observacoes = EXCLUDED.observacoes,
                        deletado = FALSE,
                        updated_at = NOW()
                    """,
                    (
                        mid,
                        row["revisao_id"],
                        row["volume_mensal"],
                        row["tempo_medio_execucao_min"],
                        row["tempo_retrabalho_min"],
                        row["percentual_retrabalho"],
                        row["percentual_erro"],
                        row["quantidade_erros_mes"],
                        row["custo_hora_mao_obra"],
                        row["custo_unitario_erro"],
                        row["custo_unitario_retrabalho"],
                        row["custo_outros_desperdicios"],
                        row.get("base_referencia_mes"),
                        row.get("observacoes"),
                    ),
                    auto_commit=False,
                )
            else:
                self.execute(
                    """
                    INSERT INTO transformometro.medicoes (
                        revisao_id, volume_mensal, tempo_medio_execucao_min,
                        tempo_retrabalho_min, percentual_retrabalho, percentual_erro,
                        quantidade_erros_mes, custo_hora_mao_obra, custo_unitario_erro,
                        custo_unitario_retrabalho, custo_outros_desperdicios,
                        base_referencia_mes, observacoes, deletado
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                    ON CONFLICT (revisao_id) DO UPDATE SET
                        volume_mensal = EXCLUDED.volume_mensal,
                        tempo_medio_execucao_min = EXCLUDED.tempo_medio_execucao_min,
                        tempo_retrabalho_min = EXCLUDED.tempo_retrabalho_min,
                        percentual_retrabalho = EXCLUDED.percentual_retrabalho,
                        percentual_erro = EXCLUDED.percentual_erro,
                        quantidade_erros_mes = EXCLUDED.quantidade_erros_mes,
                        custo_hora_mao_obra = EXCLUDED.custo_hora_mao_obra,
                        custo_unitario_erro = EXCLUDED.custo_unitario_erro,
                        custo_unitario_retrabalho = EXCLUDED.custo_unitario_retrabalho,
                        custo_outros_desperdicios = EXCLUDED.custo_outros_desperdicios,
                        base_referencia_mes = EXCLUDED.base_referencia_mes,
                        observacoes = EXCLUDED.observacoes,
                        deletado = FALSE,
                        updated_at = NOW()
                    """,
                    (
                        row["revisao_id"],
                        row["volume_mensal"],
                        row["tempo_medio_execucao_min"],
                        row["tempo_retrabalho_min"],
                        row["percentual_retrabalho"],
                        row["percentual_erro"],
                        row["quantidade_erros_mes"],
                        row["custo_hora_mao_obra"],
                        row["custo_unitario_erro"],
                        row["custo_unitario_retrabalho"],
                        row["custo_outros_desperdicios"],
                        row.get("base_referencia_mes"),
                        row.get("observacoes"),
                    ),
                    auto_commit=False,
                )
            count += 1
        return count

    def _import_investimentos(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            iid = row["investimento_id"]
            self.execute(
                """
                INSERT INTO transformometro.investimentos (
                    investimento_id, revisao_id, tipo_investimento, categoria_investimento,
                    descricao_item, quantidade, valor_unitario, valor_total,
                    data_investimento, recorrencia, meses_vigencia, centro_custo,
                    observacoes, deletado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (investimento_id) DO UPDATE SET
                    revisao_id = EXCLUDED.revisao_id,
                    tipo_investimento = EXCLUDED.tipo_investimento,
                    categoria_investimento = EXCLUDED.categoria_investimento,
                    descricao_item = EXCLUDED.descricao_item,
                    quantidade = EXCLUDED.quantidade,
                    valor_unitario = EXCLUDED.valor_unitario,
                    valor_total = EXCLUDED.valor_total,
                    data_investimento = EXCLUDED.data_investimento,
                    recorrencia = EXCLUDED.recorrencia,
                    meses_vigencia = EXCLUDED.meses_vigencia,
                    centro_custo = EXCLUDED.centro_custo,
                    observacoes = EXCLUDED.observacoes,
                    deletado = FALSE,
                    updated_at = NOW()
                """,
                (
                    iid,
                    row["revisao_id"],
                    row["tipo_investimento"],
                    row.get("categoria_investimento"),
                    row["descricao_item"],
                    row["quantidade"],
                    row["valor_unitario"],
                    row["valor_total"],
                    row.get("data_investimento"),
                    row.get("recorrencia", "unico"),
                    row.get("meses_vigencia"),
                    row.get("centro_custo"),
                    row.get("observacoes"),
                ),
                auto_commit=False,
            )
            count += 1
        return count

    def _import_recursos(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            rid = row["recurso_compartilhado_id"]
            self.execute(
                """
                INSERT INTO transformometro.recursos_compartilhados (
                    recurso_compartilhado_id, codigo_recurso, nome_recurso,
                    categoria_recurso, fornecedor, tipo_custo, recorrencia,
                    valor_total_recorrente, data_inicio_vigencia, data_fim_vigencia,
                    centro_custo, criterio_rateio, status_recurso, observacoes, deletado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (recurso_compartilhado_id) DO UPDATE SET
                    codigo_recurso = EXCLUDED.codigo_recurso,
                    nome_recurso = EXCLUDED.nome_recurso,
                    categoria_recurso = EXCLUDED.categoria_recurso,
                    fornecedor = EXCLUDED.fornecedor,
                    tipo_custo = EXCLUDED.tipo_custo,
                    recorrencia = EXCLUDED.recorrencia,
                    valor_total_recorrente = EXCLUDED.valor_total_recorrente,
                    data_inicio_vigencia = EXCLUDED.data_inicio_vigencia,
                    data_fim_vigencia = EXCLUDED.data_fim_vigencia,
                    centro_custo = EXCLUDED.centro_custo,
                    criterio_rateio = EXCLUDED.criterio_rateio,
                    status_recurso = EXCLUDED.status_recurso,
                    observacoes = EXCLUDED.observacoes,
                    deletado = FALSE,
                    updated_at = NOW()
                """,
                (
                    rid,
                    row["codigo_recurso"],
                    row["nome_recurso"],
                    row.get("categoria_recurso"),
                    row.get("fornecedor"),
                    row["tipo_custo"],
                    row["recorrencia"],
                    row["valor_total_recorrente"],
                    row.get("data_inicio_vigencia"),
                    row.get("data_fim_vigencia"),
                    row.get("centro_custo"),
                    row.get("criterio_rateio", "igualitario"),
                    row.get("status_recurso", "ativo"),
                    row.get("observacoes"),
                ),
                auto_commit=False,
            )
            count += 1
        return count

    def _import_vinculos(self, rows: list[dict]) -> int:
        count = 0
        for row in rows:
            vid = row["vinculo_id"]
            self.execute(
                """
                INSERT INTO transformometro.revisao_recursos_compartilhados (
                    vinculo_id, revisao_id, recurso_compartilhado_id,
                    data_inicio_uso, data_fim_uso, ativo, peso_rateio, observacoes, deletado
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, FALSE)
                ON CONFLICT (vinculo_id) DO UPDATE SET
                    revisao_id = EXCLUDED.revisao_id,
                    recurso_compartilhado_id = EXCLUDED.recurso_compartilhado_id,
                    data_inicio_uso = EXCLUDED.data_inicio_uso,
                    data_fim_uso = EXCLUDED.data_fim_uso,
                    ativo = EXCLUDED.ativo,
                    peso_rateio = EXCLUDED.peso_rateio,
                    observacoes = EXCLUDED.observacoes,
                    deletado = FALSE,
                    updated_at = NOW()
                """,
                (
                    vid,
                    row["revisao_id"],
                    row["recurso_compartilhado_id"],
                    row.get("data_inicio_uso"),
                    row.get("data_fim_uso"),
                    row.get("ativo", True),
                    row.get("peso_rateio"),
                    row.get("observacoes"),
                ),
                auto_commit=False,
            )
            count += 1
        return count


def normalize_raw_rows(raw: TransformometroRawData) -> TransformometroRawData:
    """Converte linhas da planilha para tipos graváveis no Postgres."""

    processos: list[dict[str, Any]] = []
    for idx, row in enumerate(raw.processos, start=1):
        pid = ensure_uuid_row(row, "processo_id")
        codigo = (row.get("codigo_processo") or "").strip() or f"PROC-IMPORT-{idx:04d}"
        processos.append(
            {
                "processo_id": pid,
                "codigo_processo": codigo,
                "nome_processo": (row.get("nome_processo") or codigo).strip(),
                "descricao_processo": row.get("descricao_processo"),
                "filial_id": normalize_filial_row(row.get("filial_id")),
                "setor_id": (row.get("setor_id") or "geral").strip(),
                "gestor_responsavel": row.get("gestor_responsavel"),
                "objetivo_processo": row.get("objetivo_processo"),
                "status_processo": (row.get("status_processo") or "ativo").strip(),
            }
        )

    processo_ids = {p["processo_id"] for p in processos}
    processo_by_codigo = {p["codigo_processo"]: p["processo_id"] for p in processos}

    revisoes: list[dict[str, Any]] = []
    for row in raw.revisoes:
        pid = parse_uuid(row.get("processo_id"))
        if not pid and row.get("codigo_processo"):
            pid = processo_by_codigo.get(str(row.get("codigo_processo")).strip())
        rid = ensure_uuid_row(row, "revisao_id")
        versao = (row.get("versao_revisao") or "1.0.0").strip()
        revisoes.append(
            {
                "revisao_id": rid,
                "processo_id": pid,
                "versao_revisao": versao,
                "chave_unica_processo_revisao": f"{pid}|{versao}",
                "descricao_revisao": row.get("descricao_revisao"),
                "motivo_revisao": row.get("motivo_revisao"),
                "cenario_tipo": (row.get("cenario_tipo") or "baseline").strip(),
                "data_implantacao": parse_date(row.get("data_implantacao")),
                "data_inicio_vigencia": parse_date(row.get("data_inicio_vigencia"))
                or "2000-01-01",
                "data_fim_vigencia": parse_date(row.get("data_fim_vigencia")),
                "revisao_ativa": parse_bool(row.get("revisao_ativa")),
                "observacoes": row.get("observacoes"),
            }
        )

    revisao_ids = {r["revisao_id"] for r in revisoes}

    medicoes = [
        {
            "medicao_id": parse_uuid(row.get("medicao_id")),
            "revisao_id": parse_uuid(row.get("revisao_id")),
            "volume_mensal": parse_number(row.get("volume_mensal")),
            "tempo_medio_execucao_min": parse_number(row.get("tempo_medio_execucao_min")),
            "tempo_retrabalho_min": parse_number(row.get("tempo_retrabalho_min")),
            "percentual_retrabalho": parse_number(row.get("percentual_retrabalho")),
            "percentual_erro": parse_number(row.get("percentual_erro")),
            "quantidade_erros_mes": parse_number(row.get("quantidade_erros_mes")),
            "custo_hora_mao_obra": parse_number(row.get("custo_hora_mao_obra")),
            "custo_unitario_erro": parse_number(row.get("custo_unitario_erro")),
            "custo_unitario_retrabalho": parse_number(row.get("custo_unitario_retrabalho")),
            "custo_outros_desperdicios": parse_number(row.get("custo_outros_desperdicios")),
            "base_referencia_mes": (row.get("base_referencia_mes") or "").strip() or None,
            "observacoes": row.get("observacoes"),
        }
        for row in raw.medicoes
    ]

    investimentos = []
    for row in raw.investimentos:
        qty = parse_number(row.get("quantidade"), 1)
        unit = parse_number(row.get("valor_unitario"))
        total = parse_number(row.get("valor_total"), round(qty * unit, 2))
        investimentos.append(
            {
                "investimento_id": ensure_uuid_row(row, "investimento_id"),
                "revisao_id": parse_uuid(row.get("revisao_id")),
                "tipo_investimento": (row.get("tipo_investimento") or "unico").strip(),
                "categoria_investimento": row.get("categoria_investimento"),
                "descricao_item": (row.get("descricao_item") or "Item").strip(),
                "quantidade": qty,
                "valor_unitario": unit,
                "valor_total": total,
                "data_investimento": parse_date(row.get("data_investimento")),
                "recorrencia": (row.get("recorrencia") or "unico").strip(),
                "meses_vigencia": parse_int(row.get("meses_vigencia")),
                "centro_custo": row.get("centro_custo"),
                "observacoes": row.get("observacoes"),
            }
        )

    recursos = []
    for idx, row in enumerate(raw.recursos_compartilhados, start=1):
        recursos.append(
            {
                "recurso_compartilhado_id": ensure_uuid_row(row, "recurso_compartilhado_id"),
                "codigo_recurso": (row.get("codigo_recurso") or f"RC-IMPORT-{idx:04d}").strip(),
                "nome_recurso": (row.get("nome_recurso") or f"Recurso {idx}").strip(),
                "categoria_recurso": row.get("categoria_recurso"),
                "fornecedor": row.get("fornecedor"),
                "tipo_custo": (row.get("tipo_custo") or "assinatura").strip(),
                "recorrencia": (row.get("recorrencia") or "mensal").strip(),
                "valor_total_recorrente": parse_number(row.get("valor_total_recorrente")),
                "data_inicio_vigencia": parse_date(row.get("data_inicio_vigencia")),
                "data_fim_vigencia": parse_date(row.get("data_fim_vigencia")),
                "centro_custo": row.get("centro_custo"),
                "criterio_rateio": (row.get("criterio_rateio") or "igualitario").strip(),
                "status_recurso": (row.get("status_recurso") or "ativo").strip(),
                "observacoes": row.get("observacoes"),
            }
        )

    recurso_ids = {r["recurso_compartilhado_id"] for r in recursos}

    vinculos = [
        {
            "vinculo_id": ensure_uuid_row(row, "vinculo_id"),
            "revisao_id": parse_uuid(row.get("revisao_id")),
            "recurso_compartilhado_id": parse_uuid(row.get("recurso_compartilhado_id")),
            "data_inicio_uso": parse_date(row.get("data_inicio_uso")),
            "data_fim_uso": parse_date(row.get("data_fim_uso")),
            "ativo": parse_bool(row.get("ativo"), default=True),
            "peso_rateio": parse_number(row.get("peso_rateio")) if row.get("peso_rateio") else None,
            "observacoes": row.get("observacoes"),
        }
        for row in raw.revisao_recursos_compartilhados
    ]

    return TransformometroRawData(
        processos=processos,
        revisoes=revisoes,
        medicoes=medicoes,
        investimentos=investimentos,
        recursos_compartilhados=recursos,
        revisao_recursos_compartilhados=vinculos,
    )


def ensure_uuid_row(row: dict, field: str) -> str:
    return ensure_uuid(row.get(field))


def normalize_filial_row(value: Any) -> str:
    return normalize_filial(value)
