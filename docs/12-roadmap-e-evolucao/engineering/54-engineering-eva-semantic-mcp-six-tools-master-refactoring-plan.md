# EVA — Plano Mestre de Refatoração MCP Semântico (6 tools)

**ID:** EVA.MCP.SEMANTIC.R1 · **Estado:** TARGET / PLANNED (plano, não implementação)  
**Owner:** Engenharia / Engineering API / EVA · **Coordenação:** EVA Architecture  
**Fonte de baseline:** documento 53; código real `engineering-api/engineering_app/interface/mcp/{constants.py,server.py,tool_bridge.py}` em `origin/main` no inventário de 29/10/2026.  
**Escopo:** reestruturação da superfície MCP, contratos semânticos, catálogo extensível, orquestração, execução governada, conhecimento técnico, migração e homologação.  
**Não autoriza:** grants, provisionamento administrativo, deploy produtivo, habilitação de ACT produtivo, importação destrutiva, exclusão real de acervo ou mudança de owner.

## 0. Decisão de arquitetura e problema

A EVA expõe hoje 23 tools técnicas (ver doc 53): 1 descoberta, 17 READ, 1 PREPARE e 4 ACT, alinhadas a 23 intenções REST. A paridade DEV foi homologada; ACT produtivo continua sob gate `ENG_EVA_ACT_ENABLED` e OAuth MCP produtivo exige comprovação. O acoplamento crescente entre endpoint/intent e tool não escala para desenhos, roteiros, materiais, BOM, inspeções e futuras funcionalidades do Portal Engenharia.

**Decisão TARGET:** reduzir a superfície pública MCP a **exatamente seis tools semânticas estáveis**:

| Tool | Semântica | Efeitos |
|---|---|---|
| `get_context` | Identidade/contexto de trabalho, entidades e **capacidades disponíveis**, catálogo schema/action e provenance. Contexto não é AuthZ. | READ |
| `read` | Consultar entidades e facts oficiais: busca/detalhe/relacionamentos/timeline/indicadores/exportação quando cabível. | READ |
| `analyze` | Comparar, calcular/interpretar fatos e produzir análise técnica ancorada, com incerteza e provenance. | ANALYSIS, sem persistência |
| `knowledge` | Recuperar guias, normas, especificações e conhecimento de Engenharia **autorizado e versionado**; não substitui fatos do domínio. | READ |
| `execute` | CREATE, UPDATE, associações e workflows não destrutivos; ações de alto impacto (ex. import replace-all/publicação) usam governança reforçada. | ACT controlado |
| `delete` | DELETE/remover associação, com identificação de alvo, impacto e **confirmação explícita vinculada**. | ACT destrutivo |

Os nomes são contratos públicos e não devem proliferar a cada rota nova. Pode existir mais de uma classe interna de operação e múltiplos adapters/handlers atrás de cada tool. A superfície de seis tools não é autorização para aceitar URL, SQL, método HTTP ou nome de handler arbitrário do modelo.

### Comportamento de interação aprovado

- Consultar / analisar / conhecimento: executar imediatamente, dentro das permissões.
- CREATE / UPDATE com intenção inequívoca, payload válido e risco baixo/moderado: executar diretamente após validação e AuthZ live, sem confirmação conversacional redundante.
- Pedidos compostos: resolver plano de dependências e orquestrar ações permitidas na mesma solicitação; não simular transação global sem suporte; reportar resultados parciais, idempotência e compensação.
- DELETE: apresentar alvo e impacto, exigir confirmação humana explícita antes de ACT.
- Importação de substituição total, publicação oficial ou operação equivalente de alto impacto: **mesmo via `execute`**, aplicar confirmação reforçada e gates do owner; `delete` não é o único caminho destrutivo.
- Impedimento/permissão ausente/ambiguidade material: não executar; explicar objetivamente o bloqueio. Não tentar fallback de privilégio, outro endpoint ou credencial.

## 1. Evidência e referências de TÉO/VISTA

