# 40 — Matriz de Dependências e Backlog de Slices V1

**Estado:** TARGET / PLANNED / TEST_NOT_RUN — execução não autorizada. Leia primeiro [39 — Roadmap Mestre](./39-roadmap-mestre-implementacao-v1.md), [23 — RQ/AC](./23-ledger-rq-ac-testes.md) e [38 — gate](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md).

## 1. Semântica do backlog

- Os códigos **IMP-\*** identificam *unidades de planejamento* futuras, **não** novas permissions, endpoints, tabelas ou estados de negócio.
- `G-DOC + G-FREEZE + G-AUTH` devem estar aprovados **antes de qualquer IMP com código runtime**. IMP-00 pode ser inventário/revisão documental até a autorização, sem scaffold.
- Uma linha não autoriza implementar páginas seguintes; abrir brief e PR para o menor comportamento do contexto owner. Revalidar HEAD, `git status`, regras .cursor, producers/consumers, contratos físicos, RQ/AC, safety e Help a cada slice.
- `PROVEN` exige evidência de source/CI e `PASS` de comportamento exige testes executados na revisão atual. Ausência de arquivo numa busca é **TO_INVENTORY**, não inexistência definitiva.
- Ordem é baseline; somente mudar por dependência material demonstrada, preservando review, brief e stop line. Não converter estrutura deste plano em escolha de produto.

## 2. Grafo de dependências e owners

| Produtor / authority | Contrato consumer | Slices afetados | Inventário / stop |
|---|---|---|---|
| Core — Keycloak identity, effective permissions, usuários e foto | BFF do Portal expõe dados autorizados; browser não acessa contracts de plataforma indevidamente | A01, A02–A07, P1–P6 | T05: permission code PROVEN no source; atributos corporativos e vínculo de área **TO_INVENTORY**, fail-closed |
| Core — notifications | Evento de responsabilidade/revisão → aviso; falha de e-mail não modifica negócio | P2/P5, Sala, tarefas e Administração | T02/Core capability identificada; adapter idempotente, preferências, retry e escopo a provar |
| P6 — templates, catálogos, áreas obrigatórias versionadas | P2 congela requisitos; P5 congela required-area snapshot por tipo de pacote | P2, P5, P6 | E01/E05/E06, vigência, OCC, owner e seeds; contrato semântico P5-H/DEC-04 aprovado |
| api-delpi / owner ERP TOTVS | P3 obtém dados canônicos e status de estoque, não escreve ERP | P3, P1, Visão geral | T03: owner/source/status `STOCK_CLOSED` canônico obrigatório; paridade R$ 0,00 |
| strategic-indicators-api | Visão geral consome metas/indicadores governados sem recalcular fórmulas | Visão geral | O04/O05: owner, source, unidade, fórmulas, freshness |
| Product BFF P2/P4/P5 | Minhas tarefas cria **TaskProjections**, não TaskEntity; usuário navega ao owner | Minhas tarefas / Início / P2 / P4 / P5 | TSK01–TSK05: projection self-only; P5 obligations **por área**, elegibilidade por usuário |
| Owner da Sala / contexto | Sala contextual, membership/mentions/links e atividade | Sala, P1–P5 | R01–R05: authz de contexto, armazenamento/realtime/retention sem adivinhação |
| `@delpi/plugin-ui` / Portal principal | Page families, profile page, task workspace, room, manual, navegação e design system | Todas | Ver [30](./30-plugin-ui-reuse-map.md); não duplicar kit, chrome, modal host ou autorização |

**Boundary de segurança:** JWT apenas identifica; Core resolve effective permissions; BFF autoriza com capability **AND** scope/ownership **AND** regra de negócio. Para aceite P5, adicionar elegibilidade de função/grupo/área e versão. `controllership-finance.manage` **não** implica `.access`; filial/unidade não é permission code. Falhas em Core/owner relevante devem negar ação sensível, sem fallback permissivo.

## 3. Fila única de entregas — preparação e superfícies comuns

