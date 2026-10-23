# 124 — D5: investigação causal e contrato de correção generalizante

**Data:** 2026-10-23. **TASK_ID:** DELIA-C3-D5-GENERALIZING-EVIDENCE-RELEVANCE-REMEDIATION-01.
**Owner:** coordenação de arquitetura; execução/testes/deploy: Devin/Cursor autorizado pelo Product Owner a investigar e implementar a correção do D5 FAIL e D5-R PARTIAL.
**Estado:** RCA estática parcial PROVEN; execução de diff de runtime/tests PENDING.
**Baseline:** [123 — produção Kimi](./123-production-authenticated-homologation-d4-d5-d8.md), [122 — review](./122-s5-rework-independent-coordination-verdict.md), [120 — release contract](./120-s5-bounded-outcome-rework-and-production-release-contract.md), [119 — review original](./119-s1-s5-independent-coordination-review.md), [115 — S2](./115-s2-semantic-relevance-guidance-projection.md), [110 — RC1/RC2](./110-evidence-projection-control-plane-remediation.md), [112 — plano](./112-self-awareness-finite-delivery-plan.md), [ADR 58](./58-adr-llm-semantic-decision-ownership.md), [roadmap 59](./59-orchestrator-refactoring-finite-execution-roadmap.md). Reancorar sempre em HEAD/status/.cursor/authorities 16→50→17→49→51→52→21→20→25 + 03/24/60 + ledger.

## 1. Facts vs hypotheses

**PROVEN — produção 2026-10-23 / doc 123:** D5 Kimi escolheu `mcp:vista.get_catalog`, retornou `entities.playlist` com JSON técnico para pergunta sobre formatos. D5-R escolheu `get_product_guide`, executou `index_select`, terminou `insufficient_evidence`. D4 e D8 foram PASS; nenhum write. HTTP 200/grounded não comprovam resposta útil.

**PROVEN — inspeção estática em HEAD:** `_contract_fact_rows(outcome)` dentro de `delia-api/app/application/capability_provision/orchestration.py` possui branch de `entity_schemas` que emite literalmente `entities.<name>: <JSON compactado>` para até quatro entradas, e o contrato `OUTCOME_CONTRACT_FACTS` pode alimentar CRI. `_CAPABILITY_VOCABULARY_KEYS` já remove seções como `productguide` e `displayformatcatalog` dos records de negócio, mas não torna conteúdo de schema pertinente à pergunta. `_deterministic_guidance_content` e `_select_guidance_records` existem. Proteção de `agent_directives`/control-plane RC1 permanece obrigatória.

**TO_INVENTORY:** qual é o ponto exato de classificação `CONTRACT_FACTS`→`answered` no turno D5; por que `index_select` rejeitou cobertura em D5-R; conteúdo do `get_product_guide` nas etapas relevantes; qual evento typed marca interesse em documentação de formato; compatibilidade com outras perguntas legitimamente sobre schema/campos/entidades.

**Não inferir:** `get_catalog` é sempre seleção errada (ele pode publicar `displayFormatCatalog`); `get_product_guide` sempre tem resposta suficiente; qualquer `entities.*` é malicioso; token/output do LLM é FACT.

## 2. Decisão de responsabilidade

LLM existente é dono da interpretação semântica de intenção, relevante section/capability e necessidade de owner, via proposal tipado. Determinístico valida contrato, proveniência, admissibilidade, sufficiency/outcome, segurança e apresentação. A regra generalizante é: **metadados de catálogo/schema só podem suportar resposta explícita sobre contrato/schema quando a correspondência de evidência à intenção for comprovada; não são dados de negócio nem resposta automática sobre documentação funcional do produto**. Não usar blacklist global `entities.playlist`, branch VISTA, keywords `formatos`, heurísticas por provider ou filtro de registros empresariais homônimos. Sem novo planner/catalog/engine. `EXISTING_EQUIVALENT=YES`: seleção tipada atual + projection/evidence + outcome_assessment + guidance + conversational_response + JSON governado. `REUSE_DECISION=EXTEND` sujeito aos gates reais.

## 3. Sequência bounded de implementação (único pacote excepcional, não novo S5)

