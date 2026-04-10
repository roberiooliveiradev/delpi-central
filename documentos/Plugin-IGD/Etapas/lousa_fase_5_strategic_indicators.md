# Fase 5 — Strategic Indicators: estado consolidado e detalhado

## Resumo executivo da fase

A Fase 5 consolidou a migração do módulo Strategic Indicators para um fluxo real no backend e frontend, com rotas reais para resumo executivo, departamentos, detalhe departamental, indicadores, alertas, tendências, configurações e auditoria. As telas principais do módulo já consomem APIs reais, e o contrato de metas estruturadas com `goal_label`, `goal_value` e `goal_periodicity` já estava estabilizado antes desta etapa.

Além disso, nesta continuação da fase, o módulo passou por uma refatoração estrutural de performance e arquitetura baseada em snapshot services, com centralização da orquestração, redução de recomputação entre endpoints e paralelização da coleta de medições reais. Essa refatoração atingiu Strategic Indicators, produção, comercial, engenharia e qualidade.

Agora, a fase também passou a incluir:
- a integração inicial do RH via PostgreSQL do Portal RH
- o desenho completo do departamento Financeiro com fonte híbrida (Google Sheets + TOTVS financeiro)
- a padronização universal de parsing de datas vindas de planilhas, para evitar falhas com formatos variados e datas numéricas do Excel

## O que já estava concluído antes desta etapa

### Backend real disponível

- rota `/executive-summary` real
- rota `/departments` real
- rota `/departments/{id}` real
- rota `/indicators` real
- rota `/alerts` real
- rota `/trends` real
- rota `/settings` real
- rota `/settings/audit` real

### Telas já ligadas em API real

- `ExecutiveDashboardPage`
- `DepartmentsPage`
- `DepartmentDetailsPage`
- `IndicatorsPage`
- `AlertsPage`
- `PresentationPage`
- `TrendsPage`
- `SettingsPage`

### Migração de contratos e dados

- pasta `data/mocks` removida
- componentes e páginas remanescentes migrados para tipos reais compartilhados
- contratos antigos baseados em `goal2026`, `goal_2026` e textos `Meta 2026` removidos
- rota `/indicators` já retorna apenas metas estruturadas, sem qualquer campo legado
- rota `/alerts` já devolve metas estruturadas em `indicator_alerts`
- seed consolidado em `V006`
- `V007` removida após consolidação do seed

### Metas estruturadas e cálculo

O módulo já operava com:
- `goal_label`
- `goal_value`
- `goal_periodicity`

E o calculator já havia sido ajustado para:
- usar meta numérica estruturada
- considerar o período consultado
- suportar periodicidades
- expor helpers de variação e direção entre período atual e anterior

## O que foi consolidado estruturalmente nesta fase

### Snapshot service global

Foi introduzida a camada central de snapshot do Strategic Indicators, responsável por:
- resolver período
- carregar catálogo
- carregar medições reais com cache
- calcular indicadores
- calcular departamentos
- calcular IGD
- montar comparativos atual vs anterior
- montar séries temporais

Isso retirou a orquestração transversal dos use cases e concentrou a composição do módulo em uma camada própria.

### Use cases refatorados

Os use cases de:
- executive summary
- departments
- department details
- indicators
- alerts
- trends

passaram a depender do snapshot consolidado, em vez de recomputar o pipeline inteiro localmente.

### Provider central em paralelo

O `RealStrategicIndicatorsMeasurementsProvider` passou a:
- usar cache
- coletar áreas em paralelo
- agregar resultados departamentais de forma centralizada

Antes ele conhecia apenas:
- engineering
- production
- commercial
- quality

Agora ele também foi preparado para incorporar:
- `hr`
- `financial`

no mesmo modelo de coleta.

### Produção, comercial, engenharia e qualidade

