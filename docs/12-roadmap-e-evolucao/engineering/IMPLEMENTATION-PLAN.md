# Portal de Engenharia — Implementation Plan

> **Status:** `PLANNED / NOT_STARTED` — 2026-09-11  
> **Primeiro gate:** E0 baseline.  
> **Regra de execução:** nenhuma etapa futura é autorização automática; revalidar código/contratos/regras antes de cada `E*.S*` e executar somente após pedido explícito do Product Owner.

## 1. Overview

Construir `plugins/engineering` + `engineering-api` como Portal de Engenharia nativo da Minha DELPI, absorvendo progressivamente dashboards de Engenharia/LMP, criando Sala, Home, worklist e ferramentas sem duplicar owners existentes.

TopBar alvo:

```text
Início → Visão geral → Sala de interação → Minhas tarefas → LMPs → Ajuda
```

## 2. Ledger

| ID | Requisito | Cobertura |
|---|---|---|
| RQ-01 | Portal central de Engenharia | E1–E3 |
| RQ-02 | TopBar na ordem travada | E2 |
| RQ-03 | Produtos como ferramenta | E3/E8 |
| RQ-04 | LMPs jornada principal | E7 |
| RQ-05 | Sala geral/contextual | E5 |
| RQ-06 | Minhas tarefas agregada | E6 |
| RQ-07 | Controle MP sem duplicar workflow | E10 |
| RQ-08 | TRANSFORMA+ preserva owner | E4/E10 |
| RQ-09 | Biblioteca de desenhos | E9 |
| RQ-10 | Documentos técnicos seguros | E9 |
| RQ-11 | Indicadores oficiais | E4 |
| RQ-12 | Ajuda TopBar/contextual | transversal + E11 |
| RQ-13 | `@delpi/plugin-ui` kit-first | transversal |
| RQ-14 | BFF próprio; MFE sem api-delpi direto | E1 + testes estruturais |
| RQ-15 | Core-first AuthZ | E1/transversal |
| RQ-16 | deep links/F5/back-forward | cada GATE-FEATURE |
| RQ-17 | light/dark/mobile/keyboard | cada GATE-FEATURE |
| RQ-18 | cutover gradual dos legados | E12 |
| RQ-19 | documentação rastreável | transversal/E13 |
| RQ-20 | FILESERVER allowlisted, sem Explorer irrestrito | E9 |

## 3. Readiness

| Área | Estado |
|---|---|
| documentação de produto | **READY_BOUNDED** |
| inventário técnico | **precisa E0** |
| `plugins/engineering` | não existe |
| `engineering-api` | não existe |
| schema/persistence | planejado; runner/banco a revalidar |
| manifesto/RBAC | draft; catálogo Core a revalidar |
| Sala/realtime | arquitetura pronta; decisões P-01…P-05 abertas |
| Minhas tarefas | arquitetura pronta; fontes P0 abertas |
| Overview | 2 indicadores SI confirmados; operacionais abertos |
| LMP | legado confirmado; paridade detalhada precisa E0 |
| Produtos/desenhos | contratos existentes; mapa exato precisa E0 |
| documentos FILESERVER | `NOT_READY` até allowlist P-12 |
| cutover | bloqueado por paridade |

## 4. Dependências

```text
E0
├── E1 API foundation
│   └── E2 shell/manifest/RBAC
│       └── E3 Home
│           ├── E4 Overview
│           ├── E5 Sala
│           ├── E6 Minhas tarefas
│           └── E7 LMPs
│               └── E8 Produtos
│                   └── E9 Desenhos/Documentos
│
E10 integrações externas pode avançar por contrato após E1/E2
E11 Help é transversal; auditoria final depois das páginas
E12 paridade/cutover depende E4+E7 e gates correspondentes
E13 verify-final depende de todos P0 autorizados
```

A ordem de páginas pode ser repriorizada pelo Product Owner, mas uma página só é promovida com dependências e decisões prontas. Não executar várias telas P0 em paralelo por conveniência.

## 5. Gates

```text
GATE-E0       inventário/ownership/decisões
GATE-ARCH     boundaries e dependency direction
GATE-AUTHZ    Core-first/fail-closed
GATE-RBAC     capabilities/personas
GATE-RUNTIME  compose/gateway/health/remoteEntry
GATE-FEATURE  por página
GATE-PARITY   por legado
GATE-CUTOVER  rollout/rollback
VERIFY-FINAL  pedido original
```

## 6. E0 — Baseline e decisões

### E0.S1 — Inventário runtime

**Objetivo:** congelar ativos, contratos, consumidores e drifts reais.

**Requisitos:** RQ-18, RQ-19.

**Fazer:** `INVENTARIO-ATIVOS.md`; manifests `dashboard-engineering`/`dashboard-lmps`; chamadas de API; OpenAPI Engenharia/Produtos; SI; Controle MP; Transformômetro; FILESERVER; plugin-ui; Comercial Sala; deep links/consumidores.

**Não fazer:** criar `engineering-api`/MFE.

**Evidência:** arquivos/código/contratos atuais + Core DEV/HML quando acessível.

**Teste:** checklist de inventário; nenhuma afirmação P0 sem fonte.

**Pronto quando:** drifts classificados e owners inequívocos.

