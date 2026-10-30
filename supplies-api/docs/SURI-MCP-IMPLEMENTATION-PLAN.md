# SURI — Plano completo de implementação do MCP de Suprimentos

> **Identidade:** **SURI — Suprimentos Unificados, Resultados e Inteligência**. Especialista em Suprimentos da Minha DELPI.  
> **Status:** `PLANNED / IMPLEMENTATION_NOT_AUTHORIZED_BY_DOCUMENT` — 2026-10-29. O pedido autoriza elaborar este plano, **não** executar automaticamente as etapas.  
> **Repo:** `roberiooliveiradev/delpi-central`. HEAD remoto observado para planejamento: `71d11ef46875cbebf9a00d69a42d974ef488e6a0`. Git status local: não observável pelo conector GitHub. Antes de executar cada etapa, refazer baseline e comparar HEAD/working tree.  
> **Escopo:** novo canal MCP/ChatGPT sobre `supplies-api` e suas capacidades publicadas; sem substituir MFE, sem migrar Flask, sem criar owner paralelo, sem desbloquear writes ERP.  
> **Plan authority:** subordinado à instrução oficial, regras .cursor, ADRs, contratos, código atual e testes. Este plano **não** modifica `docs/12-roadmap-e-evolucao/supplies/IMPLEMENTATION-PLAN.md` nem a ordem page-by-page do Portal.

## 0. Decisão de produto e sucesso final

**Missão:** permitir que usuários autenticados consultem, compreendam, analisem, acompanhem e executem, em linguagem natural e quando autorizados, as capacidades reais do Portal Suprimentos. Três camadas: **ASSIST** (auxílio operacional), **KNOW** (informação/conhecimento com fontes) e **INSIGHT** (inteligência, análise e recomendações explicáveis).

**Objetivo final:** paridade governada entre capacidades semanticamente adequadas do Portal e tools SURI, respeitando autorização e estado real do BFF. Paridade não significa gerar uma tool por endpoint ou conceder todas as funcionalidades indiscriminadamente.

**Prova final:** matriz capability-by-capability com `MFE/BFF implemented`, `SURI exposed`, `AuthZ validated`, `source/knowledge evidence`, `tests`, `runtime`, `postcondition` e riscos. Não anunciar “paridade completa” enquanto houver lacuna sem classificação e autorização.

## 1. Authorities e insumos obrigatórios

Ordem: `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md` → regras `.cursor` globais (`development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`) → especializadas (`plan-construction`, `plan-execution`, `test-and-commit`, `openai-plugin-mcp-integration`, `platform-security-identity-authorization`, `platform-api-contracts-integration`, `platform-architecture-boundaries`, `platform-quality-testing`, `platform-delivery-runtime-operations`, `ai-external-tools-security`) → ADRs e contratos → código/testes → docs → este plano.

Consultar `docs/12-roadmap-e-evolucao/supplies/{README.md,IMPLEMENTATION-PLAN.md,API-ROUTES.md,INTEGRACOES.md,PERFIS-E-PERMISSOES.md,HELP-AND-ONBOARDING.md}`, ADRs aplicáveis; `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md`; `supplies-api/docs/SURI-MCP-PRODUCT-ARCHITECTURE.md`, `SURI-MCP-REFERENCE-INVENTORY-20261027.md` e `SURI-MCP-GITHUB-CODE-INVENTORY-20261027.md`.

Ler código real: `shared/delpi_mcp/{transport,identity,resource_contract,tool_metadata,errors}.py`; `delpi_auth`; `transformometro-api/tm_app/interface/mcp/*`, `tv-dashboard-api/tv_app/interface/mcp/*`, `controllership-finance-api/controllership_finance_app/{interface/mcp/*,application/clara/*}`, `api-delpi/app/interface/mcp/*`; `supplies-api/app/{composition,interfaces/http,application,infrastructure}`, configuração/deploy/testes, MFE consumers.

**Drift inicial:** `README.md` de Suprimentos contém status E11 mais atual que o topo de `IMPLEMENTATION-PLAN.md`. Não corrigir silenciosamente; registrar o desacordo de baseline e consultar evidência da etapa no HEAD. Drifts históricos `/me/routes` e manifest v2 devem ser tratados conforme Core vigente.

## 2. Evidências já existentes versus lacunas

