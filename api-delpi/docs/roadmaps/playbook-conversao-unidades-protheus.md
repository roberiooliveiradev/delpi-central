# Playbook DELPI — Conversão correta de unidades no Protheus

**Versão:** jun/2026  
**Espelho RAG (agente chat):** [`minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt`](../../../minha-delpi-ai-api/docs/knowledge/domains/agents/minha-delpi-chat/produto-conversao-unidades-protheus.txt)

---

## 1. Objetivo

Este playbook explica como interpretar e converter unidades de medida no Protheus DELPI em **quatro contextos distintos**, e como as **rotas da api-delpi** aplicam a convenção produtiva — em especial PA com `B1_UM = MI` (milheiro).

| Contexto | Fonte Protheus | Uso típico |
|----------|----------------|-------------|
| Existe / descrição da unidade | `SAH010` | Validar código UM; **não calcula conversão** |
| Produção / estrutura / BOM | `SG1010` + `SB1010` | Rotas `/structure`, `/cost-impact-simulation`, `/stock` |
| Cadastro do produto | `SB1010` (`B1_UM`, `B1_CONV`, …) | `GET /products/{code}` |
| Fiscal / DIPI / NF-e | `SB5010` | Integrações fiscais (fora das rotas de BOM) |
| OP / consumo real | `SC2010` + `SD4010` + `SB1010` | `/production-status`, Playbook 15 |

**Regra-mãe:** separar o **objetivo** da conversão antes de calcular. Nunca misturar regra fiscal com regra produtiva.

---

## 2. Convenção DELPI — MI (milheiro)

No cadastro DELPI, produto acabado (PA) frequentemente usa:

```text
B1_UM = MI
1 MI = 1000 peças (PC ou UN)
```

Duas bases de cálculo coexistem na operação:

| Base | Significado | Quando usar |
|------|-------------|-------------|
| **Por 1 PA / 1 MI** | Quantidades da BOM para fabricar **1 milheiro** | Rotas api-delpi, simulador de custo, estoque «por PA» |
| **Por 1 peça** | Necessidade unitária avulsa | Engenharia, desenho, cálculo manual |

Conversão entre bases (PA em MI):

```text
quantidade_por_1_peça = quantidade_por_1_MI / 1000
quantidade_por_1_MI   = quantidade_por_1_peça × 1000
```

---

## 3. Implementação na api-delpi

### 3.1 Serviço canônico

| Artefato | Caminho |
|----------|---------|
| Serviço | `app/domain/services/product/product_pa_bom_reference_service.py` |
| Perfil JSON | `app/content/product_pa_bom_reference.json` |

Para `B1_UM = MI`:

```json
{
  "referenceQuantity": 1,
  "referenceUnit": "PA",
  "catalogUnit": "MI",
  "catalogQuantityPerReference": 1,
  "bomQuantityFactor": 1
}
```

**Interpretação:** quantidades acumuladas na BOM (`SG1010`) já representam necessidade para **1 milheiro**. A API **não divide por 1000** automaticamente (`bomQuantityFactor = 1`).

Campo exposto nas respostas: `pa_reference` (e `product.pa_reference`).

### 3.2 Rotas que consomem a convenção

| Rota | Campo de quantidade | Base |
|------|---------------------|------|
| `GET /products/{code}/structure` | `accumulated_quantity` / `G1_QUANT` | Por 1 PA (1 MI se `B1_UM=MI`) |
| `GET /products/{code}/structure/exclusivity` | `accumulated_quantity` | Idem |
| `GET /products/{code}/cost-impact-simulation` | `quantity_per_pa` | Por 1 PA |
| `GET /products/{code}/stock` (playbook) | `quantity_required_for_one_pa` | Por 1 PA |
| `GET /products/directives/{identifier}` | estrutura + cobertura estoque | Por 1 PA |
| `GET /products/{code}/factory-status` | blocos structure / stock | Por 1 PA |

### 3.3 Fórmula do simulador de custo

Ver também [`playbook-simulador-impacto-custos-pa.md`](./playbook-simulador-impacto-custos-pa.md).

```text
extended_cost = quantity_per_pa × unit_cost
impacto % materiais = extended_cost / Σ(extended_cost) × 100
simulação +N%       = unit_cost × (1 + N/100)
```

