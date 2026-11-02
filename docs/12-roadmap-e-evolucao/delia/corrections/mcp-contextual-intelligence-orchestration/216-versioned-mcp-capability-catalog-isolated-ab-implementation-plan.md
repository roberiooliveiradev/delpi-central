# 216 — Plano integral: catálogo MCP versionado em JSON e experimento A/B isolado

**Status:** APPROVED_FOR_BOUNDED_EXPERIMENT_DESIGN; IMPLEMENTATION_PENDING; PRODUCTION_SWITCH_NOT_APPROVED.  
**Data:** 2026-11-02. **HEAD observado no planejamento:** `52228e9551deff0c3eb19c7a4fdbec4dbc246f20` (revalidar na execução).  
**TASK_ID sugerido:** `DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01`.  
**Contexto:** hipótese da coordenação: persistir snapshots versionados de `tools/list` e contratos semânticos e sincronizar manualmente por script, oferecendo ao LLM contexto estável/relevante, pode melhorar owner/capability selection, argumentação, custos e latência.
**Autoridades obrigatórias:** HEAD/status, Project Instructions/.cursor, documentos 16→50→17→49→51→52→21→20→25, arquitetura técnica, product spec, especificação temática, ledger. Em divergência: STOP/EXECUTION_DRIFT/ARCHITECTURE_DECISION_REQUIRED, sem reconciliação silenciosa.
**Referências:** Doc 210 (plano vivo), Doc 211 (28 cenários congelados), Doc 212 (argumentos), Doc 213 (discovery live Task 33 e arquitetura-alvo), Doc 214 (gates S2–S6), Doc 215 (checkpoint), execution ledger; revalidar estado atual no HEAD. Task S2–S6 e sua homologação não são canceladas nem substituídas.

## 0. Objetivo, limites e decisões congeladas

Entregar **experimento funcional isolado**, não uma segunda orquestração: A=discovery live atual, B=snapshot JSON persistido e versionado, ambos usando o **mesmo planner, prompts, inferência/modelo, Policy/Decision, providers de execução, AuthZ e Outcome**, com alternância exclusivamente no *discovery/semantic projection boundary* existente. Nenhuma mudança de comportamento de produção ou da variante A.
- Default e produção: `LIVE`; variante `SNAPSHOT_EXPERIMENT` somente allowlisted em avaliação local/test. Flag de composição com fail-closed, sem ativação por requisição do cliente.
- Snapshot é **dados não confiáveis**, não permission, não fonte de FACT, não prova de disponibilidade/execução. Antes de ACT/WRITE (não autorizados neste experimento), política normal. Para READ/ANALYZE, verificar permissão live e contrato/owner conforme boundary atual; cache não faz invocation por si.
- Nenhuma UI, auto-sync em produção, cron novo, segundo planner, substituição do MCP SDK, migração de Chat, integração por banco alheio, ou alteração de perguntas/oráculos para obter PASS.
- Decisão Task 33 `tools/list live por request` permanece baseline congelada; eventual promoção exige ADR independente e aprovação de coordenação. **Documentação deste plano não autoriza mudar essa decisão em produção.**

## 1. Inventory gate — antes de projetar componentes

Registrar fluxo real de owner identity, `SpecialistInterop`, `McpCapabilityProvider`, `tools/list`, `get_context`, registry `_SPECIALIST_IDENTITY`, schema/enum handling, schema validation, configuration, persistence owner, migration mechanism, scripts, admin infra, telemetry, tests A–F. Confirmar se já há snapshot/cache/versionamento/repository port no Core ou DÉLIA com legitimidade.
Para cada componente proposto: `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY`, `REUSE_DECISION=REUSE|EXTEND|NEW`, owner, fonte, consumers, contrato, implementation, test. `TO_INVENTORY` impede NEW.
**A pesquisa é bounded:** inventário de paths necessários; sem redescobrir o projeto completo. Não presumir PostgreSQL, JSONB, driver, tabelas, migrations ou acesso à infraestrutura.

## 2. Boundary experimental e contratos antes do código

