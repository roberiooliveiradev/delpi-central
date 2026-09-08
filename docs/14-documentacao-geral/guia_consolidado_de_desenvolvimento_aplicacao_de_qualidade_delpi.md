# Guia Consolidado de Desenvolvimento — Aplicação de Qualidade DELPI

## 1. Propósito do documento

Este documento consolida a visão funcional, arquitetural e técnica da futura **Aplicação de Qualidade da DELPI**, servindo como **guia oficial de desenvolvimento** para implementação do produto.

O objetivo é orientar a construção de uma solução corporativa para:

- inspeções de qualidade internas
- não conformidades internas
- não conformidades externas
- plano de ação
- investigação de causa raiz
- validação de eficácia
- anexos, histórico e auditoria
- indicadores e relatórios

Este material deve ser tratado como base de referência para:

- modelagem de domínio
- estruturação do backend
- construção do frontend
- desenho do banco de dados
- governança do plugin
- definição do roadmap de implementação

---

## 2. Visão executiva da solução

### 2.1 Problema atual

Hoje parte relevante do processo de qualidade é controlada por planilhas.

No cenário descrito, existem ao menos dois fluxos relevantes:

1. **Não conformidade externa**
   - problemas ligados a fornecedor, cliente, devolução, resposta externa, plano de ação formal e contenção externa

2. **Inspeção e não conformidade interna**
   - inspeções de ordens de produção e produtos
   - registro de defeitos encontrados
   - tratamento interno de problemas detectados na produção ou inspeção

Esse modelo baseado em planilhas gera limitações importantes:
- baixa rastreabilidade
- risco de perda de histórico
- dificuldade de auditoria
- pouca padronização do processo
- dificuldade para consolidar indicadores
- pouca integração com o ecossistema DELPI Central

### 2.2 Decisão de produto

A recomendação final é **não criar duas aplicações independentes**.

A melhor solução é construir **um produto único de qualidade**, com múltiplos fluxos especializados.

### 2.3 Nome sugerido do produto

**Quality Hub DELPI**

ou, tecnicamente:

**`quality-nc`**

### 2.4 Estrutura funcional do produto

O produto deve ser composto por três grandes blocos:

1. **Inspeções Internas de Qualidade**
2. **Não Conformidades Internas**
3. **Não Conformidades Externas**

Esses blocos compartilham infraestrutura e governança, mas não devem ser confundidos como um único processo operacional.

---

## 3. Decisão arquitetural final

### 3.1 Estrutura da solução

A aplicação será construída como:

- **frontend próprio em formato de plugin da DELPI Central**
- **backend governado dentro da `api-delpi`**
- **persistência no banco `postgres-plugins`**
- **registro oficial via manifesto e Core API**
- **autorização por RBAC no padrão DELPI Central**

### 3.2 O que isso significa na prática

#### Frontend
Será um plugin real da plataforma, com rotas próprias sob `/apps/<plugin>`.

#### Backend
Não será criado um backend novo agora. O domínio será implementado como um novo conjunto de bounded contexts dentro da `api-delpi`.

#### Banco
A persistência da aplicação ficará no `postgres-plugins`, separado do banco do TOTVS e separado da infraestrutura SQL Server já usada pela `api-delpi`.

### 3.3 Regra estrutural obrigatória

A aplicação **não pode reutilizar a `BaseRepository` atual do TOTVS** para a persistência do novo domínio.

Será obrigatória a criação de uma infraestrutura separada para PostgreSQL do contexto plugins.

---

## 4. Princípios obrigatórios de construção

1. **Não misturar o contexto de qualidade com o contexto TOTVS**.
2. **Não misturar SQL Server e PostgreSQL no mesmo repository base**.
3. **Seguir Clean Architecture no backend**.
4. **Seguir separação UI / state / data no frontend**.
5. **Aplicar permissões granulares por recurso e ação**.
6. **Modelar o processo, não reproduzir a planilha visualmente**.
7. **Manter auditoria forte em ações críticas**.
8. **Tratar inspeção como evento operacional e NC como evento de gestão**.
9. **Construir núcleo compartilhado entre NC interna e externa, com especializações separadas**.
10. **Evoluir de forma incremental por fases**.

