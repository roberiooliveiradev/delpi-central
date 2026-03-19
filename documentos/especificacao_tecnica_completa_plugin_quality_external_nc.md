# Especificação Técnica Completa — Plugin de Não Conformidades Externas

## 1. Objetivo

Construir uma aplicação completa para **controle de não conformidades externas da DELPI**, substituindo o processo baseado em planilhas por um módulo oficial da DELPI Central, com:

- registro estruturado de ocorrências
- investigação de causa raiz
- plano de ação
- validação de eficácia
- anexos e evidências
- comentários e auditoria
- dashboard e relatórios
- governança por RBAC e manifesto oficial

---

## 2. Decisão arquitetural final

### 2.1 Estrutura da solução

A solução será composta por:

- **frontend próprio do plugin**
- **backend hospedado dentro da `api-delpi`**
- **persistência no banco `postgres-plugins`**
- **governança central pela DELPI Central (Core API + manifesto + permissões + menu dinâmico)**

### 2.2 O que isso significa na prática

#### Frontend
Será um plugin real da plataforma, por exemplo:

`/plugins/quality-external-nc`

#### Backend
Não será criado um serviço novo agora. O domínio será implementado como **novo bounded context dentro da `api-delpi`**.

#### Banco
Os dados do módulo não ficarão no banco do TOTVS nem devem reutilizar a infraestrutura atual de SQL Server. O módulo usará o **`postgres-plugins`** já existente na stack.

---

## 3. Princípios obrigatórios de implementação

1. **Não misturar o domínio do plugin com o domínio TOTVS**.
2. **Não reutilizar a `BaseRepository` atual do TOTVS/SQL Server** para persistência do módulo.
3. **Criar datasource PostgreSQL separado** dentro da `api-delpi`.
4. **Seguir Clean Architecture** no backend.
5. **Seguir segregação UI / state / data** no frontend.
6. **Aplicar permissões granulares por recurso e ação**.
7. **Registrar o plugin por manifesto oficial**.
8. **Manter auditoria das ações críticas**.
9. **Centralizar autenticação e autorização no padrão DELPI Central**.
10. **Tratar a aplicação como produto corporativo, não como planilha digitalizada**.

---

## 4. Escopo funcional completo

### 4.1 Módulo de cadastro e triagem
Responsável pela abertura da ocorrência.

Funcionalidades:
- registrar fornecedor
- registrar empresa/unidade
- registrar material/produto
- informar lote
- informar pedido/nota/documento
- informar quantidade defeituosa
- descrever problema
- classificar severidade
- classificar categoria do defeito
- definir responsável interno
- anexar evidências iniciais

### 4.2 Módulo de contenção
Responsável pelas ações imediatas.

Funcionalidades:
- bloqueio
- segregação
- devolução
- retrabalho
- seleção
- uso sob concessão
- impacto no estoque
- impacto em produção
- impacto no cliente

### 4.3 Módulo de investigação
Responsável pela análise da causa raiz.

Funcionalidades:
- 5 porquês
- Ishikawa
- causa de ocorrência
- causa de não detecção
- conclusão de causa raiz
- equipe envolvida

### 4.4 Módulo de plano de ação
Responsável pelo tratamento estruturado.

Funcionalidades:
- ações de contenção
- ações corretivas
- ações preventivas
- responsável
- prazo
- status
- vínculo com causa raiz
- anexos por ação

### 4.5 Módulo de validação de eficácia
Responsável pelo encerramento técnico.

Funcionalidades:
- critério de validação
- data de verificação
- resultado
- parecer
- reabertura quando necessário

### 4.6 Módulo de comentários e colaboração
Funcionalidades:
- comentários internos
- observações operacionais
- histórico de conversas do caso

### 4.7 Módulo de auditoria
Funcionalidades:
- trilha de status
- log de alterações
- log de anexos
- log de ações críticas
- log de encerramento e reabertura

