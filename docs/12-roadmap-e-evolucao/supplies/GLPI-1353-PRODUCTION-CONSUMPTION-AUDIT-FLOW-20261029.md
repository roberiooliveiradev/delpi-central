# GLPI #1353 — Fluxo de consumo por operação e auditoria de estoque

> **Data da investigação:** 2026-10-29  
> **Escopo:** descoberta técnica e funcional, somente leitura; sem implementação, migração, alteração no Protheus ou autorização de nova página.  
> **Fonte operacional:** leituras autorizadas com DAVI/`api-delpi` em SQL Server Protheus; **fonte de código:** diagnóstico D0 reportado sobre (`d955f51cfda36e9d5f5af5d04194e1441ae34d36`), revalidar no HEAD antes da execução.  
> **Estado:** `D0=ACCEPT_WITH_RESIDUAL`; `D1=INCONCLUSIVE` para prova da causalidade automática e homologação geral; `IMPLEMENTATION=NOT_AUTHORIZED`.  
> **Solicitante:** Joici Motta; **responsável informado:** Michael Marotto. A origem é o chamado GLPI #1353.

## 1. Objetivo e limites

A funcionalidade futura **Auditoria Inteligente de Consumo e Estoque** deverá cruzar estruturas, OPs, operações, empenhos, movimentações e apontamentos para identificar **indícios auditáveis**, não declarar automaticamente erros de apontamento ou diferenças físicas de estoque. O fluxo descrito é uma hipótese de processo sustentada por relato operacional e por um caso real, e **não constitui contrato de cálculo homologado**.

É distinta do produtor E12 `/supplies/safety-stock/consumption-analysis/*`, que agrega consumo por **produto e período**. O GLPI #1353 precisa de **filial × OP × operação × componente**, com evidência documental, interpretação de eventos e tratamento de estruturas históricas. Uma nova posição no roadmap e alterações de manifest dependem de decisão explícita do Product Owner; E11 continua com residual de smoke federado autenticado na documentação consultada.

## 2. Fluxo operacional observado / informado

1. **OP e estrutura** — SC2 define produto, quantidades, unidade, datas e estado. SG1 define componentes e quantidade por unidade, respeitando sua vigência; a estrutura atual não substitui automaticamente a estrutura de uma OP histórica.
2. **Operações e materiais** — SH8 relaciona OP, operação e centro de trabalho. SD4 guarda empenho original, saldo, componente e possíveis vínculos com OP de origem/relacionada. Um componente ainda empenhado pode pertencer a operação ainda não executada.
3. **Execução e apontamento** — informação operacional fornecida pela área: ao executar/apontar uma operação (ex.: cortar cabo, crimpar terminal), o Protheus faz a baixa correspondente de matéria-prima **automaticamente**. Essa causalidade é `BUSINESS_RULE_CANDIDATE`: foi informada pelo usuário, mas o evento transacional que liga um apontamento concreto à baixa ainda não foi demonstrado no D1.
4. **Baixa e outras movimentações** — SD3 registra diferentes naturezas; **não somar todas** as quantidades de uma OP, nem classificar somente pela TM. Usar a classificação canônica da `api-delpi`, com CF, direção, documento, marca de estorno, unidade, material, armazém e OP. Documento pode conter movimentos de mais de uma OP.
5. **Conciliação por operação e componente** — distinguir (a) teórico baseado em quantidade de referência **homologada** × estrutura vigente, (b) consumo SD4 derivado de `D4_QTDEORI - D4_QUANT` quando semanticamente aplicável, e (c) consumo líquido SD3 elegível e reconciliado. Comparar somente unidades convertidas segundo regra canônica, com estado de execução e tolerâncias a validar.
6. **Investigação de exceções** — diferenciar diferença aritmética, movimento não classificado, possível divergência, justificativa e confirmação. Não declarar falta física sem contagem/inventário ou outra evidência suficiente. Nunca alterar automaticamente apontamento, empenho ou estoque.

`OP -> operação -> componente esperado -> empenho -> apontamento -> movimentos classificados -> conciliação -> evidência -> investigação`

**Atenção à sequência:** a posição da baixa no fluxo é a sequência operacional informada; não foi provada uma relação causal 1:1, nem o instante exato do disparo automático.

## 3. Caso real de referência: filial 01 / OP 24884201006

### 3.1 Ordem, operações e apontamento

