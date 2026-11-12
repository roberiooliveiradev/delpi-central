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



### GLPI #1197 — atalhos de estoque sem giro (nov/2026)

A aba **Estoque sem giro** oferece **Últimos 6 meses** e **Últimos
12 meses**, calculados até o dia atual. Cada atalho substitui as duas
datas de forma atômica e limpa a competência mensal anterior, mantendo
unidade, armazém e demais filtros de detalhamento. KPIs e tabela são
atualizados juntos; a paginação volta à primeira página.

O botão ativo é inferido das datas (inclusive após restauração de URL).
Alterar manualmente datas ou a competência muda o contexto para
**Período personalizado**, e clicar novamente no atalho recupera a
janela móvel. O atalho de 12 meses continua usando o comportamento
padrão canônico da API, sem parâmetros explícitos de datas; 6 meses
reutiliza os parâmetros de datas existentes.

A janela examina **consumos efetivos** naquele intervalo, enquanto
os valores financeiros permanecem baseados no **estoque atual** (SB2),
não no valor histórico do estoque no mês selecionado. Por isso uma
janela maior pode resultar em menos valor classificado como sem giro.

Testes: `cd plugins/dashboard-supplies && npm run test`,
`npm run lint` e `npm run build`. Para homologação, testar
setembro/2026 → 6m → 12m → personalizado → 6m, com diferentes
unidades e armazéns, confirmando os mesmos KPIs do período padrão.