**Commit sugerido:** `docs(engineering): congelar baseline técnico do Portal`

### E0.S2 — Resolver decisões bloqueantes da primeira onda

**Objetivo:** promover apenas decisões necessárias para fundação/shell/Home.

**Requisitos:** RQ-01, RQ-02, RQ-13, RQ-14, RQ-15.

**Fazer:** confirmar schema manifesto, banco/migration runner, auth resolver, basePath, API prefix, kit/factories, infra naming.

**Não fazer:** resolver P-01…P-20 sem necessidade.

**Teste:** matriz READY_CONFIRMED/READY_BOUNDED/NOT_READY.

**Pronto quando:** E1/E2 não dependem de TBD material.

**Commit:** `docs(engineering): fechar decisões da fundação`

## 7. E1 — engineering-api foundation

### E1.S1 — Scaffold e runtime

**Objetivo:** criar serviço Flask testável com health/readiness/config/errors/logs.

**Requisitos:** RQ-14, RQ-15.

**Fazer:** Clean Architecture, DI por composição, config/env, Docker, requirements, testes base.

**Não fazer:** endpoints de negócio especulativos.

**Evidência:** padrões de serviços Flask maduros no repo.

**Dependência:** E0 PASS.

**Teste:** comandos reais descobertos no serviço/repo; health, lint, unit.

**Pronto quando:** container sobe e health/readiness possuem semântica correta.

**Commit:** `feat(engineering): criar fundação da API`

### E1.S2 — AuthZ Core-first

**Objetivo:** resolver identidade/capabilities sem confiar em permission list do JWT.

**Fazer:** validator JWT compartilhado; gateway Core; policy fail-closed; request context.

**Teste:** JWT inválido/expirado; sem `engineering.access`; Core indisponível; autorizado.

**Pronto quando:** nenhuma rota protegida depende apenas do frontend/JWT claims.

**Commit:** `feat(engineering): aplicar autorização Core-first`

### E1.S3 — Gateways base

Criar ports/adapters vazios tipados para providers realmente confirmados; não implementar rotas de produto antecipadamente.

**Teste:** unit de adapter/error mapping.

## 8. E2 — MFE, shell, manifesto e RBAC

### E2.S1 — Scaffold `plugins/engineering`

**Objetivo:** MFE Module Federation com façade `engineeringUi.ts`.

**Fazer:** app/router/session/content/features base; consumir apenas `engineering-api`.

**Teste:** typecheck/lint/build/standalone.

### E2.S2 — TopBar e navegação

**Objetivo:** ordem perceptível correta e rotas tipadas.

**Teste:** ordem exata, capabilities, Ctrl+K, favoritos, mobile/hamburger, F5/back.

### E2.S3 — Manifest/RBAC/gateway/compose

**Objetivo:** registrar um único Portal no Core e publicar MFE/API.

**Teste:** manifest contract, remoteEntry 200, API health, `/me/apps`/contrato vigente, persona permitida/negativa.

**Gate:** `GATE-RUNTIME + GATE-AUTHZ + GATE-RBAC`.

## 9. E3 — Início

### E3.S1 — `/home` BFF

Compor atenção/tarefas/LMP/menções/ferramentas apenas com fontes promovidas. Degradação parcial explícita.

**Teste:** todas fontes OK; uma fonte falha; sem capability; timeout.

### E3.S2 — Home UI

PageHero + prioridades + ferramentas + atividade. Kit-first, Help sincronizado.

**Teste:** loading/empty/partial/error/403, mobile/light/dark/keyboard, rota/favoritos.

**Gate:** `GATE-FEATURE WF-01`.

## 10. E4 — Visão geral

### E4.S1 — Contrato Overview

Compor Strategic Indicators e blocos operacionais aprovados. Preservar `engineering-projects-on-time` e `engineering-transforma-plus` sem recalcular IDD.

### E4.S2 — UI Overview

Filtros somente se coerentes com todas as fontes; charts/KPIs do kit; drills.

**Testes:** valores SI, consolidado, parcial por downstream, URL, loading/empty/error, mobile/theme.

**Gate:** `GATE-FEATURE WF-02` + base para paridade dashboard-engineering.

## 11. E5 — Sala de interação

Só promover depois de P-01…P-05 estarem suficientemente resolvidos.

### E5.S1 — Modelo/migrations/repositories

Rooms, members, messages, mentions/reactions/read state e attachments apenas se storage aprovado.

### E5.S2 — HTTP use cases

Inbox, room, messages, reactions, membership/read state conforme policy.

### E5.S3 — Realtime

Persist-before-publish; subscribe/unsubscribe; reconnect; keepalive; anti-echo; isolamento.

### E5.S4 — UI inbox/thread/composer

Mapear componentes genéricos do Comercial e extrair para `plugin-ui` somente onde reutilização for realmente visual/transversal.

### E5.S5 — Notifications/attachments

Implementar apenas contratos aprovados, com segurança e categoria própria quando necessária.

**Testes:** API/resource IDOR + dois browsers + reload persistence + mobile/keyboard.

**Gate:** `GATE-FEATURE WF-03`.

## 12. E6 — Minhas tarefas

### E6.S1 — Freeze sources

Resolver P-06/P-07 e mapear owner→DTO→deep link/actions.

