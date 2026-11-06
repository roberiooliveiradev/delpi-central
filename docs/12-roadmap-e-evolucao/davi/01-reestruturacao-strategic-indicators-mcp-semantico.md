# DAVI V2 — Plano mestre de evolução do MCP semântico e integração de fontes

> **Status:** PRODUCT_DIRECTION_ACCEPTED / IMPLEMENTATION_PENDING. Revisão consolidada em 2026-11-06.
> **Documento único de execução/decisão desta iniciativa.** Atualizar este arquivo nas próximas fases em vez de criar planos paralelos; histórico recuperável por Git.
> **Direção corrigida:** DAVI **permanece no contexto técnico `api-delpi`** e no MCP/resource atuais. Prioridade 1 = padronizar as tools semânticas sem regressão. Prioridade 2 = permitir consumo governado de Strategic Indicators, quando houver contratos e segurança aprovados. **Não transferir o DAVI para Strategic Indicators nem criar container, MCP ou BFF SQL novo nesta fase.**
> **Authority:** `docs/12-roadmap-e-evolucao/davi/README.md`, regras `.cursor`, contratos dos owners, Core API/governança, evidências runtime. Documento de plano não é prova de deploy e não autoriza implementação antes dos gates.
> **Snapshot:** repositório/documentação consultados em 2026-11-06; HEAD local, working tree, code-path e SHA de deploy ainda exigem validação no Cursor antes de código.

## 1. Decisões congeladas nesta revisão

1. DAVI continua como especialista em dados/informações DELPI, com seu módulo/adapter MCP atualmente hospedado em `api-delpi`; **não migrar código ou domínio para API Strategic Indicators**.
2. Manter, por enquanto, `mcp-api-delpi`, `END_USER_ACCOUNT`, OAuth Authorization Code + PKCE S256 e `https://minhadelpi.com.br/apps/api-delpi/mcp`. Sem renomear client, resource ou ingress em produção por organização.
3. Refatorar a **surface MCP** seguindo invariantes reais de MCPs irmãos: `get_context`, `read`, `knowledge` prioritárias, `analyze` depois, `execute` e `delete` apenas por capabilities ACT aprovadas. Não é obrigatório publicar seis tools sem semântica funcional.
4. Preservar a operação atual do DAVI para usuários existentes, suas consultas, allowlists, candidate tokens, SQL SELECT canônico, end-user identity, context budget, provenance e backend AuthZ.
5. Strategic Indicators é **futura fonte / bounded context**; DAVI poderá consumir capabilities autorizadas por contrato estável, sem import de internals nem acesso direto ao banco da API vizinha.
6. **Core API permanece responsável pela governança de acesso aos aplicativos e permissões da plataforma**. Ter acesso ao DAVI **não concede** acesso a Strategic Indicators. A API/owner de Indicadores Estratégicos deve exigir o contexto/permissões efetivas da Core API, além das regras de negócio pertinentes ao owner, em cada consulta ou alteração. Sem autorização efetiva para o aplicativo/escopo correspondente, resultado é **deny/fail-closed**, inclusive para READ, knowledge sensível, PREPARE e ACT.
7. **Sem segundo RBAC local DAVI**: MCP metadata, tool discovery, OAuth scopes, Agent instructions, claims isoladas, frontend ou Memory não autorizam negócio. A avaliação efetiva ocorre no boundary canônico do backend por usuário e recurso; o desenho de propagação/validação cross-API continua TO_INVENTORY.
8. Ajuste de metas/CRUD de Indicadores Estratégicos = TARGET posterior, em capabilities específicas, com PREPARE/ACT, AuthZ, policy, idempotência, OCC quando aplicável, auditoria e postcondition. Não habilitar executor de escrita genérico.
9. Container DAVI próprio, mudança de Keycloak client ou hosting, segundo MCP, mudança de domínio físico, nova BFF SQL: **DEFERRED**. Só reabrir mediante evidência de isolamento, escalabilidade, ownership ou operação e ADR própria.
10. Manter **este arquivo** como plano mestre. Evidências técnicas podem permanecer nos runbooks canônicos de seus donos, mas decisões, fases, gaps e aceite desta iniciativa devem ser atualizados aqui, não espalhados por novos roadmaps.

## 2. Modelo de autoridade e arquitetura

```text
Workspace Agent DAVI
  -> App / user OAuth -> MCP DAVI (continua hospedado em api-delpi)
  -> semantic capability selection + bounded adapter
       |-> API DELPI canonical use cases / policies
       |     -> authoritative AuthZ + operational sources
       |-> FUTURE stable Strategic Indicators API contract
             -> Core API platform app/permission governance (canonical)
             -> Strategic Indicators owner business AuthZ/rules
             -> authoritative indicator and target data
```

**Atenção:** o diagrama expressa responsabilidade, não uma ordem HTTP necessariamente sequencial. Inventariar se a API de Indicadores utiliza Core resolver, middleware, claims canônicas ou outro mecanismo oficial; não duplicar a verificação na camada DAVI e não confiar apenas numa consulta inicial de permissões. **Core governa acesso da plataforma; o owner de domínio executa sua AuthZ final de negócio**. Checagens devem acontecer na operação efetiva, não apenas em `get_context`.

Exemplo negativo obrigatório: usuário A possui acesso ao DAVI, mas não ao aplicativo Strategic Indicators. Se ele solicitar KPI/meta via DAVI, o backend deverá negar qualquer leitura, alteração ou inferência de valor protegido. Os READs da API DELPI que o ator já tem direito de acessar não são automaticamente revogados por essa negativa. Usuário B autorizado a indicadores só vê o escopo efetivamente permitido (filial, área, indicador, ação, conforme contrato do owner).

## 3. Baseline conhecido e lacunas

