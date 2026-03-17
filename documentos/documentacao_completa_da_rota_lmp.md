# Documentação oficial da rota LMP

## Objetivo

Documentar a implementação atual da rota de **LMPs (Lançamento ou Modificação do Produto)** no ecossistema DELPI/TOTVS, contemplando:

- entendimento funcional da LMP;
- tabelas e estruturas envolvidas;
- regras de negócio consolidadas;
- arquitetura atual no backend e frontend;
- lógica de cálculo de status para dashboard;
- critérios de identificação de atraso/pontualidade;
- queries de auditoria para validação;
- pontos de atenção para evolução.

---

## Conceito de LMP

**LMP = Lançamento ou Modificação do Produto**.

A rota de LMP não representa qualquer oportunidade de venda. Ela representa OVs que passaram por estágios específicos do fluxo comercial/técnico que caracterizam um processo de lançamento, homologação, modificação ou acompanhamento do produto.

Durante a evolução da análise, ficou claro que:

- a engenharia participa de vários pontos do fluxo;
- porém, nem toda passagem na engenharia define uma LMP;
- a identificação correta depende da combinação **processo + estágio**;
- o dashboard não deve mais depender de regras de negócio no frontend;
- a regra final deve estar centralizada no backend.

---

## Tabelas envolvidas

## 1. AD1010 — Cabeçalho da OV

Função:

- representa o cabeçalho da oportunidade;
- guarda descrição da OV;
- cliente, vendedor, revisão atual;
- processo e estágio atual da oportunidade.

Campos relevantes:

- `AD1_FILIAL`
- `AD1_NROPOR`
- `AD1_REVISA`
- `AD1_DESCRI`
- `AD1_CODCLI`
- `AD1_LOJCLI`
- `AD1_VEND`
- `AD1_PROVEN`
- `AD1_STAGE`
- `D_E_L_E_T_`

Regra:

- considerar apenas registros ativos:
  - `D_E_L_E_T_ = ''`

---

## 2. AIJ010 — Histórico/Evolução da OV

Função:

- histórico completo da movimentação da oportunidade;
- base principal para entender entrada, saída, reentrada e tempo efetivo em engenharia;
- origem dos dados de `start_date`, `end_date`, `engineering_status` e `engineering_total_minutes`.

Campos relevantes:

- `AIJ_FILIAL`
- `AIJ_NROPOR`
- `AIJ_REVISA`
- `AIJ_PROVEN`
- `AIJ_STAGE`
- `AIJ_DTINIC`
- `AIJ_HRINIC`
- `AIJ_DTENCE`
- `AIJ_HRENCE`
- `AIJ_HISTOR`
- `AIJ_STATUS`
- `D_E_L_E_T_`
- `R_E_C_N_O_`

Leitura correta:

- o histórico sempre precisa ser analisado por:
  - filial;
  - número da OV;
  - revisão;
  - processo;
  - estágio.

Ordenação recomendada:

- data de início;
- hora de início;
- stage;
- `R_E_C_N_O_`.

---

## 3. AC2010 — Dicionário de etapas do processo

Função:

- traduz `processo + estágio` para significado funcional;
- foi a base para abandonar a hipótese de que stage tem significado global.

Conclusão importante:

**o mesmo `AIJ_STAGE` não significa a mesma coisa em todos os processos**.

Exemplos relevantes:

### Processo `000002`

- `000003` = engenharia
- `000008` = amostra engenharia
- `000012` = lançamento / homologação
- `000013` = etapa posterior / follow-up do lançamento

### Processo `000003`

- `000003` = engenharia
- `000012` = etapa relevante para LMP
- `000013` = etapa posterior / follow-up da LMP

Essa constatação motivou a parametrização por processo + estágio no repository.

---

## 4. ADJ010 — Produtos vinculados à OV

Função:

- relacionar produtos à oportunidade;
- servir de base para cálculo de PI por produto e por OV.

