# 79 — CRI E4 · Real evaluation, rollback & acceptance — execution report

**TASK_ID:** `DELIA-CRI-E4-REAL-EVAL-ROLLBACK-AND-ACCEPTANCE-01`
**Data:** 2026-10-21 · **SHA avaliado:** `0af32302e9ca3072e73a9b47d09206111c9c2e5d`
**Tipo:** avaliação independente bounded — real LLM, real HTTP boundary,
OFF/ON pairing, rollback e falha segura. Nenhuma linha de runtime alterada.

Estados de entrada revalidados (docs 73–78, ledger §6.355–6.357):
`CRI_E0/E1/E2/E3=ACCEPT_WITH_RESIDUAL`, `CRI_E3_CLOSED=YES`,
`CRI_E4=AUTHORIZED_FOR_BOUNDED_EVALUATION`, `DEFAULT_STATE=OFF`,
`SELECTION_ONLY=FROZEN`, `REAL_MODEL_EVAL=TEST_NOT_RUN` (anterior),
`PRODUCTION_ACTIVATION=NOT_AUTHORIZED`, `I04_ACCEPTED=NO`,
`C3_EXECUTED=NO`.

## 1. Ambiente e prova de ativação

| Campo | Valor |
|---|---|
| ENVIRONMENT | Docker local dev/homologation — rede `infra_delpi-network` |
| EVALUATED_SHA / RUNTIME_SHA | `0af32302e9ca3072e73a9b47d09206111c9c2e5d` (env-pinnado `DELIA_RUNTIME_SHA`, log de startup confere) |
| CONFIG_VERSION | worktree `delia-cleanup-wt` @ evaluated SHA, bind-mount `/app` |
| MODEL_REF | OpenAI-compatible OpenRouter `moonshotai/kimi-k3` |
| SUBJECT_TYPE | usuário dev portal (Keycloak password grant, helper documentado `infra/scripts/get-dev-token.sh`); `is_superadmin` no Core dev |
| INSTRUCTION_RESOURCE | `delia.cri.answer_requirements_instruction` v1, sha256 `7e3c5515d3926c391aa961ca66c700df4c159b8daa100ade0b2377e5b6e32549` |
| PRESENTATION_RESOURCE | `delia.cri.presentation_vocabulary` v2, sha256 `c947616dcc906eaa49a7c0f5f57fd388aada0a5b42b1a2d6151567d95baf0c28` |
| REQUESTED_MODE / EFFECTIVE_MODE | OFF: `baseline/baseline`; ON: `cri/cri` (log `delia_response_intelligence` por boot) |
| Container de avaliação | `delia-eval-cri` — instância isolada, mesmo image/env da stack, flag e SHA pinados; o serviço em uso do usuário (`delpi-delia-api`) **nunca foi tocado** |

Prova de ativação real (não apenas a flag): log de composição
`requested=cri effective=cri` + carregamento dos dois recursos
versionados com sha256; por turno `stage=response_mode decision=cri`;
na orquestração `stage=outcome_assessment` seguido de
`stage=cri_response decision=composed presented=N delivered=N`.

## 2. Limitação material de ambiente (registrada, não contornada)

Os especialistas MCP (TÉO, VISTA, DAVI-MCP) estão **alcançáveis**
(transport probe 401-auth-challenge) e a troca delegada produz token
válido (`same_sub`, `resource_audience_bound`, `mcp:tools` scope,
`azp` do requester) — porém `tools/list` retorna
`mcp_authentication_failed` para os três, **idêntico** no container
principal `delpi-delia-api` (código pré-CRI). Condição pré-existente
do ambiente dev, não introduzida nem relacionada à frente CRI.

Consequência: a superfície de capabilities do sujeito contém apenas
`openapi:delpi` (`select_group groups=1`). Cenários TÉO e VISTA não
podem grounded live nesta identidade/ambiente → `TEST_NOT_RUN`,
conforme §15 da especificação (acesso parcial).

## 3. Matriz OFF/ON — quatro casos obrigatórios