| Elemento | Evidência / status |
|---|---|
| DAVI MCP atual hospedado em `api-delpi`, resource e client atuais | PROVEN documental, runtime recheck PENDING |
| Tools atuais `discover_delpi_information` e `execute_delpi_information` | PROVEN provider discovery desta sessão e documentação |
| `search_products` atrás do broker, não tool dedicada | PROVEN documental |
| Broker READ, HMAC candidate token, allowlists e projections | PROVEN documental; código/deploy atual TO_INVENTORY |
| README descreve allowlist v30, 94 elegíveis e índice live 97 | Snapshot documental; reconciliar source e provider |
| `execute_readonly_sql` em `POST /data/sql` via broker e validador canônico | PROVEN documental; não criar novo BFF/SQL executor |
| Layering drift `Application → Composition Root` | RESOLVED documental (`DAVI-ARCH-RUNTIME-001`); regressão recheck pendente |
| Strategic Indicators: owner, contratos, permissões Core e resolvers | TO_INVENTORY; **integração não implementada por este plano** |
| Schema detalhado e diferenças das tools semânticas dos outros MCPs | TO_INVENTORY; nomes/descrições descobertos nesta sessão |
| Segundo usuário / negative business AuthZ, rate policy, rollout amplo | PENDING conforme documentação; revalidar |
| Nova interface DAVI, conexão cross-API e writes | TARGET / TEST_NOT_RUN |

A documentação mais atual do repo prevalece sobre snapshots antigos anexados ao Project para retratar source; **runtime só se prova em runtime/provider**.

## 4. Inventário das tools dos MCPs irmãos — provider discovery de 06/11/2026

| MCP | get_context | read | analyze | knowledge | execute | delete | extra | total |
|---|---|---|---|---|---|---|---|---|
| CAIO | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| CLARA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| EVA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| SURI | SIM | SIM | SIM | SIM | SIM | NAO | — | 5 |
| TÉO | SIM | SIM | SIM | SIM | SIM | SIM | `helpdesk_upload_attachment` | 7 |
| VISTA | SIM | SIM | SIM | SIM | SIM | SIM | — | 6 |
| DAVI | NAO | NAO | NAO | NAO | NAO | NAO | `discover_delpi_information`, `execute_delpi_information` | 2 |

Esta matriz prova **somente nomes e descrições anunciados ao ChatGPT nesta sessão**, não uso funcional nem implantação de cada ação. Ausência de tool física não prova ausência da capacidade subjacente.

Padrões observados:
- `get_context`: contexto, catálogo, entidade/ação, versão, schema on demand; discovery nunca é AuthZ.
- `read`: READ por entidade e ação fechadas, filtros, identificação e paginação allowlisted; source e owner AuthZ.
- `analyze`: análises tipadas com evidência, provenance e distinção fato/cálculo/inferência/recomendação; sem side effect.
- `knowledge`: guias, corpus/itens versionados e, onde existente, `search|get|sources`; não substitui fonte operacional atual.
- `execute`: ações de escrita governadas; políticas de PREPARE/ACT, consentimento e replay **diferem entre owners**, portanto não copiar mecanicamente.
- `delete`: destruição separada em cinco MCPs, geralmente proposta selada e confirmação segura.
- TÉO usa tool dedicada de upload por binding especializado: seis nomes comuns **não** impõem interface rígida.

**A investigar em código:** input/output schemas, envelopes, errors, pagination, contracts, permission checks, provider compatibility, taxas e limites, versioning e observabilidade de cada family.

## 5. Tool surface alvo DAVI (por ondas)

| Wave | Tool | Responsabilidade e gate |
|---|---|---|
| W1 | `get_context` | Descoberta limitada do catálogo e schemas sem conceder permissão; disponibilidades reais, por ator, sem expor detalhes protegidos indevidamente |
| W1 | `read` | Consultas semânticas autorizadas; **preservar regras do broker atual** (candidate token e allowlists, SQL SELECT via backend, field projections, paging/completeness, no arbitrary SQL/HTTP) |
| W1 | `knowledge` | Orientação/metodologia governada com owner, versão, fonte, classificação, provenance e tratamento anti-injection; knowledge não é dado operacional live |
| W2 | `analyze` | Análises específicas e reprodutíveis quando houver caso, owner e contrato; sem SQL livre disfarçado |
| W3+ | `execute` | ACT específico e autorizado, inicialmente somente após capability aprovada; PREPARE != ACT |
| W3+ | `delete` | Exclusões destrutivas específicas e raras, com confirmação verificável e authoritative postcondition |

Não registrar `execute/delete` vazios por aparência de padronização. Nome de tool não é permission nem capability. `read` não pode executar SQL mutável nem permitir bypass de seus fluxos internos. `get_context` pode substituir a descoberta externa para o modelo, mas a escolha do candidato técnico e a validação de execução não podem ser simplesmente removidas.

## 6. Sequência de implementação controlada

### Fase 0 — Rebaseline e inventário técnico (PRÓXIMA, READ-ONLY)

- Cursor: `git fetch origin`; `git rev-parse HEAD`; `git rev-parse origin/main`; `git status --short`; `git branch --show-current`, deployed SHA/fingerprint quando acessível.
- Ler README DAVI, `.cursor` arquitetura, security, contracts, MCP, testing e context budget; runbook `api-delpi/docs/integrations/openai-plugin-mcp.md`.
- Inventariar código das duas tools DAVI: rota, schemas, HMAC candidate tokens, allowlist, projections, SQL SELECT, throttling, intelligence/knowledge, consumers, constraints e testes.
- Inspecionar código/docs dos MCPs CAIO, CLARA, EVA, SURI, TÉO e VISTA; comparar contratos, não só nomes.
- Mapear golden prompts/casos reais e baseline de latência, compatibilidade, erros e isolamento de usuários.
- Entregar `DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001` com evidência, opções para W1, impacto em contrato e risco. **Não implementar runtime.**

**Exit:** architecture review + spec W1 aceitos, source/owner/consumers identificados. Se premissa invalidada, `EXECUTION_DRIFT`.

### Fase 1 — Contratos semânticos W1 e UX de transição