### 4.8 Módulo de dashboard e relatórios
Funcionalidades:
- ocorrências abertas
- ocorrências vencidas
- tempo médio de fechamento
- reincidência por fornecedor
- causas mais frequentes
- eficácia na primeira validação
- ranking por fornecedor
- exportação do relatório final

---

## 5. Workflow do processo

### 5.1 Status principal
- `draft`
- `open`
- `under-triage`
- `containment-defined`
- `under-investigation`
- `action-plan-approved`
- `in-progress`
- `pending-effectiveness-check`
- `closed`
- `cancelled`
- `reopened`

### 5.2 Status de interação com fornecedor
- `not-requested`
- `awaiting-supplier`
- `supplier-responded`
- `supplier-action-pending`
- `supplier-validated`
- `supplier-overdue`

### 5.3 Regras obrigatórias
- não encerrar sem validação de eficácia aprovada
- não aprovar plano sem causa raiz registrada
- não concluir ação sem responsável e prazo
- ocorrência encerrada pode ser reaberta
- anexos podem existir na ocorrência, ação e validação
- ações vencidas devem ser identificadas no dashboard

---

## 6. Modelo de domínio

### 6.1 Agregados principais
- `ExternalNonconformity`
- `ExternalNonconformityAction`
- `ExternalNonconformityRootCause`
- `ExternalNonconformityEffectivenessCheck`
- `ExternalNonconformityAttachment`

### 6.2 Entidades complementares
- `Supplier`
- `NonconformityComment`
- `NonconformityTeamMember`
- `NonconformityAuditEvent`

### 6.3 Value objects sugeridos
- `NonconformityCode`
- `SeverityLevel`
- `WorkflowStatus`
- `ActionType`
- `OccurrenceType`
- `Quantity`
- `Deadline`

---

## 7. Entidades e campos

### 7.1 `external_nonconformities`
Campos:
- id
- code
- company_unit
- supplier_id
- supplier_name_snapshot
- customer_name
- origin_type
- source_channel
- material_code
- material_description
- material_specification
- lot_number
- purchase_order
- invoice_number
- document_reference
- occurrence_date
- detection_date
- defective_quantity
- inspected_quantity
- uom
- severity
- priority
- occurrence_type
- defect_category
- recurrence_flag
- containment_required
- title
- problem_description
- business_impact
- customer_impact
- production_impact
- cost_estimate
- current_status
- supplier_status
- responsible_user_id
- opened_by_user_id
- due_date
- closed_at
- cancellation_reason
- created_at
- updated_at

### 7.2 `external_nc_root_causes`
Campos:
- id
- nonconformity_id
- analysis_method
- cause_dimension
- category
- why_level
- description
- is_root_cause
- created_by_user_id
- created_at

### 7.3 `external_nc_actions`
Campos:
- id
- nonconformity_id
- root_cause_id
- action_type
- title
- description
- responsible_user_id
- responsible_external_name
- responsible_external_email
- start_date
- due_date
- completed_at
- status
- verification_required
- effectiveness_due_date
- completion_notes
- created_by_user_id
- created_at
- updated_at

### 7.4 `external_nc_effectiveness_checks`
Campos:
- id
- nonconformity_id
- action_id
- checked_by_user_id
- checked_at
- criteria
- result
- notes
- next_action
- created_at

### 7.5 `external_nc_attachments`
Campos:
- id
- nonconformity_id
- action_id
- effectiveness_check_id
- file_name
- original_name
- mime_type
- size_bytes
- storage_provider
- storage_path
- checksum
- uploaded_by_user_id
- uploaded_at

### 7.6 `external_nc_comments`
Campos:
- id
- nonconformity_id
- comment_type
- content
- is_internal
- created_by_user_id
- created_at

### 7.7 `external_nc_team_members`
Campos:
- id
- nonconformity_id
- user_id
- role_in_case
- joined_at

### 7.8 `external_nc_audit_events`
Campos:
- id
- nonconformity_id
- event_type
- actor_user_id
- payload_json
- created_at

