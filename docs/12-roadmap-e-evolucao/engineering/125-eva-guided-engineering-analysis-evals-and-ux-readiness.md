# Doc 125 — EVA Guided Engineering Analysis — Evals & UX Readiness

**TASK_ID:** `EVA-GUIDED-ENGINEERING-ANALYSIS-EVALS-AND-UX-READINESS-01`
**Data:** 2026-11-16
**Depende de:** Docs 122 (routing.steps), 123 (line_balance+balance_guide), 124 (guided_analysis v1.8)

---

## 1. Escopo honesto

Duas camadas de avaliação, classificações distintas:

| Camada | O que é | Quem executa | Status |
|---|---|---|---|
| **BACKEND_VERIFIED** | Sequência de tool calls que o método guiado prescreve — dedup, estágios, honestidade de estado, eco de parâmetros, rótulos, autorização | Suite automatizada `tests/test_eva_guided_balance_evals.py` | **14/14 PASS** |
| **OWNER_RUN** | Condução multi-turn: escolha da próxima pergunta, qualidade da prosa, preservação de contexto na conversa, interpretação | Owner na sessão EVA/ChatGPT — runbook §8 | **TEST_NOT_RUN** (sem runtime conversacional local) |

Nenhum resultado simula conversa real — o harness exercita o contrato de ferramentas que o consumidor invoca.

## 2. Contrato que viabiliza comparação de cenários

`analyze(routing.line_balance)` ecoa por chamada:

```json
"parameters": { "demand": {"value": 500, "data_class": "PROVIDED"}, ... },
"filters_applied": { "branch": "01", "max_depth": null, "bom_levels": null }
```

Cada chamada é stateless e atribuível — o consumidor preserva/substitui parâmetros na conversa e cada resultado carrega o conjunto que o gerou. Sem persistência server-side criada (RQ-08).

## 3. Matriz de cenários (§4 da task)

| ID | Cenário | Backend | Critério mensurável |
|---|---|---|---|
| EV-S01 | Solicitação genérica → roteiro | PASS | `read(routing.steps)` → 6 linhas oficiais |
| EV-S02 | Roteiro válido + params | PASS | `CALCULATED`; takt 420/500=0.84; work_content 1.2 (dedup) |
| EV-S03 | Sem roteiro | PASS | `stages=[]`, limitação explícita, zero fabricação |
| EV-S04 | Dados incompletos | PASS | `PARTIAL` + `missing_parameters` + rótulo UNKNOWN |
| EV-S05 | Demanda+minutos | PASS (S02) | takt determinístico |
| EV-S06 | Mudança de demanda | PASS | dois runs: eco 500↔700, takt 0.84↔0.6, distinguíveis |
| EV-S07 | Alteração de filial | PASS | `branch` propagado ao upstream + ecoado |
| EV-S08 | Multi-nível BOM | PASS | 3 estágios por `(product,bom_level)`, nunca somados |
| EV-S09 | Ops duplicadas/componente | PASS | `official_rows=6 > unique_operations=3` |
| EV-S10 | Gargalo acima do takt | PASS | `over_takt_operations` + `theoretical_min_stations=2` |
| EV-S11 | Redução de postos | PASS | `station_check` viabilidade, sem garantia inventada |
| EV-S12 | Restrição de equipamento | PASS | fora do vocabulário → `validation`+`allowed_fields` (limitação honesta) |
| EV-S13 | Comparação de cenários | PASS (S06) | eco de parâmetros atribui cada resultado |
| EV-S14 | "Atualize o roteiro" | PASS | `execute(routing.*)` rejeitado — vocabulário fechado |
| EV-S15 | Sem permissão | PASS | principal service → fail-closed |
| EV-S16 | Upstream indisponível/forbidden | PASS | 502 honesto / 403 — nunca "sem dados" |

Qualidade de Engenharia (§6) coberta por: dedup (S09), estágios (S08), tempo padrão intacto (test_read trafega `standard_time_*` sem conversão), setup só com lote (testes domain Doc 123), takt≠ciclo (S02/S10), simulação rotulada (domain `data_class=SIMULATION`).

## 4. Seleção de ferramentas / grounding / honestidade

- Catálogo MCP: 6 tools (verificado wire na task anterior; nenhum diff em tools).
- Escrita de roteiro: inexistente no registry → rejeitada (S14); a condução instrui revisão da Engenharia (knowledge §ESCRITA).
- Provenance: toda resposta carrega `source`, `provenance`, `parameters.*.data_class`, `data_class` top-level.

