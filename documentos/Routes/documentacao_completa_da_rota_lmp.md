# Documentação oficial da rota LMP

## Objetivo

Documentar a implementação **atualizada** da rota de **LMPs (Lançamento ou Modificação do Produto)** no ecossistema DELPI/TOTVS, contemplando:

- entendimento funcional da LMP;
- tabelas e estruturas envolvidas;
- regras de negócio consolidadas;
- arquitetura atual no backend e frontend;
- lógica de cálculo de status para dashboard;
- critérios de identificação de atraso, pontualidade, andamento e retorno;
- filtro por filial;
- contrato atual do payload;
- paginação SQL na rota base;
- pontos de atenção para evolução.

---

## Conceito de LMP

**LMP = Lançamento ou Modificação do Produto**.

A rota de LMP não representa qualquer oportunidade de venda. Ela representa OVs que passaram por estágios específicos do fluxo comercial/técnico que caracterizam um processo de lançamento, homologação, modificação ou acompanhamento do produto.

Durante a evolução da análise, ficou claro que:

- a engenharia participa de vários pontos do fluxo;
- porém, nem toda passagem na engenharia define uma LMP;
- a identificação correta depende da combinação **processo + estágio**;
- o dashboard não deve depender de regra de negócio no frontend;
- a regra final deve estar centralizada no backend;
- o filtro por filial também deve ser centralizado no backend.

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
- `000012` = etapa relevante em históricos antigos / alternativos
- `000013` = etapa posterior / follow-up

Ajuste consolidado:

- na operação atual, a engenharia do processo `000003` usa o estágio `000003` como estágio de entrada real;
- por isso, a configuração passou a aceitar `000003` como estágio âncora de LMP para esse processo, mantendo `000012` por compatibilidade histórica quando necessário.

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

## 5. Tempo efetivo nem sempre está na mesma revisão do status

Problema encontrado:

- alguns casos tinham a última revisão correta para status, mas não para medir o tempo real de engenharia;
- isso gerava `engineering_total_minutes = 0` mesmo em OVs corretamente classificadas como finalizadas.

Conclusão:

- a implementação atual usa uma abordagem **híbrida**:
  - **última revisão** para o status atual;
  - **revisão de medição** para calcular tempo, avanço, retorno e encerramento implícito.

Regra prática:

- a revisão de medição prioriza a revisão mais nova que contenha a etapa âncora relevante da engenharia/LMP;
- se não existir, usa a maior revisão disponível no conjunto de eventos de engenharia.

---

## 6. O frontend não deve decidir regra de negócio

Antes:

- o frontend calculava nível, SLA, status, prazo e evolução;
- havia adapter com regra de negócio local.

Agora:

- essas regras foram movidas para o backend;
- o frontend apenas consome o payload já enriquecido;
- isso evita divergência entre listagem, detalhe e dashboard.

---

## 7. O filtro de filial deve ser resolvido no backend

Antes:

- a request podia até carregar `branch`, mas o repository ainda dependia apenas de `settings.branches`;
- isso fazia o filtro ser inconsistente ou inexistente em partes da query.

Agora:

- o repository resolve a filial efetiva a partir de duas possibilidades:
  - se `request.branch` vier preenchida, filtra apenas a filial informada;
  - se `request.branch` vier `None`, usa todas as filiais configuradas em `LMPQuerySettings.branches`.

Consequência:

- a regra fica centralizada no repository;
- CTEs, histórico, produtos e consolidações passam a usar a mesma resolução de filial;
- o frontend apenas informa a filial desejada, sem decidir o fallback.

---

## Configuração consolidada do repository

Arquivo: `app/infrastructure/persistence/totvs/lmp_repositories/lmp_query_settings.py`

