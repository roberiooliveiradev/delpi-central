BEGIN;

-- Additive journey presentation metadata for existing request types.
-- Does not alter transitions; WorkflowEngine ignores unknown keys.

UPDATE my_requests.request_types
SET
    workflow_definition = workflow_definition || jsonb_build_object(
        'journey',
        '{
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
            {"statuses": ["cancelled"], "stageId": "service", "progressPercent": 66, "outcome": "cancelled", "summary": "Solicitação cancelada"},
            {"statuses": ["rejected"], "stageId": "service", "progressPercent": 66, "outcome": "rejected", "summary": "Solicitação rejeitada"}
          ]
        }'::jsonb
    ),
    updated_at = NOW()
WHERE code = 'invoice-issuance'
  AND COALESCE(workflow_definition->'journey', 'null'::jsonb) = 'null'::jsonb;

UPDATE my_requests.request_types
SET
    workflow_definition = workflow_definition || jsonb_build_object(
        'journey',
        '{
          "stages": [
            {"id": "intake", "label": "Solicitação criada"},
            {"id": "service", "label": "Em atendimento"},
            {"id": "closure", "label": "Conclusão"}
          ],
          "statusMappings": [
            {"statuses": ["submitted"], "stageId": "intake", "progressPercent": 33, "outcome": "in_progress"},
            {"statuses": ["in_progress"], "stageId": "service", "progressPercent": 66, "outcome": "in_progress"},
            {"statuses": ["completed"], "stageId": "closure", "progressPercent": 100, "outcome": "succeeded"},
            {"statuses": ["cancelled"], "stageId": "intake", "progressPercent": 33, "outcome": "cancelled", "summary": "Solicitação cancelada"},
            {"statuses": ["rejected"], "stageId": "service", "progressPercent": 66, "outcome": "rejected", "summary": "Solicitação rejeitada"}
          ]
        }'::jsonb
    ),
    updated_at = NOW()
WHERE code = 'raw-material-creation'
  AND COALESCE(workflow_definition->'journey', 'null'::jsonb) = 'null'::jsonb;

COMMIT;