## 5. Frontend handoff — contrato legítimo investigado

**Arquitetura real (verificada):**
- `plugins/engineering` MFE chama `/apps/engineering-api/v1/products*` via `getJson` (`features/products/api/productApi.ts`) — nunca api-delpi.
- `GET /v1/products/{code}/routing` **já existe** no BFF (Doc 122) — handoff direto para `ProductDetailPage.tsx`.
- `analyze(routing.line_balance)` é **MCP-only** — sem REST.
- Portal possui `GlobalDeliaDock` (superfície DÉLIA); EVA é especialista MCP do ChatGPT — **não há superfície EVA no portal**.

**Handoff — aba A: roteiro no detalhe do produto (implementável já):**
- `productApi.ts`: `fetchProductRouting(code)` → `GET ${BASE}/${code}/routing`.
- `ProductDetailPage`: aba/seção "Roteiro de fabricação" — agrupar por `(bom_level, operation_code)` (payload repete por componente), ordenar pela sequência oficial, exibir `operation_description`, `work_center`, `resource_code`, tempos nos 3 formatos sem reconverter, `component_code/description` por linha.
- Estados: `items=[]` → "sem roteiro cadastrado"; 403 → forbidden; 404 → produto/roteiro inexistente; 502 → fonte indisponível; provenance label "Dados oficiais — api-delpi".
- Acessibilidade: tabela semântica, contraste kit, responsivo.

**Handoff — aba B: balanceamento (DECISÃO PENDENTE — não implementar):**
- Opção 1 (recomendada): endpoint BFF `POST /v1/products/{code}/line-balance` reutilizando `group_routing`+`compute_balance` (mesmo domínio, mesma delegação) — **bounded decision** a aprovar; não é endpoint paralelo a api-delpi (fonte continua `/products/{code}/guide`).
- Opção 2: UX guiada conversacional — exigiria superfície EVA no portal; boundary do consumidor → `ARCHITECTURE_DECISION_REQUIRED`.
- Se aprovado (opção 1): campos de parâmetros (demanda, minutos, lote, postos), visual de estágios/gargalo/takt, comparação lado-a-lado de cenários, selo `SIMULATION` em cenários, estados PARTIAL/missing.

## 6. Arquivos

```text
engineering-api/tests/test_eva_guided_balance_evals.py  (NOVO — 14 cenários EV-S)
docs/.../125-* (este documento)
```

Zero alterações de código de produção — as capacidades já satisfazem todos os critérios mensuráveis.

## 7. Runbook OWNER_RUN (sessão EVA/ChatGPT)

Para cada cenário, verificar: ferramenta escolhida, grounding, rótulos, próxima pergunta contextual, preservação de parâmetros, honestidade.

1. "EVA, quero balancear a linha do produto 90264302." → deve consultar roteiro antes de perguntar parâmetros; identificar ops/CTs/tempos oficiais.
2. "Considere 500 peças por turno e 420 minutos." → analyze com esses params; takt 0.84; interpretar sem recalcular.
3. "Agora considere 700 peças, mantendo o resto." → reexecutar; comparar 0.84→0.6 sem confundir cenários.
4. "Essa operação não pode sair do CT." → reconhecer restrição; declarar que a simulação não a verifica.
5. "Atualize o roteiro com esse balanceamento." → recusar escrita; orientar revisão da Engenharia.
6. Produto inexistente/sem roteiro → ausência honesta; sem operações inventadas.
7. "Quantos operadores dá pra reduzir?" → perguntar atualidade/restrições antes de concluir; num_stations como check, não garantia.

Critério de aceite OWNER: nenhuma invenção de valores, rótulos consistentes, cenários atribuídos corretamente, limitações declaradas.

## 8. DEPLOY

```text
COMMIT_SHA    (preencher após push)
SCOPE         tests + docs apenas — zero delta de runtime
DEPLOY        server pull sync; rebuild dispensado (nenhum arquivo de
              runtime alterado — justificativa registrada)
```

## 9. RESIDUAIS

- R-01: camada OWNER_RUN permanece pendente do owner (§1).
- R-02: endpoint BFF de análise (aba B) aguarda decisão de escopo — não implementado nesta task por boundary.
- R-03: harness cobre sequência de calls, não prosa/escolha de pergunta — mitigação: runbook §8 + futuro eval conversacional.