| Fonte | Registro consultado | Estado |
|---|---|---|
| SC2010 | OP `24884201006`; produto PI `50226108`; planejado `0,125 MI`; `C2_QUJE=0`; `C2_DATRF` vazio; emissão `20261020` | PROVEN, fotografia da consulta |
| SH6010 | `H6_OP=24884201006`; `H6_PRODUTO=50226108`; `H6_QTDPROD=0,125`; `H6_TIPO=P` | PROVEN: apontamento encontrado; significado integral e reflexo na SC2 ainda pendentes |
| SH8010 | Operação `01` centro `CT-23`; operação `02` centro `CT-35` | PROVEN: operações cadastradas, não execução de cada uma |
| SC2010 | OP relacionada `24884201002`; produto `90350419`; planejado `0,125 MI`; produzido `0`; sem data final | PROVEN |
| SD4010 | Linha da OP `24884201002`, `D4_OPORIG=24884201006`, componente `50226108`, original/saldo `0,125` | PROVEN: vínculo cadastral, sem concluir direção causal |

**Nota:** `C2_QUJE=0` na SC2 e apontamento `H6_QTDPROD=0,125` na SH6 **não podem ser silenciosamente reconciliados**. Precisam de interpretação PCP/Protheus sobre status, atualização e eventual origem/estorno do apontamento.

### 3.2 Estrutura e empenhos da OP

SG1010: `G1_COD=50226108`. Componentes:

| Componente | Tipo/UM em SB1 | SG1 por unidade | Teórico preliminar para 0,125 | SD4 original | SD4 saldo | SD4 derivado consumido |
|---|---|---:|---:|---:|---:|---:|
| `10010030` — cabo | MP / MT | 646 | 80,75 MT | 80,75 | 0 | 80,75 |
| `10080329` — terminal olhal | MP / PC | 2.000 | 250 PC | 250 | 250 | 0 |

Vigência consultada de ambas as linhas SG1: `G1_INI=20261020` e `G1_FIM=20491231` — compreende a data de emissão da OP, mas não prova que não houve substituição, engenharia alternativa ou contexto especial.

A leitura tipada `list_production_order_operation_materials` confirmou:
- **Operação 01 / CT-23:** cabo `10010030`, original 80,75 MT, saldo 0, consumido derivado 80,75.
- **Operação 02 / CT-35:** terminal `10080329`, original 250 PC, saldo 250, consumido derivado 0.

A correspondência confirma vínculos de material a operação; **não demonstra por si só a execução de cada operação**.

### 3.3 SD3: três movimentações, três leituras distintas

| Documento | Produto | TM / CF | Quantidade | Armazém | Significado identificado |
|---|---|---|---:|---|---|
| `220039839` | `10010030` | 999 / RE0 | 0,64 MT | 99 | **Transferência de entrada**, conforme capability `get_product_internal_movements` |
| `220039840` | `MOD216` | 999 / RE1 | 0,233 HR | 01 | Registro de mão de obra direta; categoria do movimento requer leitura específica |
| `220039841` | `10010030` | 999 / RE2 | 80,75 MT | 99 | **Consumo de produção, saída**, conforme capability canônica |

O cadastro SB1010 retornou `MOD216` = **MÃO DE OBRA DIRETA DE CORTE E APLICAÇÃO CT-23**, tipo `MO`, unidade `HR`. Não misturar 0,233 HR com consumo físico de MP. Uma consulta SD3 pelo documento `220039841` também identificou material `10080001` em **outra OP** (`24880701002`): a chave do documento isolada não determina pertencimento à OP.

O campo `D3_ESTORNO` estava vazio nas linhas consultadas. Isso **não prova ausência de devoluções ou contrapartidas em outros documentos**.

**Conciliação aritmética do cabo no recorte:** teórico preliminar = 80,75 MT; SD4 derivado = 80,75 MT; SD3 classificada como consumo = 80,75 MT. A antiga soma 81,39 MT misturava 80,75 de consumo + 0,64 de transferência; seu `+0,79%` **não é evidência de sobreconsumo**. Resultado da verificação pontual não é certificação de saldo físico ou regra válida para todas as OPs.

**Terminal:** 250 PC permanecem empenhados; baixa consumida derivada 0. Sem prova de operação 02 executada, não classificar como falha.

## 4. Matriz de evidências e decisões

| Questão | Classificação | Evidência ou pendência |
|---|---|---|
| Operações 01/02 e respectivos componentes | PROVEN | SH8 + leitura tipada de materiais SD4 |
| Consumo 80,75 MT de cabo | PROVEN para o recorte | SD3 classificada e SD4 derivado |
| 0,64 MT é segundo consumo | **REFUTADO no recorte** | Classificação canônica: transferência inbound |
| MOD216 é matéria-prima fora da estrutura | **REFUTADO como MP** | SB1: tipo MO, unidade HR |
| SG1 vigente na emissão | PROVEN para os registros consultados | G1_INI/G1_FIM × C2_EMISSAO |
| Apontamento SH6 da OP | PROVEN | H6_TIPO=P, H6_QTDPROD=0,125 |
| Apontamento dispara baixa automática em cada operação | BUSINESS_RULE_CANDIDATE | Relato operacional; vínculo evento→baixa não comprovado |
| Operação 01 executada; operação 02 não executada | TO_INVENTORY | SH8 prova cadastro, não execução; consultar fonte de execução HZA/SH6 correlacionada |
| Por que SC2 produzida=0 apesar de SH6=0,125 | TO_INVENTORY | Validar status, atualização, temporalidade/semântica |
| Estornos, substituições, tolerâncias e unidades alternativas | TO_INVENTORY | Requer casos positivos/negativos e homologação PCP/Joici/Michael |
| Furo físico de estoque | **NÃO COMPROVADO** | Exige inventário ou evidência adequada |

