-- V003 — BPMN Modeler revision metadata
-- Campos opcionais de contexto do usuário na revisão (checkpoint
-- imutável): nome/observação escolhidos na criação e display name do
-- autor denormalizado (o subject uuid permanece em created_by).
-- Migration aditiva, up-only: V001/V002 permanecem imutáveis
-- (checksum enforcement).

BEGIN;

ALTER TABLE bpmn_modeler.revisions
    ADD COLUMN name varchar(120) NULL,
    ADD COLUMN description varchar(500) NULL,
    ADD COLUMN created_by_name text NULL;

ALTER TABLE bpmn_modeler.revisions
    ADD CONSTRAINT revisions_name_len
        CHECK (name IS NULL OR (btrim(name) <> '' AND char_length(name) <= 120)),
    ADD CONSTRAINT revisions_description_len
        CHECK (description IS NULL OR char_length(description) <= 500);

COMMIT;
