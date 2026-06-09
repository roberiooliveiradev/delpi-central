# Reconciliação do Total Produzido — Planilha RQ 005 × Indicador Corporativo

**Filial:** 01 (Matriz)  
**Período analisado:** janeiro a maio de 2026  
**Documento:** argumentação para alinhamento entre Qualidade, Produção e Indicadores  
**Data de elaboração:** junho de 2026  

---

## 1. Resumo executivo

Foi realizada uma análise comparativa entre o **Total Produzido** informado pela planilha de inspeção **RQ 005** e o total calculado automaticamente a partir dos **apontamentos reais de produção** registrados no Protheus.

**Conclusão:** a divergência observada **não se origina no indicador corporativo** (PPM / total produzido do sistema). Os números do sistema são **consistentes, repetíveis e alinhados à regra de negócio acordada** — produção de **produto acabado (PA)**, na **última operação do roteiro**, pela **data do apontamento**, sem depender de um centro de trabalho fixo por filial.

O principal motivo da diferença está na **forma como a planilha RQ 005 consolida o total**: ela soma lotes registrados manualmente, **inclui produtos intermediários (PI)**, **pode contar duas vezes o mesmo retrabalho** e **não utiliza a mesma regra de produto** que o cadastro oficial de produção.

Em maio de 2026, o valor divulgado pelo inspetor (**136.243 unidades**) coincide **exatamente** com o indicador automático — e **não** com o total que a planilha calcula hoje (**108.991 unidades**). Isso reforça que, quando se usa a mesma base, os números convergem.

---

## 2. Contexto

A área de Qualidade acompanha o **Total Produzido** na planilha RQ 005 (*Inspeção da Qualidade*). Esse valor entra na dinâmica mensal e, historicamente, foi comparado ao **PPM** (partes por milhão), cujo denominador é justamente a quantidade produzida.

Surgiu a percepção de que o sistema “estaria errado” porque os totais mensais da planilha — especialmente de janeiro a abril — apareciam **muito acima** do indicador automático. Em maio, os valores **coincidiram**, o que levou a investigação detalhada.

O objetivo deste documento é **explicar de forma clara por que a planilha diverge** e **por que o indicador corporativo deve ser tratado como referência oficial** para o total produzido de PA, reservando a planilha para seu papel de **controle de inspeção por lote**, e não como fonte única do denominador de PPM.

---

## 3. Regra acordada para “Total Produzido” no PPM

Em alinhamento com Produção e Qualidade, ficou definido que o denominador do PPM deve representar:

| Critério | Definição |
|----------|-----------|
| **O quê** | Somente **produto acabado (PA)** |
| **Onde na produção** | Apontamento na **última operação do roteiro** do produto — ou seja, quando a peça conclui o fluxo produtivo cadastrado, **sem amarrar a um centro de inspeção fixo** (como CT-70 na filial 01), pois isso varia entre filiais e nem todo PA passa pelo mesmo centro na prática |
| **Quando** | Pela **data do apontamento** de produção |
| **Unidade** | Conversão de **milheiro para unidades** quando o cadastro do produto está em milheiro |
| **Quantidade por OP** | **Programado − saldo = apontado**: usa a quantidade planejada da OP menos o que ainda falta; o apontado considerado é o **maior registro** na operação final (evita duplicar retrabalho); se o apontamento superar o programado, **limita ao programado** |

Fórmula operacional:

```text
saldo_pendente = max(0, programado − apontado)
produzido_na_OP = programado − saldo_pendente  (= apontado, limitado ao programado)
```

Essa regra está documentada, implementada no indicador automático e **foi testada mês a mês** no período analisado.

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

## 5. Comparativo dos números (filial 01)

### 5.1 Totais mensais (unidades)

| Mês | Planilha (informado pelo inspetor) | Indicador automático (regra acordada) | Diferença |
|-----|-----------------------------------:|--------------------------------------:|----------:|
| Janeiro/2026 | 297.532 | 138.556 | Planilha **+115%** |
| Fevereiro/2026 | 465.410 | 181.383 | Planilha **+157%** |
| Março/2026 | 367.052 | 123.818 | Planilha **+196%** |
| Abril/2026 | 135.718 | 159.023 | Planilha **−15%** |
| Maio/2026 | 136.243 | 136.243 | **Igual** |
| **Acumulado jan–mai** | **1.401.955** | **739.023** | Planilha **+90%** |

