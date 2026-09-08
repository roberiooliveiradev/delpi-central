# Smoke live — turnos complexos consolidados (C1–C4)

**Status:** vigente  
**Harness:** `scripts/smoke_complex_consolidated_turns_live.py`  
**Evidence estrutural:** [`evidence/chat-complex-consolidated-turns-live.json`](./evidence/chat-complex-consolidated-turns-live.json)  
**Protocolo canônico:** [`chat-ai-flow-families.md`](./chat-ai-flow-families.md) §16.1 (camadas L1–L4)  
**Famílias:** F03 (actions), F13 (apresentação), F14 (follow-up), pedido composto (§7)

---

## 1. O que o harness mede (e o que não mede)

O script valida **camada estrutural / pipeline**:

- tools executadas (`ok`, contagem mínima);
- markers/grupos de path;
- presença de `kinds` / rich surfaces (table, tree, kpi, dashboard…);
- prosa presente e sem fence SQL Protheus;
- latência agregada.

Isso **não** prova, sozinho:

- fidelidade prosa ↔ payload (`dataAnswer`);
- árvore com nós legíveis;
- ausência de painéis duplicados;
- path canônico por subtarefa (estoque ≠ summary);
- checklist do pedido do usuário (R9 / L4).

```text
HARNESS PASS  =  PASS_ESTRUTURAL
≠  PASS de release / “passou para o usuário”
```

Release exige L1∧L2∧L3∧L4 conforme §16.1 do protocolo.

---

## 2. Casos

| ID | Pedido (resumo) | Required dimensions mínimas |
|----|-----------------|-----------------------------|
| **C1** | Visão integrada: ficha, estrutura, roteiro, estoque + painéis | R1–R5, R8, R9, R11 + **L1–L4** |
| **C2** | BOM + estoque + open-orders numa resposta | R1–R5, R8, R9, R11 + **L1–L4** |
| **C3** | ROL KPI/série + prosa; sem fan-out IDD | R1–R5, R8, R9, R11 + **L1–L4** |
| **C4** | Seed estoque/descrição → follow-up estrutura + cobre demanda | R1–R6, R8, R9, R11 + **L1–L4** |

Produto de referência do corpus atual: `90260149`. Agente smoke: `SMOKE_AGENT_ID` (ex. Minha DELPI).

---

## 3. Rubrica L1–L4 aplicada a este smoke

| Camada | Fail típico neste corpus |
|--------|---------------------------|
| **L1 R-tools** | Seed pede estoque e cai em `/summary`; follow-up de cobertura sem `/stock`; C3 com department-indicators |
| **L2 R-facts** | Prosa “não trouxe estoque” com `/stock` ok e saldo 0; juízo de cobertura sem saldo no workspace |
| **L3 R-ui** | `treePresentation` com filhos `label: "—"` / `id: unknown`; dashboard com dois painéis de Estrutura; Automático com `selected=text` sem `explicitSessionFormat` |
| **L4 R-ask** | Subtarefa pedida ausente, ilegível ou só “presente” via visual quebrado |

Montagem canônica esperada (um formato por domínio):

```text
prosa lead (decisão + lacunas)
→ um visual BOM (tree boa XOR table)
→ tabela estoque
→ veredito cobertura (se pedido)
→ roteiro só se pedido / secundário
```

---

## 4. Como avaliar após o harness

1. Rodar o script; gravar evidence + `sessionId` por caso.
2. No Postgres (`plugins_hub.ai_chat_messages`), inspecionar último assistant (e seed em C4):
   - `metadata.toolCalls[].metadata.path|ok|dataAnswer|treePresentation|dashboardPresentation|preferredFormat|presentationDecision|explicitSessionFormat`
   - `content` (prosa)
3. Preencher a matriz L1–L4.
4. Declarar:

```text
CASO | L1 | L2 | L3 | L4 | HARNESS | VEREDITO_RELEASE
```

5. **Não** atualizar `passed: true` no JSON de evidence estrutural como se fosse release PASS. Anexar `qualitativeReview` (ou arquivo irmão) com a matriz.

---

## 5. Revisão qualitativa — sessão evidence vigente

Fonte estrutural: `evidence/chat-complex-consolidated-turns-live.json` (`passed: true` no harness).  
Revisão humana/banco + UI (conversa C4 `b40bd3f3-…`), alinhada aos critérios §16.1:

| Caso | session_id | L1 | L2 | L3 | L4 | Harness | **Release** |
|------|------------|----|----|----|----|---------|-------------|
| C1 | `45f6b159-…` | PASS (analyser+stock) | **FAIL** (prosa nega estoque com tool ok / saldo 0) | PASS parcial | **FAIL** (estoque omitido na leitura) | PASS | **FAIL** |
| C2 | `763b3861-…` | PASS (structure+stock+open-orders) | PASS parcial (estoque ok; open-orders fraco) | WARN (`explicitSessionFormat=text` → selected text) | PASS parcial | PASS | **PASS parcial / WARN** |
| C3 | `d0e61ce1-…` | PASS (só ROL; sem IDD) | PASS (empty-state honesto) | PASS (empty KPI) | PASS | PASS | **PASS** |
| C4 | `b40bd3f3-…` | **FAIL** (seed `/summary`; follow-up sem stock) | **FAIL** (cobertura sem saldo) | **FAIL** (tree `—`; Estrutura duplicada no dashboard) | **FAIL** | PASS | **FAIL** |

**Placar release:** 1 PASS (C3), 1 parcial (C2), 2 FAIL (C1, C4) — **não** 4/4.

Achados C4 (UI/banco) que o harness estrutural não pegou:

- seed: cadastro/summary em vez de estoque;
- `treePresentation.children` com `id: unknown`, `label: "—"`;
- `dashboardPresentation.panels`: “Estrutura do produto …” + “Estrutura” + “Roteiro”;
- prosa de follow-up admite ausência de estoque sem reconsultar `/stock`.

---

## 6. Execução

```bash
docker exec -e SMOKE_BASE_URL=http://delpi-gateway \
  -e SMOKE_AGENT_ID=4f9c225b-0414-40d3-a462-040889719b83 \
  -w /app delpi-minha-delpi-ai-api \
  python scripts/smoke_complex_consolidated_turns_live.py
```

Depois: matriz L1–L4 no banco/UI antes de qualquer afirmação de excelência ou fechamento de plano.