Campos relevantes:

- `ADJ_FILIAL`
- `ADJ_NROPOR`
- `ADJ_REVISA`
- `ADJ_PROD`
- `D_E_L_E_T_`

---

## 5. SB1010 — Cadastro de produtos

Função:

- descrição do produto;
- tipo do produto;
- referência;
- grupo;
- identificação de PA e PI.

Campos relevantes:

- `B1_COD`
- `B1_DESC`
- `B1_GRUPO`
- `B1_TIPO`
- `B1_REFEREN`
- `D_E_L_E_T_`

---

## 6. SG1010 — Estrutura / BOM

Função:

- navegar na estrutura do produto;
- contar componentes tipo PI;
- consolidar `qtd_pi` por produto e por OV.

Campos relevantes:

- `G1_COD`
- `G1_COMP`
- `G1_FIM`
- `D_E_L_E_T_`

---

## 7. SA1010 / SA3010

Função:

- `SA1010`: dados do cliente;
- `SA3010`: dados do vendedor.

---

## Evolução das regras de negócio

## 1. A rota inicial misturava revisões

Problema encontrado:

- análises por número da OV apenas misturavam eventos de revisões diferentes;
- isso causava status errado, tempos errados e duplicidade implícita.

Conclusão:

- toda leitura da AIJ precisa considerar:
  - `FILIAL`
  - `NROPOR`
  - `REVISA`
  - `PROVEN`

---

## 2. Engenharia não pode ser inferida por um único stage global

Problema encontrado:

- assumir que engenharia era sempre um mesmo stage gerou leituras incorretas;
- a tabela AC2010 mostrou que o significado muda conforme o processo.

Conclusão:

- engenharia deve ser parametrizada por **processo + estágio**.

---

## 3. LMP e engenharia são conceitos relacionados, mas não idênticos

Foi necessário separar:

### a) estágios âncora de LMP

São os estágios que definem que a OV é uma LMP.

### b) estágios de apoio da engenharia

São os estágios usados para:

- contabilizar tempo efetivo em engenharia;
- contar passagens;
- identificar entradas/saídas;
- definir status atual;
- alimentar o dashboard.

### c) estágios de follow-up da LMP

Foram adicionados para corrigir casos em que a etapa âncora ficava sem encerramento explícito, mas a OV seguia seu fluxo na revisão seguinte ou em estágio posterior.

---

## 4. Status atual deve refletir a última revisão

Problema encontrado:

- revisões antigas abertas faziam a OV parecer em andamento, mesmo havendo revisão posterior finalizada.

Conclusão:

- o **status atual** da engenharia deve sempre ser derivado da **última revisão** relevante;
- métricas históricas podem continuar consolidadas, mas o status operacional precisa refletir o estado mais recente.

---

## 5. O frontend não deve decidir regra de negócio

Antes:

- o frontend calculava nível, SLA, status, prazo e evolução;
- havia adapter com regra de negócio local.

Agora:

- essas regras foram movidas para o backend;
- o frontend apenas consome o payload já enriquecido;
- isso evita divergência entre listagem, detalhe e dashboard.

---

## Configuração consolidada do repository

Arquivo: `app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_settings.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01"])

    lmp_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
            "000003": ["000012"],
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

    engineering_status_labels: Dict[str, str] = field(
        default_factory=lambda: {
            "in_progress": "EM_ANDAMENTO",
            "finished": "FINALIZADA",
            "partial": "PARCIAL",
        }
    )

    root_product_types: List[str] = field(default_factory=lambda: ["PA"])
    pi_product_types: List[str] = field(default_factory=lambda: ["PI"])
    active_delete_flag: str = ""
    max_bom_level: int = 999
```

---

## Interpretação da configuração

### `lmp_anchor_process_stages`

Define o ponto principal que caracteriza a LMP.

### `lmp_followup_process_stages`

Define etapas posteriores que ajudam a encerrar logicamente a LMP quando a etapa âncora não recebeu data final explícita.

