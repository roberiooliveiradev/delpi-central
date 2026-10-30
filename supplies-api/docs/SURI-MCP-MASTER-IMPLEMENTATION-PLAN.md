# SURI — Plano Mestre de Construção do MCP até KEYCLOAK_READY

> **Plano:** SURI-MCP-MASTER-001 — versão 1.0 — 2026-10-29  
> **Produto:** SURI — **Suprimentos Unificados, Resultados e Inteligência**.  
> **Pedido do PO:** construir MCP funcional com tools iniciais, identidade/ficha e avatar, deixando-o pronto para **cadastramento no Keycloak**. Não cadastrar ainda; não instalar no ChatGPT; expansão futura a CRUD completo em outro ciclo.  
> **Status:** `PLANNED / AWAITING_EXECUTION`. Este documento é autorização para **planejar**, não é comprovação de execução/deploy, e não substitui authorities.  
> **Repositório:** `roberiooliveiradev/delpi-central`. HEAD remoto consultado em 2026-10-29: `0a60c3a5763491b01ab847b01b5ad0f99eb4166f`. A branch de documentação não é a mesma coisa que main atual. `git status` local não observado por GitHub connector; executor precisa obter BASE HEAD e status.  
> **Escopo da execução futura:** S0–S9, automaticamente entre gates PASS e sem pedir autorização a cada passo **desde que o usuário aprove expressamente a execução deste plano**. Mudança material de scope, implementação de mutações ERP, alteração de RBAC/Keycloak produtivo, deploy e conflitos de authority **não** são autorizados implicitamente.  
> **Critério final:** `KEYCLOAK_READY`, não `CHATGPT_LIVE`. Não confundir build PASS com runtime ou onboarding.

## 1. Outcome contratado e limites objetivos

Entregar uma SURI que **inicialize um servidor MCP real**, ofereça descoberta e ao menos uma ferramenta operacional READ com integração BFF, uma superfície de orientação/knowledge com proveniência e uma análise determinística inicial quando dados homologados a suportarem; conte com identidade narrativa coerente; possua interface de autenticação MCP protegida, resource metadata, tool schemas, testes positivos/irmãos/negativos e um pacote de configuração Keycloak **sem registrar o client**. As capacidades iniciais só poderão ser marcadas `PASS` quando testadas. Se conhecimento/análise exigirem dados, corpus, permission ou contrato indisponíveis, gate é `INCONCLUSIVE` e o executor deve reportar bloqueio, não gerar informação sintética.

**Exclusões desta release**: novas operações de escrita/CRUD, mutações de fornecedores/ERP, aprovação/cancelamento/cutover de SC/PC, abertura de permissions, mudança de papéis ou manifest Core por tool, cadastro do cliente Keycloak, obtenção/configuração de secrets, rollout em produção, registro do plugin no ChatGPT, expansão integral da paridade e chamadas MCP-to-MCP. São etapas posteriores. O **target de produto** continua CRUD completo por paridade de usuário, usando `supplies-api`, e será coberto por roadmap separado após `KEYCLOAK_READY`.

**Invariantes**: `supplies-api` permanece Flask; o MCP é adapter, sem novo owner de regras; `plugins/supplies` continua UX; MFE→BFF; MCP→BFF use cases por canal aprovado (ou HTTP BFF), nunca MCP→`api-delpi`, `purchase-requests-api`, `strategic-indicators-api` ou bancos vizinhos diretamente. Keycloak=SSO, Core=permissions efetivas, BFF=authz server-side e escopo: `capability AND unit_scope AND resource_scope/ownership AND business_rule`. `view-all` nunca amplia unidade. JWT é identidade e contexto, não lista final de permissões. Falha = fail-closed. Tool metadata ou prompt não autoriza negócio.

## 2. Authorities, evidências e status inicial

