# Portal Controladoria & Finanças (controllership-finance)

Microfrontend do Portal Controladoria & Finanças — Minha DELPI.

- **Plugin id:** `controllership-finance`
- **Base path:** `/apps/controllership-finance`
- **BFF:** `controllership-finance-api` (`/apps/controllership-finance-api`)
- **Permissions:** `controllership-finance.access`,
  `controllership-finance.manage`,
  `controllership-finance.access.dre`
  (RW03 — a legada `closing-documents.read` foi removida após a
  migração comprovada do papel DRE no Core, doc 115 §11)

Escopo entregue (IMP-MFE-HOME + IMP-CF-R01-R02-D3-UI-01): bootstrap
federado, manifesto, shell de navegação, Home com saudação/estados
honestos, catálogo somente de rotas implementadas, busca `?q=`, últimos
acessos locais e ajuda contextual.

Central de Fechamento — Baixas financeiras (R01/R02): rota interna
`closing/financial-settlements` com visão pagar/receber, filtros de
período/natureza/movimento, resumo por moeda (`officialTotals=false` —
nunca soma moedas nem declara fechamento oficial), tabela paginada no
servidor e estado tipado `scope_unavailable` quando o dataset D3 ainda
não está habilitado no ambiente. Filial sem origem rende
«Não identificada» — nunca fallback 01/02.

Central de Fechamento — Estoque P7 (R03): rota interna
`closing/stock-inventory` com motor único — `EM ESTOQUE` (SB9 ex-
armazém de processo) + `EM PROCESSO` (MATR989 `as_of`), seleção
«Todos os produtos» × «MP, PA e PI — DRE» (`report_scope=
all_products|mp_pi_pa`), export CSV/PDF com metadados/hash e marca
não-oficial (`officialP7=false`, `parityStatus=PENDING` — não é o
relatório oficial MATR460 homologado). Estados tipados `available` /
`incomplete` / `source_missing` / `no_matching_items`; snapshot
ausente exibe apenas banner — nunca tabela vazia (ausência não é
saldo zero).

Central de Fechamento — Entradas e Saídas R05 + Material em Processo
R08 (IMPLEMENTATION-009): rotas internas `closing/stock-movements` e
`closing/work-in-process`, consultáveis por mês de referência +
filial autorizada **sem competência formal, checklist, documentos ou
pacote DRE** (DEC-ANALYTICS-INDEPENDENCE). R05 = matriz MATR320 por
tipo de produto; R08 = físico loc99 + alocado `RE−DE` (mesmo motor
MATR989 do P7). Ambos exportam CSV/PDF com selo `parityStatus=PENDING`
(`officialMatr320=false`, `officialMatr989=false`). A aba exibe ainda
a **conciliação analítica** `closing/analytics/stock-reconciliation`
— `E/S − P7 − H02` calculada só quando os três operandos estão
disponíveis na mesma competência, filial e data-base (ausente ≠ zero;
referência divergente → `INELIGIBLE`), `governedReconciliation=not_persisted`,
declarada na UI como «não substitui a conciliação governada (P3)».
REWORK-010: os operandos são partições do mesmo universo SB9 —
delta zero reporta `IDENTITY_ONLY` («Composição dos saldos
consistente», controle de integridade interno) e
`reconciliationVerdict=INCONCLUSIVE`; nunca `EXACT_PARITY` — a
paridade entre os relatórios oficiais independentes segue pendente
de homologação. Delta ≠ zero reporta `DIVERGENCE` real da composição.

Central de Fechamento — Relatórios e divergências (aba `?tab=reports`):
hub de análise com indicadores honestos, atenção primeiro e cartões por
relatório; cada cartão abre página contextual
`closing/monthly-closing/{YYYY-MM}/reports/{reportKey}`
(`financial-settlements` | `stock-inventory` | `stock-movements` |
`work-in-process`) dentro do próprio Fechamento mensal — as páginas
legadas são reutilizadas em modo `reportContext` com competência
travada, agrupamentos em tabelas por colunas e export CSV/PDF real.
O retorno restaura competência, aba e família analisada; a matriz
R01–R15 permanece como rastreabilidade técnica recolhida.
REWORK-008: os estados das fontes da conciliação distinguem
disponibilidade operacional de elegibilidade P3 — `fetched_at` nulo
(domínio nunca registrado no workflow governado) exibe «Fonte não
registrada»/«Não registrada»; P7 sem `AVAILABLE` com consulta
operacional respondendo exibe «Conciliação pendente» + «consulta
disponível». Consulta disponível não equivale a fonte elegível, e
domínio sem validação nunca é lido como divergência zero.
REWORK-011: a distinção consulta-operacional × elegibilidade P3 foi
estendida de P7 para R05 e R08 usando os operandos da conciliação
analítica — «Consulta disponível — conciliação pendente»,
«Posição histórica ainda não disponível» (snapshot SB9 ausente,
diferente de falha técnica), «Falha ao consultar a fonte» e
«Dados incompletos»; a fonte P3 registrada permanece autoritativa.
O indicador «Divergências identificadas» só exibe número comprovado:
`0` exige todas as conferências concluídas; verificações pendentes
mostram `—` «não verificadas» — `INCONCLUSIVE` nunca vira zero.
RW01: os filtros vigentes das páginas contextuais são serializados na
própria URL da rota (`reportQueryParams.ts` — `side`, datas, natureza,
movimento, ordenação e página para Baixas; `branch`, `scope`, `warehouse`
e página para Estoque) — F5, deep link e voltar/avançar restauram o
contexto, datas fora da competência da rota são descartadas e filtros
da última família só retornam na reabertura dela (sem vazamento entre
relatórios).

