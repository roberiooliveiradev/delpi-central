# ENGINEERING.NC.G0 — Ownership, PostgreSQL CRUD Migration & EVA Capability Parity

**Tipo:** plano vinculante para inventário, decisão e implementação em gates subsequentes; não é autorização para migrar dados, executar writes, fazer cutover ou publicar tools mutáveis.  
**Owner de coordenação:** EVA — Architecture / Coordination. **Owners a confirmar:** Engenharia (domínio NC), owner atual da persistência API DELPI/PostgreSQL, Platform DB/Security, Core RBAC, owner EVA/MCP.  
**Data:** 2026-10-29. **Estado:** PLANNED / ARCHITECTURE_DECISION_REQUIRED para transferência de authority da persistência.  
**Base canônica:** docs 32–45, especialmente doc 33 §8/§15–16, doc 40 §2/§3/§5, doc 41 §4, doc 45; HEAD real a revalidar antes da execução.

## 1. Decisão de produto e objetivo

Não Conformidades (NC) deixa de ser uma aba do Dashboard LMPs e passa a ser funcionalidade independente em **Início → Não Conformidades**, no Portal Engenharia, ao fim de seus gates. O Dashboard de LMPs continua independente, incluindo seu KPI de dias sem NC.

**Arquitetura TARGET:**
- **Portal Engenharia**: listagem, busca, filtros, formulário, edição, detalhe, histórico, exclusão/import/export quando autorizados, e contextualização de produto/OV.
- **Engineering API**: ownership funcional NC; validações, regras, contratos READ/WRITE, auditoria, idempotência e AuthZ Core live. Permissões operacionais exclusivamente `engineering.access`; `engineering.manage` somente configurações administrativas, sem implicação de access.
- **PostgreSQL**: persistência de NC acessada através de repository port/adapter sob ownership aprovado de Engenharia; preferencialmente aproveitar a estrutura física atual mediante governança, isolamento de credenciais e acesso restrito, sem duplicar dados sem necessidade. Nenhuma API de outro bounded context deverá persistir NC após cutover.
- **API DELPI**: facts originados em TOTVS e enriquecimento de formulários (OV, produtos, estruturas/BOM) através do BFF governado; não será caminho CRUD/persistência NC em TARGET.
- **Core/Keycloak**: Core autoridade efetiva RBAC; Keycloak identidade/SSO; MCP, frontend, JWT e token técnico nunca conferem autoridade.
- **EVA**: interpretação governada dos mesmos contratos Engineering API, com evolução pareada por capability e classificação READ/PREPARE/ACT. Sem acesso direto a tabelas, a API DELPI ou autorizações paralelas.

**ATUAL — PROVEN por inventários anteriores, revalidar no HEAD:** `api-delpi` mantém `engineering.lmp_nonconformities` em PostgreSQL, repositório `postgres_lmp_nonconformity_repository.py`, rotas `/engineering/lmps/nonconformities*`; MFE legado `plugins/dashboard-lmps` possui list/detail/form/histórico/import/export e escreve via API DELPI. `engineering-api` já expõe streak READ delegado, não é persistência NC. A API DELPI também integra TOTVS; não presumir que registros NC sejam fatos TOTVS.

## 2. Gate de autoridade: ADR-NC-OWNERSHIP (obrigatório antes de ACT)

A decisão de Coordenação aprova o **TARGET de ownership funcional**, mas a transferência formal de ownership dos dados, grants de banco, migrações físicas e exclusividade de escrita exigem revisão do owner atual, Engenharia e Plataforma. Registrar `ARCHITECTURE_DECISION_REQUIRED` e retornar à Coordenação se aprovação faltante.

O ADR deverá resolver: titular do esquema/tabelas; cluster/banco efetivo em cada ambiente; acesso e credenciais exclusivos; RLS/privileges/triggers se houver; migrations e versionamento; compatibilidade de leitores; estratégia para desligar writers legados; tratamento de dados históricos; backups; rollback; observabilidade; retenção; retenção de trilha auditável; exigências de privacidade; operação em múltiplas instâncias. **Não há autorização implícita para usar conexão administrativa ou grant de outro serviço.**

