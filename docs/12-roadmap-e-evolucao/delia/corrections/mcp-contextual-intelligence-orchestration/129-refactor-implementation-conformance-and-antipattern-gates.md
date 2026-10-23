# 129 — Protocolo de conformidade da implementação: refactor modular e inteligência reutilizável

**Data:** 2026-10-23  
**TRACK:** DELIA-ORCHESTRATION-RESPONSIBILITY-REFACTOR-FINITE-01  
**Tipo:** diretriz normativa subordinada às authorities; NÃO é autorização de implementação  
**Estado:** PLANNED; R0–R7 NOT_AUTHORIZED até baseline pós-estabilização e decisão do Product Owner  
**Aplica-se a:** tasks de arquitetura, execução, review e testes do [plano 125](./125-orchestration-complete-refactoring-finite-plan.md); reuso/RPA do [128](./128-cross-application-intelligence-and-rpa-capability-review.md).

## 1. Autoridade, precedência e premissas

Antes de propor ou executar diff: working tree/HEAD/origin-main → Project Instructions e .cursor → docs 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec 24 → spec temática 03/60 e outras materiais → ledger vigente. Aplicar [ADR 58](./58-adr-llm-semantic-decision-ownership.md), [roadmap 59](./59-orchestrator-refactoring-finite-execution-roadmap.md), auditorias 56/57, matriz 113, decisão S4 [117](./117-s4-orchestration-redistribution-decision.md), pareceres [127](./127-d5-generalizing-remediation-independent-review.md) e docs futuros que prevaleçam por authority/HEAD.

Este documento não substitui a autoridade superior, não aprova runtime RPA/Work/Watch, não cria endpoints, não altera Policy, não muda fase, nem autoriza segunda extração sobre S4/117. Em conflito material ou evidência que invalide a premissa: STOP → EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED. Não reconciliar silenciosamente. Documentação não é prova de runtime.

**Regra operacional:** a instrução ao Devin nunca é autorização para criar todo arquivo citado como candidato. Um plano de organização é hipótese de destino, não ordem de mover código.

## 2. Entrega exigida ANTES de qualquer código R1–R6

A etapa R0 deve produzir, para cada grupo M01–M10 e cada função afetada, uma linha rastreável:

FUNCTION / CURRENT_FILE_AND_LINE / RESPONSIBILITY / OWNER / CANONICAL_SOURCE / REAL_CONSUMERS / BOUNDARY / CURRENT_CONTRACT / DEPENDENCY_DIRECTION / TRIGGER / TRUST_CLASS / BUSINESS_OUTCOME / EXISTING_EQUIVALENT / REUSE_DECISION / PROPOSED_FILE / ALLOWED_CHANGE / FORBIDDEN_CHANGE / CONTRACT_IMPACT / TESTS / ROLLBACK / STATUS.

Valores obrigatórios:
- EXISTING_EQUIVALENT = YES | NO | TO_INVENTORY.
- REUSE_DECISION = REUSE | EXTEND | NEW, apenas quando a evidência permitir a decisão; se TO_INVENTORY, decisão de criação fica PENDING.
- STATUS = KEEP | EXTEND | EXTRACT | SKIP_WITH_DECISION | BLOCKED.
- Fatos = PROVEN | TO_INVENTORY | PLANNED | TARGET; testes = PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE.

Para qualquer novo arquivo, registrar também por que o módulo existente é insuficiente, o motivo independente para mudar, sua API pública mínima, consumidores reais, regras de erro, limites, compatibilidade, isolamento e prova de redução de acoplamento. Sem TODOS esses campos e revisão, NOVO ARQUIVO = NÃO. Busca sem resultados não prova ausência de equivalente.

**Compartilhamento:** extrair para shared/ de plataforma exige 2+ consumidores reais, contrato estável, ausência de regra específica e ownership do compartilhado conforme .cursor/rules/platform-architecture-boundaries.mdc. Um módulo INTERNO de application pode ter um único consumidor quando houver responsabilidade/boundary real independente, mas isso não prova reuso cross-app nem autoriza package shared.

## 3. Separação de responsabilidades que deve sobreviver ao refactor