Mesma identidade, mesma pergunta, mesmo escopo, mesmo modelo,
mesma versão de capabilities, execuções a minutos de distância.
Os conjuntos de registros retornados foram idênticos entre modos;
a fonte é mutável mas nenhuma divergência de dados foi observada.

### Caso A — TÉO · "Qual é o último processo alterado no Transformômetro?"

| | OFF | ON |
|---|---|---|
| HTTP / grounding | 200 / NON_GROUNDED | 200 / NON_GROUNDED |
| Latência | 14 917 ms | 16 906 ms |
| Comportamento | recusa honesta, sem inventar | recusa honesta, contexto preservado |

`TEST_NOT_RUN` (grounded) — TÉO fora da superfície por limitação de
ambiente (§2). Em ambos os modos a DÉLIA não fabricou dado: explicou
a ausência e apontou o caminho governado.

### Caso B — DAVI · "Use o DAVI para trazer três exemplos de terminal bandeira."

| | OFF | ON |
|---|---|---|
| Grounding / owner | GROUNDED / `delpi.search_products` | GROUNDED / `delpi.search_products` |
| Latência | 20 544 ms | 22 122 ms |
| Apresentação | `Encontrei 3 registros:` + linhas crudas (`— PC — S`) | `Aqui estão 3 exemplos:` + campos rotulados (Código · Descrição · Groupcode · Tipo) + `A fonte informa 65 registros no total` |
| Contagens | não comunicadas | presented=3, delivered=3, available=65 |

`PASS` (sucesso de integração + resultado real). ON distingue
apresentado (3) do total reportado pelo owner (65) — semântica R1
correta ao vivo; campos técnicos deixam de dominar.

### Caso C — API DELPI · "Pesquise três exemplos de terminal grupo 1008."

| | OFF | ON |
|---|---|---|
| Grounding / owner | GROUNDED / `delpi.search_products` (group_code=1008) | idem |
| Latência | 18 850 ms | 16 172 ms |
| Apresentação | `Encontrei 3 registros:` + campos crus | `Aqui estão 3 exemplos:` + rotulados + `A fonte informa 40 registros no total` |
| Contagens | não comunicadas | presented=3, delivered=3, available=40 |

`PASS`. Três exemplos distintos reais, grupo 1008 conferido nos
registros, total do owner atribuído à fonte — nunca ao apresentado.

### Caso D — VISTA · "O que tem nas minhas playlists da TV?"

| | OFF | ON |
|---|---|---|
| Grounding | NON_GROUNDED | NON_GROUNDED |
| Latência | 17 756 ms | 14 421 ms |

`TEST_NOT_RUN` (grounded) — VISTA fora da superfície (§2). Recusa
honesta em ambos os modos; ON contextualiza sem prometer o que não
pode entregar.

## 4. Generalização (subconjunto executável)

| Cenário | OFF | ON | Veredito |
|---|---|---|---|
| Resultado único (`pesquise um terminal do grupo 1008`) | GROUNDED, apresentou 4 (`Encontrei 4 registros`) | GROUNDED, apresentou 1 (`Aqui estão 1 exemplos`) + `Exibindo 1 de 32 registros retornados` + `result_truncated` | **PASS-ON** — respeita a quantidade pedida e declara truncamento; OFF inflava a contagem |
| Lista (`liste meus processos no Transformômetro`) | budget-limited | budget-limited | mensagem idêntica e segura nos dois modos |
| Vazio (`processo QQ-INEXISTENTE-99`) | budget-limited | budget-limited | **TEST_NOT_RUN** — consulta não concluiu; resultado vazio real não exercitado |
| Quantidade > retornada (`dez exemplos de terminal bandeira`) | budget-limited ~30 s | budget-limited ~30 s | **INCONCLUSIVE** — estoura `GLOBAL_TURN_BUDGET` nos dois modos; custo é da orquestração/modelo, não do CRI |
| Ordenação temporal sem semântica (`processo mais antigo`) | NON_GROUNDED | NON_GROUNDED | TEST_NOT_RUN (TÉO ausente); recusa honesta |
| Follow-up contextual (`e o penúltimo?`) | NON_GROUNDED | NON_GROUNDED, contextualmente ciente | recusa honesta com memória da limitação |
| Controle conversacional (`o que você pode fazer?`) | NON_GROUNDED | NON_GROUNDED | personalidade coerente nos dois modos |