Decisões a preparar para o owner:
- **Opção B preferencial:** Engine API assume repository port e writes do storage NC existente, com ownership DB explicitamente atribuído e troca governada do writer único; nenhuma mudança física se desnecessária.
- **Opção B com movimentação física:** somente se justificativa operacional demonstrar necessidade; plano de backup, backfill, checksums, rollback e janela.
- **Opção A transitória:** API DELPI permanece owner temporário de READ/WRITE apenas para legado enquanto não houver readiness e autorização de cutover; nunca criar double-write silenciosa.
- Proibir `engineering-api → api-delpi → Postgres NC` como arquitetura permanente; permitir apenas compatibilidade estritamente delimitada e registrada durante transição.

## 3. G0 — Inventário factual obrigatório (READ-only)

Antes de codificar: `git fetch origin`, registrar `HEAD`, `origin/main`, branch, status, concorrentes; ler AGENTS/authorities de DB, auth, APIs, interservice, CI, clean architecture e docs 32–45.

Inventariar **rotas** da API DELPI e callers: GET list/detail/history/streak/problem-tags/export; POST create/import; PUT/PATCH update; DELETE; identificar exatamente contagem, payload, validações, side effects, paginação, ordenação, filtros, export, erros e HTTP status. Inventariar 10 endpoints NC e as rotas auxiliares de produto conforme doc 40; números definitivos vêm do HEAD.

Inventariar **banco**: esquema `engineering`, tabelas NC e associadas history/tags, chaves, índices, FK, constraints, triggers, migrations, sequence, funções, transações, backups; RLS e principal técnico; proveniência de `OV`/produto e regras de hydrate.

Inventariar **regras e dados**: status, severidade, tags de problema, observações, prazos, revisão, histórico/auditoria, validações por operação, delete policy, import e idempotência; timestamps/locale/timezone; autor de mudança e requisitos de autorização.

Inventariar **consumidores**: MFE Dashboard LMPs legado, NC legacy direct links, LMP streak, dashboards, SI, DÉLIA/EVA, TV, scripts, integrações externas. Telemetria de 30–60 dias quando autorizada; ausente = `TO_INVENTORY`, não inventar ausência.

Inventariar **permissões legadas e grants**: `api-delpi.access`, `dashboard-lmps.view`, `dashboard-lmps.nc.write`; o achado de `api-delpi.access` implicar write no legado exige hardening coordenado e testes de não regressão; nenhuma dessas permissões será usada em novos endpoints NC.

## 4. Contratos TARGET Engineering API — contrato antes de código

Propor contratos versionados, usando naming e padrões reais da Engineering API (IDs candidatos):
- E-NC-01: listagem com filtros/paginação/ordenação/search.
- E-NC-02: detalhe por ID; distinção 404/403.
- E-NC-03: histórico de mudanças com ator, timestamp, fonte, campos autorizados.
- E-NC-04: streak (dias sem NC) e agregados READ, mantendo compatibilidade do KPI LMP.
- E-NC-05: catálogo de problem-tags e opções oficiais.
- E-NC-06: exportação READ governada.
- E-NC-07: CREATE.
- E-NC-08: UPDATE.
- E-NC-09: DELETE/soft-delete conforme semântica comprovada.
- E-NC-10: IMPORT com idempotência e política explícita de erro parcial/transações.
- E-NC-11: enriquecimento de formulário por OV/produto/BOM, **somente por gateway/adapter oficial via API DELPI facts**, sem acesso direto do browser e sem transferir SoT TOTVS.

Para cada contrato documentar: owner, consumer, request/response e schema, erros e status, AuthN/AuthZ, field/row-level rights, dados sensíveis, limites, paginação, concurrency/version/ETag quando aplicável, idempotency, rate limit, transaction/postcondition, observability, compatibility/versioning, provenance e rollout flag. Convenção de endpoint definitiva será decidida antes do código, evitando publicar caminhos apenas propostos como implementados.

**Segurança:** auth humano Keycloak; Core `engineering.access` live em backend para READ e legitimate WRITEs, sem `engineering.manage` implícita; não dar poderes mutáveis a identidades técnicas ou EVA por default. Validação estrita, negative 401/403/404/409/422, forbidden source, Core down fail-closed. API DELPI S2S somente para facts/lookup; `engineering.*` nunca em seus guards.

## 5. Sequência de implementação governada — não executar tudo em G0

