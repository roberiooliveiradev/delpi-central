from unittest.mock import patch

from tm_app.application.services.dashboard_export_service import DashboardExportService


@patch(
    "tm_app.application.services.dashboard_export_service.DashboardLiveService"
)
def test_build_excel_html_includes_pt_headers(mock_live):
    mock_live.return_value.build_summary.return_value = {
        "economia_bruta_total": 1000,
        "economia_liquida_total": 600,
        "investimento_unico_total": 100,
        "custo_recorrente_total": 200,
        "custo_recursos_compartilhados_total": 100,
        "investimento_total": 400,
    }
    mock_live.return_value.query_export_rows.return_value = [
        {
            "codigo_processo": "P-001",
            "nome_processo": "Teste",
            "familia_processo": "ia",
            "agrupador_ferramenta": "chatgpt",
            "filial_id": "01",
            "setor_id": "engenharia",
            "competencia": "2026-01",
            "cenario_tipo": "melhoria",
            "economia_bruta": 1000,
            "economia_liquida_mes": 800,
            "investimento_unico_mes": 0,
            "custo_recorrente_mes": 200,
            "horas_economizadas_mes": 10,
        }
    ]

    html_out = DashboardExportService().build_excel_html(filial_id="01")

    assert "Código processo" in html_out
    assert "Economia líquida mês" in html_out
    assert "P-001" in html_out
    assert "<table>" in html_out
    assert "TOTAIS DO RECORTE" in html_out
    assert "ROI acumulado" in html_out


@patch(
    "tm_app.application.services.dashboard_export_service.DashboardLiveService"
)
def test_build_csv_appends_summary_row(mock_live):
    mock_live.return_value.build_summary.return_value = {
        "economia_bruta_total": 500,
        "economia_liquida_total": 300,
        "investimento_unico_total": 50,
        "custo_recorrente_total": 100,
        "custo_recursos_compartilhados_total": 50,
        "investimento_total": 200,
    }
    mock_live.return_value.query_export_rows.return_value = [
        {
            "codigo_processo": "P-001",
            "nome_processo": "Teste",
            "familia_processo": "",
            "agrupador_ferramenta": "",
            "filial_id": "01",
            "setor_id": "eng",
            "competencia": "2026-01",
            "cenario_tipo": "melhoria",
            "economia_bruta": 500,
            "economia_liquida_mes": 300,
            "investimento_unico_mes": 50,
            "custo_recorrente_mes": 100,
            "custo_recursos_compartilhados_mes": 50,
            "investimento_total_mes": 200,
            "horas_economizadas_mes": 5,
        }
    ]

    csv_out = DashboardExportService().build_csv()

    assert "TOTAIS DO RECORTE" in csv_out
    assert "ROI acumulado 1.5×" in csv_out
