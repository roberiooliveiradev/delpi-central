# CAIO MCP Comercial — Plano fechado de implementação até READY_FOR_KEYCLOAK

**Status:** PLANNED — documento de execução para Devin. **Sem cadastro em Keycloak/ChatGPT neste escopo. **Revisão de catálogo semântico:** seis tools públicas definidas pelo usuário; operações de escrita dependem de contratos e autorização oficiais.**
**Fonte de decisões de personagem:** [README.md](./README.md) — preservar aprovado × proposto; nunca tornar narrativa não aprovada canônica.
**Base investigada (2026-10-29):** `main` em `0a60c3a5763491b01ab847b01b5ad0f99eb4166f`; revalidar `origin/main` imediatamente antes de qualquer edição. Este documento não afirma que o MCP já existe.

## 0. Resultado esperado e limites

Entregar um **MCP remoto CAIO executável**, integrado à **commercial-api** pelo caminho canônico da aplicação, com identidade do personagem, catálogo semântico mínimo, autenticação OAuth/OIDC e autorização efetiva, transporte Streamable HTTP, protected resource metadata, distribuição pública do avatar original, documentação operacional, testes e deploy comprovado **até o ponto em que restem somente as ações humanas de registro/configuração no Keycloak e adição no ChatGPT**.

**Não executar neste trabalho:** criar client/usuários/segredos no Keycloak; vincular ChatGPT; inventar escrita comercial sem contrato governado; expor cada endpoint; inventar permissões, service accounts privilegiadas ou dados; alterar recursos de outros MCPs; mudar `shared` por conveniência. Não declarar READY_FOR_KEYCLOAK se faltar componente crítico verificável.

### Ledger de requisitos e aceites
| ID | Requisito | Evidência/critério |
|---|---|---|
| RQ-01 | MCP integrado ao domain owner comercial | tools invocam use cases/client autorizado da commercial-api sem regra duplicada |
| RQ-02 | Ferramentas iniciais finitas | seis tools semânticas (get_context/read/analyze/knowledge/execute/delete), sem proxy arbitrário |
| RQ-03 | OAuth e resource metadata | discovery, 401/403, issuer/audience/scopes e resource binding testados |
| RQ-04 | Paridade de identidade e escopo | READ respeita usuário, carteira, filial e permissões oficiais; testes negativos |
| RQ-05 | Personagem e avatar | ficha local, validação e projeções; arquivo original aprovado + hash + rota pública |
| RQ-06 | Entrega operacional | container, gateway, observabilidade, CI, deploy e endpoint público comprovado |
| RQ-07 | Handoff Keycloak/ChatGPT | URLs e parâmetros EXATOS e checklist de configuração externa, sem registrar cliente |
| RQ-08 | Segurança de escopo | zero writes sem autorização canônica, zero SQL/path arbitrário, zero dependência MCP-MCP, zero AuthZ via LLM |

## 1. Evidência verificada e inferência

**PROVEN em código:** `commercial-api/commercial_app/interface/http/routes` contém `customer_routes.py`, `seller_portfolio_routes.py`, `open_orders_routes.py`, `analytics_routes.py` e vários outros; use cases incluem `list_customers_in_scope.py`, `get_open_portfolio_summary.py`, `manage_seller_portfolio.py`. Em `customer_routes.py` há `GET /customers/in-scope` (`list_customers_in_scope`) e `GET /customers/search`; em `seller_portfolio_routes.py` há `GET /seller-portfolios/me`; em `open_orders_routes.py` há `GET /open-orders/` (`list_commercial_open_orders`); analytics usa escopo de carteira e gateway para TOTVS.

**PROVEN como referência de arquitetura:** `engineering-api/engineering_app/interface/mcp/{server,asgi,tool_bridge,oauth_contract,routes}.py` apresenta MCP Streamable HTTP, discovery `get_catalog`, metadata OAuth, `delpi_mcp` compartilhado, identidade/contexto de usuário e tool bridge para casos de uso; `shared/delpi_auth` governa identidade e segurança; `shared/delpi_character_profiles` rege ficha narrativa; `shared/delpi_mcp` contém primitives de transporte/metadata. TÉO, VISTA, DAVI e CLARA são referências adicionais, **mas não copiar cegamente**.

**TO_INVENTORY ao executar:** layout exato de deploy comercial, wiring existente de ingress/gateway, conjunto completo de schemas de rotas, compatibilidade do token MCP com commercial-api, contratos de analytics e permissão efetiva. Inspecionar `commercial-api/commercial_app/{main.py,interface/http/routes,application/security,application/use_cases,composition}`, testes, manifests, infra e exemplos de MCP antes de editar. Descoberta não prova ausência.

