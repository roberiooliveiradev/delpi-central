# Playbook de Correção — Rotas LMP / Amostra / Outros

## 1. Objetivo

Corrigir a lógica das rotas de listagem de LMPs, Amostras e Outros para que a listagem reflita o fluxo real do CRM/Engenharia, sem depender do RQ-060 como regra principal.

O RQ-060 deve ser usado apenas como controle, evidência e auditoria manual.

A regra principal deve nascer do histórico real do CRM/Protheus, principalmente da tabela `AIJ010`, cruzada com a revisão atual da OV no `AD1010`.

---

## 2. Problemas encontrados

Durante a validação foram identificados estes problemas:

1. O sistema lista OVs que apenas tocaram rapidamente a engenharia.
2. Algumas OVs chegam na engenharia por engano e são movidas depois.
3. A mesma OV pode existir em filial antiga e filial atual.
4. A mesma OV pode ter histórico antigo de 2019/2020 e fluxo novo de 2026.
5. Algumas OVs possuem marcador de LMP e Amostra na mesma revisão.
6. A classificação por “último marcador” pode transformar uma LMP real em Amostra.
7. O `AD1_DESCRI` nem sempre possui referência suficiente para comparar com a planilha.
8. O RQ-060 pode ter erro de controle, como a mesma OV associada a dois LMP Ano diferentes.

Exemplo de erro de controle encontrado:

```text
OV 000061 → LMP Ano 064/26
OV 000061 → LMP Ano 086/26
```

Portanto, o RQ-060 não deve comandar a listagem. Ele deve ser usado apenas para conferência.

---

## 3. Regra-mãe da correção

```text
AIJ010 define se chegou na engenharia.
Tempo mínimo define se chegou de verdade.
AD1010 revisão atual define filial/revisão correta.
Prioridade LMP > Amostra define a classificação.
RQ-060 serve apenas para auditoria e controle manual.
```

---

## 4. Regra funcional nova

Uma OV só deve aparecer na listagem principal se cumprir todos os critérios:

```text
1. Está ativa no AD1010.
2. Está em uma filial válida.
3. O evento AIJ010 pertence à mesma filial da OV.
4. O evento AIJ010 pertence à revisão atual da OV.
5. Possui evento real de chegada na engenharia.
6. Se classificada como **LMP**, permaneceu no fluxo por pelo menos 30 minutos.
7. Se classificada como **AMOSTRA** ou **OUTRO**, pode listar mesmo com passagem pontual (0 minutos).
```

---

## 5. Conceitos separados

A correção deve separar três conceitos que hoje ficam misturados.

### 5.1 Chegou na Engenharia

Usar `engineering_support_process_stages`.

Representa OVs que passaram por etapas consideradas engenharia.

### 5.2 É LMP

Usar `lmp_anchor_process_stages`.

Representa marcador real de LMP.

### 5.3 É Amostra

Usar `sample_anchor_process_stages`.

Representa marcador real de Amostra.

### 5.4 É Outros

Quando chegou na engenharia, ficou tempo suficiente, mas não possui marcador confiável de LMP ou Amostra.

---

## 6. Alteração no `lmp_query_settings.py`

Adicionar configuração de tempo mínimo de permanência em engenharia.

### Patch sugerido

```python
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01", "02"])

    # Tempo mínimo para considerar que a OV realmente chegou na engenharia.
    # Usado para eliminar casos de passagem por engano.
    min_engineering_residence_minutes: int = 30

    # Prioridade de classificação quando a OV possui mais de um marcador.
    # Se tiver LMP e Amostra, LMP prevalece.
    listing_kind_priority: Dict[str, int] = field(
        default_factory=lambda: {
            "LMP": 2,
            "AMOSTRA": 1,
            "OUTROS": 0,
        }
    )

    lmp_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000003", "000012"],
            "000003": ["000003", "000012"],
        }
    )

    lmp_followup_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000013"],
            "000003": ["000013"],
        }
    )

    engineering_support_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000003", "000008", "000012"],
            "000003": ["000003", "000012"],
        }
    )

    sample_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000008"],
            "000003": ["000002", "000008"],
        }
    )

    lmp_finalized_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
            "000003": ["000012"],
        }
    )

    engineering_status_labels: Dict[str, str] = field(
        default_factory=lambda: {
            "in_progress": "ABERTA",
            "finished": "FINALIZADA",
            "partial": "PARCIAL",
            "returned": "RETORNADA",
        }
    )

    root_product_types: List[str] = field(default_factory=lambda: ["PA"])
    pi_product_types: List[str] = field(default_factory=lambda: ["PI"])
    active_delete_flag: str = ""
    max_bom_level: int = 10
```