### E6.S2 — BFF aggregator

Normalizar sem duplicar workflow; falha parcial por source.

### E6.S3 — UI worklist

Filtros, contadores, DataTable/card mobile e deep links.

**Gate:** `GATE-FEATURE WF-04`.

## 13. E7 — LMPs

### E7.S1 — Freeze de paridade legado

Mapear lista, filtros, detalhe, produtos, histórico, Gantt, NCs, permissions e deep links de `dashboard-lmps`.

### E7.S2 — BFF LMP

Adapters de `/engineering/lmps/*`; DTO interno; nenhuma regra TOTVS no MFE.

### E7.S3 — Lista

### E7.S4 — Detalhe

### E7.S5 — Histórico/Gantt

### E7.S6 — Não conformidades

Preservar `view` × `nc.write` e casos negativos.

**Gate:** `GATE-FEATURE WF-05` + `GATE-PARITY dashboard-lmps` antes do cutover.

## 14. E8 — Produtos

### E8.S1 — Freeze contratos api-delpi

Pesquisa, detalhe, structure, parents, drawing, stock, suppliers, pricing/cost.

### E8.S2 — BFF Product 360

### E8.S3 — Busca/lista

### E8.S4 — Ficha 360

Preço/custo só com P-10 resolvida.

**Gate:** `GATE-FEATURE Produtos`.

## 15. E9 — Desenhos e documentos

### E9.S1 — Biblioteca de desenhos

Reusar backend existente; nenhuma exposição de path.

### E9.S2 — Document libraries contract

Executar somente após P-12/P-13; `library_id` e `document_id` opacos.

### E9.S3 — UI Documentos

Read-only no MVP; Office download se preview não estiver aprovado.

**Testes:** traversal, extension, size, RBAC, share down, streaming.

## 16. E10 — Integrações externas

### E10.S1 — Controle MP

Resumo opcional + deep links reais `my-requests`; sem workflow local.

### E10.S2 — TRANSFORMA+

Resumo/drill; owner permanece Transformômetro.

Cada integração tem teste de permission, timeout e deep link.

## 17. E11 — Help/onboarding consolidation

Help é transversal em E2–E10. E11 apenas audita:

- Quero→onde;
- FAQ;
- glossário;
- tooltips;
- route targets;
- termos de negócio;
- ausência de `?` standalone onde há label apropriado.

## 18. E12 — Paridade e cutover

### E12.S1 — dashboard-engineering parity

### E12.S2 — dashboard-lmps parity

### E12.S3 — permission/deep-link migration

### E12.S4 — soft cutover

### E12.S5 — observation + redirect

### E12.S6 — hard cutover

Seguir `HOMOLOGACAO-PARIDADE.md` e `CUTOVER-RUNBOOK.md`. Nunca juntar criação do target e hard cutover no mesmo subpasso.

## 19. E13 — Verify-final

**Objetivo:** provar o pedido original, não somente testes unitários.

Rodar:

- backend tests/lint/type checks vigentes;
- MFE tests/typecheck/lint/build;
- manifest/gateway contracts;
- smoke federado;
- realtime 2-clientes;
- paridade quantitativa;
- mobile/light/dark/keyboard;
- docs/help audit;
- grep/structural gate de `plugins/engineering` chamando apenas `engineering-api` para dados;
- revisão de todos RQ-*.

Resultado por requisito: `PASS | FAIL | INCONCLUSIVE`.

## 20. Rastreabilidade compacta

| RQ | Evidência | Decisão | Etapa | Prova |
|---|---|---|---|---|
| 01/14/15 | arquitetura oficial + E0 | bounded context/BFF/Core-first | E1/E2 | gates ARCH/AUTHZ |
| 02/13/17 | design system/portais maduros | TopBar + kit-first | E2 | UI tests/smoke |
| 03/09/10/20 | api-delpi/fileserver | ferramentas seguras | E8/E9 | contract/security tests |
| 04/18 | dashboard-lmps | paridade antes de cutover | E7/E12 | parity matrix |
| 05 | Comercial como referência | Sala própria | E5 | API + realtime smoke |
| 06/07 | owners de worklist/requests | agregação sem workflow | E6/E10 | source tests/deep links |
| 08/11 | SI/Transformômetro | preservar owner | E4/E10 | values/source parity |
| 12 | feature-help-sync | Help no entregável | transversal/E11 | structural/content tests |
| 16 | router/URL | deep links persistentes | todas páginas | F5/back tests |
| 19 | docs `.cursor` | rastreabilidade | E0–E13 | verify-final |

## 21. Stop-the-line

Parar a etapa se:

- código atual contradizer o plano;
- owner real for diferente;
- contrato necessário não existir;
- working tree tiver mudança preexistente material sobre o mesmo ownership;
- permission/security ficar ambígua;
- teste exato não puder ser definido;
- uma decisão `NOT_READY` estiver sendo tratada como receita.

Registrar drift e replanejar antes de continuar.

## 22. Todos YAML

