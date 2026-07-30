# Scrap Monitoring (Acompanhamento de Refugos)

Plugin id: **`scrap-monitoring`**. Título exibido ao usuário: **Acompanhamento de Refugos**.

Painel multi-filial (SC/ES) de refugos em R$, consumindo a API **`/refugos`** da api-delpi.

**Escopo:** a API exclui produto de terceiro (`SB1.B1_TPMAT = 2`, cadastro SB1 «Produto de Terceiro»). KPIs, rankings, série, filtros e registros já vêm sem esses itens — não há toggle no MFE.

## Rotas da UI

| Path | Permissão | Filial TOTVS |
|------|-----------|--------------|
| `/apps/scrap-monitoring/sc` | `scrap-monitoring.view.filial-sc` | `01` |
| `/apps/scrap-monitoring/es` | `scrap-monitoring.view.filial-es` | `02` |
| `/apps/scrap-monitoring/{sc\|es}/registro?…` | mesma da filial | detalhe do registro |

Permissão ampla (ambas filiais): `scrap-monitoring.view` · acesso ao app: `scrap-monitoring.access`.

## API

Base: `/apps/api-delpi` (gateway). Header: `X-Delpi-Caller-App: scrap-monitoring`.

| Endpoint | Uso |
|----------|-----|
| `GET /refugos/resumo` | KPIs valor dia / mês / período |
| `GET /refugos/serie` | Evolução temporal (dia/mês) |
| `GET /refugos/rankings?dimension=…` | Top N (motivo, MP, PA, CT, colaborador) |
| `GET /refugos/registros` | Tabela do acompanhamento |
| `GET /refugos/filtros` | Opções MP/PA/OP/motivo |

Todos os endpoints acima respeitam a exclusão de produto de terceiro na api-delpi.

**Valor (R$):** `BC_QUANT × B2_CM1` do armazém **`01` (almoxarifado)**; fallback `B1_CUSTD`. O local **`99` é fábrica** e não entra no custo. Detalhe: [scrap-monitoring.md](../../api-delpi/docs/api/scrap-monitoring.md) § Valor.

Doc completa: [api-delpi/docs/api/scrap-monitoring.md](../../api-delpi/docs/api/scrap-monitoring.md).

## Estado desta entrega

Painel MFE alinhado a `@delpi/plugin-ui` e ao padrão visual do dashboard commercial: canvas full-bleed, filtros autoaplicados (debounce), balões `HelpTooltip` (`src/content/helpTooltips.ts`), gráficos full-width (1 por linha), `DataTableSection` com clique abrindo detalhe e exportação Excel.

## Dev

```bash
cd plugins/scrap-monitoring
npm install
npm run build
npm test
```

Docker (scripts sequenciais):

```bash
./infra/scripts/up-dev-sequential.sh --fase remote --build plugin-ui
./infra/scripts/up-dev-sequential.sh --fase mfe --build scrap-monitoring
```

Registrar manifesto no portal após deploy do plugin:

```bash
TOKEN=$(bash infra/scripts/get-dev-token.sh) \
  bash plugins/scrap-monitoring/scripts/register-manifest.sh
```

Depois atribua no RBAC: `scrap-monitoring.access`, `.view.filial-sc`, `.view.filial-es` e `.view`.