- Desenhar `get_context`, `read`, `knowledge` com schema mínimo, erros tipados, atores, bounds, output, provenance e segurança.
- Definir se `read` faz resolução/discovery interna do catálogo atual, usa tokens bound ou envelope equivalente; nunca bypass.
- Classificar o conhecimento existente (persona/directives, docs, data domain, provider prompt); atribuir owner e freshness.
- Definir testes de golden queries, eval de seleção de tools, contexto e não regressão.
- Manter `discover_delpi_information` e `execute_delpi_information` durante piloto; se coexistência causar ambiguidade, validar switchover versionado com rollback e consumer proof.
- Mudanças pequenas por contrato/teste, sem alterar OAuth/client/resource, SQL owner ou backend AuthZ.

**Exit:** tool surface W1 validada localmente e no provider, com resultados comparáveis e usuários autorizados/negativos; deprecar legacy apenas se consumer impact aprovado.

### Fase 2 — Análises semânticas

- Inventariar quais análises possuem consumidores e contrato real.
- Incorporar `analyze` com provas de amostragem/completude, cálculo, métricas, escopo e rotulagem de incerteza.
- Evitar promover cálculos de negócio do owner para DAVI.

**Exit:** análise específica aceita; não exigir publicação da tool sem capability.

### Fase 3 — Strategic Indicators como nova source (FUTURO)

- Ratificar necessidades, owner humano/técnico, source of truth, API stable contract, consumers, field allowlist, freshness, classificação e budgets.
- Inventariar Core API: app access, permission resolver, vínculo entre usuário, escopo e capability, como Strategic Indicators aplica Core governance e sua própria business AuthZ.
- **Teste negativo inegociável:** usuário autenticado autorizado no DAVI mas SEM acesso a Strategic Indicators obtém deny em `read`, `knowledge` protegida, `analyze`, PREPARE e ACT relativos a indicadores. Deny em outras combinações de escopo e ações também.
- Escolher integração por HTTP/contrato estável ou mecanismo oficial aprovado; nunca importar domain/application de Strategic Indicators para `api-delpi` nem acessar banco direto.
- Validar propagação da identidade end-user, audience/delegation, fail-closed, proteção contra confused deputy e cross-user privilege inheritance.
- Integrar somente capabilities READ ratificadas; preservar consultas DELPI existentes.

**Exit:** positive e negative AuthZ e provider calls comprovados para fonte Strategic Indicators, com proveniência e sem regressão.

### Fase 4 — PREPARE / ACT e alterações de metas (FUTURO, GATE INDEPENDENTE)

- Ratificar individualmente cada ação (ex.: ajustar meta), sem CRUD genérico, com authority owner, payload, permission e escopo da Core API e backend.
- `PREPARE`: preview/diff, verificação de target/version e policy, sem persistir.
- `ACT`: authenticated user, Core platform permission + owner final business AuthZ, policy/consent verificável, idempotência, OCC quando aplicável, audit/correlation e authoritative postcondition.
- `delete` somente se owner suportar política destrutiva explícita e confirmação confiável.
- Testes positivos/negativos por usuário e ação, bypass, replay, staleness, conflito de versão e rollback.

**Exit:** cada capability ACT aceita individualmente. `2xx` ou tool discovery não provam negócio.

### Fase 5 — Avaliar extração física, novos MCPs e container (DEFERRED)

Somente se evidência comprovar benefício real de deployment/escala/isolamento/ownership. Não mover DAVI do `api-delpi` por mera nomenclatura. Qualquer novo MCP resource, OAuth client, audiences, callback e plugin exigirá ADR, migração, live evidence, pilot e rollback; não é parte desta iniciativa atual.

## 7. Sequência de dependências

```text
F0 inventário
 -> F1 W1 semantic tools (get_context/read/knowledge) + regression
 -> F2 analyze por caso concreto
 -> F3 Strategic Indicators READ via contratos + Core AuthZ
 -> F4 ACT metas por capability governada
 -> F5 container/MCP/keycloak re-evaluation somente se justificado
```

F2 e F3 podem ser ajustadas na ordem após review; F3 requer foundation de segurança, não necessariamente todas as análises. Sempre diff pequeno, deploy controlado e evidência.

## 8. Guardrails e acceptance gates