---

## 7. Correção de prioridade LMP x Amostra

### Problema

Hoje a classificação pode escolher o marcador mais recente.

Isso gera erro quando uma OV tem LMP e Amostra na mesma revisão ou no mesmo fluxo.

Caso validado:

```text
OV 000124
Aparecia como Amostra.
Deveria ser LMP.
```

### Regra correta

```text
Se existe marcador LMP na revisão válida → LMP
Senão, se existe marcador Amostra → AMOSTRA
Senão → OUTROS
```

### Onde alterar

Função:

```python
_sql_listing_anchor_marker_cte()
```

### Trecho problemático

```sql
ROW_NUMBER() OVER (
    PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
    ORDER BY
        R.AIJ_DTINIC DESC,
        R.AIJ_HRINIC DESC,
        CASE
            WHEN R.LISTING_KIND = ? THEN 1
            ELSE 0
        END DESC,
        R.R_E_C_N_O_ DESC
) AS RN_DESC
```

### Substituição sugerida

```sql
ROW_NUMBER() OVER (
    PARTITION BY R.AIJ_FILIAL, R.AIJ_NROPOR
    ORDER BY
        CASE
            WHEN R.LISTING_KIND = ? THEN 2 -- LMP
            WHEN R.LISTING_KIND = ? THEN 1 -- AMOSTRA
            ELSE 0
        END DESC,
        R.AIJ_DTINIC DESC,
        R.AIJ_HRINIC DESC,
        R.R_E_C_N_O_ DESC
) AS RN_DESC
```

### Parâmetros necessários

Enviar nesta ordem:

```python
LISTING_KIND_LMP,
LISTING_KIND_SAMPLE,
```

---

## 8. Correção de permanência mínima na engenharia

### Regra final (jun/2026)

O filtro de tempo **não é geral da listagem** — é filtro de **LMP**:

```text
O filtro de 30 minutos aplica SOMENTE para LMP.
AMOSTRA não passa pelo filtro de tempo.
OUTRO não passa pelo filtro de tempo.
```

| Tipo da listagem | Aplica filtro de 30 minutos? | Deve listar quando tempo = 0? |
|---|---:|---:|
| LMP | Sim | Não |
| AMOSTRA | Não | Sim |
| OUTRO | Não | Sim |

Valor homologado: `min_engineering_residence_minutes = 30`.

### Caso que motivou o ajuste

OV `003578` (Amostra, jun/2026): `Minutos critério: 0` — deve listar mesmo com passagem pontual.

### Onde aplicar

Aplicar o filtro nos selects finais da listagem, após o join com `EngenhariaResumoUltimaRevisao`, **condicionado ao `LISTING_KIND`**.

---

## 9. Alteração em `_staged_final_select`

### Situação atual

O select final traz os dados de `CandidateLMPs` e faz `LEFT JOIN` com `#Delpi_EngResumo`.

### SQL incorreto (não usar)

```sql
WHERE ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
```

Esse filtro exclui Amostras pontuais que devem aparecer.

### SQL correto

```sql
WHERE
    C.LISTING_KIND <> 'LMP'
    OR ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
```

### Exemplo

```sql
SELECT
    C.AD1_FILIAL AS branch,
    C.AD1_NROPOR AS sale_number,
    C.AD1_DESCRI AS sale_description,
    C.LISTING_KIND AS listing_kind,
    C.LMP_START_DATE AS start_date,
    C.LMP_END_DATE AS end_date,
    H.ENGINEERING_STATUS AS engineering_status,
    H.QTD_PASSAGENS_ENG AS qtd_engineering_entries,
    H.QTD_PASSAGENS_ENCERRADAS AS qtd_engineering_closed,
    H.QTD_AVANCOU_ENG AS qtd_advanced_from_engineering,
    H.QTD_RETORNOU_ENG AS qtd_returned_from_engineering,
    H.TEMPO_TOTAL_MINUTOS_ENG AS engineering_total_minutes,
    {qtd_pi_select}
FROM {self._TEMP_CANDIDATES} C
LEFT JOIN {self._TEMP_ENG_RESUMO} H
    ON H.AIJ_FILIAL = C.AD1_FILIAL
   AND H.AIJ_NROPOR = C.AD1_NROPOR
{qtd_pi_join}
WHERE
    C.LISTING_KIND <> 'LMP'
    OR ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
GROUP BY
    C.AD1_FILIAL,
    C.AD1_NROPOR,
    C.AD1_DESCRI,
    C.LISTING_KIND,
    C.LMP_START_DATE,
    C.LMP_END_DATE,
    H.ENGINEERING_STATUS,
    H.QTD_PASSAGENS_ENG,
    H.QTD_PASSAGENS_ENCERRADAS,
    H.QTD_AVANCOU_ENG,
    H.QTD_RETORNOU_ENG,
    H.TEMPO_TOTAL_MINUTOS_ENG
    {qtd_pi_group_by}
```

