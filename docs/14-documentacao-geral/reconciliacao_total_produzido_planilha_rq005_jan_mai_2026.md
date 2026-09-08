# Reconciliação do Total Produzido — Planilha RQ 005 × Indicador Corporativo

**Filial:** 01 (Matriz)  
**Período analisado:** janeiro a maio de 2026  
**Documento:** argumentação para alinhamento entre Qualidade, Produção e Indicadores  
**Data de elaboração:** junho de 2026  

---

## 1. Resumo executivo

Foi realizada uma análise comparativa entre o **Total Produzido** informado pela planilha de inspeção **RQ 005** e o total calculado automaticamente a partir dos **apontamentos reais de produção** registrados no Protheus.

**Conclusão:** a divergência observada **não se origina no indicador corporativo** (PPM / total produzido do sistema). Os números do sistema são **consistentes, repetíveis e alinhados à regra de negócio acordada** — apontamentos no **centro de trabalho de inspeção final** (CT dinâmico por filial via `SHB010`), incluindo **PA e PI**, pela **data do apontamento**.

O principal motivo da diferença está na **forma como a planilha RQ 005 consolida o total**: ela soma lotes registrados manualmente, **inclui produtos intermediários (PI)**, **pode contar duas vezes o mesmo retrabalho** e **não utiliza a mesma regra de produto** que o cadastro oficial de produção.

Em **abril/2026**, inspetor, planilha e indicador automático **convergem** (diferença ≤ 2%). Nos demais meses, o inspetor repete o total da **planilha linha 4** (jan–mar muito acima do Protheus); em **maio** o inspetor (**136.243**) diverge tanto da planilha (**108.991**) quanto do indicador CT (**111.833**) — provável uso de **outra base** (ex.: regra anterior por roteiro) na divulgação daquele mês.

---

## 2. Contexto

A área de Qualidade acompanha o **Total Produzido** na planilha RQ 005 (*Inspeção da Qualidade*). Esse valor entra na dinâmica mensal e, historicamente, foi comparado ao **PPM** (partes por milhão), cujo denominador é justamente a quantidade produzida.

Surgiu a percepção de que o sistema “estaria errado” porque os totais mensais da planilha — especialmente de janeiro a abril — apareciam **muito acima** do indicador automático. Em maio, os valores **coincidiram**, o que levou a investigação detalhada.

O objetivo deste documento é **explicar de forma clara por que a planilha diverge** do indicador corporativo e **por que o PPM deve usar apontamentos no CT de inspeção final (Protheus)**, reservando a RQ 005 para **controle de inspeção por lote**.

---

## 3. Regra oficial do denominador PPM (vigente desde jun/2026)

Em alinhamento com Produção, Qualidade e o playbook de inspeção/expedição, o denominador do PPM representa:

| Critério | Definição |
|----------|-----------|
| **O quê** | **Produto acabado (PA) e produto intermediário (PI)** apontados no CT de inspeção final |
| **Onde** | Apontamento cujo recurso pertence a CT com nome **INSPEÇÃO FINAL** / **INSPECAO FINAL** na `SHB010` (ex.: filial 01 → CT-70; filial 02 → CT-99) — **sem fixar código de CT** |
| **Como localizar o CT** | `UPPER(HB_NOME) LIKE '%INSPE%FINAL%'` + recurso do apontamento na `SH1010` (`H1_CTRAB`) |
| **Quando** | Pela **data do apontamento** de produção (`H6_DTAPONT`) |
| **Quantidade** | Soma de `H6_QTDPROD` (quantidade boa) por OP/produto/operação no CT de inspeção |
| **Unidade** | Conversão de **milheiro para unidades** (× 1000) |

Fórmula operacional:

```text
Total produzido = SUM(H6_QTDPROD) dos apontamentos no CT de inspeção final (PA + PI)
```

Essa regra está documentada, implementada no indicador automático e alinhada ao playbook de produção.

---

## 4. Como a planilha RQ 005 calcula o Total Produzido

Na planilha, o **Total Produzido** corresponde à **soma da “Quantidade do Lote”** (linha 4) de todas as colunas de lotes em cada aba mensal. Esse total alimenta a aba *Dinâmica*.

Características operacionais da planilha:

