BEGIN;

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
    'raw-material-creation',
    'Criação de Matéria-prima',
    'Solicitação schema-driven de cadastro de matéria-prima (MVP 3 campos).',
    'engineering',
    'package',
    TRUE,
    1,
    'schema_driven',
    'optional',
    '{
      "type": "object",
      "required": ["description", "unit"],
      "properties": {
        "description": {"type": "string", "minLength": 1, "title": "Descrição"},
        "unit": {"type": "string", "enum": ["UN", "KG", "M"], "title": "Unidade"},
        "notes": {"type": "string", "title": "Observações"}
      },
      "additionalProperties": false
    }'::jsonb,
    '{
      "notes": {"widget": "textarea"}
    }'::jsonb,
    '{"initialStatus": "submitted", "terminalStatuses": ["completed", "rejected", "cancelled"], "computedActions": [{"action": "view", "requires": {"ownershipOr": ["view_all", "process", "manage"]}}], "transitions": [{"action": "start", "from": ["submitted"], "to": "in_progress", "requires": {"permissions": ["process"]}, "assignSelf": true}, {"action": "complete", "from": ["in_progress"], "to": "completed", "requires": {"permissions": ["process"]}}, {"action": "reject", "from": ["in_progress"], "to": "rejected", "requires": {"permissions": ["process"]}}, {"action": "cancel", "from": ["submitted"], "to": "cancelled", "requires": {"permissions": ["create"], "ownership": true}}]}'::jsonb,
    '{"adapter": "none"}'::jsonb,
    'my-requests.raw-material-creation'
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
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