| Gate | Entrega | Critério para avançar |
|---|---|---|
| **NC.G0** | Inventário source→consumer, modelo de dados, AD R formal, contrato completo, riscos e plano de migração; mapa EVA por capacidade | Owner dos dados e authority decididos ou bloqueios explícitos; **nenhum código CRUD ou mudança DB** |
| **NC.G1** | Domain/Application + ports/adapter PostgreSQL sob owner aprovado, migrações não destrutivas se necessárias, contracts READ; EVA READ em lockstep | Shadow READ, 401/403 e paridade lista/detail/history/streak; sem mudança de writer |
| **NC.G2** | Contratos WRITE e use cases + tests; estratégia writer único, transações, audit, import/idempotência, rollback; EVA PREPARE no limite aprovado | Escrita só em ambiente autorizado, negativas e concorrência; sem produção ou dupla escrita |
| **NC.G3** | UI nativa independente `Início → Não Conformidades`: list/form/detail/history/export, enriquecimento TOTVS pelo BFF; hooks/adapters novos | Paridade funcional e visual em navegador, temas/responsividade; EVA READ/PREPARE coerentes |
| **NC.G4** | E2E homologação com corpus e autorização real, integração EVA MCP, task outcome, testes de writes e auditoria | Owners aprovam; nenhum bypass; test suites/rollback verificáveis |
| **NC.G5** | Cutover explícito (writers + consumidores) por PREPARE/ACT separado, rollback, monitoramento | Exclusividade writer e grants efetivos comprovados, registros não divergentes |
| **NC.G6** | Deprecar rotas CRUD legadas e permission codes só após evidência de zero consumidores | Ledger, métricas e owner aprovam; sem remoção prematura |

**Nota:** nomenclatura de gates acima é PROPOSTA; poderá ser refinada pela Coordenação. Nenhum gate autoriza o seguinte automaticamente. Separar deploy do cutover. O documento 45 (retirada de abas LMPs) segue independente e não autoriza ativar NC.

## 6. EVA — parity-by-capability obrigatória

A cada adição/alteração na Engineering API, produzir linha no ledger **API capability → EVA capability → maturity → AuthZ → verification → gate**. EVA é uma especialista governada, não SoT e não mapeamento automático 1:1 de endpoints REST para tools.

| Engineering API | EVA TARGET | Categoria | Regra |
|---|---|---|---|
| NC list/search | `search_nonconformities` | READ | Respeitar escopo/filtragem efetiva da Core e limites |
| NC detail | `get_nonconformity` | READ | Usar resposta oficial, provenance e PII minimizada |
| NC history | `get_nonconformity_history` | READ | Não fabricar causas/revisões; evidenciar incerteza |
| Streak/tags | `get_nonconformity_indicators` / `get_nonconformity_tags` | READ | Não recalcular indicador oficial |
| Produto/OV | `get_nonconformity_context` | READ | Enriquecer via Engineering API, não chamar DB/TOTVS diretamente |
| Create/update/import | Preparar candidato com diff, validação e confirmação humana | PREPARE | Sem write indireto, não assumir permission de acesso como aprovação humana |
| Create/update/delete/import ACT | Ferramenta mutável somente após contrato específico e aprovação | ACT / PENDING | Live AuthZ, confirmação explícita, ownership, idempotência, postcondition, auditoria e revogação/rollback |

- Toda capability nova da API exige **avaliação EVA na mesma entrega** e atualização do catálogo/tool specs e documentação. Quando READ estiver efetivamente disponível e autorizado, implementar e testar tool MCP se a exposição for adequada; caso contrário justificar `PENDING`, sem inventar capability.
- As operações de escrita da EVA não serão habilitadas automaticamente pela existência de rota WRITE; `PREPARE` é distinto de `ACT`. Para exclusão/importação exigir análise de risco e confirmação humana reforçada conforme contrato.
- Tool bridge do Engineering API é superfície MCP in-process: nunca source of truth, escopo ampliado ou permissão derivada de prompt/provider.
- Testes obrigatórios conforme risco: catalog / schema / grounding / permission boundaries (usuário com/sem access, manage-only, Core down, service identity) / hallucination / task outcome / negative write / auditable postcondition / legacy isolation.
- Usar classificações de fatos `PROVEN | TO_INVENTORY | PLANNED | TARGET` e execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Capabilities não comprovadas não entram no catálogo disponível.

## 7. Compatibilidade, dados e rollback