- O registro é **manual**, lote a lote, conforme a inspeção avança.
- A linha 4 **não distingue formalmente PA de PI** — na prática, **produtos intermediários entram no total** quando inspecionados.
- Quando um lote é **rejeitado na primeira inspeção** e passa por **segunda inspeção após retrabalho**, a planilha prevê **dois registros** (primeira e segunda inspeção), e **ambos entram na soma** da linha 4.
- O código do produto informado pode ser o **PI** ou uma **variante** diferente do PA pai cadastrado no Protheus.
- Não há deduplicação automática por ordem de produção: **cada coluna/lote soma**, independentemente de ser retrabalho da mesma OP.

Ou seja: a planilha mede **volume inspecionado/registrado na rotina de qualidade**, não necessariamente **PA produzido uma única vez por ordem**, na última operação do roteiro.

---

## 5. Comparativo validado dos números (filial 01)

**Fontes cruzadas em 09/06/2026** — planilha RQ 005 (linha 4), valores informados pelo inspetor e rota PPM (regra CT inspeção). Script: `api-delpi/scripts/validate_ppm_produced_quantity_rule.py`.

**CTs (SHB010):** filial 01 → **CT-70**; filial 02 → **CT-99**.

### 5.1 Totais mensais (unidades)

| Mês | Inspetor | Planilha (linha 4) | PPM CT (PA+PI) | Insp. vs PPM | Plan. vs PPM |
|-----|---------:|-------------------:|---------------:|-------------:|-------------:|
| Jan/2026 | 297.532 | 299.577 | **108.223** | +175% | +177% |
| Fev/2026 | 465.410 | 465.410 | **156.445** | +197% | +197% |
| Mar/2026 | 367.052 | 367.052 | **116.582** | +215% | +215% |
| Abr/2026 | 135.718 | 135.718 | **138.765** | −2% | −2% |
| Mai/2026 | 136.243 | 108.991 | **111.833** | +22% | −3% |
| **Acum.** | **1.401.955** | **1.376.748** | **631.848** | **+122%** | **+118%** |

### 5.2 Detalhe PA × PI no PPM (CT inspeção)

| Mês | Total | PA | PI |
|-----|------:|---:|---:|
| Jan | 108.223 | 108.223 | 0 |
| Fev | 156.445 | 155.678 | 767 |
| Mar | 116.582 | 116.572 | 10 |
| Abr | 138.765 | 138.765 | 0 |
| Mai | 111.833 | 111.433 | 400 |

PIs **50232465**, **50233615**, **50233616** somam **~711 mil un.** na planilha (jan–mar) e **~1,2 mil un.** no CT-70.

### 5.3 Leituras

- **Jan–mar:** inspetor ≈ planilha; ambos **~2× a 3×** acima do PPM (PIs na planilha + código errado **550232465** em **Jan!LX3**).
- **Abr:** três fontes alinhadas (Δ ≤ 2%).
- **Mai:** planilha ≈ PPM (−3%); inspetor **136.243** (+22% vs PPM) — origem a esclarecer.

### 5.4 Regra anterior (referência)

Roteiro final, só PA (substituída): **739.023** acum. vs **631.848** (CT atual, −17%).

### 5.5 Maio

| Fonte | Un. |
|-------|----:|
| Inspetor | 136.243 |
| Planilha | 108.991 |
| **PPM CT** | **111.833** |

### 5.6 Tabela detalhada — planilha sem CT-70 × apontamentos Totvs

Cruzamento **lote a lote** (75 colunas) dos **14 códigos** presentes na planilha com **zero apontamento no CT-70** no período, vinculando cada OP à planilha (data linha 8) e aos apontamentos reais no Protheus (outros CTs).

| Artefato | Descrição |
|----------|-----------|
| [`tabela_planilha_sem_ct70_apontamentos_totvs.md`](./tabela_planilha_sem_ct70_apontamentos_totvs.md) | Resumo + amostra (80 linhas) + agregado por produto/CT |
| [`tabela_planilha_sem_ct70_apontamentos_totvs.csv`](./tabela_planilha_sem_ct70_apontamentos_totvs.csv) | **813 linhas** completas (1 linha por apontamento Totvs × lote planilha) |

Colunas: mês, coluna planilha, código produto, OP, qtd planilha, **data planilha**, **CT Totvs**, **data apontamento Totvs**, qtd apontada.