```yaml
todos:
  - id: e0-s1-runtime-inventory
    content: Congelar inventário e contratos atuais da Engenharia
    status: pending
  - id: e0-s2-foundation-decisions
    content: Fechar decisões necessárias para fundação/shell
    status: pending
  - id: e1-s1-api-foundation
    content: Criar fundação engineering-api
    status: pending
  - id: e1-s2-core-authz
    content: Implementar AuthZ Core-first fail-closed
    status: pending
  - id: e1-s3-base-gateways
    content: Criar ports/adapters base confirmados
    status: pending
  - id: e2-s1-mfe-foundation
    content: Criar plugins/engineering e façade plugin-ui
    status: pending
  - id: e2-s2-shell-navigation
    content: Implementar TopBar e navegação canônicas
    status: pending
  - id: e2-s3-platform-integration
    content: Integrar manifest RBAC gateway compose
    status: pending
  - id: e3-home
    content: Implementar e fechar Home
    status: pending
  - id: e4-overview
    content: Implementar e fechar Visão geral
    status: pending
  - id: e5-rooms
    content: Implementar e fechar Sala de interação após decisões bloqueantes
    status: pending
  - id: e6-my-tasks
    content: Implementar worklist agregada
    status: pending
  - id: e7-lmps
    content: Implementar LMPs com paridade do legado
    status: pending
  - id: e8-products
    content: Implementar ferramenta Produtos
    status: pending
  - id: e9-documents
    content: Implementar Desenhos e Documentos técnicos autorizados
    status: pending
  - id: e10-integrations
    content: Integrar Controle MP e TRANSFORMA+ sem duplicar owner
    status: pending
  - id: e11-help-audit
    content: Consolidar auditoria de Help e onboarding
    status: pending
  - id: e12-parity-cutover
    content: Homologar paridade e executar cutover autorizado
    status: pending
  - id: e13-verify-final
    content: Provar todos os requisitos do Portal de Engenharia
    status: pending
```

## 23. Primeiro próximo passo

**Somente E0.S1:** revalidar inventário real da `main`, Core e contratos. Nenhum scaffold deve ser criado antes do baseline congelado.


## ADENDO — PRC-N0–N6: plano executável do Product Registration nativo (2026-11-06)

> **Status:** `PLANNED`. **Precedência:** para o vertical Controle e Cadastro de Produtos, este adendo operacionaliza o direcionamento do [ROADMAP.md](./ROADMAP.md) (adendo Native Product Registration). As fases E0–E13 antigas continuam históricas e não autorizam implementar o BFF legado, PRC-1a de token central ou um segundo Request Engine. [Inventário técnico](./PRODUCT-REGISTRATION-COMPLETE-INVENTORY.md) é baseline de paridade, não contrato final.

### Gate zero (obrigatório; nenhum diff produtivo)

- Revalidar `AGENTS.md`, `.cursor`, HEAD, status/worktrees, código real e owners no SHA atual. Planejar PRC em paths novos; **não tocar nos arquivos de desenho/OCR/SLANet/VAL-01**, nem commitar alterações preexistentes de outro agente.
- Aplicar Abstraction Gate sobre `requests-api`: mapear consumers, capacidades de intake, filas, workflow, RBAC, comentários, attachments, schemas JSONB e versões já existentes; propor extensão/adapters em vez de novo engine quando suficiente. **Mudança de owner/source/workflow: `ARCHITECTURE_DECISION_REQUIRED` em Coordination**, com aceite formal antes de writes/migrations.
- Confirmar owner de cadastro técnico e autoridade de produto oficial (TOTVS/Domain API), inclusive quem pode aprovar, publicar, alterar e revogar; não migrar essa autoridade para EVA ou para o frontend.

### PRC-N1 — Contract-first

- Contratos separados: `create` com campos mínimos obrigatórios de solicitação; `update` com `productId`, `baseRevision` e change set explícito por campo. Em update, **não exigir todos os campos**, nem aceitar replacement do objeto completo.
- Definir `requesterSubject` (Keycloak `sub` ou identidade de origem governada), `externalSource`, `externalRequestId`, `sourceItemId`, idempotency, proveniência, response/status/error, live AuthZ e `allowedActions`.
- Catálogo de campos JSONB com `schemaVersion`, validação por tipo/operador, caminhos autorizados, defaults não inventados, campos obrigatórios distintos em **intake vs aprovação/publicação**; confirmar nomenclatura/mapeamento do `compart number` com owner.
- Estados governados e efeitos: `submitted`, `in_progress`, `under_review`, `needs_information`, `rejected`, `completed` (ou equivalentes aprovados); descrever `PREPARE/ACT`, auditoria e postcondition.
- `AC`: create rejeita falta de campo de intake; update de um campo preserva os demais; stale version gera 409 sem write; sem AuthZ é 403; repetição de intake não duplica; rejeição não altera ficha vigente.

### PRC-N2 — Domain + persistence

- No bounded context/owner aprovado, separar solicitação/caso/draft/ficha/revisão. Colunas tipadas para ids/status/atores/códigos/tempo/concurrency; JSONB versionado para atributos variáveis.
- Cada revisão é **snapshot imutável completo** + diff por `fieldPath` antes/depois, autor, timestamp, motivo, solicitação e evidência; rejeição preserva `currentRevision`. Use CAS/ETag/version constraint e audit append-only; não armazenar credenciais em payload.
- Testar replay idempotente, concorrência, renomeação de schema, deep field updates, tipos/arrays/fornecedores e reconstrução íntegra de `N` e `N+1`.

