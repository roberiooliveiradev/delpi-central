# 06 — Arquitetura Funcional TO-BE

## Superfícies

```text
Central de Fechamento
├── P1 Cockpit da Competência
├── P2 Checklist e Documentos
├── P3 Estoque e Conciliação
├── P4 Classificações e Pendências
├── P5 Pacote, Finalização e Envio
└── P6 Administração e Configuração
```

IA é transversal.

## Entidades conceituais

- ClosingCompetence
- ChecklistTemplate
- ChecklistTemplateVersion
- ChecklistItemDefinition
- MonthlyChecklistItem
- Evidence / Attachment
- Validation
- EvidenceSet
- Pendency
- Package
- PackageVersion
- PackageRecipient
- Clarification
- StructuralCorrectionRequest
- NotificationEvent

Isso não impõe schema físico.

## Snapshot

Na abertura da competência:
- capturar versão do template;
- materializar itens aplicáveis;
- preservar configuração;
- mudanças futuras no mestre não alteram a competência.

## Requirement type

### REQUIRED
Bloqueia quando aplicável e não satisfeito. Nunca N/A.

### CONDITIONAL
Quando aplicável, comporta-se como REQUIRED. Pode N/A quando a regra permitir, com justificativa.

### OPTIONAL
Ausência não bloqueia.

## Satisfaction rule

### ATTACHMENT_PRESENT
Presença pode satisfazer conforme regra.

### VALIDATION_REQUIRED

```text
ATTACHED → UNDER_REVIEW → ACCEPTED
```

ou:

```text
ATTACHED
→ UNDER_REVIEW
→ REJECTED
→ REPLACEMENT_REQUIRED
→ NEW_ATTACHMENT
→ UNDER_REVIEW
→ ACCEPTED
```

## Multi-anexo

### PER_ATTACHMENT
Cada arquivo independente.

### WHOLE_SET
Conjunto é unidade lógica. Nova composição exige revalidação, sem reupload total.

## Versionamento

Nunca sobrescrever evidência histórica.

```text
SET v1 = contrato v1 + swift v1 + comprovante v1 → REJECTED
SET v2 = contrato v1 + swift v2 + comprovante v1 → ACCEPTED
```

## Correção estrutural

Pré-execução:
- ACCESS edita opções permitidas.

Pós-execução:
- edição estrutural bloqueada;
- ACCESS solicita;
- MANAGE aprova/rejeita;
- aprovação cria nova revisão;
- evidências/validações anteriores preservadas;
- mudança de validade reabre revisão.

MANAGE pode autoaprovar, mas request e approval continuam auditados separadamente.

## ERP

V1 não assume escrita ERP para:
- sacramentação;
- classificação/CC.

Nova necessidade exige nova decisão de owner/arquitetura.


## Boundary de plataforma — Gate V2

Identidade técnica congelada:

```text
MFE  = plugins/controllership-finance
base = /apps/controllership-finance
BFF  = controllership-finance-api
API  = /apps/controllership-finance-api
```

Fluxo:

```text
MFE
→ controllership-finance-api
→ Core / api-delpi / strategic-indicators-api / demais owners
```

Nunca:

```text
browser → api-delpi
browser → Core
browser → strategic-indicators-api
browser → DB vizinho
```

## Owners canônicos

- Core: identidade, apps, effective permissions, RBAC, users, notification platform capability;
- api-delpi: SQL/regras canônicas TOTVS/Protheus;
- strategic-indicators-api: metas/indicadores estratégicos;
- controllership-finance-api: regras/estado próprios do produto + composição/adapters;
- plugin-ui: chrome/componentes reutilizáveis.

Experiência unificada não transfere ownership.

## Security boundary

```text
JWT
→ identity/context only

Core PermissionResolver
→ effective permissions

BFF
→ capability
AND resource_scope / ownership
AND business_rule
→ fail-closed
```

Somente:
- `controllership-finance.access`;
- `controllership-finance.manage`.

## Notification boundary

Core atual prova integração S2S de notificações.

```text
PORTAL BUSINESS EVENT
→ controllership-finance-api adapter
→ Core /integrations/notifications
→ Minha DELPI inbox/history
```

Isso não equivale a package delivery.

## P3 terminal boundary

Decisão E02:

```text
STOCK_CLOSED
= terminal no P3 Portal V1
```

Correções posteriores permanecem no owner/ERP.

## P5 delivery boundary

```text
PACKAGE_FINALIZED
→ [delivery owner/outcome DECISION_REQUIRED E04/T04]
→ PACKAGE_SENT
```

Não criar endpoint/canal/proof por preferência.