## 2. Arquitetura travada

```
ChatGPT/OpenAI Plugin (futuro, configuração humana)
→ OAuth/OIDC Keycloak (a registrar posteriormente)
→ gateway/ingress + protected resource metadata
→ CAIO MCP remote Streamable HTTP (principal autenticado, tool allowlist)
→ commercial-api owner-local application/use case ou cliente autorizado existente
→ commercial permissions / customer and portfolio scope / downstream owner (TOTVS via gateway existente)
```

**Decisão de localização:** preferir adapter MCP **dentro de `commercial-api/commercial_app/interface/mcp`**, como engenharia, se a revalidação comprovar acoplamento adequado; não criar microserviço separado só para duplicar client/identity. Se já existir arquitetura canônica mais apropriada para MCP Comercial, seguir essa arquitetura, documentando a razão e preservando ownership. Não criar regra de negócio no adapter.

**Invariantes:** Keycloak = identidade; Core = permissões efetivas transversais; commercial-api = escopo e regras Comerciais; CAIO = canal conversacional. Token válido ≠ autorizado. Fail-closed; não aceitar usuário, seller_id/portfolio_id arbitrário como substituto do contexto de usuário.

## 3. Catálogo semântico aprovado — exatamente seis tools públicas

**DECISÃO DO USUÁRIO (2026-10-29):** substituir tools por entidade/rota por seis ferramentas semânticas estáveis. A semântica organiza capacidades; não é autorização nem endpoint genérico. Catálogo de **tools fixo**, catálogo de operações internas evolutivo e allowlisted. A implantação inicial deve conter a interface das seis tools com contratos e erros honestos; somente operações com casos de uso e permissões reais poderão ser executadas. Não inventar CRUD.

| Tool | Responsabilidade | Política |
|---|---|---|
| `get_context` | Contexto, escopo e capacidades efetivas do usuário | READ; executar diretamente; não tratar dados declarados pelo cliente como permissão |
| `read` | Consultas semânticas comerciais | READ; executar diretamente |
| `analyze` | Análises e inteligência comercial usando resultados do owner | ANALYSIS; executar diretamente; sem inventar cálculos ou fatos |
| `knowledge` | Conhecimento e orientação sobre processos/produto com fontes | READ/GUIDANCE; executar diretamente; documentação não é verdade operacional |
| `execute` | Criar, atualizar ou executar operação permitida | ACT; executar diretamente **quando autorizada e quando a política efetiva da operação permitir**, com validação, auditoria e verificação do resultado |
| `delete` | Exclusões governadas | DESTRUCTIVE; preparação/validação sem efeito colateral, **confirmação explícita para alvo e efeito exatos**, depois ACT autorizado + verificação |

### Comportamento conversacional obrigatório
- Consultar e analisar: executar sem pedir confirmação ritual.
- Criar/atualizar: executar sem pedir confirmação extra **se a permissão efetiva, o contrato de domínio e a política de risco permitirem ação direta**. Caso a política canônica exija consentimento, aprovação ou etapa adicional, cumpri-la; não reduzir requisitos de segurança por instrução do modelo.
- Pedidos múltiplos: decompor e orquestrar na mesma solicitação, com ordem/dependências, tratamento de falha parcial, idempotência quando pertinente e resultado por operação; nunca alegar transação atômica se o owner não oferecer.
- Excluir: apresentar alvo, impacto e escopo; pedir uma confirmação explícita para exclusão específica; revalidar versão/estado/permissão antes de executar. Confirmação humana não substitui autorização do backend.
- Bloqueio: explicar motivo e não executar; nunca improvisar rota, bypass ou fallback permissivo.
- Não pedir aprovação para seleção de tool, consulta ou raciocínio; apenas solicitar dados essenciais que realmente faltarem ou confirmação exigida pela política.