- **Business access:** usuário com acesso ao DAVI não herda acesso a Strategic Indicators. Core API governa acesso/app; backend do owner revalida business AuthZ final. Sem permissões efetivas: no protected data, no target value inference, no write.
- **Identity:** end-user token e resource binding; não usar service account para user-parity, nem confiar na existência da tool em `tools/list`.
- **Bounded exposure:** no generic SQL/HTTP/expose-all; SQL READ atual apenas por use case canônico e SqlValidator; fields/projections allowlisted e paginação/completeness explícitas.
- **Compatibility:** clientes produtivos, consumers, schemas e golden queries; rollout paralelo quando cabível, migração com rollback, sem drop abrupto do broker.
- **Knowledge:** guidance jamais autoridade, fonte live ou direito de acesso; proteger contra prompt injection.
- **Observability/security:** audit, rate policy, error handling fail-closed, redaction, no secrets.
- **Ladder:** source → local tests → public HTTP → OAuth discovery/user connection → MCP initialize/tools/list → provider discovery → authenticated call → field allowlist → negative business AuthZ (incl. Core app access) → Agent preview → deploy SHA → postcondition se ACT.
- Classificações: `PROVEN | TO_INVENTORY | PLANNED | TARGET`; execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`; premissa invalidada `EXECUTION_DRIFT`.

## 9. Governança e documentação compacta

Este é o **único plano evolutivo principal**. A cada onda atualizar aqui: decisões, owners, fonte, contratos, checks, status, bloqueios, evidência/SHAs, mudanças de prioridade e próxima fase. Referenciar runbooks e contratos canônicos, não duplicá-los integralmente; handoff/evidence report de execução podem residir no fluxo Cursor/GitHub conforme necessário, mas **não produzir novos roadmaps paralelos**.

- GPT Architecture / Coordination: owner/boundary decisions, briefs, review/acceptance.
- Cursor: code inventory, minimal diff, testing, residual search e evidence report.
- Core API: authority de acesso/plataforma, app permissions e resolução canônica, quando aplicável.
- Strategic Indicators: authoritative indicator/target data, business use cases e final domain policy.
- API DELPI: authoritative operational sources/use cases, inclusive SQL SELECT.
- Security/Testing/Operations: OAuth/cross-API, negative tests, deployment/provenance, release.

**Não abrir nova frente cross-cutting sem voltar a Architecture / Coordination.**

## 10. Próximo brief — DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001

**SCOPE:** READ-ONLY INVENTORY, nenhuma implementação.

**RQ-1:** revalidar HEAD/working tree e deployed SHA, lendo `.cursor` e as fontes canônicas.

**RQ-2:** inventariar schemas exatos `get_context/read/knowledge/analyze/execute/delete` de CAIO, CLARA, EVA, SURI, TÉO, VISTA; mapear semelhanças e diferenças justificadas de inputs, outputs, status, boundaries e auth.

**RQ-3:** mapear implementação `discover_delpi_information → candidate_token → execute_delpi_information`, catálogo, SQL read-only, intelligence, allowlist, consumidores e tests.

**RQ-4:** produzir spec proposta de W1 sem bypass, com estratégia de coexistência/cutover e matriz de golden queries/negative tests; NÃO codificar.

**RQ-5:** listar risco de integração futura Strategic Indicators via Core API (sem implementá-la), identificando os pontos de backend AuthZ e informação ainda TO_INVENTORY.

**RETURN:** BASE HEAD, FINAL HEAD, branch, working tree, files inspected, source/owner/contracts map, contract impact, tests (ou TEST_NOT_RUN), deploy/provider evidence, gaps, drift, recomendação de próximo menor diff.

**STOP:** conflito de owner, permissão ou autoridade; registrar `EXECUTION_DRIFT` e remeter à coordenação.

## 11. Critérios de sucesso (TARGET)

- DAVI segue atendendo usuários atuais sem regressão.
- Tools semânticas padronizadas com capabilities governadas e descoberta/uso comprovados.
- SQL READ existente preservado sem execução irrestrita.
- Strategic Indicators integrada futuramente somente para usuários autorizados no aplicativo e no escopo da operação, com Core API + domain backend AuthZ.
- Writes futuros usam PREPARE/ACT e pós-condição verificável, sem CRUD genérico.
- Sem migração física involuntária, sem duplicação de auth/owner e com evidências persistentes de cada onda.


## 12. Inventário de código — GitHub main, 2026-11-06 (DAVI-V2-SEMANTIC-TOOLS-INVENTORY-001)

> **Escopo desta passagem:** leitura estática do `main` via GitHub e comparação de interfaces MCP de CAIO, CLARA, EVA, SURI e TÉO. Não executamos testes, não coletamos deployed SHA, não auditamos a working tree local e não alteramos runtime. `main` consultado inicialmente em `c6ba5b457039c79b0beaf7f8d2d32a9956701f33`; confirmar SHA final antes de qualquer execução. Inventário técnico PARCIAL por escopo do código inspecionado, não certificação completa de cada API.

### 12.1 Mapa do DAVI comprovado por código

- `api-delpi/app/interface/mcp/server.py`: `ApiDelpiMCPServer`, `list_tools()`, `call_tool()`, `create_mcp_server()`; registro apenas de `discover_delpi_information` e `execute_delpi_information` em operação normal. Ferramenta experimental de transporte documental pode ser registrada por flag isolada: avaliar como impacto da invariante de duas tools.
- `api-delpi/app/interface/mcp/schemas.py`: Pydantic `extra="forbid"` para requests; `DiscoverDelpiInformationInput(query, top_k<=10)`; `ExecuteDelpiInformationInput(candidate_token, arguments)`; envelopes tipados de discovery/execute.
- `api-delpi/app/application/external_capabilities/dynamic_information/{discover_service,retrieval,action_index,eligibility,catalog_builder,argument_validator}.py`: indexação de ações OpenAPI, filtragem elegível e recuperação semântica; discovery devolve candidatos, argumentos requeridos, schema, hints, score e `action_id` técnico.
- `.../candidate_token.py`: HMAC-SHA256 sobre `action_id`, `actor_id`, emissão e expiração; comparação constante de assinatura, vínculo ao mesmo ator e prazo.
- `.../execute_service.py`: revalida token, action elegível, argumentos e plano; executa `ApprovedCapabilityPlan` ou `CatalogActionPlan`, projeta campos aprovados e limita payload.
- `app/composition/davi_dynamic_read_composer.py`: injeta runner `search_products` ou executor ASGI; authorization do usuário é associado ao request no boundary.
- `app/infrastructure/davi/asgi_catalog_action_executor.py`: rejeita método distinto de GET e POST semanticamente READ explicitamente governado; resolve path a partir do catálogo confiável, repassa Authorization e mapeia erros.
- `app/interface/mcp/oauth_contract.py`: `mcp-api-delpi`, resource exato `https://minhadelpi.com.br/apps/api-delpi/mcp`, scopes `openid profile email mcp:tools`; metadata e policies em `resource_metadata.py`, `asgi.py`.
- `app/application/external_capabilities/davi_agent_intelligence_service.py` e `app/content/davi_agent_intelligence.json`: directives/knowledge orchestration projetadas no `capability_surface`, não fonte de autorização.
- `app/application/use_cases/read_governed_technical_knowledge_use_case.py` + `app/infrastructure/knowledge/governed_knowledge_repository.py`: recuperação governada de corpus técnico; já existe base funcional para futura tool `knowledge`, sem criar fonte paralela.
- `app/content/davi_dynamic_read_budgets.json`: `discover_default_top_k=5`, `discover_max_top_k=10`, `candidate_token_ttl_seconds=300`, `execute_max_items=50`, `execute_max_response_bytes=65536`, `projection_max_depth=8`, `max_page_size=50`, `execute_max_resultsets=8`, `execute_max_result_columns=64`.

