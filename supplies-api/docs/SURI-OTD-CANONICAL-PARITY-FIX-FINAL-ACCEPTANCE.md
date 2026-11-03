# SURI OTD Parity Fix — Final Acceptance

OTD_OFFICIAL_SOURCE=PASS (source_consolidated via api-delpi
  branch=None — mesmo valor publicado pelo SI)
OTD_SINGLE_BRANCH=PASS (95.86 preservado, method=branch)
OTD_CONSOLIDATED=PASS (91.12 live, method=source_consolidated)
OTD_PERIOD_FILTERS=PASS (custom + competence)
OVERVIEW_PARITY=PASS · OTD_PAGE_PARITY=PASS · SURI_PARITY=PASS
  (todos = 91.12 no período; 94.27 em setembro)
GOAL_SEMANTICS=PASS (KPI-OTD goals inalterados)
IDD_UNCHANGED=PASS (nenhum cálculo de score tocado)
OTHER_SUPPLIES_KPIS=REGRESSION_PASS (~429 testes)
AUTHZ=PASS · UNIT_SCOPE=PASS (require_unit preservado;
  consolidado só quando usuário tem acesso às filiais)
MCP_TOOL_COUNT=5 · MCP_CONTRACT=COMPATIBLE (campo aditivo)
DEPLOY=PASS (server merge 00d197b3fa, container healthy)
AUTHENTICATED_RUNTIME=PASS (3 consultas live como user)
STOP_CONDITIONS: nenhuma ativada