Revalidar sempre:
1. `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
2. regras `.cursor` globais `development-standards-index`, `evidence-driven-execution`, `centralized-rules-first`, `clean-code-architecture-guardrails`, `english-code-identifiers`; especializadas por responsabilidade `plan-construction`, `plan-execution`, `test-and-commit`, `openai-plugin-mcp-integration`, `platform-api-contracts-integration`, `platform-security-identity-authorization`, `platform-architecture-boundaries`, `platform-quality-testing`, `platform-delivery-runtime-operations`, `platform-reliability-observability`, `ai-external-tools-security`, `feature-help-sync` quando aplicável;
3. ADRs e contratos vigentes de `docs/12-roadmap-e-evolucao/supplies/` (`README.md`, `IMPLEMENTATION-PLAN.md`, `API-ROUTES.md`, integrações e RBAC);
4. schemas, implementation, tests e consumers no HEAD;
5. `docs/10-guias-operacionais/mcp-chatgpt-plugin-onboarding-runbook.md` e documentações MCP dos especialistas;
6. `shared/delpi_character_profiles/{README.md,PROMPT_MESTRE_UNIVERSAL.md,models.py,projection.py,validation.py}`;
7. docs SURI: `SURI-MCP-PRODUCT-ARCHITECTURE.md`, `SURI-MCP-REFERENCE-INVENTORY-20261027.md`, `SURI-MCP-GITHUB-CODE-INVENTORY-20261027.md`, `SURI-MCP-IMPLEMENTATION-PLAN.md`, `SURI-CHARACTER-PROFILE-PREVIEW.md`.

**Fatos comprovados em leitura de código/documentação:** `supplies-api/app/composition/root_composer.py` monta Flask e blueprints; `supplies-api/app/interfaces/http/auth_middleware.py` valida Bearer e resolve effective user no Core; `me_routes.py` possui `/me/capabilities` com `require_policy(can_enter_shell)`; `purchase_orders_routes.py` possui `GET /purchase-orders` protegida por `require_policy(can_use_operations)` e `require_units("branch")`. Código dos MCPs TÉO/VISTA/CLARA/DAVI e `shared/delpi_mcp` já foi localizado. **Nenhuma dessas leituras prova ambiente rodando ou configuração de SURI.**

**Drifts conhecidos:** `README.md` atual de Suprimentos e o topo histórico `IMPLEMENTATION-PLAN.md` divergem sobre E10/E11; não atualizar o roadmap principal silenciosamente. Manifest real `schemaVersion:1.0.0`, rotas efetivas Core `/me/apps` (`apps[].routes`) prevalecem sobre docs antigas que dizem manifest v2 ou `/me/routes`.

## 3. Estado final esperado (DoD KEYCLOAK_READY)

- [ ] Servidor MCP inicializa corretamente sob execução documentada e possui endpoint Streamable HTTP/mount **definido por contrato**, sem redirecionamento indevido e com proteção transport.
- [ ] Resource URI canônica e URL pública **TARGET** especificadas, metadata RFC 9728 + OAuth challenge e scopes/audience exigidos pelo backend conforme o padrão dos outros MCPs.
- [ ] Cliente Keycloak **não criado**; fornecido handoff seguro de nome proposto, tipo de client, PKCE, token auth, audience mapper, scopes, URIs, callback conforme exigência da plataforma, checklist de claims sanitizados e comandos/verificações para o operador.
- [ ] Ferramentas iniciais registradas com input/output schemas tipados; nenhuma tool HTTP/SQL proxy ou CRUD mecânico.
- [ ] `get_catalog` (ou equivalente definido no contract freeze) lista somente funções realmente implantadas.
- [ ] Pelo menos uma tool READ de Suprimentos executa use case/rota BFF autorizados, com escopo de unidade, paginação e erro tipado, em testes integrados.
- [ ] Orientação de produto/knowledge implementada para escopo aprovado, com `source_id`, versão e citações; não dar status de published a fonte ausente.
- [ ] Uma análise inicial de domínio com regra/fórmula homologada ou decomposição de dados reais, sem inferir fatos não fornecidos. Se falta fonte homologada, `GATE KNOW/INSIGHT=INCONCLUSIVE` (não declarar o objetivo integral entregue).
- [ ] Ficha `CharacterProfile` local baseada em `shared/delpi_character_profiles`, voz/conduta e projeção pública, zero validation ERROR; imagem aprovada **anexada como asset binário real no owner** com SHA-256 e status coerente. Se arquivo não estiver acessível ao Dev, tratar como bloqueio específico.
- [ ] Nenhuma alteração de RBAC, escopo, Core, ERP ou segredo embutido; logging sanitizado e correlacionável.
- [ ] Cobertura de testes unit, contracts, integration, security, regression e smoke controlado com resultados reais, além de `TEST_NOT_RUN` quando não executável. Sem criar falso usuário autorizado para simular produção.
- [ ] Documentação de execução, configuração, troubleshooting e expansão posterior; commits com SHAs, branch e evidência rastreáveis; revisão de diff/ownership; `git status` final conhecido.
- [ ] **Sem cadastro Keycloak, sem publicação ChatGPT, sem deploy produtivo** nesta entrega.

## 4. Ledger de requisitos, aceite e rastreabilidade

| ID | Requisito | Etapa | Critério objetivo | Teste |
|---|---|---|---|---|
| MS-RQ-01 | Ficha SURI e visual aprovado | S2 | `CharacterProfile`, projections, avatar hash, status | T-PERSONA |
| MS-RQ-02 | Boundary Flask/MCP correto | S0–S3 | owner e runtime separados corretamente, sem mudança Flask | T-ARCH |
| MS-RQ-03 | OAuth resource + usuário real | S1/S3/S8 | metadata, audience, PKCE checklist, 401/403 | T-AUTHN |
| MS-RQ-04 | AuthZ Core efetiva e escopos | S0/S3/S4 | cenário positive/sibling/negative e fail-closed | T-AUTHZ |
| MS-RQ-05 | Discovery sem falsa tool | S1/S4 | catálogo de tools implementadas sem proxy | T-CATALOG |
| MS-RQ-06 | Operação READ funcional | S4 | resultado real de rota/use case BFF e paginação | T-READ |
| MS-RQ-07 | Conhecimento com fonte | S5 | guia + source/versão/locator, sem alucinação | T-KNOW |
| MS-RQ-08 | Inteligência explicável | S6 | um caso reproduzível com dados homologados | T-INSIGHT |
| MS-RQ-09 | Segurança de outputs/injeção | S3–S8 | bounded output, erros neutros, não obedecer docs maliciosas | T-SEC |
| MS-RQ-10 | CI/build observabilidade | S7 | testes e artefatos de runtime, logs sem secrets | T-CI |
| MS-RQ-11 | Handoff pronto para Keycloak | S8 | guia operacional com valores não secretos, pending external config | T-READY |
| MS-RQ-12 | Verify-final, handoff e SHAs | S9 | relatório e matrix RQ→AC→evidence | T-FINAL |
| MS-RQ-13 | CRUD completo no futuro | S9/futuro | backlog de paridade, NÃO implementado agora | N/A deferred |
| MS-RQ-14 | Não regressão do Portal | Todas | tests BFF/MFE impactados continuam válidos | T-REGRESSION |

### Matriz de ferramentas iniciais — contratos *candidatos*, a congelar em S1

| Tool candidata | Classe | Fonte/uso | Gate |
|---|---|---|---|
| `get_my_context` | READ | contexto mínimo sem grants; usar fonte Core já autorizada | verificar necessidade e PII |
| `get_catalog` | DISCOVERY | tool surface implantada + limites sem repetir RBAC | S1 |
| `list_purchase_orders` | READ | `GET /purchase-orders` existente, `can_use_operations` + `require_units("branch")` | S0 valida contrato, S4 implementa |
| `get_purchase_order` | READ | `GET /purchase-orders/<branch>/<number>` **a verificar**: recurso, resposta, scope e código atual | S0/S4 opcional |
| `get_product_guide` | READ | Ajuda oficial autorizada, não regra operacional | S5 |
| `analyze_purchase_orders` | ANALYSIS | resumo determinístico baseado em campos/semântica confirmados pelo owner | S6 |

**Regra:** nomes exatos, cardinalidade de tools, inputs, outputs e fonte devem ser ratificados em S1. Preferir **3–5 tools de valor** para a primeira versão, sem exigir tool extra sem consumidor real. `get_my_context` e detalhe só entram se aprovados em S1. Evitar que análise replique lógica canônica de atraso/OTD ou invente métrica: pode apenas compor dados existentes de forma reprodutível. Se o caso de PC não for apropriado após inventário, escolher outra READ com mesmo ou menor risco e registrar decisão de substitution/EXECUTION_DRIFT conforme impacto.

## 5. Hipóteses concorrentes para coexistência Flask + MCP

**A. ASGI boundary co-local, aplicação Flask preservada:** servidor MCP em módulo de interface separado, no mesmo bounded context, compartilhando use cases próprios; bridge de contexto deve provar que instancia os mesmos gates de AuthZ. Build/container/hosting compatíveis; sem importar framework no domain. **Risco:** ambient context da Flask (`g`) não atravessa ASGI automaticamente, e uso direto dos handlers HTTP pode perder autorização.

**B. Servidor MCP transport-only isolado, cliente HTTP para `supplies-api`:** preserves fronteira Flask e usa rota HTTP com Bearer end-user, sem token compartilhado; testável e desacoplado do request context Flask. **Risco:** infra extra, propagation e público/privado de rota, timeout/observabilidade, circuito de confiança.

**Decisão `ARCH-MCP-01` permanece aberta até S0:** avaliar evidência de deployment e testes das alternativas, escolher uma, escrever ADR breve com consequências e controlar mínimo diff. **Proibido** decidir A só por “outros MCPs usam ASGI”, decidir B por conveniência sem provar OAuth delegation ou migrar Flask para FastAPI.

## 6. Grafo e sequência de execução contínua

```text
S0 HEAD+INVENTORY+ARCH_DECISION
  → S1 CONTRACT_FREEZE & INITIAL_TOOLS
  → S2 CHARACTER_PROFILE & AVATAR_ASSET
  → S3 MCP_TRANSPORT + RESOURCE_AUTHN
  → S4 READ/DISCOVERY VERTICAL SLICE
  → S5 KNOWLEDGE FIRST SLICE
  → S6 INTELLIGENCE FIRST SLICE
  → S7 CI/HARDENING/REGRESSION
  → S8 KEYCLOAK_HANDOFF/CONFIG PACKAGE
  → S9 VERIFY_FINAL/COMMIT/HANDOFF
  = KEYCLOAK_READY