### 12.2 Código dos MCPs irmãos verificado

- CAIO: `commercial-api/commercial_app/interface/mcp/server.py`
- CLARA: `controllership-finance-api/controllership_finance_app/interface/mcp/server.py`
- EVA: `engineering-api/engineering_app/interface/mcp/server.py`
- SURI: `supplies-api/app/interfaces/mcp/server.py`
- TÉO: `transformometro-api/tm_app/interface/mcp/server.py`
- VISTA: `tv-dashboard-api/tv_app/interface/mcp/server.py`; registro das seis tools verificado no código.

Nos seis arquivos de `server.py` efetivamente examinados, `get_context`, `read`, `analyze`, `knowledge` e `execute` são registradas diretamente com `@mcp.tool`. `delete` é registrada em CAIO/CLARA/EVA/TÉO, não SURI. `read` usa com frequência `entity + action` e filtros allowlisted; `knowledge` e `get_context` têm diferenças de schema legítimas (não copiar contrato literalmente). `execute` exige policy apropriada ao owner.

### 12.3 Testes existentes identificados (NÃO EXECUTADOS)

- `tests/test_davi_mcp_tool_surface_simplification.py`: duas tools, produto via broker, regressão.
- `tests/test_davi_mcp_platform_conformance.py`: manifesto e conformance MCP compartilhada.
- `tests/test_davi_dynamic_read.py`: tokens por ator, allowlist, argumento, exceções 401/403, projection, transport, paginação e SQL; **alguns nomes/asserções históricos são divergentes e precisam revisão**.
- `tests/test_davi_knowledge_orchestration.py`, `test_davi_governed_knowledge_bundle.py`, `test_davi_live_governed_knowledge.py`, `test_davi_live_governed_knowledge_v2.py`: seleção, corpus, versionamento, provenance, falha segura.
- `tests/test_mcp_auth_middleware.py`, `test_mcp_oauth_contract.py`, `test_mcp_mount_routing.py`: autenticação e roteamento.
- `tests/test_sql_validator_security_hardening.py`: validação sintática e policy de SQL em modo teste.

### 12.4 Divergências que exigem STOP antes da W1

**GAP-SQL-001 — documentação versus teste:** README DAVI descreve `execute_readonly_sql` via broker, mas `test_davi_dynamic_read.py` possui `test_canonical_sql_route_bounded_not_generic_capability`, `test_sql_intent_queries_never_surface_sql_candidate` e `test_candidate_token_cannot_authorize_sql_route`, todos exigindo que a rota SQL **não** seja executável por discovery/execute. Não presumir resultado produtivo; reconciliar `openapi_baseline`, allowlist, testes, código e deployed SHA. Classificar a premissa de disponibilidade como `INCONCLUSIVE / EXECUTION_DRIFT candidate` até confirmação.

**GAP-SQL-002 — tabela allowlist bypass:** `app/application/services/sql_validator.py` tem `DATA_SQL_SKIP_TABLE_WHITELIST` com default textual `true`; testes de hardening forçam `false`. Isso **não prova acesso indevido**, mas significa que SELECT-only não implica restrição de tabelas por default. Levantar configuração real, autorização efetiva e política aprovada antes de alegar proteção completa ou ampliar SQL na nova `read`.

**GAP-TEST-001:** no arquivo `test_davi_dynamic_read.py` há testes históricos chamados `...ninety_three` com `assert len(eligible) == 94`, e outros nomes antigos referentes a três tools; atualizar nomenclatura apenas após avaliar se asserções são ainda executadas e relevantes. Não inferir falha sem `pytest`.

**GAP-TOOL-001:** `read` no padrão irmão aceita frequentemente `entity/action`; o DAVI atual exige descoberta prévia, token HMAC e plano técnico aprovado. É necessária decisão de design para mapear resolução semântica sem permitir `action_id`/URL/SQL livre nem relaxar o gate do candidato.

**GAP-KNOWLEDGE-001:** conhecimento DAVI já existe por use case/corpus e diretivas. Mapear claramente que parte deve ir à tool `knowledge` e que parte deve continuar em `get_context`/instructions, incluindo ACL, versão e provenance.

**GAP-RUNTIME-001:** deployed SHA, owner parity, provider current discovery, rate policy e segundo usuário negativo não comprovados nesta passagem. `TEST_NOT_RUN` para testes e `STALE_EVIDENCE` para claims históricos sem revalidação.

### 12.5 Proposed smallest diff / review gate

1. Primeiro revalidar código/allowlist/SQL e baseline de testes no Cursor; resolver GAP-SQL antes de alterar `read`.
2. Produzir contratos de `get_context` e `knowledge` adaptando, respectivamente, catalog/intelligence existente e corpus governado — sem duplicar lógica ou permitir acesso fora da autorização.
3. Definir `read` como façade semanticamente fechada sobre mecanismo governado, com UX sem ambiguidade (preservar broker antigo até migração de clients/evals). Não apagar candidate-token lifecycle sem equivalente formalmente aprovado.
4. Implementação incremental por tool com contrato/versionamento e testes de regressão e paridade de usuários, seguida de provider rediscovery e live positive/negative AuthZ.
5. Não integrar Strategic Indicators neste mesmo diff. A integração futura exige Core app-permission + backend owner AuthZ, sem permissão herdada por DAVI.

### 12.6 Status desta passagem

| Evidência | Status |
|---|---|
| GitHub `main` lido, DAVI MCP e serviços inspecionados | PASS (source inspection) |
| Seis MCPs irmãos `server.py` inspecionados | PASS (source inspection) |
| VISTA código source registration | PASS (source inspection) |
| Testes locais/CI executados nesta passagem | TEST_NOT_RUN |
| Working tree local | INCONCLUSIVE |
| Deployed SHA e provider live verificados nesta passagem | STALE_EVIDENCE |
| Implementação/mudança runtime | NONE |
| Próximo aceite | Reconciliation report SQL + W1 contract design |

## 13. Wave 001 — Semantic Tools Foundation (DAVI-V2-WAVE-001-SEMANTIC-TOOLS-FOUNDATION)