## 5. E4-G1 — gate de semântica temporal

Inspeção do contrato efetivamente autoritativo do owner TÉO
(`transformometro-api`):

- `processos.updated_at` é **declarado pelo owner** como data de
  atualização: `process_activity_touch.py` — *"Bump
  `processos.updated_at` after any process-family mutation. Single
  owner for list ordering ('Data de atualização')"*; chamado após
  writes de filhos do processo (revisão, instância, diagrama,
  evidência, vínculo).
- A ordenação canônica de listagem do próprio owner é
  `ORDER BY p.updated_at DESC` (`process_repository.py`).
- `updated_at` está na allowlist owner `_SEARCH_DATE_FIELDS` para
  `instance`, `revision` e `measurement` (`dispatch_service.py`).

**Veredito do gate:** `PROVEN` (nível contrato/owner) para o campo
`updated_at` — a semântica "alteração" é declarada e mantida pelo
próprio owner; não é inferência lexical. **Porém** o exercício live
do estágio CRI com turno TÉO real ficou `TEST_NOT_RUN` (§2): a
heurística lexical `_field_declares_modification` não foi observada
end-to-end. O residual E3 sobre semântica temporal permanece
exatamente como registrado — não promovido a PASS.

## 6. Fidelidade factual e segurança

- Todos os valores exibidos no modo ON são folhas verbatim do owner
  (códigos/descrições idênticos aos dados crus observados no modo
  OFF). `SELECTION_ONLY` preservado ao vivo.
- Nenhum turno executou write/PREPARE/ACT; todas as perguntas foram
  READ ou conversacionais. `MATERIAL_ACT=0`.
- Respostas NON_GROUNDED não inventaram dado em nenhum modo.
- Falha de auth no catálogo MCP foi rejeitada fail-closed (grupo não
  ofertado) — comportamento correto.
- Nenhuma chamada extra ao modelo: o estágio `cri_response` é
  composição determinística (log `decision=composed` sem
  `model_propose` associado). `ADDITIONAL_MODEL_STAGE=NONE`.
- `AuthZ` inalterada: mesmo sujeito, mesmas permissões; a ausência
  de TÉO/VISTA é autorização do ambiente, não do CRI.

## 7. Latência e orçamento

| Métrica | OFF | ON | Δ |
|---|---|---|---|
| Média dos 11 turnos | ~19 113 ms | ~20 016 ms | ≈ +5% |
| Máximo | 30 030 ms | 30 035 ms | budget hit idêntico |

`GLOBAL_TURN_BUDGET=30_SECONDS` respeitado; turnos pesados estouram
o budget nos dois modos pelo mesmo motivo (seleção/argumentos do
modelo, pré-CRI). O compositor CRI é determinístico — nenhum
overhead estrutural observado; diferenças estão dentro da variância
do modelo. `POST_ORCHESTRATION_FALLBACK` não violado.

## 8. Controle central, rollback e falha segura (real)

`OFF → ON → OFF` executado por recriação do container de avaliação
(o caminho operacional suportado — config resolvida na composição):

1. **OFF** (flag false): `requested=baseline effective=baseline`,
   recursos CRI não carregados, matriz OFF executada.
2. **ON** (flag true): `requested=cri effective=cri`, recursos v1+v2
   carregados com sha256, `response_mode=cri` por turno, estágio
   `cri_response` compõe.
3. **OFF** (flag false, restart): baseline restaurada —
   `requested=baseline effective=baseline`, turno DELPI reproduziu o
   formato OFF (`Encontrei 3 registros:`). Nenhum estado residual.

`ROLLBACK_REAL=YES` — reversibilidade operacional comprovada.

Falha segura real: container separado com vocabulário version `99`
montado sobre o recurso + flag true →
`delia_response_intelligence decision=fail_closed
reason=cri_resource_invalid` → `requested=cri effective=baseline`,
health 200, turno real respondeu em modo baseline.
`INVALID_RESOURCE_FALLBACK=PROVEN_LIVE`. Recurso do worktree nunca
foi modificado (mount `ro` de arquivo scratch).

