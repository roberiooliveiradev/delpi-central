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