Já haviam sido organizados com snapshot services e providers mais finos:
- `ProductionMetricsSnapshotService`
- `CommercialMetricsSnapshotService`
- `EngineeringMetricsSnapshotService`
- provider de qualidade sem duplicação de Kaizen

# Integração do RH no Strategic Indicators

## Objetivo

Conectar o departamento de RH ao módulo Strategic Indicators usando o Portal RH em PostgreSQL, mantendo o mesmo padrão arquitetural dos demais departamentos.

## Premissas do RH

### Peso do RH no modelo IGD/IDD

No modelo consolidado de IGD/IDD:
- RH pesa 15% no IGD
- o IDD RH possui 5 indicadores
- cada indicador tem 20% de peso dentro do RH

### Regra de consolidação

Foi definida a seguinte regra para o RH:
- os indicadores devem ser calculados por filial
- o valor final usado no Strategic Indicators deve ser a média entre as filiais
- os `unit_values` devem ser preservados para detalhamento futuro

## Arquitetura adotada para o RH

O RH foi desenhado para entrar assim:

```text
Portal RH PostgreSQL
 -> portal_rh_postgres_connection
 -> PortalRhBaseRepository
 -> HrMetricsRepository
 -> HrMetricsSnapshotService
 -> HrIndicatorsSnapshotProvider
 -> RealStrategicIndicatorsMeasurementsProvider
 -> StrategicIndicatorsSnapshotService
 -> rotas /strategic-indicators/*
```

### Novas peças arquiteturais do RH

Foram definidos os seguintes componentes:
- `portal_rh_postgres_connection.py`
- `portal_rh_base_repository.py`
- `hr_metrics_repository.py`
- `hr_metrics_snapshot_service.py`
- `hr_indicators_snapshot_port.py`
- `hr_indicators_snapshot_provider.py`
- `hr_composer.py`

Além disso:
- `config.py` foi ampliado para incluir as envs `PORTAL_RH_*`
- `strategic_indicators_composer.py` passou a ter o RH como novo departamento conectado
- `RealStrategicIndicatorsMeasurementsProvider` passou a suportar `hr` como área coletável

## Indicadores do RH no modelo estratégico

O RH possui estes 5 indicadores no modelo IGD/IDD:

1. **Absenteísmo**  
   Meta 2026: `2,0%`  
   Natureza: **quanto menor, melhor**

2. **Turnover (Rotatividade)**  
   Meta 2026: `1,5% ao mês`  
   Natureza: **quanto menor, melhor**

3. **Satisfação Interna (Clima/Engajamento)**  
   Meta 2026: `85% de satisfação`  
   Natureza: **quanto maior, melhor**

4. **% de PDIs Ativos**  
   Meta 2026: `100%`  
   Natureza: **quanto maior, melhor**

5. **Horas de Treinamento por Colaborador/mês**  
   Meta 2026: `2 horas/mês`  
   Natureza: **quanto maior, melhor**

## Situação técnica atual dos indicadores de RH

### Indicadores já encaminhados com base real

Os 3 indicadores mais bem sustentados pelo schema do Portal RH e já encaminhados tecnicamente são:
- **Absenteísmo**
- **Turnover**
- **Horas de treinamento por colaborador/mês**

### Indicadores ainda pendentes de definição funcional/técnica

Ainda faltam fechar:
- **Satisfação Interna (Clima/Engajamento)**
- **% de PDIs Ativos**

## Problemas encontrados na integração do RH

### 1. Variáveis de ambiente não chegavam ao container
Inicialmente, o serviço `api-delpi` não estava recebendo as envs `PORTAL_RH_*` via docker-compose.

### 2. Erro de data no PostgreSQL
As datas resolvidas pelo Strategic Indicators chegam em formato `DD-MM-YYYY`, e o PostgreSQL não lidava bem com casts ambíguos.

A correção aplicada foi usar:
- `TO_DATE(..., 'DD-MM-YYYY')`
- com `CAST(... AS text)` e `NULLIF(..., '')`

