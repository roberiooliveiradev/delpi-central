# Avaliação humana A–D — falhas + variações/typos

Data: 2026-08-31 · roteiro `scripts/eval_packages_a_d_human_live.py`  
JSON: `smoke-packages-a-d-human-eval.json`

## 1. Análise das falhas originais

| Falha | Causa raiz | Não é |
|-------|------------|-------|
| **B Identity ~15–45s** | Heurística `identity.json` não pega «como posso te chamar / u / vc»; o LLM de turn analysis roda **antes** do dispatch. Conteúdo final ok (Minha DELPI, skipRag). | Dispatch desligado no send |
| **C dataAnswer** | Enrichment grava em `toolCalls[].metadata`; envelope send **filtra** `dataAnswer`. Eval antigo olhava o lugar errado → falso FAIL. Com assert canônico: **C1 PASS**. | Pipeline de commentary quebrado |
| **D filial×filial** | Intermitente: às vezes `text_task` / lastAction fraco; às vezes dual ok mas rota errada. Seed + frase importam. | compareAxis inexistente no planner |

## 2. Baseline pré-hotfix (PASS / FAIL)

### Identidade (B) — sempre lento

| Caso | Pergunta | Resultado | ms |
|------|----------|-----------|----|
| B1 | como u posso te chamar? | FAIL latência (conteúdo ok) | 14s |
| B2 | como vc se chama? | FAIL latência | 33s |
| B3 | como te chamo mesmo? | FAIL latência | 45s |
| B4 | como posso te chamar? | FAIL latência | 28s |
| B5 | qual seu nome? | FAIL latência | 25s |

Padrão: resposta certa, **sem shortcut heurístico** → analysis LLM.

### Guidance comum (A) — estável com typo de filial

| Caso | Pergunta | Resultado |
|------|----------|-----------|
| A1 | qual o rol filial 01 | **PASS** 322ms |
| A2 | me fala o rol da **filail** 01 | **PASS** 353ms |
| A3 | rol 01 agora | **PASS** 435ms |
| A4 | quanto foi o **faturamento** da filial 01? | **FAIL** — caiu em «se eu consigo» (capabilities), sem guidance de agente |

Vocabulário «faturamento» ≠ trigger operacional de ROL no comum.

### ROL agente (A) — bom, mas abreviação quebra

| Caso | Pergunta | Resultado |
|------|----------|-----------|
| A5 | ROL filial 01 agosto 2026 | **PASS** `/financial/rol` br=01 |
| A6 | rol da **filail** 01 em agosto/2026 | **PASS** br=01 |
| A7 | rol 01 **ago/26** | **FAIL** clarify ~72s |
| A8 | …só da **unidade** 01 no mês de agosto… | **PASS** br=01 |

### dataAnswer (C)

| Caso | Resultado |
|------|-----------|
| C1 consolidado agosto | **PASS** (dataAnswer nos tools); valor R$ 0,00 é qualidade de dado/período, não metadata |
| C2 **consollidado** ago 2026 | **FAIL** clarify ~55s (typo derruba intenção) |

### Compare período (D)

| Caso | Pergunta | Resultado |
|------|----------|-----------|
| D1 | comparar com o período anterior | Dual **ok**, mas label prior = «ano anterior» → FAIL qualidade |
| D2 | periodo **anteriror** | **FAIL** — não dualiza; LLM pede julho |
| D3 | e no mês passado? | PASS soft (sem inventar número) |

### Filial×filial (D)

| Caso | Pergunta | Resultado |
|------|----------|-----------|
| D4 | comparar filial 01 com 02 (seed ROL ago) | Dual br 01/02, mas path **new-clients-rol-pct** (errado) |
| D5 | compara **filail** 01 vs **filail** 02 | **PASS** dual `/financial/rol` 01×02 |
| D6 | compara entre filiais 01 e 02 | **FAIL** — 1 tool `branch_rol_target_pct`, sem dual |

### YoY / challenge (herança)

| Caso | Resultado |
|------|-----------|
| Y1 YoY canônico | **PASS** dual 2026×2025 |
| Y2 typo «ano **anteriror** mesmo periodo» | Dual roda, mas cai em **julho/2026** (previous_period) — typo quebra match de «ano anterior» |
| Y3 challenge filial≠consolidado | **PASS** prosa correta |