Essa configuração foi importante para corrigir casos de histórico em que:

- `000012` ficava sem `AIJ_DTENCE`;
- a OV seguia adiante para `000013`;
- o repository precisava inferir o encerramento real.

### `engineering_support_process_stages`

Define todos os estágios que contam como tempo efetivo de engenharia.

---

## Estrutura atual da implementação

## Backend

### `lmp_query_repository.py`

Responsável por:

- montar filtros SQL;
- compor os CTEs;
- listar LMPs;
- buscar uma LMP específica;
- consolidar histórico de engenharia;
- calcular `engineering_total_minutes`;
- montar produtos e quantidade de PI;
- devolver dados crus já corretos para os use cases.

### `lmp_business_rules.py`

Responsável por regras de negócio do dashboard:

- definição do nível (`Nível 1`, `Nível 2`, `Nível 3`);
- SLA em dias úteis;
- SLA em minutos;
- data limite;
- lead time útil;
- status final (`Pontual`, `Atrasado`, `Andamento`).

### `list_lmp_dashboard_use_case.py`

Responsável por:

- buscar LMPs no repository;
- enriquecer itens com as regras de negócio;
- aplicar filtro por status;
- calcular resumo do dashboard;
- devolver paginação e payload pronto para o frontend.

### `get_lmp_use_case.py`

Responsável por:

- buscar uma OV específica;
- aplicar regras de dashboard no detalhe;
- devolver campos enriquecidos no endpoint individual.

### `lmp_dashboard_item.py`

DTO específico do dashboard, com os campos já enriquecidos.

### `lmp_routes.py`

Endpoints relevantes:

- `GET /lmps/`
- `GET /lmps/{sale_number}`
- `GET /lmps/dashboard`

### `lmp_composer.py`

Composição dos use cases com o repository.

---

## Frontend

### Mudança importante

O adapter local do dashboard foi removido.

Antes:

- o plugin calculava localmente status, SLA, nível e gráficos.

Agora:

- o plugin consome a rota `/lmps/dashboard` já enriquecida;
- o hook `useLmpsDashboard` trabalha com a estrutura devolvida pelo backend;
- o `lmpApi.ts` passou a refletir o novo contrato.

Benefício:

- backend e frontend passam a falar a mesma linguagem de negócio;
- elimina divergência entre tela, regra e detalhe da OV.

---

## Regra atual do dashboard

Arquivo: `app/application/services/lmp_business_rules.py`

## 1. Nível por quantidade de PI

```python
if qtd_pi <= 10:
    nivel = "Nível 1"
elif qtd_pi <= 20:
    nivel = "Nível 2"
else:
    nivel = "Nível 3"
```

## 2. SLA por nível

- Nível 1 = 4 dias úteis
- Nível 2 = 8 dias úteis
- Nível 3 = 20 dias úteis

## 3. SLA em minutos

O dashboard passou a usar também SLA em minutos, com base em dia cheio:

- 1 dia = 24 horas
- 1 dia = 1440 minutos

Logo:

- Nível 1 = 4 × 1440 = 5760 min
- Nível 2 = 8 × 1440 = 11520 min
- Nível 3 = 20 × 1440 = 28800 min

## 4. Margem de tolerância

Foi adicionada margem de **1 dia** para reduzir falsos atrasos em casos limítrofes.

Essa margem influencia:

- comparação por minutos;
- comparação por data;
- especialmente cenários como o da OV `003263`.

## 5. Critério de status

### Item finalizado

Para OVs com `engineering_status = FINALIZADA`, o comportamento desejado é:

- considerar pontual se estiver dentro da janela aceitável;
- considerar atrasado quando extrapolar o SLA efetivo.

### Item em andamento

Para OVs não finalizadas:

- `Andamento` enquanto ainda dentro da janela aceitável;
- `Atrasado` quando o tempo efetivo extrapolar o limite.

---

