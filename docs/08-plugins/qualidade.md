# Minha DELPI — Plugin de Qualidade / External NC

> **Arquivo:** `docs/08-plugins/qualidade.md`  
> **Status:** especificação oficial consolidada em documentação  
> **Produto:** Minha DELPI  
> **Escopo:** plugin de qualidade para não conformidades externas

---

## 1. Objetivo

O plugin de **Qualidade / External NC** tem como objetivo substituir o processo baseado em planilhas por um módulo oficial da Minha DELPI para controle de não conformidades externas.

O módulo deve cobrir:

- registro estruturado de ocorrências;
- investigação de causa raiz;
- plano de ação;
- validação de eficácia;
- anexos e evidências;
- comentários;
- auditoria;
- dashboard;
- relatórios;
- governança por RBAC e manifesto oficial.

---

## 2. Decisão arquitetural

A solução deve ser composta por:

```text
frontend próprio do plugin
backend hospedado dentro da api-delpi
persistência no postgres-plugins
governança pela Core API
```

Não deve ser criado um backend separado neste momento.

O domínio backend será implementado como bounded context dentro da `api-delpi`.

---

## 3. Identidade sugerida

Nome técnico sugerido:

```text
quality-external-nc
```

Pasta frontend sugerida:

```text
plugins/quality-external-nc
```

Contexto backend sugerido:

```text
external_nc
```

Schema de banco sugerido:

```text
quality
```

Base pública do frontend:

```text
/apps/quality-external-nc
```

Base da API operacional:

```text
/apps/api-delpi/quality/external-nc
```

---

## 4. Tipo de plugin

Tipo:

```text
microfrontend
```

Renderização inicial sugerida:

```text
embedded
```

Também pode evoluir para `federated`, desde que siga o padrão oficial de microfrontends.

---

## 5. Princípios obrigatórios

1. Não misturar domínio do plugin com domínio TOTVS.
2. Não reutilizar BaseRepository atual do TOTVS/SQL Server para persistência do módulo.
3. Criar datasource PostgreSQL separado dentro da `api-delpi`.
4. Seguir Clean Architecture no backend.
5. Seguir separação `ui / state / data` no frontend.
6. Aplicar permissões granulares por recurso e ação.
7. Registrar o plugin por manifesto oficial.
8. Manter auditoria de ações críticas.
9. Centralizar autenticação e autorização no padrão da plataforma.
10. Tratar o módulo como produto corporativo, não como planilha digitalizada.

---

## 6. Escopo funcional

### 6.1 Cadastro e triagem

Funcionalidades:

- registrar fornecedor;
- registrar empresa/unidade;
- registrar material/produto;
- informar lote;
- informar pedido/nota/documento;
- informar quantidade defeituosa;
- descrever problema;
- classificar severidade;
- classificar categoria do defeito;
- definir responsável interno;
- anexar evidências iniciais.

### 6.2 Contenção

Funcionalidades:

- bloqueio;
- segregação;
- devolução;
- retrabalho;
- seleção;
- uso sob concessão;
- impacto no estoque;
- impacto em produção;
- impacto no cliente.

### 6.3 Investigação

Funcionalidades:

- 5 porquês;
- Ishikawa;
- causa de ocorrência;
- causa de não detecção;
- conclusão de causa raiz;
- equipe envolvida.

### 6.4 Plano de ação

Funcionalidades:

- ações de contenção;
- ações corretivas;
- ações preventivas;
- responsável;
- prazo;
- status;
- vínculo com causa raiz;
- anexos por ação.

### 6.5 Validação de eficácia

Funcionalidades:

- critério de validação;
- data de verificação;
- resultado;
- parecer;
- reabertura quando necessário.

### 6.6 Comentários e colaboração

Funcionalidades:

- comentários internos;
- observações operacionais;
- histórico de conversas do caso.

### 6.7 Auditoria

Funcionalidades:

- trilha de status;
- log de alterações;
- log de anexos;
- log de ações críticas;
- log de encerramento e reabertura.

### 6.8 Dashboard e relatórios

Funcionalidades:

- ocorrências abertas;
- ocorrências vencidas;
- tempo médio de fechamento;
- reincidência por fornecedor;
- causas mais frequentes;
- eficácia na primeira validação;
- ranking por fornecedor;
- exportação do relatório final.

---

## 7. Workflow

Status principal:

```text
draft
open
under-triage
containment-defined
under-investigation
action-plan-approved
in-progress
pending-effectiveness-check
closed
cancelled
reopened
```

