# 15 — Requisitos, Critérios de Aceite e Testes

O ledger detalhado por página está em [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md). Os ACs específicos de paridade P3 permanecem em [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md).

## Famílias de requisitos

### P1
Cobrir competência/unidade, eixos independentes, blockers, freshness, deep links, histórico, IA e experience states.

### P2
Cobrir snapshot, requirement/origin/scope, recipients, satisfaction, anexos, validação, N/A, rejeição, substituição, multi-anexo, item excepcional, correção estrutural, notificações e ACCESS/MANAGE.

### P3
Cobrir preliminary, cutoff, revalidação, conciliação, readiness e canonical STOCK_CLOSED.

### P4
Cobrir sugestão, confirmação humana, filas, claim/reassign, states, resolução e dismiss.

### P5
Cobrir package version, finalize, reopen, recipient packages, partial send, clarification, correction after send e completion.

### P6 / Administração

Cobrir Painel/Templates/Catálogos/Histórico, `controllership-finance.manage` como única permission administrativa, DRAFT→REVIEW→PUBLISH→EFFECTIVE_FROM, snapshot immutability, catálogos tipados, inativação prospectiva sem hard delete, referências de pessoas via Core, notifications boundary, optimistic concurrency, audit, URL/F5, light/dark/mobile/a11y e Help.

Fonte de página: [28-administracao.md](./28-administracao.md).

### Minhas tarefas

Cobrir `TaskWorkspacePage`, TaskProjection self-only, producers P2/P4 e P5 conditional, ação `Abrir` owner, ausência de task entity livre, ausência de team scope/SLA global, partial coverage, URL/F5, integração com Home/Sala, light/dark/mobile/a11y e Help.

Fonte detalhada: [27-minhas-tarefas.md](./27-minhas-tarefas.md).

### Sala de interação

Cobrir full-page `InteractionRoomPage`, contexto obrigatório, resolve idempotente, AuthZ por recurso, message policy, attachments, mentions, reply/reactions/pins, realtime degradável, notifications canônicas, deep links, light/dark/mobile/a11y e Help.

Fonte detalhada: [26-sala-de-interacao.md](./26-sala-de-interacao.md).

### Visão geral

Cobrir Overview family comum, indicator governance, filtros URL/F5, partial isolation, charts semânticos, drilldown rastreável, owner strategic quando aplicável, AuthZ ACCESS/MANAGE, light/dark/mobile/a11y e Help.

Fonte detalhada: [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md).

### Início

Cobrir Home family comum, Hero operacional, Eventos resilientes, catálogo runtime+AuthZ, busca `?q=`, Últimos acessos, Favoritos, light/dark/mobile/a11y e Help sincronizada.

Fonte detalhada: [32-inicio-home.md](./32-inicio-home.md).

### Ajuda

Cobrir `createDashboardUserManual`, rota `/help`, ACCESS guard, TOC/deep-link por hash, concepts/guide table/FAQ/glossary, feature gating por runtime, seção Administração condicionada a MANAGE, links tipados, Help contextual, ausência de BFF/CMS na V1, light/dark/mobile/a11y e `feature-help-sync`.

Fonte detalhada: [29-ajuda.md](./29-ajuda.md).

### Página do usuário
Cobrir deep route sem item de topbar, identidade owned pelo Core, leitura de outro usuário com ACCESS, RBAC self-only, edição via Meu Perfil, estados honestos de source, reuso full-page do `plugin-ui`, atalhos somente para runtime autorizado e Help sincronizada.

Fonte detalhada: [31-pagina-do-usuario.md](./31-pagina-do-usuario.md).

## Critérios indispensáveis

- STOCK_CLOSED + REQUIRED pendente → pacote incompleto;
- último documento satisfeito → não auto-send;
- pre-cut zero → não final;
- source indisponível → não zero;
- PACKAGE_SUBMITTED_FOR_REVIEW + clarification → não complete;
- mudança mestre → snapshot intacto;
- rejected evidence → preservada;
- replacement → nova validação;
- OPTIONAL rejected → não blocker global;
- WHOLE_SET alterado → aceite anterior não reaproveitado;
- nova versão após rejeição → reversal antiga bloqueada;
- correction request stale → sem auto-apply;
- CANCELLED → sem delete/reativação;
- PACKAGE_SUBMITTED_FOR_REVIEW → imutável.

## Matriz de testes

### Positive
Happy path e transições válidas.

### Sibling
Outra unidade/item/destinatário não deve ser afetado indevidamente.

### Negative
Permission, scope, state e payload inválidos.

## Segurança

Testar:
- sem ACCESS;
- ACCESS sem MANAGE;
- cross-unit;
- validator indevido;
- MANAGE fora do scope;
- IA fora do scope;
- tentativa de delete de histórico;
- tentativa de contornar state machine;
- usuário sem ACCESS consultando perfil;
- target fora do Portal;
- exposição de permissions/capabilities de outro usuário;
- tentativa de listar tarefas de outro usuário;
- task projection sem responsabilidade individual;
- source indisponível interpretada como fila vazia;
- pendingSince tratado como SLA/overdue;
- ACCESS alterando configuração;
- permission code criado por catálogo/CRUD;
- stale admin write sobrescrevendo revisão mais nova;
- hard delete de item mestre histórico;
- Administração criando usuário/RBAC no lugar do Core;
- Help publicando capability/rota futura;
- usuário ACCESS-only recebendo instruções executáveis de Administração;
- tool link do manual apontando URL arbitrária;
- criação de BFF/DB/CMS para Help sem nova decisão.

## Experiência

Por página:
- loading;
- empty;
- partial;
- unavailable source;
- error;
- 403;
- 404;
- desktop/mobile;
- claro/escuro;
- teclado/foco;
- deep link/F5 quando aplicável.

## Evidência de execução

Reportar:
- BASE HEAD;
- FINAL HEAD;
- STATUS;
- FACTS PROVEN;
- TO_INVENTORY;
- EXECUTION_DRIFT;
- arquivos;
- contratos;
- testes;
- segurança;
- cobertura RQ/AC;
- residual search;
- unresolved;
- next step.