Central de Fechamento — Documentos do fechamento (UX-012): catálogo
mestre administrativo em `closing/admin/documents` (MANAGE). A listagem
deriva cada tipo de documento (`item_key`) da timeline de versões
publicadas do checklist mestre — janelas de vigência, situação
(vigente/futuro/encerrado), exigência e destino — sem persistência
paralela. Cadastro (`/new`) e edição (`/{itemKey}`) abrem páginas
completas, nunca modal, e gravam orquestrando o contrato versionado
existente (DRAFT → REVIEW → PUBLISHED com `effective_from_period`) —
sempre prospectivo, snapshots de competências abertas/encerradas
preservados. RW01: a base de cada publicação é a versão vencedora no
boundary (`effective_from DESC, version DESC` — regra de
`resolve_published_version`); como versões são conjuntos absolutos, o
item é propagado a todos os boundaries cobertos pela janela e a remoção
é publicada em `until+1` (`planDocumentSave`). Cada passo é
idempotente: configuração já vigente é pulada, versão DRAFT/REVIEW com
itens idênticos é retomada, conteúdo divergente vira conflito honesto —
falha intermediária nunca informa sucesso e retry converge. Limites
pendentes de gate (Plano 113 §28.2): atomicidade multi-versão real
(DECISION_REQUIRED-1) e encerramento da última exigência do checklist
(DECISION_REQUIRED-2 — o contrato exige ≥1 item por versão publicada).
Filtros da listagem (`q`, `status`, `dest`) ficam na URL; o retorno do
formulário preserva a consulta.

Central de Fechamento — Administração do checklist em cascata (UX-015):
a página `closing/admin` lista apenas as versões do template mestre;
cada versão abre página contextual própria em
`closing/admin/versions/{n}` (metadados + documentos daquele snapshot
histórico — nunca a configuração vigente — e ações por estado, com
edição de itens DRAFT atômica via OCC `revision`); cada documento abre
em `versions/{n}/documents/{itemKey}` sempre em leitura, com «Editar
exigência futura» encaminhando ao fluxo governado do catálogo; o
histórico de auditoria saiu do modal para páginas `closing/admin/events`
(template) e `versions/{n}/events` (recorte por `?version=` da BFF).
Breadcrumbs `CfPagePath` preservam o retorno por nível; deep links, F5
e voltar/avançar funcionam por `popstate`. Núcleo compartilhado:
`features/closing/checklistAdminShared.tsx` (constantes, ações de
versão + diálogos, editor de item) consumido pela lista e pelo detalhe.
O ator dos eventos permanece `actor_subject` (rótulo «Ator (id):»)
até o contrato de identidade do UX-014 — DECISION_REQUIRED registrado
no Plano 113 §28.14 (falta rota BFF de lookup administrativo de usuários).

RW02 (estrutural): superfície única por página — removido o card
intermediário da Administração; ações governadas com ícones no
`headerActions` da `DataTableSection`; colunas `sortable` + alternância
Tabela/Cards (`viewLayoutPreferencesKey` + `renderCard` com
`CfDataRecordCard` navegável); clique/Enter/Espaço na linha abre o
detalhe (sem botão «Abrir» redundante) e a coluna «Ações» usa
`rowClick:"stop"` para não disparar navegação nas ações destrutivas;
títulos/subtítulos não exibem códigos técnicos do template.

UX-016 (hero contextual + listagem flexível): Administração e Versão
compartilham `CfPageHero` (título, métricas reais, ações com ícone e a
toolbar de listagem) acima de uma única superfície `.cf-flex-listing`
irmã. A toolbar nativa da `DataTableSection` é portada para o hero via
`toolbarPortalTarget` (mesma instância — sem controles duplicados) e a
tabela ocupa a altura útil via `tableLayout="scroll"` +
`dashboard-page--fill` aplicado às duas views no `PluginShell`;
paginação ancorada ao fim. A Administração não tem coluna «Ações» nem
Inativar — o ciclo de vida da versão (incluindo Inativar danger)
existe apenas na página do detalhe.