## 3. Re-smoke pós-hotfix (E7.S1–S5) — 2026-08-31

Hotfixes: identity direct antes do analysis LLM; `period_compare_prior_label`; text_task isento filial×filial; typos `anteriror`/`ago/26`/`consollidado`; faturamento → guidance operacional.

Subset live (`SMOKE_ONLY`): B1,B2,B4,B5,A4,A7,C2,D1,D2,D4,D6,Y2.  
1ª onda: **8 PASS / 4× HTTP 429**. Retry após ~90s: D2,D4,D6,Y2 → **4 PASS**. Artefato: `smoke-packages-a-d-human-eval.json` (merge).

| Caso | Resultado pós-hotfix | Evidência |
|------|----------------------|-----------|
| B1 | **PASS** | 583ms, skipRag, Minha DELPI |
| B2 | **PASS** | 406ms |
| B4 | **PASS** | 414ms |
| B5 | **PASS** | 367ms |
| A4 faturamento | **PASS** | 206ms, guidance «Dados operacionais exigem um agente» |
| A7 ago/26 | **PASS** | 1599ms, `/financial/rol` |
| C2 consollidado | **PASS** | 1436ms, br=all, `/financial/rol` |
| D1 período anterior | **PASS** | dual jul/2026; label **«período anterior»** |
| D2 anteriror | **PASS** | dual jul/2026 (retry pós-429) |
| D4 filiais 01×02 | **PASS** | dual `/financial/rol` br 01/02 |
| D6 entre filiais | **PASS** | dual `/financial/rol` br 01/02 |
| Y2 typo YoY | **PASS** | dual ago/2025 (não caiu em previous_period) |

**Fora do subset:** B3 («como te chamo mesmo?») permanece no JSON como FAIL lento pré-hotfix — não reavaliado nesta onda.

**Nota de qualidade (não bloqueia dual):** em D4/D6 a prosa ainda rotula o slot prior como «ano anterior (mesmo intervalo)» embora o eixo seja filial×filial (datas iguais). Dual de path/branch está correto.

## 4. Síntese

**Corrigido pelos hotfixes (re-smoke)**
- Identity canônico/typo u/vc/nome → <1s
- «faturamento» no comum → guidance agente
- `ago/26`, `consollidado`, `anteriror` (período e YoY)
- Label previous_period = «período anterior»
- Filial×filial («comparar» / «entre filiais») dual `/financial/rol`

**Aberto / residual**
- B3 não re-smokeado nesta onda (eval stale)
- Latência dual compare ainda alta (30–120s) — esperado (2× API + síntese), não regressão do shortcut

## 6. Qualidade pós-hotfix (E8) — 2026-09-01

Hotfixes adicionais: labels compare por eixo branch; bare `01` em date_branch; consolidado omite `branch`; «mês passado» → `previous_period`.

### Consolidado R$ 0 — causa raiz (E3)

**Param, não dado TOTVS.** O builder enviava `branch=all` quando a mensagem continha «consolidado». A api-delpi filtra `D2_FILIAL = 'all'` (valor inexistente) → ROL zerado. Sem `branch` no query, a API soma todas as filiais (~R$ 4,3M em ago/2026 no dev). Fix: omitir `branch` para consolidado/todas as filiais.

### Critérios verify-final (E6)

| Caso | Alvo |
|------|------|
| B3 | identity &lt;2s |
| A7 | `branch=01`, valor ~filial 01 |
| C1 | consolidado ≠ 0 (params sem branch) |
| D3 | dual ago×jul, label período anterior |
| D4/D5/D6 | prosa «filial 01/02», sem «ano anterior» |

## 5. Hotfixes aplicados (E7)

1. **B** — `identity.json` + `prefer_identity_direct` / skip analysis LLM  
2. **D label** — `period_compare_prior_label(kind)`  
3. **D text_task** — isentar compare filial×filial + lastAction  
4. **D/C typo** — `periodTypoReplacements` / typing correction  
5. **A** — faturamento em KPI/capabilities patterns  
