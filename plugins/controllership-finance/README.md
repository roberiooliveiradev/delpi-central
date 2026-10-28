# Portal Controladoria & Finanças (controllership-finance)

Microfrontend do Portal Controladoria & Finanças — Minha DELPI.

- **Plugin id:** `controllership-finance`
- **Base path:** `/apps/controllership-finance`
- **BFF:** `controllership-finance-api` (`/apps/controllership-finance-api`)
- **Permissions:** `controllership-finance.access`, `controllership-finance.manage`

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

Central de Fechamento — Estoque histórico P7 (R03): rota interna
`closing/stock-inventory`, consulta operacional por competência/filial
(`officialP7=false` — não é o relatório oficial MATR460). Estados
tipados `available` / `incomplete` / `source_missing` /
`no_matching_items`; snapshot ausente exibe apenas banner — nunca tabela
vazia (ausência não é saldo zero).

Central de Fechamento — Relatórios e divergências (aba `?tab=reports`):
hub de análise com indicadores honestos, atenção primeiro e cartões por
família; cada cartão abre página contextual
`closing/monthly-closing/{YYYY-MM}/reports/{reportKey}`
(`financial-settlements` | `stock-inventory`) dentro do próprio
Fechamento mensal — as páginas legadas são reutilizadas em modo
`reportContext` com competência travada, agrupamentos em tabelas por
colunas e slot de PDF honesto enquanto não houver produtor homologado.
O retorno restaura competência, aba e família analisada; a matriz
R01–R15 permanece como rastreabilidade técnica recolhida.
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
O ator dos eventos permanece `actor_subject` até o contrato de
identidade do UX-014.

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
