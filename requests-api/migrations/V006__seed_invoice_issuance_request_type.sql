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
    'invoice-issuance',
    'Emissão de Notas Fiscais',
    'Solicitação de emissão de NF com lookups TOTVS via api-delpi.',
    'fiscal',
    'file-text',
    TRUE,
    1,
    'specialized',
    'required',
    '{}'::jsonb,
    '{}'::jsonb,
    '{"initialStatus": "submitted", "terminalStatuses": ["completed", "cancelled", "rejected"], "statusAliases": {"submitted": "pending", "needs_information": "returned", "completed": "issued"}, "computedActions": [{"action": "view", "requires": {"ownershipOr": ["view_all", "process", "manage"]}}, {"action": "edit", "whenStatus": ["needs_information"], "requires": {"permissions": ["create"], "ownership": true}}], "transitions": [{"action": "start", "from": ["submitted"], "to": "in_progress", "requires": {"permissionsAny": ["process", "manage"]}, "assignSelf": true}, {"action": "return", "from": ["in_progress"], "to": "needs_information", "requires": {"permissionsAny": ["process", "manage"], "fields": ["return_reason"]}}, {"action": "resubmit", "from": ["needs_information"], "to": "submitted", "requires": {"permissions": ["create"], "ownership": true}}, {"action": "complete", "from": ["in_progress"], "to": "completed", "requires": {"permissionsAny": ["process", "manage"]}, "actionAlias": "issue"}, {"action": "cancel", "from": ["submitted", "in_progress", "needs_information"], "to": "cancelled", "requires": {"anyOf": [{"permissions": ["create"], "ownership": true, "from": ["submitted"]}, {"permissions": ["process"], "from": ["in_progress"]}, {"permissions": ["manage"]}], "fields": ["cancel_justification"]}}]}'::jsonb,
    '{"adapter": "api_delpi", "capabilities": ["search_parties", "search_products", "search_carriers", "list_open_sales_orders", "warehouse_01_balance"]}'::jsonb,
    'my-requests.invoice-issuance'
)
ON CONFLICT (code) DO UPDATE SET
    name = EXCLUDED.name,
    description = EXCLUDED.description,
    workflow_definition = EXCLUDED.workflow_definition,
    destination_config = EXCLUDED.destination_config,
    presentation_mode = EXCLUDED.presentation_mode,
    branch_scope = EXCLUDED.branch_scope,
    permission_prefix = EXCLUDED.permission_prefix,
    active = TRUE,
    updated_at = NOW();

COMMIT;