### Contrato interno e anti-abstração
- Descoberta semântica deve mapear `intent/operation` **enumerado e versionado** para handler canônico, caso de uso, schema tipado, recurso, permissão efetiva, risco, política de confirmação, auditoria e read-back. Qualquer `operation` desconhecida = erro controlado, não dispatch por URL.
- **Proibir** `path`, `method`, URL ou SQL arbitrário, seleção livre de tabela/campo, métodos Python por nome, `eval`, `getattr` dinâmico para operações, e payload genérico sem validação por operação.
- `get_context` pode devolver a lista de operações efetivamente elegíveis por tool e status (implemented/blocked/not_implemented), não só seis nomes. Backend é autoridade das permissões.
- A ferramenta `knowledge` precisa usar conhecimento aprovado existente; se não houver fonte confiável, retornar orientação de escopo e indisponibilidade, não inventar corpus.
- `analyze` pode compor métricas vindas de casos de uso oficiais, rotulando fatos, cálculo determinado, inferência e limite; não reimplementar regra de negócio.
- `execute` e `delete` deverão existir **como ferramentas públicas com superfície interna deny-by-default**. Só ativar operações de escrita que já tenham contrato, autorização, auditoria e teste confirmado; se nenhuma existir no MVP, resposta tipada `not_implemented` e nenhuma persistência. Isso não equivale a implementação de uma capability de escrita.
- Política de operações é um mapeamento pequeno e explícito; não criar motor universal novo se a lista inicial não justificar.

### Primeiras operações de leitura a mapear (não nomes de tools)
1. Contexto comercial e carteira do próprio usuário → `get_context`; investigar `GET /seller-portfolios/me`.
2. Clientes autorizados na carteira → `read(operation=list_my_customers)`; investigar `GET /customers/in-scope`.
3. Pedidos em aberto autorizados → `read(operation=list_my_open_orders)`; investigar `GET /open-orders/`.
4. Resumo de carteira em aberto → `analyze(operation=open_portfolio_summary)`; investigar use case `get_open_portfolio_summary.py`.
5. Visões analíticas permitidas → `analyze(operation=...)`; **enum pequeno confirmado** de `analytics_routes.py`, sem passar caminho arbitrário.
6. Orientações comerciais → `knowledge(operation=...)`, somente se houver fonte de orientação oficial, com proveniência.

**Gate:** no mínimo `get_context` + uma consulta `read` com autorização comprovada; idealmente os itens 1–5, conforme contratos existentes. Tool pública presente ≠ operação de domínio implementada. Catálogo deve declarar as lacunas em vez de simular suporte.

## 4. Plano executável por etapas (Devin: seguir em ordem sem solicitar opinião por detalhes rotineiros)

### E0 — Reancorar e inventariar (read-only)
- Executar `git fetch origin`, `git rev-parse HEAD`, `git rev-parse origin/main`, `git branch --show-current`, `git status --short`, `git worktree list`.
- Ler `AGENTS.md`, `.devin/rules`, `.cursor/rules/development-standards-index.mdc`, `evidence-driven-execution.mdc`, `openai-plugin-mcp-integration.mdc`, `platform-security-identity-authorization.mdc`, `plan-construction.mdc`, `plan-execution.mdc`, `test-and-commit.mdc`, regras de API, testes e deployment aplicáveis.
- **Governança de branch:** `AGENTS.md` manda commit/push em `main` e proíbe trocar/criar branch sem autorização. Este plano foi redigido em uma branch documental e PR rascunho: **não trocar branch, integrar PR nem forçar push por conta própria**. Usar a branch já autorizada da sessão de execução; se houver conflito material, registrar `EXECUTION_DRIFT` e interromper somente o trecho de publicação.
- Montar matriz tool → operação canônica → use case → permissão → recurso/escopo → testes. Identificar owners e consumidores; comparar exemplos TÉO, VISTA, DAVI, CLARA e EVA; registrar HEAD e diffs. Não inventar campos.

### E1 — Contratos e wiring MCP
- Criar adapter no local confirmado, preferencialmente `commercial_app/interface/mcp/`: `constants.py`, `server.py`, `asgi.py`, `oauth_contract.py`, `resource_metadata.py`, `routes.py`, `tool_bridge.py`, `branding.py` **somente se o padrão local realmente os exigir**.
- Reutilizar `shared/delpi_mcp` para transport security, identity/context, resource metadata, errors, tool metadata/validation; reutilizar `shared/delpi_auth` e o middleware comercial. Rotas oficiais/ingress devem corresponder a path efetivo (não inventar URL pública).
- Expor `mcp` Streamable HTTP e discovery, versions, health/readiness existentes; metadata `/.well-known/oauth-protected-resource` no path real; securitySchemes por tool; `WWW-Authenticate` para 401; CORS/Origin/host protections; lifespans/streaming corretos.
- Configuração segura: issuer, audience, resource URL exata, OAuth scopes, allowed origins/hosts; sem fallback permissivo, segredo hardcoded ou client registration auto.