### 5.2 Outras referências no acumulado (jan–mai)

| Fonte | Total acumulado | Observação |
|-------|----------------:|------------|
| Planilha, **somente PA** (excluindo PI manualmente) | ~627.549 | Ainda **abaixo** do inspetor e **acima** do CT inspeção em alguns meses |
| Indicador automático (última operação do roteiro, só PA) | **739.023** | Referência oficial testada |
| Apontamentos só no centro de **inspeção final** (CT dinâmico por filial) | ~630.671 | Mede “liberado na inspeção”, **não** “produzido no roteiro” — fica ~15% abaixo |

### 5.3 Maio — evidência decisiva

| Fonte | Maio/2026 |
|-------|----------:|
| Valor informado pelo inspetor | 136.243 |
| Indicador automático | 136.243 |
| Planilha RQ 005 (arquivo atual) | 108.991 |

Em maio, quem divulgou o número **utilizou o indicador automático**, não o total que a planilha calcula sozinha hoje. Isso demonstra que **não há erro sistemático no cálculo corporativo** — quando a mesma base é usada, o resultado é idêntico.

---

## 6. Por que a planilha diverge — cinco argumentos

### Argumento 1 — A planilha inclui PI; o PPM considera só PA

De janeiro a março, uma fatia relevante da linha 4 da planilha corresponde a **produtos intermediários (PI)** — na ordem de **52% a 68%** do total daqueles meses. PI é peça em fabricação, **não produto acabado**.

O indicador de PPM, por definição de negócio, **exclui PI**. Somar PI na planilha **infla artificialmente** o “total produzido” em relação ao denominador correto do indicador.

**Impacto:** explica boa parte do gap de janeiro a março (planilha muito acima do sistema).

---

### Argumento 2 — Retrabalho pode ser contado duas vezes na planilha

A rotina operacional da RQ 005 permite **dois registros** para o mesmo lote rejeitado: primeira inspeção e reinspeção após retrabalho. A linha 4 **soma os dois**.

No sistema corporativo, apontamentos repetidos na mesma ordem e mesma operação final entram com o **maior apontamento** por ordem. A quantidade produzida segue **programado − saldo = apontado**: o que foi efetivamente reconhecido na OP, **sem ultrapassar o programado** e **sem somar repasses** como se fossem produção nova.

**Impacto estimado no período:** cerca de **213 ordens** com mais de um apontamento na operação final. A planilha, ao somar lotes de 1ª e 2ª inspeção, reproduz inflação que o sistema evita.

---

### Argumento 3 — Cadastro manual de produto e ordem não replica o Protheus

Na conciliação produto a produto (jan–mai, só PA):

- **84%** dos produtos apresentam diferença **≤ 5%** entre planilha (PA) e indicador automático.
- Os desvios maiores concentram-se em famílias em que a planilha usa o **código do PA pai** (ex.: 90300069) e o Protheus aponta **variantes/códigos filhos** (ex.: 903503xx / 903504xx) — **~128 mil unidades** no acumulado só nessa diferença de codificação.

A planilha reflete **como o inspetor preencheu**; o sistema reflete **como a produção apontou** no cadastro oficial. Ambos podem estar “certos” para seus fins, mas **não são a mesma métrica**.

---

### Argumento 4 — A planilha é controle de inspeção; o sistema é registro de produção

| | Planilha RQ 005 | Indicador corporativo |
|---|-----------------|----------------------|
| **Finalidade** | Controle de lotes inspecionados | Total de PA produzido para indicadores |
| **Origem** | Digitação manual por lote | Apontamentos oficiais de produção |
| **Granularidade** | Coluna por lote / inspeção | Ordem de produção × operação final |
| **PI** | Entra na linha 4 | Excluído |
| **Retrabalho** | Pode somar 1ª + 2ª inspeção | Uma quantidade por ordem na operação final |
| **Auditoria** | Difícil rastrear sem revisar coluna a coluna | Rastreável por ordem, produto, data e operação |

Usar a planilha como **única fonte do denominador de PPM** mistura **volume inspecionado** com **volume produzido (PA)** — conceitos diferentes.