---

## 5. Visão de módulos do produto

## 5.1 Módulo de Inspeções Internas

Responsável por registrar inspeções de qualidade sobre ordens de produção, itens e lotes.

### Funções esperadas
- registrar inspeção
- vincular ordem de produção
- vincular item/produto
- vincular lote
- registrar quantidade produzida
- registrar quantidade inspecionada
- registrar quantidade rejeitada
- registrar operação/posto/etapa
- registrar critérios ou checklist
- registrar defeitos encontrados
- definir resultado da inspeção
- gerar não conformidade interna quando aplicável

## 5.2 Módulo de Não Conformidades Internas

Responsável por tratar problemas detectados internamente.

### Funções esperadas
- abrir NC manualmente
- abrir NC a partir de inspeção
- registrar produto/OP/lote/setor
- registrar defeito
- registrar contenção interna
- registrar disposição do material
- registrar causa raiz
- registrar ações corretivas e preventivas
- registrar eficácia
- encerrar ou reabrir o caso

## 5.3 Módulo de Não Conformidades Externas

Responsável por problemas ligados a fornecedor, cliente ou interface externa.

### Funções esperadas
- abrir ocorrência externa
- registrar fornecedor
- registrar cliente, quando aplicável
- registrar item, lote, pedido, NF, documento
- registrar contenção externa
- controlar retorno do fornecedor
- investigar causa raiz
- gerir plano de ação
- validar eficácia
- emitir relatório final

## 5.4 Módulo de Plano de Ação

Compartilhado entre NC interna e externa.

### Funções esperadas
- cadastrar ações
- classificar tipo da ação
- definir responsável
- definir prazo
- controlar status
- vincular ação a causa raiz
- anexar evidência
- concluir ação

## 5.5 Módulo de Eficácia

Compartilhado.

### Funções esperadas
- registrar critério de validação
- registrar data de verificação
- registrar parecer
- marcar eficaz / ineficaz
- gerar reabertura quando necessário

## 5.6 Módulo de Auditoria e Histórico

Compartilhado.

### Funções esperadas
- log de transição de status
- log de edição relevante
- log de anexos
- log de encerramento e reabertura
- comentários e histórico narrativo

## 5.7 Módulo de Dashboard e Relatórios

Compartilhado.

### Funções esperadas
- indicadores por fluxo
- indicadores consolidados
- filtros por período
- relatórios por fornecedor
- relatórios por item
- relatórios por causa
- relatórios por defeito
- exportação PDF e Excel

---

## 6. Diferença conceitual entre inspeção, NC interna e NC externa

## 6.1 Inspeção interna

A inspeção é um **evento operacional**.

Ela representa o ato de verificar um item, lote, OP ou processo.

### Exemplo
Um inspetor avalia 100 peças de uma ordem de produção e identifica que 12 estão fora de especificação.

Nesse caso:
- a inspeção é o evento primário
- a não conformidade pode ser consequência desse evento

## 6.2 Não conformidade interna

É um **evento de gestão da qualidade** originado por falha interna detectada em inspeção, processo, retrabalho, montagem, teste ou outra etapa interna.

### Exemplo
Um defeito dimensional recorrente em produção gera uma NC interna para investigação, correção e prevenção.

## 6.3 Não conformidade externa

É um **evento de gestão da qualidade com interface externa**, normalmente envolvendo fornecedor, cliente ou documento externo.

### Exemplo
Fornecedor entrega lote com material fora de especificação e é necessário registrar ocorrência, contenção, resposta e plano de ação.

## 6.4 Regra de modelagem essencial

**Inspeção não é igual a não conformidade.**