```

Só transitar para a próxima com `COMPLETE_GATE=PASS`; falha material gera `EXECUTION_DRIFT` e paralisa o subgrafo afetado (sem contornar segurança). **Permite execução sem intervenção humana entre etapas validamente desbloqueadas**, mas não presume autorização para atos externos (Keycloak/produção/ChatGPT).

### S0 — Rebaseline, inventário integral e decisão de arquitetura [READ-FIRST]

**TASK:** inventariar código e surfaces atuais, escolher A/B com owner.  
**Pré-condições:** `git fetch origin`; `git rev-parse HEAD origin/main`; `git status --short`; ler authorities e documentos; não descartar trabalho alheio. Abrir `supplies-api` e consumidores MFE; schemas, integration tests, env/deploy, existing MCP `shared/delpi_mcp` e `delpi_auth`.  
**Atividades:** inventário para cada tool candidata: rota, método, parâmetros, use case, headers, payload/envelope, condição de AuthZ, unidade/ownership, mensagens de erro, fallback, testes, referências. Inspecionar `purchase_orders_routes.py` inteiro, `auth_decorators.py`, `authorization_service.py`, `supplies_permissions.py`, `DelpiApiGateway`, config e pipeline; confirmar se exposição read-only exige schema novo ou pode reusar. Revisar infraestrutura real (NGINX/compose/Wsgi/ASGI), sem mudar infra. Avaliar A/B com diagrama de sequence identity→Core→BFF e matriz de risco. Confirmar asset SURI disponível e sua origem.  
**Deliverables:** `SURI-S0-BASELINE-AND-ARCH-DECISION.md` + capability matrix + ADR `ARCH-MCP-01` + evidência arquivos/linhas/SHAs + escolha primeira tool.  
**Tests:** inspeção de testes atuais e smoke sem efeitos, se disponível; indicar `TEST_NOT_RUN` para não executados.  
**AC:** ownership/padrão de bridge/autorização determinados, tool READ e contrato de conhecimento viáveis, bloqueios classificados. **STOP:** ambiguidade real de auth delegation ou incompatibilidade de Flask. **GATE:** `S0_PASS`.

### S1 — Contract freeze, schemas e políticas de superfície

**TASK:** fechar contrato de transporte, tools e respostas antes de tocar código de operação.  
**Atividades:** definir nome técnico SURI, canonical resource URL **TARGET** (ex.: `https://minhadelpi.com.br/apps/supplies-api/mcp` **somente se gateway contract confirmar**), mount path, protected-resource metadata, OAuth challenges, scopes, audience, provider flow, headers, tools/classes, annotations e securitySchemes metadata. Input schemas tipados, limite de page/page_size, branch bound, output budgets, `source`, `as_of`, `truncated`, `is_complete`, errors estruturados e sem stack trace. Guardar tool map aprovado. Especificar versionamento do catálogo e contrato do guia; classificação de corpus/owner/autoridade.  
**Security:** scopes transport não são business perms. `GET /me/capabilities` não fornece grant para tool: enforcement real sempre no service. tool list não representa acesso a todos os recursos. Contrato de negativos e falha Core indisponível=503/fail-closed.  
**Deliverables:** `SURI-S1-CONTRACT-FREEZE.md` e schema snapshots/fixtures.  
**Tests:** schemas por hipótese e ADR review.  
**AC/GATE:** RQ→tool→owner→AuthZ→contract frozen; `S1_PASS`; nenhuma permissão por tool.

