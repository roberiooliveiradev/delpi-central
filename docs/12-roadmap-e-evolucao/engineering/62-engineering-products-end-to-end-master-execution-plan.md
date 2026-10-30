# ENGINEERING.PRODUCTS.E2E.MASTER.R1 — Plano Mestre de Execução Ponta a Ponta

**Status:** APPROVED PLAN / IMPLEMENTATION PENDING — este documento autoriza o fluxo de execução técnica dentro das authorities existentes, não constitui evidência de rotas descobertas, testes ou deploy.

**Data:** 2026-10-30  
**Repositório:** roberiooliveiradev/delpi-central  
**Owner de experiência:** Portal Engenharia  
**Especialista:** EVA  
**Fontes e autoridades:** TOTVS / Domain APIs / Engineering API / owner oficial do File Server-Cockpit / Core / Keycloak  
**Especificação visual mandatória:** [Documento 61](61-engineering-products-visual-ux-master-specification.md).  
**Referências:** docs 28, 44, 48–60, especialmente 52 (UX NC), 54 (MCP semântico), 55–58 (EVA e ACT), 59/60 (frontend/deploy).

## 0. Missão e sequência não negociável

Executar continuamente **G0 → G1 → G2 → G3 → G4 → G5 → G6 → G7 → G8 → G9**, com correção e reteste, commits e evidência no SHA final:

1. Reancorar Git/authorities, proteger concorrência.
2. **Inventariar primeiro todos os facts, rotas, owners, permissões, schemas e consumers reais**.
3. **Publicar e preencher o Documento Mestre de Inventário de Contratos (doc 63 ou próximo livre)**, com referências para código, testes, respostas e dados; usar esse documento como contrato operacional durante todas as etapas seguintes.
4. Fechar Contract Gate e escolhas de implementação por capacidade; sem criar endpoints por suposição.
5. Implementar/estender primeiro as **rotas backend oficiais** e seus testes, observando boundaries; garantir que listagem/detalhe/estrutura/reverso/fornecedores/desenhos e histórico tenham contratos reais ou estado de bloqueio justificado.
6. Incorporar todas as capacidades comprovadas da página no registry semântico EVA antes de declarar entregue.
7. Construir somente depois o frontend segundo doc 61 e padrões nativos.
8. Executar testes automatizados, browsers reais e regressão.
9. Commit/push, deploy canônico via SSH Operator no SHA homologado, smoke e documentação de evidência.
10. Não parar por bug corrigível; rework até PASS. Se faltar source of truth/owner/contrato, registrar gate governado e seguir com demais trilhas autorizadas; nunca inventar fato ou declarar PASS fictício.

**"Todas as rotas" significa todas as rotas identificadas como necessárias com owner e fontes oficiais disponíveis; não autoriza fabricar integrações sem evidência.** Se uma aba não tiver fonte/autoridade, construir estado honesto e registrar pendência específica sem bloquear as demais. Não deixar frontend simular capacidade.

## G0 — Reancoragem / authorities / baseline

- Ler `AGENTS.md`, regras always-on, docs 61, 54–60, docs de ownership API DELPI, Engineering API, Core, Keycloak, Cockpit, file server e deploy; registrar precedência.
- `git fetch origin && git rev-parse HEAD && git rev-parse origin/main && git status --short && git log -10 --oneline`.
- Identificar worktrees e alterações concorrentes; não usar reset destrutivo/force push.
- Inventariar convenções `plugins/engineering`, `engineering-api`, `api-delpi`, `shared`, gateways, clients, tests e compose sem assumir caminhos exatos.
- Guardar baseline de features, builds, schema, testes, runtime e SHA produtivo (READ-only).

**Saída:** baseline verificável, donos identificados, drift e riscos.

## G1 — Discovery completo e Documento Mestre de Inventário (obrigatório antes de código funcional)

### Fontes que o Devin deve localizar e provar