Não remover nem modificar rotas de legado `api-delpi` até writer handoff e zero consumers verificados; não duplicar inserts/updates em dois services. Plano de dados precisa incluir snapshot/backup, comparação por PK e hist, controle de contagem/checksum, freeze de writer legado na janela de troca, replay/delta se necessário, troca de grants, rollback com garantia de não perder writes e reconciliação. Não sugerir rollback simplista para alternância de writer após novos writes sem estratégia de compensação.

Streak de NC já é consumido por cards LMP — nova fonte só substitui após paridade por período e fronteira de data, incluindo divergências DEV vs PROD documentadas. Metas/IDD não mudam de owner. Não remover funcionalidade do MFE legado antes de prova de paridade.

## 8. Critérios de aceite G0

- NC-G0-01: Reancoragem/authorities.
- NC-G0-02: Mapa completo de rotas READ/WRITE + todos os consumers conhecidos.
- NC-G0-03: Modelo PostgreSQL e autoridade atual comprovados.
- NC-G0-04: Regras, statuses, history, tags, import/export, validações inventariados.
- NC-G0-05: Plano ADR de ownership DB submetido aos owners.
- NC-G0-06: Contratos E-NC-* com AuthN/AuthZ, erros, limites e postcondition definidos.
- NC-G0-07: Plano de isolamento de writer, dados e rollback verificado.
- NC-G0-08: Compatibilidade do legado e do KPI streak preservada.
- NC-G0-09: Lookup TOTVS restrito ao BFF da API DELPI.
- NC-G0-10: `engineering.access/manage` confinadas à Engineering API; Core RBAC efetiva.
- NC-G0-11: Ledger API↔EVA completo com READ/PREPARE/ACT e estados honestos.
- NC-G0-12: Plano de testes negativos, paridade e cenários de concorrência.
- NC-G0-13: Nenhum runtime write, migração DB, deploy ou cutover no G0.
- NC-G0-14: Documentação/evidências no SHA final e relatório.
- NC-G0-15: Drift/architecture decisions explicitamente reportados.

**Entregáveis:** próximo documento de evidências sequencial de NC.G0; ADR (proposto ou aprovado com prova de owner), matriz source→consumer, schema/contratos, ledger EVA e roadmap refinado. Distinguir `PASS` de `PENDING` quando authority ou evidência real faltarem.

## 9. Relatório obrigatório Devin

```text
EVA EXECUTION REPORT
TASK: ENGINEERING.NC.G0 — Ownership, PostgreSQL CRUD & EVA Parity
BASE_HEAD:
FINAL_HEAD:
AUTHORITIES_READ:
FILES_INSPECTED:
FILES_CHANGED:
NC_ROUTES_READ:
NC_ROUTES_WRITE:
NC_POSTGRES_SCHEMA:
CURRENT_DATA_OWNER:
PROPOSED_DATA_OWNER:
ADR_NC_OWNERSHIP:
DB_ACCESS_MODEL:
LEGACY_CONSUMERS:
LEGACY_PERMISSION_RISK:
RULES_AND_VALIDATION:
WRITE_SINGLE_OWNER_PLAN:
MIGRATION_AND_ROLLBACK:
BFF_TOTVS_ENRICHMENT:
ENGINEERING_API_CONTRACTS:
CORE_AUTHZ:
EVA_CAPABILITY_LEDGER:
EVA_READ_TOOLS:
EVA_PREPARE_ACT_GATES:
TEST_PLAN:
TEST_COMMANDS:
TEST_RESULTS:
TESTED_SHA:
DOCUMENT_PATH:
COMMIT_SHA:
AC_RESULTS:
EXECUTION_DRIFT:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
NEXT_BOUNDED_STEP:
```

## 10. Instrução executiva para Devin

Executar **somente G0**: reancorar; verificar authorities, source e consumers; criar ADR e contratos; inventariar schema e writers; formular estratégia de writer único e cutover; mapear e versionar capability EVA com testes e gates; documentar e publicar diff exclusivamente documental salvo autorização explícita adicional. NÃO implementar CRUD, alterar banco, criar tools mutáveis, alterar grants, provisionar ambientes ou antecipar G1. Voltar à Coordenação para `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | INCONCLUSIVE`. A orientação TARGET não substitui decisão formal dos owners da persistência.