UX-016-RW01 (help contextual + paginação inteligente): todas as colunas
informativas das tabelas CF usam `headerHint` (HelpTooltip acessível do
kit), a busca das listagens usa `searchHint` e os indicadores/campos
somente leitura usam `hintedLabel`/`hint` — textos centralizados em
`helpTooltips.ts`. A paginação é inteligente por padrão em todo o portal:
`hidePaginationWhenSinglePage` (prop nova do `DataTableSection`, ativada
no wrapper `cfDataTableUi`) só renderiza o rodapé quando há mais de uma
página efetiva — o seletor «Itens por página» permanece na toolbar.

RW01 (design): `cf-detail-list` — padrão read-only usado nas páginas de
detalhe — passou a ser o grid semântico do portal (auto-fit ~200px,
label muted + valor forte, `__full` para textos extensos); a versão
mostra `CfMetricStrip` com tiles reais do DTO e ações junto ao resumo;
o documento da versão traz badges e ações no cabeçalho com o contexto
da versão reduzido a uma linha compacta.

Padrão de tabelas: `DataTableSection` do `@delpi/plugin-ui` via
`cfDataTableUi` — banda única com ícone + título + pill de contagem do
universo filtrado à esquerda e controles nativos (itens/página + Fonte +
Colunas) à direita, quebrando para a linha seguinte em telas estreitas;
células em duas linhas (`cf-cell-primary/secondary`), proporções de
coluna via classes do kit (`cf-table__col--wrap/wide/compact/status/
numeric`), `resizableColumns` com handles nativos do kit, preferências
de coluna/fonte persistidas pelo kit. Código cru de auditoria (ex.:
`paymentDirection`) fica em tooltip/`cf-visually-hidden`, nunca como
caractere solto na célula. Resumos P7 exibem participação percentual
derivada do total histórico do contrato.

Central de Fechamento — experiência DRE (DRE-ACCESS-019/RW04):
entrada exclusiva pela capability `controllership-finance.access.dre`
(a legada `closing-documents.read` foi descontinuada após a migração
comprovada do papel — doc 115 §11). O usuário DRE entra pelo **mesmo
basePath** `/apps/controllership-finance` — o guard do Portal monta o
app quando ele detém ≥1 rota autorizada (`hasAuthorizedAppEntry`) e a
rota `/home` (entrada do launcher) canonicaliza em `/`. É a **mesma
`HomePage`** — mesmo hero, top bar única («Início» para os dois
públicos), «Eventos e interações», «Caminhos e funcionalidades» e
busca projetados por capability — com a seção «Central de
Fechamento» → «Fechamento Mensal», que abre Documentos e interações
em `closing/documents`. O viewer sem `access` não vê nav/busca
internas e rotas internas redirecionam com segurança para a Home.
A listagem N1–N3 (`ReceivedDocumentsPage`,
`ReceivedDocumentDetailPanel`, `ReceivedConversationPanel`) consome
somente a projeção BFF `GET/POST /closing/received-documents/*`:
deliveries por competência, documentos efetivamente liberados
(assignment `RECIPIENT` + pacote `SUBMITTED`), versões liberadas,
download auditado, mensagens `SHARED` e solicitações de ajuste
`OPEN → ANSWERED → CONFIRMED` (responder não encerra; só o requerente
confirma). Estados de loading/erro/vazio honestos; Help contextual nos
grupos `receivedDocuments` e `dreHome`.

UX-022 (padronização de loading): todo carregamento do portal usa os
indicadores canônicos do `@delpi/plugin-ui` — `CfSectionLoading`
(`LoadingActivityCard` panel/compact) para páginas e seções,
`CfLoadingBadge` para atualizações compactas, `CfScreenLoading` para o
bootstrap do MFE e `CfInlineLoadingProgress` somente com progresso real
mensurável. Texto isolado de "carregando…" e `CfEmptyState` usado como
loader foram eliminados; regiões em consulta declaram `aria-busy` e KPIs
exibem `—` até o valor ser comprovado (Divergências nunca mostra `0`
antes da verificação concluir). Matriz completa no doc 30 §UX-022.

## Runtime

- React 19 + Vite 7 + `@originjs/vite-plugin-federation`
- `@delpi/plugin-ui` via remote federado (`preparePluginUiRemote`)
- Sem React Router — resolução de rota via `resolvePluginRoute`
- Origens de dados na BFF do produto: `GET /viewer-context`,
  `GET /closing/financial-settlements`, `GET /closing/financial-settlements/summary`

## Testes

```bash
npm install
npm test        # vitest + structural (tsx --test src/**/*.test.mjs)
npm run build   # tsc -b && vite build
```