- `unit_cost`: `B1_CUSTD` (`price_source=standard_cost`) ou `B1_UPRC` (`last_purchase`).
- `B1_CUSTD` do PA está na unidade `B1_UM` (MI quando aplicável).

---

## 4. Tabelas Protheus

### 4.0 SAH010 — Cadastro de unidades de medida

A **SAH010** é o cadastro mestre das unidades de medida (produtos, estruturas, NF, compras, estoque, produção).

**Não calcula conversão** — apenas registra que a unidade existe e sua descrição.

Exemplos: `UN` = Unidade · `PC` = Peça · `MI` = Milheiro · `MT` = Metro · `KG` = Quilograma · `CX` = Caixa · `RL` = Rolo

| Tabela | Campo | Uso da SAH010 |
|--------|-------|---------------|
| `SB1010` | `B1_UM` | Unidade principal |
| `SB1010` | `B1_SEGUM` | Segunda unidade |
| `SB1010` | `B1_UM3` | Terceira unidade |
| `SC2010` | `C2_UM` | Unidade da OP |
| `SD4010` | `D4_UM` (quando existir) | Consumo/empenho |
| `SD1010` | `D1_UM` (quando existir) | NF de entrada |
| `SB5010` | `B5_UMDIPI` | Unidade fiscal/DIPI |

| Campo | Descrição |
|-------|-----------|
| `AH_FILIAL` | Filial |
| `AH_UNIMED` | Código da unidade |
| `AH_DESCPO` | Descrição (ex.: `MI` → MILHEIRO) |
| `D_E_L_E_T_` | Exclusão lógica |

**O que a SAH010 não guarda:** fatores como `1 MI = 1000 PC` ou `1 MT = 1000 mm`.

| Necessidade | Fonte correta |
|-------------|---------------|
| Fator principal ↔ segunda unidade | `SB1010.B1_CONV` + `B1_TIPCONV` |
| Unidade principal / segunda | `SB1010.B1_UM` / `B1_SEGUM` |
| Conversão fiscal/DIPI | `SB5010.B5_CONVDIP` |
| Quantidade na BOM | `SG1010.G1_QUANT` |

**SQL — listar unidades:**

```sql
SELECT AH_FILIAL, AH_UNIMED AS UNIDADE, AH_DESCPO AS DESCRICAO
FROM SAH010
WHERE D_E_L_E_T_ = ''
ORDER BY AH_UNIMED;
```

**SQL — validar unidade do produto:**

```sql
SELECT P.B1_COD, P.B1_DESC, P.B1_UM, U.AH_DESCPO AS DESCRICAO_UNIDADE
FROM SB1010 P
LEFT JOIN SAH010 U ON U.AH_UNIMED = P.B1_UM AND U.D_E_L_E_T_ = ''
WHERE P.D_E_L_E_T_ = '' AND P.B1_COD = '90260882';
```

**SQL — produtos com unidade não cadastrada:**

```sql
SELECT P.B1_COD, P.B1_DESC, P.B1_UM
FROM SB1010 P
LEFT JOIN SAH010 U ON U.AH_UNIMED = P.B1_UM AND U.D_E_L_E_T_ = ''
WHERE P.D_E_L_E_T_ = '' AND ISNULL(P.B1_UM, '') <> '' AND U.AH_UNIMED IS NULL;
```

> **Conclusão:** `SAH010` = referência de unidades · `SB1010` = unidade e conversão do produto · `SB5010` = fiscal · `SG1010` = quantidade da estrutura.

### 4.1 SB1010 — Cadastro de produtos

| Campo | Descrição |
|-------|-----------|
| `B1_COD` | Código |
| `B1_DESC` | Descrição |
| `B1_TIPO` | `PA`, `PI`, `MP`, … |
| `B1_UM` | Unidade principal |
| `B1_SEGUM` | Segunda unidade |
| `B1_CONV` | Fator entre principal e segunda |
| `B1_TIPCONV` | `M` = multiplica; `D` = divide |
| `B1_CUSTD` | Custo padrão (na `B1_UM`) |
| `B1_UPRC` | Último preço compra |
| `D_E_L_E_T_` | Exclusão lógica (`''` = ativo) |

Conversão cadastral:

```text
Se B1_TIPCONV = M:  qtd_convertida = qtd × B1_CONV
Se B1_TIPCONV = D:  qtd_convertida = qtd / B1_CONV
```

Exemplo: produto em MI, `1 MI = 1000 PC` → `2 MI × 1000 = 2000 PC`.

### 4.2 SG1010 — Estrutura (BOM)

| Campo | Descrição |
|-------|-----------|
| `G1_COD` | Produto pai |
| `G1_COMP` | Componente |
| `G1_QUANT` | Quantidade na estrutura |
| `G1_FIM` | Fim de vigência (`> hoje` = vigente) |
| `D_E_L_E_T_` | Exclusão lógica |

A SG1010 informa **quanto** entra na BOM; a SB1010 informa **em qual unidade** interpretar.

### 4.3 SB5010 — Complemento fiscal

Usar **somente** para DIPI / NF-e / unidade tributável:

```text
quantidade_fiscal = quantidade_comercial × B5_CONVDIP
```

| Campo | Descrição |
|-------|-----------|
| `B5_COD` | Código (= `B1_COD`) |
| `B5_UMDIPI` | Unidade fiscal |
| `B5_CONVDIP` | Fator fiscal |

**Não** usar `SB5010` para cálculo produtivo nem para rotas de estrutura/custo.

### 4.4 SC2010 — Ordem de produção

| Campo | Descrição |
|-------|-----------|
| `C2_OP` | Número da OP |
| `C2_PRODUTO` | Produto produzido |
| `C2_QUANT` | Quantidade planejada |
| `C2_QUJE` | Quantidade produzida |
| `C2_UM` | Unidade da OP |

### 4.5 SD4010 — Consumo / empenho

| Campo | Descrição |
|-------|-----------|
| `D4_OP` | OP |
| `D4_COD` | Item consumido |
| `D4_QUANT` | Quantidade consumida |
| `D4_QTNECES` | Quantidade necessária |

Relações:

```text
SG1010.G1_COD  = SB1010.B1_COD (pai)
SG1010.G1_COMP = SB1010.B1_COD (componente)
SC2010.C2_OP   = SD4010.D4_OP
SB1010.B1_COD  = SB5010.B5_COD (fiscal)
```

---

## 5. Conversão produtiva — por 1 peça (manual)

Passos:

1. Ler `B1_UM` do PA em `SB1010`.
2. Explodir BOM em `SG1010` (vigência `G1_FIM > hoje`).
3. Ler `B1_UM` de cada componente.
4. Normalizar para **1 peça**:

```text
Se B1_UM do pai = MI:  qtd_1_peça = G1_QUANT / 1000
Se B1_UM do pai = PC ou UN:  qtd_1_peça = G1_QUANT
```

Componentes intermediários em MI dentro de PA em MI exigem explosão multinível antes da divisão (ver exemplo §6).

---

## 6. Exemplo real — PA 90260882

| Campo | Valor |
|-------|-------|
| Código | `90260882` |
| Descrição | PROTETOR TERM CABO 145 C NF 7AM/CD79 |
| Tipo | PA |
| Unidade | MI |

Trecho da estrutura (1 MI do PA):

| Nível | Código | UM | Qtd na BOM |
|-------|--------|-----|------------|
| 2 | 10080626 | PC | 1000 |
| 2 | 10090482 | PC | 1000 |
| 2 | 50213309 | MI | 2 |
| 3 | 10380035 (dentro 50213309) | MT | 63 |

**Por 1 peça** (÷1000 na base MI):

| Componente | Cálculo | Resultado |
|------------|---------|-----------|
| 10080626 | 1000 PC / 1000 | 1 PC |
| 10090482 | 1000 PC / 1000 | 1 PC |
| 50213309 | 2 MI → 2000 peças / 1000 | 2 PC |
| 10380035 | 63 MT / 1000 × 2 peças do PI | 0,126 MT (126 mm) |

**Por 1 MI (api-delpi):** usar quantidades da BOM diretamente — ex.: 10080626 = **1000 PC por 1 MI**, não 1 PC.

Produto homologado simulador: **`90261255`** (PA, MI) — ver [`playbook-simulador-impacto-custos-pa.md`](./playbook-simulador-impacto-custos-pa.md).

