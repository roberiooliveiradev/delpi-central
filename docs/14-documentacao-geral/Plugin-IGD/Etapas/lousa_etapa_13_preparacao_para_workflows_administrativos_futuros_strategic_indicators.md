# Etapa 13 — Preparação para workflows administrativos futuros do Strategic Indicators

## Status da etapa
Concluída

## Objetivo da etapa
Preparar a camada administrativa do módulo para evoluções futuras de workflow, sem ainda implementar aprovação completa, rollback administrativo ou versionamento enterprise.

---

## Referência da etapa
Esta etapa nasce da evolução natural após a conclusão de:
- bootstrap do plugin
- dashboards executivos
- drill-down departamental
- indicadores
- tendências
- alertas
- modo apresentação
- governança administrativa
- persistência real e edição administrativa
- endurecimento administrativo e histórico evolutivo
- refinamento final da experiência administrativa

Também permanece alinhada ao manifesto do plugin, ao padrão `delpi_auth`, à Clean Architecture da `api-delpi` e à persistência em `postgres-plugins`.

---

## Lista oficial do que foi feito nesta etapa

### 1. Preparação estrutural para workflow futuro
- criação da base de solicitações administrativas (`change_requests`)
- criação da base de comentários internos das solicitações
- definição de status inicial controlado (`draft`, `submitted`)
- definição do bloco alvo da solicitação (`weights`, `goals`, `parameters`, `governance`)

### 2. Backend da fila administrativa
- criação de repository dedicado para change requests
- criação de DTOs, ports e use cases
- integração via composer do módulo
- unificação das rotas no mesmo namespace de `strategic-indicators`
- correção final dos paths para `/strategic-indicators/change-requests/*`

### 3. Governança e segurança
- proteção das rotas por `strategic-indicators.settings.manage`
- reaproveitamento do `delpi_auth.authorization`
- extração consistente do ator autenticado via `request.state.user`
- preservação do backend dentro da `api-delpi`

### 4. Frontend da preparação de workflow
- centralização dos tipos de auditoria e change requests
- integração de API para listagem e criação de solicitações
- workspace visual de solicitações administrativas
- incorporação do workspace à rota `/settings`
- manutenção da auditoria já existente sem regressão

### 5. Limite intencional da etapa
Entrou nesta etapa:
- fila administrativa
- criação de solicitação
- comentário interno
- transição simples para `submitted`
- preparação clara para workflow futuro

Não entrou nesta etapa:
- aprovação/reprovação formal
- rollback automático
- anexos
- múltiplos aprovadores
- versionamento enterprise

---

## Base documental aplicada
A etapa foi construída com base em:
- instrução operacional fixa do projeto
- manifesto oficial do plugin Strategic Indicators
- padrão `delpi_auth`
- Clean Architecture da `api-delpi`
- persistência e auditoria validadas no `postgres-plugins`
- diretriz de evolução modular e governada da DELPI Central

---

## Resultado final da etapa
O plugin agora possui:
- fila administrativa própria para futuras mudanças governadas
- comentários internos de solicitações
- status inicial de workflow (`draft` / `submitted`)
- integração backend/frontend da preparação de workflow
- camada administrativa pronta para a próxima evolução sem quebrar a arquitetura

---

## Próxima etapa sugerida
A próxima etapa natural é:

**Fase 14 — Workflow administrativo inicial**

Objetivo da próxima etapa:
- introduzir a primeira camada real de decisão administrativa sobre solicitações,
- sem ainda entrar em workflow enterprise completo.