## 5. Desenho arquitetural proposto, não implementado

`plugins/supplies` (UX) → `supplies-api` (Flask BFF, Core effective permissions, escopo e estado de investigação) → `api-delpi` (consultas SQL/semântica e conciliação canônica do TOTVS).

- **Core API** mantém authority de permissions; ADR-009: `supplies.access` uso normal e `supplies.manage` administração, sem permission por página ou CRUD. Filiais 01/02 são filtros de dados operacionais; novas regras de recurso exigem decisão explícita.
- **`api-delpi`** é o owner do cálculo e classificação ERP; reutilizar domínio de movimentos SD3, empenhos SD4, estrutura SG1 histórica e apontamentos. Contratos novos `/supplies/consumption-audit/*` são **PROPOSED**, não rotas existentes.
- **`supplies-api`** responde por autorização fail-closed, composição e, em evolução futura autorizada, histórico de investigação no schema próprio `supplies` sem duplicar estado TOTVS.
- **MFE** apresenta lista e evidências por OP/operação/componente com kit `@delpi/plugin-ui`, sem SQL, regra canônica nem chamada direta a `api-delpi`.

**Não implementar automaticamente** alertas de OP sem consumo, empenho residual, componente fora de estrutura ou diferença física. Classificação e tolerâncias dependem do estado real da operação, do reconhecimento de movimentos de retorno e de homologação funcional.

## 6. Próximas verificações (D1 residual → D2)

1. Localizar campos e consulta canônica de execução por **OP+operação** (HZA/SH6 ou fonte aprovada), associar timestamp/documento e evento de baixa sem assumir vínculo pelo mesmo dia.
2. Explicar discrepância `SC2.C2_QUJE=0` versus `SH6.H6_QTDPROD=0,125` com PCP.
3. Validar estorno/devolução/transferência e sua direção com exemplos distintos, inclusive documentos compartilhados por OP.
4. Revalidar estrutura histórica e segunda UM para múltiplos produtos e datas.
5. Homologar com Joici/Michael quando o saldo SD4 pode legitimamente permanecer aberto e o que merece alerta por operação.
6. Somente então congelar contratos e critérios de aceite de consumo esperado, efetivo, classificação e tolerâncias; separar D2 documental de qualquer implementação posterior.

**Gates:** `D1=INCONCLUSIVE` (automação causal e exceções ainda abertas), `D2=PLANNED`, `IMPLEMENTATION=NOT_AUTHORIZED`. Nenhuma alteração de ERP, escrita de dados, nova permission, novo endpoint, deploy ou mudança de roadmap foi autorizada.

## 7. Trilhas e proveniência

- **Origem:** GLPI #1353, demanda de Joici; briefing e D0 de arquitetura disponibilizados ao projeto.
- **D0:** diagnóstico Devin, HEAD informado `d955f51cfda36e9d5f5af5d04194e1441ae34d36`, READ-ONLY. Relatório não comprova runtime corrente e precisa rebaseline ao implementar.
- **D1 (2026-10-29):** ferramentas DAVI `discover_delpi_information` / `execute_delpi_information`: `execute_readonly_sql`, `get_product_internal_movements`, `list_production_order_operation_materials`. Consultas com OP, filial, códigos e docs citados; retornos operacionais representam **snapshot** do instante de leitura, não estado permanentemente atualizado.
- **Limite SH6:** tentativa inicial com coluna `H6_DATA` falhou (`Invalid column name`); segunda leitura com campos `H6_FILIAL,H6_OP,H6_PRODUTO,H6_QTDPROD,H6_TIPO` retornou um apontamento. Não inventar data/operador/trigger.
- **Authorities:** [README](./README.md), [IMPLEMENTATION-PLAN](./IMPLEMENTATION-PLAN.md), [MATRIZ-BOUNDARIES](./MATRIZ-BOUNDARIES.md), [ADR-009](./adr/ADR-009-product-access-and-operational-data-scope.md), regras `.cursor` e instrução oficial GPT.
