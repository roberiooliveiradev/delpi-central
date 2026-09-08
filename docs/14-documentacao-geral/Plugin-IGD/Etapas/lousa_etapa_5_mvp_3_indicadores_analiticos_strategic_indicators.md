# Etapa 5 — MVP 3: Indicadores analíticos do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Criar a visão operacional e analítica completa dos indicadores, permitindo leitura detalhada por indicador, com filtros, busca e estrutura pronta para futura integração com API real.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 5 — MVP 3: Indicadores analíticos**.

Objetivos previstos:
- criar a visão operacional e analítica completa
- introduzir filtros avançados
- introduzir busca textual
- criar tabela estruturada de indicadores
- preparar o caminho para exportação e análises futuras

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base oficial de indicadores
- manter os indicadores oficiais de cada IDD
- manter pesos internos por indicador
- manter metas 2026 por indicador
- manter descrições estratégicas

### 2. Definir o recorte funcional do MVP 3
- criar rota visual de indicadores
- permitir busca textual
- permitir filtro por departamento
- permitir filtro por faixa de status
- apresentar tabela estruturada dos indicadores

### 3. Criar os componentes mínimos desta etapa
- `IndicatorFiltersBar`
- `IndicatorAnalyticsTable`
- `IndicatorAnalyticsRow` ou equivalente
- `IndicatorAnalyticsPage`

### 4. Criar dados mock estruturados para indicadores
- departamento
- indicador
- peso interno
- meta 2026
- descrição estratégica
- nota simulada
- status visual

### 5. Adaptar a navegação do plugin
- manter a visão executiva e o drill-down já existentes
- fazer a rota `/indicators` virar a visão analítica central dos indicadores

### 6. Definir critérios de validação da etapa
- o usuário deve conseguir listar e comparar indicadores
- o usuário deve conseguir filtrar por departamento
- o usuário deve conseguir buscar um indicador específico
- a tabela deve continuar pronta para futura API real

---

## Base documental consolidada para esta etapa

### Estrutura oficial dos indicadores
Cada departamento possui indicadores oficiais no IDD, com:
- peso interno
- meta 2026
- descrição estratégica

### Escopo desta etapa
Entram agora:
- busca
- filtros
- tabela analítica
- leitura cruzada entre departamentos por indicador

Não entram agora:
- API real
- exportação funcional
- histórico temporal por indicador
- alertas avançados

---

## Entregáveis previstos ao final da etapa
- página de indicadores funcionando
- barra de filtros funcionando em mock
- tabela analítica de indicadores funcionando
- visão operacional pronta para futura integração real

---

## Encerramento oficial da etapa

A **Fase 5 — MVP 3: Indicadores analíticos** foi concluída com sucesso.

### O que foi entregue
- rota `/indicators` funcionando
- barra de filtros com:
  - busca textual
  - filtro por departamento
  - filtro por status
- tabela analítica de indicadores
- síntese analítica da base filtrada
- priorização rápida dos indicadores em atenção
- leitura por departamento
- detalhe rápido do indicador selecionado

### Base documental aplicada
A etapa foi construída com base no documento oficial consolidado do IGD/IDD, usando:
- indicadores oficiais por departamento
- pesos internos
- metas 2026
- descrições estratégicas

### Resultado final da etapa
O plugin agora permite:
- visão executiva consolidada do IGD
- drill-down inicial por departamento
- visão analítica central dos indicadores
- leitura operacional rápida com filtros, síntese, priorização e detalhe rápido

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 6 — Tendências e visão temporal**

Objetivo da próxima etapa:
- introduzir leitura histórica do IGD
- introduzir evolução dos departamentos ao longo do tempo
- preparar a percepção de comportamento e tendência antes da etapa de alertas