1. **Produtos / TOTVS**: API(s) oficiais de busca paginada, detail por código/filial, grupo, tipo (PA/PI/MP), unidade, NCM, descrições, referências, situação, dados adicionais; inspecionar owners/repositories/adapters e índices adequados. Screenshots não são esquema de API.
2. **BOM / estrutura**: rotas existentes da Engineering API e API DELPI, profundidade, componente, pai, quantidade, unidade, revisão, restrições, limite e histórico; distinguir estrutura parcial.
3. **Onde é usado**: busca reversa do produto em estruturas superiores; se não houver contrato, localizar owner e propor contrato sem consulta direta a banco alheio ou derivação incompleta.
4. **Fornecedores**: vínculo produto–fornecedor / amarração, filial, código no fornecedor, nome, campos comerciais sensíveis, autorização; fonte oficial possivelmente em domínio de compras/TOTVS. Respeitar owner suprimentos.
5. **Desenhos**: Cockpit do Operador, serviços/rotas oficiais de file server, resolução por produto/código/revisão, media types, preview/stream/download, expiração e AuthZ, acesso do browser e backend, erros; nenhum acesso MFE direto ao compartilhamento.
6. **Histórico**: trilha oficial de revisões/alterações de produto; não confundir datas de cadastro e update com auditoria.
7. **Edição**: descobrir se existe WRITE oficial de cadastro; enum de campos editáveis, role, ownership, validação, auditoria, concorrência, idempotência, postconditions. Sem autorização escrever somente READ/UX controlado.
8. **EVA**: registry `product.structure` atual, semântica de `get_context/read/analyze/knowledge/execute/delete`, OAuth, Core, contratos e consumidores; acrescentar entidade+ação sem novas tools.
9. **Portal**: catálogo/ícone Package, navegação, layout hero, tabelas, tabs, viewer, timeline, help em label, responsividade e performance.
10. **Segurança e runtime**: AuthN (Keycloak), AuthZ (Core effective), S2S para facts, cache, secrets, logging, limites, multi-filial, erros.

### Documento 63 — contrato de evidência obrigatório

Criar no mesmo diretório o próximo número livre, título: **ENGINEERING.PRODUCTS.CONTRACT.INVENTORY.R1 — Rotas, Sources, Permissions & Capability Ledger**.

Preencher antes da primeira rota nova, com:

- **Tabela por capacidade/aba**: `ID | Status (PROVEN/TO_INVENTORY/PLANNED/TARGET) | owner | source of truth | serviço | endpoint/route/método | request schema | response schema | campo-origem | AuthN | live AuthZ | S2S | pagination/limits | errors | cache | provenance | consumer Portal | consumer EVA | testes | evidência commit/linhas | gap | decisão`.
- Inventário campo a campo de tela: `UI label → payload field → fonte → transformação permitida → null semantics → permissão`.
- Exemplos sanitizados de payload e 200/400/401/403/404/409/502 com limites; não armazenar tokens, senhas ou dados pessoais.
- Dependências, N+1/performance, multi-filial, status de desenhos, compatibilidade, versionamento, rollback e itens sensíveis.
- ADR para qualquer mudança de owner/SoT/bounded context; não implementá-la silenciosamente.
- **Matriz de implementabilidade**: IMPLEMENT_NOW / OWNER_CONTRACT_REQUIRED / BLOCKED; cada bloqueio com owner, contrato necessário e bounded next step.
- **Registro de evolução atualizado em cada gate**: `inventory → contract → code → test → outcome` com SHA testado.
- Todos os novos contratos definidos antes da implementação e reutilizados por frontend e EVA.

Ao terminar G1, efetuar commit desse inventário se tecnicamente consistente; continuar na mesma missão sem aguardar novo prompt.

## G2 — Contratos e ordem de implementação de APIs

Aplicar Contract Gate por operação com owner, readers/writers, request/response, erros, AuthN/AuthZ, rate/size limits, compatibilidade, postconditions de ACT, observabilidade.

**Ordem preferencial das rotas oficiais (ajustar apenas quando discovery demonstrar dependência real):**
1. `product.search`: listagem, filtros e paginação/ordenação server-side.
2. `product.detail`: campos genéricos/estendidos por código + contexto de filial.
3. `product.structure`: reaproveitar contrato existente; adicionar apenas campos oficiais comprovados.
4. `product.where_used`: referência reversa governada.
5. `product.suppliers`: vínculos governados do owner de suprimentos.
6. `product.drawings` e acesso seguro ao documento via contrato do Cockpit/file server (metadados/preview/download conforme escopo).
7. `product.history`: somente se trilha oficial existir.
8. `product.update` (ou operação write específica): apenas com owner, live AuthZ, idempotência/concurrency/audit e aprovação de publicação; nenhuma escrita direta TOTVS por Engenharia.

Para cada operação: testes contratuais, negativas, limites, erros tipados, fonte indisponível, nulidade, no N+1. Adapters oficiais e boundaries DDD/Clean Arch; Engineering API não vira source of truth do cadastro TOTVS.

**Bloqueio controlado:** se owner externo não permitir nova rota, registrar OWNER_CONTRACT_REQUIRED; o Devin continua os outros endpoints sem fabricar resposta e sem ampliar permissions.

## G3 — Backend e integração de dados

- Implementar menores diffs corretos nos owners reais. Reusar adapters/query/services existentes e evitar API duplicada.
- Garantir consumo por Engineering API/Portal via contratos governados; nenhum acesso direto frontend a DB, file share, API interna não autorizada ou implementação de outro contexto.
- Testes para filtros, performance, paginação, multicódigo/multifilial, tipos, BOM parcial/completa, relações reversas, fornecedor, desenho inexistente/negado/indisponível, históricos e snapshots.
- Não expor custo/preço/tributos apenas por estarem no screenshot TOTVS.
- Para desenhos, não retornar URLs públicas sem expiração/controle; documentar caching e acesso; revisão somente da fonte.
- Registrar cada rota concluída e provas no documento de inventário.