## Regra consolidada sobre tempo efetivo

A principal conclusão mais recente foi:

> **não basta subtrair `end_date - start_date` para medir atraso.**

Isso gerava erros quando:

- a OV saía da engenharia e voltava depois;
- havia revisão nova com reentrada na etapa;
- uma etapa âncora ficava aberta sem fechamento explícito;
- o fluxo avançava para estágio seguinte e o cálculo acabava contando tempo corrido em vez de tempo efetivo de posse da engenharia.

Logo, o status de atraso do dashboard deve considerar o **tempo efetivo em engenharia** (`engineering_total_minutes`), e não apenas a diferença entre datas de início e fim.

---

## Regra de ouro atual

### `lead_time_util`

Usado para leitura operacional e exibição.

Representa:

- quantidade de dias úteis entre `start_date` e `end_date`.

### `engineering_total_minutes`

Usado para avaliar atraso/pontualidade.

Representa:

- tempo efetivo que a OV ficou em etapas tratadas como engenharia.

### Conclusão

- **Lead Time Útil** é indicador de leitura;
- **engineering_total_minutes** é critério principal de SLA efetivo.

---

## Ajuste importante no repository

Foi necessário melhorar o cálculo de `start_date` e `end_date` em cenários de revisão.

Problema encontrado:

- algumas revisões deixavam a etapa `000012` sem `AIJ_DTENCE`;
- depois a OV reaparecia em nova revisão ou em estágio de follow-up;
- o repository acabava tratando a passagem como aberta indefinidamente.

Correção conceitual:

- usar follow-up para inferir encerramento lógico;
- considerar próxima revisão / próxima movimentação relevante;
- separar claramente:
  - âncora da LMP;
  - follow-up da LMP;
  - apoio da engenharia.

Isso reduziu fortemente falsos atrasos e corrigiu casos como:

- `003181`
- `003211`
- parte dos itens que antes apareciam em atraso por cadastro incompleto.

---

## Casos reais de análise

## Caso `003211`

Situação observada:

- `engineering_status = FINALIZADA`
- `end_date` da LMP vinha vazia
- havia linha no histórico sem `AIJ_DTENCE`
- porém a OV já não estava mais na engenharia

Conclusão:

- o repository estava coerente com o histórico bruto;
- o cadastro possuía etapa sem encerramento explícito;
- o service precisou respeitar o fato de que a OV já estava finalizada na engenharia e não poderia ser classificada como item aberto.

---

## Caso `003181`

Situação observada:

- várias revisões ao longo do tempo;
- reentrada em engenharia;
- `000012` em revisões diferentes, algumas sem fechamento;
- diferença entre histórico consolidado e última revisão.

Conclusão:

- usar apenas subtração de datas levava a erro;
- foi necessário separar:
  - histórico completo;
  - última revisão;
  - follow-up;
  - tempo efetivo sob posse da engenharia.

---

## Caso `003263`

Situação observada:

- no frontend visualmente deveria ser pontual;
- no backend ainda aparecia como atrasado.

Conclusão:

- o caso é limítrofe;
- justificou a criação da tolerância de 1 dia;
- serviu para refinar a regra e evitar atraso indevido em cenário muito próximo do SLA.

---

## Query de auditoria do histórico

Abaixo está o modelo de query usado para validar eventos, revisão e consolidação.

## 1. Detalhe dos eventos que contam como engenharia

Usada para inspecionar:

- início real do evento;
- fim real usado;
- regra de encerramento aplicada;
- minutos do evento;
- próxima movimentação.

Estrutura lógica:

- filtrar por processo + estágio de engenharia;
- calcular próxima movimentação com `LEAD(...)`;
- montar `DT_INICIO_REAL`;
- montar `DT_FIM_REAL_USADO`;
- registrar a regra de fechamento usada;
- calcular `TEMPO_MINUTOS_EVENTO`.

## 2. Total por revisão

Usado para verificar:

- quantos eventos relevantes houve na revisão;
- quanto tempo total aquela revisão consumiu.

## 3. Total da última revisão

Usado para comparar:

- esforço real da revisão corrente;
- divergência com histórico consolidado.

## 4. Total histórico

Usado para validar:

- soma total de esforço em engenharia ao longo da vida da OV.

---

## Campos atualmente expostos no dashboard

Cada item do dashboard retorna:

- `sale_number`
- `sale_description`
- `start_date`
- `end_date`
- `engineering_status`
- `qtd_pi`
- `nivel`
- `dias_uteis_sla`
- `sla_minutos`
- `engineering_total_minutes`
- `data_limite`
- `lead_time_util`
- `status`

Resumo agregado:

- `total_lmps`
- `percent_dentro_prazo`
- `avg_lead_time`

---

## Endpoint oficial de dashboard

## `GET /lmps/dashboard`

Parâmetros:

- `date_start`
- `date_end`
- `status`
- `page`
- `page_size`

Comportamento:

- busca LMPs no repository;
- aplica regras de negócio no use case;
- devolve itens enriquecidos;
- permite filtrar por status.

---

## Pontos de atenção atuais

## 1. Há diferença entre data limite e SLA efetivo em minutos

A data limite continua sendo útil para leitura humana.

Mas o atraso real do dashboard agora depende principalmente de:

- `engineering_total_minutes`
- SLA em minutos
- tolerância configurada

Isso significa que alguns casos podem parecer “dentro da data” visualmente e ainda precisarem auditoria pelo histórico real.

---

## 2. Casos limítrofes ainda exigem validação manual

Os itens remanescentes classificados como atrasados precisam ser auditados caso a caso.

Na fase atual, isso é esperado.

A regra já foi muito refinada, mas alguns cenários ainda dependem de confirmar:

- se o histórico representa esforço real;
- se existe erro de cadastro;
- se houve etapa sem encerramento explícito;
- se uma nova revisão deveria encerrar logicamente a anterior.

---

## 3. Histórico bruto pode conter inconsistência operacional

Alguns atrasos aparentes não são erro da regra.

Podem ser:

- erro de cadastro;
- revisão aberta sem baixa;
- etapa concluída operacionalmente sem data final gravada;
- retorno tardio com reaproveitamento do fluxo anterior.

Por isso, o repository foi evoluído para ser o mais aderente possível ao histórico, mas ainda assim a análise de alguns casos precisa de auditoria funcional.

---

## Melhorias futuras recomendadas

- criar rota de auditoria por OV com detalhamento dos eventos considerados no cálculo;
- expor no backend a regra de encerramento aplicada por evento;
- separar explicitamente no payload:
  - tempo histórico total;
  - tempo da última revisão;
  - tempo efetivo usado para SLA;
- criar flag de “cadastro inconsistente” quando houver etapa âncora sem encerramento explícito e sem follow-up claro;
- permitir filtros por cliente, vendedor e faixa de PI;
- paginação SQL nativa no dashboard;
- incluir endpoint de indicadores agregados por período.

---

## Resumo executivo

A rota LMP evoluiu de uma leitura simplificada para um modelo aderente ao comportamento real do Protheus.

As decisões mais importantes foram:

- LMP deve ser identificada por **processo + estágio**;
- engenharia também deve ser mapeada por **processo + estágio**;
- o frontend não deve mais calcular regra de negócio;
- o dashboard deve consumir dados enriquecidos do backend;
- o status atual deve refletir a **última revisão**;
- o atraso deve considerar **tempo efetivo em engenharia**;
- follow-up da LMP passou a ser necessário para corrigir encerramentos implícitos;
- margem de tolerância foi adicionada para reduzir falsos atrasos em casos limítrofes.

Com isso, a rota passou a ser uma base mais confiável para:

- análise operacional;
- dashboard executivo;
- auditoria de SLA;
- investigação de inconsistências no histórico.

