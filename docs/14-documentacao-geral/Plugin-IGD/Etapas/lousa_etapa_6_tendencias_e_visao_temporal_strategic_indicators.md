# Etapa 6 — Tendências e visão temporal do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Introduzir a leitura histórica do IGD e dos IDDs departamentais, permitindo entender não apenas o valor atual, mas também o comportamento e a evolução do desempenho ao longo do tempo.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 6 — Tendências e visão temporal**.

Objetivos previstos:
- criar leitura histórica do IGD
- criar leitura histórica dos departamentos
- introduzir noção de evolução temporal
- preparar o caminho para alertas e priorização futura

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base conceitual da etapa
- manter o IGD como nota global consolidada
- manter os 7 departamentos oficiais do índice
- preservar as faixas de interpretação do IGD
- estruturar uma série temporal mock coerente com a visão mensal do painel

### 2. Definir o recorte funcional da fase
- criar rota visual de tendências
- criar visão histórica do IGD
- criar visão temporal dos departamentos
- criar leitura executiva da variação do índice

### 3. Criar os componentes mínimos desta etapa
- `TrendHeroCard`
- `IgdTrendTimeline`
- `DepartmentTrendGrid`
- `DepartmentTrendCard`

### 4. Criar dados mock temporais
- competências mensais
- valores do IGD por mês
- valores resumidos dos departamentos por mês
- variação simples entre meses

### 5. Adaptar a navegação do plugin
- manter as rotas já existentes
- fazer `/trends` virar a visão temporal central

### 6. Definir critérios de validação da etapa
- o usuário deve entender a evolução do IGD
- o usuário deve comparar rapidamente o comportamento dos departamentos
- a tela deve estar pronta para futura API real de séries históricas

---

## Base documental consolidada para esta etapa

### Estrutura oficial do índice
- o IGD é uma nota global de 0 a 10
- ele consolida os resultados dos principais departamentos
- é apresentado mensalmente no Painel Estratégico de Indicadores

### Departamentos oficiais do índice
- Financeiro
- RH
- Comercial
- Produção
- Qualidade
- Suprimentos
- Engenharia

### Faixas de interpretação
- Excelência Integrada
- Alto Desempenho
- Satisfatório com Alertas
- Regular, Exige Ação
- Crítico

---

## Decisão de execução da etapa

Nesta etapa, o foco será criar a **primeira leitura temporal do painel**.

Entra agora:
- tendência do IGD
- leitura temporal dos departamentos
- noção de melhora, estabilidade ou piora
- base visual para histórico

Não entra agora:
- API real
- gráficos históricos avançados
- alertas automáticos
- exportação

---

## Entregáveis previstos ao final da etapa
- página `/trends` funcionando
- leitura histórica do IGD
- leitura resumida da evolução dos departamentos
- base pronta para a etapa de alertas

---

## Encerramento oficial da etapa

A **Fase 6 — Tendências e visão temporal** foi concluída com sucesso.

### O que foi entregue
- rota `/trends` funcionando
- hero temporal do IGD
- síntese temporal da variação do índice
- comparação do último fechamento
- destaques do período
- timeline mensal mock do IGD
- leitura de pontos de atenção
- grid temporal dos departamentos

### Base documental aplicada
A etapa foi construída com base no documento oficial consolidado do IGD/IDD, usando:
- IGD como nota global mensal
- os 7 departamentos oficiais do índice
- faixas de classificação executiva
- coerência com a leitura estratégica do painel

### Resultado final da etapa
O plugin agora permite:
- visão executiva consolidada do IGD
- drill-down inicial por departamento
- visão analítica dos indicadores
- visão temporal do índice e dos departamentos
- leitura gerencial de melhora, estabilidade e queda no período

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 7 — Alertas e priorização**

Objetivo da próxima etapa:
- transformar o painel em instrumento de ação
- destacar riscos e prioridades
- estruturar leitura de criticidade antes de integrações e automações futuras