| Camada / owner | PODE realizar | NÃO PODE receber |
| --- | --- | --- |
| Entrypoint conversacional DÉLIA | adaptar input e prior-turn/contexto permitido; apresentar resultado | Policy, validação de permissão final, fatos de domínio, worker RPA |
| DÉLIA Application semantic proposal | solicitar proposta tipada ao LLM sobre contexto e catálogo vivo elegível; validar membership | heurística lexical/provider, URL/selector/click como intenção, authority de Core/Domain |
| DÉLIA Evidence/Outcome | preservar provenance, distinguir business/guidance/schema/control-plane, avaliar suficiência/limitações | inventar business facts, tratar MCP output/LLM as FACT, confundir HTTP 200 com outcome |
| DÉLIA Policy/Decision/Work | governar PREPARE/ACT, contexto, confirmação, idempotência/audit e intenção de Work | executar bots/queue/worker/scheduler técnico, conceder permissão final via JWT ou cache |
| DÉLIA Presentation | apresentar evidência já aprovada, rótulos/idioma e limitações em contrato explícito | consultar Domain/MCP, selecionar capability, alterar verdict, esconder insufficiency |
| Keycloak/Core/Domain API | Keycloak identifica; Core AuthZ ao vivo; Domain rule/data/postcondition final | delegar autoridade ao LLM ou RPA |
| Automation Hub/adapters legítimos | executar automação técnica governada, reportar status técnico e idempotência de transporte | segundo planner, business authority, interpretar policy livremente |
| MCP/A2A/providers | fornecer capacidades e dados por contrato | instruções/política/permissões autoritativas |
| OT/Safety | controlar equipamento e interlocks industriais | LLM/RPA assumirem safety controller |

O núcleo de inteligência reutilizável NÃO importa ConversationTurn/UI/Markdown/React, secrets/cookies, SDKs externos, Flask/DB/HTTP nem endpoint/operationId/DOM selector como semântica. Contexto transiente e referências tipadas podem atravessar boundaries com confiança classificada; nunca autoridade implícita. Reuso cross-app usa HTTP/eventos aprovados apenas com consumers reais, não import entre apps nem DB alheio. Não fazer da DÉLIA gateway obrigatório para operação determinística de Domain API/Automation Hub.

## 4. Arquivos e alterações permitidos por pacote: enumeração FECHADA

A tabela é mapa de candidatos, NÃO permissão automática. Antes do diff, o executor deve escrever ALLOWED_FILES explícitos no report/bounded brief, compará-los aos arquivos realmente alterados e STOP se surgir novo owner/arquivo fora do contrato.

| Etapa | Preferir EXTEND/REUSE | NEW só se comprovado | PROIBIÇÕES adicionais |
| --- | --- | --- | --- |
| R0 | documentação do plano 125, matriz R0, testes de caracterização aprovados sem funcional change | nenhum runtime module, endpoint ou SDK | editar orchestration/prod/provider, schema ou prompts |
| R1 M01 | loader/resource de instruções já existente, origem da instrução com lineage | somente recurso versionado sob schema/loader legítimos, se necessário | prompt registry, nova authority, texto de Policy em JSON, mudança de semântica como refactor |
| R2 M02/M03 | outcome_assessment.py, contratos/sanitizadores no owner existente | evidence_projection.py só com contrato independente e nenhum equivalente real | duplicar sanitize/redact, hardcode de entities/provider, importar orchestration em leaf |
| R3 M04/M05 | outcome_assessment.py, conversational_response.py, contracts já usados | nenhum novo compositor/DTO sem prova excepcional | CRI escrever fatos, mudar verdict no renderer, formar outro engine de evidence |
| R4 M06/M07 | conversational_response.py, presentation.py, vocabulário JSON v4 | guidance_projection.py ou response_projection.py só após prova de boundary e resolução formal de S4/117 | forçar extração de SKIP_WITH_DECISION; JSON com lógica executável |
| R5 M08/M09 | interaction/argument_validation.py, model_invocation contracts, current coordinator | nenhum parser semântico, registry de provider ou model broker | if por frase/owner, segundo planner, alterar retries/budget/policy sem task |
| R6 M10 | orchestration.py para coordenação, current capability_attempt/pending/ports/contracts | nenhum novo engine de workflow/ACT/planner | reescrever state machine, duplicar Policy, trazer adapter/provider mechanics para application |
| R7 | testes, avaliação, documentação/evidência; release separado quando autorizado | endpoint/worker/RPA NÃO é escopo do refactor | deploy automático, regressão ignorada, aceite pelo executor |