## G4 — EVA parity obrigatória

- `get_context` passa a descobrir ações PROVEN com schema on-demand.
- `read` mapeia todas as operações READ oficiais implementadas de Produtos (search/detail/structure/where_used/suppliers/drawings/history).
- `analyze` e `knowledge` apenas quando houver corpus/dados verificados; `execute` de produto apenas sob contrato WRITE real e live Core AuthZ; sem inferir edição pelo master flag de NC.
- Modelo mantém **seis ferramentas semânticas**, sem criar tool por aba/rota e sem importar internals entre bounded contexts.
- Teste de parity por capacidade: mesmo código/usuário/filtro, resultado Portal vs EVA baseado no mesmo contrato, com provenance. Dados proibidos ao usuário devem ser negados em ambos.
- Desenhos: EVA pode localizar/ler metadados; interpretar conteúdo apenas com acesso e extração oficialmente suportados; saída técnica candidata, nunca documento oficial.
- Atualizar capability ledger; não marcar ações PLANNED como PROVEN.

## G5 — Frontend segundo doc 61 (somente após APIs ou blockers formalizados)

### Página A — Produtos / Catálogo
- Registrar rota, card de acesso e ícone Package no catálogo canônico do Portal, respeitar favorites/recents.
- Hero nativo com título Produtos, descrição aprovada, chips/links reais; KPIs apenas se oficiais.
- Busca por código/descrição/referência quando suportada, filtros por tipo/grupo/situação segundo contrato, limpar, URL state conforme padrão, query bounded.
- Tabela com Código, Descrição, Tipo, Unidade, colunas adicionais quando fonte; paginação e sorting server-side, navegação ao detalhe, keyboard focus, mobile sem overflow.
- Empty/loading/unavailable/forbidden/error, sem exibir false empty.

### Página B — Ficha do Produto
- Breadcrumb, hero compacto, código, descrição, badges reais, Visualizar como padrão, Editar somente permitido.
- Abas **exatamente**: Visão geral; Estrutura; Onde é usado; Fornecedores; Desenhos; Histórico; carregamento independente/lazy.
- Visão geral com identificação, classificação, referências, unidades, NCM, estados honestos.
- Estrutura hierárquica e links para componentes, com controles de profundidade.
- Onde é usado com lista reversa contratual.
- Fornecedores com tabela de vínculos autorizados.
- Desenhos: para PA encontrado, card de destaque na Visão geral, aba com preview e revisão; para MP/PI exibir docs disponíveis; reutilizar integração segura do Cockpit e viewer oficial.
- Histórico com timeline oficial somente se fonte existe.
- Editar: apenas campos reais editáveis; Save/Cancel, dirty-state, validações, conflito, autoria, confirmação proporcional; sem habilitar edição por UX antes do backend.
- Contextual help no texto do label (hover/focus/touch) e sync da feature, sem '?' redundantes.
- Acessibilidade WCAG prática, light/dark, desktop/tablet/mobile; textos PT-BR; design system e referência NC/Home/Visão Geral, **jamais reproduzir o visual TOTVS**.
- Sem mocks ou fixtures em produção. Telas sem fonte mostram motivos e próximos passos honestos, não valores inventados.

## G6 — QA integrado e browser real

- Backend: unit/integration/contract AuthN/AuthZ/negativas/compat/errors/pagination/perf/doc streaming, no data leakage e regression.
- EVA: discovery, read parity, tool schema, permission separation, provenance, auth boundary; write only if authorized.
- MFE: typecheck, lint, vitest, build, routing, tab navigation, filters, form errors, viewer secure, help, empty/unavailable.
- Playwright/Chromium com SSO em ambiente autorizado: catálogo, detalhe, cada aba, PA com desenho quando houver fixture autorizado, MP sem desenho, edição habilitada/desabilitada, 401/403, mobile/tablet/desktop e light/dark. Capturas reais por viewport.
- Proibido alegar teste de integração ou dados existentes quando só mock foi usado; classificar TEST_NOT_RUN quando ambiente/consumer indisponível.
- Verificar head SHA final; reexecutar testes após último diff e após merges.

## G7 — Preflight e deploy via SSH Operator

