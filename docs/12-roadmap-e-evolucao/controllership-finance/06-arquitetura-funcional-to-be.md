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