Alvos físicos NÃO aprovados: evidence_projection.py, guidance_projection.py, response_projection.py, semantic_surface_projection.py. A ausência de justificativa é SKIP_WITH_DECISION, e não motivo para inventar util.py, manager.py, service.py, facade.py, base.py ou common.py. Se um destino legítimo existir na matriz, REUSE/EXTEND antes de NEW.

## 5. Contratos e imports: testes de inversão obrigatórios

Fluxo permitido de dependência no núcleo: orchestrator → interfaces/tipos de application/domain → leaf puro de projeção/evidence/outcome → tipagem apropriada; apresentação consome resultado saneado; infrastructure/adapters implementam ports, sem serem importados em Domain/Application.

**Proibido em módulos novos ou alterados:**
1. leaf de Evidence/Outcome/Presentation importar orchestration.py;
2. domain/application importar SDK/DB/HTTP/framework/providers por comodidade;
3. arquivo compartilhado importar MFE/ConversationTurn/handler/cookies/provider mechanics;
4. bounded context A importar application/domain internos de bounded context B;
5. circularidade mascarada por import dentro de função, global singleton, service locator, dependency injection por string ou importlib;
6. copiar sanitizador/classifier/field-label resolver para romper um ciclo, mantendo dois owners;
7. wrapper/facade permanente para manter função duplicada sem contrato de depreciação e remoção;
8. retornar dicionário genérico sem contrato quando já existe DTO/typing legítimo; não criar DTO espelho do mesmo conceito;
9. transformar redistribuição de código em change de comportamento sem task/ADR.

**Prova mínima:** gerar call graph/AST/import DAG do caminho impactado, comparar before/after; verificar módulos e funções públicas por consumidores reais; examinar imports indiretos, dynamic imports e strings de provider, URL, SQL, selectors e tokens nos diffs. Teste automatizado existente é preferível; inspeção manual só é evidência manual, nunca CI PASS.

## 6. Antipadrões sentinela e condições inequívocas de bloqueio

| Código do gate | Antipadrão / evidência observável | Decisão obrigatória |
| --- | --- | --- |
| AP-01 | novo god module contém selection+evidence+render+write/dispatcher; ou pasta criada só para deslocar LOC | REWORK; separar por contratos ou SKIP |
| AP-02 | criação NEW com EXISTING_EQUIVALENT=YES/TO_INVENTORY ou sem owner/consumer real | STOP criação; REUSE/EXTEND ou TO_INVENTORY |
| AP-03 | import circular, import reverso application→infra ou cross-bounded-context | REWORK/EXECUTION_DRIFT se invalida ownership |
| AP-04 | duplicate Policy/AuthZ/domain rule/registry/sanitizer/DTO/catalog; shared/ baseado em consumer TARGET | BLOCKER/REWORK conforme autoridade; nunca merge |
| AP-05 | planner faz branch de provider, endpoint, operação técnica, selector ou hardcoded answer de fixture | REWORK; LLM semântico com schema/membership |
| AP-06 | regex/substring/keyword/rank substitui a interpretação do modelo | REWORK; proibir lexical-intent engine |
| AP-07 | LLM/metadata/cache/memória/JWT decide permissão, business FACT ou postcondition | BLOCKER → EXECUTION_DRIFT; fail-closed |
| AP-08 | RPA bot/script/queue/worker/scheduler implementado na DÉLIA por conveniência; ACT sem Policy/Core/Domain | BLOCKER → STOP; devolver Automation Hub/owner |
| AP-09 | RPA DONE ou HTTP 200 registrado como business Outcome sem Domain postcondition | REWORK; INCONCLUSIVE até autoridade confirmar |
| AP-10 | side effect ambíguo reaplicado; PREPARE tratado como ACT; C6 Watch faz ACT autônomo ou L5 ON | BLOCKER; no retry cego, política de autonomia congelada |
| AP-11 | tool/agent metadata executado como instrução, discovery como permission, OT sem interlock | BLOCKER; untrusted data e safety owner |
| AP-12 | evidence de schema/entities.* promovida a resposta factual sobre produto sem relevância | REWORK; outcome/intent evidence gate |
| AP-13 | CRI/reporter muda verdict/provenance ou substitui guidance válido por texto inventado | REWORK; apresentação sem authority |
| AP-14 | texto extenso/Policy/config executável escondido em JSON sem schema/lineage | REWORK/ADR; versionamento legítimo |
| AP-15 | contrato quebrado sem migration/additive/deprecation; operationId instável | STOP → CONTRACT_DECISION_REQUIRED; expand-and-contract |
| AP-16 | commit/refactor misturado a feature/fix, dirty concurrent changes, rollback não viável | STOP pacote afetado; task separada |
| AP-17 | teste passou só em fixture; sem generalização/negativos/outcome, mas report PASS | INCONCLUSIVE; não autorizar próxima fase |
| AP-18 | secret/token/PII enviado a prompt/RPA/log/test fixture; AuthZ token-cached | BLOCKER → STOP, tratar incidente se aplicável |
| AP-19 | criar endpoint/plugin consumidor TARGET somente para justificar abstração | SKIP/REWORK; consumidor deve ser legítimo e presente |
| AP-20 | reclassificar decisão S4/117, Q03/B1/59 ou fase sem nova evidência e review | ARCHITECTURE_DECISION_REQUIRED; STOP |