Script: `api-delpi/scripts/export_planilha_sem_ct70_table.py`.

**Leitura rápida:** os PIs **50232465**, **50233615** e **50233616** aparecem apontados em **CT-23** (corte), **CT-08** (montagem), **CT-61/62/63** etc., mas **nunca no CT-70**; a data da planilha (inspeção) costuma ser **1–3 dias depois** do último apontamento de montagem/corte no Totvs.

---

## 6. Por que a planilha diverge — cinco argumentos

### Argumento 1 — A planilha inclui PI que não entram no CT de inspeção da mesma forma

De janeiro a março, **52% a 68%** da linha 4 da planilha são **PIs** (códigos **50232465**, **50233615**, **50233616** — cabos/fios). Na planilha somam **~711 mil un.** no período; no PPM (CT-70) aparecem **~1,2 mil un.** de PI — ou seja, esses intermediários são **registrados na planilha**, mas **não apontados no CT de inspeção final** no Protheus com o mesmo volume.

O PPM **inclui PA e PI** quando apontados no CT; a divergência vem do **registro manual na planilha**, não da exclusão de PI no sistema.

**Impacto:** explica a maior parte do gap jan–mar (planilha/inspetor **~2× a 3×** acima do PPM).

---

### Argumento 2 — Retrabalho pode ser contado duas vezes na planilha

A rotina operacional da RQ 005 permite **dois registros** para o mesmo lote rejeitado: primeira inspeção e reinspeção após retrabalho. A linha 4 **soma os dois**.

No sistema corporativo, a quantidade produzida considera **somente apontamentos no CT de inspeção final** (via cadastro de CTs na `SHB010`), somando `H6_QTDPROD` por ordem de produção — **incluindo PA e PI** conforme a nova regra de negócio.

**Impacto estimado no período:** cerca de **213 ordens** com mais de um apontamento na operação final. A planilha, ao somar lotes de 1ª e 2ª inspeção, reproduz inflação que o sistema evita.

---

### Argumento 3 — Cadastro manual de produto e ordem não replica o Protheus

Na conciliação produto a produto (jan–mai, só PA):

- **84%** dos produtos apresentam diferença **≤ 5%** entre planilha (PA) e indicador automático.
- Os desvios maiores concentram-se em famílias em que a planilha usa o **código do PA pai** (ex.: 90300069) e o Protheus aponta **variantes/códigos filhos** (ex.: 903503xx / 903504xx) — **~128 mil unidades** no acumulado só nessa diferença de codificação.

A planilha reflete **como o inspetor preencheu**; o sistema reflete **como a produção apontou** no cadastro oficial. Ambos podem estar “certos” para seus fins, mas **não são a mesma métrica**.

---

### Argumento 4 — A planilha é controle de inspeção; o sistema é registro de produção

| | Planilha RQ 005 | Indicador corporativo (PPM) |
|---|-----------------|------------------------------|
| **Finalidade** | Controle de lotes inspecionados | Total apontado no CT de inspeção final |
| **Origem** | Digitação manual por lote | Apontamentos oficiais SH6010 + SHB010/SH1010 |
| **Granularidade** | Coluna por lote / inspeção | Soma por OP/produto/operação no CT |
| **PI** | Entra na linha 4 (volume alto jan–mar) | Entra **se** apontado no CT (volume baixo vs planilha) |
| **Retrabalho** | Pode somar 1ª + 2ª inspeção | Soma apontamentos no CT (sem planilha manual) |
| **Auditoria** | Coluna a coluna na planilha | Rastreável por OP, produto, CT, data |

Usar a planilha como **única fonte do denominador de PPM** mistura **volume inspecionado** com **volume produzido (PA)** — conceitos diferentes.

---

### Argumento 5 — Unidade de medida não explica a divergência

Houve hipótese de erro de conversão (milheiro × 1.000). A verificação no cadastro e nos apontamentos mostrou que **todos os PA relevantes estão em milheiro** e a conversão está correta.

As diferenças vêm de **escopo** (PI, retrabalho, codificação) e **método de soma**, não de erro de unidade.

---

## 7. O que confirma que o indicador corporativo está correto