### Importante

Como o SQL passa a ter mais um `?`, o batch precisa adicionar este parâmetro:

```python
self.settings.min_engineering_residence_minutes
```

---

## 10. Alteração no count

A contagem da página precisa usar o mesmo filtro da listagem.

### Patch em `_staged_count_select`

Adicionar o mesmo filtro condicional por `LISTING_KIND` antes do `GROUP BY`:

```sql
WHERE
    C.LISTING_KIND <> 'LMP'
    OR ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
```

Se o count não receber esse filtro, a página pode mostrar total diferente da lista.

---

## 11. Atenção ao parâmetro no staged batch

Como `_staged_final_select()` e `_staged_count_select()` hoje retornam apenas string SQL, será necessário ajustar o desenho para que o parâmetro de tempo mínimo seja incluído em `final_params`.

### Exemplo para listagem simples

Em `list_lmps()`:

```python
final_select = self._staged_final_select(
    include_qtd_pi=include_qtd_pi,
    order_by=True,
)

batch_sql, batch_params = self._build_staged_batch(
    request,
    include_qtd_pi=include_qtd_pi,
    final_select=final_select,
    final_params=(self.settings.min_engineering_residence_minutes,),
)
```

### Exemplo para paginação

Em `list_lmps_page()`:

```python
combined_final = f"""
    {count_select};
    {rows_select}
    OFFSET ? ROWS
    FETCH NEXT ? ROWS ONLY
"""

batch_sql, batch_params = self._build_staged_batch(
    request,
    include_qtd_pi=include_qtd_pi,
    final_select=combined_final,
    final_params=(
        self.settings.min_engineering_residence_minutes,
        self.settings.min_engineering_residence_minutes,
        offset,
        page_size,
    ),
)
```

O parâmetro precisa aparecer duas vezes porque o filtro será usado no count e no select de linhas.

---

## 12. Regra de revisão atual

Para evitar misturar LMP antiga com nova, os eventos da `AIJ010` devem ser filtrados pela revisão atual do `AD1010`.

### Regra obrigatória

Sempre que a listagem mensal for calculada, usar:

```sql
AD1.AD1_FILIAL = A.AIJ_FILIAL
AND AD1.AD1_NROPOR = A.AIJ_NROPOR
AND AD1.AD1_REVISA = A.AIJ_REVISA
```

### Onde revisar

Revisar estes blocos:

```python
_sql_eng_support_ov_reference_cte()
_sql_listing_anchor_marker_cte()
_sql_historico_ov_cte()
_sql_candidate_lmps_cte()
```

### Observação

Hoje existem trechos que amarram apenas por filial e OV.

Isso permite misturar:

```text
OV antiga de filial 01
com
OV nova de filial 02
```

ou:

```text
revisão antiga
com
revisão atual
```

---

## 13. Correção da classificação final

Na saída final, o tipo deve ser calculado assim:

```sql
CASE
    WHEN C.QTD_LMP > 0 THEN 'LMP'
    WHEN C.QTD_AMOSTRA > 0 THEN 'AMOSTRA'
    ELSE 'OUTROS'
END
```

Evitar depender exclusivamente do último evento ou do último marcador.

---

## 14. Query de homologação mensal

Usar esta query para validar mês a mês antes de publicar.