### E2 — Implementar as seis tools semânticas e suas operações governadas
- `get_context`, `read`, `analyze`, `knowledge`, `execute`, `delete` com schemas explícitos; mapear os casos de uso de contexto, clientes, pedidos e analytics segundo a seção 3. Não criar `get_catalog` como sétima tool: discovery nativo MCP e `get_context` cumprem essa função.
- Chamar diretamente application/use cases com contexto seguro quando o adapter é owner-local; se boundary exigir HTTP, usar client compartilhado/contrato existente com identidade do mesmo usuário e defesa contra confused-deputy. Nenhum acesso direto a banco ou TOTVS.
- Cada tool/operação: request tipado, validação, limite, autorização de domínio, envelope de sucesso/erro, documentação, teste positivo e negativo, sem dados, inválido, 403, timeout e falha downstream. Não duplicar cálculos de analytics no MCP. Escritas só com contrato governado; excluir sempre após confirmação específica.
- Se algum caso do domínio não estiver pronto, usar menor funcionalidade já comprovada que satisfaz intenção; não produzir compatibilidade falsa.

### E3 — Personagem e avatar
- Preservar a ficha completa de `README.md` e este plano. Criar `CharacterProfile` preenchido **dentro do CAIO**, nunca em shared, usando tipos públicos. Somente traços/aparência aprovados são fatos narrativos; idade, eventos e relacionamentos não aprovados ficam vazios ou internos explicitamente em proposta fora do runtime.
- `validate_profile` zero ERROR, `project_persona_context` no canal MCP existente, `project_public_profile` somente via distribuição aprovada. Testar ficção ≠ AuthZ.
- **Asset bloqueante:** exigir o arquivo **exato** aprovado pelo usuário, não uma nova imagem semelhante. Preservar original, nome/versionamento, MIME e SHA-256 no MCP dono; adicionar rota pública **somente avatar** com path estável, cache control apropriado e hash verificável. Se arquivo indisponível, não substituir silenciosamente: marcar etapa `PENDING_ASSET` e não declarar avatar concluído.

### E4 — Segurança, qualidade e infraestrutura
- Comparar permission codes comerciais atuais e scope resolver (usuário/carteira/cliente/filial). Provar 401 sem token, 403 sem permissão, 403 para recurso fora da carteira, claim inválida, aud errada, scope OAuth insuficiente e 5xx no resolver fail-closed.
- Rodar suíte comercial, testes MCP, auth/transport, serialização, metas de limites, tool-discovery, build container e testes negativos. Nenhuma escrita sem contrato validado e política de execução correta; regressão de rotas HTTP comerciais intacta.
- Atualizar Dockerfile/requirements/infra routes/ingress apenas quando necessários para o MCP; adicionar healthcheck, env-template, métricas/logs não sensíveis. Testar origin/mount exato, metadata, long-lived session, restart e falhas upstream.

### E5 — Deploy canônico e validação remota
- Seguir `AGENTS.md` e regras de release: deployment em servidor **que realmente serve endpoint público**; obter SHA antes/depois, `git pull --ff-only`, `./infra/scripts/up-prod-sequential.sh --build <serviços afetados>` conforme ambiente e autorização válidos; não divulgar credenciais ou valores de secrets.
- Verificar SHA em produção, health, protected-resource metadata, challenge 401, lista de tools via cliente MCP autenticado **de teste**, respostas READ com usuário autorizado e 403 de outro escopo. Verificar rota do PNG por GET HTTP, MIME, bytes e SHA-256.
- Sem acesso a client OAuth de teste, documentar `TEST_NOT_RUN` e não alegar AuthZ autenticada comprovada. Deploy só é PASS com deployed SHA/health/metadata e tools validadas onde operacionalmente possível.

### E6 — Handoff pronto para cadastro (final)
Produzir `KEYCLOAK_CHATGPT_HANDOFF.md` com valores confirmados, placeholders explícitos para valores que só usuário/admin pode decidir, e instruções passo a passo:
- endpoint MCP público exato; protected-resource metadata URL; issuer e authorization/token endpoints do realm; audience/resource binding e scopes reais; securitySchemes.
- Nome/display do client a criar, tipo `public/confidential` conforme segurança canônica, authorization code + PKCE e redirect URIs **fornecidos pelo ChatGPT no momento do cadastro** (não inventar).
- Permissões comerciais mínimas que o backend requer para o usuário de teste (não autocriar roles/grupos).
- Passos: admin registra/configura client no Keycloak → operador cadastra Plugin/MCP no ChatGPT → OAuth consent/login → discovery → smoke test leitura autorizada → teste negativo de escopo.
- Avatar URL, versão, SHA-256; testes conversacionais e instruções do agente.
- Separar `READY_FOR_KEYCLOAK` (implementado+publicado+metadata+testes suficientes) de `KEYCLOAK_REGISTERED` e `CHATGPT_CONNECTED` (fora do escopo).