### 3. Falhas genéricas no repository base
Foi identificado que a base repository do Portal RH precisava aplicar `rollback()` também em `fetch_one()` e `fetch_all()` em caso de erro, para evitar conexão presa em transação abortada.

### 4. Produção: container não acessava o PostgreSQL do Portal RH
Na produção, mesmo com as envs corretas, o container `delpi-api-delpi` não conseguia alcançar `192.168.1.237:5432` inicialmente.

Os testes comprovaram:
- do host: conexão TCP funcionava
- do container: havia timeout
- depois do ajuste no firewall: TCP passou
- em seguida o PostgreSQL negava por `pg_hba.conf`

# Configuração de produção feita para o Portal RH

## Situação observada em produção

### Variáveis no container
Foi validado que o container `delpi-api-delpi` recebia corretamente:
- `PORTAL_RH_DB_HOST=192.168.1.237`
- `PORTAL_RH_DB_PORT=5432`
- `PORTAL_RH_DB_NAME=portal_rh`
- `PORTAL_RH_DB_USER=ti_delpi`
- `PORTAL_RH_DB_PASSWORD=Delpi@2022`
- `PORTAL_RH_DB_CONNECT_TIMEOUT=5`
- `PORTAL_RH_DB_SSLMODE=prefer`

### Diagnóstico de conectividade
O host de produção era o próprio `192.168.1.237`, e o container saía pela rede Docker `172.19.0.x`. No `ufw`, a porta `5432` estava liberada apenas para `192.168.1.0/24`, então o host conseguia conectar, mas o container não.

## Ajuste de firewall (UFW)

### Decisão operacional final
Foi decidido abrir o PostgreSQL do Portal RH para qualquer container da rede Docker `172.19.0.0/16`, em vez de só um IP específico de container.

### Regra operacional adotada
No `ufw`, a liberação final deve ser mantida como:

```bash
sudo ufw allow from 172.19.0.0/16 to any port 5432 proto tcp
```

## Ajuste do PostgreSQL (`pg_hba.conf`)

Depois que o firewall passou a permitir o tráfego, o PostgreSQL do Portal RH ainda negava a conexão por falta de entrada correspondente no `pg_hba.conf`.

### Configuração final recomendada
A configuração final recomendada para o `pg_hba.conf` passa a ser:

```conf
host    portal_rh    ti_delpi    172.19.0.0/16    scram-sha-256
```

ou `md5`, caso a instalação esteja usando esse método.

### Aplicação
Depois da alteração, foi necessário recarregar o PostgreSQL:

```bash
sudo systemctl reload postgresql
```

## Resultado final em produção

Após:
- ajuste das envs no compose
- liberação da rede Docker no `ufw`
- inclusão da rede Docker no `pg_hba.conf`
- reload do PostgreSQL

o teste dentro do container passou com sucesso:
- conexão PostgreSQL estabelecida
- `SELECT 1` retornando `(1,)`
- `PG_OK`

Isso comprovou que o `delpi-api-delpi` já consegue acessar o banco `portal_rh` em produção.

# Integração do Financeiro no Strategic Indicators

## Objetivo

Conectar o departamento Financeiro ao Strategic Indicators usando uma fonte híbrida:
- dados monetários e operacionais vindos de Google Sheets
- `rol_with_ipi` vindo do módulo financeiro já existente no TOTVS

## Premissas do Financeiro

### Peso do Financeiro no modelo IGD/IDD

No modelo consolidado de IGD/IDD:
- Financeiro pesa 15% no IGD
- o IDD Financeiro possui 3 indicadores

### Catálogo oficial do Financeiro

O catálogo oficial do seed consolidado define:
- `department_id`: `financial`
- `short_name`: `FIN`
- `aggregation_mode`: `consolidated`

Indicadores oficiais:
- `financial-ebitda`
- `financial-fixed-cost`
- `financial-pmr`