---

## 7. Conversão fiscal (exemplo)

```text
Unidade comercial = MI
Quantidade comercial = 0,5
B5_UMDIPI = UN
B5_CONVDIP = 1000

Quantidade fiscal = 0,5 × 1000 = 500 UN
```

---

## 8. Fórmulas rápidas

| Conversão | Fórmula |
|-----------|---------|
| MI → PC/UN | `Qtd_PC = Qtd_MI × 1000` |
| PC/UN → MI | `Qtd_MI = Qtd_PC / 1000` |
| MT → mm | `Qtd_MM = Qtd_MT × 1000` |
| mm → MT | `Qtd_MT = Qtd_MM / 1000` |
| BOM → 1 peça (PA em MI) | `G1_QUANT / 1000` |
| BOM → 1 PA/MI (api-delpi) | `G1_QUANT` (sem ÷1000) |

---

## 9. SQL modelo — unidade do produto

```sql
SELECT
    B1_COD, B1_DESC, B1_TIPO, B1_UM,
    B1_SEGUM, B1_CONV, B1_TIPCONV, B1_UM3, B1_CONV3
FROM SB1010
WHERE D_E_L_E_T_ = ''
  AND B1_COD = '90260882';
```

Equivalente REST: `GET /products/90260882?view=summary`.

---

## 10. SQL modelo — estrutura com unidades

```sql
SELECT
    E.G1_COD AS PRODUTO_PAI,
    PAI.B1_UM AS UM_PAI,
    E.G1_COMP AS COMPONENTE,
    COMP.B1_UM AS UM_COMPONENTE,
    E.G1_QUANT AS QTD_ESTRUTURA
FROM SG1010 E
INNER JOIN SB1010 PAI ON PAI.B1_COD = E.G1_COD AND PAI.D_E_L_E_T_ = ''
INNER JOIN SB1010 COMP ON COMP.B1_COD = E.G1_COMP AND COMP.D_E_L_E_T_ = ''
WHERE E.D_E_L_E_T_ = ''
  AND E.G1_COD = '90260882';
```

Preferir: `GET /products/90260882/structure` ou `/structure/exclusivity`.

---

## 11. SQL modelo — necessidade por 1 peça (PA em MI)

```sql
SELECT
    E.G1_COMP AS COMPONENTE,
    COMP.B1_UM AS UM_COMPONENTE,
    E.G1_QUANT AS QTD_PARA_1_MI,
    CASE
        WHEN PAI.B1_UM = 'MI' THEN E.G1_QUANT / 1000.0
        ELSE E.G1_QUANT
    END AS QTD_PARA_1_PECA
FROM SG1010 E
INNER JOIN SB1010 PAI ON PAI.B1_COD = E.G1_COD AND PAI.D_E_L_E_T_ = ''
INNER JOIN SB1010 COMP ON COMP.B1_COD = E.G1_COMP AND COMP.D_E_L_E_T_ = ''
WHERE E.D_E_L_E_T_ = ''
  AND E.G1_COD = '90260882';
```

---

## 12. SQL modelo — conversão fiscal

```sql
SELECT
    P.B1_COD, P.B1_UM AS UM_COMERCIAL,
    F.B5_UMDIPI AS UM_FISCAL, F.B5_CONVDIP AS FATOR_FISCAL,
    1 AS QTD_COMERCIAL,
    CASE WHEN ISNULL(F.B5_CONVDIP, 0) > 0 THEN F.B5_CONVDIP ELSE 1 END AS QTD_FISCAL
FROM SB1010 P
LEFT JOIN SB5010 F ON F.B5_COD = P.B1_COD AND F.D_E_L_E_T_ = ''
WHERE P.D_E_L_E_T_ = '' AND P.B1_COD = '90260882';
```

---

## 13. SQL modelo — OP com consumo

```sql
SELECT
    OP.C2_OP, OP.C2_PRODUTO, OP.C2_QUANT, OP.C2_QUJE, OP.C2_UM,
    C.D4_COD, ITEM.B1_UM, C.D4_QUANT, C.D4_QTNECES
FROM SC2010 OP
INNER JOIN SD4010 C ON C.D4_FILIAL = OP.C2_FILIAL AND C.D4_OP = OP.C2_OP AND C.D_E_L_E_T_ = ''
INNER JOIN SB1010 ITEM ON ITEM.B1_COD = C.D4_COD AND ITEM.D_E_L_E_T_ = ''
WHERE OP.D_E_L_E_T_ = '' AND OP.C2_OP = 'NUMERO_DA_OP';
```