## 5. Critérios de go/no-go

`READY_FOR_KEYCLOAK=TRUE` somente quando:
1. Código do MCP, tool discovery e as seis tools públicas registradas com capabilities honestas, contexto e ao menos uma família comercial READ estão implantados e verificáveis.
2. OAuth protected resource metadata e protocolo MCP correspondem exatamente à URL pública, 401/403 e audience/scope corretos testados.
3. Segurança backend e paridade de escopo têm provas positivas e negativas; nenhuma escrita ou tool arbitrária.
4. Perfil aprovado é válido, imagem original de CAIO integrada, versão/hash/rota pública verificáveis.
5. Container/ingress, health, deployed SHA e testes definidos estão comprovados.
6. `KEYCLOAK_CHATGPT_HANDOFF.md` contém checklist e parâmetros exatos para o administrador.

Caso falhe item crítico: `PENDING` ou `INCONCLUSIVE` com causa precisa e próximo passo; nunca mascarar como DONE. Operações que dependam de credenciais, edição de cliente Keycloak, redirect URI do ChatGPT ou aprovação de dados narrativos ficam fora do escopo e não impedem criar a estrutura, mas impedem afirmar fluxo OAuth autenticado fim-a-fim sem teste.

## 6. Relatório obrigatório ao final

```
PLAN: CAIO-MCP-BOOTSTRAP
BASE_HEAD / FINAL_HEAD / DEPLOYED_SHA:
BRANCH / WORKTREE / UNRELATED_CHANGES_PRESERVED:
OWNERS / ROUTE_CONTRACTS / TOOL→USE_CASE→PERMISSION:
TOOLS_IMPLEMENTED / TOOLS_BLOCKED_WITH_REASON:
FILES_CHANGED / REGRESSION / BUILD / NEGATIVE_AUTH_TESTS:
CHARACTER_PROFILE_VERSION / AVATAR_ORIGINAL_SHA256 / PUBLIC_URL:
OAUTH_RESOURCE / ISSUER / AUDIENCE / SCOPES / 401-403:
DEPLOY_HOST / HEALTH / MCP_DISCOVERY / AUTHENTICATED_SMOKE:
KEYCLOAK_HANDOFF_PATH / CHATGPT_SETUP_PENDING:
PROVEN / TO_INVENTORY / PLANNED / TARGET:
PASS / FAIL / PENDING / INCONCLUSIVE / TEST_NOT_RUN / STALE_EVIDENCE:
EXECUTION_DRIFT / SECURITY_GAPS / OPEN_BLOCKERS:
READY_FOR_KEYCLOAK: TRUE|FALSE
FINAL_VERDICT: ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE
```

**Regra de autonomia:** Devin não deve interromper por escolhas rotineiras de nomes internos, testes, mapeamento de schemas e reuso de primitives. Deve usar evidência e o menor diff correto. **Não pode** decidir por conta própria sobre mudança de branch não autorizada, ausência de asset aprovado, novas permissões, bypass de auth, nova capability comercial fora da allowlist, cronologia narrativa, secrets e registro no Keycloak. Se surgir drift material, preservar tudo que já está comprovado e devolver bloqueio específico, não inventar solução.

**Fonte de verdade:** GitHub para contratos/código; execução e testes para runtime; admin Keycloak para credenciais e clients; usuário para aprovação narrativa; backend comercial para dados e regras.

## 7. Registro de decisão de execução — sem confirmação repetitiva

**Aprovado pelo usuário:** consultas, análises, criação, atualização e lotes de operações devem fluir diretamente quando o usuário estiver autorizado; exclusões exigem confirmação explícita; operações bloqueadas devem ser explicadas sem execução. **Compatibilidade de segurança obrigatória:** risco, efeitos materiais, consentimento e permissões finais são governados pelo contrato da operação e pelo backend, que podem exigir controles adicionais mesmo sem exclusão. Nunca trocar autorização por confirmação conversacional. Esta decisão substitui no plano anterior a proposta de tools fragmentadas por endpoint e a restrição de MVP estritamente READ; não cria automaticamente capacidades de escrita.