Reutilizar abstração existente de discovery por provider/adapter quando possível. Variante A e B devem fornecer **a mesma projeção semântica contratual** (identidade de owner+tool, descrição, schema completo sob demanda, contract hash, provenance/scope); diferença só na obtenção do snapshot. Planner nunca conhece backend, tabela, cache, script, owner específico ou mecanismo de sync.
Separar: (i) catálogo owner-factual capturado; (ii) projeção compacta para seleção semântica; (iii) schema completo para arggen; (iv) verificação live/authoritative no momento de invoke. Nunca reduzir cobertura factual da variante A artificialmente.
Definir contrato com: owner/consumers, request/response, errors tipados, AuthZ, idempotência de sync, limits, compatibilidade, audit, observabilidade, postconditions, version pin. Se API HTTP nova for absolutamente necessária, OpenAPI+operationId estável; preferir script e boundaries existentes.
**Estado de contrato:** snapshot `DRAFT/CAPTURED/VALIDATED/ACTIVE/RETIRED/INVALID`; nenhuma ativação de `INVALID`. Version monotônica por owner+scope com hash de conteúdo canonizado. Mudança na contagem de tools sozinha é insuficiente.

## 3. Modelo JSON versionado / armazenamento

**Primeiro reuse existing storage legítimo.** Se PostgreSQL/JSONB já for oficial para a DÉLIA, avaliar tabela transacional isolada; se não, escolher mecanismo autorizado comprovado em inventário e registrar ADR de storage. Não criar migrations especulativas.
Representação lógica mínima (nomes físicos definidos pelo contrato real):
- `owner_id`, `tenant/scope` autorizado sem material sensível, `schema_version`, `catalog_version`, `contract_hash_sha256`, `source_mcp_protocol_version`, `captured_at`, `validated_at`, `activated_at`, `status`, `tool_count`, `normalized_tools_json`, `change_summary`, `source_provenance`, `actor/service identity audit ref`.
- Tool: nome estável, descrição autorizada, `inputSchema`, `outputSchema` quando publicado, annotations/metadata estritamente necessários, provenance, per-tool hash; manter `required`, `enum`, nested schema, nullability, types e descrições sem perda.
- Scopes: se `tools/list` variar por identidade/tenant/permissão, snapshot **não global** por padrão; ou capturar interseção pública segura; proibir metadata de outro principal. Credenciais e JWT nunca persistidos.
- Comparação determinística do JSON sem depender de ordem de keys; preservar diferenças semanticamente relevantes (inclusive description e tool name). Controlar duplicidades, concorrência, transação e ativação atômica; histórico imutável e rollback de ponteiro ativo.
- Invariantes: um ACTIVE por owner+scope, hash verificável, idempotência de apply sem diff, mudanças incompatíveis requerem validação, limpeza/retention governada.

## 4. CLI de sincronização manual (único controle administrativo nesta fase)

Criar ou estender script **somente após inventory**. Interface alvo (ajustar convenção existente sem alterar semântica): 
```bash
python scripts/mcp_catalog_sync.py --owner mcp:caio --dry-run
python scripts/mcp_catalog_sync.py --owner mcp:caio --apply
python scripts/mcp_catalog_sync.py --owner mcp:caio --history
python scripts/mcp_catalog_sync.py --owner mcp:caio --activate-version <version>
python scripts/mcp_catalog_sync.py --owner mcp:caio --verify
```
- `dry-run` é default seguro: discovery live autenticado via owner boundary, canonicalization, diff por tool (added/removed/schema/description changed), efeito e riscos, sem side effects.
- `apply`: autenticação de operador/service e autorização administrativa legítima (não autorização inferida de CLI/JWT); lock por owner+scope; capture → validate → persist immutable snapshot → atomic activate → audit; idempotent.
- `history/verify`: hash/provenance/status; `activate-version`: rollback explícito com verificação de legitimidade/compatibilidade e audit; sem reativar unsafe contract sem live verification.
- Falhas: 401/403, timeout/503, JSON inválido, zero tool inesperado, schema inválido, edição concorrente, incompatibilidade, DB down, duplicate apply, partial failure → fail closed e anterior ACTIVE intacto.
- Scripts não salvam tokens, PII, secrets ou resultados empresariais em logs, snapshots ou Git. Não executar writes de Domain APIs.