```sql
WITH PARAM AS (
    SELECT
        '20260401' AS DATA_INICIO,
        '20260501' AS DATA_FIM,
        30 AS MINUTOS_MIN_ENG
),

AD1_ATIVA AS (
    SELECT
        AD1.AD1_FILIAL,
        AD1.AD1_NROPOR,
        AD1.AD1_REVISA,
        AD1.AD1_DESCRI
    FROM AD1010 AD1
    WHERE
        AD1.D_E_L_E_T_ = ''
        AND AD1.AD1_FILIAL IN ('01','02')
),

AIJ_REV_ATUAL AS (
    SELECT
        A.AIJ_FILIAL,
        A.AIJ_NROPOR,
        A.AIJ_REVISA,
        A.AIJ_PROVEN,
        A.AIJ_STAGE,
        A.AIJ_DTINIC,
        A.AIJ_HRINIC,
        A.AIJ_DTENCE,
        A.AIJ_HRENCE,
        A.R_E_C_N_O_,

        CONVERT(
            DATETIME,
            STUFF(STUFF(A.AIJ_DTINIC,5,0,'-'),8,0,'-')
            + ' ' + A.AIJ_HRINIC + ':00',
            120
        ) AS DT_HR_INICIO
    FROM AIJ010 A
    INNER JOIN AD1_ATIVA AD1
        ON AD1.AD1_FILIAL = A.AIJ_FILIAL
       AND AD1.AD1_NROPOR = A.AIJ_NROPOR
       AND AD1.AD1_REVISA = A.AIJ_REVISA
    CROSS JOIN PARAM P
    WHERE
        A.D_E_L_E_T_ = ''
        AND A.AIJ_DTINIC >= P.DATA_INICIO
        AND A.AIJ_DTINIC <  P.DATA_FIM
        AND A.AIJ_DTINIC <> ''
        AND A.AIJ_HRINIC <> ''
),

EVENTOS AS (
    SELECT
        A.*,

        CASE
            WHEN A.AIJ_PROVEN = '000002'
             AND A.AIJ_STAGE IN ('000003','000008','000012')
            THEN 1

            WHEN A.AIJ_PROVEN = '000003'
             AND A.AIJ_STAGE IN ('000003','000012')
            THEN 1

            ELSE 0
        END AS FLAG_CHEGOU_ENG,

        CASE
            WHEN A.AIJ_PROVEN IN ('000002','000003')
             AND A.AIJ_STAGE IN ('000003','000012')
            THEN 1 ELSE 0
        END AS FLAG_LMP,

        CASE
            WHEN A.AIJ_PROVEN = '000002'
             AND A.AIJ_STAGE = '000008'
            THEN 1

            WHEN A.AIJ_PROVEN = '000003'
             AND A.AIJ_STAGE IN ('000002','000008')
            THEN 1

            ELSE 0
        END AS FLAG_AMOSTRA
    FROM AIJ_REV_ATUAL A
),

RESUMO AS (
    SELECT
        E.AIJ_FILIAL,
        E.AIJ_NROPOR,
        E.AIJ_REVISA,

        SUM(E.FLAG_CHEGOU_ENG) AS QTD_CHEGOU_ENG,
        SUM(E.FLAG_LMP) AS QTD_LMP,
        SUM(E.FLAG_AMOSTRA) AS QTD_AMOSTRA,

        MIN(CASE WHEN E.FLAG_CHEGOU_ENG = 1 THEN E.DT_HR_INICIO END) AS DT_HR_CHEGADA_ENG,
        MAX(E.DT_HR_INICIO) AS DT_HR_ULTIMO_EVENTO
    FROM EVENTOS E
    GROUP BY
        E.AIJ_FILIAL,
        E.AIJ_NROPOR,
        E.AIJ_REVISA
),

CALCULO AS (
    SELECT
        R.*,
        DATEDIFF(
            MINUTE,
            R.DT_HR_CHEGADA_ENG,
            R.DT_HR_ULTIMO_EVENTO
        ) AS MINUTOS_CRITERIO
    FROM RESUMO R
    WHERE
        R.QTD_CHEGOU_ENG > 0
)

SELECT
    CONVERT(CHAR(6), C.DT_HR_CHEGADA_ENG, 112) AS MES,
    COUNT(*) AS TOTAL,
    SUM(CASE WHEN C.QTD_LMP > 0 THEN 1 ELSE 0 END) AS TOTAL_LMP,
    SUM(CASE WHEN C.QTD_LMP = 0 AND C.QTD_AMOSTRA > 0 THEN 1 ELSE 0 END) AS TOTAL_AMOSTRA,
    SUM(CASE WHEN C.QTD_LMP = 0 AND C.QTD_AMOSTRA = 0 THEN 1 ELSE 0 END) AS TOTAL_OUTROS
FROM CALCULO C
CROSS JOIN PARAM P
WHERE
    C.MINUTOS_CRITERIO >= P.MINUTOS_MIN_ENG
GROUP BY
    CONVERT(CHAR(6), C.DT_HR_CHEGADA_ENG, 112)
ORDER BY
    MES;
```

---

## 15. Resultados esperados na homologação

