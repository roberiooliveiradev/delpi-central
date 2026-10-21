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

Padrão de tabelas: `DataTableSection` do `@delpi/plugin-ui` via
`cfDataTableUi` — contagem do universo filtrado em pill junto ao título,
toolbar nativa (itens/página + Fonte + Colunas), células em duas linhas
(`cf-cell-primary/secondary`), colunas longas com `cf-table__col--wrap`,
preferências de coluna/fonte persistidas pelo kit.

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