**Inventário de tool surfaces consultadas** (não pressupor reuso de código): TÉO possui `get_catalog`, `get_process_context`, `record_read`, `analyze`, famílias `prepare_*_change` e `commit_proposal`; VISTA possui `get_catalog`, `get_playlist_context`, `search_data_routes`, `suggest_change`, `prepare_change`, `commit_proposal`. Esses padrões comprovam **dispatch semântico + catálogo de ações + propostas governadas**, mas não autorizam import runtime dos seus contextos. Inventariar esquemas, políticas, testes e UX de confirmação reais antes de implementar. Extrair só padrões neutros sob owner EVA, sem dependência em internals ou DB de outros produtos.

Fontes da própria EVA: doc 53 e `TOOL_CLASS` em `constants.py`, decorators em `server.py`, `_TOOL_CONTRACT`, `_require_eva_act`, `_require_confirmation`, delegação a use cases em `tool_bridge.py`, OpenAPI de `/v1`, Core/AuthZ, docs 26/28/29, 46–53. Antes de alterar: `git fetch`, HEAD/status, authorities, inventário de consumers, testes do SHA.

## 2. Arquitetura alvo e boundaries

```text
Usuário / Host / ChatGPT Plugin
    → OAuth MCP (Keycloak) → seis semantic tools
    → Semantic Catalog/Dispatcher (Engineering-owned; schemas versionados)
       → Resolver entity + action + contexto + risco
       → Validar argumentos tipados + permissões + limites
       → Application use cases / official Engineering API contracts
           → Core live AuthZ; fact adapters → API DELPI para TOTVS
           → domain NC → Postgres via Engineering API port/adapter
       → outcome/postcondition + audit + provenance
```

- MCP é interface de interoperabilidade, não autoridade. EVP/EVA não é source of truth.
- Keycloak identidade; Core RBAC; Engineering API é owner de regras e writes NC; API DELPI fornece facts TOTVS; owners de Engenharia aprovam técnicos quando necessário.
- Domain/Application independem de MCP, SDK LLM, ORM, HTTP, DB e provider. Separação Ports & Adapters.
- `get_context` não concede autorização: o catálogo pode filtrar por acesso, mas toda operação exige AuthZ live no backend; princípio do menor privilégio.
- Sem DB, integração TOTVS direta ou reutilização do Chat legado via EVA.
- Escopo de usuário humano e principal técnico não são intercambiáveis; tokens não vão em parâmetros das tools, logs, memória ou artefatos.
- Aplicar Abstraction Gate antes de novos registries/engines: dono, consumer, boundary e redução efetiva de coupling; preferir um dispatcher explícito simples a um framework genérico.

## 3. Contrato semântico antes do código

Definir e congelar schema das **seis tools**, compatível com MCP e limites de tamanho de contexto. Proposta inicial, sujeita a validação T1:

- `get_context`: `{topic?, entity?, selected_ref?}` → user/workspace hints, `capability_catalog_version`, available entities/actions, schemas sob demanda, estados `PROVEN|PLANNED|UNAVAILABLE`, ACL hints (nunca AuthZ decisória).
- `read`: `{entity, action, ref?, filters?, pagination?, projection?}`; actions explicitamente permitidas por entidade, e.g. `nonconformity.search|detail|history|tags|indicators|context|export`, `lmp.list|summary|detail|history_events|history_flow|goal_context|department_idd|nc_streak`, `product.structure`, `engineering.home|overview`. Tipos/campos/limites são per-action.
- `analyze`: `{analysis_type, subject_refs, question?, parameters?}` → facts citados, método, cálculo verificável, distinção `OBSERVED|CALCULATED|INFERRED|UNKNOWN`, limites; jamais fabricar desenho, norma ou dado técnico.
- `knowledge`: `{topic, task?, source_refs?, revision?, query?}` → guidance/fonte, versão, alcance, permissão, validade; `NOT_IMPLEMENTED` honesto enquanto corpus/owner/ingestão não existirem.
- `execute`: `{entity, action, target_ref?, payload?, changes?, idempotency_key?, expected_version?, proposal_ref?, phase?}` → CREATE/UPDATE e workflows declarados. Ações simples de baixo risco podem executar diretamente (`phase=act` inferida pela intenção inequívoca); para alto risco, `phase=prepare` retorna proposta e `phase=commit` apenas com proposta vinculada/confirmada. Não aceitar `confirmed=true` do modelo como prova independente para destrutivos.
- `delete`: `{entity, target_ref, proposal_ref?, phase?}`; `prepare` calcula impacto e emite proposta assinada/selada server-side com owner/user/target/diff/version/expiry/nonce/risk; `commit` só aceita a proposta íntegra após confirmação humana verificável; previne replay. Não há exclusão direta sem confirmação.

