# Duplicidades e sobreposições — Suprimentos

> Correlação ≠ identidade de regra. Sem dump/contrato do BI, não declarar duplicata perfeita.

---

## DRIFTs transversais

| ID | Fontes | Prevalece | Impacto | Ação |
|---|---|---|---|---|
| D1 | `purchase-requests.unit.filial-01/02` vs `estoque-seguranca.view.filial-sc/es` | eixo B `supplies.unit.filial-{TOTVS}` | papéis inconsistentes até migração | aliases + RBAC canônico no Core |
| D2 | inventário oficial incompleto vs ativos reais | código/manifest/Compose/runtime | documentação defasada | atualizar inventário na implementação |
| D3 | exemplos históricos com permissions mais granulares | ADR-007 | risco de inflar RBAC | usar menor catálogo suficiente |
| D4 | fixture `supplies.view` vs permission canônica do novo Portal | ADR-004 + ADR-007 | fixture não pode ditar contrato | ajustar para `supplies.portal.access` na E3 |
| D5 | path legado `/analise-consumo` PT vs naming novo EN | english-code-identifiers | deep links | alias/redirect para `/safety-stock/consumption-analysis` |
| D6 | savings Sheets vs SI | SI = meta; Sheets = origem atual do realizado | duas superfícies | uma ficha KPI, ownership separado |
| D7 | instrução oficial Flask vs APIs recentes FastAPI | instrução oficial | risco de copiar framework errado | supplies-api = Flask, ADR-001 |
| D8 | `flask_auth.py` lê claims; `fastapi_auth.py` segue sem Core (`rbac_lookup_unavailable_using_token_claims`) | instrução oficial/Core | copiar qualquer um dos dois quebra GATE-AUTHZ | ADR-001 DRIFT-AUTHZ-01; não reutilizar na E2 |

---

## Atraso de Fornecedores BI × Dashboard OTD

| Dimensão | Dashboard `/otd` | BI Atraso SC |
|---|---|---|
| Universo | MP ou `3019*` conforme regra atual | desconhecido |
| Fonte | api-delpi `get_supplies_otd` | desconhecida |
| Regra atraso | recebimento depois da prometida | desconhecida |
| Filial | branch/consolidado autorizado | nome sugere SC |
| Período | start/end/competência | desconhecido |
| Granularidade | KPI + série + ranking | desconhecida |

**Veredito:** complementar/possivelmente especializado até E1.S1. Não declarar duplicata.

O Portal deve preferir `purchase-order-otd` / `panel` / `series` existentes antes de propor SQL novo.

---

## Controle de Estoques BI × Dashboard × ESTSEG

| Conceito | Dashboard stock | ESTSEG | BI Estoque SC |
|---|---|---|---|
| estoque físico/qty | sim | saldo usado na regra | desconhecido |
| valor | sim | não é foco | desconhecido |
| giro | página própria | não | desconhecido |
| cobertura | auxiliar/definição própria | projeção/consumo | desconhecido |
| ESTSEG | não | canônico | desconhecido |
| projeção | não | sim | desconhecido |

**Veredito:** não são o mesmo produto. Portal mantém jornadas distintas e compõe no Produto 360 quando fizer sentido.

---

## Indicadores Sheets × Strategic Indicators

- fórmula TOTVS: api-delpi;
- meta canônica: Strategic Indicators;
- realizado de savings atual: Sheets via api-delpi;
- Portal não cria segunda meta nem copia planilha para Postgres.

Destino do app Sheets depende de E1.S1/P-07.

---

## Onde o item é usado

`get_product_parents` é capability nativa reutilizável. Isso não prova paridade do BI externo.

Decisão:

```text
Portal Produto 360
→ supplies-api
→ api-delpi get_product_parents
```

Sem SQL duplicado. BI só muda de estado após comparação.

---

## Outras sobreposições

| Par | Relação |
|---|---|
| PO-OTD API × OTD dashboard | API mais rica sem UI; reutilizar contratos existentes |
| TV stock alert × ESTSEG | superfície especializada; não absorver TV |
| Safety-stock price history × product price history | família irmã; compor sem mudar semântica |
| Frete financeiro × custo de item | complementar; Financeiro continua owner |
| Qualidade × Supplier 360 | projeção controlada; processo continua na Qualidade |

---

## Falsos positivos

- materiais-terceiros ≠ estoque de MP de compra;
- inspeções de entrada ≠ alçada;
- CPV ≠ valor de estoque;
- `C7_APROV` ≠ status operacional da SC;
- vários endpoints sobre o mesmo recurso ≠ várias permissions obrigatórias.