---

### Argumento 5 — Unidade de medida não explica a divergência

Houve hipótese de erro de conversão (milheiro × 1.000). A verificação no cadastro e nos apontamentos mostrou que **todos os PA relevantes estão em milheiro** e a conversão está correta.

As diferenças vêm de **escopo** (PI, retrabalho, codificação) e **método de soma**, não de erro de unidade.

---

## 7. O que confirma que o indicador corporativo está correto

1. **Repetibilidade:** a mesma regra aplicada mês a mês produz resultados estáveis e auditáveis no Protheus.  
2. **Alinhamento com a decisão de negócio:** só PA, última operação do roteiro, data do apontamento — sem CT fixo por filial.  
3. **Convergência em maio:** inspetor e sistema **136.243** — prova de que, usando a mesma base, não há divergência.  
4. **Conciliação por produto:** em **84%** dos códigos PA, planilha e sistema ficam dentro de **5%** de diferença.  
5. **Coerência com inspeção final:** total por centro de inspeção final (~631 mil) fica **abaixo** do total por roteiro (~739 mil), como esperado — nem todo PA apontado na operação final passa imediatamente pelo CT de inspeção, e vice-versa.  
6. **Playbook de produção:** a documentação interna alerta que somar todos os apontamentos sem regra gera **percentuais acima de 100%** da ordem — exatamente o risco que a planilha corre ao somar lotes e retrabalhos sem deduplicação.

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

1. **Oficializar** o indicador automático (regra da seção 3) como **fonte única do Total Produzido (PA)** para PPM e relatórios gerenciais.  
2. **Renomear ou segregar** na planilha/dinâmica o que hoje aparece como “Total Produzido”, deixando claro se é:  
   - *Total inspecionado (PA + PI + retrabalho)* — uso operacional de Qualidade; ou  
   - *Total produzido PA (sistema)* — referência para PPM.  
3. **Comunicar à equipe de inspeção** que divergências jan–abr não indicam falha do sistema, e sim ** diferença de método e escopo**.

### 9.2 Operacionais

4. **Padronizar o código do produto** na planilha conforme o apontamento de produção (ou documentar de-para PA pai × variantes).  
5. **Marcar visualmente** colunas de retrabalho (2ª inspeção) para não entrarem em totais comparados ao PPM.  
6. **Separar PI do total** usado em indicadores — PI pode continuar na planilha para controle, mas **fora** do denominador de PPM.

### 9.3 Indicadores complementares (opcional)

7. Manter, se desejado, um indicador à parte: **“PA liberado na inspeção final”** (centro de inspeção por filial) — **não substitui** o total produzido por roteiro, mas complementa a visão de expedição.

---

## 10. Conclusão

A investigação de janeiro a maio de 2026 na filial 01 leva a uma conclusão objetiva:

> **O problema não está no cálculo corporativo do total produzido. O problema está no uso da planilha RQ 005 como se ela medisse a mesma coisa.**

A planilha soma **lotes manuais**, inclui **PI**, **pode duplicar retrabalho** e usa **codificação nem sempre igual** ao Protheus. O indicador automático aplica a **regra de negócio acordada** sobre apontamentos oficiais de **PA na última operação do roteiro**.

A coincidência exata em **maio (136.243 unidades)** entre o valor informado e o sistema demonstra que, quando alinhados à mesma base, **os números fecham**.

**Proposta de encaminhamento:** adotar o total do sistema para PPM; manter a RQ 005 para controle de inspeção; ajustar labels e rotina da planilha para deixar explícito o que é “inspecionado” versus “produzido (PA)”.

---

## 11. Referências internas

- Planilha: *RQ 005 Inspeção da Qualidade Rev08 Matriz - 2026*  
- Playbook — Situação de Produção de PA  
- Playbook — PA, Inspeção Final e Expedição  
- Documentação das rotas de Qualidade (denominador PPM)  
- Implementação: `app/domain/services/ppm_produced_quantity.py` (regra **programado − saldo = apontado**)

---

*Documento elaborado com base na reconciliação quantitativa jan–mai/2026, filial 01, cruzando planilha RQ 005, apontamentos Protheus e indicador PPM. Atualizado em jun/2026 com a formalização da regra de quantidade produzida por OP.*
