# Etapa 4 — MVP 2: Departamentos e drill-down do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Evoluir o plugin da visão executiva consolidada para uma leitura analítica por departamento, criando uma visão específica de área e preparando o caminho para o detalhamento progressivo dos indicadores de cada IDD.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 4 — MVP 2: Departamentos e drill-down**.

Objetivos previstos:
- permitir leitura analítica por área
- criar visão específica de departamento
- preparar o caminho para o detalhamento dos indicadores de cada IDD

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base oficial de departamentos e indicadores
- manter os 7 departamentos oficiais do IGD
- manter os pesos oficiais por departamento
- manter os indicadores oficiais de cada IDD
- manter as metas 2026 associadas a cada indicador

### 2. Definir o recorte funcional do MVP 2
- criar rota visual de departamentos
- criar rota visual de detalhe do departamento
- permitir seleção de área a partir do dashboard ou da rota dedicada
- apresentar os indicadores do IDD como cards ou linhas resumidas

### 3. Criar os componentes mínimos desta etapa
- `DepartmentOverviewTable` ou equivalente comparativo
- `DepartmentDetailHero`
- `IndicatorDetailCard`
- `IndicatorDetailGrid`

### 4. Adaptar a navegação do plugin
- manter a visão executiva como entrada principal
- fazer a rota `/departments` virar a visão comparativa das áreas
- fazer a rota `/departments/:departmentId` virar o drill-down da área

### 5. Criar dados mock estruturados para departamentos
- departamento
- peso
- nota IDD
- foco estratégico
- lista de indicadores
- meta 2026
- peso interno do indicador
- descrição estratégica

### 6. Definir critérios de validação da etapa
- o usuário deve conseguir comparar departamentos
- o usuário deve conseguir abrir uma área específica
- o usuário deve visualizar os indicadores que compõem o IDD da área
- a solução deve continuar pronta para futura API real

---

## Base documental consolidada para esta etapa

### Estrutura do IGD
- o IGD é uma nota global de 0 a 10
- ele consolida os IDDs departamentais em uma única nota
- sua composição é ponderada pelos pesos oficiais

### Departamentos e pesos
- Financeiro: 15%
- RH: 15%
- Comercial: 17%
- Produção: 17%
- Qualidade: 14%
- Suprimentos: 12%
- Engenharia: 10%

### Estrutura dos IDDs
Cada departamento possui seu próprio IDD, formado por indicadores-chave com:
- peso interno
- meta 2026
- descrição estratégica

---

## Decisão de execução da etapa

Nesta etapa, o foco será a **primeira leitura analítica por departamento**.

Entra agora:
- visão comparativa de departamentos
- detalhe do departamento
- indicadores resumidos da área
- metas e pesos dos indicadores

Não entra agora:
- API real
- histórico mensal detalhado
- alertas avançados
- cruzamento entre departamentos
- configurações administrativas

---

## Entregáveis previstos ao final da etapa
- página de departamentos funcionando
- página de detalhe do departamento funcionando
- cards ou blocos com indicadores do IDD
- leitura mais analítica por área
- base pronta para futuras integrações reais

---

## Encerramento oficial da etapa

A **Fase 4 — MVP 2: Departamentos e drill-down** foi concluída com sucesso.

### O que foi entregue
- visão comparativa de departamentos em rota dedicada
- drill-down inicial por área
- detalhe do departamento com hero próprio
- indicadores do IDD exibidos com:
  - peso interno
  - meta 2026
  - descrição estratégica
- navegação do plugin ajustada com base em `pathname`
- manifesto atualizado com rotas explícitas de detalhe por departamento
- gateway de desenvolvimento corrigido para respeitar a lógica do portal shell
- gateway de produção alinhado à mesma lógica estrutural

### Base documental aplicada
A etapa foi construída com base no documento oficial consolidado do IGD/IDD, usando:
- os 7 departamentos oficiais do IGD
- pesos oficiais por departamento
- indicadores de cada IDD
- metas 2026
- descrições estratégicas dos indicadores

### Resultado final da etapa
O plugin agora permite:
- visão executiva consolidada do IGD
- visão comparativa das áreas
- abertura de um departamento específico
- leitura inicial do IDD da área e de seus indicadores

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 5 — MVP 3: Indicadores analíticos**

Objetivo da próxima etapa:
- criar a visão operacional e analítica completa dos indicadores
- introduzir filtros, busca e tabela estruturada
- preparar a camada de análise detalhada antes das tendências e alertas
