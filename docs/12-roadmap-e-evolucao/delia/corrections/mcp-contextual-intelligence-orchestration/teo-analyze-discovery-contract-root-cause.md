# Root cause — TÉO analyze, discovery e schema efetivo

TASK_ID: DELIA-C3-TEO-MCP-DISCOVERY-ANALYZE-CONTRACT-ROOT-CAUSE-01
BASE_HEAD: 698916cf81 | evidência: código TÉO + artifact tipado B2

## Q1 — Contrato analyze (server.py:131-216)

Signature: analyze(view, params=None, filial_id=None, setor_id=None,
processo_id=None, revisao_id=None, instancia_id=None, familia_processo,
competencia, competencia_inicio/fim, horizonte_meses, limit).
Descrição lista o vocabulário completo de views incluindo
`dashboard_strategic_indicators` — DESCRIPTION_ADEQUATE para B2.

## Q2 — Schema efetivo: apenas `view` é required (todos os filtros
Optional). filial_id/setor_id EXISTEM como flat args e via params —
preservados owner→MCP→catálogo→toolset (typed trace provou).

## Q3 — Obrigatoriedade CONDICIONAL POR VIEW (regra de domínio runtime):
#6 usou view tipo "departamento" (exige filial_id+setor_id) → 400 legítimo.
#7 usou view dashboard (não exige) → SUCCESS. H6 PROVEN — chamadas com
contratos diferentes, não equivalentes. A condicionalidade NÃO é
expressa no JSON Schema (impossível representar required-por-view em
schema simples) — está apenas em prosa + validação runtime do owner.

## Q4 — Discovery: as 3× discover foram chamadas ao DAVI (api-delpi),
catálogo de actions api-delpi — TÉO tools NÃO estão no escopo desse
catálogo. As ferramentas TÉO (read/analyze/get_context) já estavam no
MCPToolset do Agent com schemas completos — o modelo não precisava do
discovery DAVI para achá-las. H4 PROVEN (model churn, selection).

## Matriz causal
H1 TEO_CONTRACT: PARTIAL — required condicional só em prosa/runtime
  (limitação inerente de JSON Schema; erro 400 é o contrato falando)
H2 DELIA_PROJECTION: REFUTED — schema preservado (trace tipado)
H3 DISCOVERY: REFUTED como canal — DAVI catalog é owner-escopo correto;
  nunca deveria listar caps TÉO
H4 MODEL_SELECTION: PROVEN — caps TÉO já disponíveis; 3 discovers
  sem progresso + filial_id omitido em view que exige
H5 LEGITIMATE: PARCIAL — recovery do 400 foi legítimo; discovers não
H6 DIFFERENT_CONTRACTS: PROVEN — #6 e #7 são views com requisitos
  distintos; sucesso não foi "mesma chamada com sorte"

ROOT_CAUSE: model churn (H4) amplificado por contrato com requisito
condicional não expresso em schema (H1 parcial — owner TÉO, por
natureza de JSON Schema).
RECOMMENDED (não implementado): descrição do analyze poderia declarar
que views snapshot "departamento/process" exigem filial_id+setor_id —
contrato do owner, decisão arquitetural do TÉO, fora do escopo DÉLIA.
