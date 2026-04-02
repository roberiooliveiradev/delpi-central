# Etapa 9 — Configurações e governança do painel Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Estruturar a camada de configurações e governança do painel, preparando o módulo para administrar pesos, metas, parâmetros e controles de uso, antes de integrações e automações futuras.

---

## Referência da etapa
Esta etapa nasce da evolução natural do plugin após:
- visão executiva do IGD
- drill-down departamental
- visão analítica dos indicadores
- visão temporal
- alertas e priorização
- modo apresentação

Também está alinhada ao manifesto atual do plugin, que já prevê a rota de configurações e a permissão administrativa correspondente.

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base conceitual da etapa
- manter o IGD como índice global governado
- preservar os 7 departamentos oficiais
- preservar pesos, metas e parâmetros como entidades administráveis
- separar claramente visualização operacional de governança administrativa

### 2. Definir o recorte funcional da fase
- criar rota visual de configurações
- apresentar visão administrativa do módulo
- organizar pesos, metas e parâmetros em blocos distintos
- preparar a tela para futura persistência real

### 3. Criar os componentes mínimos desta etapa
- `SettingsHero`
- `SettingsWeightsPanel`
- `SettingsGoalsPanel`
- `SettingsGovernancePanel`
- `SettingsPage`

### 4. Criar dados mock de governança
- pesos por departamento
- metas resumidas por área
- parâmetros globais do painel
- status de governança e observações administrativas

### 5. Adaptar a navegação do plugin
- manter as rotas já existentes
- fazer `/settings` virar a visão central de administração e governança do módulo

### 6. Definir critérios de validação da etapa
- o usuário deve entender rapidamente o que é configurável no painel
- a tela deve separar pesos, metas e parâmetros
- a solução deve ficar pronta para futura persistência via API real

---

## Base documental consolidada para esta etapa

### Estrutura oficial do índice
- o IGD é uma nota global de 0 a 10
- ele consolida os resultados dos principais departamentos
- sua composição usa pesos oficiais por departamento

### Base para governança
- pesos oficiais do IGD
- metas 2026 por indicador e por área
- manifesto com rota administrativa do plugin
- permissão específica para gerenciamento das configurações

---

## Decisão de execução da etapa

Nesta etapa, o foco será criar a **primeira visão administrativa do painel**.

Entra agora:
- modo configurações
- blocos de pesos
- blocos de metas
- governança e observações administrativas

Não entra agora:
- persistência real
- edição salva em banco
- workflow de aprovação
- auditoria administrativa avançada
- automação de configuração

---

## Entregáveis previstos ao final da etapa
- página `/settings` funcionando
- visão administrativa do painel
- separação entre pesos, metas e parâmetros
- base pronta para futura integração real

---

## Encerramento oficial da etapa

A **Fase 9 — Configurações e governança do painel** foi concluída com sucesso.

### O que foi entregue
- rota `/settings` funcionando
- hero administrativo do módulo
- síntese de governança
- parâmetros globais do painel
- painel de pesos oficiais do IGD
- painel de metas resumidas por área
- painel de governança do módulo
- leitura de prontidão administrativa
- destaque executivo da governança
- painel de próxima ação administrativa

### Base documental aplicada
A etapa foi construída com base no documento oficial consolidado do IGD/IDD e no contrato vigente do manifesto de plugins, usando:
- os pesos oficiais do IGD totalizando 100%
- metas 2026 por área e por indicador
- rota administrativa `/settings`
- permissão `strategic-indicators.settings.manage`
- governança formal do ecossistema de plugins da DELPI Central

### Resultado final da etapa
O plugin agora permite:
- visão executiva consolidada do IGD
- drill-down inicial por departamento
- visão analítica dos indicadores
- visão temporal do painel
- leitura acionável de criticidade e prioridade
- modo apresentação para reuniões
- camada administrativa inicial de governança do módulo

### Próxima etapa sugerida
A próxima etapa natural é:

**Fase 10 — Persistência real e edição administrativa**

Objetivo da próxima etapa:
- estruturar persistência para pesos, metas e parâmetros
- conectar a tela administrativa à API real
- preparar trilha de edição controlada antes de auditoria avançada