**PROVEN por leitura do GitHub anterior:** os quatro servidores `MCPServer` Python (TÉO/VISTA/CLARA/DAVI); o pacote `shared/delpi_mcp`; bridge de identidade/contrato OAuth do MCP; CLARA `corpus_ingestion.py`; `supplies-api` Flask com blueprints `me`, `analytics`, `purchase_requests`, `purchase_orders`, `deliveries`, `inventory`, `safety_stock`, `market_intelligence`, `suppliers`, `supplier_creation`, `supplier_enrichment`, `users`. **PROVEN quanto a código, não quanto a runtime atual.**

**TO_INVENTORY:** árvore completa dos quatro MCPs e infra, `delpi_auth` real, schemas/hardening, status e testes atuais, uso de Flask/ASGI (co-local ou sidecar), endpoints reais e cada autorização do BFF, client Keycloak MCP de Suprimentos, corpus permitido, consentimento, rollback e ambiente produtivo.

**Gates herdados:** API responsável por regras TOTVS = `api-delpi`; authn Keycloak; permissions efetivas Core; `supplies-api` BFF e authz server-side; UX `plugins/supplies`; meta SI em `strategic-indicators-api`; `purchase-requests-api` preserva C1→C2→paridade→C3. **Writes ERP OFF enquanto gates não liberarem.**

## 3. Ledger de requisitos — rastreabilidade

| RQ | Requisito | Estado no plano | Etapa | Teste/aceite |
|---|---|---|---|---|
| SURI-RQ-01 | Nome, sigla, branding, português | ATENDIDO_NO_PLANO | S1/S2/S8 | AC-01 |
| SURI-RQ-02 | OAuth por usuário, resource binding, Core AuthZ e scopes | ATENDIDO_NO_PLANO | S0/S1/S2/S3 | AC-02 |
| SURI-RQ-03 | MCP de owner correto, sem bypass/duplicação | ATENDIDO_NO_PLANO | S0/S1/S2 | AC-03 |
| SURI-RQ-04 | Descoberta governada de capabilities | ATENDIDO_NO_PLANO | S1/S3 | AC-04 |
| SURI-RQ-05 | Consulta operacional e paridade por capacidade | ATENDIDO_NO_PLANO | S3/S7 | AC-05 |
| SURI-RQ-06 | Ajuda e conhecimento versionados/citados | ATENDIDO_NO_PLANO | S4 | AC-06 |
| SURI-RQ-07 | Inteligência com dados/fórmulas homologados | ATENDIDO_NO_PLANO | S5 | AC-07 |
| SURI-RQ-08 | Mutações permitidas, proposta selada, consentimento, verificação | ATENDIDO_NO_PLANO | S6 | AC-08 |
| SURI-RQ-09 | Segurança de dados, prompt injection e resiliência | ATENDIDO_NO_PLANO | S2-S8 | AC-09 |
| SURI-RQ-10 | Observabilidade, rate limit e troubleshooting | ATENDIDO_NO_PLANO | S2/S8 | AC-10 |
| SURI-RQ-11 | Onboarding ChatGPT e produção com rollback | ATENDIDO_NO_PLANO | S8 | AC-11 |
| SURI-RQ-12 | Paridade mensurável e verify-final | ATENDIDO_NO_PLANO | S7/S9 | AC-12 |
| SURI-RQ-13 | Não regressão do Portal e Help sincronizada | HERDADO_POR_SOLUCAO_TRANSVERSAL | Todas | AC-13 |
| SURI-RQ-14 | Sem novas permissions mecânicas e sem mudanças ERP indevidas | HERDADO_POR_SOLUCAO_TRANSVERSAL | Todas | AC-14 |

**AC gerais:** AC-01 metadados/instructions conferidos; AC-02 PKCE/aud/scope e identidade pessoal, 401/403/tenant/unit/resource/sibling/negative; AC-03 dependências sem acesso direto a banco de outro contexto e sem migração Flask; AC-04 catálogo somente operações homologadas, não executor HTTP/SQL genérico; AC-05 respostas vinculadas a dados reais, paginação/freshness; AC-06 fonte/versão/citation_locator/evidence_classification/access scope; AC-07 rastreabilidade de cálculo e separação FACT/RECOMMENDATION; AC-08 prepare não grava, consentimento confiável, idempotência, replay/concurrency, read-back outcome; AC-09 injeção em documentos e outputs não comanda tools, sem vazamento; AC-10 trace e logs sanitizados; AC-11 smoke ChatGPT real, 401/403/200 e rollback demonstrado; AC-12 matriz ≥ capacidades autorizadas no corte acordado e residual explicável; AC-13 testes BFF/MFE/regressão e guia Ajuda; AC-14 permission Core reutilizada quando adequada e gates ERP preservados.