Pesos e metas:
- `financial-ebitda`
  - peso: `40%`
  - meta: `13.0`
  - periodicidade: `monthly`
- `financial-fixed-cost`
  - peso: `30%`
  - meta: `14.0`
  - periodicidade: `monthly`
- `financial-pmr`
  - peso: `30%`
  - meta: `39`
  - periodicidade: `monthly`

## Fontes do Financeiro

### Google Sheets
As abas definidas para o Financeiro são:
- `ebitida`
  - colunas: `filial`, `data`, `ebitida`, `created_at`, `updated_at`, `deleted`
- `custos_fixos`
  - colunas: `filial`, `data`, `custos_fixos`, `created_at`, `updated_at`, `deleted`
- `recebimento`
  - colunas: `filial`, `data`, `prazo_medio_recebimento`, `created_at`, `updated_at`, `deleted`

### TOTVS / módulo financial
O indicador usa como base de receita o campo:
- `rol_with_ipi`

## Regras de cálculo do Financeiro

### ROL base
Foi confirmado que o ROL utilizado será:
- `rol_with_ipi`

### Fórmulas oficiais adotadas
- **EBITDA / Receita Operacional** = `ebitida / rol_with_ipi`
- **% Custos Fixos / Receita Operacional** = `custos_fixos / rol_with_ipi`
- **Prazo Médio de Recebimento (PMR)** = `prazo_medio_recebimento`

### Consolidação por filial
O Financeiro foi desenhado para:
- calcular os indicadores por filial
- devolver `unit_values` por filial
- consolidar o valor final como média entre as filiais

Mesmo com `aggregation_mode = consolidated`, os `unit_values` seguem disponíveis para análise.

## Arquitetura adotada para o Financeiro

```text
Google Sheets + FinancialRepository.get_rol()
 -> FinancialMetricsSpreadsheetRepository
 -> FinancialMetricsSnapshotService
 -> FinancialIndicatorsSnapshotProvider
 -> RealStrategicIndicatorsMeasurementsProvider
 -> StrategicIndicatorsSnapshotService
```

### Componentes definidos
Foram definidos os seguintes componentes para o Financeiro:
- `sheet_sources.py`
- `financial_metrics_repository.py`
- `financial_metrics_snapshot_service.py`
- `financial_indicators_snapshot_port.py`
- `financial_indicators_snapshot_provider.py`
- ajustes em `financial_composer.py`
- ajustes em `strategic_indicators_composer.py`
- ajustes em `real_indicator_measurements_provider.py`

## Situação atual do Financeiro

### O que já está resolvido
- pesos, metas e IDs oficiais do catálogo definidos
- uso de `rol_with_ipi` confirmado
- fórmulas dos 3 indicadores definidas
- leitura de Google Sheets alinhada ao `GoogleSheetsClient`
- consolidação por filial definida
- provider e snapshot service desenhados

### Indicadores do Financeiro
- `financial-ebitda` = `ebitida / rol_with_ipi`
- `financial-fixed-cost` = `custos_fixos / rol_with_ipi`
- `financial-pmr` = `prazo_medio_recebimento`

# Padronização universal de datas de planilha

## Problema identificado

Os módulos que consomem planilhas estavam usando estratégias diferentes para interpretar datas:
- Produção comparava `row["data"]` como texto
- Auditoria 5S fazia parsing local e também chamava `Utils.parse_date(...)`
- Kaizen dependia de `Utils.parse_date(...)` para filtro de período e cálculo financeiro
- Financeiro precisava lidar com datas heterogêneas vindas de planilhas

Isso gerava risco de falhas com formatos como:
- `dd/mm/yyyy`
- `dd-mm-yyyy`
- `yyyy-mm-dd`
- `yyyy/mm/dd`
- strings com hora
- serial numérico do Excel, como `45567`

## Decisão adotada

Foi definida a criação de um **conversor universal de datas de planilha**, centralizado e reutilizável, para suportar todos os formatos mais comuns que podem chegar do Google Sheets e do Excel.