Regras contratuais comuns:
1. Registry `(entity, action)` explícito, schemas versionados e bindings allowlist para use cases/ports; jamais `method+url`, strings de função, execução dinâmica ou SQL.
2. Erros tipados: `UNAUTHORIZED`, `FORBIDDEN`, `NOT_FOUND`, `VALIDATION_ERROR`, `CONFLICT`, `CONFIRMATION_REQUIRED`, `PROPOSAL_EXPIRED`, `ACT_DISABLED`, `UNAVAILABLE`, `NOT_IMPLEMENTED`, `PARTIAL_OUTCOME`.
3. Resposta uniforme `{action,entity,status,data?,error?,source?,provenance?,revision?,postcondition?,correlation_id?}`; preservar compatibilidade e não vazar PII/segredos.
4. Catálogo é descoberta de operação e schema sob demanda, com páginas/caps para evitar crescimento descontrolado do contexto. Não incluir todos os payload schemas e conteúdo de conhecimento em cada resposta.
5. Idempotência, optimistic lock, limites, budget de operações, timeouts, classificação de risco, auditoria, confirmação e política de rollback/postcondition por operação. Sem auto-commit de propostas de alto risco.
6. As ferramentas públicas semanticamente READ/ANALYZE/KNOWLEDGE têm `readOnlyHint` coerente; `execute`/`delete` são ACT e devem declarar anotações de risco honestas; IMPORT destrutivo dentro de execute exige sinalização no *catálogo de action* além das anotações gerais da tool.

## 4. Mapeamento sem perda das 23 tools atuais

| Atual (doc 53) | Destino | Action semântica |
|---|---|---|
| `get_catalog` | `get_context` | `capabilities` |
| `get_engineering_home`, `get_engineering_overview` | `read` | `engineering.home|overview` |
| `list_lmps`, `get_lmp_summary`, `get_lmp_detail` | `read` | `lmp.list|summary|detail` |
| `get_lmp_history`, `get_lmp_goal_context`, `get_lmp_department_idd`, `get_lmp_nc_streak` | `read` | `lmp.history|goal_context|department_idd|nc_streak` |
| `get_product_structure` | `read` | `product.structure` |
| `search_nonconformities`, `get_nonconformity`, `get_nonconformity_history` | `read` | `nonconformity.search|detail|history` |
| `get_nonconformity_indicators`, `get_nonconformity_tags`, `get_nonconformity_context`, `export_nonconformities` | `read` | `nonconformity.indicators|tags|context|export` |
| `prepare_nonconformity_mutation` | `execute` e `delete` | `phase=prepare`, conforme operação |
| `create_nonconformity`, `update_nonconformity`, `import_nonconformities` | `execute` | `nonconformity.create|update|import` |
| `delete_nonconformity` | `delete` | `nonconformity.delete` |

`analyze` e `knowledge` não são equivalentes triviais a uma rota existente: implementar capacidades reais sustentadas por facts oficiais, cálculos testáveis e corpus autorizado. Onde não houver owner/fonte, catálogo deve marcar `PLANNED`/`NOT_IMPLEMENTED`, nunca improvisar um resultado supostamente canônico.

A paridade é por **intenção + schema + segurança + resultado**, não por contagem de tools. Preservar 23/23 intenções atuais (considerando histórico events/flow como variações), filtros, paginação, export, tags, context, PREPARE/ACT, OAuth, status honestos e auditoria. Validar baseline real no HEAD antes de congelar ledger.