| ID / sequência | Slice e authority principal | Contrato/AC selecionados | Pré-requisitos e STOP material | Evidence/exit do slice |
|---|---|---|---|---|
| IMP-00 — documental | Inventário e gate A12/A14/A15/A16; [33](./33-plano-mestre-fechamento-documental.md), [38](./38-rebaseline-pos-merge-evidencias-gate-2026-10-16.md) | Owners, E/T, Core T05, P6/P5 semântica, fonte T03, branches, test matrix, four freezes | Qualquer decision/owner/binding material não provado = PENDING/DECISION_REQUIRED; **sem runtime** | Ata A16, SHA, status real, autorização PO explícita |
| IMP-01 — A01 | [Página do usuário](./31-pagina-do-usuario.md) (deep route, sem item topbar) | RQ-USER-01..09; D1=B, D2=A; identidade/foto Core, edição externa no Meu Perfil | Primeiro slice só após gate; plugin-ui, Core S2S, BFF AuthZ, photo proxy, no RBAC de outro usuário; sem persistência local | Tela self/other com falha fechada, states, deep link/F5, Help, tests |
| IMP-02 — A02 | [Início](./32-inicio-home.md) | RQ-HOME-01..09, RQ-NAV-01; Hero operacional, catálogo ativo, recentes, favoritos | H01/H02/H03/H04; catálogo só de rotas implementadas e autorizadas; favoritos não inventar persistence | Home família padrão, filtros, failure/partial por source, topbar/Help |
| IMP-03 — A03 | [Visão geral](./25-visao-geral-indicadores-financeiros.md) | RQ-OVW-01..10; indicadores governados, competência/mês vigente, Consolidado | O04/O05: source/fórmula estratégica, filtros, DTOs BFF, freshness; **STOP** se inventar fórmula, meta ou zero | KPI/charts/drilldown consistentes com owner; sibling partial, UX |
| IMP-04 — A04 | [Minhas tarefas](./27-minhas-tarefas.md) | RQ-TASK-01..12; TaskProjection **self-only** e link ao owner | TSK01–TSK05; producers reais; P5 por área quando owner implementado; sem TaskEntity ou SLA global | Lista/filtros/deep link; coverage partial honesta e source-only |
| IMP-05 — A05 | [Sala de interação](./26-sala-de-interacao.md) | RQ-ROOM-01..12; contextual, não altera negócio | R01–R05; authz de contexto, transport, storage, retention, mentions; sem criar task V1 | Messages, ACL negative, outages degradáveis, feedback e Help |
| IMP-06 — A06 | [Administração](./28-administracao.md) — common admin surface | RQ-ADM-01..12; Painel/Templates/Catálogos/Histórico | MANAGE + administrative_scope; ADM01–ADM07; sem user/role write local; P6 owner | Templates/catálogos com publish/version/audit, concurrency e snapshots quando ativados |
| IMP-07 — A07 | [Ajuda](./29-ajuda.md) — superfície completa | RQ-HELP-01..12; manual tipado, navigation e links seguros | Feature/route gating; nenhum conteúdo antecipando capabilities não publicadas | Manual navegável/teclado/tema, apenas conteúdos de runtime; **não** substitui Help sync nas PRs anteriores |

**Nota sobre IMP-04:** o ledger histórico ainda chama P5 “conditional”; o contrato posterior [37](./37-p5-submissao-e-revisao-no-portal.md) e [27](./27-minhas-tarefas.md) estabeleceu projeções por **área obrigatória** para cada usuário elegível, quando o review é acionável. Implementar apenas quando P5 owner real existir, sem fabricar tarefa desde IMP-04.

## 4. Fila única — Central de Fechamento

| ID / sequência | Página / authority | RQ/AC selecionados | Pré-requisitos/stop | Exit verificável |
|---|---|---|---|---|
| IMP-08 — A08 / P1 | [Cockpit da competência](./08-p1-cockpit-da-competencia.md) | RQ-P1-01..07; composição de P2/P3/P4/P5 | T01/T05; não recriar source owner nem inferir sucesso de HTTP 200 | Readiness, axes, blockers, source unavailable, drilldown correto |
| IMP-09 — A09 / P2 | [Checklist e documentos](./09-p2-checklist-e-documentos.md) | RQ-P2-01..12; requirements, evidência/versões, validação | P6 contract de catálogo/template/snapshot (E05/E06); T05 eligibility e storage/versioning reais | Upload != validação; replacement/NA/cancel com auditoria; negativas |
| IMP-10 — A10 / P3 | [Estoque, cutoff, conciliação](./10-p3-estoque-cutoff-e-conciliacao.md), [15.1 — paridade](./15.1-p3-criterios-paridade-monetaria.md) | RQ-P3-01..10 (inclui RQ-P3-08A); E02 `STOCK_CLOSED` terminal; tolerância **R$ 0,00** | T03 owner/endpoint TOTVS, reconciliation sources; sem sacramentar ERP; se source desconhecida, **STOP** | Status canônico, revalidação temporal, diferença exatamente zero e negativos por source |
| IMP-11 — A11 / P4 | [Classificações e pendências](./11-p4-classificacoes-e-pendencias.md) | RQ-P4-01..08; classificação e tratamento de pendência | T01/T05 e owner do centro de custo; sem duplicar regras de api-delpi | Origem/proveniência, ações autorizadas, states de pendência e auditoria |
| IMP-12 — A12 / P5 | [Pacotes](./12-p5-pacote-finalizacao-e-envio.md) + [submissão/revisão](./37-p5-submissao-e-revisao-no-portal.md) | RQ-P5-01..12; RQ-P5-AREA-01..04; RQ-P5-TERM-01..03; C2 / P5-A..J / DEC-01..03 | **BLOCKED até** T05 grupos/funções, coordenação, areas-by-package-type P6 e snapshot, contracts de estados/DTOs/eventos/OCC, notifications/tasks e scope | Finalize != submit, PackageVersion imutável, 1 aceite/área/versão, decline/terminal formal, audit e task projection |
| IMP-13 — A13 / P6 | [Administração e configuração P6](./13-p6-administracao-e-configuracao.md) + [28](./28-administracao.md) | RQ-P6-01..10; RQ-ADM-01..12; DEC-04 | E01/E05/E06, version/validity, MANAGE+administrative_scope, stale revision; snapshot P2/P5 | Nova configuração prospectiva, audit, sem retroatividade ou hard delete, testado com P2/P5 |

