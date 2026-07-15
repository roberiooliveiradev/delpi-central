# Indicador de Inadimplência

Microfrontend da Minha DELPI para acompanhar pontualidade e inadimplência de
títulos financeiros quitados, consumindo a `api-delpi`.

```text
Portal → MFE financeiro-inadimplencia → /apps/api-delpi/financeiro/inadimplencia/*
```

## Objetivo

Exibir:

- resumo de pontualidade/inadimplência (quantidade e valor);
- evolução mensal;
- distribuição por faixa de atraso;
- ranking de clientes;
- drill-down de títulos do cliente.

## Arquitetura

- Vite + React 19 + Module Federation (`@originjs/vite-plugin-federation`)
- UI compartilhada via remote `@delpi/plugin-ui`
- HTTP local (`src/api/httpClient.ts`) com Bearer do Portal / `VITE_DEV_ACCESS_TOKEN`
- Sem estado global — hooks locais
- Percentuais e totais **sempre** vindos da API (sem recalcular regra de negócio)

## API consumida

Base: `/apps/api-delpi/financeiro/inadimplencia`

| Endpoint | Uso |
|---|---|
| `GET /resumo` | Cards KPI |
| `GET /mensal` | Série mensal |
| `GET /faixas-atraso` | Distribuição por faixa |
| `GET /clientes` | Ranking paginado |
| `GET /titulos` | Modal de títulos |

Payload em `snake_case`. Doc: `api-delpi/docs/api/financeiro-inadimplencia.md`.

## Período padrão

Últimos **12 meses completos** (fim exclusivo = dia 1 do mês atual).

Filtro temporal da API:

```text
MES_REFERENCIA >= start_date
MES_REFERENCIA < end_date
```

## Variáveis de ambiente

| Variável | Uso |
|---|---|
| `VITE_DEV_ACCESS_TOKEN` | JWT para standalone |
| `VITE_PLUGIN_UI_DEV=1` | Remote plugin-ui em `localhost:5010` |
| `VITE_PLUGIN_UI_REMOTE` | Override da URL do remote |

Não existe `VITE_API_*` — caminhos absolutos via gateway.

## Execução standalone

```bash
# Terminal 1
cd plugins/plugin-ui && npm run dev

# Terminal 2
cd plugins/financeiro-inadimplencia
VITE_PLUGIN_UI_DEV=1 \
VITE_DEV_ACCESS_TOKEN="$(bash ../../infra/scripts/get-dev-token.sh)" \
npm run dev
```

Abra a URL do Vite (tipicamente `http://localhost:5173/apps/financeiro-inadimplencia/`).

## Scripts

```bash
npm install
npm run lint
npm test
npm run build
npm run ci
```

## Module Federation

| Campo | Valor |
|---|---|
| remote name | `financeiro-inadimplencia` |
| remote entry | `/apps/financeiro-inadimplencia/assets/remoteEntry.js` |
| exposed | `./App` → `src/bootstrap.tsx` |
| exports | `mount`, `updateRoute`, `unmount` |

## Fórmulas (backend)

```text
% em dia (qtd) = SUM(PAGO_EM_DIA) / COUNT(*) * 100
% inadimplência (qtd) = SUM(PAGO_COM_ATRASO) / COUNT(*) * 100
% em dia (valor) = valor em dia / valor total * 100
% inadimplência (valor) = valor atrasado / valor total * 100
```

## Faixas

1. Em dia  
2. 1 a 5 dias  
3. 6 a 15 dias  
4. 16 a 30 dias  
5. Acima de 30 dias  

## Pendências (próxima etapa)

- Registrar manifesto (`scripts/register-manifest.sh`)
- Cadastrar/atribuir `financeiro-inadimplencia.access` e `.view` no RBAC
- Incluir serviço no Docker Compose / Gateway
- Publicar no Portal

Nesta etapa o manifesto existe no repositório, mas **não** foi registrado.
