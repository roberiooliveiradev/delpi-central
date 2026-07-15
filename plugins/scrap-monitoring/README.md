# Scrap Monitoring (Acompanhamento de Refugos)

Plugin id: **`scrap-monitoring`**. Título exibido ao usuário: **Acompanhamento de Refugos**.

Painel multi-filial (SC/ES) de refugos em R$, consumindo a API **`/refugos`** da api-delpi.

## Rotas da UI

| Path | Permissão | Filial TOTVS |
|------|-----------|--------------|
| `/apps/scrap-monitoring/sc` | `scrap-monitoring.view.filial-sc` | `01` |
| `/apps/scrap-monitoring/es` | `scrap-monitoring.view.filial-es` | `02` |

Permissão ampla (ambas filiais): `scrap-monitoring.view` · acesso ao app: `scrap-monitoring.access`.

## API

Base: `/apps/api-delpi` (gateway). Header: `X-Delpi-Caller-App: scrap-monitoring`.

| Endpoint | Uso |
|----------|-----|
| `GET /refugos/resumo` | KPIs valor dia / mês / período |
| `GET /refugos/rankings?dimension=…` | Top N (motivo, MP, PA, CT, colaborador) |
| `GET /refugos/registros` | Tabela do acompanhamento |
| `GET /refugos/filtros` | Opções MP/PA/OP/motivo |

Doc completa: [api-delpi/docs/api/scrap-monitoring.md](../../api-delpi/docs/api/scrap-monitoring.md).

## Estado desta entrega

Painel MFE com KPIs (dia/mês/período), rankings (motivo, MP, PA, CT, colaborador) e tabela paginada de registros. Filtros: filial SC/ES, período, MP, PA, OP, motivo e centro de trabalho.

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

Registrar manifesto no portal após deploy do plugin.