### S2 — Ficha, personalidade e avatar real

**TASK:** implementar CharacterProfile no bounded context `supplies-api` e integrar asset do avatar pré-aprovado **sem** alterar OAuth/tools.  
**Atividades:** usar `shared/delpi_character_profiles` sem duplicar models; identificar content layer canônica `app/content/suri_agent_intelligence.json` (nome candidato), implementar builder de perfil local em `app/persona/suri_profile.py` (candidato), projection, public profile se houver canal aprovado; narrar SURI mulher negra 25 anos, black e variante nagô, “articuladora resolutiva”, humor breve, comunicação objetiva. Relações DAVI/VISTA/TÉO/CLARA/EVA **propostas**, não serializar amizade/reciprocidade como aprovada sem owner. Inserir **bytes da imagem real** recebida em asset path do owner, verificar integridade e registro de referência. Não confundir visual “gostei”/prévia com permissão para publicar oficial sem validação; manter `REFERENCE_NOT_OFFICIAL_AVATAR` até verificação e aprovação oficial.  
**Tests:** `validate_profile=0 ERROR`, public projection sem private metadata, persona context, schema/profile version, branding test, avatar exists/hash, serialization; fallback se arquivo ausente → BLOCKED, não imagem sintética.  
**Deliverables:** ficha real + asset + testes + doc/versão.  
**GATE:** `S2_PASS` com asset íntegro, ou `S2_INCONCLUSIVE` se bytes indisponíveis.