STOP material não autoriza código de “correção” fora do escopo; relatar a causa e retornar ao owner. Rework é no máximo um bounded por pacote conforme plano 125, sem loop.

## 7. Testes obrigatórios e provas adversariais

**A cada pacote com runtime diff** (além dos testes específicos no plano 125):
- invariantes de trust: schema/contract/guidance/business/control-plane, spoof de metadata MCP/A2A, vazamento de agent_directives e credenciais;
- seleção provider-neutral com add/remove/rename/reorder, no-tool, aliases e negativas; variação inédita com LLM quando semântica material;
- D4 autoconhecimento, D5/D5-R guidance/formatos, D8/D8-R READ/contexto, SIPOC e perguntas explicitamente sobre contrato; proveniência/idioma/limitações;
- CRI on/off, owner unavailable, scope revoked, consent expired, context stale, source missing, timeout/retries, empty/truncated, HTTP 200 com business miss;
- PREPARE/ACT com Core live/AuthZ negative, Domain final rule, idempotência, audit, confirmação, simulate!=apply, ambiguous side-effect, no duplicate ACT;
- se RPA/Work afetado por contrato real e autorizado: technical DONE/business UNVERIFIED, RPA→API replacement, scheduler duplicate/overlap, C6 no autonomous ACT, OT fail-closed. NÃO criar runtime falso para esses tests;
- se um contrato interno virar API/event cross-app autorizado: old/new consumer, 401/403/invalid issuer/tenant, rate/budget, schema version, operationId stable, redaction, rollback e observability.

**R0 documental:** fontes/consumers/AST/import map com PROVEN/TO_INVENTORY; NÃO reportar TEST PASS de execução. **R1–R6:** RED/green ou baseline→parity com SHA, full backend, architecture checks existentes, análise residual e resultados. **R7:** outcome no modelo/config avaliado, deploy apenas sob autorização explícita, independent review. Simuladores são testes, não evidência de produção.

Sempre distinguir TEST_NOT_RUN, INCONCLUSIVE, STALE_EVIDENCE de PASS. Não apagar teste para torná-lo verde.

## 8. Uso do CI: sem alegar enforcement inexistente

Ler e executar os comandos suportados por .cursor/rules/architecture-ci-enforcement.mdc e pelos scripts reais em scripts/ci (quando materiais). Verificar CLI real antes de invocar; não inventar flag ou gate. Os CI guards atuais são diff-aware em partes e NÃO cobrem automaticamente todos os AP-01…AP-20. Revisor precisa listar:
- CHECK_ALREADY_AUTOMATED com caminho do script + resultado no SHA;
- CHECK_MANUALLY_REVIEWED com diff/linha, responsável e evidência;
- CHECK_NOT_IMPLEMENTED (não rotular como PASS; abrir necessidade bounded se gate automático for realmente justificável).