## Arquitetura proposta

Foi definido um helper compartilhado com responsabilidade de:
- converter valores de planilha em `date`
- aceitar strings, números, floats e datas com hora
- suportar datas numéricas do Excel
- normalizar filtros de intervalo

## Módulos impactados

### Produção
Os repositories:
- `direct_labor_repository.py`
- `production_cost_repository.py`
- `depreciation_repository.py`

passam a usar o conversor universal em vez de comparar strings diretamente.

### Financeiro
O `FinancialMetricsSnapshotService` passa a reutilizar o mesmo helper para filtrar linhas por período, evitando normalização manual isolada.

### Auditoria 5S
O `Audit5SRepository` passa a depender do parser universal para:
- formatar datas para apresentação
- filtrar intervalo de datas

### Kaizen
O `KaizenRepository` passa a depender do parser universal para:
- filtrar período
- calcular dias ativos
- calcular savings total no intervalo

## Benefício da padronização

Com isso, Produção, Financeiro, Auditoria 5S e Kaizen passam a compartilhar a mesma lógica de parsing de datas de planilha, reduzindo bugs, duplicação e inconsistências entre módulos.

# Produção — validação da lógica atual

## Situação observada

A Produção já estava funcionando de forma semelhante ao Financeiro:
- lê valores monetários da planilha
- busca `rol_with_ipi`
- calcula os percentuais por filial
- consolida matriz e filial por média no provider

### Indicadores já operando nesse modelo
- `production-direct-labor` = custo mão de obra direta / `rol_with_ipi`
- `production-costs` = custo de produção / `rol_with_ipi`
- `production-depreciation` = depreciação / `rol_with_ipi`

### Fontes dos numeradores
- `custo_mao_de_obra_direta`
- `custo_de_producao`
- `depreciacao`

### Ajuste necessário identificado
O principal ponto frágil da Produção era o filtro de data textual nos repositories de planilha. Esse ponto passou a ser coberto pela padronização universal de datas.

# Situação geral atual da Fase 5

## O que já está resolvido
- snapshot service global consolidado
- providers departamentais mais finos
- paralelização da coleta por área
- RH integrado estruturalmente ao módulo
- conectividade de produção com Portal RH resolvida
- Financeiro desenhado com catálogo oficial e fórmulas fechadas
- Produção validada no mesmo modelo lógico do Financeiro
- parser universal de datas de planilha definido e aplicado nos módulos críticos

## O que ainda falta
- validar os retornos reais das rotas de RH em produção
- concluir os indicadores restantes do RH:
  - satisfação interna
  - PDIs ativos
- aplicar e validar o pacote completo do Financeiro no backend
- validar em runtime a padronização universal de datas nas planilhas
- avançar para Suprimentos e demais áreas faltantes

## Pendências reais da fase

1. validar em produção as rotas com RH real
2. concluir a implementação efetiva do Financeiro no backend
3. confirmar a origem oficial dos indicadores restantes do RH
4. validar a refatoração de datas em Produção, Financeiro, Kaizen e Auditoria 5S
5. expandir a mesma abordagem para Suprimentos e outras áreas ainda faltantes no cálculo agregado

## Diretrizes para continuidade

- manter Clean Architecture
- backend concentra regra de negócio e orquestração
- snapshot services concentram composição transversal
- providers departamentais devem ser finos e focados
- planilhas devem usar o parser universal de datas
- configurações operacionais de produção fazem parte da integração técnica dos departamentos

## Próximo passo sugerido

Seguir nesta ordem:

1. validar RH real nas rotas de Strategic Indicators
2. aplicar o pacote completo do Financeiro
3. validar a padronização universal de datas em runtime
4. concluir os indicadores pendentes do RH
5. iniciar Suprimentos com o mesmo padrão de snapshot service e fontes híbridas quando necessário