Status de interação com fornecedor:

```text
not-requested
awaiting-supplier
supplier-responded
supplier-action-pending
supplier-validated
supplier-overdue
```

---

## 8. Regras obrigatórias de domínio

- não encerrar sem validação de eficácia aprovada;
- não aprovar plano sem causa raiz registrada;
- não concluir ação sem responsável e prazo;
- ocorrência encerrada pode ser reaberta;
- anexos podem existir na ocorrência, ação e validação;
- ações vencidas devem ser identificadas no dashboard;
- ações críticas devem gerar auditoria.

---

## 9. Modelo de domínio

Agregados principais:

```text
ExternalNonconformity
ExternalNonconformityAction
ExternalNonconformityRootCause
ExternalNonconformityEffectivenessCheck
ExternalNonconformityAttachment
```

Entidades complementares:

```text
Supplier
NonconformityComment
NonconformityTeamMember
NonconformityAuditEvent
```

Value objects sugeridos:

```text
NonconformityCode
SeverityLevel
WorkflowStatus
ActionType
OccurrenceType
Quantity
Deadline
```

---

## 10. Persistência

Banco:

```text
postgres-plugins
```

Schema sugerido:

```text
quality
```

Tabelas sugeridas:

```text
quality.external_nc_suppliers
quality.external_nonconformities
quality.external_nc_root_causes
quality.external_nc_actions
quality.external_nc_effectiveness_checks
quality.external_nc_attachments
quality.external_nc_comments
quality.external_nc_team_members
quality.external_nc_audit_events
```

---

## 11. Backend na API DELPI

Estrutura recomendada:

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

Componentes necessários:

- conexão dedicada PostgreSQL para plugins;
- base repository para plugins;
- ports do domínio;
- repositórios concretos;
- DTOs;
- composers;
- use cases;
- rotas HTTP;
- serialização;
- auditoria.

---

## 12. Rotas da API

Base recomendada:

```text
/apps/api-delpi/quality/external-nc
```

### Ocorrências

```text
GET    /nonconformities
POST   /nonconformities
GET    /nonconformities/{id}
PATCH  /nonconformities/{id}
POST   /nonconformities/{id}/transition
```

### Causa raiz

```text
GET  /nonconformities/{id}/root-causes
POST /nonconformities/{id}/root-causes
```

### Ações

```text
POST  /nonconformities/{id}/actions
PATCH /actions/{id}
POST  /actions/{id}/complete
```

### Eficácia

```text
POST /nonconformities/{id}/effectiveness-checks
```

### Comentários

```text
GET  /nonconformities/{id}/comments
POST /nonconformities/{id}/comments
```

### Anexos

```text
POST /nonconformities/{id}/attachments
POST /actions/{id}/attachments
```

### Dashboard

```text
GET /dashboard/summary
GET /dashboard/by-supplier
GET /dashboard/by-cause
GET /dashboard/overdue-actions
```

### Exportação

```text
GET /nonconformities/{id}/export
```

---

## 13. Use cases mínimos

```text
CreateExternalNonconformityUseCase
ListExternalNonconformitiesUseCase
GetExternalNonconformityDetailsUseCase
UpdateExternalNonconformityUseCase
TransitionExternalNonconformityStatusUseCase
AddRootCauseUseCase
CreateActionUseCase
UpdateActionUseCase
CompleteActionUseCase
RegisterEffectivenessCheckUseCase
UploadAttachmentUseCase
AddCommentUseCase
ExportNonconformityReportUseCase
GetExternalNcDashboardUseCase
```

---

## 14. Frontend

Pasta sugerida:

```text
plugins/quality-external-nc
```

Estrutura recomendada:

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

Telas obrigatórias:

```text
DashboardPage
NonconformityListPage
NonconformityCreatePage
NonconformityDetailsPage
ReportsPage
SettingsPage
```

Blocos da tela de detalhe:

- cabeçalho da ocorrência;
- dados do fornecedor;
- impacto;
- contenção;
- causa raiz;
- plano de ação;
- anexos;
- comentários;
- validação de eficácia;
- histórico.

---

## 15. Permissões sugeridas

```text
quality.external-nc.view
quality.external-nc.create
quality.external-nc.edit
quality.external-nc.assign
quality.external-nc.comment
quality.external-nc.attach
quality.external-nc.investigate
quality.external-nc.approve-plan
quality.external-nc.execute-action
quality.external-nc.validate-effectiveness
quality.external-nc.close
quality.external-nc.reopen
quality.external-nc.export
quality.external-nc.dashboard.view
quality.external-nc.admin
```