1. **Repetibilidade:** mesma consulta, mesmo resultado — validado em 09/06/2026 via script de validação.  
2. **Alinhamento com playbook:** CT de inspeção final via `SHB010`, recurso em `SH1010`, apontamento em `SH6010`.  
3. **Convergência em abril:** inspetor, planilha e PPM dentro de **2%** — mês de referência.  
4. **Maio:** planilha e PPM CT **próximos** (−3%); inspetor **fora** — problema de **fonte divulgada**, não de cálculo automático.  
5. **CTs explícitos:** filial 01 = CT-70; filial 02 = CT-99 (consulta dinâmica, sem hardcode único).  
6. **PIs identificados na planilha** (50232xxx / 50233xxx) com rastreio de células — ex.: erro **550232465** em **Jan!LX3** (36 mil un.).

---

## 8. O que a planilha continua fazendo bem

Este documento **não** propõe abandonar a RQ 005. A planilha permanece essencial para:

- registro de **lotes inspecionados** e **quantidade inspecionada** (linha 5 — amostra);  
- rastreio de **rejeições, retrabalhos e segunda inspeção**;  
- evidência operacional para auditorias e análises de causa;  
- controle diário/semanal da rotina do inspetor.

O ajuste necessário é de **governança do indicador**: o **Total Produzido do PPM** deve vir do **sistema**, não da soma da linha 4 da planilha.

---

## 9. Recomendações

### 9.1 Imediatas

1. **Oficializar** o indicador automático (regra da seção 3 — CT inspeção, PA + PI) como **fonte única do Total Produzido** para PPM.  
2. **Renomear ou segregar** na planilha/dinâmica o rótulo “Total Produzido”:  
   - *Total inspecionado / registrado (planilha, PA + PI + retrabalho)* — operacional Qualidade;  
   - *Total apontado CT inspeção (sistema)* — denominador PPM.  
3. **Esclarecer com o inspetor** a origem do **136.243 em maio** (≠ planilha 108.991 ≠ PPM 111.833).

### 9.2 Operacionais

4. **Padronizar o código do produto** na planilha conforme o apontamento de produção (ou documentar de-para PA pai × variantes).  
5. **Marcar visualmente** colunas de retrabalho (2ª inspeção) para não entrarem em totais comparados ao PPM.  
6. **Corrigir** código **550232465** (Jan!LX3) — provável **50232465**.  
7. **Separar na planilha** totais PA vs PI para não comparar linha 4 “cheia” com PPM CT.

### 9.3 Indicadores complementares (opcional)

8. Manter histórico da regra **roteiro final / só PA** (~739 mil acum. jan–mai) apenas para análise de transição — **não** usar como denominador PPM.

---

## 10. Conclusão

A investigação de janeiro a maio de 2026 na filial 01 leva a uma conclusão objetiva:

> **O problema não está no cálculo corporativo do total produzido. O problema está no uso da planilha RQ 005 como se ela medisse a mesma coisa.**

A planilha soma **lotes manuais**, inclui **PIs que não refletem no CT-70**, **pode duplicar retrabalho** e contém **códigos incorretos** (ex.: 550232465). O indicador automático aplica a **regra vigente**: **SUM(H6_QTDPROD)** no **CT de inspeção final** (PA + PI), filial 01 → **CT-70**.

**Abril** valida o alinhamento (Δ ≤ 2%). **Maio** mostra planilha ≈ PPM; valor do inspetor **136.243** permanece **sem fonte única** identificada na reconciliação.

**Proposta:** adotar **631.848 un.** (acum. jan–mai, PPM CT) para indicadores; RQ 005 para controle de inspeção; corrigir planilha e alinhar comunicação mensal à rota PPM.

---

## 11. Referências internas

- Planilha: *RQ 005 Inspeção da Qualidade Rev08 Matriz - 2026*  
- Playbook — Situação de Produção de PA  
- Playbook — PA, Inspeção Final e Expedição  
- Documentação das rotas de Qualidade (denominador PPM)  
- Implementação: `app/domain/services/ppm_inspection_denominator.py` e `ppm_production_sql.py` (CT inspeção final, PA + PI)

---

*Documento atualizado em 09/06/2026 — reconciliação jan–mai/2026, filial 01; denominador PPM: CT inspeção final (SHB010), PA + PI; totais PPM validados via `validate_ppm_produced_quantity_rule.py`.*