### S3 — MCP real, wire transport e identidade

**TASK:** implementar server/bridge/ASGI app ou adapter HTTP conforme S0, mantendo `supplies-api` Flask.  
**Atividades:** reutilizar `shared/delpi_mcp` transport, resource contract, tool metadata/error/identity se aplicável ao modelo; criar entrypoint de servidor, mount ASGI e `streamable_http_app(stateless_http=True,json_response=True)` se compatível; tool register, branding da ficha, resource metadata, WWW-Authenticate. Authn: validação de issuer/aud/scopes, proteção origin/host, proteção de redirect, contexto request isolation. Se adapter HTTP: propagar Bearer do mesmo usuário exclusivamente à `supplies-api`; proibir service account para user parity. Se co-local: usar ponto de composição de aplicação/autorização sem Flask context falso nem bypass. Infra/config por env sanitizado. Não registrar Keycloak nem secrets.  
**Tests:** HTTP MCP initialize/list_tools, malformed JSON-RPC, wrong method, 401 bearer missing/bad/expired, wrong audience/scope, 403 permission, DNS rebinding/host/origin, cross-request actor leaking, failures Core, no bypass WSGI. Validate SDK/version lock e container build.  
**AC/GATE:** `S3_PASS` com health local e auth gate provado, embora live Keycloak pendente.

### S4 — Discovery e tool READ ponta a ponta

**TASK:** registrar primeiro `get_catalog` e uma READ de PC ou equivalente aprovado, com acesso ao BFF e sem tool executor genérico.  
**Atividades:** descrever contract/version, inputs fechados, filtro de unidade e paginação, calls ao use case/HTTP BFF aprovado, reutilizar `can_use_operations`/`require_units` ou equivalente funcional, preserve 401/403/404/422/503; não reinterpretar `view-all`; truncation/partial. Não enviar dado pessoal irrelevante nem tokens em tool output. Catálogo expõe tool capabilities realmente entregues; atualização junto de tests.  
**Tests:** user permitido filial 01; sibling filial 02 sem alcance; user sem permission, ausência de token, branch injection, parâmetro inválido, lista vazia, resposta BFF incompleta, Core outage, source upstream error, regressão do endpoint HTTP. Teste de integração real com fake Core/HTTP de contrato (não atribuir a produção).  
**AC/GATE:** `S4_PASS` — tool MCP entrega dado BFF com AuthZ e regressão negativa demonstradas.

### S5 — Knowledge/guia inicial versionado