Preferir: `GET /products/{code}/production-status`.

---

## 14. Erros comuns

| Erro | Consequência |
|------|--------------|
| Ignorar `B1_UM` do PA ao ler SG1010 | Consumo 1000× maior ou menor |
| Tratar MI como PC | Necessidade de material errada |
| Usar `B1_CONV` para fiscal sem `SB5010` | NF com unidade tributável incorreta |
| Usar `SB5010` em cálculo produtivo | Mistura fiscal × produção |
| Omitir `D_E_L_E_T_ = ''` | Registros excluídos na consulta |
| Dividir tudo por 1000 sem checar UM do pai | PA em PC/UN fica errado |
| Confundir «1 peça» com «1 PA/MI» na api-delpi | Simulador ou estrutura com escala errada |
| Usar `SAH010` para fator de conversão | Fator inexistente — usar `SB1010` / `SB5010` / `SG1010` |

---

## 15. Ordem de validação

1. Produto ativo? → `SB1010` ou `GET /products/{code}`
2. Unidade cadastrada (descrição)? → `SAH010` (`AH_UNIMED`, `AH_DESCPO`)
3. Unidade do pai? → `B1_UM`
4. Estrutura vigente? → `SG1010` ou `/structure`
5. Unidade de cada componente? → `SB1010.B1_UM`
6. Segunda UM / fator? → `B1_SEGUM`, `B1_CONV`, `B1_TIPCONV`
7. Contexto fiscal? → `SB5010`
8. Consumo real OP? → `SC2010` + `SD4010` ou `/production-status`
9. Impacto de custo / ranking MPs? → `/cost-impact-simulation` (somente PA)

---

## 16. Perguntas típicas → rota

| Pergunta | Rota | Notas |
|----------|------|-------|
| Estrutura / BOM | `/structure` | Quantidades por 1 PA/MI |
| MPs exclusivas | `/structure/exclusivity` | Idem + flag exclusividade |
| Materiais que mais impactam custo | `/cost-impact-simulation` | `adjustment_percent=0` |
| Simular +10% nos materiais | `/cost-impact-simulation?adjustment_percent=10` | Somente PA |
| Quanto de MP para **1 peça** (PA MI) | `/structure` → qty / 1000 | Pós-processamento |
| Quanto para **1 milheiro** | `/structure` ou simulador | Qty direta da API |
| Consumo real da OP | `/production-status` | |
| Unidade fiscal NF | SQL `SB5010` | Não há rota dedicada |

---

## 17. Resumo

```text
Referência UM      → SAH010 (cadastro/descrição — sem fator)
Produção / BOM     → SG1010 + SB1010  → rotas /structure, /cost-impact-simulation
Cadastro           → SB1010
Fiscal / NF-e      → SB5010
OP / consumo       → SC2010 + SD4010 + SB1010

MI: 1 MI = 1000 peças
MT: 1 MT = 1000 mm

Manual (1 peça, PA em MI):  qtd_estrutura / 1000
api-delpi (1 PA/MI):        qtd_estrutura × bomQuantityFactor (1 para MI)

Fiscal: qtd_fiscal = qtd_comercial × B5_CONVDIP
```

---

## 18. Referências cruzadas

| Documento | Conteúdo |
|-----------|----------|
| [`playbook-simulador-impacto-custos-pa.md`](./playbook-simulador-impacto-custos-pa.md) | Ranking e simulação de custo |
| [`playbook-estrutura-produto-exclusividade-mp.md`](./playbook-estrutura-produto-exclusividade-mp.md) | BOM + exclusividade |
| [`playbook-situacao-de-producao-pa.md`](./playbook-situacao-de-producao-pa.md) | OP e apontamentos |
| [`02-produtos.md`](../api/02-produtos.md) | Referência HTTP das rotas |
| [`11-guia-agente-chat.md`](../api/11-guia-agente-chat.md) | Mapa intenção → rota |
