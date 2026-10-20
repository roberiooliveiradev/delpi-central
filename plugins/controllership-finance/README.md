# Portal Controladoria & Finanças (controllership-finance)

Microfrontend do Portal Controladoria & Finanças — Minha DELPI.

- **Plugin id:** `controllership-finance`
- **Base path:** `/apps/controllership-finance`
- **BFF:** `controllership-finance-api` (`/apps/controllership-finance-api`)
- **Permissions:** `controllership-finance.access`, `controllership-finance.manage`

Escopo entregue (IMP-MFE-HOME): bootstrap federado, manifesto, shell de
navegação, Home com saudação/estados honestos, catálogo somente de rotas
implementadas, busca `?q=`, últimos acessos locais e ajuda contextual.

## Runtime

- React 19 + Vite 7 + `@originjs/vite-plugin-federation`
- `@delpi/plugin-ui` via remote federado (`preparePluginUiRemote`)
- Sem React Router — resolução de rota via `resolvePluginRoute`
- Única origem de dados: `GET /viewer-context` na BFF do produto

## Testes

```bash
npm install
npm test        # vitest + structural (tsx --test src/**/*.test.mjs)
npm run build   # tsc -b && vite build
```