### PRC-N3 — Ingestão e API

- Ingressos de fontes diversas só por portas e contratos autorizados; primeira origem pode ser Control MP, **mas sem dependência de runtime do DB/Flask**. Se exigida ponte temporária, adapter de importação governado é separado do owner do fluxo. Não criar dual-write indefinido.
- Fila paginada/filtros/detalhe/atribuição, provenance e permissions aplicadas no backend; teste de isolamento por usuário, escopo e origem.
- TOTVS permanece fonte oficial. Não declarar criação ou alteração ERP sem contrato de write e pós-condição confirmada.

### PRC-N4 — Frontend nativo

- `plugins/engineering` com área `product-registration` e duas jornadas núcleo: fila/detalhe para analista e solicitação `create/update` por campos autorizados, conforme origem disponível. Labels pt-BR, identifiers EN, `@delpi/plugin-ui`, acessibilidade, light/dark/mobile, reload/deep link/erro/403.
- No formulário `update`, apresentar ficha atual e seleção explícita de campos; enviar somente changes e baseRevision. Não copiar interface/chat legado.

### PRC-N5 — Assistência EVA e resultado governado

- EVA apenas auxilia: valida descrição, consistência, padronização e possíveis problemas com fonte/limitações visíveis; resultado `DRAFT/CANDIDATE`. Sem aprovação automática, source of truth ou escrita oficial. A indisponibilidade da EVA não impede a avaliação humana quando permitido.
- Aprovação humana + confirmação oficial (quando aplicável) precedem `completed`/revisão publicada; rastrear owner, código, evidências e read-back.

### PRC-N6 — Paridade, migração, cutover

- Usar inventário 51 rotas/11 tags e histórico como referência de paridade, **não reproduzir os defeitos legados**. Migrar dados por ETL versionada, dry-run e apply idempotente, preservando IDs legados, `sub`, snapshots originais, eventos, anexos/checksums, autoria e resultados; relatório de reconciliação.
- Implantação nativa em piloto isolado, legado permanece autoridade até cutover assinado; congelamento de escrita ou delta auditado, validação por amostragem, rollback de operação e plano de retenção sem drop prematuro.

### Sequência e responsabilidade

`N0` → aceite arquitetural → `N1` contrato aprovado → `N2` domínio persistência → `N3` intake/API → `N4` UI → `N5` EVA assistiva/decisão → `N6` migração/cutover. Etapas podem ser desenvolvidas em branches separadas quando paths não colidem, mas somente promovidas após gates integrados.

**Arquivos compartilhados** (`engineering-api/engineering_app/main.py`, `config.py`, `plugins/engineering/src/App.tsx`, `engineeringRoutes.ts`, `engineeringRouteCatalog.ts`, manifest, Core/RBAC e CI/deploy): serializar merge por integrador designado após a frente VAL-01. Testar ambos no mesmo SHA e registrar `HEAD/DIFF/TESTS/DEPLOY_DIGEST`. **Sem deploy autorizado por este adendo.**


## ADENDO — PRC Engineering-only: execução sem Requests API no MVP (2026-11-06)

> **Precedência operacional:** atualiza PRC-N0–N6. O roadmap mestre [ROADMAP.md](./ROADMAP.md) determina **Engineering API como contexto de implementação inicial**, sem conexão runtime com `requests-api`, `my-requests` ou API Flask do Controle MP. Não executar PRC-1a de delegação de JWT do legado. Os documentos anteriores ficam apenas como evidência histórica e base de migração futura.

**PRC-N0 — Architecture/Contract Gate:** confirmar propriedade de intake, fila, casos, histórico e ficha técnica **em Engenharia**, registrar `ARCHITECTURE_DECISION_REQUIRED` para nova autoridade de workflow, sem transferir authority de cadastro oficial do TOTVS; não criar dependências de runtime de Requests API. Inventariar equivalentes já encontrados apenas como avaliação de duplicação; não ampliar scope. Ler HEAD/status e isolar arquivos em paralelo à VAL-01.

**PRC-N1 — Contract-first:** duas portas versionadas da `engineering-api`: intake (`create` e `update` por campo, solicitante/origem/idempotency) e outbound de status/resultado (consulta e/ou notificação conforme consumidor real). Definir schemas JSONB versionados, required intake vs required official registration, states, allowedActions, AuthZ live, concorrência CAS/ETag, errors, auditoria, idempotência, rate/size limits, observabilidade, revisões. Confirmar significado de "compart number" com owner.

**PRC-N2 — Domain/Persistence:** criar módulo próprio da `engineering-api` para requests/cases/drafts/technical records/revisions, snapshots JSONB imutáveis, diff por campo e ledger append-only; migrations exclusivas da Engenharia, sem copiar banco legado; testes de replay/CAS/isolamento.

**PRC-N3 — HTTP/API:** implementar intake e saída oficiais, além de listagem/detalhe/ações internas autorizadas para analistas. Nenhum endpoint da Requests API como downstream do MVP; nenhum BFF legado. Confirmar critérios de source identity e postcondition.

**PRC-N4 — Frontend:** no `plugins/engineering`, fila, detalhe, create com obrigatórios de solicitação e update seletivo por field path, histórico/revisões, mensagens pt-BR e rotas técnicas em inglês. UI chama somente `engineering-api`.