**TASK:** expor orientação oficial das funções iniciais com fonte e versão.  
**Atividades:** reutilizar `HELP-AND-ONBOARDING` / docs de Portal (conforme owner e licença), catálogo explícito de fontes, aprovação por classificação; implementar ferramenta de guia ou busca restrita **conforme S1**; `source_id`, version/hash, `citation_locator`, `evidence_classification`, `published_at`. Preferir **corpus mínimo estático versionado** para primeiro corte, se atende a consulta sem exigir pipeline/DB. Não copiar corpus CLARA. Não consumir docs privadas fora permission. Separar GUIDANCE_NOT_DOMAIN_TRUTH e operational source.  
**Tests:** exact citation, negative source access, revoked/unpublished, missing source, outdated source, malicious instruction injection, absent topic unknown, no leakage.  
**AC/GATE:** `S5_PASS` com demonstração de pergunta respondida usando referência identificável; não afirmar “conhecimento completo”.

### S6 — Insight inicial, factual e explicável

**TASK:** uma análise útil como “resumo de pedidos e prioridades” baseada em campos realmente disponíveis.  
**Atividades:** freeze das regras métricas via owner, decidir se a análise deve delegar a serviço BFF já existente; não construir regra TOTVS nova no MCP; explicar período, unidade, filtros, denominador, warnings e aspecto parcial. Return FACT/CALCULATED/RECOMMENDATION sem tomar ação. Não inventar atraso ou regra temporal.  
**Tests:** fixtures canônicas, invariância por permutação da lista, ausência de itens, datas/filiais e duplicatas, arredondamento, scope, formula, stale/partial, no-tool/no-data cases, recommendation never ACT.  
**AC/GATE:** `S6_PASS` com cálculo reproduzível e aceite funcional; `INCONCLUSIVE` se fonte ou fórmula não homologada.

### S7 — Endurecimento, compatibilidade e CI

**TASK:** testar a solução integral e regressões, qualidade/segurança/observabilidade/build.  
**Atividades:** unit/contracts/integration/security; `test-and-commit.mdc` e guardrails Phase 3 apropriados; lock dependencies, build container no contexto correto, relative imports, packaging shared, docs env exemplares sem secrets, logs de correlation id e status, timeouts e limites; sem crash por Core/downstream indisponível. Auditoria de imports: MCP não importa domínio de outro serviço nem chama `api-delpi` direto. Revisão adversarial do diff, residual search por permissões criadas indevidamente, `/me/routes`, manifest v2, secrets e logic duplicated.  
**Tests:** T-PERSONA, T-ARCH, T-AUTHN, T-AUTHZ, T-CATALOG, T-READ, T-KNOW, T-INSIGHT, T-SEC, T-CI e smoke MCP isolado. Executar, quando material, `python -m unittest scripts/ci/test_audit_architecture_phase3.py -v`, `python -m unittest scripts/ci/test_audit_platform_guardrails.py -v`, `python scripts/ci/audit_architecture_phase3.py --check --base <BASE>`, `python scripts/ci/audit_platform_guardrails.py --check --base <BASE>`; adaptar comandos aos contratos atuais sem suprimi-los.  
**AC/GATE:** `S7_PASS`, com resultados e duração reais, falhas e residuals documentados.

### S8 — Pacote KEYCLOAK_READY, **sem cadastrar**

**TASK:** gerar kit de handoff e ensaio offline/configuração segura.  
**Atividades:** seguir `mcp-chatgpt-plugin-onboarding-runbook.md`: client `mcp-supplies` **candidato**, confidential, authorization code + PKCE S256, direct grants OFF, service accounts OFF, scope `mcp:tools` sem mapper específico; mapper de audience **dedicado ao resource SURI**, identity audience transversal segundo authority, URI exata, metadata protected resource, paths gateway e TLS, securitySchemes. Identificar callback/registration conforme documentação atual da plataforma e expor **variáveis em placeholders**, nunca secret. Handoff ao responsável por IAM com checklist, step-by-step, tester de claims sanitizados: iss, azp, aud, scope, exp; isolamento contra audiences TÉO/VISTA/CLARA/DAVI. Preparar checklist pós-cadastro de 401/403/200, reauth, tool discovery e health sem executá-lo.  
**Evidência obrigatória:** configuração host/gateway apenas inventariada; `KEYCLOAK_CREATED=NO`, `CLIENT_SECRET_CONFIGURED=NO`, `CHATGPT_PLUGIN_CONNECTED=NO`; documento de operação e rollback. Nenhuma alteração no Keycloak real.  
**Tests:** metadata/challenge em teste local, lint de placeholders, aud config, secret scan, route uniqueness/mount.  
**AC/GATE:** `S8_PASS` quando operador dispõe dos parâmetros precisos, testes e passos sem decisões técnicas pendentes; se path real de gateway não puder ser provado, `INCONCLUSIVE` e registrar exatamente o que falta.