> Execução em 2026-11-06 pelo Cursor sobre `main`. Escopo W1 aprovado nesta onda: `get_context` + `knowledge` apenas; `read` fica para onda posterior (decisão do brief).

### 13.1 Rebaseline e reconciliação

```text
BASE HEAD       = f9376621b979 (origin/main sync, working tree limpo p/ escopo)
HEAD pré-commit = 0a25a1a4358f (commit concorrente DÉLIA, sem overlap de escopo)
BRANCH          = main
WORKING TREE    = alterações concorrentes de terceiros preservadas
                  (delia docs, engineering-api, infra scripts — não staged)
DEPLOYED SHA    = não acessível nesta sessão — STALE_EVIDENCE
```

**GAP-SQL-001 — reconciliado (sem mudança de política).** No seeding do OpenAPI live (`refresh_davi_action_index_from_live_openapi`, lifespan de `app.main`), `execute_readonly_sql` = `DAVI_ELIGIBLE_READ`/executable (requestBody `{sql:string}` normaliza `supported=True`); 97 ops elegíveis. No fallback baseline (`build_technical_actions_from_baseline`), `request_body_supported=False` → `NEEDS_BOUNDED_EXECUTION`/fail-closed — é esse caminho que os testes (`test_canonical_sql_route_bounded_not_generic_capability` etc.) provam. Documento README "restored" e testes não se contradizem: medem trilhas distintas do mesmo pipeline. Comentários de teste que dizem "DAVI surface is fail-closed" genericamente estão semanticamente datados — nenhuma política SQL alterada nesta onda.

**GAP-SQL-002 — TO_INVENTORY, sem mudança.** `DATA_SQL_SKIP_TABLE_WHITELIST` default textual `true` segue política do SqlValidator da rota (`api-delpi.data` backend AuthZ); fora de escopo W1.

**GAP-TEST-001 — resolvido nesta execução.** Todos os pins de superfície "exactly 2 tools" foram atualizados para o manifesto W1 aprovado (4 tools); nomes de teste datados renomeados (`*_wave001_four`); `surface_parity.mcp_tools` do content layer e fixture `tool_surface` alinhados a 4.

### 13.2 Decisões ratificadas

| DECISION | RATIONALE | OWNER |
|---|---|---|
| `get_context(action=context|catalog|schema)` | paridade semântica com CAIO/CLARA/EVA/SURI/TÉO/VISTA; catálogo real do Action Index, versões, limites, diretivas live; schema sob demanda só para capability elegível; planned tools reportadas `PLANNED_NOT_IMPLEMENTED` | aplicação `context_service.py` |
| `knowledge(action=search|get|sources)` | façade semântica sobre a capability `read_governed_technical_knowledge` já elegível — zero reimplementação de corpus/index | aplicação `knowledge_service.py` |
| Execução via `execute_catalog_read` compartilhado | knowledge reusa plano validado + `CatalogActionExecutorPort` request-bound → backend `api-delpi.access` AuthZ segue autoridade; sem candidate token porque a tool é a seleção fixa (mesmo boundary pós-discovery) | `execute_service.py` |
| `sources` via `published_knowledge_topics` injetado | metadata de índice do corpus já publicada no OpenAPI da rota; conteúdo continua exigindo backend AuthZ | composition |
| Sem segunda fonte de catálogo/conhecimento | reuso de `DaviAgentIntelligenceService`, Action Index, GovernedKnowledgeRepository | — |

### 13.3 Implementação

- `app/interface/mcp/server.py`: registro de `get_context` + `knowledge` (input fechado, outputSchema, `delpi/toolClass` DISCOVERY/READ, securitySchemes).
- `app/interface/mcp/schemas.py`: `GetContextInput/Output`, `KnowledgeInput/Output` + JSON schemas (`extra="forbid"`).
- `app/application/external_capabilities/constants.py`: nomes/títulos/classes das tools.
- `app/application/external_capabilities/dynamic_information/context_service.py` (novo): context/catalog/schema bounded.
- `app/application/external_capabilities/dynamic_information/knowledge_service.py` (novo): search/get/sources sobre pipeline governado.
- `app/application/external_capabilities/dynamic_information/execute_service.py`: extração de `execute_catalog_read` (semântica catalog_action única).
- `app/composition/davi_dynamic_read_composer.py`: executor request-bound compartilhado + `davi_knowledge_wired`.
- `app/content/davi_agent_intelligence.json`: `surface_parity.mcp_tools` 2→4, `knowledge_orchestration.sources.governed_knowledge.tools` += `knowledge`, version 2026.11.06.1.
- Docs de integração correntes atualizadas para superfície de 4 tools (`openai-plugin-mcp.md`, `keycloak-mcp-client-runbook.md`, `integrations/openai-plugin/README.md`).

### 13.4 Testes

```text
pytest -k "davi or mcp"  → 1644 PASS (HEAD pré-commit)
tests/test_davi_semantic_tools_wave001.py → 22 PASS (novo)
Compatibilidade broker (discover/execute, search_products, candidate token,
allowlist, projections, SQL bounded, auth middleware, oauth contract,
mount routing) → PASS sem mudança de contrato externo.
Live/provider/deploy → TEST_NOT_RUN / PENDING.
```

### 13.5 Pendências pós-W1

- Provider rediscovery + live positive/negative AuthZ (segundo usuário) → PENDING.
- `read` semântica (façade sobre broker governado) → próxima onda (GAP-TOOL-001 aberto como decisão de design registrada).
- Avaliação de tool selection/ambiguidade da coexistência 4-tool → PENDING (eval de seleção).

## 14. Execução DAVI-V2-VALIDATION-AND-SEMANTIC-EXPANSION-002

> Executada em 2026-11-06 sobre `main`. W1 revalidada integralmente; `read` implementada como façade semântica sobre o pipeline governado (piloto GAP-TOOL-001 resolvido por decisão de design).

### 14.1 Rebaseline

