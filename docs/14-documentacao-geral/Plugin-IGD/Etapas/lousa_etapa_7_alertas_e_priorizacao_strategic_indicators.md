# Etapa 7 — Alertas e priorização do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Transformar o painel em instrumento de ação, destacando riscos, prioridades e sinais de criticidade com base na leitura consolidada do IGD, dos departamentos e dos indicadores analíticos.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 7 — Alertas e priorização**.

Objetivos previstos:
- destacar riscos relevantes
- estruturar leitura de criticidade
- consolidar prioridades operacionais e executivas
- preparar o caminho para integrações e automações futuras

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base conceitual da etapa
- manter o IGD como referência executiva central
- manter as faixas de interpretação do índice
- manter os indicadores com status e notas simuladas
- transformar status e tendência em sinais de alerta

### 2. Definir o recorte funcional da fase
- criar rota visual de alertas
- criar leitura de criticidade do painel
- priorizar departamentos e indicadores
- destacar sinais executivos e operacionais

### 3. Criar os componentes mínimos desta etapa
- `AlertsSummaryCards`
- `CriticalDepartmentList`
- `CriticalIndicatorList`
- `AlertsPage`

### 4. Criar dados mock de alertas
- alertas executivos do IGD
- alertas por departamento
- alertas por indicador
- criticidade, impacto e recomendação resumida

### 5. Adaptar a navegação do plugin
- manter as rotas já existentes
- fazer `/alerts` virar a visão central de criticidade e priorização

### 6. Definir critérios de validação da etapa
- o usuário deve entender rapidamente o que exige ação
- o usuário deve conseguir ver prioridades por área e por indicador
- a tela deve preparar bem a futura evolução para notificações e automações

---

## Base documental consolidada para esta etapa

### Estrutura oficial do índice
- o IGD é uma nota global de 0 a 10
- ele consolida os resultados dos principais departamentos
- é apresentado mensalmente no Painel Estratégico de Indicadores

### Faixas de interpretação
- Excelência Integrada
- Alto Desempenho
- Satisfatório com Alertas
- Regular, Exige Ação
- Crítico

### Base para criticidade
A etapa usará como sinais de alerta:
- classificação do IGD
- tendência temporal
- indicadores em faixa de atenção
- áreas em queda no período

---

## Decisão de execução da etapa

Nesta etapa, o foco será criar a **primeira leitura acionável do painel**.

Entra agora:
- alertas executivos
- ranking de criticidade
- indicadores prioritários
- recomendações resumidas

Não entra agora:
- notificações automáticas
- e-mail
- websocket
- regras automatizadas reais
- integração operacional externa

---

## Entregáveis previstos ao final da etapa
- página `/alerts` funcionando
- leitura de criticidade executiva
- priorização por departamento e indicador
- base pronta para futuras automações

---

## Encerramento oficial da etapa

A **Fase 7 — Alertas e priorização** foi concluída com sucesso.

### O que foi entregue
- rota `/alerts` funcionando
- síntese de criticidade do painel
- direcionamento executivo com ação recomendada
- destaque do alerta principal do recorte
- alertas executivos resumidos
- priorização por departamento
- priorização por indicador
- recomendações resumidas para ação

### Base documental aplicada
A etapa foi construída com base no documento oficial consolidado do IGD/IDD, usando:
- o IGD como índice global mensal
- faixas oficiais de classificação executiva
- indicadores departamentais com pesos internos, metas 2026 e descrição estratégica

### Resultado final da etapa
O plugin agora permite:
- visão executiva do IGD
- drill-down inicial por departamento
- visão analítica dos indicadores
- visão temporal do painel
- leitura acionável de criticidade e prioridade

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 8 — Modo apresentação e acabamento do painel**

Objetivo da próxima etapa:
- criar a experiência de apresentação executiva
- preparar uma visualização limpa para reuniões
- consolidar o acabamento final do módulo antes de integrações e automações futuras
