# ADR-004 — Fusão do Portal Financeiro no Portal Controladoria & Finanças

| Campo | Valor |
|---|---|
| Status | **ACCEPTED** (decisões); implementação depende do inventário M0 e dos contratos M2 |
| Data | 2026-11-16 |
| Decisor | owner do produto |
| Contexto | Portal Financeiro (`plugins/financial` + `financial-api`, 7 áreas, 9 permissões) passa a viver no Portal Controladoria & Finanças |
| Relacionados | [plan.md](../financial-merge/plan.md) (doc 172) · [ADR-001](./ADR-001-hospedagem-lancamento-notas-fiscais.md) (precedente) · [doc 126 §4](../126-gate-contratual-r10-r11-comparacao-clara-2026-10-30.md) |

## Decisão

As áreas do Portal Financeiro (Gestão à vista, Faturamento, Inadimplência, Despesas por centro de custo, Frete, Notas Fiscais, Indicadores) viram páginas do Portal Controladoria & Finanças. As rotas vão para a `controllership-finance-api`, que segue consumindo a api-delpi e a strategic-indicators-api. A integração com o Questor fica, por ora, na `financial-api`.

| Id | Decisão |
|---|---|
| D1 | As 9 permissões `financial.*` não são herdadas. Tudo sob `controllership-finance.access`; `manage` segue para gestão. A ampliação de audiência é aceita pelo owner. |
| D2 | Todos com acesso veem as duas filiais. Filial é dimensão de dado, não permissão. |
| D3 | Rotas na `controllership-finance-api` (uma BFF por Portal, como o LNF no ADR-001). MFE só fala com a BFF do Portal. |
| D4 | Despesas por centro de custo: **duas páginas**. O R10 (Fechamento mensal; `D1_DTDIGIT`, seleção oficial e investigação) e a do Financeiro (acompanhamento; view `vw_fin_despesas_centro_custo`, `D1_EMISSAO`) não são equivalentes (doc 126 §4). Nomes e ajuda deixam a diferença explícita. |
| D5 | Notas Fiscais (Questor) no card «Notas fiscais», com a Auditoria de Entradas e o LNF. |
| D6 | `dashboard-financial`, `financeiro-centro-custo`, `financeiro-inadimplencia` seguem no ar; desativação só com autorização do owner. |
| D7 | Indicadores e Gestão à vista entram no Portal. |
| D8 | Exportar com `access`. |
| D9 | `/apps/financial/*` redireciona para o Portal no corte; desativar o plugin `financial` só com autorização do owner. |
| D10 | Questor permanece na `financial-api` nesta fusão. Futuro: migrar para a `external-data-api` e a CF-API consumir de lá (plan §8); só então a `financial-api` pode sair, com autorização. |

## Consequências

- Usuários com `controllership-finance.access` passam a ver dado financeiro que hoje não veem (lista no M0, antes do corte).
- A `financial-api` continua em PROD (Questor) — o LNF e a Auditoria não mudam nesta fusão.
- A CLARA ganha as leituras financeiras pelo mesmo catálogo, sem tool nova.

## Fora deste ADR

Contratos (M2), páginas (M4), corte (M6), desativações (M7, cada uma com autorização), migração do Questor (plan §8).
