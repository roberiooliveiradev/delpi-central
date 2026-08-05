# Portal Comercial — documentação

> **Status:** playbook oficial (ago/2026) — documentação; implementação por fases  
> **Nome ao usuário:** **Portal Comercial**  
> **Id técnico:** `commercial`  
> **Produto:** hub de decisão e execução comercial da Minha DELPI (várias funcionalidades)

O **Portal Comercial** é a nova aplicação do domínio comercial: concentra jornadas (carteira, pedidos, CRM, etc.) com API própria (`commercial-api`) e reads TOTVS via api-delpi.

O plugin `pedidos-venda-abertos` (Portal do Vendedor) permanece **ativo até paridade completa** no Portal Comercial; só então é **depreciado**. `dashboard-commercial` e `propostas-comerciais` seguem coexistindo / compostos.

## Documentos

| Documento | Conteúdo |
|-----------|----------|
| **[PLAYBOOK-MODULO-COMERCIAL.md](./PLAYBOOK-MODULO-COMERCIAL.md)** | Playbook mestre — Portal Comercial, **§ 1.2 matriz dores × cobertura**, fases, gates `.cursor` |
| **[API-ROUTES.md](./API-ROUTES.md)** | Mapeamento de **todas** as rotas commercial-api + api-delpi |
| **[DATA-MODEL.md](./DATA-MODEL.md)** | Estrutura física de **todas** as tabelas Postgres (`commercial`) |
| **[WIREFRAMES.md](./WIREFRAMES.md)** | Wireframes das páginas (shell, paridade F2b, Meu dia, CRM) |
| **[PLAYBOOK-01-fronteiras-api-delpi.md](./PLAYBOOK-01-fronteiras-api-delpi.md)** | Contrato vivo api-delpi × commercial-api; migração do estado Delpi de carteira (GET+CRUD) |
| **[INVENTARIO-ATIVOS.md](./INVENTARIO-ATIVOS.md)** | Baseline factual — rotas, plugins, gaps |
| **[adr/ADR-001-commercial-api.md](./adr/ADR-001-commercial-api.md)** | ADR — API própria e migração sellers/avatar |
| **[KPI-FICHAS.md](./KPI-FICHAS.md)** | Fichas KPI (F0) — fórmulas e owners |
| **[IMPLEMENTATION-PLAN.md](./IMPLEMENTATION-PLAN.md)** | Plano executável F0–F2b (status) |
| **[HOMOLOGACAO-PARIDADE-PEDIDOS.md](./HOMOLOGACAO-PARIDADE-PEDIDOS.md)** | Checklist de paridade Portal do Vendedor (F2b) |

> **Implementação:** F0–F2b entregues em código (`commercial-api/`, `plugins/commercial/`). Homologação Comercial ainda aberta no checklist.

## Escala (obrigatório no desenho)

Ver playbook **[§ 14](./PLAYBOOK-MODULO-COMERCIAL.md#14-escalabilidade-resiliência-e-performance)**: API dedicada stateless, paginação server-side, sem SQL TOTVS na commercial-api, features modulares no MFE, outbox, degradação parcial, orçamentos de latência.

## Decisão de fronteira (resumo)

```text
MFEs analíticos (dashboard, propostas) + reads TOTVS de pedidos
  → api-delpi → TOTVS

Portal Comercial (carteira Delpi, CRM, admin vendedores)
  → commercial-api → Postgres
  → commercial-api → api-delpi → TOTVS
```

- Nomes técnicos: **English** · ao usuário: **Portal Comercial** (pt-BR)
- UI: `plugins/commercial` + `@delpi/plugin-ui`
- Depreciação de `pedidos-venda-abertos`: **somente** após checklist § 2.1.1 do playbook

## Ativos existentes

| Plugin | Papel | Destino |
|--------|--------|---------|
| `dashboard-commercial` | Cockpit KPIs / OTD / propostas OV | Permanece (compor) |
| `pedidos-venda-abertos` | Portal do Vendedor | **Depreciar após paridade** no Portal Comercial |
| `propostas-comerciais` | Propostas ativas + PDF | Permanece (compor) |

## Pacotes alvo

| Pacote | Papel |
|--------|--------|
| `commercial-api/` | Backend dedicado |
| `plugins/commercial/` | App **Portal Comercial** (telas de paridade + expansão) |

## Fases (ordem)

| Fase | Entrega |
|------|---------|
| F0 | Fichas KPI + ownership |
| F1 | Scaffold commercial-api |
| F2 | Migrar rotas Delpi de carteira/avatar (GET + CRUD) |
| **F2b** | **Paridade UX** Portal do Vendedor → Portal Comercial |
| **F2c** | Depreciar `pedidos-venda-abertos` |
| F3–F4 | Runtime módulo + composição dashboard/propostas |
| F5–F7 | Worklist, pipeline/forecast, amostras/confirmação |

## Referências de plataforma

- [Plugin × módulo](../../05-plugin-system/plugin-vs-module.md)
- [Roadmap runtime 1.1.0](../../05-plugin-system/roadmap-implementacao-plugin-modulo.md)
- [Checklist novo MFE](../../05-plugin-system/novo-plugin-mfe-checklist.md)
- Fronteira irmã: [maintenance PLAYBOOK-01](../maintenance/PLAYBOOK-01-fronteiras-api-delpi.md)
- Pedidos (legado até F2c): [pedidos-venda-abertos](../pedidos-venda-abertos/README.md)
- Propostas: [propostas-comerciais](../propostas-comerciais/README.md)