## 4. Arquitetura: hipóteses concorrentes e decisão diferida

```text
ChatGPT Plugin SURI
  → Keycloak OAuth/OIDC por usuário (Authorization Code + PKCE)
  → protected resource MCP de Suprimentos [URL TARGET, não publicada]
  → MCP adapter / tool bridge [sem business authority]
  → supplies-api: use cases + AuthZ server-side Core-first
  → Core | api-delpi | purchase-requests-api | strategic-indicators-api | owners autorizados
```

### Alternativas obrigatórias em S0

**A — MCP ASGI co-local ao serviço Flask**, compondo ASGI/Wsgi boundary ou processo integrado: reuso de serviços da própria `supplies-api`, sem HTTP loop; exige comprovar isolamento, ciclo de vida, deployment Gunicorn e compatibilidade framework. **Não migrar a BFF de Flask.**

**B — MCP adapter isolado, transport-only, chamando somente contratos HTTP `supplies-api`** com credencial vinculada ao usuário: mantém Flask intocada e boundary explícita; exige provar user delegation, AuthZ, retries, tempos, infra adicional, observabilidade e que não surge um segundo owner de domínio.

**Gate de decisão ARCH-01:** comparar A/B com evidência e escolher a menor solução correta segundo `.cursor`; se ambas falharem restrições de AuthZ ou custo/coupling, interromper como `EXECUTION_DRIFT`. Não usar preferência estética para congelar escolha.

**Invariantes:** JWT não é permissions source; `mcp:tools` scope de transporte ≠ permissão de negócio; `aud` do MCP é exata e isolada; `capability AND unit_scope AND resource_scope/ownership AND business_rule`; fail-closed. Sem tool SQL/HTTP proxy, endpoint arbitrário, import cross-context, espelhamento TOTVS, duplicação de metas SI ou permission por tool.

## 5. Grafo executável — uma etapa por gate

```text
S0 Inventário e ARCH-01 (READ only)
 ↓
S1 Contract freeze: identity/tool semantics/API/knowledge
 ↓
S2 Infra MCP + OAuth/AuthZ (sem capacidades de negócio mutáveis)
 ↓
S3 READ vertical slice (um fluxo de baixo risco)
 ↓
S4 KNOW corpus/guia governados
 ↓
S5 INSIGHT primeira análise homologada
 ↓
S6 ACT governado (somente capability com write permitido e gate individual)
 ↓
S7 Expansão por capabilities + paridade mensurável
 ↓
S8 Onboarding / observabilidade / deployment
 ↓
S9 Verify-final + operação assistida / documentação
```

**Independentemente do grafo, cada capacidade nova exige contract freeze e gate próprio.** A fase S6 pode permanecer bloqueada sem impedir um lançamento READ/KNOW/INSIGHT explicitamente reduzido. Nenhuma fase futura equivale a aprovação automática.

### S0 — Reconciliação e decisão arquitetural

**TASK:** inventariar no HEAD o padrão MCP, infra, BFF e autorização; resolver A/B.  
**OWNER:** Architecture / Integrations / Security, com Cursor.  
**ALLOWED:** leitura, relatórios, decisões/ADR propostas; sem código produtivo.  
**EVIDENCE:** HEAD/status, arquivos com SHA, diagrama de sequência OAuth, schemas, consumers, classificador de capabilities (`BFF_PROVEN`, `MFE_PROVEN`, `TO_INVENTORY`, `BLOCKED_WRITE`), inventário de `supplies-api` e MFE, matriz A/B com risco e decisão.  
**TESTS:** revisão de testes existentes, mapeamento 401/403 e negativos; `TEST_NOT_RUN` permitido em S0.  
**GATE S0:** ARCH-01 assinado, owners fechados, sem conflito de autoridade, RQ/AC priorizados. **STOP:** AuthZ/identidade impossível de preservar, Flask mudaria, producer/owner incerto → EXECUTION_DRIFT.