| Cenário | Esperado |
|---|---:|
| Abril/2026 | 16 registros |
| Maio/2026 | 17 registros |
| OV 000124 | Deve ser LMP |
| OV 000073 | Deve entrar como LMP |
| OV 003306 | Deve ficar fora, pois não tem AIJ010 |
| OV 000061 | Deve entrar, mas deve ser tratado como possível divergência de controle |
| Passagens menores que 30 minutos | Devem ficar fora |
| Filiais antigas sem fluxo CRM | Devem ficar fora |
| Revisões antigas sem vínculo com AD1 atual | Devem ficar fora |

---

## 16. Testes manuais já validados

### Abril/2026

Com filtro de 30 minutos:

```text
Total retornado: 16
Quantidade da planilha: 16
Status: bateu
```

### Maio/2026

Com filtro de 30 minutos:

```text
Total retornado: 17
Quantidade da planilha: 17
Status: bateu
```

---

## 17. Casos especiais conhecidos

### OV 000124

```text
Problema anterior: aparecia como Amostra.
Resultado esperado: LMP.
Causa: possui marcador LMP e Amostra; LMP deve prevalecer.
```

### OV 003306

```text
Problema: consta no RQ-060 como LMP 067/26.
Resultado esperado na rota: não listar.
Motivo: não existe evento AIJ010 de engenharia.
```

### OV 000061

```text
Problema: aparece em dois RQ-060:
000061 → 064/26
000061 → 086/26

Resultado esperado na rota: listar se cumprir AIJ010 + 30 minutos.
Observação: duplicidade deve ser tratada como erro de controle, não como regra da rota.
```

---

## 18. Definição final para o desenvolvedor

A rota de LMP não deve perguntar “existe RQ-060?”.

A rota deve perguntar:

```text
Essa OV entrou no fluxo de engenharia?
Ficou tempo suficiente para ser considerada real?
Está na revisão atual da OV?
Tem marcador LMP?
Tem marcador Amostra?
```

E então classificar:

```text
Se tem LMP → LMP.
Se não tem LMP e tem Amostra → AMOSTRA.
Se chegou na engenharia e não tem LMP/Amostra → OUTRO.
```

Depois de classificar, aplicar filtro de tempo **somente** se o tipo final for LMP:

```text
Se LMP e não ficou 30 minutos → excluir.
Se AMOSTRA ou OUTRO → listar independente do tempo.
```

---

## 19. Ordem recomendada de implementação

1. Adicionar `min_engineering_residence_minutes` no settings.
2. Alterar prioridade de classificação para `LMP > AMOSTRA > OUTROS`.
3. Aplicar filtro `TEMPO_TOTAL_MINUTOS_ENG >= ?` **somente para LMP** na listagem.
4. Aplicar o mesmo filtro condicional no count.
5. Garantir que o parâmetro seja passado no batch.
6. Revisar joins com `AD1_REVISA = AIJ_REVISA`.
7. Rodar homologação de abril/2026.
8. Rodar homologação de maio/2026.
9. Validar casos 000124, 000073, 003306, 000061, 003578 e 003520.
10. Publicar.

---

## 20. Critério de aceite

A correção só deve ser aceita se:

```text
Abril/2026 = 16 registros
Maio/2026 = 17 registros
000124 = LMP
003306 = fora
000073 = LMP
000061 = entra pelo AIJ010, mas não depende do RQ-060
003578 = AMOSTRA com 0 minuto → listar
003520 = AMOSTRA com 0 minuto → listar
LMP com < 30 minutos = fora
OUTRO com 0 minuto = listar
Contagem da página = quantidade real da lista
```

---

## 21. Regra final — filtro de tempo por tipo (referência)

### Patch em `_engineering_residence_filter_sql`

```python
def _engineering_residence_filter_sql(self) -> str:
    return """
        WHERE
            C.LISTING_KIND <> 'LMP'
            OR ISNULL(H.TEMPO_TOTAL_MINUTOS_ENG, 0) >= ?
    """
```

### Exemplos esperados

| OV | Tipo | Minutos | Resultado |
|---:|---|---:|---|
| 003578 | AMOSTRA | 0 | Listar |
| 003520 | AMOSTRA | 0 | Listar |
| 000124 | LMP ou AMOSTRA (conforme classificação) | 2725 | Listar |
| LMP com passagem rápida | LMP | 0 | Não listar |
| OUTRO com passagem rápida | OUTRO | 0 | Listar |

### Resumo

```text
Filtro de tempo não é filtro geral da listagem.
Filtro de tempo é filtro de LMP.

Amostra pode ser pontual.
Outros pode ser pontual.
LMP precisa comprovar permanência mínima de 30 minutos.
```
