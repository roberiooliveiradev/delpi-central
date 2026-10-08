BEGIN;

-- Tipo "Solicitação Diversa" — demandas gerais criadas pelo próprio usuário no
-- portal e tratadas pelo departamento de Processos no Minhas Solicitações.
-- branch_scope=none: demandas diversas não pertencem a uma filial; sem vínculo
-- a filial, todo processador enxerga a fila e qualquer usuário com
-- my-requests.general-request.create consegue abrir sem escopo de filial.
-- Workflow propositalmente flexível: concluir direto da entrada, pedir
-- complemento (needs_information) e cancelamento do próprio solicitante
-- enquanto aguarda atendimento.
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
    'general-request',
    'Solicitação Diversa',
    'Demanda geral direcionada ao departamento de Processos, criada pelo portal com título e descrição.',
    'general',
    'clipboard-plus',
    TRUE,
    1,
    'schema_driven',
    'none',
    '{
      "type": "object",
      "required": ["title", "description"],
      "properties": {
        "title": {"type": "string", "minLength": 3, "title": "Título"},
        "description": {"type": "string", "minLength": 10, "title": "Descrição"}
      },
      "additionalProperties": false
    }'::jsonb,
    '{
      "title": {"hint": "Resumo curto do que você precisa."},
      "description": {"widget": "textarea", "hint": "Descreva a demanda, o contexto e o resultado esperado."}
    }'::jsonb,
    '{
      "initialStatus": "submitted",
      "terminalStatuses": ["completed", "cancelled"],
      "computedActions": [
        {"action": "view", "requires": {"ownershipOr": ["view_all", "process", "manage"]}},
        {"action": "edit", "whenStatus": ["submitted"], "requires": {"permissions": ["create"], "ownership": true}}
      ],
      "transitions": [
        {"action": "start", "from": ["submitted"], "to": "in_progress", "requires": {"permissionsAny": ["process", "manage"]}, "assignSelf": true},
        {"action": "return", "from": ["in_progress"], "to": "needs_information", "requires": {"permissionsAny": ["process", "manage"], "fields": ["return_reason"]}},
        {"action": "resubmit", "from": ["needs_information"], "to": "submitted", "requires": {"permissions": ["create"], "ownership": true}},
        {"action": "complete", "from": ["submitted", "in_progress"], "to": "completed", "requires": {"permissionsAny": ["process", "manage"]}},
        {"action": "cancel", "from": ["submitted", "in_progress", "needs_information"], "to": "cancelled", "requires": {"anyOf": [{"permissions": ["create"], "ownership": true, "from": ["submitted"]}, {"permissions": ["process"], "from": ["in_progress", "needs_information"]}, {"permissions": ["manage"]}], "fields": ["cancel_justification"]}}
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
          {"statuses": ["needs_information"], "stageId": "service", "progressPercent": 66, "outcome": "waiting_requester", "summary": "Aguardando informação do solicitante"},
          {"statuses": ["completed"], "stageId": "closure", "progressPercent": 100, "outcome": "succeeded"},
          {"statuses": ["cancelled"], "stageId": "closure", "progressPercent": 100, "outcome": "cancelled", "summary": "Solicitação cancelada"}
        ]
      }
    }'::jsonb,
    '{"adapter": "none"}'::jsonb,
    'my-requests.general-request'
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