### 7.9 `external_nc_suppliers`
Campos:
- id
- code
- legal_name
- trade_name
- tax_id
- email
- phone
- active
- created_at
- updated_at

---

## 8. Modelagem PostgreSQL

### 8.1 Banco
Usar o banco já existente:

`postgres-plugins`

### 8.2 Schema
Sugestão:

`quality`

### 8.3 Tabelas
Criar:
- `quality.external_nc_suppliers`
- `quality.external_nonconformities`
- `quality.external_nc_root_causes`
- `quality.external_nc_actions`
- `quality.external_nc_effectiveness_checks`
- `quality.external_nc_attachments`
- `quality.external_nc_comments`
- `quality.external_nc_team_members`
- `quality.external_nc_audit_events`

### 8.4 Regras de modelagem
- PK em UUID
- índices por status, fornecedor, vencimento e data
- snapshots textuais de dados importantes
- timestamps em entidades relevantes
- anexos desacoplados do storage
- constraints coerentes com fluxo do domínio

### 8.5 Estratégia de migração
Definir e implementar uma estratégia de versionamento para o banco do plugin dentro da `api-delpi`, mantendo separação clara entre:
- migrations do contexto TOTVS
- migrations do contexto plugins

---

## 9. Backend dentro da `api-delpi`

### 9.1 Decisão
A `api-delpi` será o backend governado da aplicação, hospedando o novo módulo como contexto isolado.

### 9.2 Estrutura recomendada

```text
app/
  application/
    dto/
      external_nc/
    use_cases/
      external_nc/
  composition/
    external_nc_composer.py
  domain/
    entities/
      external_nc/
    ports/
      external_nc/
    services/
      external_nc/
  infrastructure/
    persistence/
      plugins/
        connection/
        repositories/
          external_nc/
  interface/
    http/
      routes/
        external_nc_routes.py
```

### 9.3 O que precisa ser criado
- conexão dedicada PostgreSQL para plugins
- base repository para plugins
- ports do domínio external_nc
- repositórios concretos do módulo
- DTOs de entrada e saída
- composers do módulo
- use cases do módulo
- rotas HTTP do módulo
- serialização das respostas
- auditoria do módulo

### 9.4 O que não deve ser feito
- não usar a `BaseRepository` do TOTVS para o plugin
- não acoplar regras do domínio à camada HTTP
- não misturar query SQL Server com query PostgreSQL

---

## 10. Datasource separado dentro da `api-delpi`

### 10.1 Variáveis de ambiente necessárias
Criar uma nova família de variáveis para o banco de plugins:

- `PLUGINS_DB_HOST`
- `PLUGINS_DB_PORT`
- `PLUGINS_DB_NAME`
- `PLUGINS_DB_USER`
- `PLUGINS_DB_PASSWORD`

### 10.2 Infraestrutura necessária
Criar algo equivalente a:

```text
app/infrastructure/persistence/plugins/
  plugin_postgres_connection.py
  plugin_base_repository.py
```

---

## 11. Rotas da API do módulo

### 11.1 Base path sugerido
Como o backend estará dentro da `api-delpi`, a base recomendada é:

`/apps/api-delpi/quality/external-nc`

### 11.2 Endpoints principais

#### Ocorrências
- `GET /apps/api-delpi/quality/external-nc/nonconformities`
- `POST /apps/api-delpi/quality/external-nc/nonconformities`
- `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}`
- `PATCH /apps/api-delpi/quality/external-nc/nonconformities/{id}`
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/transition`

#### Causa raiz
- `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/root-causes`
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/root-causes`

#### Ações
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/actions`
- `PATCH /apps/api-delpi/quality/external-nc/actions/{id}`
- `POST /apps/api-delpi/quality/external-nc/actions/{id}/complete`

#### Eficácia
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/effectiveness-checks`