**PRC-N5 — Técnico/resultado:** assistência EVA `DRAFT/CANDIDATE` opcional, decisão do analista, confirmação oficial por Domain API autorizada; não marcar `completed` nem publicar revisão oficial sem evidência do resultado.

**PRC-N6 — Posterior, fora do MVP:** somente depois de sistema funcional e paridade, planejar integração com `requests-api` e/ou importação governada dos dados Controle MP (dry-run, idempotência, reconciliação, anexos, identificação/retention, cutover, rollback). Não realizar migração agora.

**Gates de colaboração:** todo diff em arquivos compartilhados com VAL-01 fica para integrador designado e teste em SHA único. Não alterar drawing/OCR/SLANet/comparadores/jobs. **Esta revisão é apenas documental; não há deploy.**


## ADENDO — PRC: verificação oficial obrigatória antes de Concluir (2026-11-06)

> **Atualização executável dos gates PRC-N1–N5** conforme direção mais recente do Product Owner. O MVP roda dentro da `engineering-api` e `plugins/engineering`; `requests-api` e Controle MP não são downstreams runtime. O cadastro oficial no TOTVS é **manual** e a Engenharia somente lê/verifica o resultado antes de concluir.

**N1 — contrato/schema.** Transpor o catálogo de 11 tags do inventário legado para schemas nativos de `create` e `update`: `codigo_atual`, `novo_codigo`, `grupo`, `descricao`, `tipo`, `armazem_padrao`, `unidade`, `produto_terceiro`, `cta_contabil`, `ref_cliente`, `fornecedores` incluindo `supplier_code/store/supplier_name/part_number/catalog_number`. Nome correto é **Part Number**; nome técnico `part_number`. Diferenciar required de intake, required para o analista e required para publicação; validar backend, sem herdar cegamente defaults ou restrições apenas visuais do legado. Contratos `intake` e `outbound` versionados, origin/actor, idempotência, AuthZ e errors. Aprovar mapeamento de cada campo ao retorno ERP antes de declarar contrato de conclusão pronto.

**N2 — persistência.** Contexto de Engenharia: solicitações/casos, ficha JSONB com `schemaVersion`, base revision e change set seletivo, snapshots imutáveis, auditoria por campo, revisão vigente apontada apenas após confirmação; status intermediário explícito para cadastro ERP realizado/aguardando verificação. CAS/409 e idempotência de Concluir.

**N3 — endpoints.** Porta de chegada versionada capaz de receber `create/update` de origem autenticada, mesmo sem connector externo; porta de saída versionada de leitura de resultado/status/revisão para consumidores autorizados; APIs internas da fila, detalhe, ações e consulta. Testes de intake por harness autenticado ou formulário **somente de teste**, sem registrar plugin externo. Sem chamadas à `requests-api` ou Flask.

**N4 — UI.** Fila, detalhe, ficha, seleção de campos update e histórico; botão Concluir chama operação única backend de **verificar no TOTVS e concluir**. Se não houver produto/alteração oficial, UI mostra código/campos divergentes e mantém caso aberto; sem sucesso otimista. Sem chat legado. Revisar componente UI do form de teste para não criar rota pública sem permissão.

**N5 — verificação e outcome.** Integrar somente contrato autorizado de leitura `api-delpi`/Domain API: lookup código + validação de valores campo a campo (inclusive `part_number` e fornecedores quando exigidos), normalização tipada documentada, sem assumir que existe endpoint que não foi comprovado. `create` exige produto oficial presente e ficha válida; `update` exige mudanças oficiais correspondentes. Falha/timeout/campo inacessível → não concluir. Aprovação humana/autorização live + read-back + audit/evidence da consulta antes de marcar `completed` e publicar snapshot como revisão vigente. Não fazer write ERP. EVA opcional candidata, sem confirmação automática.

**Tests/quality gates:** inexistência código, código certo com descrição divergente, alteração de 1 de N campos, fornecedor/Part Number divergente, dois analistas, repetição de Concluir, stale baseRevision, 403, timeout/502, falta de campo no contrato API, fingerprint da evidência ERP, nenhuma revisão vigente em falha. Testes em SHA específico; rollback/revoke se necessário. **Shared-file gate** com VAL-01 para `main.py`, `config.py`, router, manifest e deploy.

**Futuro:** integração a `requests-api`, fontes externas, similaridade no intake e automação de escrita TOTVS — tudo fora da etapa inicial.


## Referência executável do vertical Product Registration — 2026-11-06

A especificação de rotas, payloads, PostgreSQL/JSONB, regras de transição, verificação TOTVS e critérios de aceite do MVP Engineering-only está em [PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md](./PRODUCT-REGISTRATION-MVP-TECHNICAL-CONTRACT.md). **Para este vertical, o contrato mais recente prevalece sobre exemplos e premissas históricas de BFF legado, My Requests e proibições de persistir workflow do antigo Controle MP.** Não altera outros domínios; ownership ainda exige `ARCHITECTURE_DECISION_REQUIRED` e a escrita ERP continua fora do escopo. A fase atual é documentação, sem código ou deploy.


## Plano transversal de capacidades EVA — Product Registration (2026-11-06)