A aplicação deve modelar isso explicitamente.

---

## 7. Estratégia de produto recomendada

A aplicação deve ser construída como um único produto, com um núcleo compartilhado e três fluxos principais:

- inspeções
- NC interna
- NC externa

### 7.1 Benefícios dessa decisão
- reaproveitamento de infraestrutura
- padronização do processo
- consolidação de indicadores
- governança única
- menor duplicação de código
- melhor escalabilidade do produto

### 7.2 O que não deve ser feito
- criar uma aplicação separada para cada fluxo agora
- fundir inspeção e NC como se fossem a mesma coisa
- construir a solução como simples substituição visual das planilhas

---

## 8. Estrutura técnica recomendada do backend

O backend será implementado dentro da `api-delpi`.

## 8.1 Bounded contexts sugeridos

- `inspections`
- `internal_nc`
- `external_nc`
- `shared_quality`

## 8.2 Estrutura de diretórios sugerida

```text
app/
  application/
    dto/
      inspections/
      internal_nc/
      external_nc/
      shared_quality/
    use_cases/
      inspections/
      internal_nc/
      external_nc/
      shared_quality/
  domain/
    entities/
      inspections/
      internal_nc/
      external_nc/
      shared_quality/
    ports/
      inspections/
      internal_nc/
      external_nc/
      shared_quality/
    services/
      inspections/
      internal_nc/
      external_nc/
      shared_quality/
    value_objects/
      shared_quality/
  infrastructure/
    persistence/
      plugins/
        connection/
        repositories/
          inspections/
          internal_nc/
          external_nc/
          shared_quality/
    storage/
      attachments/
    logging/
    auth/
  composition/
    inspections_composer.py
    internal_nc_composer.py
    external_nc_composer.py
    shared_quality_composer.py
  interface/
    http/
      routes/
        quality_inspection_routes.py
        internal_nc_routes.py
        external_nc_routes.py
```

---

## 9. Núcleo compartilhado do domínio

O sistema deve ter um núcleo compartilhado entre NC interna e NC externa.

## 9.1 Entidades compartilhadas
- `NonconformityAction`
- `NonconformityAttachment`
- `NonconformityComment`
- `NonconformityEffectivenessCheck`
- `NonconformityAuditEvent`
- `RootCause`

## 9.2 Objetos de valor compartilhados
- `NonconformityCode`
- `SeverityLevel`
- `PriorityLevel`
- `WorkflowStatus`
- `ActionType`
- `DefectCategory`
- `Deadline`
- `Quantity`

## 9.3 Serviços compartilhados
- geração de código sequencial
- serviço de auditoria
- serviço de transição de status
- serviço de anexos
- serviço de exportação

---

## 10. Domínio de inspeções internas

## 10.1 Entidade principal

### `QualityInspection`

Campos sugeridos:
- id
- code
- inspection_date
- inspector_user_id
- shift
- production_order
- item_code
- item_description
- lot_number
- operation_code
- operation_description
- work_center
- quantity_produced
- quantity_inspected
- quantity_approved
- quantity_rejected
- inspection_type
- inspection_origin
- result_status
- notes
- created_at
- updated_at

## 10.2 Entidades auxiliares

### `QualityInspectionCriterion`
- id
- inspection_id
- criterion_code
- criterion_description
- expected_value
- measured_value
- result
- notes

### `QualityInspectionDefect`
- id
- inspection_id
- defect_code
- defect_description
- defect_category
- defective_quantity
- severity
- location_or_stage
- notes

### `QualityInspectionAttachment`
- id
- inspection_id
- file metadata

## 10.3 Regras do módulo de inspeção
- deve permitir múltiplos defeitos por inspeção
- deve permitir múltiplos critérios avaliados
- deve permitir anexos
- deve permitir gerar NC interna a partir da inspeção
- deve permitir histórico completo da inspeção

---

## 11. Domínio de NC interna

