# Etapa 3 — MVP 1: Visão Executiva do plugin Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Construir a primeira tela útil do dashboard executivo, introduzindo a visão consolidada do IGD e a base visual dos IDDs departamentais, sem ainda entrar no drill-down analítico completo.

---

## Referência da etapa no roadmap
Esta etapa corresponde à **Fase 3 — MVP 1: Visão Executiva**.

Objetivos previstos:
- construir a primeira tela útil do dashboard
- introduzir hero do IGD
- introduzir faixa de classificação
- introduzir cards dos departamentos
- iniciar os primeiros blocos executivos reais

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar o conteúdo executivo oficial do IGD
- confirmar pesos por departamento
- confirmar faixas de classificação
- confirmar nota de exemplo que será usada no MVP inicial
- confirmar departamentos que compõem o índice

### 2. Definir o recorte funcional do MVP executivo
- hero do IGD
- faixa de classificação
- cards resumidos dos departamentos
- bloco de explicação executiva
- bloco de próximos passos ou leitura gerencial

### 3. Criar os componentes executivos mínimos
- `IgdHeroCard`
- `ClassificationBand`
- `DepartmentSummaryCard`
- `DepartmentSummaryGrid`

### 4. Adaptar a página `ExecutiveDashboardPage`
- substituir os blocos de fundação visual por blocos executivos reais
- introduzir conteúdo derivado do documento oficial do IGD/IDD
- manter layout preparado para evolução futura

### 5. Definir dados mock iniciais do MVP
- criar estrutura temporária para IGD
- criar estrutura temporária para departamentos
- manter os mocks alinhados ao documento oficial

### 6. Definir critérios de validação da etapa
- a tela deve comunicar o IGD rapidamente
- a classificação deve ser compreensível
- os departamentos devem aparecer com peso e nota
- a interface deve estar pronta para futura integração com API real

---

## Base documental consolidada para esta etapa

### Estrutura do IGD
- o IGD é uma nota global de 0 a 10
- ele consolida os principais departamentos em uma única nota
- ele é apresentado mensalmente no Painel Estratégico de Indicadores

### Departamentos e pesos
- Financeiro: 15%
- RH: 15%
- Comercial: 17%
- Produção: 17%
- Qualidade: 14%
- Suprimentos: 12%
- Engenharia: 10%

### Exemplo consolidado de nota
- IGD calculado: 7,768
- IGD arredondado: 7,8

### Faixas de classificação
- 9,0 a 10: Excelência Integrada
- 8,0 a 8,9: Alto Desempenho
- 7,0 a 7,9: Satisfatório com Alertas
- 6,0 a 6,9: Regular, Exige Ação
- abaixo de 6: Crítico

---

## Decisão de execução da etapa

Nesta etapa, o foco será construir a **primeira leitura executiva real** do dashboard.

Não entra ainda:
- drill-down por departamento
- tabela analítica completa de indicadores
- tendências históricas detalhadas
- alertas avançados
- integração com API real

Entra agora:
- hero do IGD
- régua de classificação
- cards resumidos dos 7 departamentos
- leitura executiva inicial

---

## Entregáveis previstos ao final da etapa
- hero do IGD funcionando
- faixa de classificação visível
- grid de departamentos com notas e pesos
- tela principal do plugin com leitura executiva real
- MVP visual pronto para futura integração com API

---

## Subexecução em andamento — enriquecimento executivo dos departamentos

### Objetivo desta subexecução
Aprofundar o MVP executivo sem sair do escopo da Fase 3, adicionando contexto gerencial aos departamentos com base no documento oficial do IGD/IDD.

### Fonte oficial utilizada
O documento consolidado do IGD/IDD define:
- pesos oficiais por departamento
- exemplo de cálculo do IGD com nota 7,768 → 7,8
- faixas de classificação do IGD
- indicadores e descrições estratégicas de cada IDD departamental

### Recorte desta subexecução
Entra agora:
- descrição estratégica resumida por departamento
- preview dos principais indicadores de cada IDD
- leitura mais executiva dos cards departamentais

Não entra agora:
- drill-down completo por departamento
- tabela analítica completa dos indicadores
- API real
- gráficos históricos

### Arquivos previstos para ajuste nesta subexecução
- `src/ui/components/ExecutiveMethodCard.tsx`
- `src/ui/pages/ExecutiveDashboardPage.tsx`
- `src/index.css`

### Resultado esperado após esta subexecução
- leitura metodológica do IGD explícita na tela
- melhor entendimento de como o índice é formado
- MVP executivo praticamente fechado para validação final

---

## Encerramento oficial da etapa

A **Fase 3 — MVP 1: Visão Executiva** foi concluída com sucesso.

### O que foi entregue
- hero do IGD com valor consolidado
- faixa interpretativa do IGD
- leitura executiva lateral com destaques
- bloco metodológico mostrando a soma ponderada do índice
- ranking de contribuição por departamentos
- grid de departamentos com:
  - peso oficial
  - nota resumida
  - contribuição ponderada
  - foco estratégico
  - meta executiva de referência
  - indicadores-chave resumidos

### Base documental aplicada
O MVP foi construído com base no documento oficial consolidado do IGD/IDD, usando:
- pesos oficiais por departamento
- fórmula do IGD
- exemplo de cálculo 7,768 → 7,8
- faixas de classificação
- metas 2026 e indicadores dos IDDs departamentais

### Resultado final da etapa
A tela principal do plugin agora comunica de forma executiva:
- o que é o IGD
- qual é a nota atual do exemplo oficial
- em que faixa o índice se encontra
- como o índice é calculado
- como os departamentos participam da composição do resultado

### Próxima etapa do roadmap
A próxima etapa é:

**Fase 4 — MVP 2: Departamentos e drill-down**

Objetivo da próxima etapa:
- permitir leitura analítica por área
- criar visão específica de departamento
- preparar o caminho para o detalhamento dos indicadores de cada IDD
