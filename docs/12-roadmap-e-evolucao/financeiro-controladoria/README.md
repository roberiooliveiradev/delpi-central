# Financeiro / Controladoria — índice Transforma+

> **Papel:** roadmap de negócio Transforma+ para fechamento, Contabilidade e custos sob a ótica de Controladoria.  
> **Não substitui** o Portal Financeiro P0 nem o Planejamento Orçamentário.  
> **Não autoriza** implementação, permission nova, gravação ERP ou fórmula contábil/mão de obra.

## Documentos desta pasta

| Documento | Conteúdo |
|---|---|
| [ROADMAP.md](./ROADMAP.md) | Visão, backlog CTL-*, ondas, integrações, questões abertas |

## Relação com produtos já existentes

| Produto | Path canônico | Relação |
|---|---|---|
| Portal Financeiro (P0) | [../financial/README.md](../financial/README.md) · `plugins/financial` · `financial-api` | Gestão à vista, faturamento, inadimplência, despesas por CC, frete, indicadores — **não** é o cockpit de fechamento Contábil |
| Planejamento Orçamentário | [../planejamento-orcamentario/](../planejamento-orcamentario/) | Orçamento CAPEX/pessoal/cockpit de aprovações — domínio próprio; fora do P0 Financial |
| Portal Suprimentos (Transforma+) | [../supplies/ROADMAP-TRANSFORMA-PLUS.md](../supplies/ROADMAP-TRANSFORMA-PLUS.md) | Custos de importação: **mesma fonte**, visões por perfil (SUP-013 ↔ CTL-007) |
| Lançamento de NF | [../lancamento-notas-fiscais/](../lancamento-notas-fiscais/) | App Financeiro/Fiscal existente; pré-validação Transforma+ permanece proposta |

## Boundaries

- Core = RBAC / effective permissions  
- `api-delpi` = SQL/TOTVS financeiro e demais producers  
- `financial-api` = BFF do Portal Financeiro  
- Outros contexts = owners das próprias regras  
- **Não** criar ownership técnico novo por conveniência neste roadmap