## 11.1 Entidade principal

### `InternalNonconformity`

Campos sugeridos:
- id
- code
- source_type
- source_inspection_id nullable
- production_order
- item_code
- item_description
- lot_number
- sector
- operation_code
- operation_description
- defect_category
- defect_description
- detected_by_user_id
- detection_date
- defective_quantity
- inspected_quantity
- severity
- priority
- current_status
- containment_action_summary
- disposition_type
- immediate_cause_notes
- root_cause_summary
- responsible_user_id
- due_date
- closed_at
- created_at
- updated_at

## 11.2 Disposições possíveis
- retrabalho
- sucata
- segregação
- liberação condicional
- reinspeção
- devolução interna

## 11.3 Regras do módulo de NC interna
- pode nascer de inspeção ou abertura manual
- deve registrar vínculo com OP/item/lote
- deve permitir contenção interna
- deve permitir causa raiz
- deve permitir ações corretivas e preventivas
- deve permitir validação de eficácia
- deve permitir encerramento e reabertura

---

## 12. Domínio de NC externa

## 12.1 Entidade principal

### `ExternalNonconformity`

Campos sugeridos:
- id
- code
- supplier_id
- supplier_name_snapshot
- customer_name nullable
- company_unit
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

## 12.2 Regras do módulo de NC externa
- deve permitir fornecedor
- deve controlar comunicação e resposta externa
- deve permitir contenção externa
- deve permitir causa raiz
- deve permitir plano de ação
- deve permitir validação de eficácia
- deve permitir encerramento formal

---

## 13. Modelo de ações, causa raiz, eficácia e auditoria

## 13.1 `RootCause`
Campos:
- id
- nc_type
- nc_id
- analysis_method
- cause_dimension
- category
- why_level
- description
- is_root_cause
- created_by_user_id
- created_at

## 13.2 `NonconformityAction`
Campos:
- id
- nc_type
- nc_id
- root_cause_id nullable
- action_type
- title
- description
- responsible_user_id nullable
- responsible_external_name nullable
- responsible_external_email nullable
- start_date
- due_date
- completed_at nullable
- status
- verification_required
- effectiveness_due_date nullable
- completion_notes
- created_by_user_id
- created_at
- updated_at

## 13.3 `NonconformityEffectivenessCheck`
Campos:
- id
- nc_type
- nc_id
- action_id nullable
- checked_by_user_id
- checked_at
- criteria
- result
- notes
- next_action
- created_at

## 13.4 `NonconformityAttachment`
Campos:
- id
- nc_type nullable
- nc_id nullable
- inspection_id nullable
- action_id nullable
- effectiveness_check_id nullable
- file_name
- original_name
- mime_type
- size_bytes
- storage_provider
- storage_path
- checksum
- uploaded_by_user_id
- uploaded_at

## 13.5 `NonconformityComment`
Campos:
- id
- nc_type
- nc_id
- comment_type
- content
- is_internal
- created_by_user_id
- created_at

## 13.6 `NonconformityAuditEvent`
Campos:
- id
- entity_type
- entity_id
- event_type
- actor_user_id
- payload_json
- created_at

---

## 14. Estratégia de banco de dados

## 14.1 Banco
Usar o banco já existente:

`postgres-plugins`

## 14.2 Schema recomendado

`quality`

## 14.3 Tabelas sugeridas

### Inspeções
- `quality.inspections`
- `quality.inspection_criteria`
- `quality.inspection_defects`
- `quality.inspection_attachments`

### NC interna
- `quality.internal_nonconformities`

### NC externa
- `quality.external_nonconformities`
- `quality.external_nc_suppliers`

### Compartilhadas
- `quality.nc_root_causes`
- `quality.nc_actions`
- `quality.nc_effectiveness_checks`
- `quality.nc_attachments`
- `quality.nc_comments`
- `quality.nc_audit_events`
- `quality.nc_team_members`