### S9 — Verify-final, commits e handoff para cadastro

**TASK:** fechar todas as evidências e demonstrar objetivo em ambiente controlado.  
**Atividades:** revalidar HEAD e `git status`, comparar RQ→AC→tests e scope, verificar version/hash/avatar, tests, container, docs, tool signatures, semantics, security tests. Executar servidor MCP no ambiente permitido e `initialize/list_tools/call_tool` para tool READ/guide/insight com identidade de teste autêntica no ambiente apropriado ou mocks explícitos onde a dependência externa não está configurada; não declarar OAuth end-to-end real no Keycloak não cadastrado. Gerar relatório com `BASE HEAD, FINAL HEAD, GIT STATUS, FACTS PROVEN, TO_INVENTORY, EXECUTION_DRIFT, FILES, CONTRACT IMPACT, TESTS, SECURITY CHECKS, RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION, UNRESOLVED, NEXT STEP`. Rejeitar `PASS` inferido de test-only sem wiring.  
**GATE final:** `KEYCLOAK_READY=PASS` apenas se S0–S8 PASS e verificações S9 de MCP funcional em ambiente controlado; `KEYCLOAK_REGISTERED=NO`, `CHATGPT_CONNECTED=NO`. Se smoke/runtime inexecutável, `INCONCLUSIVE`. Documentar diferenças de ambiente.

## 7. Instrução de execução autônoma para Dev / Cursor

```text
TASK: Execute SURI-MCP-MASTER-001 to KEYCLOAK_READY.
GOAL: Deliver functional SURI MCP with initial governed tools,
      character profile/avatar, knowledge and one verified insight;
      stop BEFORE Keycloak client registration and ChatGPT onboarding.
AUTHORITIES: official GPT architect, applicable .cursor rules,
             supplies ADR/contracts/HEAD code/tests, this plan.
OWNER: supplies-api domain/composition/AuthZ; Keycloak identity;
       Core effective permissions; shared/delpi_mcp infrastructure;
       delpi_character_profiles structure only.
CURRENT_STATE: planned; inspect HEAD, origin/main, git status,
               evidence before any change.
EVIDENCE_REQUIRED: per-step files+SHAs, schemas, AuthZ, tests,
                   runtime wiring, coverage, final handoff.
ALLOWED_SCOPE: S0-S9, minimal owner-local changes and supporting tests/docs;
               commits/push only per repo rules and explicit execution authorization.
FORBIDDEN_SCOPE: Keycloak client change, secrets, production rollout,
                 ChatGPT registration, ERP writes, permission inflation,
                 service/bank bypass, domain imports from other owners,
                 framework migration Flask→ASGI.
CONTRACTS: MCP Streamable HTTP, OAuth protected resource,
           user-bound Core AuthZ, canonical supplies-api use cases;
           profile contract from shared/delpi_character_profiles.
SECURITY: 401/403/cross-audience/cross-user/cross-unit; fail-closed;
          no prompt injection or PII/token leakage.
ACCEPTANCE: S0-S9 PASS, T-* complete, KEYCLOAK_READY, all constraints.
TESTS: positive+sibling+negative, unit+contract+integration+controlled
       smoke+regression+architecture guardrails, evidence preserved.
STOP_CONDITION: EXECUTION_DRIFT, absent user-binding/AuthZ, owner conflict,
                unsupported identity/resource contract, secret leak,
                missing approved asset for avatar, or unresolved material
                dependency. Never improvise bypass; report BLOCKED/INCONCLUSIVE.
RUN_POLICY: Automatically proceed to the next step ONLY after COMPLETE_GATE
            is proven, within authorized scope. Do not request confirmation
            for routine within-scope choices; do not treat the plan as
            authority over new material evidence or external actions.
REPORT: BASE HEAD, FINAL HEAD, STATUS, FACTS PROVEN, TO_INVENTORY,
        EXECUTION_DRIFT, FILES, CONTRACT IMPACT, TESTS, SECURITY CHECKS,
        RQ/AC COVERAGE, RESIDUAL SEARCH, POSTCONDITION/OUTCOME,
        UNRESOLVED, NEXT STEP.
```

## 8. Backlog separado após KEYCLOAK_READY

