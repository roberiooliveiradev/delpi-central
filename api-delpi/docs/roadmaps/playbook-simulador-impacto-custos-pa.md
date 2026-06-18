# Playbook DELPI — Simulador de impacto de custos do produto acabado (PA)

## 1. Objetivo

Identificar e ranquear as **matérias-primas (MPs)** que mais impactam o **custo de 1 unidade de PA**, com base na BOM vigente, e simular reajustes percentuais de preço.

Responde:

- Quais MPs compõem o PA e em que quantidade por unidade?
- Qual o custo estendido de cada MP (`qtd × preço unitário`)?
- Quais MPs concentram o maior impacto (Pareto de custo)?
- Quanto representam os materiais no custo padrão do PA?
- Qual o efeito de um reajuste simulado (ex.: +10%) no custo total de materiais?

---

## 2. Regra-mãe

```text
Impacto de custo de MP no PA =
quantidade acumulada da MP na BOM vigente (por 1 PA)
× custo unitário da MP (padrão ou última compra)
```

Ranking: ordenar por `extended_cost` decrescente.

### 2.1 PA em MI (milheiro)

Produtos PA com `B1_UM = MI` seguem a convenção DELPI **1 MI = 1000 peças**. Na api-delpi:

- A BOM (`SG1010`) expressa quantidades para **1 milheiro** (1 PA em MI).
- `quantity_per_pa` = quantidade acumulada na explosão **sem** ÷1000 (`ProductPaBomReferenceService`, `bomQuantityFactor = 1`).
- A resposta inclui `pa_reference` (`reference_unit: PA`, `catalog_unit: MI`).
- `B1_CUSTD` do PA está **por MI**.

Para necessidade **por 1 peça** (engenharia manual): `quantity_per_pa / 1000`.

Documentação completa: [`playbook-conversao-unidades-protheus.md`](./playbook-conversao-unidades-protheus.md).

---

## 3. Rota implementada

```http
GET /products/{code}/cost-impact-simulation
```

| Parâmetro | Default | Descrição |
|---|---|---|
| `code` | path | Código do **PA** |
| `max_depth` | 50 | Profundidade máxima da BOM |
| `price_source` | `standard_cost` | `standard_cost` → `B1_CUSTD`; `last_purchase` → `B1_UPRC` |
| `adjustment_percent` | 0 | Reajuste simulado aplicado a todas as MPs (-100 a 1000) |
| `top_n` | todas | Limita ranking às N MPs de maior impacto |

**operationId:** `get_product_cost_impact_simulation`  
**shape:** `composite_analysis`

---

## 4. Tabelas e colunas

| Tabela | Uso |
|---|---|
| `SG1010` | BOM vigente — explosão recursiva |
| `SB1010` | Cadastro PA/MP — `B1_CUSTD`, `B1_UPRC`, `B1_TIPO` |

Filtro de vigência:

```sql
AND G1.G1_FIM > CONVERT(CHAR(8), GETDATE(), 112)
```

Somente MPs na agregação:

```sql
AND SB1.B1_TIPO = 'MP'
```

Quantidade por PA:

```sql
SUM(accumulated_quantity) GROUP BY component_code
```

---

## 5. Indicadores retornados

| Campo | Cálculo |
|---|---|
| `extended_cost` | `quantity_per_pa × unit_cost` |
| `impact_on_material_cost_percent` | `extended_cost / total_material_cost × 100` |
| `impact_on_pa_cost_percent` | `extended_cost / pa_standard_cost × 100` |
| `simulated_extended_cost` | `quantity_per_pa × unit_cost × (1 + adjustment_percent/100)` |
| `projected_cost_delta` | `simulated_total_material_cost - total_material_cost` |

---

## 6. Validação

Produto homologado: `90261255` (PA com BOM multinível).

```bash
curl -s "http://localhost/apps/api-delpi/products/90261255/cost-impact-simulation?top_n=5" \
  -H "Authorization: Bearer $TOKEN"
```

Simulação +10%:

```bash
curl -s ".../cost-impact-simulation?adjustment_percent=10&price_source=last_purchase"
```

---

## 7. Limitações

- Considera **somente custo de materiais** (MPs da BOM); não inclui MOD, CIF ou custo industrial completo além do `B1_CUSTD` do PA como referência.
- PIs são expandidos na BOM; custo agregado é das **MPs folha**.
- MPs sem custo cadastrado (`B1_CUSTD` e `B1_UPRC` zerados) entram com custo 0.

---

## 8. Integração chat

Intenções sugeridas:

- «Quais materiais mais impactam o custo do PA 90261255?»
- «Simule aumento de 10% nos materiais do produto 90261255»
- «Ranking Pareto de matérias-primas do PA 90261255»

Rota: `get_product_cost_impact_simulation` · presenter `composite_analysis` · perfil `product_cost_impact_simulation`.

Knowledge RAG: `produto-conversao-unidades-protheus.txt` + `sql-playbook-simulador-impacto-custos-pa.txt`.