- Antes de deploy, commit/push diff testado; aprovação operacional segundo AGENTS/owners aplicáveis; conferir `origin/main` e SHA produtivo, dirty tree, serviços afetados, endpoint diffs, flags, rollback de imagens/artefatos.
- Referência histórica `operador@192.168.1.237`, `~/projetos/delpi-central`; confirmar nas authorities atuais, não presumir host/config.
- Procedimento canônico: `git pull --ff-only`, validar script `./infra/scripts/up-prod-sequential.sh --build <serviços afetados>` antes de executar.
- Ordem dependente de contratos: backend oficial/adapters primeiro quando mudaram, smoke/API/parity, MFE depois; serviços mínimos necessários. Não derrubar stack inteira nem alterar DB/migrations/grants de outros contexts.
- Deploy somente com precondições e autorizações. Se houver write externo/desenho acesso sem owner approval, publicar somente capacidades seguras; não forçar flags. Preservar Core/Keycloak, NC writer e ACT existente.
- Smoke produção com usuário autorizado e dados reais não destrutivos: catalog search, detail, abas disponíveis, PA drawing view quando permitido, Core denies, EVA read same products, browser real, health/logs; NÃO alterar dados oficiais como smoke.
- Em falha: rollback artefatos/flags com postconditions, preservar dados e documentar incident.
- Registrar deployed SHA + build hash, testes e screenshots produtivos; não afirmar PROD PASS sem prova.

## G8 — Documentação de execução e residual closure

Publicar documento final número livre: **ENGINEERING.PRODUCTS.E2E.R1 — Implementation, Test, Deploy & Runtime Ledger**. Atualizar continuamente doc 63 com rotas implementadas, schemas finais, consumer mapping, coverage, blocked items e SHA. Atualizar doc 61 somente por decisão explícita de design (não distorcer specification silenciosamente).

- Matriz `PRD-01..25` com PASS/FAIL/PENDING/TEST_NOT_RUN; detalhe de pendências por owner.
- Evidências de commits, testes no SHA, screenshots, endpoints, file server, EVA parity, Segurança, deploy, smoke, rollback, version.
- Dados de TOTVS: referenciar sem armazenar conteúdo sensível em docs.
- Conclusão honesta: FULL_SCOPE_PASS apenas se todas as capacidades aprovadas e autorizadas estiverem prontas; caso contrário IMPLEMENTED_WITH_GOVERNED_RESIDUAL e ownership claro.

## G9 — Report final e handoff

Entregar:
```text
EVA EXECUTION REPORT
TASK: ENGINEERING.PRODUCTS.E2E.MASTER.R1
BASE_HEAD:
INVENTORY_DOCUMENT:
INVENTORY_COMMIT:
MASTER_PLAN_DOCUMENT: 62
AUTHORITIES_READ:
SOURCES_AND_OWNERS:
CONTRACT_MATRIX:
API_ROUTES_PROVEN:
API_ROUTES_IMPLEMENTED:
API_ROUTES_OWNER_BLOCKED:
AUTHN_AUTHZ:
DRAWING_COCKPIT_REUSE:
SUPPLIERS_SOURCE:
WHERE_USED_SOURCE:
HISTORY_SOURCE:
EDIT_WRITE_AUTHORITY:
EVA_SEMANTIC_PARITY:
FRONTEND_CATALOG:
FRONTEND_PRODUCT_DETAIL:
TABS_STATUS:
DRAWING_PREVIEW:
EDIT_MODE_STATUS:
LIGHT_DARK_MOBILE:
TEST_COMMANDS:
TEST_RESULTS:
TESTED_SHA:
BROWSER_EVIDENCE:
COMMITS:
PUSHED_SHA:
DEPLOY_APPROVAL:
SSH_OPERATOR:
PROD_PREVIOUS_SHA:
PROD_DEPLOYED_SHA:
PROD_SMOKE:
ROLLBACK_READY:
PRD_AC_MATRIX:
EXECUTION_DRIFT:
ARCHITECTURE_DECISION_REQUIRED:
UNRESOLVED:
NEXT_BOUNDED_STEP:
FINAL_STATUS:
```

## 10. Guardrails vinculantes

- **Inteligência ampla + autoridade estreita, explícita e governada**.
- Keycloak identidade; Core governança/RBAC; Portal host; owner dos dados oficial; EVA assistente, **não** SoT.
- Source → contract → code → test → runtime; status `PROVEN | TO_INVENTORY | PLANNED | TARGET`; execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`.
- `ARCHITECTURE_DECISION_REQUIRED` para alteração de owner/SoT/boundary; `EXECUTION_DRIFT` para premissa invalidada.
- Contrato antes de implementação; nenhuma permissão fabricada; AuthZ backend-first; no secret/token em prompt/artefato/log.
- READ/WRITE separadas; desenho/artefato técnico sempre DRAFT até aprovação/publicação pelo owner.
- Não fazer promessa de entrega para rotas de fornecedores/onde-usado/histórico/WRITE sem fonte e autoridade; tentar resolver via owner e contrato oficial, seguir outros gates e documentar.
- Objetivo é missão contínua sem novas perguntas rotineiras, **não** poder de tomar decisões de autoridade no lugar dos owners.