## 5. Experimento A/B sem contaminação

- Composição única: `LIVE` vs `SNAPSHOT_EXPERIMENT`; flags em ambiente de testes, auditable mode+active_version/hash, rollback instantâneo por config. Nenhum path snapshot público em produção.
- A sempre usa discovery live; B lê somente snapshot validado na etapa de seleção/arggen (não pede tools/list repetido para preparar contexto), **mas** o invoke preserva a verificação live e os gates existentes. Instrumentar separadamente discovery calls de planejamento vs validação live.
- Evitar diferença artificial de prompt ou modelo; oferecer semântica/escopo equivalente a A e B, sem restringir A intencionalmente. Se quiser testar *compact semantic projection*, tratar como fator separado 2×2 (live/snapshot × full/compact), nunca confundir impacto de persistência com redução de tokens de prompt.
- Conjunto: Documento 211 (28 questões intactas), bateria 89 quando compatível/sem duplicar desnecessariamente, casos held-out novos com semânticas similares e não triviais, negativos/segurança, cenários de mudança do schema (tools add/remove/rename; enum/required/description change), stale, owner unavailable, authz revocation, scope mismatch, rollback.
- Mesmos modelos/quantizações/temperatura, identity, owners enabled, budgets, prompts, infraestrutura e dados comparáveis; alternar ordem AB/BA e repetir (mínimo 3 vezes/caso quando custeável; se não, justificativa e status `INCONCLUSIVE` para significância). Executar com SHA/config capturados, avaliação cega contra oráculos congelados. Emparelhar runs por cenário e registrar variância.
- Medidas: owner-selection accuracy, capability-selection accuracy, schema-valid args, invoke success, evidence relevance, subobjective coverage, Business Outcome, security violations, latency p50/p95, discovery time, prompt tokens, output tokens, tool calls, cache hit/miss/version mismatch, resync duration, stale-block rate.
- Não aceitar `want_owner` ou 200 como Outcome. Reportar clusters com primeira divergência causal; owner 503 permanece availability, não flag de planner.

## 6. Slices e provas — executar integralmente no escopo autorizado

**E0** Reanchor + inventory gate bounded + baseline congelada A (SHA, configuração, contratos, latência/tokens, 211/heldout). Deliverable: matriz de equivalentes e decisão storage.
**E1** Contratos e isolamento A/B: teste RED prova A unchanged, B opt-in, fail closed em B sem snapshot; GREEN em composition root; rollback de flag.
**E2** Persistência versionada e migrations autorizadas: JSON/JSONB, canonical hash, immutable versions, active pointer transacional, scopes, retenção; testes CRUD/rollback/concurrency/migration.
**E3** CLI sync: `dry-run/apply/history/verify/activate-version`, contracts live, diff real, auth admin, tests negativos; capturar snapshots de sete MCPs autorizados ou justificar impossibilidade por scope/credenciais (não inventar).
**E4** Leitura e projeção para LLM: seleção de tool semântico da fonte snapshot, schema completo para arggen, exec owner live; tests de igualdade de contracts, sem registry paralelo.
**E5** Segurança/compliance: injections em schema/description untrusted, permissão revogada, tenant isolation, stale owner, rollback, retries e budgets; zero material writes.
**E6** Benchmark pareado A/B + held-out; scripts reproduzíveis e corpus congelado; relatório estatístico por dimensão + evidências literais armazenadas em local protegido.
**E7** Regressão completa, validação de trace/audit, rollback A/B, decisão `KEEP_LIVE|PROMOTE_CANDIDATE|HYBRID_CANDIDATE|INCONCLUSIVE`, docs/ledger, commits/push verificados.
Cada slice: RED→minimal diff→GREEN→E2E→security relevant→integrated regression; não encerrar docs-only. Não implementar UI nesta fase.