**Fatiamento especial P5:** o planejamento pode abrir sub-slices **IMP-12a** finalização/versão, **IMP-12b** submissão interna e reviewer eligibility, **IMP-12c** acceptance/clarification/rejection, **IMP-12d** conclusão C2/projections. Cada sub-slice requer contrato completo próprio e teste de fronteira/segurança. **Nunca** “entregar envio” parcial com revisão desautorizada ou fingir completion.

**Fatiamento especial P6:** o **contrato semântico** de configuração de required areas deve estar disponível antes de submissão P5, mesmo que a **UI P6 completa** seja IMP-13. Se o owner P6 exigir implementação física antecipada, registrar um **micro-slice predecessor** no owner correto, com gate/AC/autorização próprios; não reordenar silenciosamente nem adicionar CRUD genérico.

## 5. Famílias de inventário com stop conditions

| ID / risco | O que provar antes do consumer | Não inferir / workaround proibido |
|---|---|---|
| T01 — composição | owner de cada KPI/eixo, contrato e provenance/period | SQL no BFF ou recomputação de indicador sem owner |
| T02 — notificação | Core delivery/notification API, preferências e idempotência, destinatário permitido | e-mail transacional como outcome da submissão ou SMTP local |
| T03 — Estoque ERP | fonte/produtor de cutoff, conciliação, status `STOCK_CLOSED` | repetir regra TOTVS ou escrita ERP direta |
| T04/E04 — legacy delivery | envio P5 portal-first, external attachment NOT_REQUIRED_IN_V1 | reabrir entrega por e-mail de anexo por histórico antigo |
| T05 — identidade/permissions | effective-access via Core, associação corporativa grupo/função→área, escopo/coordenação P5 | RBAC por página/filial/reviewer; JWT/front decide eligibility |
| E01/E05/E06 — catálogos/seeds | catálogo configurável, ownership, versão, vigência, snapshots | hardcode de catálogo, retroatividade, migração especulativa |
| H01–H04, O04/O05 | favoritos, eventos/tasks, indicador/fórmula e contract/freshness | “zero” ou gráfico estimado em source unavailable |
| TSK01–TSK05 | producer→TaskProjection, coverage, self-only, deep link | TaskEntity local, seleção de usuário alheio, SLA fabricado |
| R01–R05 | contexto e ACL, retention, storage, realtime, mentions/notificações | sala global, attachment como evidence, task a partir de mensagem |
| ADM01–ADM07 / HELP01–HELP04 | registry, auditoria, concorrência, versões; manual no kit | CMS/backend Help V1 ou duplicar chrome do kit |

**Classificação padrão:** `TO_INVENTORY` até autoridade verificada, `PLANNED` para roteiros sem execução, `TARGET` para decisões aprovadas; nenhum item muda para `PROVEN` ou `PASS` só porque está listado.

## 6. Critério de dependência pronta para um slice

Para cada seta X→Y: (1) contrato canônico X e owner; (2) evidence source e, se pertinente, endpoint/DTO/evento; (3) filtro AuthZ/scope; (4) version/currency/time/freshness; (5) erro/fail-closed, idempotência/OCC em writes; (6) testes producer, consumer e sibling; (7) Help/no-regression; (8) link ao commit/SHA. **Se não existir prova, marcar Y BLOCKED, não preencher design por preferência.**

## 7. Rastreabilidade e acompanhamento

Registrar uma linha por IMP (e por sub-slice aprovado) no relatório de execução do [42](./42-playbook-brief-cursor-execution-report-v1.md): `IMP_ID | base_SHA | git_status | RQ/AC | dependencies | owner | evidence | commit_SHA | CI | test_status | postcondition | review_result | next`.

Nunca estimar percentual “pronto” por quantidade de rotas ou documentos. Sem gate transversal: todos os IMP de runtime ficam **PLANNED / NOT_STARTED**.