Não adicionar auditor global ou ignore-list nova sem owner/consumer/contract, sinal estático confiável, plano de falsos positivos e teste que detecta a violação e o negativo legítimo. Nunca contornar CI/quality via exceção ampla.

## 9. Contrato de entrega por subetapa ao Devin

**Antes do código (MANDATORY):**
TASK_ID / STEP / BASE_HEAD / GIT_STATUS / APPLICABLE_AUTHORITIES / AUTHORIZED_PHASE / GOAL / ALLOWED_FILES / FORBIDDEN_FILES / PRECONDITIONS / SOURCE_FUNCTIONS / DESTINATION_MODULES / OWNER_AND_CONSUMERS / EXISTING_EQUIVALENT / REUSE_DECISION / CONTRACT_IMPACT (NONE|ADDITIVE|BEHAVIORAL|DEPRECATED|BREAKING) / CP-RQ / RISKS_AND_AP_GATES / TEST_PLAN / ROLLBACK_PLAN.

**Depois do código (MANDATORY):**
FINAL_HEAD / ORIGIN_MAIN / PUSH_VERIFIED / ACTUAL_FILES / SCOPED_DIFF / FUNCTION_MOVE_MAP / IMPORT_DAG_BEFORE_AFTER / DUPLICATE_CHECK / API_COMPAT / AST_OR_ARCH_CHECK / RED_GREEN / FULL_BACKEND / SECURITY / GENERALIZATION / USER_OUTCOME / BUSINESS_POSTCONDITION / AI_EVAL_SHA_MODEL_CONFIG / AP01_AP20_REVIEW_WITH_EVIDENCE / RESIDUAL_SEARCH / ROLLBACK_READY / LEDGER / EXECUTION_DRIFT / EXECUTOR_VERDICT.

Todos os AP gates relevantes devem ser classificados PASS (evidência), FAIL, INCONCLUSIVE, TEST_NOT_RUN ou NOT_APPLICABLE_COM_RATIONALE. Se qualquer AP blocker material não tiver evidência, o pacote NÃO está pronto para merge/deploy. A classificação N/A não pode esconder um gate aplicável. Não deixar campo vazio.

Executor conclui apenas IMPLEMENTATION_EVIDENCE_READY_FOR_REVIEW / IMPLEMENTATION_FAILED / IMPLEMENTATION_INCONCLUSIVE / EXECUTION_DRIFT; **somente coordenação** emite ACCEPT/ACCEPT_WITH_RESIDUAL/REWORK/INCONCLUSIVE e liberação da etapa seguinte.

## 10. Portas de autorização e finalização

1. **NOW:** correção pré-refactor funcional enviada ao Devin permanece separada; acompanhar sua evidência e revisão. PLANO 125/129 = documentação; R0–R7 = NOT_AUTHORIZED.
2. **ENTRY R0:** somente após estabilização e decisão explícita do PO; R0 não cria runtime/module/adapter/endpoint. Resultado: matriz M01–M10 e decisões de candidatos/CONTRACT, sem inventar consumidores TARGET.
3. **ENTRY R1…R6:** autorizar pacote bounded individual após review das precondições; não usar conclusão de R0 como permissão irrestrita de todo o plano.
4. **ENTRY R7/deploy:** QA no SHA/config, contrato de release e rollback, autorização operacional específica; não se presume release porque testes unitários passaram.
5. **CLOSE:** comparar plano/contrato/consumers antes-depois, business outcomes, CI/negative tests e resíduos; preservar S4 SKIP quando não existir boundary legítimo, mesmo que orchestration.py continue grande.
6. **FAIL/DRIFT:** primeira violação crítica STOP → evidence → Product Master/architecture. Sem segundo engine, sem patch de frase, sem rework infinito.

**Sentença de execução vinculante:** se a arquitetura modular correta não puder ser implementada com owner/contrato/consumidor evidenciado, **não implementar** a extração. Registrar SKIP_WITH_DECISION ou ARCHITECTURE_DECISION_REQUIRED. A ausência de extração é preferível a um novo antipadrão.
