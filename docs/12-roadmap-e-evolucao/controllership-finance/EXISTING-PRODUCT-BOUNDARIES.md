# Existing Product Boundaries — Portal Controladoria & Finanças

## Portal Financeiro P0 — runtime existente

Fonte: [../financial/README.md](../financial/README.md).

Existe `plugins/financial` + `financial-api`, com gestão à vista, faturamento, inadimplência, despesas por centro de custo e outras capacidades documentadas.

O novo Portal Controladoria & Finanças:
- não prova absorção automática do P0;
- não autoriza remover/deprecar `plugins/financial`;
- não transfere ownership por conveniência;
- não deve duplicar capacidade existente sem inventário e decisão explícita.

Qualquer consolidação futura exige paridade, target saudável, owners, contratos e rollback.

## Financeiro / Controladoria — Transforma+ — discovery/histórico

Fonte: [../financeiro-controladoria/README.md](../financeiro-controladoria/README.md).

A pasta CTL-* permanece útil como histórico/discovery, mas não substitui o TARGET detalhado do PROC-0072.

Itens compatíveis podem ser rastreados; divergências não podem ser reconciliadas silenciosamente.

## Novo TARGET

```text
Portal Controladoria & Finanças
└── Central de Fechamento
    └── PROC-0072
```

Futuros macroprocessos cabem no portal, mas não são considerados implementados/autorizados apenas por isso.

## Ownership

Na implementação, owner é verificado capacidade por capacidade. Não inferir um único BFF/banco como owner de todo Financeiro/Controladoria.