#### Comentários
- `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/comments`
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/comments`

#### Anexos
- `POST /apps/api-delpi/quality/external-nc/nonconformities/{id}/attachments`
- `POST /apps/api-delpi/quality/external-nc/actions/{id}/attachments`

#### Dashboard
- `GET /apps/api-delpi/quality/external-nc/dashboard/summary`
- `GET /apps/api-delpi/quality/external-nc/dashboard/by-supplier`
- `GET /apps/api-delpi/quality/external-nc/dashboard/by-cause`
- `GET /apps/api-delpi/quality/external-nc/dashboard/overdue-actions`

#### Exportação
- `GET /apps/api-delpi/quality/external-nc/nonconformities/{id}/export`

---

## 12. Casos de uso do backend

Criar, no mínimo:

- `CreateExternalNonconformityUseCase`
- `ListExternalNonconformitiesUseCase`
- `GetExternalNonconformityDetailsUseCase`
- `UpdateExternalNonconformityUseCase`
- `TransitionExternalNonconformityStatusUseCase`
- `AddRootCauseUseCase`
- `CreateActionUseCase`
- `UpdateActionUseCase`
- `CompleteActionUseCase`
- `RegisterEffectivenessCheckUseCase`
- `UploadAttachmentUseCase`
- `AddCommentUseCase`
- `ExportNonconformityReportUseCase`
- `GetExternalNcDashboardUseCase`

---

## 13. Regras de domínio obrigatórias

- gerar código sequencial da ocorrência
- impedir encerramento sem eficácia aprovada
- impedir transições inválidas
- impedir ação sem prazo
- impedir ação sem responsável
- permitir reabertura com justificativa
- registrar evento de auditoria nas ações críticas
- persistir histórico de comentários
- permitir anexos em múltiplos níveis

---

## 14. Frontend do plugin

### 14.1 Projeto
Criar o plugin frontend em pasta dedicada, por exemplo:

`/plugins/quality-external-nc`

### 14.2 Tipo de plugin
- `type: microfrontend`
- `renderMode: embedded` inicialmente

### 14.3 Estrutura recomendada

```text
src/
  ui/
    pages/
    components/
  state/
    hooks/
    store/
  data/
    api/
    adapters/
    mappers/
  routes/
  bootstrap/