```text
BASE HEAD       = faf75fe8d3 (W1) → d398ae055d pós-rebase sobre concorrência
BRANCH          = main
WORKING TREE    = alterações de terceiros preservadas (delia/engineering/infra)
DEPLOYED SHA    = container dev local pré-W1 — STALE_EVIDENCE
```

### 14.2 Wave 001 — validação integrada

| Item | Resultado |
|---|---|
| 4 tools registradas, schemas fechados, outputSchema, annotations, securitySchemes, delpi/toolClass | PASS |
| get_context context/catalog/schema + negative (capability inexistente/indisponível) | PASS |
| knowledge sources/search/get, provenance, projeção allowlisted, corpus indisponível honesto, AuthZ propagada | PASS |
| Broker discover→execute, search_products, candidate tokens, allowlist, projeções, SQL bounded | PASS (sem mudança de contrato) |
| Catálogo não concede permissão | PASS (catalog_is_not_permission; backend AuthZ intacto) |
| Live MCP/provider (OAuth, tools/list, second-user negative, agent preview) | TEST_NOT_RUN / PENDING (stack dev existe; container pré-W1; OAuth end-user indisponível na sessão) |
| Tool selection/coexistência eval | PENDING (matriz abaixo; provider eval requer live) |

Matriz de seleção esperada (para eval live pendente):

```text
"o que você consegue consultar?"     → get_context
"regras de descrição de MP"          → knowledge (fonte+provenance)
"cadastro do produto 10080010"       → read|discover→execute (AuthZ backend)
"conceito + dados reais"             → knowledge + read separados, sem mistura
"o que não tenho permissão"          → deny backend, sem vazamento
```

### 14.3 Wave 002 — tool `read`

**Contrato:** `read(capability, arguments?)` — `capability` = action_id publicado pelo catálogo governado (`get_context` catalog/schema). Não é operationId livre: só ids que resolvem para TechnicalAction `executable` executam; demais → `CAPABILITY_NOT_ALLOWED`. Sem URL/path/method/SQL.

**Decisão de design (GAP-TOOL-001 resolvido):** candidate token não é exigido porque a tool é a seleção fixa — mesmo boundary pós-discovery: `get_action_by_id` → `executable` → `build_execution_plan` → dispatch compartilhado `execute_action_plan` (ApprovedCapabilityPlan → search_products runner com enforce_authz; CatalogActionPlan → `execute_catalog_read` → executor request-bound → backend AuthZ → projeção aprovada → bounds). Nenhum registry semântico novo, nenhum mapeamento PT→operationId.

**Reuso total:** Action Index, eligibility, argument validator, execution plan, CatalogActionExecutorPort, approved projection, response bounds, backend AuthZ.

**Compatibilidade:** broker inalterado; `read` e `execute_delpi_information` compartilham `execute_action_plan`. Surface = 5 tools; `read` sai de `PLANNED` no `get_context`.

### 14.4 Testes e gates

```text
tests/test_davi_semantic_tools_wave001.py: 29 PASS (5 novos read)
pytest -k "davi or mcp": ver resultado final registrado em commit
Pins de superfície: 4→5 tools (manifesto semantic waves aprovado)
Content: surface_parity.mcp_tools=5, version 2026.11.06.2
Docs de integração correntes: 5 tools
```

### 14.5 Pendências

```text
WAVE_001_LIVE_PROVIDER      = PENDING (deploy + rediscovery + negative AuthZ)
WAVE_002_READ_LIVE_PROVIDER = PENDING
TOOL_SELECTION_EVAL         = PENDING (matriz §14.2 definida; execução live)
analyze/execute/delete      = PLANNED_NOT_IMPLEMENTED (ondas futuras, por capability aprovada)
Strategic Indicators        = FUTURO (Core API + owner AuthZ — não nesta rodada)
```

## 15. Deploy controlado W1+W2 (DAVI-V2-WAVE-001-002-PRODUCTION-DEPLOY)

> 2026-11-06 — `up-prod-sequential.sh --build api-delpi` em `operador@192.168.1.237`.

```text
ENVIRONMENT         = produção (srv-api 192.168.1.237)
PREVIOUS_DEPLOY_SHA = 47be2a8e0d02 (git já continha W2; container rodava imagem pré-W1 — 2 tools)
TARGET_DEPLOY_SHA   = a38e679ea1 (rebuild da imagem infra-api-delpi)
DEPLOY_METHOD       = git pull (já aplicado por outra frente) + build + recreate seletivo api-delpi + nginx reload
ROLLBACK            = rebuild da imagem anterior / SHA anterior via mesmo script — DISPONÍVEL, não executado
HEALTH              = container healthy; GET /apps/api-delpi/health = 200
502 transitório no healthcheck do script durante boot de migrations — resolvido sozinho
```

Validação pós-deploy:

```text
tools list in-container  = [discover_delpi_information, execute_delpi_information,
                            get_context, knowledge, read] — 5 tools, sem spike/experimental
public /mcp GET+POST     = 401 OAuth challenge (não 307/403)
resource metadata        = resource/scopes canônicos (mcp:tools; aud/resource inalterados)
OAuth/Keycloak/client    = inalterados
tools/call end-user OAuth = TEST_NOT_RUN (token de usuário indisponível na sessão)
negative multi-user AuthZ = PENDING
plugin ChatGPT update     = PENDING — etapa manual do responsável (não nesta execução)
```

## 16. Wave 003 — Governed Analysis (DAVI-V2-WAVE-003-GOVERNED-ANALYSIS)

> 2026-11-06. `analyze` implementada como façade semântica sobre capacidades analíticas já elegíveis — sem recomputação sobre dados paginados.

### 16.1 Decisão de contrato