### S1 — Congelar contratos MCP e políticas

**TASK:** produzir contrato de tool/resource/knowledge, OAuth, schema de resposta/erros, limits, metadados e policies.  
**OWNER:** `supplies-api` + owner IAM/infra.  
**CONTRACT:** decidir `resource_url`, `client_id`, scopes, protected-resource metadata, `WWW-Authenticate`, OpenAI securitySchemes, taxonomy `DISCOVERY/READ/ANALYSIS/PREPARE/ACT`, versionamento, capability descriptors, `structuredContent`, códigos 401/403/404/409/422/429/502/503/504, truncation/pagination, freshness. Names técnicos em inglês e apresentação em PT-BR.  
**SECURITY:** sem credentials estáticas de serviço para representar usuário. Não permitir tool por payload arbitrário, SQL ou host escolhido pelo modelo.  
**GATE S1:** contrato/ADR ratificados e teste de schema especificado; `CONTRACT_FROZEN`. **STOP:** conflito entre metadata e AuthZ real.

### S2 — Infraestrutura transport + identidade

**TASK:** implementar o menor adapter MCP escolhido no S0, biblioteca `shared/delpi_mcp` reutilizada quando compatível, com Keycloak/OAuth end-user e metadata protegida.  
**OWNER:** owner da BFF + plataforma IAM/infra nos próprios recursos.  
**TESTS:** init/list_tools, 401 token ausente/inválido, 403 audience errada, scope isolado, expiração, host/origin, DNS rebinding, route /mcp sem redirect perigoso, context leakage, request id, log masking, negativa cross-user, regressão Flask.  
**GATE S2:** testes unit/integration PASS, authn validada; nenhum dado de negócio acessado antes de authorization. **STOP:** bypass JWT↔Core, falha de isolamento ou secrets em output.

### S3 — Primeiro fluxo READ + catálogo vivo

**TASK:** selecionar **uma** capability read-only já PROVEN na `supplies-api` com escopo simples, implementar tool sem transformar endpoint em proxy genérico; catálogo discovery indica limites, tipo, comportamento.  
**CONTRACT:** inputs tipados em inglês, unidade explícita ou default autorizada provada, paginação, resultado com `as_of`/source e estado partial/error, tool metadata; orientação “o que consigo fazer” baseada no catálogo.  
**TESTS:** caso feliz com usuário permitido, outra unidade/sibling, sem permission, filtro fora escopo, recurso inexistente, downstream timeout, dados vazios/partial, campo sensível redigido, BFF route integration, performance dentro budget definido.  
**GATE S3:** resposta ChatGPT/tool associada ao resultado real da BFF com positive/sibling/negative; smoke MCP autenticado em ambiente controlado. **STOP:** 200 sem AuthZ/completion ou tool sobre rota inexistente.

### S4 — Conhecimento governado / KNOW

**TASK:** definir corpus SURI (Ajuda, glossário, procedimentos e docs canônicos permitidos); inventário explicitamente autorizado; ingestão e recuperação versionadas com `source_id`, SHA/hash, `citation_locator`, `evidence_classification`, audiência e `published_at`.  
**OWNER:** conteúdo do Portal + BFF, com validadores de processo para regras; não usar banco da CLARA.  
**CONTRACT:** `get_product_guide`, `search_supplies_knowledge`, `get_knowledge_item`, `list_knowledge_sources` são **nomes candidatos**, sujeitos ao S1. O índice não pode prometer conteúdo não autorizado; corpus publicado é uma superfície de recuperação, não authority.  
**TESTS:** publicação idempotente, supersede, revogação, source missing fail, prompt injection em documentos, acesso negativo, citações verificáveis, pergunta sem fonte → UNKNOWN, conteúdo de outra unidade oculto.  
**GATE S4:** exemplos end-to-end com proveniência e Help sincronizada; coverage do corpus documentada e limitações explícitas.

### S5 — Inteligência explicável / INSIGHT