A paridade **Portal/REST/EVA** integra cada slice deste vertical: para cada capacidade legítima do usuário, conectar uma ação `(entity, action)` ao **mesmo caso de uso** nas **seis tools semânticas existentes**, sem nova tool nem bypass de Core/Domain AuthZ. Matriz das 18 rotas, ações `product_registration.*`, riscos `read/execute`, PREPARE/ACT, confirmação humana para rejeição/conclusão, testes e integração serializada com VAL-01 em [PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md](./PRODUCT-REGISTRATION-EVA-SEMANTIC-INTEGRATION.md). O documento é `TARGET/PLANNED`, não evidência de runtime. EVA não aprova produto nem escreve no TOTVS e não pode contornar a verificação oficial na conclusão. A publicação de uma rota humana requer cobertura semântica testada ou `PARITY_GAP` explicitamente bloqueado/aceito em release governado.


## ADENDO — PRC-C0..C3: primeira entrega executável do Product Registration (2026-11-06, SHA 773332c110)

> **Status:** `PRC-C1..C3 IMPLEMENTED / TESTED / PUSHED`; `PRC-C4 PARITY_GAP (dispatch EVA + UI + manifest)`; `PRC-C5 PENDING`; `DEPLOY_NOT_AUTHORIZED`.

**PRC-C0 gates:** B (persistência/migrations) `PROVEN` — schema `engineering` no plugins_hub, runner de checksum (`api-delpi/migrations/plugins/engineering`, V012 criada), role dedicada `eng_prc` (`db/eng_prc_grants.sql`), adapters `ENG_PRC_REPOSITORY`/`ENG_PRC_DB_*`. A (ownership operacional) `ARCHITECTURE_DECISION_REQUIRED` registrado. D (contrato TOTVS) `CONTRACT_GAP_PARTIAL` — `view=engineering` cobre descrição/tipo/grupo/unidade/TPMAT/armazém/ref-cliente + SA5 (partNumber/catalog); `accountingAccount` (B1_CONTA) fora da view → `unverifiable`. E (permissões) `AUTHZ_CONTRACT_PENDING` — códigos `engineering.product-registration.{read,create,process,verify,admin}` implementados fail-closed; registro no manifest pendente. C/F `OWNER_SIGNOFF_PENDING`.

**Entregue:** domínio (catálogo de campos, state machine, comparação oficial), ports, adapters Postgres/in-memory/unavailable, `OfficialProductReader` delegado (SB1+SA5, read-only, sem escrita ERP), service com intake/queue/workflow/verify/outbound, 18 rotas REST `/v1/product-registration`, registro EVA `product_registration.*` (18 ações, `status=planned` — não executáveis até dispatch integrado). 25 testes novos + 98 no conjunto de regressão executado — `PASS`.

**Pendente (próximo incremento seguro):** dispatch EVA em `semantic_bridge.py`/`tool_bridge.py` (serialização VAL-01), UI em `plugins/engineering`, permissões no `engineering.manifest.json`, grants/migration aplicados pelo operador, homologação TOTVS real (PRC-C5).


## Gate de implementação — BFF exclusivo para leitura TOTVS (2026-11-06)

> **Decisão explícita do Product Owner, prevalente para Product Registration:** toda busca, consulta, lookup, conferência de atributos, fornecedores/Part Number e validação de conclusão baseada no TOTVS **deve passar pelo BFF da `engineering-api`, que consome exclusivamente contratos oficiais da `api-delpi`**, com identidade delegada e autorização do usuário. A `api-delpi` é owner da integração/consulta ao TOTVS; a Engineering API adapta o contrato para os casos de uso de Engenharia. Nem `plugins/engineering` nem a EVA acessam diretamente TOTVS, banco SQL/ODBC, API Flask do Controle MP ou `api-delpi` contornando o BFF de Engenharia.

Fluxo autorizado: `Portal ou EVA -> Engineering API (REST ou mesma application use case via ações semânticas) -> OfficialProductReader adapter -> api-delpi /products/* (read-only) -> TOTVS`. Para EVA, usar os mesmos ports/use cases e AuthZ, **sem novas tools MCP**; não duplicar HTTP call no handler semântico. Sem escrita ERP neste MVP: analista realiza criação/alteração manual no TOTVS; `verify-and-complete` lê resultado pela `api-delpi`, compara campos, e só conclui quando todos os campos exigidos são comprovados.

**Gate D / lacuna atual:** o relatório PRC-C3 indica que `B1_CONTA` (`accountingAccount`) não é exposto pela view `engineering` embora outros atributos e SA5/Part Number estejam disponíveis. Resolver **no contrato/owner `api-delpi`**, verificando escopo/autorizações, ou propor view oficial apropriada; não adicionar acesso SQL/TOTVS direto à Engineering API e não relaxar comparação. Enquanto qualquer campo obrigatório não for verificável via `api-delpi`, bloquear `completed` (fail-closed, erro `unverifiable`). Aprovação de novo campo/view é do owner da API e das permissões, não do BFF.