## 5. Extensibilidade longitudinal (desenhos, roteiros, BOM, matérias-primas, intermediários)

Novas funcionalidades oficiais são declaradas como `entity/action/schema/handler/owner/permission/risk/outcome` no registry e catalog, sem criar tool MCP. Exemplos **TARGET, não capacidades atuais**:
- `read(drawings,detail)`, `analyze(drawing,compare_to_bom)`, `analyze(drawing,check_dimensions)`;
- `read(routing,steps)`, `analyze(routing,consistency)`;
- `read(product,bom)`, `read(raw_material,specification)`, `read(intermediate,description)`;
- `knowledge(technical_description,standard)`, `knowledge(inspection,method)`;
- `execute(technical_document,prepare_draft)`, `execute(technical_document,submit_for_review)`.

Todo desenho: `fonte → percepção/extraction → análise → candidato DRAFT → revisão/aprovação → publicação owner`. Sem inferir cotas/tolerâncias/materiais/normas inexistentes. Não conectar entidades de sistemas diferentes sem IDs/contratos/provenance válidos. Knowledge: fontes versionadas, indexação governada, escopo de acesso, atualização/revogação e citações, sem transformar embeddings em SoT.

Gates para adicionar action nova: contrato owner, schema, AuthN/AuthZ, semântica, custo/limites, erros, testes de grounding, generalização, safety, permission boundary, outcome, observabilidade, rollback, compatibilidade. Se nova tool parecer necessária, documentar Exception Gate com necessidade única impossível de modelar pelas seis, owners/consumers e Architecture Decision Required.

## 6. Orquestração sem tool explosion

Um pedido composto pode gerar um plano tipado e temporário de ações do catálogo: dependências explícitas, ordenação, checks antes de writes, idempotency keys por etapa, limites de cardinalidade, escopo de usuário e budget de chamadas. O agente orquestra; Domain APIs confirmam autoridade e resultados. Não criar serviço transacional corporativo ou A2A acoplado sem Abstraction Gate.

Ex.: buscar NC de uma OV, verificar produto, atualizar uma NC inequivocamente identificada e ler histórico: `read → read → execute(update) → read`. Revalidar status/etag e AuthZ em ACT. Para batch parcialmente executado, reportar `PARTIAL_OUTCOME`; não declarar rollback automático sem mecanismo de compensação oficial.

## 7. Modelo de confirmação governada e conflito com ACT atual

**Drift atual:** as 4 ACT do doc 53 exigem `confirmed=true` indiscriminadamente; a política TARGET aprovada determina CREATE/UPDATE diretos quando usuário autoriza claramente, DELETE com confirmação explícita e operações de alto impacto com controle reforçado.

Refatorar:
- `execute(create|update)` simples: exigir intenção de usuário inequívoca, campos completos, AuthZ, idempotência, optimistic locking, auditoria e postcondition. Sem confirmação adicional artificial. Em caso de ambiguidades/perdas massivas/outros riscos, PREPARE/confirmation.
- `delete` e `execute(import_replace_all)`: proposta server-side com `proposal_ref`, hash dos parâmetros/versão/alvo, actor, expiração, impacto, política e confirmação humana vinculada ao conteúdo exibido. A simples asserção `confirmed=true` do LLM não basta. Definir canal comprovável de confirmação (host/OAuth user action), persistência/validade/revogação do handle e nonce; não inventar assinatura criptográfica sem owner/security review.
- O MCP pode continuar com 6 tools usando `phase=prepare|commit` em `execute` e `delete`, com `phase=act` somente para baixo risco. ACT sem aprovação de produção segue fail-closed.
- Confirmar a semântica oficial de IMPORT NC (`ENG_NC_IMPORT_REPLACE_ENABLED=false` em prod documentado) e preservar gates; não habilitar import destrutivo por mudança de interface.

É obrigatória decisão de arquitetura/segurança sobre confirmation binding e auditabilidade antes de enable de DELETE/import ACT produtivos: `ARCHITECTURE_DECISION_REQUIRED`.

## 8. Migração/compatibilidade (sem big bang)