**TASK:** selecionar uma análise relevante e determinística (por exemplo, resumo de SCs pendentes/atrasos ou indicadores de entrega), somente após fonte e fórmula homologadas; produzir FACT/CALCULATED/INFERRED/RECOMMENDATION com contexto.  
**OWNER:** regras no owner de dado; `supplies-api` composição; MCP apenas projeção conversacional.  
**TESTS:** reprodutibilidade, filtros/unidade, dado stale/partial, fonte ausente, cálculo de período, precisão/rounding, evitar alucinação de meta, recomendações não mutam recursos.  
**GATE S5:** análise auditável e validada por responsável funcional; sem promoção de hipótese a fato.

### S6 — Mutações governadas / ACT (gate separado por capability)

**TASK:** inventariar escrita já permitida na BFF e sua pós-condição; implementar `prepare_governed_operation` + `commit_proposal` ou semântica equivalente do S1, sem criar backend writer paralelo.  
**PREPARE:** resolve owner, capability/unidade/recurso, preconditions, diff, efeito, risco, expiração e fingerprint/actor binding; não persiste efeito de negócio. **CONFIRM:** consentimento humano verificável quando material; texto de chat por si só não comprova consentimento para operação sensível. **ACT:** revalida Core/AuthZ/estado, idempotency key, stale/replay/concorrência, registra audit, executa pelo use case canônico, faz read-back, devolve VERIFIED/FAILED/UNKNOWN.  
**TESTS:** PREPARE sem write, alterações entre prepare/act, cross-user, cross-unit, replay/duplicidade, cancelamento, consentimento ausente, resultado inconclusivo, side effect no owner correto, rollback quando possível.  
**GATE S6:** somente a capability aprovada pode virar ACT; fornecedor ERP write continua bloqueado até gate separado do owner. **STOP:** qualquer write que burle o gate atual.

### S7 — Expansão capability-by-capability e paridade

**TASK:** mapear cada jornada implementada: SC → PC → entregas → inventário/ESTSEG → fornecedor → análise, priorizando valor e risco. Não gerar tool por endpoint.  
**LEDGER obrigatório:** `capability_id`, intenção, BFF route/use case, owner, permission efetiva, unidade/ownership, tipo READ/ANALYSIS/ACT, parâmetros, resposta, errors, knowledge references, tests, deploy SHA, runtime gate e status.  
**GATE por capability:** PROVEN somente quando BFF, MCP e testes positivos/irmãos/negativos e pós-condição/resposta real forem comprovados. Features planejadas, bloqueadas ou indisponíveis permanecem `PLANNED`/`BLOCKED` na matriz.  
**Saída S7:** relatório de paridade com numerador/denominador explícitos e exceções. Sem métricas inventadas.

### S8 — Onboarding, produção, governança e observabilidade

**TASK:** configurar cliente Keycloak dedicado, protected resource, gateway TLS e deployment segundo runbook, register/install no ChatGPT, nome/descrição “SURI — Suprimentos Unificados, Resultados e Inteligência”; documentação de operações, FAQ/Help e runbook incident/rollback.  
**TESTS:** ambiente real provado (host, compose/container, Keycloak, gateway, bundle/server SHA), login end-user, consentimento, reconnect, list_tools, execução positiva/403/401, cross-audience, rate limit, revogação de access, latência, timeout, logs sem token, rollback/redeploy.  
**GATE S8:** smoke autenticado pelo conector ChatGPT, evidência de origem produtiva e rollback disponível; se smoke inacessível, `INCONCLUSIVE` — nunca PASS inferido.

### S9 — Verify-final e handoff operacional

