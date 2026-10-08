BEGIN;

-- P1: tipo "Problema de Processo" — ocorrências de processo reportadas pelo
-- cockpit de produção, tratadas pelo dept. de Processos no Minhas Solicitações.
-- branch_scope=required: toda ocorrência pertence a uma filial.
-- form_schema intencionalmente permissivo: o snapshot de produção (P2) pode
-- evoluir sem nova migration a cada campo contextual.
INSERT INTO my_requests.request_types (
    code,
    name,
    description,
    category,
    icon,
    active,
    version,
    presentation_mode,
    branch_scope,
    form_schema,
    ui_schema,
    workflow_definition,
    destination_config,
    permission_prefix
) VALUES (
    'process-issue',
    'Problema de Processo',
    'Ocorrência de processo identificada durante a produção e encaminhada para análise e correção pelo departamento de Processos.',
    'engineering',
    'wrench',
    TRUE,
    1,
    'schema_driven',
    'required',
    '{"type": "object"}'::jsonb,
    '{}'::jsonb,
    '{
      "initialStatus": "submitted",
      "terminalStatuses": ["completed"],
      "computedActions": [
        {"action": "view", "requires": {"ownershipOr": ["view_all", "process", "manage"]}}
      ],
      "transitions": [
        {"action": "start", "from": ["submitted"], "to": "in_progress", "requires": {"permissionsAny": ["process", "manage"]}, "assignSelf": true},
        {"action": "complete", "from": ["in_progress"], "to": "completed", "requires": {"permissionsAny": ["process", "manage"]}}
      ],
      "journey": {
        "stages": [
          {"id": "intake", "label": "Solicitação criada"},
          {"id": "service", "label": "Em atendimento"},
          {"id": "closure", "label": "Conclusão"}
        ],
        "statusMappings": [
          {"statuses": ["submitted"], "stageId": "intake", "progressPercent": 33, "outcome": "in_progress"},
          {"statuses": ["in_progress"], "stageId": "service", "progressPercent": 66, "outcome": "in_progress"},
          {"statuses": ["completed"], "stageId": "closure", "progressPercent": 100, "outcome": "succeeded"}
        ]
      }
    }'::jsonb,
    '{"adapter": "none"}'::jsonb,
    'my-requests.process-issue'
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    category = EXCLUDED.category,
    icon = EXCLUDED.icon,
    form_schema = EXCLUDED.form_schema,
    ui_schema = EXCLUDED.ui_schema,
    workflow_definition = EXCLUDED.workflow_definition,
    destination_config = EXCLUDED.destination_config,
    presentation_mode = EXCLUDED.presentation_mode,
    branch_scope = EXCLUDED.branch_scope,
    permission_prefix = EXCLUDED.permission_prefix,
    active = TRUE,
    updated_at = NOW();

COMMIT;
