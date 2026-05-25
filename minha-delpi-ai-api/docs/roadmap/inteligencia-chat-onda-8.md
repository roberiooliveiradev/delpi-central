# Inteligência do chat — Onda 8

**Status:** concluída (maio/2026)  
**Pré-requisitos:** [Onda 7](./inteligencia-chat-onda-7.md)

## Objetivo

Ampliar a cobertura de **sub-rotas de produto** (estrutura, onde é usado/parents) com detecção de intent dedicada e priorização correta no ranking de actions, eliminando falsos positivos para `/analyser`.

---

## Entregas da onda

| # | Entrega | Descrição | Status |
|---|---------|-----------|--------|
| 8.1 | Intent `STRUCTURE` | Detecção dedicada para perguntas de estrutura/BOM; fast path para `/products/{code}/structure` | Concluído |
| 8.2 | Intent `PARENTS` | Detecção de "onde é usado", "produto pai", "where used"; fast path para `/products/{code}/parents` | Concluído |
| 8.3 | Bloco explícito no `select_action` | Prioridade de despacho por intent antes do fallback genérico (PARENTS → STRUCTURE → STOCK → DESCRIPTION) | Concluído |
| 8.4 | Scoring dedicado no ranking | Blocos `elif` por intent em `_rank_product_actions` com penalização de rotas concorrentes | Concluído |
| 8.5 | Resolução de código via contexto | `resolve_product_code` extrai código de `conversation_context` para follow-ups ("onde é usado?" sem código explícito) | Concluído |
| 8.6 | Documentação do guia de rotas | `api-delpi-rotas-agente.md` atualizado com `/parents`, exemplos e vocabulário | Concluído |

---

## 8.1 — Intent STRUCTURE

Perguntas como "qual a estrutura do 10080001?" ou "componentes do produto" são detectadas por `_looks_like_structure_question` e recebem prioridade máxima para a rota `/products/{code}/structure`.

**Scoring:** +150 (path `/structure`) + 40 (keywords) − 40 (se `analyser` presente) − 80 (se `search` no path).

---

## 8.2 — Intent PARENTS

Perguntas como "onde é usado o 10080001?" ou "produto pai" são detectadas por `_looks_like_parents_question` (20+ variações) e direcionadas à rota `/products/{code}/parents`.

**Frases reconhecidas (amostra):**
- "onde é usado o …"
- "produto pai do …"
- "em quais produtos é usado …"
- "quem usa o …"
- "faz parte de qual …"
- "where used …"

**Scoring:** +200 (path `/parents`) + 40 (keywords `parent`/`pai`) − 40 (`analyser`) − 80 (`search`).

---

## 8.3 — Despacho por intent no `select_action`

Antes desta onda, apenas STRUCTURE, STOCK e DESCRIPTION tinham blocos explícitos. O intent PARENTS caía no fallback genérico (`_looks_like_product_question` → intent FULL), perdendo a priorização.

**Ordem de verificação atual:**

```text
1. PARENTS  → _select_product_action(intent=PARENTS)
2. STRUCTURE → _select_product_action(intent=STRUCTURE)
3. STOCK     → _select_product_action(intent=STOCK)
4. DESCRIPTION → _select_product_action(intent=DESCRIPTION)
5. Genérico  → _select_product_action(intent=FULL)
```

---

## 8.4 — Scoring por intent no `_rank_product_actions`

Cada intent agora possui bloco `elif` dedicado que aplica boost forte à rota esperada e penaliza concorrentes:

| Intent | Rota preferida | Boost principal |
|--------|---------------|-----------------|
| PARENTS | `/parents` | +200 |
| STRUCTURE | `/structure` | +150 |
| STOCK | `/stock` | +120 |
| DESCRIPTION | `/analyser` | +70 |
| FULL (sem sub-intent) | `/analyser` | +100 |

---

## 8.5 — Resolução de código em follow-up

O método `resolve_product_code` agora tenta extrair código do `conversation_context` quando:
- A mensagem é detectada como `_looks_like_parents_question`
- Ou `_looks_like_structure_question`
- Ou qualquer follow-up referenciando produto anterior

Isso permite que "onde é usado?" (sem código) funcione quando há código no histórico.

---

## Correções durante a onda

### Bug: intent PARENTS sem bloco no select_action

**Causa raiz:** `select_action` verificava apenas STRUCTURE, STOCK e DESCRIPTION. O intent PARENTS passava para o fallback genérico que testava `_looks_like_product_question` — que não continha termos de "onde é usado" / "parent".

**Correção:** Adicionado bloco `if product_code and intent == PARENTS` como primeiro despacho de sub-rota, com termos de parents em `_looks_like_product_question` como safety net.

### Bug: scoring genérico priorizava analyser

**Causa raiz:** No bloco `else` do ranking, rotas com "analyser" recebiam +100+60=160, superando o +120 de `wants_parents`.

**Correção:** Com o bloco `elif PARENTS` dedicado (+200), a rota `/parents` agora vence consistentemente.

---

## Próximos passos

1. Reimportar OpenAPI após deploy da api-delpi.
2. Validar em produção com perguntas reais de "onde é usado".
3. Considerar Onda 9: cache de resultados de actions, melhoria de contexto conversacional multi-turno.

---

## Referências

- [api-delpi-rotas-agente.md](../knowledge/api-delpi-rotas-agente.md)
- [inteligencia-chat-onda-7.md](./inteligencia-chat-onda-7.md)
- `external_action_selection_service.py`
- `chat_product_query_intent_service.py`