```

### 14.4 Telas obrigatórias
- `DashboardPage`
- `NonconformityListPage`
- `NonconformityCreatePage`
- `NonconformityDetailsPage`
- `ReportsPage`
- `SettingsPage`

### 14.5 Blocos da tela de detalhe
- cabeçalho da ocorrência
- dados do fornecedor
- impacto
- contenção
- causa raiz
- plano de ação
- anexos
- comentários
- validação de eficácia
- histórico

### 14.6 Regras de frontend
- sem regra de negócio na UI
- sem hardcode de permissão
- consumo de API via camada `data`
- separação clara entre view, estado e acesso a dados

---

## 15. Manifest do plugin

### 15.1 Responsabilidade do manifesto
Declarar:
- identidade do plugin
- tipo
- basePath
- entry frontend
- permissões
- rotas
- backend requerido

### 15.2 Campos obrigatórios
- `schemaVersion`
- `id`
- `name`
- `version`
- `type`
- `basePath`
- `permissions`
- `entry` para microfrontend
- `routes`

### 15.3 Estratégia do backend no manifesto
O backend será compartilhado com a `api-delpi`, então o manifesto deve refletir isso no bloco `backend`, apontando para a `api-delpi`, não para um serviço novo.

### 15.4 Permissões sugeridas
- `quality.external-nc.view`
- `quality.external-nc.create`
- `quality.external-nc.edit`
- `quality.external-nc.assign`
- `quality.external-nc.comment`
- `quality.external-nc.attach`
- `quality.external-nc.investigate`
- `quality.external-nc.approve-plan`
- `quality.external-nc.execute-action`
- `quality.external-nc.validate-effectiveness`
- `quality.external-nc.close`
- `quality.external-nc.reopen`
- `quality.external-nc.export`
- `quality.external-nc.dashboard.view`
- `quality.external-nc.admin`

### 15.5 Rotas do app
- `/apps/quality-external-nc/dashboard`
- `/apps/quality-external-nc/cases`
- `/apps/quality-external-nc/cases/new`
- `/apps/quality-external-nc/cases/:id`
- `/apps/quality-external-nc/reports`
- `/apps/quality-external-nc/settings`

---

## 16. Governança central

### 16.1 Registro do plugin
Registrar o manifesto na Core API.

### 16.2 Permissões
Criar e vincular permissões do módulo ao ecossistema RBAC.

### 16.3 Rotas
Publicar rotas do plugin para o menu dinâmico.

### 16.4 Fluxo esperado
- autenticação pelo ecossistema DELPI
- Core resolve apps e rotas do usuário
- plugin aparece no menu conforme permissão
- frontend consome backend dentro da `api-delpi`
- backend valida JWT e permissão antes de executar casos de uso

---

## 17. Integrações futuras

Planejar para evolução futura:

### 17.1 TOTVS
- fornecedor
- pedido de compra
- nota fiscal
- material
- lote
- custo

### 17.2 Google Sheets
- importação de modelos legados
- carga inicial de dados
- apoio a relatórios auxiliares

### 17.3 Notificações
- e-mail
- alertas internos
- websocket/socket.io quando fizer sentido

### 17.4 Exportação
- PDF do plano de ação
- Excel compatível com legado

---

## 18. Roadmap de implementação

### Visão geral
O desenvolvimento deve seguir uma abordagem incremental, com entregas curtas, validáveis e aderentes à arquitetura da DELPI Central. O roadmap abaixo organiza a construção da aplicação em fases técnicas e funcionais, reduzindo risco arquitetural e permitindo colocar valor em produção gradualmente.

---

### Fase 0 — Alinhamento e definição do produto
**Objetivo:** fechar o contrato funcional e técnico antes de iniciar código.

**Entregáveis:**
- definição oficial do nome do módulo
- definição do ID final do plugin
- definição dos perfis de acesso
- definição do workflow oficial
- definição dos campos obrigatórios da ocorrência
- definição do relatório final esperado
- validação da estratégia de uso da `api-delpi` como backend compartilhado
- validação da estratégia de persistência no `postgres-plugins`

**Dependências:**
- alinhamento entre qualidade, TI e arquitetura

**Critério de conclusão:**
- escopo funcional aprovado
- nomenclatura aprovada
- workflow aprovado
- arquitetura aprovada

---

### Fase 1 — Fundação técnica da solução
**Objetivo:** criar a base estrutural do plugin e do módulo backend.

**Entregáveis backend:**
- criação do contexto `external_nc` dentro da `api-delpi`
- estrutura de pastas em Clean Architecture
- criação do datasource PostgreSQL para plugins
- criação do `plugin_postgres_connection.py`
- criação do `plugin_base_repository.py`
- configuração de variáveis `PLUGINS_DB_*`
- inclusão do novo router no `main.py`
- healthcheck do módulo

**Entregáveis frontend:**
- criação do projeto frontend `quality-external-nc`
- bootstrap inicial do plugin
- configuração de build/publicação
- estrutura base de páginas, componentes, estado e data

**Entregáveis de governança:**
- rascunho inicial do `delpi.manifest.json`
- definição do `basePath`
- definição das permissões iniciais

**Critério de conclusão:**
- plugin frontend sobe localmente
- `api-delpi` sobe com o novo módulo sem quebrar os atuais
- conexão com `postgres-plugins` validada

---

### Fase 2 — Persistência e modelagem do domínio
**Objetivo:** materializar a base de dados e a camada de domínio.

**Entregáveis:**
- criação do schema `quality`
- migration inicial do módulo
- criação das tabelas principais
- criação dos índices e constraints
- criação das entidades de domínio
- criação dos ports do domínio
- criação dos repositórios concretos PostgreSQL
- criação da regra de geração do código sequencial da ocorrência

**Entidades prioritárias:**
- `ExternalNonconformity`
- `ExternalNonconformityAction`
- `ExternalNonconformityRootCause`
- `ExternalNonconformityEffectivenessCheck`
- `ExternalNonconformityAttachment`
- `NonconformityComment`
- `NonconformityAuditEvent`

**Critério de conclusão:**
- banco criado e versionado
- repositórios funcionando com testes básicos
- domínio conseguindo persistir e consultar uma ocorrência completa

---

### Fase 3 — MVP operacional
**Objetivo:** substituir a planilha no fluxo mínimo do dia a dia.

**Entregáveis backend:**
- endpoint de criação de ocorrência
- endpoint de listagem paginada
- endpoint de detalhe
- endpoint de atualização
- endpoint de comentários
- endpoint de anexos
- endpoint de transição básica de status

**Entregáveis frontend:**
- tela de listagem de ocorrências
- filtros por status, fornecedor, severidade e período
- tela de criação de ocorrência
- tela de detalhe da ocorrência
- upload de evidências
- histórico básico de comentários

**Critério de conclusão:**
- usuário consegue abrir, consultar e atualizar uma ocorrência real
- fluxo mínimo substitui a planilha em casos simples

---

### Fase 4 — Investigação e plano de ação
**Objetivo:** estruturar tecnicamente o tratamento da não conformidade.

**Entregáveis backend:**
- endpoints de causa raiz
- endpoints de ações
- endpoint de conclusão de ações
- regras de validação de prazo e responsável
- persistência de equipe da análise
- auditoria de eventos críticos

**Entregáveis frontend:**
- bloco de causa raiz
- bloco de ações
- cadastro de responsáveis
- gestão de prazo e status das ações
- timeline mais rica do caso

**Critério de conclusão:**
- ocorrência pode sair de triagem para investigação e plano formal
- plano de ação fica totalmente rastreável no sistema

---

### Fase 5 — Validação de eficácia e encerramento
**Objetivo:** fechar o ciclo da qualidade com regra corporativa.

**Entregáveis backend:**
- endpoint de validação de eficácia
- regra de bloqueio de encerramento sem eficácia aprovada
- suporte à reabertura com justificativa
- auditoria de encerramento e reabertura
- endpoint de exportação do relatório final

**Entregáveis frontend:**
- bloco de validação de eficácia
- ação de encerrar ocorrência
- ação de reabrir ocorrência
- visualização de parecer final
- exportação do caso

**Critério de conclusão:**
- sistema suporta o ciclo completo: abertura → investigação → ações → eficácia → encerramento

---

### Fase 6 — Dashboard e gestão
**Objetivo:** transformar o módulo em instrumento de gestão, não só operação.

**Entregáveis backend:**
- endpoint de resumo geral
- endpoint por fornecedor
- endpoint por causa
- endpoint de ações vencidas
- consultas otimizadas para indicadores

**Entregáveis frontend:**
- dashboard com KPIs principais
- visão por fornecedor
- visão por causa
- visão de vencimentos
- relatórios filtráveis

**KPIs iniciais:**
- abertas
- vencidas
- tempo médio de fechamento
- reincidência por fornecedor
- causas mais frequentes
- eficácia na primeira validação

**Critério de conclusão:**
- gestão consegue acompanhar o comportamento do processo sem depender de planilhas paralelas

---

### Fase 7 — Governança completa do plugin
**Objetivo:** concluir a integração plena com a DELPI Central.

**Entregáveis:**
- manifesto final validado pelo schema oficial
- registro do plugin na Core API
- cadastro das permissões
- cadastro das rotas
- validação do menu dinâmico
- testes por perfil de acesso
- revisão de segurança JWT/RBAC

**Critério de conclusão:**
- plugin visível no ecossistema oficial da DELPI Central
- acesso controlado corretamente por perfil

---

### Fase 8 — Integrações e evolução corporativa
**Objetivo:** reduzir retrabalho operacional e elevar maturidade do módulo.

**Entregáveis possíveis:**
- integração com TOTVS para fornecedor, pedido, nota e item
- integração com Google Sheets para importações legadas
- templates de plano de ação por empresa/cliente
- notificações por e-mail
- alertas internos
- custo estimado automatizado
- exportações padronizadas em PDF e Excel

**Critério de conclusão:**
- módulo deixa de ser apenas operacional e passa a compor o fluxo corporativo integrado

---

### Sequência recomendada de execução
1. Fase 0 — Alinhamento
2. Fase 1 — Fundação técnica
3. Fase 2 — Persistência e domínio
4. Fase 3 — MVP operacional
5. Fase 4 — Investigação e plano de ação
6. Fase 5 — Eficácia e encerramento
7. Fase 6 — Dashboard e gestão
8. Fase 7 — Governança completa
9. Fase 8 — Integrações e evolução

---

### Priorização prática
Se a meta for colocar valor rápido em uso, a melhor linha de corte é:
- **MVP 1:** fases 0 a 3
- **MVP 2:** fase 4
- **Release operacional completa:** fase 5
- **Release gerencial:** fase 6
- **Release corporativa:** fases 7 e 8

---

### Riscos principais a evitar
- misturar persistência do plugin com a infraestrutura TOTVS
- acoplar regra de negócio na rota HTTP
- construir a UI copiando a planilha em vez de modelar o processo
- deixar permissões genéricas demais
- não versionar corretamente o schema do `postgres-plugins`
- atrasar a auditoria das ações críticas

## 19. Checklist final do que é preciso desenvolver

### Infraestrutura
- [ ] configurar variáveis `PLUGINS_DB_*`
- [ ] implementar conexão com `postgres-plugins`
- [ ] definir estratégia de migrations

### Backend `api-delpi`
- [ ] criar contexto `external_nc`
- [ ] criar ports do domínio
- [ ] criar entidades
- [ ] criar DTOs
- [ ] criar use cases
- [ ] criar composer
- [ ] criar repositórios PostgreSQL
- [ ] criar router HTTP
- [ ] plugar router no `main.py`
- [ ] implementar auditoria
- [ ] implementar validações de domínio

### Banco de dados
- [ ] criar schema `quality`
- [ ] criar tabelas do domínio
- [ ] criar índices
- [ ] criar constraints
- [ ] criar migration inicial

### Frontend do plugin
- [ ] criar projeto `quality-external-nc`
- [ ] criar bootstrap do plugin
- [ ] criar rotas do app
- [ ] criar telas principais
- [ ] criar camada de API
- [ ] criar gerenciamento de estado
- [ ] implementar fluxos de cadastro, detalhe, ações e eficácia

### Governança DELPI Central
- [ ] criar `delpi.manifest.json`
- [ ] declarar permissões
- [ ] declarar rotas
- [ ] apontar backend compartilhado da `api-delpi`
- [ ] registrar plugin na Core
- [ ] validar menu dinâmico e acesso por papel

### Produto
- [ ] modelar workflow completo
- [ ] definir SLA e critérios de eficácia
- [ ] definir dashboard inicial
- [ ] definir padrão de exportação final

---

## 20. Conclusão executiva

A aplicação deve ser construída como **plugin oficial da DELPI Central no frontend**, com **backend governado dentro da `api-delpi`** e **persistência no `postgres-plugins`**, mantendo **isolamento real entre o contexto TOTVS e o novo contexto de qualidade**.

A solução correta não é criar outro backend neste momento, nem misturar o módulo novo à infraestrutura SQL Server existente. O caminho correto é:

- frontend do plugin independente
- módulo novo dentro da `api-delpi`
- datasource PostgreSQL dedicado
- manifesto oficial
- permissões granulares
- registro na Core
- evolução incremental por fases

Esse é o conjunto final de tudo que é preciso para desenvolver a aplicação completa.

