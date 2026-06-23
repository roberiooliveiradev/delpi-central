# Dashboard Comercial

Microfrontend para indicadores comerciais (ROL por filial 01/02, OTD, conversão, novos negócios) via **api-delpi** `/commercial/*`, com metas do catálogo SI.

## Documentação

| Arquivo | Conteúdo |
|---------|----------|
| [docs/DOCUMENTACAO.md](./docs/DOCUMENTACAO.md) | Guia completo |
| [docs/API_MAPPING.md](./docs/API_MAPPING.md) | Endpoints |
| [docs/PROPOSTAS-PERIODO.md](./docs/PROPOSTAS-PERIODO.md) | Tabela de propostas (sort, busca, paginação server-side) |
| [docs/DETALHE-PROPOSTA.md](./docs/DETALHE-PROPOSTA.md) | Detalhe da OV |
| [docs/export.md](./docs/export.md) | Exportação CSV/Excel/PDF |
| [docs/TESTING.md](./docs/TESTING.md) | Build e homologação |

## Início rápido

```bash
cd plugins/dashboard-commercial
npm install && npm run ci
```

Registro: `TOKEN=... ./scripts/register-manifest.sh`
