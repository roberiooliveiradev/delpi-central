-- V004 — BPMN Modeler owner-scoped list index
-- A listagem de modelos passou a ser scoped por resource owner
-- (Model.created_by, P0 resource authorization). O índice existente
-- idx_models_list (archived_at, updated_at) não lidera por created_by,
-- então a query owner-scoped caía em seq scan + filter. Índice
-- composto cobre o predicado de igualdade por owner + filtro de
-- archive + ordenação default (updated_at DESC, id DESC).
-- Migration aditiva, up-only: V001–V003 permanecem imutáveis.

BEGIN;

CREATE INDEX idx_models_owner_list
    ON bpmn_modeler.models (created_by, archived_at, updated_at DESC, id DESC);

COMMIT;