```text
CONTRATO   = analyze(capability, arguments?)
CAPABILITY = action_id publicado pelo catálogo governado (get_context)
ELIGÍVEL   = executable AND shape ∈ {playbook_report, composite_analysis}
             — só relatórios/agregados computados no backend autoritativo
NEGATIVA   = CAPABILITY_NOT_ALLOWED para single/list shapes, SQL, ids desconhecidos
SAÍDA      = {facts{action_id,entity,shape,projection,data},
             completeness{is_complete,truncated,response_bytes},
             provenance{source:api-delpi, calculation_authority:backend,
                        ANALYTIC_READ, note:no-recompute},
             limitations[]}
```

**Piloto ratificado:** `get_production_appointments_summary` — backend aggregation (appointments summary), já `DAVI_ELIGIBLE_READ` na allowlist v30, shape `playbook_report`. Owner de cálculo = backend api-delpi; a tool não inventa totais nem extrapola janelas.

**Diretivas alinhadas:** `discovery.principle` DISCOVER_THEN_EXECUTE → `SEMANTIC_TOOLS_FIRST_DISCOVER_FALLBACK` (read/analyze/knowledge para capability conhecida; broker para descoberta de candidato). `read` saiu de PLANNED; surface = 6 tools; `analyze` fora de `_PLANNED_TOOLS` (restam execute/delete).

### 16.2 Segurança preservada

Mesmo boundary do `read`: `get_action_by_id` → `executable` + shape gate → `build_execution_plan` → `execute_action_plan` → executor request-bound → backend AuthZ → projeção aprovada → bounds. Sem SQL genérico, sem operationId livre, sem recompute de agregações, sem writes. `tool_name="analyze"` no runner auditável.

### 16.3 Decisão permanente — tools legadas

`discover_delpi_information` + `execute_delpi_information` **serão removidas após migração completa e comprovada** — exige inventário de capabilities legadas, equivalência semântica, migração de consumidores, positive/negative tests, validação no ChatGPT, deploy controlado e rollback plan. Preservadas na W3. `execute`/`delete` não serão implementadas por completude — writes exigem governança própria e aprovação prévia.

### 16.4 Pendências

```text
LIVE MCP/PROVIDER W3   = PENDING (deploy controlado + tools/call OAuth)
NEGATIVE multi-user    = PENDING
TOOL SELECTION eval    = PENDING
execute/delete         = não implementar sem governança de writes
```

## 17. Wave 004 — Analytics parity + legacy readiness (DAVI-V2-WAVE-004-ANALYTICS-AND-LEGACY-PARITY)

> 2026-11-06. Nenhuma ferramenta nova; expansão de `analyze` comprovada por cobertura (gate de shape é genérico) + matriz de equivalência legado↔semântico.

### 17.1 Inventário analítico (baseline offline, allowlist v30)

```text
ELIGÍVEIS TOTAIS  = 94 actions executáveis
ANALÍTICAS        = 25 (playbook_report=21, composite_analysis=4)
  produção : get_production_appointments_summary/produced_totals/otd/
             allocation_gaps/consumption_by_item/consumption_top_items/
             losses_records/losses_top_materials/
             orders_finished_without_consumption/appointments_series...
  suprimentos: get_supplies_{inventory_accuracy,inventory_adjustments,
             non_moving_stock,stock_balances}_summary,
             safety_stock_* , supplier_price_history
  produto  : get_product_{last_purchase,purchase_price_history,
             factory_status,production_status,shipping_status,
             structure_exclusivity,raw_material_set_shortages}
             list_exclusive_raw_materials_catalog, list_production_order_operation_materials
PROVA             = test_analyze_gate_admits_all_eligible_analytic_actions
                    (25 admitidas; 69 não-analíticas → CAPABILITY_NOT_ALLOWED)
```

### 17.2 Matriz de equivalência — broker legado ↔ interface semântica

| Capability legada | Fluxo legado | Fluxo semântico | Paridade | Gap |
|---|---|---|---|---|
| Catálogo de actions | discover (NL retrieval top_k + hints) | get_context action=catalog/schema | PARCIAL | discover faz scoring semântico NL; get_context lista tudo — o modelo seleciona via description/entity/tags |
| Execução de qualquer READ | execute + candidate_token | read(capability,args) | TOTAL | mesmo plano/executor/projeção/AuthZ; token substituído por id fixo publicado pelo catálogo |
| Análises/relatórios | execute | analyze | TOTAL (subset 25/94 com shape gate explícito) | — |
| Knowledge governado | execute(read_governed_technical_knowledge) | knowledge(search/get/sources) | TOTAL + | sources index sem executor |
| search_products | execute runner | read runner | TOTAL | enforce_authz idêntico |

**Gates de retirada (status atual):**

```text
CAPABILITY PARITY   = PASS source/testes (94/94 via read; 25/25 analyze;
                      get_context cobre descoberta estrutural)
CONSUMER MIGRATION  = PENDING (ChatGPT/consumidores ainda usam o broker;
                      instruções já guiam semantic-first)
SECURITY REGRESSION = PASS (boundary idêntico; sem token relaxa só o
                      vínculo de descoberta — seleção fixa equivalente)
LIVE MCP TESTS      = PASS parcial (5→6 tools live; tools/call autenticadas
                      = TEST_NOT_RUN localmente)
PROVIDER DISCOVERY  = PENDING (plugin manual)
ROLLBACK READY      = PASS (SHA anterior + script canônico)
```

**Resíduo funcional real do legado:** `discover` oferece retrieval NL ranqueado (scores/semantic_hints) que `get_context` não replica — migração exige ou (a) aceitar seleção pelo modelo sobre catálogo completo, ou (b) tool `search` semântica dedicada. Decisão na onda de remoção.

### 17.3 Seleção semântica (Frente C) — já coerente

```text
capabilities → get_context | documentação → knowledge
dados → read | relatório → analyze | ambíguo → discover (fallback temporário)
diretivas: SEMANTIC_TOOLS_FIRST_DISCOVER_FALLBACK (W3)
```

### 17.4 Pendências

```text
NEGATIVE multi-user AuthZ    = PENDING
tools/call OAuth live        = PENDING
consumer migration broker    = PENDING
NL-retrieval equivalence     = decisão pendente na remoção
execute/delete               = não implementar (writes exigem governança própria)
```