## 14.4 Princípios de modelagem
- PK em UUID
- índices por status, data e responsável
- índices específicos por fornecedor, OP, item e lote
- timestamps em entidades principais
- uso de snapshots textuais quando necessário
- separação entre tabelas de inspeção e tabelas de NC

## 14.5 Estratégia de migrations
A `api-delpi` deve possuir estratégia versionada para o contexto plugins, separada logicamente do contexto TOTVS.

---

## 15. Datasource e persistência dentro da `api-delpi`

## 15.1 O que precisa ser criado

```text
app/infrastructure/persistence/plugins/
  plugin_postgres_connection.py
  plugin_base_repository.py
```

## 15.2 Variáveis de ambiente necessárias
- `PLUGINS_DB_HOST`
- `PLUGINS_DB_PORT`
- `PLUGINS_DB_NAME`
- `PLUGINS_DB_USER`
- `PLUGINS_DB_PASSWORD`

## 15.3 Regra obrigatória
A `BaseRepository` atual do TOTVS/SQL Server não deve ser usada por este produto.

---

## 16. Casos de uso principais

## 16.1 Inspeções
- `CreateInspectionUseCase`
- `ListInspectionsUseCase`
- `GetInspectionDetailsUseCase`
- `UpdateInspectionUseCase`
- `RegisterInspectionDefectUseCase`
- `AttachInspectionEvidenceUseCase`
- `GenerateInternalNcFromInspectionUseCase`

## 16.2 NC interna
- `CreateInternalNonconformityUseCase`
- `ListInternalNonconformitiesUseCase`
- `GetInternalNonconformityDetailsUseCase`
- `UpdateInternalNonconformityUseCase`
- `TransitionInternalNcStatusUseCase`
- `AddInternalNcRootCauseUseCase`
- `CreateInternalNcActionUseCase`
- `CompleteInternalNcActionUseCase`
- `RegisterInternalNcEffectivenessCheckUseCase`
- `CloseInternalNcUseCase`
- `ReopenInternalNcUseCase`

## 16.3 NC externa
- `CreateExternalNonconformityUseCase`
- `ListExternalNonconformitiesUseCase`
- `GetExternalNonconformityDetailsUseCase`
- `UpdateExternalNonconformityUseCase`
- `TransitionExternalNcStatusUseCase`
- `AddExternalNcRootCauseUseCase`
- `CreateExternalNcActionUseCase`
- `CompleteExternalNcActionUseCase`
- `RegisterExternalNcEffectivenessCheckUseCase`
- `CloseExternalNcUseCase`
- `ReopenExternalNcUseCase`

## 16.4 Compartilhados
- `UploadAttachmentUseCase`
- `AddCommentUseCase`
- `ExportQualityCaseUseCase`
- `GetQualityDashboardUseCase`
- `GenerateQualitySequentialCodeUseCase`

---

## 17. Regras de domínio obrigatórias

### Compartilhadas
- gerar código sequencial por tipo
- impedir transições inválidas
- registrar auditoria em toda ação crítica
- permitir anexos em múltiplos níveis
- permitir comentários com rastreabilidade

### Inspeções
- permitir registrar múltiplos defeitos
- permitir gerar NC interna automaticamente quando houver rejeição
- permitir inspeção sem gerar NC, quando necessário

### NC interna
- impedir encerramento sem eficácia aprovada
- exigir vínculo operacional mínimo com item, defeito e contexto
- permitir origem manual ou derivada de inspeção

### NC externa
- impedir encerramento sem eficácia aprovada
- exigir fornecedor ou origem externa equivalente
- permitir controle de status do fornecedor

---

## 18. API do backend

Como o backend ficará dentro da `api-delpi`, a base sugerida é:

`/apps/api-delpi/quality`

