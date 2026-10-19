# Dashboard Suprimentos

Microfrontend com indicadores de suprimentos via **api-delpi** (`/supplies`).

## KPIs e gráficos

| Recurso | Endpoint | Descrição |
|---------|----------|-----------|
| CPV | `GET /supplies/cpv` | Custo de produto vendido e % sobre ROL |
| OTD compras | `GET /supplies/otd` | Pontualidade (MP ou código `3019*`) |
| Estoque | `GET /supplies/stock-value` | Valor total por localização |

Plano de correção vs. Registro de Inventário TOTVS: `api-delpi/docs/api/padroes-totvs/playbooks/playbook-correcao-estoque-supplies-inventario.md`.

**Performance (jun/2026):** o KPI do dashboard principal usa `summary_only=true` (`getStockValueSummary`); detalhe por local/produto na rota dedicada continua com bundle completo. Ver `api-delpi/docs/api/supplies-estoque-historico.md`.
| Giro IDD | `GET /supplies/inventory-turnover` | Giro de estoque em meses |

## Registro

```bash
export TOKEN="<jwt com apps.manage>"
./scripts/register-manifest.sh
```

Atribuir permissão `dashboard-supplies.view` no RBAC.

## Deploy

```bash
cd infra
docker compose up -d --build dashboard-supplies api-delpi
docker compose restart gateway
```

### Acuracidade e estoque sem giro — recuperação de consultas

O botão **Atualizar** recarrega o resumo e o detalhamento das duas abas.
Quando a consulta do detalhamento falha, a tela mostra o erro e **Tentar novamente**;
ela não apresenta essa falha como uma consulta bem-sucedida com zero registros.
A ordenação por data/produto preserva desempate estável sem repetir colunas.
Para validação com DAVI, ver `api-delpi/docs/integrations/davi-supplies-inventory-validation.md`.