**M0 — Baseline:** congelar inventário atual do doc 53/HEAD, schemas MCP, consumers, testes, plugin manifest, versões, observabilidade, volumes; mapear 23 → 6. `PROVEN` somente fatos auditados.
**M1 — Contratos:** RFC de seis tools, catálogo paginado por entidade/ação, erros, versões, compatibilidade, risk matrix, UX de confirmação e formal gates.
**M2 — Implementar em paralelo (DEV):** adapters semânticos sobre application use cases/ports existentes; ferramentas antigas continuam funcionando; evitar duplicação de regras; tipos e schemas validados.
**M3 — Segurança:** OAuth humano, Core live AuthZ, claims/actor, proposal binding, ACT gates, negatives e isolamento S2S; garantir que catálogo/hints não virem autoridade.
**M4 — Conhecimento e análise:** implementar análises sustentadas por fatos oficiais e guias realmente existentes; registrar gaps/corpus futuro como PLANNED.
**M5 — Homologação comparativa:** para cada intento antigo, chamar nova action e comparar semântica, erros, paginação, autorização, postcondition, auditoria, performance, contexto de tokens; E2E MCP OAuth real com user autorizado e não autorizado; testes de tools reais, não só mocks.
**M6 — Consumidores e depreciação:** atualizar instruções EVA, manifest do plugin, schemas e prompts; se os consumidores conhecidos estiverem migrados e janela/telemetria aprovadas, descontinuar tools antigas **somente em gate separado**. Não declarar 6-only enquanto as legacy ainda forem publicadas.
**M7 — Produção PREPARE:** runbook, flags, smoke READ primeiro, ACT ainda off até autorização, rollback por versão/feature flag, observabilidade por action e incident response.
**M8 — CUTOVER (fora da autorização deste plano):** produção só com owner/ops ACT específico e provas de pré-condições. Remover tools antigas só após métricas e aprovação; reversão segura.

Ideal de compatibilidade: duas surfaces versionadas ou alias temporário; se dual registry expuser 29 nomes, aceitar apenas temporariamente em DEV, sem afirmar redução antes do switch. Não criar contrato em que nome das seis tools mude por entidade.

## 9. Matriz de testes e critérios de qualidade

- Catalog: schema versioning, discovery on-demand, actions não permitidas, paginação, ausência de prompt injection, tamanho bounded.
- 23/23 parity: chamadas READ, history flow/events, filters, sorting, export, tags, context, LMP, produto, detalhes; resultados/erros equivalentes.
- ACT: create/update direto autorizado; conflito etag 409, idempotency replay, read-back, audit actor, no silent full-replace loss.
- Destructive: delete unconfirmed blocked, proposal tampering/expiry/replay/cross-user/cross-target rejected, import replace-all requires gates/dry-run + approved confirmation.
- Security: 401/403, `engineering.manage` alone denied, no permission escalation, Core offline fail-closed, token/audience/scope, service-principal denied, malicious content unable to drive ACT.
- Intelligence: factual provenance, inferences explicit, missing fields, revision mismatch, drawing knowledge unknown, not_invented; privacy/PII.
- Composition: multi-step dependency, partial failure, compensation, budget/timeout and negative cancellation.
- Reliability: concurrent requests, stable public schema, bounded context size, latency baseline, tracing w/o secret, load/response size, no N+1.
- Regression: backend, EVA MCP, Engineering MFE (if touched), legacy, S2S facts, Playwright/OAuth real; final SHA tested.
- Runtime maturity: `TEST_NOT_RUN` and `PENDING` where prod ACT/OAuth unavailable; do not count mocked tests as live outcome.

## 10. Gates de execução e AC

