# GLPI #1614 — Material de terceiro com valor R$ 0,00 na acuracidade e divergência de estoque

**Data:** 17/11/2026  
**Owner do cálculo e SQL:** `api-delpi` (Suprimentos/inventário)  
**Consumidores:** Dashboard Suprimentos, TV Dashboard/GR Diário e leituras DAVI autorizadas

## Solicitação aprovada

Material pertencente a terceiros não integra o custo da DELPI. Deve **permanecer visível** nas consultas e contagens do inventário, inclusive em ajustes, séries temporais e rankings, mas sua **contribuição monetária deve ser R$ 0,00**. Não excluir do denominador da acuracidade física nem alterar dados/custo cadastrado no Protheus.

## Regra canônica

- Origem: `SB1010.B1_TPMAT` (`'2'` = produto de terceiro; `'1'` = não), diferente de remessas `SB6010`.
- A classificação usa `inventory_adjustment_product_apply` com `OUTER APPLY TOP (1)` por `B1_COD`; cadastro específico da filial do movimento tem preferência sobre cadastro global. Registros deletados não entram. A cardinalidade 0..1 impede duplicar movimentos.
- Valor gerencial do movimento: `CASE WHEN B1_TPMAT='2' THEN 0 ELSE ISNULL(D3_CUSTO1,0) END`. `D3_CUSTO1` já é valor total do ajuste, **não** custo por unidade.
- Sem cadastro SB1 elegível, a regra não presume material de terceiro e preserva a valoração original (identificação explícita obrigatória para zerar). Falhas/missing cost do material próprio continuam reportáveis.
- Quantidades `D3_QUANT`, `B7_QUANT`, natureza `RE0/DE0`, eventos SB7 e fórmula da acuracidade quantitativa **não mudam**.

## Superfícies afetadas

| Fonte | Tratamento |
|---|---|
| `GET /supplies/inventory-adjustments/summary` | `gross/net/shortage/surplus_value` total e por mês/filial/natureza zeram contribuições de terceiros; contadores/quantidades permanecem |
| `GET /supplies/inventory-adjustments` | `movement_value` e `signed_value` de terceiro = 0; linha física permanece |
| `GET /supplies/inventory-adjustments/tv/summary` | KPIs do ano/mês/período reutilizam resumo canônico, portanto R$ coerente |
| `GET /supplies/inventory-adjustments/tv/monthly-series` | Buckets dia/semana/mês/ano usam a mesma valoração |
| `GET /supplies/inventory-adjustments/tv/weekly-items` | Agrupar primeiro, ordenar TOP por valor efetivo em R$, exibindo terceiro com zero quando dentro do TOP; quantidade preservada |
| `GET /supplies/inventory-accuracy/summary` e `items` | `shortage_value/surplus_value` monetários zero; `quantity_accuracy_percentage`, contagem e saldo teórico físicos intactos |

**Importante:** O TOP-N da TV pode não mostrar um terceiro com valor zero caso existam N movimentos de valor maior. Isso não é exclusão: a API retorna o TOP do impacto financeiro; a consulta paginada de ajustes mantém todos os materiais.

**Fora de escopo:** base R07 da Controladoria (custo histórico as-of/TTAT), outros KPIs de estoque e alterações de dados no ERP. Divergências financeiras históricas devem ser reconciliadas antes de equiparar R07 e o GR Diário.

## Testes e deploy

- Testes: `api-delpi/tests/test_inventory_third_party_zero_value_1614.py`, `test_supplies_inventory_adjustments.py`, `test_tv_inventory_divergences_1598.py`, `test_supplies_inventory_accuracy.py`.
- CI: executar `PYTHONPATH=. pytest tests/test_inventory_third_party_zero_value_1614.py tests/test_supplies_inventory_adjustments.py tests/test_tv_inventory_divergences_1598.py tests/test_supplies_inventory_accuracy.py -q` a partir da pasta `api-delpi`.
- Verificar no Protheus (somente leitura) pelo menos um `B1_TPMAT=2` com `D3_DOC='INVENT'` e `D3_CUSTO1<>0`, mais um próprio `B1_TPMAT=1`, comparando quantidades idênticas e divergências R$ após ajuste.
- Confirmar não alteração em `B1_TPMAT`, `D3_CUSTO1`, registros SB7 e contagens.
- Sem mudança de contratos de rotas/operationIds, migrações, MFE, permissões ou sync OpenAPI.
- Após a PR passar pelos testes e ser incorporada em `main`, no host de produção:

```bash
cd /home/operador/projetos/delpi-central
git pull --ff-only origin main
bash ./infra/scripts/up-prod-sequential.sh --build api-delpi
```

**Aceite:** manter chamado #1614 aberto até validação dos valores em produção. Nunca encerrar apenas com merge/CI.