## 9. Personalidade (personality/01–04)

Rubrica por dimensão nos turnos executáveis:

- **Resultado:** grounded PASS (DAVI/DELPI/GEN_SINGLE); recusas
  honestas quando a evidência não existia.
- **Fundamentação:** PASS — totais atribuídos à fonte, truncamento
  declarado, nada inventado.
- **Comunicação:** PASS com uma exceção cosmética — resposta
  primeiro, campos rotulados, PT-BR natural.
- **Personalidade:** PASS — tom coerente, sem ofertas vazias nos
  resultados grounded (nenhum "posso detalhar" sem suporte — R3).

## 10. Defeitos e residuais encontrados

1. **Pluralização do vocabulário v2 (cosmético, não-bloqueante):**
   `Aqui estão 1 exemplos` quando presented=1 — o template usa a
   forma plural fixa. Registrado para decisão de rework futuro;
   **não corrigido nesta etapa** (E4 é avaliação).
2. **Resultado vazio real não exercitado** — toda consulta DELPI
   retornou dados; o caso vazio ficou `TEST_NOT_RUN`.
3. **TÉO/VISTA live `TEST_NOT_RUN`** — limitação de ambiente (§2),
   pré-existente, verificada idêntica no serviço em uso.
4. **Heurística lexical temporal não exercitada live** — evidência
   de contrato do owner PROVEN para `updated_at`; o comportamento
   E3-R2 end-to-end permanece coberto por testes, não por amostra
   real.
5. **Turnos pesados estouram 30 s em ambos os modos** — custo
   pré-existente da orquestração/modelo; não é regressão CRI, mas
   limita cenários de lista longa.

## 11. Classificação do executor

`ACCEPT_WITH_RESIDUAL` — a frente CRI funciona melhor que o baseline
nos cenários executáveis (semântica de contagem, apresentação
rotulada, total atribuído à fonte, truncamento honesto, zero
chamadas extras ao modelo, rollback e falha segura provados ao
vivo), sem violação de contratos congelados. Residuais limitados e
não críticos: cobertura TÉO/VISTA/resultado-vazio indisponível no
ambiente; defeito cosmético de pluralização; heurística temporal sem
exercício live (contrato do owner a favor).

A classificação do executor não equivale a aceite; a coordenação
decide.