**A. Reanchor:** conferir SHA/runtime afetado, authorities, ledger e decisão de produto sobre exceção após rework S5 1/1. Não reabrir Q01–Q03/B1/RC1/RC2.
**B. Reproduzir RED:** usar payload real minimizado e sanitizado da produção, com `entities.playlist`, `displayFormatCatalog`, `productGuide`, e owner guidance; D5 original + reformulação; controle positivo "Quais entidades, campos e filtros publica o contrato deste painel?" para não remover capacidade legítima de responder sobre schemas; D4/D8 positivos; variantes provider-neutral com nomes trocados.
**C. Traço D5-R:** capturar payload e índice selecionado em `index_select` e reasons do `assess_outcome`; determinar se houve seção perdida por budget, índice incorreto, escolha semântica ou ausência verdadeira de conteúdo; nenhuma correção até causa classificada.
**D. Fix mínimo:** na fronteira existente de projeção e suficiência, conservar distinção tipada entre (i) documentação funcional, (ii) schema/descritores de contrato, (iii) dados empresariais. A seleção LLM pode propor seções relevantes; validar membership e provenance, sem inventar prosa factual. Para informação de formatos disponível: projetar texto do guide em apresentação natural e bounded; para ausência real: insuficiência precisa, nunca dump do schema. Se exigir alterar `selection-only`, STOP subescopo e decisão ADR explícita.
**E. Validar:** RED→GREEN, suite backend completa, positivos/negativos, RC1/RC2 anti-leak, owner/contract homonyms, D4/D8, segurança AuthZ/PREPARE/ACT, providers renomeados/removidos, N1 no-tool, observability. Eval Ollama local para generalização; modelo Kimi permitido apenas nos gates de custo/credencial legítimos; registrar output e primeiro estágio divergente.
**F. Release:** antes de deploy, QA de code/contract/schema/rollback e baseline; commit/push main ff-only. Deploy delia-api somente se gates materiais PASS, runbook legítimo e autorização operacional; verificar image/runtime SHA, health, 401 sem bearer; rollback se incidente material. Homologar D5+D5-R em produção com identidade legítima, D4/D8 como regressões, sem extrair tokens nem reutilizar indevidamente credenciais. Sem autorização de identidade: TEST_NOT_RUN, nunca PASS.
**G. Evidência:** novo relatório sequencial, README, ledger; causas PROVEN vs HYPOTHESIS e status AC, test SHA/model/config, decisão sobre rework excepcional. Retornar à coordenação; executor nunca se autoaceita.

## 4. Critérios de aceite

- AC-D5-01: D5 original não expõe `entities.playlist`, outros schemas, operations nem JSON bruto; fornece formatos publicados ou insuficiência honesta específica.
- AC-D5-02: D5-R consulta/seleciona guidance pertinente com evidência de cobertura ou reasons exatos da insuficiência; não se aceita mera troca de capability.
- AC-D5-03: consulta explicitamente sobre schema/entidades continua podendo exibir dados contratuais legítimos, devidamente identificados como contrato, nunca business records.
- AC-D5-04: homônimos e records empresariais não perdidos; RC1/RC2 não regridem.
- AC-D5-05: D4, D8/D8-R e SIPOC preservados, generalização provider-neutral.
- AC-D5-06: seleção semântica permanece model-driven; ausência de branches lexicais/provider.
- AC-D5-07: backend full + negativos de segurança PASS, SHA/config identificados; no unauthorized ACT.
- AC-D5-08: produção D5/D5-R com Kimi e identity governada outcome PASS; release/runtime e rollback documentados.
- AC-D5-09: diff mínimo nos owners corretos, sem catálogo paralelo, sem migração arbitrária.
- Rework anti-loop: pacote de exceção único; no máximo um rework de implementação dentro deste pacote, condicionado a review; novo fracasso => STOP/PO, não patches ilimitados.

## 5. Reporting

```text
TASK_ID=DELIA-C3-D5-GENERALIZING-EVIDENCE-RELEVANCE-REMEDIATION-01
BASE_HEAD= FINAL_HEAD= ORIGIN_MAIN= PUSH_VERIFIED=
AUTHORITIES_READ= CP_RQ= LEDGER=
D5_ROOT_CAUSE= D5R_ROOT_CAUSE= FIRST_DIVERGENT_STAGE=
EXISTING_EQUIVALENT= REUSE_DECISION= OWNER_CONTRACT_CONSUMERS=
RED_GREEN= BACKEND_FULL= SECURITY= GENERALIZATION= KIMI_EVAL=
D4_OUTCOME= D5_OUTCOME= D5R_OUTCOME= D8_OUTCOME= N1_OUTCOME=
DEPLOY_STATUS= RUNTIME_SHA= IMAGE= ROLLBACK=
PROD_AUTH_IDENTITY_STATUS= PROD_USER_OUTCOME=
AC_STATUS= FILES_CHANGED= DOCS_LEDGER=
EXECUTION_DRIFT= EXECUTOR_VERDICT= COORDINATION_REVIEW_REQUIRED=YES
```