## 18.1 Rotas de inspeções
- `GET /apps/api-delpi/quality/inspections`
- `POST /apps/api-delpi/quality/inspections`
- `GET /apps/api-delpi/quality/inspections/{id}`
- `PATCH /apps/api-delpi/quality/inspections/{id}`
- `POST /apps/api-delpi/quality/inspections/{id}/defects`
- `POST /apps/api-delpi/quality/inspections/{id}/attachments`
- `POST /apps/api-delpi/quality/inspections/{id}/generate-internal-nc`

## 18.2 Rotas de NC interna
- `GET /apps/api-delpi/quality/internal-nc`
- `POST /apps/api-delpi/quality/internal-nc`
- `GET /apps/api-delpi/quality/internal-nc/{id}`
- `PATCH /apps/api-delpi/quality/internal-nc/{id}`
- `POST /apps/api-delpi/quality/internal-nc/{id}/transition`
- `POST /apps/api-delpi/quality/internal-nc/{id}/root-causes`
- `POST /apps/api-delpi/quality/internal-nc/{id}/actions`
- `POST /apps/api-delpi/quality/internal-nc/actions/{id}/complete`
- `POST /apps/api-delpi/quality/internal-nc/{id}/effectiveness-checks`
- `POST /apps/api-delpi/quality/internal-nc/{id}/attachments`
- `GET /apps/api-delpi/quality/internal-nc/{id}/export`

## 18.3 Rotas de NC externa
- `GET /apps/api-delpi/quality/external-nc`
- `POST /apps/api-delpi/quality/external-nc`
- `GET /apps/api-delpi/quality/external-nc/{id}`
- `PATCH /apps/api-delpi/quality/external-nc/{id}`
- `POST /apps/api-delpi/quality/external-nc/{id}/transition`
- `POST /apps/api-delpi/quality/external-nc/{id}/root-causes`
- `POST /apps/api-delpi/quality/external-nc/{id}/actions`
- `POST /apps/api-delpi/quality/external-nc/actions/{id}/complete`
- `POST /apps/api-delpi/quality/external-nc/{id}/effectiveness-checks`
- `POST /apps/api-delpi/quality/external-nc/{id}/attachments`
- `GET /apps/api-delpi/quality/external-nc/{id}/export`

## 18.4 Rotas compartilhadas
- `POST /apps/api-delpi/quality/comments`
- `POST /apps/api-delpi/quality/attachments`
- `GET /apps/api-delpi/quality/dashboard/summary`
- `GET /apps/api-delpi/quality/dashboard/internal-nc`
- `GET /apps/api-delpi/quality/dashboard/external-nc`
- `GET /apps/api-delpi/quality/dashboard/inspections`
- `GET /apps/api-delpi/quality/dashboard/by-defect`
- `GET /apps/api-delpi/quality/dashboard/by-cause`

---

## 19. Estrutura do frontend do plugin

## 19.1 Nome sugerido
`quality-nc`

## 19.2 Rotas do plugin
- `/apps/quality-nc/dashboard`
- `/apps/quality-nc/inspections`
- `/apps/quality-nc/inspections/new`
- `/apps/quality-nc/inspections/:id`
- `/apps/quality-nc/internal-nc`
- `/apps/quality-nc/internal-nc/new`
- `/apps/quality-nc/internal-nc/:id`
- `/apps/quality-nc/external-nc`
- `/apps/quality-nc/external-nc/new`
- `/apps/quality-nc/external-nc/:id`
- `/apps/quality-nc/reports`
- `/apps/quality-nc/settings`

## 19.3 Estrutura recomendada

