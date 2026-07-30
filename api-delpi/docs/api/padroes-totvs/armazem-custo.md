# Armazéns Protheus e custo unitário

Convenções **da empresa** para `SB2.B2_LOCAL` e uso de `B2_CM1` / `B1_CUSTD` em rotas novas da **api-delpi**.

Parte da [biblioteca de padrões TOTVS](./README.md).

Código canônico: `app/domain/totvs/protheus_warehouses.py`  
Regra Cursor: `.cursor/rules/totvs-warehouse-cost-standards.mdc`  
Checklist de rota: `new-api-route-checklist.mdc` + esta seção quando houver valor em R$ ou saldo por local.

---

## Armazéns (`SB2.B2_LOCAL`)

| Código | Nome operacional | Uso típico |
|--------|------------------|------------|
| **`01`** | **Almoxarifado** | Estoque principal; **custo unitário canônico** (`B2_CM1`) para valoração em R$ |
| **`99`** | **Fábrica** | WIP / chão de fábrica; consumo de MP em OP (`D3_LOCAL = 99` em análises de consumo) |
| `98` | (saldo disponível / WIP auxiliar) | Entra em **saldo disponível** com `01`+`99` (estoque de segurança); **não** é custo canônico |
| `50` | WIP / processo | Trabalho em processo; **não** é custo canônico |

Constantes Python:

| Constante | Valor | Módulo |
|-----------|-------|--------|
| `WAREHOUSE_ALMOXARIFADO` / `COST_UNIT_WAREHOUSE` | `01` | `protheus_warehouses` |
| `WAREHOUSE_FABRICA` | `99` | `protheus_warehouses` |
| `PRIMARY_WAREHOUSE` | `01` | `safety_stock_classification_service` (alinhar ao almoxarifado) |
| `AVAILABLE_BALANCE_WAREHOUSES` | `01`, `98`, `99` | estoque de segurança |
| `WORK_IN_PROCESS_WAREHOUSES` | `50`, `98`, `99` | estoque de segurança |

---

## Valoração em R$ (obrigatório em rota nova)

Quando a rota multiplicar quantidade × custo (refugo, perda valorizada, impacto financeiro de material, etc.):

```text
valor = quantidade × COALESCE(NULLIF(B2_CM1 do B2_LOCAL=01, 0), NULLIF(B1_CUSTD, 0), 0)
```

### O que fazer

1. Join em `SB2010` **filtrado** por `B2_LOCAL = COST_UNIT_WAREHOUSE` (`01`).
2. Fallback `SB1.B1_CUSTD` se CM1 do almoxarifado for zero/ausente.
3. Constantes em domínio (`protheus_warehouses` ou reexport no módulo); **não** espalhar `'01'` mágico sem comentário.
4. Documentar a fórmula na doc da rota e linkar esta seção.
5. Teste SQL assertando filtro `B2_LOCAL = '01'` (e que **não** há `AVG(B2_CM1)` entre locais).

### O que NÃO fazer

| Anti-padrão | Por quê |
|-------------|---------|
| `AVG(B2_CM1)` por filial+produto sem filtrar local | Mistura almoxarifado (`01`) com fábrica (`99`) e outros → divergência vs Power BI / financeiro |
| `JOIN SB2` sem agregar/filtrar local | Multiplica linhas (um registro SBC × N locais) e infla valor |
| Usar `B2_CM1` do `99` como custo de material | Fábrica não é a fonte canônica de custo unitário Delpi |
| Assumir um único `B2_LOCAL` por produto | Produtos costumam ter vários locais com CM1 diferentes |

### Exceção legítima

- Campo **descritivo** `average_unit_cost` em consolidado de estoque (vários locais no `GROUP BY` produto), desde que **não** seja a base de `ValorPerda` / KPI financeiro de perda. Preferir rotular claramente como média entre locais do filtro.

---

## Saldo / cobertura (não confundir com custo)

| Necessidade | Locais | Exemplo |
|-------------|--------|---------|
| Custo unitário (R$) | só **`01`** | `/refugos/*` |
| Saldo disponível / déficit ESTSEG | **`01` + `98` + `99`** | `/supplies/safety-stock/*` |
| Consumo fabril (baixa OP) | tipicamente **`99`** em `D3_LOCAL` | análise de consumo ESTSEG |
| WIP | `50`, `98`, `99` | classificação estoque de segurança |

---

## Filiais

Filial (`B2_FILIAL`) **não** é armazém (`B2_LOCAL`). Ver [filiais.md](./filiais.md).

---

## Checklist rápido (PR com SQL novo)

- [ ] A rota valoriza em R$? → CM1 do **`01`**, nunca média de todos os locais.
- [ ] A rota fala de saldo disponível? → conferir se é `01+98+99` ou só um local.
- [ ] Constante nomeada + doc da rota aponta para esta seção.
- [ ] Teste unitário da SQL cobre o filtro de local.

---

## Referências de implementação

| Módulo | Doc / código |
|--------|----------------|
| Refugos | [scrap-monitoring.md](../scrap-monitoring.md) · `refugos_sql.py` · `REFUGOS_COST_WAREHOUSE` |
| Estoque de segurança | [estoque-seguranca.md](../estoque-seguranca.md) · `PRIMARY_WAREHOUSE` / `AVAILABLE_BALANCE_*` |
| Constantes compartilhadas | `app/domain/totvs/protheus_warehouses.py` |