## 7. Gates de aceite não delegáveis

G0 Reanchor/authority/ownership/EXISTING_EQUIVALENT comprovados; nenhum drift silencioso.
G1 LIVE default permanece funcional, A/B flag isolada; A regressions 0.
G2 snapshot storage versionamento, hash, atomicidade, tenant/scope, migrations, rollback testados; no secrets.
G3 script admin completo + negative cases; sem side effects em dry-run; somente script permitido.
G4 B consome snapshot para seleção e arggen, não para authority; live AuthZ/owner verificados; stale fail-closed.
G5 A/B reproduzível, modelo e condições comparáveis, controle de fator compactação, todos resultados vinculados ao SHA; respostas e traces completos; Business Outcome separado de tool OK.
G6 Padrão segurança: no unauthorized ACT, tenant leak, metadata injection, secret leakage, stale permission, bypass ou catalog-to-FACT; resultados falsos PASS=0.
G7 testes completos, drift/compatibilidade, alta/baixa de tools, mudança de schema com tool_count fixo, gestão de versão; rollback sem dano.
G8 Documentação, ledger, runbook, diffs, testes, evidências, SHA/main verified. **Somente a coordenação decide adoção em produção.**
NÃO é gate obter melhora artificial. Resultado A/B igual ou pior é dado válido; task experimental completa se todos gates técnicos/metodológicos passam e decisão resulta em `KEEP_LIVE`.

## 8. Execução segura e anti-pauses

Executar no worktree isolado. Proteger commits concorrentes; sem force push; sem deploy produção; sem writes empresariais. Não misturar task S2–S6 em andamento com experimento, nem alterar sua métrica retroativamente.
Resolver defeitos de implementação/harness/ambiente em loop `REPRODUCE→RED→FIX→GREEN→E2E→REGRESSION`; continuar slices sem pedir confirmação rotineira. Se bloqueio de autoridade real, registrar `EXECUTION_DRIFT` e continuar frentes independentes. Sessão física pode terminar; persistir checkpoint factual e retomar, nunca afirmar auto-resume sem suporte.
NÃO refatorar todo planner nem criar novo runtime apenas para testar hipótese. Não depender de LLM para sync, diff ou versionamento (determinísticos).

## 9. Formato obrigatório de relatório

```text
TASK_ID=DELIA-C3-MCP-VERSIONED-CATALOG-ISOLATED-AB-01
BASE_SHA=
FINAL_SHA=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_AND_CP_RQ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
OWNER_AND_STORAGE_AUTHORITY=
LIVE_PATH_UNCHANGED=
EXPERIMENT_FLAG=
SNAPSHOT_STORE=
MIGRATIONS_TEST=
SYNC_CLI_TEST=
SYNC_7_OWNERS_STATUS=
AUTHZ_AND_SCOPE_TEST=
STALE_SCHEMA_TEST=
ROLLBACK_TEST=
AB_CORPUS_SHA_CONFIG=
AB_VALIDITY=
AB_OWNER_CAPABILITY_SELECTION=
AB_ARGS_EVIDENCE_OUTCOME=
AB_LATENCY_TOKENS=
AB_SECURITY_NEGATIVES=
FULL_REGRESSION=
ADOPTION_RECOMMENDATION=KEEP_LIVE|PROMOTE_CANDIDATE|HYBRID_CANDIDATE|INCONCLUSIVE
PRODUCTION_SWITCH=NO
PRODUCTION_DEPLOY=NO
BUSINESS_WRITES=0
TASK_STATUS=COMPLETE|INCOMPLETE|EXECUTION_DRIFT
COORDINATION_VERDICT=PENDING_INDEPENDENT_REVIEW
EVIDENCE_LINKS=
BLOCKERS=
```

## 10. Explicit future phase (NOT IN SCOPE)

UI management of MCP catalog, event/webhook-driven automatic synchronization, scheduler, proactive notifications, self-service approvals, production rollout, ADR final adoption. Future work may build on the scripts and contracts only after a proven A/B outcome, owner signoff and coordination approval.