**TASK:** confrontar meta inicial de auxílio operacional + KNOW + INSIGHT + paridade autorizada com prova runtime; revisar documento, catálogo, evidências e SHAs.  
**EVIDENCE:** `BASE HEAD`, `FINAL HEAD`, `GIT STATUS`, `FILES INSPECTED/CHANGED`, `CONTRACT IMPACT`, `SECURITY CHECKS`, `TESTS`, `RQ/AC COVERAGE`, `RESIDUAL SEARCH`, `POSTCONDITION`, `UNRESOLVED`.  
**DECISION GPT:** `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. **PASS** só com evidence aplicável.

## 6. Dependências e gates transversais

- **Core / IAM:** audience e scopes do recurso MCP, usuário real, permissions efetivas, unidades, audit de plataforma.
- **BFF supplies-api:** única composição do produto, authorization e próprios estados. Mantém Flask.
- **api-delpi:** TOTVS/SQL e regras Protheus; `purchase-requests-api`: owner C1/C2 SC; `strategic-indicators-api`: metas. MCP nunca acessa esses serviços fora do BFF.
- **Frontend/Help:** conteúdo de Ajuda acompanha cada função user-facing; MCP é canal alternativo, não prova de UI funcional.
- **Knowledge:** políticas de acesso aos documentos, fonte autorizada e ciclo de atualização. Não ingerir o repositório indiscriminadamente.
- **IA:** recomendações nunca executam operações automaticamente; dados externos são untrusted content.

### Decisões ainda abertas que impedem implementação imediata

D-01 arquitetura ASGI/Flask (A/B); D-02 identidade/OAuth client/resource URL real; D-03 catálogo inicial e primeira capability READ; D-04 autorização e versionamento do corpus; D-05 política de consentimento para mutações; D-06 release/rollback e ambiente. Marcar `TO_INVENTORY` até resolução por código e owner. Não adicionar endpoint/perm ou migration por suposição.

## 7. Artefatos/entregáveis esperados por fase

| Gate | Entregável persistido no Git | Evidência mínima |
|---|---|---|
| S0 | relatório HEAD/auth/arquitetura, matriz de paridade inicial e ADR A/B | paths/SHAs/producers/consumers |
| S1 | contract freeze tool/OpenAPI-MCP, versionamento e tabela de errors | revisão owners e schemas |
| S2 | adapter + tests + infra/env sanitize | gates authn/authz 401/403 e isolamentos |
| S3 | READ tool e contracts/tests | 200/empty/partial/403/downstream |
| S4 | corpus manifest/pipeline/knowledge tools | source+hash+locator+revogação |
| S5 | análise homologada + evidência | rastreabilidade de cálculos/hipóteses |
| S6 | proposal/consent/ACT por capability | prepare non-write + read-back |
| S7 | capability ledger + paridade e regressões | cobertura declarada com gaps |
| S8 | onboarding/runbook/deploy evidence | runtime ChatGPT real + rollback |
| S9 | acceptance/evidence/report com SHAs | verify-final do objetivo |

## 8. Brief padrão para execução no Cursor

Para **cada** subetapa, abrir tarefa isolada com campos preenchidos: `TASK, GOAL, PRODUCT STEP, RQ/AC, AUTHORITIES, OWNER, CURRENT_STATE, EVIDENCE_REQUIRED, ALLOWED_SCOPE, FORBIDDEN_SCOPE, CONTRACTS, SECURITY, ACCEPTANCE, TESTS, STOP_CONDITION`. Rebase em HEAD + git status, sem misturar alterações alheias. Rodar testes proporcionais ao diff, verificar positive/sibling/negative e residual search, documentar resultado e commit/SHA.

Modelo de entrega do Cursor: `BASE HEAD, FINAL HEAD, STATUS, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES INSPECTED/CHANGED, CONTRACT IMPACT, TESTS, SECURITY CHECKS, RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION/OUTCOME, UNRESOLVED, NEXT STEP`.

## 9. SURI.S0 — primeiro prompt executável (apenas inventário)

**TASK:** completar inventário SURI no HEAD real e produzir decisão arquitetural A/B, sem código de produto.  
**GOAL:** decidir integração MCP com `supplies-api` Flask e congelar o primeiro recorte READ, com evidência de autenticação/permissions.  
**AUTHORITIES:** seção 1 deste plano, `.cursor/rules/plan-construction.mdc`, `openai-plugin-mcp-integration.mdc`, padrões globais, ADRs de Suprimentos.  
**OWNER:** Architecture, BFF, Core/IAM e Infra nos respectivos contratos.  
**ALLOWED:** inspeção read-only, testes existentes sem side effect e documentos em branch isolada se permitido.  
**FORBIDDEN:** implementar tools, mutações, permissions, migrations, infra/Keycloak, deploy ou mudança no Portal.  
**EVIDENCE_REQUIRED:** HEAD/status, tabela de `supplies-api` routes + use cases + AuthZ + positive/negative tests + consumers; interfaces MCP/ASGI/Flask e alternativas com trade-off, campos OAuth; proposta da primeira capability segura.  
**ACCEPTANCE:** ARCH-01 decidido por evidência, owner/responsabilidade e próxima receita S1 pronta, gaps e drifts expostos.  
**STOP_CONDITION:** owner ou permission inválido, Flask migration, SURI → api-delpi direta, alegação de PASS sem runtime.

**Veredito do plano:** `PLAN_READY_FOR_S0_INVENTORY` (somente etapa de investigação); `IMPLEMENTATION_GATE = PENDING` até ARCH-01 + contract freeze. Não avançar S1–S9 automaticamente.


## 10. Decisão do Product Owner — paridade CRUD completa (2026-10-29)

**Decisão de produto aprovada:** a SURI é uma **interface operacional de CRUD completo**, isto é, tem como TARGET permitir ao usuário realizar por ChatGPT **todas as ações que esse mesmo usuário pode efetivamente executar no Portal Suprimentos**, usando as capacidades autorizadas da `supplies-api`. Não é um chatbot somente READ. Inclui `CREATE`, `READ`, `UPDATE`, `DELETE` e operações semânticas de workflow (aprovar, rejeitar, cancelar, encaminhar, reconciliar etc.) **quando realmente disponíveis e autorizadas**.

**Paridade é por capacidade efetiva do usuário, não por endpoint genérico ou tabela.** Uma operação só entra em `MCP_PROVEN` quando: (a) contrato BFF e owner existem; (b) UI/Portal expõe a ação para aquele perfil, conforme recorte de paridade; (c) `supplies-api` revalida Core effective permissions + unidade + ownership/recurso + regra de negócio; (d) MCP faz PREPARE/ACT/CONFIRM quando aplicável, com read-back; (e) testes positivos, irmãos, negativos e runtime correspondente foram aprovados. `view-all` não expande unidade. Proibição de nova permissão por tool, botão, rota ou verbo.

**Impacto no planejamento:**
- S0 deve entregar **matriz integral de CRUD e workflows** de todas as páginas/capacidades implementadas, com `capability_id`, `verb`, `UI action`, `BFF route/use_case`, `owner`, `effective_permission`, `unit/resource scope`, `business_rule`, `gate`, `tool plan`, `tests`. Não reduzir inventário a primeira fatia READ.
- S1 define catálogo completo de capacidades e política de confirmação por risco, **sem criar tools CRUD mecânicas**. Cada tool/ação representa intenção semântica e reutiliza BFF.
- S2 preserva plataforma/AuthZ. S3 READ é **incremento inicial técnico**, não limitação de escopo final.
- **S6 deixa de ser opcional no objetivo final**: implementação de `CREATE/UPDATE/DELETE` e workflows autorizados passa a ser requisito obrigatório de aceite da SURI completa. S6 pode ter vários gates menores por tipo de efeito/owner; **nunca** liberar ação ERP ainda bloqueada ou inventar caso de uso inexistente.
- S7 e S9 somente declaram **CRUD_PARITY_PASS** se cada capacidade autorizada e implementada no Portal no corte de referência estiver `PASS`/comprovação MCP correspondente, com exceções explícitas para ações intrinsecamente não conversacionais ou sem contrato, validadas pelo PO. Ausência de paridade → `ACCEPT_WITH_RESIDUAL` ou `INCONCLUSIVE`, nunca “CRUD completo entregue”.
- Conhecimento (S4) e inteligência (S5) permanecem camadas obrigatórias e distintas de execução de operações.

**RQ adicional:** `SURI-RQ-15` — paridade CRUD e workflows ponta a ponta. **AC-15:** matriz de todas as ações atuais do Portal com cobertura por verbo/intenção, permissão efetiva e unit/resource scope; testes de autorização e verificação de efeitos; avaliação quantitativa de cobertura/pendências; nenhuma ferramenta consegue executar algo proibido no Portal ou fora do gate. **Estado:** `ATENDIDO_NO_PLANO` por S0/S1/S6/S7/S9; execução `PLANNED`.

**Invariante de exceção:** o objetivo “tudo que o usuário pode fazer” **não** suspende travas do próprio Portal, APIs, Core, ERP, alçadas, confirmação humana ou escopo material de owners. Sem mutação quando o backend não a suporta ou o usuário não está autorizado. Metadados de ferramenta, prompt, token OAuth e confirmação do ChatGPT não são fontes de permissão.
