"""Gateways falsos — os testes não tocam api-delpi nem strategic-indicators-api."""

from __future__ import annotations

from typing import Any

from tests.conftest import envelope

DELINQUENCY_PERIOD = {
    "data_inicio": "2025-08-01",
    "data_fim_exclusiva": "2026-08-01",
    "rotulo": "Últimos 12 meses completos",
}

COST_CENTER_PERIOD = {"data_inicio": "01/08/2026", "data_fim": "22/08/2026"}


class FakeFinancialGateway:
    """Devolve payloads no formato da api-delpi e registra as chamadas."""

    def __init__(self, *, failing: set[str] | None = None) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self._failing = failing or set()

    def _record(self, name: str, **kwargs: Any) -> None:
        if name in self._failing:
            raise RuntimeError(f"gateway indisponível: {name}")
        self.calls.append((name, kwargs))

    def call_kwargs(self, name: str) -> dict[str, Any]:
        for called, kwargs in self.calls:
            if called == name:
                return kwargs
        raise AssertionError(f"gateway não recebeu a chamada {name}. Chamadas: {self.calls}")

    # ------------------------------------------------------------------ delinquency

    def fetch_delinquency_summary(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_delinquency_summary", **kwargs)
        return envelope(
            {
                "periodo": DELINQUENCY_PERIOD,
                "totais": {
                    "titulos": 120,
                    "titulos_em_dia": 96,
                    "titulos_atraso": 24,
                    "valor_total": 1_500_000.0,
                    "valor_em_dia": 1_200_000.0,
                    "valor_atraso": 300_000.0,
                },
                "indicadores": {
                    "percentual_em_dia_qtd": 80.0,
                    "percentual_em_dia_valor": 80.0,
                    "media_dias_atraso": 7.5,
                },
            }
        )

    def fetch_delinquency_monthly(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_delinquency_monthly", **kwargs)
        return envelope(
            {
                "periodo": DELINQUENCY_PERIOD,
                "items": [
                    {
                        "mes": "08/2026",
                        "ano_mes": "2026-08",
                        "total_titulos": 10,
                        "titulos_em_dia": 8,
                        "titulos_atraso": 2,
                        "valor_total": 100_000.0,
                        "valor_em_dia": 80_000.0,
                        "valor_atraso": 20_000.0,
                        "percentual_em_dia_qtd": 80.0,
                        "percentual_em_dia_valor": 80.0,
                    }
                ],
            }
        )

    def fetch_delinquency_aging(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_delinquency_aging", **kwargs)
        return envelope(
            {
                "periodo": DELINQUENCY_PERIOD,
                "items": [
                    {
                        "codigo": "ATRASO_1_A_5_DIAS",
                        "rotulo": "1 a 5 dias",
                        "ordem": 2,
                        "quantidade": 12,
                        "valor": 90_000.0,
                        "percentual_quantidade": 10.0,
                        "percentual_valor": 6.0,
                    },
                    {
                        "codigo": "EM_DIA",
                        "rotulo": "Em dia",
                        "ordem": 1,
                        "quantidade": 96,
                        "valor": 1_200_000.0,
                        "percentual_quantidade": 80.0,
                        "percentual_valor": 80.0,
                    },
                ],
            }
        )

    def fetch_delinquency_customers(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_delinquency_customers", **kwargs)
        return envelope(
            {
                "periodo": DELINQUENCY_PERIOD,
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 1,
                    "total": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "is_complete": True,
                },
                "sort": {"sort_by": "late_amount", "sort_dir": "desc"},
                "items": [
                    {
                        "cliente_codigo": "000001",
                        "loja": "01",
                        "nome_cliente": "WEG EQUIPAMENTOS ELETRICOS SA",
                        "nome_reduzido": "WEG",
                        "total_titulos": 40,
                        "titulos_em_dia": 30,
                        "titulos_atraso": 10,
                        "valor_total": 800_000.0,
                        "valor_atraso": 120_000.0,
                        "percentual_em_dia_qtd": 75.0,
                        "percentual_em_dia_valor": 85.0,
                    }
                ],
            }
        )

    def fetch_delinquency_titles(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_delinquency_titles", **kwargs)
        return envelope(
            {
                "periodo": DELINQUENCY_PERIOD,
                "pagination": {
                    "page": 1,
                    "page_size": 20,
                    "total_items": 1,
                    "total": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "is_complete": True,
                },
                "sort": {"sort_by": "amount", "sort_dir": "desc"},
                "items": [
                    {
                        "filial": "01",
                        "prefixo": "001",
                        "numero": "000123456",
                        "parcela": "A",
                        "tipo": "NF",
                        "cliente_codigo": "000001",
                        "loja": "01",
                        "nome_cliente": "WEG EQUIPAMENTOS ELETRICOS SA",
                        "nome_reduzido": "WEG",
                        "data_emissao": "2026-07-01",
                        "data_vencimento_real": "2026-07-31",
                        "data_baixa": "2026-08-04",
                        "valor_titulo": 25_000.0,
                        "pago_em_dia": False,
                        "dias_atraso": 4,
                        "faixa_atraso": {"codigo": "ATRASO_1_A_5_DIAS", "rotulo": "1 a 5 dias"},
                    }
                ],
            }
        )

    # ------------------------------------------------------------------ cost centers

    def fetch_cost_center_filters(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_filters", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "filiais": [{"filial": "01", "descricao": "Matriz SC"}],
                "centros_custo": [{"codigo": "1101", "descricao": "MANUTENCAO"}],
                "fornecedores": [
                    {"codigo": "000045", "loja": "01", "razao_social": "FORNECEDOR X LTDA"}
                ],
            }
        )

    def fetch_cost_center_summary(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_summary", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "total_periodo": 450_000.0,
                "quantidade_lancamentos": 320,
                "quantidade_centros_custo": 18,
                "quantidade_fornecedores": 47,
                "ticket_medio": 1_406.25,
                "maior_lancamento": 38_000.0,
            }
        )

    def fetch_cost_center_series(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_series", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "serie": [
                    {
                        "ano_mes": "2026-08",
                        "ano": 2026,
                        "mes": 8,
                        "valor_total": 450_000.0,
                        "quantidade_lancamentos": 320,
                    }
                ],
            }
        )

    def fetch_cost_center_ranking_centers(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_ranking_centers", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "ranking": [
                    {
                        "centro_custo_codigo": "1101",
                        "centro_custo_descricao": "MANUTENCAO",
                        "valor_total": 120_000.0,
                        "quantidade_lancamentos": 55,
                        "percentual": 26.7,
                    }
                ],
            }
        )

    def fetch_cost_center_ranking_suppliers(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_ranking_suppliers", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "ranking": [
                    {
                        "fornecedor_cliente_codigo": "000045",
                        "loja": "01",
                        "razao_social": "FORNECEDOR X LTDA",
                        "valor_total": 90_000.0,
                        "quantidade_lancamentos": 21,
                        "percentual": 20.0,
                    }
                ],
            }
        )

    def fetch_cost_center_entries(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_cost_center_entries", **kwargs)
        return envelope(
            {
                "periodo": COST_CENTER_PERIOD,
                "pagination": {
                    "page": 1,
                    "page_size": 50,
                    "total_items": 1,
                    "total": 1,
                    "total_pages": 1,
                    "has_next": False,
                    "has_previous": False,
                    "is_complete": True,
                },
                "sort": {"sort_by": "data_emissao", "sort_dir": "desc"},
                "items": [
                    {
                        "filial": "01",
                        "data_emissao": "2026-08-12",
                        "data_emissao_formatada": "12/08/2026",
                        "centro_custo_codigo": "1101",
                        "centro_custo_descricao": "MANUTENCAO",
                        "fornecedor_cliente_codigo": "000045",
                        "loja": "01",
                        "razao_social": "FORNECEDOR X LTDA",
                        "documento": "000998877",
                        "serie": "1",
                        "pedido": "015432",
                        "item": "01",
                        "item_pedido": "01",
                        "produto_codigo": "9000123",
                        "produto_descricao": "ROLAMENTO 6204",
                        "observacoes": "",
                        "quantidade": 4.0,
                        "valor_unitario": 250.0,
                        "valor_total": 1_000.0,
                        "conta_contabil": "41010001",
                        "rateio": "N",
                        "tes": "101",
                        "cfop": "1102",
                        "tipo_documento": "NF",
                        "tipo_produto_lancamento": "MC",
                        "recno_sd1": 998877,
                    }
                ],
            }
        )

    # ------------------------------------------------------------------ KPIs

    def fetch_rol_invoices(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_rol_invoices", **kwargs)
        return envelope(
            {
                "branch": kwargs.get("branch") or "consolidated",
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
                "truncated": False,
                "items": [
                    {
                        "kind": "sale",
                        "branch": "01",
                        "issue_date": "2026-08-02",
                        "invoice_number": "000123",
                        "series": "1",
                        "customer_code": "000001",
                        "customer_store": "01",
                        "customer_name": "WEG EQUIPAMENTOS ELETRICOS SA",
                        "gross": 1480.0,
                        "discounts": 20.0,
                        "returns": 0.0,
                        "taxes": 210.0,
                        "rol": 1250.0,
                    },
                    {
                        "kind": "return",
                        "branch": "01",
                        "issue_date": "2026-08-10",
                        "invoice_number": "000050",
                        "series": "1",
                        "customer_code": "000002",
                        "customer_store": "01",
                        "customer_name": "CLIENTE DEVOLUCAO",
                        "gross": 0.0,
                        "discounts": 0.0,
                        "returns": 80.0,
                        "taxes": 0.0,
                        "rol": -80.0,
                    },
                ],
                "totals": {
                    "count": 2,
                    "gross": 1480.0,
                    "discounts": 20.0,
                    "returns": 80.0,
                    "taxes": 210.0,
                    "rol": 1170.0,
                },
                "pagination": {
                    "limit": kwargs.get("limit") or 8000,
                    "offset": 0,
                    "returned": 2,
                    "is_complete": True,
                },
            }
        )

    def fetch_rol(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_rol", **kwargs)
        return envelope(
            {
                "rol": 5_000_000.0,
                "gross_revenue": 6_200_000.0,
                "other_values": 0.0,
                "items_without_tes": 0.0,
                "returns": 180_000.0,
                "discounts": 90_000.0,
                "icms": 720_000.0,
                "iss": 0.0,
                "pis": 80_000.0,
                "cofins": 370_000.0,
                "ipi_separated": 0.0,
                "rol_taxes": 1_200_000.0,
                "financial_titles": 0.0,
                "financial_balance": 0.0,
                "target": 5_500_000.0,
                "rol_target_pct": 90.91,
                "goal_label": "Meta SI",
            }
        )

    def fetch_rol_series(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_rol_series", **kwargs)
        return envelope(
            {
                "granularity": kwargs.get("granularity") or "month",
                "truncated": False,
                "points": [
                    {
                        "periodo": "2026-08",
                        "sort_key": "2026-08",
                        "start_date": "2026-08-01",
                        "end_date": "2026-08-31",
                        "rol_matrix": 3_200_000.0,
                        "rol_branch": 1_800_000.0,
                    },
                    {
                        "periodo": "2026-09",
                        "sort_key": "2026-09",
                        "start_date": "2026-09-01",
                        "end_date": "2026-09-30",
                        "rol_matrix": 2_900_000.0,
                        "rol_branch": 1_500_000.0,
                    },
                ],
            }
        )

    def fetch_rol_by_customer(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_rol_by_customer", **kwargs)
        return envelope(
            {
                "branch": kwargs.get("branch") or "",
                "start_date": kwargs.get("start_date"),
                "end_date": kwargs.get("end_date"),
                "items": [
                    {
                        "customer_code": "000001",
                        "customer_store": "01",
                        "customer_name": "WEG EQUIPAMENTOS ELETRICOS SA",
                        "rol": 1_250_000.0,
                        "gross_revenue": 1_480_000.0,
                        "share_pct": 25.0,
                        "rank": 1,
                    }
                ],
                "others": {
                    "customer_code": "",
                    "customer_store": "",
                    "customer_name": "Demais clientes",
                    "rol": 3_750_000.0,
                    "gross_revenue": 4_720_000.0,
                    "share_pct": 75.0,
                    "rank": 0,
                },
                "summary": {"total_rol": 5_000_000.0, "customers_count": 48, "items_count": 1},
            }
        )

    def fetch_rol_by_branch(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_rol_by_branch", **kwargs)
        return envelope(
            {
                "items": [
                    {
                        "branch": "01",
                        "rol": 3_200_000.0,
                        "gross_revenue": 3_900_000.0,
                        "returns": 110_000.0,
                        "discounts": 50_000.0,
                    },
                    {
                        "branch": "02",
                        "rol": 1_800_000.0,
                        "gross_revenue": 2_300_000.0,
                        "returns": 70_000.0,
                        "discounts": 40_000.0,
                    },
                ],
                "summary": {"items_count": 2, "total_rol": 5_000_000.0},
            }
        )

    def fetch_ebitda_pct(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_ebitda_pct", **kwargs)
        return envelope({"ebitda_over_rol_pct": 18.4, "ebitda_value": 920_000.0, "target": 20.0})

    def fetch_fixed_cost_pct(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_fixed_cost_pct", **kwargs)
        return envelope(
            {"fixed_cost_over_rol_pct": 12.1, "fixed_cost_value": 605_000.0, "target": 11.0}
        )

    def fetch_pmr(self, **kwargs: Any) -> dict[str, Any]:
        self._record("fetch_pmr", **kwargs)
        return envelope({"pmr_days": 47.0, "target": 45.0})


class FakeStrategicIndicatorsGateway:
    def __init__(self, *, failing: bool = False, partial: bool = False) -> None:
        self.failing = failing
        self.partial = partial
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def fetch_department_indicators(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("fetch_department_indicators", kwargs))
        if self.failing:
            from financial_app.domain.errors import StrategicIndicatorsGatewayError

            raise StrategicIndicatorsGatewayError("SI fora do ar")
        return {
            "item": {
                "department_id": "financial",
                "department_name": "Financeiro",
                "short_name": "FIN",
                "idd": 8.4,
                "score": 8.4,
                "classification": "bom",
                "contribution": 1.2,
                "aggregation_mode": "weighted",
                "partial_success": self.partial,
                "indicators": [
                    {
                        "indicator_id": "fin-ebitda",
                        "name": "EBITDA / ROL",
                        "weight_pct": 40.0,
                        "goal_label": "≥ 20%",
                        "goal_value": 20.0,
                        "goal_periodicity": "monthly",
                        "goal_mode": "standard",
                        "performance_direction": "higher_is_better",
                        "value": 18.4,
                        "has_value": True,
                        "score": 8.0,
                        "gap": -1.6,
                        "classification": "atencao",
                        "value_unit": "%",
                        "value_decimals": 1,
                    }
                ],
            }
        }

    def fetch_departments_indicators(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("fetch_departments_indicators", kwargs))
        return {"items": []}

    def fetch_global_score(self, **kwargs: Any) -> dict[str, Any]:
        self.calls.append(("fetch_global_score", kwargs))
        if self.failing:
            from financial_app.domain.errors import StrategicIndicatorsGatewayError

            raise StrategicIndicatorsGatewayError("SI fora do ar")
        return {
            "competence": "2026-08",
            "igd": 7.9,
            "classification": "bom",
            "trendDirection": "up",
            "bestDepartment": "Qualidade",
            "primaryRisk": "Manutenção",
        }
