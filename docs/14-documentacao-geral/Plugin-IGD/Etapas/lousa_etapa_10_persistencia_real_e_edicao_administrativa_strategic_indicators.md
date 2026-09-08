# Etapa 10 — Persistência real e edição administrativa do Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Conectar a camada administrativa do módulo à persistência real, preparando pesos, metas e parâmetros para leitura e edição controlada via backend, mantendo aderência ao ecossistema RBAC e ao contrato oficial do manifesto.

---

## Referência da etapa
Esta etapa nasce da evolução natural após a conclusão de:
- visão executiva do IGD
- drill-down departamental
- visão analítica de indicadores
- tendências e visão temporal
- alertas e priorização
- modo apresentação
- configurações e governança administrativa

Também está alinhada ao manifesto atual do plugin, que já prevê:
- backend compartilhado via `api-delpi`
- rota administrativa `/settings`
- permissão `strategic-indicators.settings.manage`

---

## Lista oficial do que deve ser feito nesta etapa

### 1. Consolidar a base conceitual da etapa
- manter o IGD como índice governado
- preservar pesos oficiais e metas como entidades persistíveis
- separar leitura, edição e persistência em camadas corretas
- manter o RBAC como guardião do acesso administrativo

### 2. Definir o recorte funcional da fase
- criar contratos de leitura e atualização das configurações
- preparar backend do módulo dentro da `api-delpi`
- preparar frontend da rota `/settings` para consumir API real
- manter fallback claro para erros e estados de carregamento

### 3. Criar os componentes mínimos desta etapa
- DTOs/contratos de configuração
- casos de uso de leitura e atualização
- controller/rota backend de configuração
- client data layer no frontend
- versão conectada da `SettingsPage`

### 4. Definir escopo de persistência inicial
- pesos por departamento
- metas resumidas por área
- parâmetros globais do painel
- observações mínimas de governança

### 5. Adaptar a governança do módulo
- respeitar `strategic-indicators.settings.manage`
- manter backend sob `api-delpi`
- manter contrato coerente com manifesto e Core API

### 6. Definir critérios de validação da etapa
- o usuário deve conseguir ler configurações reais
- o usuário deve conseguir editar o escopo inicial definido
- o backend deve validar permissão e JWT
- a UI deve refletir estados de loading, sucesso e erro

---

## Base documental consolidada para esta etapa

### Estrutura oficial do índice
- o IGD é uma nota global de 0 a 10
- sua composição usa pesos oficiais por departamento
- cada área possui metas 2026 e descrição estratégica

### Base de integração do plugin
- manifesto oficial do plugin Strategic Indicators
- backend apontando para `api-delpi`
- `validateJwt=true`
- `audience=delpi-central`
- `issuer=https://www.minhadelpi.com.br/auth`

### Base arquitetural da DELPI Central
- registro formal de plugins
- resolução dinâmica por RBAC
- pipeline de validação de manifesto
- separação entre Core API, Portal e Plugins

---

## Decisão de execução da etapa

Nesta etapa, o foco será criar a **primeira persistência real do módulo**.

Entra agora:
- leitura real das configurações
- edição administrativa inicial
- integração backend/frontend da rota `/settings`
- tratamento mínimo de erro e sucesso

Não entra agora:
- workflow de aprovação
- auditoria avançada de mudanças
- histórico versionado de configuração
- automações administrativas

---

## Entregáveis previstos ao final da etapa
- leitura real das configurações do módulo
- atualização inicial de pesos/metas/parâmetros
- rota `/settings` conectada ao backend
- base pronta para auditoria e evolução posterior

---

## Encerramento oficial da etapa

A **Fase 10 — Persistência real e edição administrativa** foi concluída com sucesso.

### O que foi entregue
- migrations do plugin aplicadas no `postgres-plugins`
- schema `strategic_indicators` criado e versionado
- tabela `module_settings` criada com seed inicial
- leitura real via `GET /strategic-indicators/settings`
- atualização real via `PUT /strategic-indicators/settings`
- validação de pesos, metas, parâmetros e governança no backend
- integração frontend ↔ backend ↔ banco funcionando na rota `/settings`
- substituição do editor JSON por formulário administrativo estruturado
- proteção da rota com `require_permission("strategic-indicators.settings.manage")`
- ajuste do shared `delpi_auth` para suportar rotas sync e async
- trilha de auditoria mínima persistida no backend
- auditoria visível no frontend da rota `/settings`
- captura correta de autoria e resumo de alteração por bloco

### Base documental aplicada
A etapa foi construída com base em:
- documento consolidado do IGD/IDD
- manifesto oficial vigente da DELPI Central
- instrução operacional fixa do projeto
- padrão de Clean Architecture da `api-delpi`
- diretriz de plugin com backend na `api-delpi` e persistência em `postgres-plugins`

### Resultado final da etapa
O plugin agora possui:
- visão executiva do IGD
- drill-down departamental
- visão analítica e temporal
- alertas e priorização
- modo apresentação
- camada administrativa de governança
- persistência real de configurações
- edição administrativa real
- auditoria mínima de alterações

### Próxima etapa sugerida
A próxima etapa natural é:

**Fase 11 — Endurecimento administrativo e histórico evolutivo**

Objetivo da próxima etapa:
- consolidar UX administrativa final
- endurecer governança da edição
- evoluir auditoria para histórico mais útil
- preparar base para workflows futuros sem quebrar a arquitetura