| Gate | Entrega | Exit criterion |
|---|---|---|
| G0 Inventário | autoridade, HEAD/status, 23-tool & API ledger, consumers | PASS sem inventar capabilities |
| G1 Design/contracts | schemas das seis, registry, error envelope, risk/confirmation ADR | aprovado, compatível |
| G2 READ/context | get_context + read com paridade legacy | 100% READ parity |
| G3 ANALYZE/KNOWLEDGE | intelligence grounded e guia real | sem falsos facts/claims |
| G4 EXECUTE/DELETE | create/update direto, proposal sealed delete/high-risk | ACT DEV E2E + negativas |
| G5 Orquestração | multi-action sem side effects indevidos | task outcomes corretos |
| G6 Consumers/cutover plan | plugin/instructions, compat, deprecation | zero quebra conhecida |
| G7 Regression/QA | OAuth DEV real, security, perf, parity | testes finais e SHA |
| G8 Docs/readiness | ledger, runbook, rollback e relatório | CODE_READY_DEV; PROD_PENDING |

**AC transversal:** exatas 6 tools no catálogo semântico versionado; paridade 23/23 intenções; nenhuma perda de autorização; nenhum acesso a DB fora do owner; PUT NC full-replace seguro; import replace-all continua bloqueada sem gate; create/update sem confirmação redundante; delete somente após confirmação humana verificável; múltiplas operações no mesmo pedido; novos módulos Engenharia incorporáveis por novos `entity/action` sem ferramentas MCP novas; documentação atualizada; suite tests/verificação no SHA final. ACT produtivo e depreciação legada exigem ACT separado.

## 11. Execução contínua de Devin (futura missão)

`FETCH → VERIFY HEAD/STATUS → READ AUTHORITIES → INVENTORY → CONTRACT → IMPLEMENT → TEST → REWORK → RETEST → DOCUMENT → COMMIT → RECHECK`.

Permitir G0–G8 técnicos em DEV, com commits por gate. Preservar concorrência e não fazer force-push. Se decisão formal de confirmed-proposal ou new owner bloquear execução, concluir etapas seguras e marcar `ARCHITECTURE_DECISION_REQUIRED`; não contornar. Nunca executar deploy/write/grants prod por esse plano.

Usar estados de fatos `PROVEN|TO_INVENTORY|PLANNED|TARGET` e testes `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`. `EXECUTION_DRIFT` quando baseline mudar.

## 12. Template de relatório

```text
EVA EXECUTION REPORT — EVA.MCP.SEMANTIC.R1
BASE_HEAD:
FINAL_HEAD:
AUTHORITIES:
CURRENT_TOOLS:
TARGET_TOOLS: get_context, read, analyze, knowledge, execute, delete
PARITY_MATRIX:
REGISTRY_AND_SCHEMAS:
TEO_VISTA_REFERENCE:
GATES_G0_G8:
READ_PARITY:
ANALYSIS_GROUNDING:
KNOWLEDGE_SOURCES:
CREATE_UPDATE_DIRECT:
DELETE_CONFIRMATION_PROOF:
HIGH_RISK_IMPORT:
COMPOSITE_ACTIONS:
AUTHZ_OAUTH:
CORE_FAIL_CLOSED:
EVA_ACT_ENABLED_DEV:
EVA_ACT_PROD:
LEGACY_COMPATIBILITY:
CONSUMER_MIGRATION:
TEST_COMMANDS_AND_RESULTS:
TESTED_SHA:
COMMITS:
DOCS_AND_LEDGER:
ARCHITECTURE_DECISION_REQUIRED:
EXECUTION_DRIFT:
RESIDUALS:
NEXT_BOUNDED_STEP:
```

## 13. Dependências e decisões a ratificar

1. Modelo de confirmação de DELETE/alto risco: binding server-side, user gesture verificável, validade, auditoria, revogação. **ADR antes do ACT destrutivo.**
2. Consumer de ChatGPT Plugin e clientes MCP: estratégia de versionamento/switch das tools públicas; sem rompimento.
3. Critérios de fonte de conhecimento: owners de normas/desenhos, indexação, revisions, controle de acesso e retenção, para `knowledge` e `analyze`.
4. Política de operação composta: limites de batch, efeitos parciais e compensação.
5. ACT produtivo: OAuth client prod, `ENG_EVA_ACT_ENABLED`, owner/security e deploy aprovados separadamente.

**Postcondition deste plano:** arquitetura e plano completo registrados; nenhuma alteração de runtime ou declaração falsa de deploy.
