# Propostas Comerciais

Plugin microfrontend da Minha DELPI para consulta read-only de propostas comerciais ativas (Protheus/TOTVS).

## Desenvolvimento local

```bash
cd plugins/propostas-comerciais
npm install
npm run dev
```

Standalone: `http://localhost:5173/apps/propostas-comerciais/` (sem auth — apenas layout).

Integrado ao portal: subir o stack `infra/` e registrar o manifesto (abaixo).

## Build

```bash
npm run build
```

## Registrar manifesto

```bash
export TOKEN="$(bash infra/scripts/get-dev-token.sh)"
bash plugins/propostas-comerciais/scripts/register-manifest.sh
```

Atribua `propostas-comerciais.view` ao perfil desejado no RBAC.

## API

- `GET /apps/api-delpi/propostas-comerciais`
- `GET /apps/api-delpi/propostas-comerciais/{proposta_interna}`

## Rotas do plugin

- `/apps/propostas-comerciais` — listagem
- `/apps/propostas-comerciais/{proposta_interna}` — detalhe