```text
KEYCLOAK_READY
 → (separada autorização) cadastro client Keycloak e audience real
 → smoke OAuth end-user em HML/produção
 → conectar SURI no ChatGPT / publicar plugin
 → verificar identidade real e tools ao usuário
 → expansão CRUD por jornadas: SC → PC → entregas →
   estoques → fornecedores → gestão e workflows
 → cada write: prepare/confirm/act, BFF canônico, idempotência, audit,
   read-back e testes positivos/irmãos/negativos
 → paridade mensurável por capability, sem liberar ERP bloqueado.
```

O mapa de expansão **não** permite acessar `api-delpi` diretamente, criar permission por tool, converter todas rotas HTTP automaticamente em tools ou executar operações ainda bloqueadas no Portal.

## 9. Situação formal desta entrega documental

`MASTER_PLAN = DOCUMENTED`; `S0 = READY_FOR_INVENTORY`; `S1..S9 = PLANNED`; `KEYCLOAK_READY = PENDING`; `KEYCLOAK_REGISTERED = NO`; `CHATGPT_CONNECTED = NO`; `SURI_MCP_RUNTIME_PROVEN = NO`.  
**Plano fechado quanto ao objetivo e aos gates, aberto apenas onde decisões dependem de código/infra/owner real.** Se uma premissa falhar, emitir `EXECUTION_DRIFT` e seguir a regra STOP-THE-LINE. Não criar “PASS” narrativo.


## 10. Adendo pós-S9 — revisão de catálogo semântico (2026-10-29)

**Authority de planejamento posterior para o catálogo de tools:** [SURI-MCP-SEMANTIC-TOOLS-REFACTOR-PLAN.md](./SURI-MCP-SEMANTIC-TOOLS-REFACTOR-PLAN.md) — task `SURI-MCP-TOOLS-SEMANTIC-001`. O plano S0–S9 é histórico da implementação de 8 tools; **não reexecutar S0–S9** para mudar o catálogo. Novo target antes de cadastrar Keycloak: quatro ferramentas `get_context`, `read`, `analyze`, `knowledge`, preservando as oito capacidades da V1 por ações/entidades explícitas. `execute` e `delete` são apenas famílias TARGET de evolução, não implementadas; a SURI fará operações autorizadas com mínimo de confirmações adicionais, exigindo confirmação explícita para DELETE e quaisquer aprovações obrigatórias do contexto. Fazer refatoração, parity tests, atualização do contract freeze/handoff e novo smoke antes de reafirmar `KEYCLOAK_READY` para o catálogo novo. Não cadastrar Keycloak nem conectar ChatGPT nesta task.


## 11. Evolução arquitetural futura — unificação FastAPI/ASGI (2026-10-30)

**Decisão do Product Owner:** manter **agora** a arquitetura homologada de `supplies-api` em Flask/Gunicorn e `supplies-mcp` como serviço/container ASGI/Uvicorn irmão (ADR `ARCH-MCP-01`). **Não migrar, não consolidar containers e não alterar deploy por causa deste registro.**

**TARGET / backlog futuro:** avaliar migração controlada da `supplies-api` para **FastAPI/ASGI**, com o objetivo de hospedar o MCP SURI no **mesmo processo/container da BFF**, em alinhamento ao padrão atualmente empregado por TÉO, VISTA, DAVI, CLARA e EVA. Este é um **objetivo futuro, não autorização para implementação**, nem decisão antecipada de tecnologia sem inventário e ADR substitutivo.

**Gates antes de eventual execução:** (1) inventariar rotas Flask, middlewares, AuthN/AuthZ, contratos, gateway, clients, testes e consumidores federados no HEAD; (2) comparar migração completa com alternativas de consolidação sem reescrita; (3) medir CPU/memória e custos operacionais reais; (4) produzir ADR de substituição com riscos, fases, rollback e critérios de paridade; (5) obter autorização explícita; (6) preservar Core como authority de RBAC, BFF como owner, quatro tools semânticas e contratos OAuth, sem mudar permissão nem regra TOTVS; (7) validar regressão, smoke federado, OAuth e isolamento de unidade antes de cutover.

**Classificação:** `CURRENT_STATE=PROVEN/Flask + ASGI sibling`; `FUTURE_FASTAPI_UNIFICATION=PLANNED`; `MIGRATION_AUTHORIZED=NO`; `EXECUTION_STATUS=TEST_NOT_RUN`. Este registro não altera o ADR vigente.