```text
src/
  ui/
    pages/
      dashboard/
      inspections/
      internal_nc/
      external_nc/
      reports/
      settings/
    components/
      shared/
      inspections/
      internal_nc/
      external_nc/
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

## 19.4 Telas obrigatórias

### Dashboard
- KPIs consolidados
- KPIs por fluxo
- ações vencidas
- principais defeitos
- principais causas

### Inspeções
- lista de inspeções
- cadastro de inspeção
- detalhe da inspeção
- registro de critérios
- registro de defeitos
- ação para gerar NC interna

### NC Interna
- lista
- cadastro
- detalhe
- causa raiz
- ações
- anexos
- comentários
- eficácia
- histórico

### NC Externa
- lista
- cadastro
- detalhe
- causa raiz
- ações
- anexos
- comentários
- eficácia
- histórico
- status do fornecedor

### Relatórios
- filtros por período
- filtros por tipo
- filtros por fornecedor, item, defeito, status
- exportações

### Configurações
- catálogos auxiliares
- parâmetros do módulo
- templates

---

## 20. Manifest do plugin

## 20.1 Tipo
`microfrontend`

## 20.2 ID sugerido
`quality-nc`

## 20.3 Base path
`/apps/quality-nc`

## 20.4 O manifesto deve declarar
- identidade do plugin
- versão
- tipo
- entry
- basePath
- permissions
- routes
- backend requerido

## 20.5 Estratégia de backend no manifesto
O backend é compartilhado com a `api-delpi`, então o bloco `backend` deve apontar para a `api-delpi`, não para um serviço novo.

## 20.6 Permissões sugeridas

### Inspeções
- `quality.inspections.view`
- `quality.inspections.create`
- `quality.inspections.edit`
- `quality.inspections.approve`
- `quality.inspections.generate-internal-nc`

### NC interna
- `quality.internal-nc.view`
- `quality.internal-nc.create`
- `quality.internal-nc.edit`
- `quality.internal-nc.assign`
- `quality.internal-nc.comment`
- `quality.internal-nc.attach`
- `quality.internal-nc.investigate`
- `quality.internal-nc.approve-plan`
- `quality.internal-nc.execute-action`
- `quality.internal-nc.validate-effectiveness`
- `quality.internal-nc.close`
- `quality.internal-nc.reopen`
- `quality.internal-nc.export`

### NC externa
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

### Dashboard e administração
- `quality.nc.dashboard.view`
- `quality.nc.admin`

---

## 21. Perfis sugeridos de acesso

### Inspetor de qualidade
- inspeções: criar, editar, visualizar
- gerar NC interna
- visualizar NC relacionadas

### Analista da qualidade
- acesso total operacional a NC interna e externa
- investigação
- ações
- eficácia
- relatórios

### Gestor da qualidade
- aprovar plano
- encerrar
- reabrir
- dashboard
- relatórios gerenciais

### Compras / interface externa
- visualizar NC externa
- comentar
- acompanhar tratativa com fornecedor

### Administrador do módulo
- administrar parâmetros, catálogos, templates e permissões operacionais do módulo

---

## 22. Dashboard e indicadores sugeridos

## 22.1 Inspeções
- total de inspeções por período
- taxa de aprovação
- taxa de rejeição
- defeitos mais frequentes
- rejeição por item
- rejeição por operação

## 22.2 NC interna
- abertas
- vencidas
- tempo médio de fechamento
- principais defeitos
- principais causas
- reincidência por item
- reincidência por setor

## 22.3 NC externa
- abertas
- vencidas
- tempo médio de resposta do fornecedor
- tempo médio de fechamento
- reincidência por fornecedor
- principais causas
- principais impactos

## 22.4 Consolidados
- total de NCs internas e externas
- eficácia na primeira validação
- backlog por responsável
- aging por status
- ações vencidas

---

## 23. Exportações e relatórios

A aplicação deve suportar, ao longo da evolução:

- relatório de inspeção
- relatório de NC interna
- relatório de NC externa
- plano de ação consolidado
- parecer final
- exportação PDF
- exportação Excel compatível com legado

---

## 24. Integrações futuras

## 24.1 TOTVS
- ordem de produção
- item/produto
- lote
- fornecedor
- pedido de compra
- nota fiscal
- custos

## 24.2 Google Sheets
- importação histórica
- carga inicial de planilhas legadas
- apoio transitório em relatórios

## 24.3 Notificações
- e-mail
- alertas internos
- websocket/socket.io se fizer sentido

---

## 25. Roadmap consolidado

## Fase 0 — Alinhamento
- nome final do produto
- definição final do escopo
- workflow validado
- aprovação da arquitetura

## Fase 1 — Fundação técnica
- criar plugin frontend
- criar contexts no backend
- criar datasource do `postgres-plugins`
- criar base repository do plugins DB
- criar manifesto inicial

## Fase 2 — Persistência e domínio
- migrations
- entidades
- ports
- repositórios
- código sequencial

## Fase 3 — Módulo de inspeções
- cadastro de inspeção
- detalhe de inspeção
- defeitos
- anexos
- geração de NC interna

## Fase 4 — Módulo de NC interna
- cadastro
- detalhe
- causa raiz
- ações
- eficácia
- encerramento

## Fase 5 — Módulo de NC externa
- cadastro
- detalhe
- causa raiz
- ações
- eficácia
- encerramento
- controle do fornecedor

## Fase 6 — Dashboard e relatórios
- KPIs
- relatórios filtráveis
- exportações

## Fase 7 — Governança completa
- manifesto final
- registro na Core
- permissões
- rotas
- testes de acesso

## Fase 8 — Integrações corporativas
- TOTVS
- Google Sheets
- notificações
- automações futuras

---

## 26. Checklist final de desenvolvimento

## Infraestrutura
- [ ] configurar `PLUGINS_DB_*`
- [ ] implementar conexão com `postgres-plugins`
- [ ] definir estratégia de migrations

## Backend
- [ ] criar contextos `inspections`, `internal_nc`, `external_nc`
- [ ] criar infraestrutura PostgreSQL do plugins DB
- [ ] criar entidades
- [ ] criar DTOs
- [ ] criar use cases
- [ ] criar composers
- [ ] criar repositórios
- [ ] criar rotas HTTP
- [ ] plugar rotas no `main.py`
- [ ] implementar auditoria
- [ ] implementar validações de domínio

## Banco
- [ ] criar schema `quality`
- [ ] criar tabelas de inspeção
- [ ] criar tabelas de NC interna
- [ ] criar tabelas de NC externa
- [ ] criar tabelas compartilhadas
- [ ] criar índices e constraints
- [ ] criar migration inicial

## Frontend
- [ ] criar plugin `quality-nc`
- [ ] criar bootstrap
- [ ] criar rotas
- [ ] criar dashboard
- [ ] criar telas de inspeção
- [ ] criar telas de NC interna
- [ ] criar telas de NC externa
- [ ] criar camada de API
- [ ] criar gerenciamento de estado
- [ ] criar fluxos de anexos, comentários, ações e eficácia

## Governança
- [ ] criar `delpi.manifest.json`
- [ ] declarar permissões
- [ ] declarar rotas
- [ ] apontar backend compartilhado da `api-delpi`
- [ ] registrar plugin na Core
- [ ] validar menu dinâmico
- [ ] validar acesso por perfil

## Produto
- [ ] definir catálogos auxiliares
- [ ] definir critérios de eficácia
- [ ] definir templates de relatório
- [ ] definir indicadores iniciais
- [ ] definir estratégia de dados históricos

---

## 27. Conclusão final

A aplicação deve ser tratada como um **produto corporativo de qualidade da DELPI**, construído como plugin oficial da DELPI Central, com backend dentro da `api-delpi` e persistência no `postgres-plugins`.

A melhor arquitetura é:

- **um único produto**
- **três fluxos principais**: inspeções, NC interna, NC externa
- **núcleo compartilhado** para ações, eficácia, anexos, comentários e auditoria
- **separação clara entre eventos operacionais e eventos de gestão**
- **governança total por manifesto, RBAC e Core API**

Esse documento deve servir como base principal para o desenvolvimento da solução completa.