**Critérios de aceite:** busca e verificação usam somente adapter oficial `api-delpi`; autorização humana propagada; ausência/403/timeout/campo omitido produzem status honesto sem revisão publicada; testes REST/EVA usam mesmo caso de uso e demonstram ausência de SQL direto, de escrita ERP e de downstream legado. Qualquer mudança nessa fronteira exige `ARCHITECTURE_DECISION_REQUIRED`. **Documentação apenas; sem deploy, migration ou mudança de código nesta atualização.**


## Decisão aprovada do Product Owner — PRC RBAC, BFF e HML (2026-11-06; vigente)

**Leia antes de implementar:** [PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md](./PRODUCT-REGISTRATION-PO-DECISIONS-2026-11-06.md). Esta decisão **substitui** as propostas anteriores de cinco permissões `engineering.product-registration.*` e a premissa de que `engineering.access` não autoriza o CRUD do módulo. Modelo vigente: `engineering.access` para CRUD/workflow operacional e `engineering.manager` para administração, com AuthZ backend live, escopo/identidade e invariantes de domínio intactos. **Ainda não implementado no PRC/Core; não alegar RBAC pronto.** Engenharia é owner do workflow e `api-delpi` é owner da leitura oficial TOTVS; autorizado estender `B1_CONTA` na `api-delpi` (inclusive SQL interno, sem bypass pela Engenharia). HML autorizada **condicionalmente** à execução por operadores habilitados, gates e testes; produção não autorizada. Merge markers PRODUCTS corrigidos na `main`, porém build/typecheck completos devem ser executados para comprovar integração.


## ADENDO — PRC-D1..D3: decisões PO implementadas (2026-11-06, SHA 949ef1b286)

> **Status:** `PRC-D1 PASS / PRC-D2 IMPLEMENTED+TESTED / PRC-D3 IMPLEMENTED+TESTED / PRC-D4 PENDING_OPERATOR / PRC-D5 PARTIAL / PROD NOT_AUTHORIZED`.

**PRC-D1 (build):** conflito PRODUCTS corrigido pelo owner (4 arquivos); `index.css` continha 5º marker commitado — resolvido preservando `Updated upstream` + regras únicas do lado stash (`.engineering-product-tree*`, `.engineering-product-drawing-frame`) que a página de detalhe usa. Arquivos de suporte products (api/copy/types) restaurados ao estado consistente com as páginas upstream. Resultado: `typecheck PASS`, `vite build PASS`, vitest `199/199 PASS`.

**PRC-D2 (RBAC):** modelo de duas permissões implementado conforme decisão PO — `engineering.access` abre consulta/criação/draft/workflow/verify-and-complete; `engineering.manager` declarado em `engineering.manifest.json` (admin fail-closed, sem operação exposta). Removidas as cinco `engineering.product-registration.*` de rotas, ator, catálogo, reference-data e testes. Fila global para todo portador de access (sem perfil oculto). Sem-access → 403 (fail-closed, testado).

**PRC-D3 (B1_CONTA):** `accounting_account` incluído em `PRODUCT_DETAIL_ENGINEERING_FIELDS` (api-delpi, owner autorizado); já era retornado pelo SQL (`SB1.B1_CONTA AS accounting_account`). `accountingAccount` virou `verifiable=True` no catálogo PRC — `verify_and_complete` agora compara a conta contábil. BFF inalterado: Portal/EVA → Engineering API → api-delpi → TOTVS. 51 testes api-delpi da família passaram.

**Pendente:** migration V012 + grants em HML por operador (`PENDING_OPERATOR`); homologação TOTVS real e E2E browser/MCP transport (`TEST_NOT_RUN`); promoção incremental das 13 ações EVA `planned`; required fields/freshness (gates C/F do PO).


## ADENDO — PRC-D4/D5: validação HML (dev stack) em PostgreSQL real (SHA pendente)

> **Status:** `POSTGRES V012+GRANTS APPLIED (dev plugins_hub) / REAL-PG TESTS PASS / CORE manager PENDING_SYNC / TOTVS real + browser + MCP transport TEST_NOT_RUN`.

Ambiente usado: stack dev local (containers delpi-*), banco descartável `plugins_hub` — equivale ao gate de HML autorizado para evidência técnica, **não** homologação de produção.

- `V012` aplicada via psql no `plugins_hub` e registrada em `engineering.schema_migrations` (checksum sha256 do arquivo). 7 tabelas `product_registration_*` existentes.
- `eng_prc_grants.sql` aplicado — role `eng_prc` criada com grants mínimos. Verificado no DB: `UPDATE` em `product_registration_revisions` por `eng_prc` → **permission denied** (append-only real, não só por contrato).
- Novo `tests/test_prc_postgres_integration.py` (skip sem `ENG_PRC_TEST_DSN`): fluxo completo real — create → start → CAS 409 → draft seletivo preservando campos → review → `complete_request` atômica (record+revision+verification+evento) → revision imutável persistida → timeline sequencial; unicidade de referência externa → `PrcDuplicateError`; idempotência roundtrip. **3/3 PASS em PostgreSQL 15 real.**
- Core: `engineering.access` presente na tabela `permissions`; `engineering.manager` ausente → `PENDING_CORE_SYNC` (manifest declarado, sync pelo pipeline/owner Core).
- Não executados (sem acesso autorizado nesta sessão): leitura TOTVS real via api-delpi (`B1_CONTA` em produção/HML real), browser E2E, transporte MCP/elicitation real.