```python
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class LMPQuerySettings:
    branches: List[str] = field(default_factory=lambda: ["01", "02"])

    lmp_anchor_process_stages: Dict[str, List[str]] = field(
        default_factory=lambda: {
            "000002": ["000012"],
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

## Interpretação da configuração

### `branches`

Define as filiais padrão da rota quando a request não informa uma filial específica.

### `lmp_anchor_process_stages`

Define o ponto principal que caracteriza a LMP.

### `lmp_followup_process_stages`

Define etapas posteriores que ajudam a encerrar logicamente a LMP quando a etapa âncora não recebeu data final explícita.

### `engineering_support_process_stages`

Define todos os estágios que contam como tempo efetivo de engenharia.

### `engineering_status_labels`

Define os estados operacionais consolidados aceitos pela aplicação:

- `ABERTA`
- `FINALIZADA`
- `PARCIAL`
- `RETORNADA`

---

## Estrutura atual da implementação

## Backend

### `lmp_query_repository.py`

Responsável por:

- montar filtros SQL;
- compor os CTEs;
- listar LMPs;
- listar LMPs paginadas via SQL;
- buscar uma LMP específica;
- consolidar histórico de engenharia;
- calcular `engineering_total_minutes`;
- montar produtos e quantidade de PI;
- devolver dados crus já corretos para os use cases.

### Estratégia atual do repository

A implementação atual é **híbrida**:

- `LMPEventos` define quais OVs entram na rota;
- `StatusUltimaRevisaoEngenharia` define o estado atual usando a **última revisão**;
- `UltimaRevisaoMedicaoEngenharia` escolhe a melhor revisão para medir tempo e encerramento implícito;
- `EngenhariaResumoUltimaRevisao` consolida:
  - `start_date`
  - `end_date`
  - `engineering_total_minutes`
  - `qtd_advanced_from_engineering`
  - `qtd_returned_from_engineering`
  - `engineering_status`
- a rota base agora usa `COUNT + OFFSET/FETCH` quando `page_size` é informado.

Essa separação foi necessária para corrigir ao mesmo tempo:

- status errados em revisões antigas;
- tempos zerados em revisões novas com reencaminhamento;
- retornos indevidamente tratados como andamento;
- dashboards que listavam ou excluíam OVs erradas por depender de âncora incorreta;
- desperdício de memória e tráfego causado por paginação em memória na listagem simples.

### `lmp_business_rules.py`

Responsável por regras de negócio do dashboard:

- definição do nível (`Nível 1`, `Nível 2`, `Nível 3`);
- SLA em dias úteis;
- SLA em minutos;
- data limite;
- lead time útil;
- status final (`Pontual`, `Atrasado`, `Andamento`, `Retornada`).

### `list_lmp_dashboard_use_case.py`

Responsável por:

- buscar LMPs no repository;
- enriquecer itens com as regras de negócio;
- aplicar filtro por status;
- calcular resumo do dashboard;
- devolver paginação e payload pronto para o frontend.

Atenção importante:

- como o dashboard serializa um DTO próprio (`LMPDashboardItem`), qualquer campo novo que venha do repository precisa ser explicitamente copiado para esse DTO;
- isso vale especialmente para `branch`.

### `get_lmp_use_case.py`

Responsável por:

- buscar uma OV específica;
- devolver a entidade serializada;
- enriquecer `list_history[]` via `enrich_history_events()` (rótulos, status legível, flags de situação);
- calcular campos de dashboard (`nivel`, `status`, `lead_time_util`, etc.) via `LMPBusinessRules`;
- preservar os demais campos vindos da entidade `LMP`, incluindo `branch` e `list_products`.

### `lmp_history_event_enrichment.py`

Serviço de domínio que enriquece cada evento de `list_history` **sem alterar o SQL** do AIJ010.

Entrada: lista de dicts vindos do repository (`LMPHistoryEvent.to_dict()`).

Saída: mesmos eventos + campos derivados:

| Campo | Descrição |
|-------|-----------|
| `process_label` | Rótulo do processo (`000001` → Abertura, `000002` → Oportunidade, …) |
| `stage_label` | Rótulo do estágio conforme `lmp_process_stage_labels.py` |
| `status_label` | Tradução de `AIJ_STATUS` (`1` → Em andamento, `2` → Encerrado, …) |
| `is_open` | `true` quando `end_date` está vazio |
| `is_late` | `true` quando limite ultrapassado (aberto ou encerrado após limite) |
| `is_current` | `true` no último evento em aberto, ou no último da sequência |
| `is_engineering` | Flag SQL (par processo+estágio em `engineering_support_process_stages`) |
| `is_engineering_flow` | `true` se `is_engineering` **ou** estágio ∈ `{000003, 000008, 000012}` |
| `duration_display` | Texto legível (`Em andamento · N dia(s)`, `2 h`, …) |

Regras importantes:

- **`is_engineering`** continua alinhada às métricas de engenharia no repository.
- **`is_engineering_flow`** é a regra de **exibição** no MFE (badge Engenharia), cobrindo casos em que o processo TOTVS ≠ `000002`/`000003` mas o estágio é técnico.
- Duração em aberto usa minutos corridos até `GETDATE()` quando não há encerramento nem próximo evento (mesma regra do SQL).

Mapa de status (`AIJ_STATUS`):

| Código | Rótulo |
|--------|--------|
| `1` | Em andamento |
| `2` | Encerrado |
| `3` | Cancelado |
| `4` | Suspenso |
| outro | `Status {código}` |

### `lmp_process_stage_labels.py`

Rótulos consolidados para processo/estágio (complementar ao AC2010):

| Código | Processo / estágio |
|--------|-------------------|
| `000001` | Abertura |
| `000002` | Oportunidade |
| `000003` | Engenharia |
| `000008` | Amostra engenharia |
| `000012` | Lançamento / homologação |
| `000013` | Acompanhamento |

### `list_lmp_use_case.py`

Responsável por:

- delegar a listagem paginada de LMPs ao repository;
- preservar o contrato de retorno em `Page[LMP]`;
- manter o caso de uso sem paginação em memória.

Regra consolidada:

- quando `page_size` não for informado, o repository retorna a coleção completa;
- quando `page_size` for informado, a paginação é executada diretamente no SQL Server com `COUNT + OFFSET/FETCH`.

Consequência arquitetural:

- a aplicação deixa de carregar todas as LMPs apenas para recortar a página em Python;
- reduz custo de memória, tráfego e tempo de resposta na rota base.

### `lmp_dashboard_item.py`

DTO específico do dashboard, com os campos já enriquecidos.

Na versão consolidada, ele deve expor também:

- `branch`
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

### `lmp.py`

Entidade de domínio da LMP.

Campos atuais relevantes:

- `branch`
- `sale_number`
- `sale_description`
- `start_date`
- `end_date`
- `engineering_status`
- `qtd_engineering_entries`
- `qtd_engineering_closed`
- `qtd_advanced_from_engineering`
- `qtd_returned_from_engineering`
- `engineering_total_minutes`
- `qtd_pi`
- cliente
- vendedor
- lista de produtos
- **`list_history`** — eventos completos do AIJ010 para a OV (detalhe)

### `lmp_history_event.py`

Entidade de um evento do histórico (`AIJ010`):

| Campo | Origem TOTVS |
|-------|----------------|
| `revision` | `AIJ_REVISA` |
| `process_code` | `AIJ_PROVEN` |
| `stage_code` | `AIJ_STAGE` |
| `start_date`, `start_time` | `AIJ_DTINIC`, `AIJ_HRINIC` |
| `limit_date`, `limit_time` | `AIJ_DTLIMI`, `AIJ_HRLIMI` |
| `end_date`, `end_time` | `AIJ_DTENCE`, `AIJ_HRENCE` |
| `duration_minutes` | calculado no SQL (`DATEDIFF` até encerramento, próximo evento ou agora) |
| `status` | `AIJ_STATUS` |
| `history_flag` | `AIJ_HISTOR` |
| `is_engineering` | `CASE` com `engineering_support_process_stages` |

Campos enriquecidos (`process_label`, `status_label`, `is_open`, …) são adicionados no **`GetLMPUseCase`**, não persistidos na entidade.

Consulta SQL: `LMPQueryRepository._sql_history_events_lmp()` — ordenação por revisão, data/hora de início, estágio e `R_E_C_N_O_`.

### `engineering_router.py`

Endpoints relevantes:

- `GET /engineering/lmps`
- `GET /engineering/lmps/{sale_number}`
- `GET /engineering/lmps/dashboard`

### `engineering_composer.py`

Composição centralizada dos use cases da área de Engenharia, incluindo:

- listagem simples de LMPs;
- dashboard de LMPs;
- detalhe de LMP;
- summary enxuto de LMP para Strategic Indicators;
- fluxos do Transforma Mais.

---

## Frontend

### Mudança importante

O adapter local do dashboard foi removido.

Antes:

- o plugin calculava localmente status, SLA, nível e gráficos.

Agora:

- o plugin consome a rota `/engineering/lmps/dashboard` já enriquecida;
- o hook `useLmpsDashboard` trabalha com a estrutura devolvida pelo backend;
- o `lmpApi.ts` reflete o contrato consolidado.

### Filtro por filial no frontend

A barra de filtros passou a considerar a filial como filtro funcional da tela.

Comportamento esperado:

- no lugar do antigo campo estático de critério, a tela deve exibir um seletor de filial;
- ao selecionar uma filial, o frontend envia `branch` para o backend;
- ao não selecionar nenhuma filial, o frontend envia ausência de `branch`, deixando o backend cair no default de `settings.branches`.

### Coluna de filial na tabela

A tabela do dashboard passou a precisar do campo `branch` no payload.

Consequência arquitetural:

- não basta o repository filtrar por filial;
- o repository também precisa projetar `branch` no `SELECT` final;
- a entidade `LMP` precisa carregar `branch`;
- o `LMPDashboardItem` precisa expor `branch`;
- o `ListLMPDashboardUseCase` precisa copiar `item.branch` para o DTO final.

Sem isso, a coluna de filial no frontend permanece vazia mesmo com o filtro funcionando no backend.

### Detalhe da OV (`LmpDetailPage`)

Rota MFE: `/apps/dashboard-lmps/ov/{sale_number}`.

Consome **`GET /engineering/lmps/{sale_number}`** com os mesmos filtros de período/filial do dashboard.

Seções da tela:

| Seção | Fonte |
|-------|--------|
| KPIs (status, lead time, tempo engenharia) | campos enriquecidos do detalhe |
| Proposta / Engenharia / Cliente | campos cadastrais + resumo engenharia |
| Produtos | `list_products[]` |
| Estrutura (BOM) | `GET /products/{code}/structure` por produto |
| **Histórico da OV** | `list_history[]` |

### Histórico da OV no frontend

Componentes (`plugins/dashboard-lmps`):

- `LmpHistorySection` — toolbar, filtros, toggle **Linha do tempo | Tabela**
- `LmpHistoryTimeline` — stepper vertical agrupado por revisão
- `historyFormatting.ts` — formatação e filtros client-side

Filtros disponíveis (somente UI; não alteram a API):

| Filtro | Critério |
|--------|----------|
| Todos | sem restrição |
| Engenharia | `is_engineering_flow === true` |
| Em aberto | `is_open === true` |
| Revisão atual | mesma revisão do evento `is_current` |

Visualização padrão: **linha do tempo**. A tabela mantém todas as colunas com tooltips (ⓘ).

Cada evento na timeline inclui **mini-Gantt** proporcional à revisão (barra início→fim/agora; traço = limite).

Preferências de visualização e filtro persistem em `localStorage` (`dashboard-lmps:history-view`, `dashboard-lmps:history-filter`).

Textos de ajuda: `src/content/helpTooltips.ts`.

**Fora de escopo atual:** Gantt consolidado multi-revisão em uma única escala global.

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

O dashboard usa SLA em minutos, com base em dia cheio:

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
- especialmente cenários limítrofes de revisão e reentrada.

## 5. Critério de status

### Item finalizado

Para OVs com `engineering_status = FINALIZADA`:

- considerar pontual se estiver dentro da janela aceitável;
- considerar atrasado quando extrapolar o SLA efetivo.

### Item retornado

Para OVs com `engineering_status = RETORNADA`:

- o dashboard devolve status **`Retornada`**;
- esse status não é tratado como `Pontual` nem como `Atrasado`;
- ele representa exceção operacional, não conclusão normal do SLA.

### Item em andamento / parcial / aberta

Para OVs não finalizadas:

- `Andamento` enquanto ainda dentro da janela aceitável;
- `Atrasado` quando o tempo efetivo extrapolar o limite.

---

## Regra consolidada sobre tempo efetivo

A principal conclusão foi:

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

## Ajustes importantes consolidados

### 1. Encerramento lógico da LMP

Foi necessário melhorar o cálculo de `start_date` e `end_date` em cenários de revisão.

Problema encontrado:

- algumas revisões deixavam a etapa âncora sem `AIJ_DTENCE`;
- depois a OV reaparecia em nova revisão ou em estágio posterior;
- o repository acabava tratando a passagem como aberta indefinidamente.

Correção conceitual:

- usar próxima movimentação relevante para inferir encerramento lógico;
- considerar próxima revisão / próxima movimentação relevante;
- separar claramente:
  - âncora da LMP;
  - follow-up da LMP;
  - apoio da engenharia.

### 2. Status atual pela última revisão

Essa regra foi preservada para evitar regressões em massa no dashboard.

### 3. Revisão de medição para tempo

Foi adicionada para corrigir casos em que a última revisão era boa para status, mas ruim para medir o tempo real.

### 4. Filtro de retornadas na camada de negócio

A camada `lmp_business_rules.py` passou a reconhecer explicitamente:

- `RETORNADA`

Isso permite:

- classificar o item como `Retornada` no dashboard;
- filtrar retornadas na camada de use case/regra de negócio;
- manter o repository focado em estado técnico e o service focado em interpretação de negócio.

### 5. Projeção e serialização de filial

A evolução recente mostrou que **filtrar filial** e **retornar filial** são preocupações diferentes.

Para a filial aparecer no payload final do dashboard, o fluxo completo precisa estar alinhado:

1. o repository precisa projetar `AD1_FILIAL AS branch` no `SELECT` final;
2. a entidade `LMP` precisa ter o campo `branch`;
3. o `LMPDashboardItem` precisa declarar `branch`;
4. o `ListLMPDashboardUseCase` precisa copiar `item.branch` ao montar o DTO;
5. a serialização final precisa usar esse DTO já enriquecido.

Sem essa cadeia completa, a API pode filtrar corretamente, mas ainda assim devolver `branch` ausente no JSON do dashboard.

### 6. Paginação SQL na rota base

A listagem simples deixou de paginar em memória.

Agora:

- o repository executa uma query de contagem;
- executa uma query paginada com `OFFSET/FETCH`;
- devolve `Page[LMP]` já consistente com o contrato da rota.

Com isso:

- a camada de aplicação deixa de carregar todas as LMPs para recortar a página;
- a rota base passa a escalar melhor em períodos maiores;
- o dashboard continua podendo operar com a coleção completa quando necessário.

---

## Casos reais de análise

## Caso `003528`

Situação observada:

- a OV passou pela engenharia;
- depois foi devolvida a estágios anteriores;
- a API retornava como se ainda estivesse em andamento na engenharia.

Conclusão:

- faltava reconhecer o cenário de retorno;
- a rota passou a devolver `engineering_status = RETORNADA`.

---

## Caso `003362`

Situação observada:

- a OV foi alterada e passada adiante;
- o status final estava correto, mas `engineering_total_minutes` ficava zerado.

Conclusão:

- a última revisão era correta para status;
- mas a revisão usada para medição precisava priorizar a revisão âncora da passagem efetiva;
- isso motivou a criação da **revisão de medição**.

---

## Caso `003529`

Situação observada:

- a OV existia na engenharia, mas não aparecia no dashboard.

Conclusão:

- a regra de âncora para o processo `000003` estava desalinhada com a operação real;
- a engenharia usa o estágio `000003`;
- a configuração de `lmp_anchor_process_stages` foi ampliada para incluir `000003` nesse processo.

---

## Campos atualmente expostos

## Listagem base (`GET /engineering/lmps`)

Cada item da listagem deve retornar ao menos:

- `branch`
- `sale_number`
- `sale_description`
- `start_date`
- `end_date`
- `engineering_status`
- `qtd_engineering_entries`
- `qtd_engineering_closed`
- `qtd_advanced_from_engineering`
- `qtd_returned_from_engineering`
- `engineering_total_minutes`
- `qtd_pi`

Payload de paginação:

- `items`
- `page`
- `page_size`
- `total`
- `total_pages`

## Detalhe (`GET /engineering/lmps/{sale_number}`)

Além dos campos base, deve retornar:

- cliente
- vendedor
- produtos relacionados
- `branch`

## Dashboard (`GET /engineering/lmps/dashboard`)

Cada item do dashboard deve retornar:

- `branch`
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

## Endpoints oficiais

## `GET /engineering/lmps`

Objetivo:

- listar LMPs em formato paginado.

Parâmetros atuais:

- `date_start`
- `date_end`
- `branch`
- `page`
- `page_size`

Comportamento consolidado:

- quando `branch` vier preenchido, o backend restringe a leitura à filial informada;
- quando `branch` vier ausente, o backend usa o fallback configurado em `LMPQuerySettings.branches`;
- quando `page_size` vier preenchido, a paginação é executada nativamente no SQL Server;
- quando `page_size` vier ausente, a rota devolve o conjunto completo respeitando os filtros informados.

Contrato de retorno:

- `items`
- `page`
- `page_size`
- `total`
- `total_pages`

## `GET /engineering/lmps/{sale_number}`

Objetivo:

- obter o detalhe completo de uma OV/LMP.

## `GET /engineering/lmps/dashboard`

Objetivo:

- listar LMPs já enriquecidas para consumo do dashboard.

Parâmetros:

- `date_start`
- `date_end`
- `status`
- `branch`
- `page`
- `page_size`

Comportamento:

- busca LMPs no repository;
- aplica regras de negócio no use case;
- devolve itens enriquecidos;
- permite filtrar por status;
- permite tratar `RETORNADA` como categoria própria;
- permite filtrar por filial;
- quando `branch` vier ausente, usa as filiais padrão do settings.

---

## Exemplo de comportamento do filtro de filial

### Request sem filial

```http
GET /engineering/lmps/dashboard?date_start=2026-03-02&date_end=2026-03-23&status=Todos
```

Comportamento esperado:

- usar todas as filiais configuradas em `LMPQuerySettings.branches`.

### Request com filial específica

```http
GET /engineering/lmps/dashboard?date_start=2026-03-02&date_end=2026-03-23&status=Todos&branch=01
```

Comportamento esperado:

- restringir o resultado à filial `01`.

---

## Exemplo de payload esperado do dashboard

```json
{
  "success": true,
  "message": "Dashboard de LMPs carregado com sucesso.",
  "data": {
    "items": [
      {
        "branch": "01",
        "sale_number": "003482",
        "sale_description": "BRASELIO REAJUSTE 2026",
        "start_date": "20260323",
        "end_date": "20260323",
        "engineering_status": "FINALIZADA",
        "qtd_pi": 274,
        "nivel": "Nível 3",
        "dias_uteis_sla": 20,
        "sla_minutos": 28800,
        "engineering_total_minutes": 0,
        "data_limite": "20260420",
        "lead_time_util": 1,
        "status": "Pontual"
      }
    ],
    "total": 1,
    "page": 1,
    "page_size": 1,
    "summary": {
      "total_lmps": 1,
      "percent_dentro_prazo": 100.0,
      "avg_lead_time": 1.0
    }
  }
}
```

---

## Pontos de atenção atuais

## 1. Há diferença entre data limite e SLA efetivo em minutos

A data limite continua sendo útil para leitura humana.

Mas o atraso real do dashboard depende principalmente de:

- `engineering_total_minutes`
- SLA em minutos
- tolerância configurada

## 2. Casos limítrofes ainda exigem validação manual

Os itens remanescentes classificados como atrasados precisam ser auditados caso a caso.

## 3. Histórico bruto pode conter inconsistência operacional

Alguns atrasos aparentes não são erro da regra.

Podem ser:

- erro de cadastro;
- revisão aberta sem baixa;
- etapa concluída operacionalmente sem data final gravada;
- retorno tardio com reaproveitamento do fluxo anterior.

## 4. O dashboard exige alinhamento entre repository, entity, DTO e use case

A presença de um campo no SQL não garante sua presença no payload final.

Exemplo crítico:

- `branch` pode existir no `SELECT` do repository;
- mas, se o DTO do dashboard não tiver `branch`, o JSON final continuará sem o campo.

## 5. O maior custo restante continua em `qtd_pi`

Mesmo com as otimizações recentes:

- separação da query mínima do summary;
- remoção de join redundante em `AD1010` quando existe escopo;
- paginação SQL na rota base;

O maior gargalo remanescente continua sendo o cálculo online de `qtd_pi`, por depender de:

- `ProdutosLMPRef`
- `ProdutosBase`
- `Recursive_BOM`
- `PI_COUNT_BY_OV`

Ou seja:

- a rota base melhorou na paginação;
- mas o cálculo de PI ainda é o principal custo estrutural da query.

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
- paginação SQL nativa também no dashboard;
- incluir endpoint de indicadores agregados por período;
- revisar caminhos de query de `qtd_pi` para reduzir ainda mais o custo da recursão BOM;
- consolidar telemetria de performance da rota base e do dashboard.

---

## Resumo executivo

A rota LMP evoluiu de uma leitura simplificada para um modelo aderente ao comportamento real do Protheus.

As decisões mais importantes foram:

- LMP deve ser identificada por **processo + estágio**;
- engenharia também deve ser mapeada por **processo + estágio**;
- o frontend não deve mais calcular regra de negócio;
- o dashboard deve consumir dados enriquecidos do backend;
- o status atual deve refletir a **última revisão**;
- o tempo de SLA deve considerar **tempo efetivo em engenharia**;
- a medição pode usar revisão diferente da revisão de status quando necessário;
- `RETORNADA` passou a ser um estado oficial do fluxo;
- o processo `000003` passou a aceitar `000003` como âncora operacional de engenharia/LMP;
- o filtro por filial passou a ter fallback oficial em `settings.branches`;
- a rota base `GET /engineering/lmps` agora aceita `branch` e paginação SQL nativa;
- a serialização de `branch` no dashboard depende do alinhamento completo entre repository, entity, DTO e use case;
- margem de tolerância foi adicionada para reduzir falsos atrasos em casos limítrofes.

Com isso, a rota passou a ser uma base mais confiável para:

- análise operacional;
- dashboard executivo;
- auditoria de SLA;
- investigação de inconsistências no histórico;
- leitura por filial com comportamento previsível.

