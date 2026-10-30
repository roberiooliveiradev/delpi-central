# R04 — Consumo por OP

Versão da ficha: 1.0 · 31/10/2026 · doc 127 Etapa 4.

Publicação: ficha **publicada no corpus produtivo** `5bebf07f-a66a-479f-aa2b-e7d0e6c7ea00` (release stage-05, 30/10/2026) — **sem contrato operacional**; estado PENDING_CONTRACT/EXTERNAL inalterado.

## Identificação

- Código/nome: **R04 — Consumo por OP** (materiais consumidos por
  ordem de produção).
- Finalidade pretendida: analisar consumo de materiais por ordem de
  produção na competência — gap de conhecimento identificado (GAP-01).
- Processo: PROC-0072 — registro no catálogo canônico (doc 118 §6).
- Owner funcional: Controladoria — `TO_INVENTORY` (consumidor incerto
  no inventário: "?").
- Owner técnico: nenhum implementado.
- Produtor candidato: `MATR860` — `TO_INVENTORY` (candidato não
  confirmado por artefato).
- Implementação: **`NOT_IMPLEMENTED` — `BLOQUEADO`** (sem artefato de
  referência; doc 85 §4).
- Homologação: nenhuma — sem evidência emitida.

## Fonte e dados

- Nenhum artefato disponível no inventário — sem PDF/XLSB observado.
- Fonte potencial: SD3 (`D3_OP` + CF `RE*`) — a linha de movimento de
  produção já é grão provado no R08; requisição por OP é o mesmo universo
  físico, recorte diferente — `TO_INVENTORY` (reuso possível, não
  equivalência provada).
- API/contrato: **nenhum** — sem endpoint, sem capability CLARA.

## Regras de negócio

- Nenhuma regra registrável — `TO_INVENTORY` (doc 85 §4 `BLOQUEADO`).
- A CLARA não deve inventar seleção, filtro ou fórmula para R04.

## Interpretação

- A CLARA **não conhece** este relatório além do nome/finalidade
  registrada — responder honestamente `INSUFFICIENT_EVIDENCE` e indicar
  a lacuna (GAP-01), nunca improvisar semântica.
- Próximo caminho documentado: inventário com o owner + artefato real
  emitido no ERP para reconstruir a seleção (mesmo método dos ciclos 1–2).

## Operação

- Não há operação Portal/CLARA disponível.
- Comparações: `NOT_COMPARABLE`/`INSUFFICIENT_EVIDENCE` — o motor
  stage-03 responde `report_not_implemented` para `R04`.

## Governança

- Evidências: doc 85 §4 (`BLOQUEADO`); doc 118 §6 (GAP-01); doc 83 §9.
- Dependências: E-gap — owner do relatório + artefato oficial.
- Limitações: qualquer resposta além do registrado é proibida —
  fail-closed.
- Referências: doc 85 §4; doc 118 §6; doc 121.
