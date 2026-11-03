# 218 — Perda de Dados Estruturados: Causa-Raiz (AUDIT, READ-ONLY)

TASK_ID: DELIA-C3-STRUCTURED-EVIDENCE-PROJECTION-AND-PRESENTATION-ROOT-CAUSE-AUDIT-01
BASE: ad5424e75a | MODELO: diagnostico, sem implementacao.

## Pergunta respondida
Por que `get_product_structure` retorna BOM completa (raiz + 2 PI +
componentes MP) e a DÉLIA apresenta so "2 registros" planos?

## Matriz de preservacao (prova in-process, outcome real)

| Fronteira | SHAPE | NODES | RESULTADO |
|---|---|---|---|
| DAVI→MCP→Adapter→Outcome | {entity,shape=hierarchy,data{root,items[2]{components}}} | 1 raiz+2 PI+4 MP | PRESERVADO |
| Outcome→EvidenceFacts.records | 2 dicts c/ components[] intactos | 2 | PRESERVADO |
| EvidenceFacts.result_context | entity+shape+root{90260148} | — | PRESERVADO (fix 1fd1c5843c) |
| **records→PresentedRecord** | **flat (k,v) escalares** | 2 | **components DESCARTADOS — 1a perda** |
| synth field-select (LLM) | escalares only | — | 2a perda: instrucao "never select object/list" |
| CriComposition._record_line | linha "k: v" | — | 3a perda: nao existe forma hierarquica no contrato |

FIRST_LOSS_BOUNDARY: `presented_record`/`cri_scalar_text` —
`conversational_response.py:557-600` — projeta CADA registro para
triples (label, valor) SOMENTE escalares; `components` (list[dict])
e descartado silenciosamente. SOURCE: convers_response.py:153
_record_line (flat) + 583+ presented_record + cri_scalar_text
reject non-scalar (1067).

## Causa-raiz (PROVEN)

O pipeline inteiro preserva a hierarquia (adapter, outcome, facts,
result_context). A perda e na CAMADA DE APRESENTACAO, por 3 gates
compostos:
1. `cri_scalar_text` rejeita valores nao-escalares por contrato
   (field diffs exigem escalares — responsabilidade legitima, mas
   aplicada como UNICO caminho de render).
2. `_record_line`/`compose_cri_response` so tem forma "registro plano"
   — nao existe vocabulary/contrato CRI para hierarquia/aninhamento.
3. `grounded_synthesis` instrui "never select object or list fields" —
   mesmo se o record chegasse com components, o stage LLM descartaria.

Nenhum output-schema do MCP chega ao compositor (so input schema/args
sao descobertos) — a forma declarada (entity/shape/root) so sobrevive
em result_context, nunca consumida pela renderizacao.

IMPACTO: SHARED_COMPOSITION → CROSS_OWNER_RISK. QUALQUER owner
retornando aninhamento (arvore, filhos, secoes, agregados c/ detalhe)
perde a sub-estrutura na apresentacao — nao e especifico do DAVI.

## Inventario de limites (relevantes)

| Limite | Valor | Onde | Aplicacao |
|---|---|---|---|
| MAX_FIELDS_PER_RECORD | 4 | orch (presented_record call) | pre-LLM, silencioso |
| MAX_PRESENTED_RECORDS | 5 | orch | pre-LLM, trunca colecao |
| _MAX_FIELD_SCAN_RECORDS | 32 | orch | scan de fields |
| cri_scalar_text | scalar-only | conv_response.py:557 | pre-LLM, descarta obj/list |
| synth instruction | "never object/list" | grounded_synthesis | LLM stage |
| sanitize | depth/bounds | _sanitize_renderable | preserva mas boundado |

## Security implications

Preservar estrutura completa exige: sanitize recursivo (JA existe —
_sanitize_renderable preserva components bounded), provenance,
bounds de profundidade/recurssao, e NUNCA raw payload ao LLM/UI.
O caveat: components ja chegam sanitized ao EvidenceFacts — o gate
de apresentacao e de FORMA, nao de seguranca.

## Recomendacao (SEM implementar)

BOUNDARY: extensao do contrato de APRESENTACAO, nao da extracao.
A forma ja e conhecida (result_context.entity/shape). Menor direcao:
`CriComposition`/`compose_cri_response` ganhar forma "structured"
(vocabulary section nova) renderizando root + nodes com children —
driven por result_context.shape, bounded, sanitized; NUNCA raw.
RED tests: compose com records+components deve incluir sub-linhas;
records com children genericos (parent/children) idem; payload
sem shape declarado -> fallback plano atual (nao inventar forma).
REUSE: result_context + cri_scalar_text + _REASON/vocabulary infra.
EXISTING_EQUIVALENT=NO (nao existe render hierarquico) → EXTEND.

TASK_STATUS=COMPLETE(audit) · COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW
