# 120 — Contrato executivo: rework S5, deploy e homologação produtiva
**TRACK_ID:** DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
**TASK_ID:** DELIA-C3-S5-BOUNDED-OUTCOME-REWORK-PRODUCTION-RELEASE-01
**Data:** 2026-10-23
**Status:** PO_AUTHORIZED_EXECUTION_AND_GOVERNED_DEPLOY; ACCEPT ainda pendente de revisão independente.
**Executor:** Devin. **Review:** Architecture / Coordination.
**Source of work:** [Plano 112](./112-self-awareness-finite-delivery-plan.md), [S0 113](./113-s0-contract-freeze-and-responsibility-matrix.md), [S1 114](./114-s1-operational-self-awareness-implementation.md), [S2 115](./115-s2-semantic-relevance-guidance-projection.md), [S3 116](./116-s3-ptbr-labels-governed-vocabulary.md), [S4 117](./117-s4-orchestration-redistribution-decision.md), [S5 118](./118-s5-homologation-and-consolidated-evidence.md), [review 119](./119-s1-s5-independent-coordination-review.md).

## 0. Reanchor e precedência
Cada ação revalida HEAD/origin/main/git status, Project Instructions/.cursor e authorities nesta ordem: [16](../../16-execution-master-plan.md) → [50](../../50-standalone-copilot-application-architecture.md) → [17](../../17-component-and-contract-map.md) → [49](../../49-architecture-and-design-patterns-standard.md) → [51](../../51-platform-integration-baseline.md) → [52](../../52-standalone-repository-and-bootstrap-plan.md) → [21](../../21-data-and-state-model.md) → [20](../../20-testing-and-acceptance-matrix.md) → [25](../../25-requirements-traceability.md), [24](../../24-product-specification.md), [03](../../03-capability-model.md), [60](../../60-agent-interoperability-mcp-a2a-and-tool-protocols.md), [ADR 58](./58-adr-llm-semantic-decision-ownership.md), [roadmap 59](./59-orchestrator-refactoring-finite-execution-roadmap.md), ledger `docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md`. GitHub=truth, ledger=state. Se novo SHA alterar contratos, atualizar baseline antes de executar. Não confiar só neste documento.

## 1. Escopo fechado e invariantes
**Objetivo:** fechar outcome funcional de D4/D5/D8 sem reabrir S0–S4, Q01–Q03, RC1/RC2, B1 ou rework S3. Um único rework bounded S5 autorizado (limite 1). Sem novo planner, registry, second knowledge engine, branches por provider, heurísticas lexicais de intent, shadow catalog, novas autoridades, mudança de Core/Domain/Keycloak. Reuso: `InvokeModel/_propose`, admission `surface_inquiry`, `ProviderSurface.groups`, guidance/evidence/outcome existentes, `conversational_response` e JSON `cri_presentation.delpi.json` v4. Antes de criar função/contrato, registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`. Manter selection-only, MODEL_AUTHORED_FACTUAL_PROSE=NONE, 60/3/300, READ≠PREPARE≠ACT, AuthZ live, Policy, idempotência, proveniência, redaction e safety.

## 2. Ordem de execução sem pausa administrativa
**A — Diagnóstico causal mínimo:** reproduzir e correlacionar S5 D4a/b/c, D5a/b, D8a e no-tool/multiturno por trace/owner/capability/admission/goal/tool invocation/evidence/CRI/render; fixar baseline RED no SHA e modelo/config usados. Não gerar inventário novo. Verificar se a falha decorre de proposta LLM, contrato owner, validação, montagem de contexto, deadline ou projeção; não pressupor que todo FAIL é bug do runtime.

**B — Correção bounded:** corrigir apenas causas provadas, usando mecanismos existentes. D4: pergunta sobre a própria DÉLIA/superfície → listagem viva compreensível, sem dump operacional, sem nome inventado e sem equiparar published a allowed; variantes provider-neutral. D5: consulta sobre visualizações nos painéis → informação dos contratos/guidance apropriados e resposta em PT-BR ou insuficiência específica comprovada; não promover `entities.playlist`, control-plane ou schema bruto a business FACT. D8: READ legítimo do material 10080043 (se autorizado) → descrição exatamente da fonte com campos PT-BR via JSON v4, sem traduzir valores. No-tool: resposta coerente ou falha honesta, sem bypass por invalid JSON. Não ajustar uma frase do prompt apenas para passar fixture: testes inéditos e metamórficos obrigatórios.

**C — Testes/evals:** escrever RED antes do diff; testes unitários, integração e segurança; suíte backend completa; negativos AuthZ, injection, READ/ACT, provenance, tool metadata untrusted, catálogo renomeado/reordenado/adicionado/removido; casos no-tool, follow-up e troca de assunto. Rodar Ollama local com identidade DEV governada, sem egress pago, e declarar limitação do 3B separadamente. Avaliar LLM de referência apenas com budget e autorização operacionais existentes; registrar SHA/model/prompt/config/latência/tokens reais vs estimados. Falha de modelo, resposta inválida ou owner gap = FAIL/INCONCLUSIVE apropriado, nunca PASS.

**D — Revisão técnica pre-release:** conferir diff contra requirements RQ-SA01–09 / AC, migrations=0 salvo decisão externa, compatibilidade CRI/non-CRI, JSON v4, nenhum secret logado, ownership preservado, regression/pass e rollback. Commit/push main ff-only; confirmar SHA remoto e que fix é ancestral do release. Evitar push de artefatos temporários, credenciais, logs sensíveis ou fixtures com token. **Se houver FAIL material de segurança, drift de authority, autorização impossível ou migração imprevista: NÃO DEPLOY; STOP subescopo e devolver relatório.**

**E — Deploy prod governado, autorizado explicitamente pelo PO como etapa final:** usar somente infraestrutura/runbook e acesso operator legítimos, validar topologia e comando existentes no HEAD antes de executar (não presumir script). Planejar e registrar pre-deploy SHA, imagem, backups/rollback e service dependencies; implantar somente o serviço necessário `delia-api`, sem mexer Keycloak/Core/Domain, permissões, tokens, usuários ou secrets. Inspecionar imagem/runtime exatos, configuração 60/3/300 e saúde, gateway sem 502/504, AuthN 401 sem bearer e pós-condições. Se já houver deploy concorrente da mesma correção, verificar provenance/runtime e não redeploy desnecessariamente. Se pós-deploy FAIL material, executar rollback documentado via runbook se seguro/autorizado; relatar runtime final; jamais mascarar falha.

**F — Homologação produtiva D4/D5/D8:** rodar somente por identidade legítima e autorizada (sessão PO ou e2e prod governado se efetivamente existente), via caminho de produção real, Core/Domain/MCP/Kimi reais. Não criar usuário produtivo, resetar senha de pessoa real, importar token, contornar MFA/AuthZ ou coletar segredo. Capturar input, hora, correlation ID seguro, provider/owner/capability, epistemic/grounding, resposta integral sem dados sensíveis, latência, tentativas, tokens providos ou `NOT_AVAILABLE`, versão/config e outcome. D4 deve explicar capacidades sem dump interno; D5 deve responder formatos com fonte ou insuficiência real; D8 deve preservar registro e rótulos PT-BR. Se nenhuma identidade homologada estiver disponível, `PRODUCTION_AUTHENTICATED_TESTS=TEST_NOT_RUN`, com deploy técnico separado de outcome. Não alegar ausência de leak em prod sem teste wire.

**G — Encerramento documental:** atualizar doc 120 com seção de execução ou relatório 121, README da trilha, matriz 25 se lacuna real e ledger com SHAs, testes, outcomes e revisão; enviar relatório consolidado para Architecture/Coordination. Executor não autodeclara ACCEPT/PLAN_COMPLETE.

## 3. Critérios de aceite (gates)
AC-S5-A: RED baseline e causa por cenário, mínimo diff. AC-S5-B: D4 original+variantes com generalização (no technical ops dump, no invented names). AC-S5-C: D5 guidance/read end-to-end ou insuficiência owner comprovada, sem schema cru. AC-S5-D: D8 business READ e PT-BR labels no runtime testado, valor/proveniência verbatim. AC-S5-E: no-tool, multiturno, negativas, injection e AuthZ. AC-S5-F: backend full PASS no SHA exato, e avaliações reais identificadas por config/model; resultado de 3B não pode substituir Kimi. AC-S5-G: deploy technical PASS com release/runtime SHA e rollback documentado. AC-S5-H: homologação produtiva separada, sem inventar credenciais. `PLAN_COMPLETE` requer aceite independente da coordenação e critérios materiais comprovados; se S5 rework não fechar, STOP, Product Master decide, sem segundo rework.

## 4. Relatório obrigatório
```text
TASK_ID=DELIA-C3-S5-BOUNDED-OUTCOME-REWORK-PRODUCTION-RELEASE-01
TRACK_ID=DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
BASE_HEAD= FINAL_HEAD= ORIGIN_MAIN= PUSH_VERIFIED=
AUTHORITIES_READ= LEDGER_REFERENCE= CP_RQ= REUSE_DECISIONS=
ROOT_CAUSE_D4= ROOT_CAUSE_D5= ROOT_CAUSE_D8= ROOT_CAUSE_NO_TOOL=
RED_GREEN= FULL_BACKEND= GENERALIZATION= SECURITY=
EVAL_SHA_MODEL_PROMPT_CONFIG= LOCAL_OLLAMA_OUTCOMES=
DEPLOY_STATUS= PRE_DEPLOY_SHA= RELEASE_SHA= IMAGE= RUNTIME_SHA=
SERVICE_HEALTH= ROLLBACK_READY= ROLLBACK_EXECUTED=
PROD_IDENTITY_GOVERNED= PROD_D4= PROD_D5= PROD_D8=
PROD_LATENCY_ATTEMPTS_TOKENS= USER_OUTCOME= BUSINESS_OUTCOME=
FILES_CHANGED= DOCS_LEDGER_UPDATED= EXECUTION_DRIFT=
REWORK_S5_USED=1
EXECUTOR_VERDICT= COORDINATION_REVIEW_REQUIRED=YES
```