```text
TASK_ID=DELIA-CRI-E4-REAL-EVAL-ROLLBACK-AND-ACCEPTANCE-01
BASE_HEAD=0af32302e9ca3072e73a9b47d09206111c9c2e5d
FINAL_HEAD=this_commit (doc-only; base origin/main 6b201d91ac)
ORIGIN_MAIN=this_commit (fast-forward push verificado após o commit)
PUSH_VERIFIED=YES (fast-forward; upstream advanced during eval — cherry-picked via temp worktree, concurrent WIP untouched)

CANONICAL_REANCHOR=DONE (worktree repontado a 0af32302e9; upstream posterior 7e67055592 disjoint)
AUTHORITIES_READ=73→74→75→76→77→78(§12)→ADR 58→personality/01–04→outcome_assessment→conversational_response→loader→routes→ledger
CP_RQ=task spec §1–§21 — matriz §13 registrada por cenário

EVALUATED_SHA=0af32302e9ca3072e73a9b47d09206111c9c2e5d
RUNTIME_SHA=0af32302e9ca3072e73a9b47d09206111c9c2e5d
ENVIRONMENT=docker-local-dev-homologation
MODEL_REF=openrouter/moonshotai/kimi-k3
CONFIG_VERSION=worktree@evaluated-sha

INSTRUCTION_RESOURCE_VERSION=1
INSTRUCTION_RESOURCE_HASH=7e3c5515d3926c391aa961ca66c700df4c159b8daa100ade0b2377e5b6e32549
PRESENTATION_RESOURCE_VERSION=2
PRESENTATION_RESOURCE_HASH=c947616dcc906eaa49a7c0f5f57fd388aada0a5b42b1a2d6151567d95baf0c28

EVALUATION_AUTHORIZED=YES_BOUNDED
REAL_MODEL_AVAILABLE=YES
REAL_OWNERS_AVAILABLE=PARTIAL (delpi OpenAPI OK; TÉO/VISTA/DAVI-MCP catalog auth fails env-wide)

OFF_EVALUATION=EXECUTED (11 turns, real boundary)
ON_EVALUATION=EXECUTED (11 turns, effective=cri, recursos v1+v2 carregados)
PAIRED_COMPARISON=DONE (same identity/model/questions/scope, minutos de distância)
SCENARIOS_EXECUTED=11 (4 obrigatórios + 7 generalização/controle)

TEO_CASE=TEST_NOT_RUN (MCP ausente da superfície — limitação ambiente, verificada no serviço principal)
TEO_TEMPORAL_SEMANTICS_PROVEN=PROVEN_CONTRACT (owner declara updated_at=“Data de atualização”, touch em toda mutação, ORDER BY próprio) / LIVE_EXERCISE=TEST_NOT_RUN
DAVI_CASE=PASS (3 presented/3 delivered/65 available; campos rotulados; total atribuído à fonte)
DELPI_CASE=PASS (3/3/40; grupo 1008 conferido; total atribuído à fonte)
VISTA_CASE=TEST_NOT_RUN (MCP ausente — recusa honesta nos dois modos)

GENERALIZATION=PARTIAL (resultado único PASS-ON; lista/vazio/quantidade>retornada INCONCLUSIVE-TEST_NOT_RUN por budget/superfície; follow-up e controle PASS conversacional)
PERSONALITY_EVALUATION=PASS (com defeito cosmético de pluralização registrado)
FACTUAL_GROUNDING=PASS (somente folhas verbatim do owner; totais honestos; nada inventado)
TASK_OUTCOME=GROUNDED casos DELPI/DAVI; recusas honestas demais
PRESENTATION_QUALITY=ON>OFF demonstrado (rótulos, contagens corretas, truncamento declarado)

SECURITY_NEGATIVE_TESTS=PASS (auth MCP rejeitada fail-closed; sem writes; sem material act)
PROMPT_INJECTION_RESISTANCE=NOT_EXERCISED_LIVE (coberto por testes E3; sem vetor de injeção disponível nesta matriz)
AUTHORITY_BOUNDARIES_PRESERVED=YES
SELECTION_ONLY_PRESERVED=YES_LIVE

LATENCY_OFF=mean ~19.1s
LATENCY_ON=mean ~20.0s (≈+5%, dentro da variância do modelo; zero overhead estrutural)
GLOBAL_BUDGET_PRESERVED=YES (30s; estouro idêntico nos dois modos em turnos pesados)

INVALID_RESOURCE_FALLBACK=PROVEN_LIVE (requested=cri + resource v99 → fail_closed → effective=baseline → turno baseline real)
ROLLBACK_REAL=YES
ROLLBACK_RESULT=baseline restaurada (formato OFF reproduzido; sem estado residual)

BACKEND_REGRESSION=NOT_RERUN (nenhuma linha de runtime alterada nesta etapa; suíte 1838-passe do rework continua aplicável)
FRONTEND_REGRESSION=NOT_RUN (zero mudanças de frontend)
REAL_MODEL_EVALUATION=EXECUTED_PARTIAL (delpi real grounded; TÉO/VISTA indisponíveis no ambiente)

DEFECTS_FOUND=1 cosmetic (pluralização “1 exemplos” no vocabulário v2)
MATERIAL_RESIDUALS=TEO/VISTA/empty-result live TEST_NOT_RUN (ambiente); E4-G1 live exercise TEST_NOT_RUN
NON_BLOCKING_RESIDUALS=pluralização; turnos pesados >30s pré-existentes nos dois modos

RUNTIME_CODE_CHANGED=NO
MATERIAL_ACT=0
PRODUCTION_ACTIVATION=NO

FILES_CHANGED=4 (doc 79 novo, doc 74, README da trilha, ledger — somente documentação/evidência)
DOCUMENTATION_UPDATED=79 (este relatório), 74, README, ledger §6.359
LEDGER_UPDATED=§6.359

EXECUTOR_VERDICT=ACCEPT_WITH_RESIDUAL
ACCEPTANCE_RECOMMENDATION=coordenação decide — evidência real parcial mas positiva nos cenários executáveis

CRI_E4_ACCEPTED=NO_PENDING_COORDINATION
I04_ACCEPTED=NO
C3_EXECUTED=NO

NEXT_COORDINATION_DECISION=aceite CRI-E4 com residuais OU avaliação complementar em ambiente com MCP autorizado; defeito de pluralização → decisão de rework bounded separada
```