Essas permissões devem ser declaradas no manifesto e atribuídas via RBAC na Core API.

---

## 16. Rotas do app

Rotas frontend sugeridas:

```text
/apps/quality-external-nc/dashboard
/apps/quality-external-nc/cases
/apps/quality-external-nc/cases/new
/apps/quality-external-nc/cases/:id
/apps/quality-external-nc/reports
/apps/quality-external-nc/settings
```

---

## 17. Manifesto esperado

Modelo conceitual:

```json
{
  "schemaVersion": "1.0.0",
  "id": "quality-external-nc",
  "name": "Não Conformidades Externas",
  "version": "1.0.0",
  "type": "microfrontend",
  "basePath": "/apps/quality-external-nc",
  "entry": "/apps/quality-external-nc/assets/remoteEntry.js",
  "permissions": [
    {
      "code": "quality.external-nc.view",
      "name": "Visualizar não conformidades externas",
      "module": "quality-external-nc"
    }
  ],
  "routes": [
    {
      "path": "/apps/quality-external-nc/dashboard",
      "label": "Qualidade",
      "permission": "quality.external-nc.view",
      "showInMenu": true,
      "order": 20
    }
  ],
  "backend": {
    "required": true,
    "validateJwt": true,
    "serviceName": "api-delpi",
    "baseUrl": "/apps/api-delpi/quality/external-nc"
  },
  "ui": {
    "renderMode": "embedded"
  }
}
```

O manifesto final deve ser validado pelo schema oficial antes do registro.

---

## 18. Integrações futuras

Possíveis integrações:

- TOTVS para fornecedor, pedido de compra, nota fiscal, material, lote e custo;
- Google Sheets para importações legadas;
- notificações por e-mail;
- alertas internos;
- WebSocket/Socket.IO quando fizer sentido;
- exportação em PDF e Excel.

---

## 19. Roadmap resumido

Fases recomendadas:

```text
0. Alinhamento e definição do produto
1. Fundação técnica
2. Persistência e modelagem do domínio
3. MVP operacional
4. Investigação e plano de ação
5. Validação de eficácia e encerramento
6. Dashboard e gestão
7. Governança completa do plugin
8. Integrações e evolução corporativa
```

Corte de valor sugerido:

```text
MVP 1: fases 0 a 3
MVP 2: fase 4
Release operacional completa: fase 5
Release gerencial: fase 6
Release corporativa: fases 7 e 8
```

---

## 20. Checklist final

### Infraestrutura

- [ ] Configurar `PLUGINS_DB_*`.
- [ ] Implementar conexão com `postgres-plugins`.
- [ ] Definir estratégia de migrations.

### Backend

- [ ] Criar contexto `external_nc`.
- [ ] Criar ports.
- [ ] Criar entidades.
- [ ] Criar DTOs.
- [ ] Criar use cases.
- [ ] Criar composer.
- [ ] Criar repositories PostgreSQL.
- [ ] Criar router HTTP.
- [ ] Plugar router no `main.py`.
- [ ] Implementar auditoria.
- [ ] Implementar validações de domínio.

### Banco

- [ ] Criar schema `quality`.
- [ ] Criar tabelas.
- [ ] Criar índices.
- [ ] Criar constraints.
- [ ] Criar migration inicial.

### Frontend

- [ ] Criar projeto `quality-external-nc`.
- [ ] Criar bootstrap do plugin.
- [ ] Criar rotas do app.
- [ ] Criar telas principais.
- [ ] Criar camada de API.
- [ ] Criar gerenciamento de estado.
- [ ] Implementar fluxos principais.

### Governança

- [ ] Criar manifesto.
- [ ] Declarar permissões.
- [ ] Declarar rotas.
- [ ] Apontar backend compartilhado da `api-delpi`.
- [ ] Registrar plugin na Core API.
- [ ] Validar menu dinâmico e acesso por papel.

---

## 21. Pontos de atenção

1. O módulo deve ser plugin oficial da plataforma.
2. O backend fica dentro da `api-delpi`.
3. A persistência é no `postgres-plugins`.
4. Não misturar com infraestrutura TOTVS.
5. Não tratar como planilha digitalizada.
6. Usar permissões granulares.
7. Registrar por manifesto oficial.
8. Auditar ações críticas.
9. Evoluir incrementalmente.
10. Confirmar implementação real antes de marcar como concluído.

---

## Referências internas

```text
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/07-api-delpi/visao-geral-api-delpi.md
```