STOP → RETURN_TO_ARCHITECTURE_COORDINATION


## 12. Independent coordination review — 2026-10-21

**Two-level verdict:** `E4_EVALUATION_EXECUTION=ACCEPT_WITH_RESIDUAL` (the bounded real-model OFF/ON evaluation and rollback were carried out and documented); **`CRI_OPERATIONAL_ACCEPTANCE=INCONCLUSIVE`** (product-wide criteria not yet demonstrated). This avoids treating completion of the evaluation package as proven readiness for rollout. Independent review read doc 79 and its claimed experimental matrix on GitHub; independent re-execution of runtime/provider tests `TEST_NOT_RUN`. Runtime source not modified by E4. Later `main` commits do not retroactively establish evaluated SHA parity; assessed runtime pinned to `0af32302e9ca3072e73a9b47d09206111c9c2e5d`.

**Grounded positives:** OFF/ON observations with the same authorized subject and OpenRouter model demonstrate more legible DELPI product records, correctly attributed owner totals, requested-example presentation counts, observed fail-closed invalid resource behavior, and isolated environment restart rollback. These are genuine but narrow observations; do not infer general provider-neutral quality, statistically significant latency, or production readiness.

**Material boundaries:** (1) The question *naming DAVI* was served by `delpi.search_products` via `openapi:delpi`, **not a DAVI-MCP execution**; label as grounded DELPI product-query case, and leave DAVI-specialist outcome `TEST_NOT_RUN` rather than unqualified DAVI PASS. (2) TÉO and VISTA grounded MCP executions `TEST_NOT_RUN` due to `mcp_authentication_failed`; do not bypass auth or blame CRI without evidence. (3) TÉO's `updated_at` owner contract was inspected and supports process-update meaning and owner ordering, but CRI live temporal claim + scope/coverage were not exercised; lexical `_field_declares_modification` is not owner contract verification on its own. (4) True empty business result, >=requested items with timeout, end-to-end injection negatives and broader behavioral generalization were not established. (5) Singular/plural defect observed live (`1 exemplos`); quality verdict should be scoped, not general personality PASS. (6) 11 paired turns and +~5% average do not prove statistical latency equivalence; several runs hit 30s in both modes.

**Coordination state:** The five primary packages E0–E4 are completed **as development/evaluation tasks**, but the **CRI feature is not fully accepted for production**. Freeze the bounded E4 report; do not authorize an E4 implementation rework or product ON implicitly. Next decision must be a bounded, separately authorized **complementary acceptance gate** in an MCP-authorized environment covering TÉO/VISTA/DAVI owner selection, temporal meaning+coverage, empty result, generalization and real safety negatives. The pluralization finding may be handled as an explicitly approved minimal defect correction, not a hidden continuation of E4 or an infinite rework chain. Keep ON default OFF and current deploy unchanged. If the environment remains unavailable, keep `INCONCLUSIVE` instead of claiming PASS.

`E4_EVALUATION_EXECUTION=ACCEPT_WITH_RESIDUAL`; `CRI_OPERATIONAL_ACCEPTANCE=INCONCLUSIVE`; `CRI_PRODUCTION_ON=NOT_AUTHORIZED`; `COMPLEMENTARY_MCP_EVAL=DECISION_REQUIRED`; `E4_RUNTIME_CODE_CHANGED=NO`; `REAL_MODEL_EVAL=EXECUTED_PARTIAL`; `I04_ACCEPTED=NO`; `C3_EXECUTED=NO`.
