-- V001 — BPMN Modeler schema
-- Padrão da plataforma: database compartilhado plugins_hub, schema dedicado
-- por contexto, owned por plugins_user (mesmo padrão de transformometro,
-- helpdesk, cipa etc.). Executado no startup da API via migrations_runner
-- com credenciais PLUGINS_DB_*.

BEGIN;

CREATE SCHEMA IF NOT EXISTS bpmn_modeler;

COMMENT ON SCHEMA bpmn_modeler IS
'Schema do plugin BPMN Modeler (Meu Modelador de Processos): modelos BPMN,
working copies, revisões imutáveis e controle de migrations.';

CREATE TABLE bpmn_modeler.models (
    id                  uuid PRIMARY KEY,
    display_name        varchar(120) NOT NULL,
    working_copy_xml    text NOT NULL,
    working_copy_sha256 char(64) NOT NULL,
    version             bigint NOT NULL CHECK (version >= 1),
    created_at          timestamptz NOT NULL,
    created_by          text NOT NULL,
    updated_at          timestamptz NOT NULL,
    updated_by          text NOT NULL,
    archived_at         timestamptz NULL,

    CHECK (btrim(display_name) <> '' AND char_length(display_name) <= 120),
    CHECK (octet_length(working_copy_xml) <= 10485760),
    CHECK (working_copy_sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX idx_models_list
    ON bpmn_modeler.models (archived_at, updated_at DESC);
CREATE INDEX idx_models_name_lower
    ON bpmn_modeler.models (lower(display_name));

CREATE TABLE bpmn_modeler.revisions (
    id               uuid PRIMARY KEY,
    model_id         uuid NOT NULL REFERENCES bpmn_modeler.models(id) ON DELETE RESTRICT,
    revision_number  integer NOT NULL CHECK (revision_number >= 1),
    artifact_xml     text NOT NULL,
    artifact_sha256  char(64) NOT NULL CHECK (artifact_sha256 ~ '^[0-9a-f]{64}$'),
    origin           varchar(16) NOT NULL CHECK (origin IN ('explicit', 'restore')),
    created_at       timestamptz NOT NULL,
    created_by       text NOT NULL,

    CHECK (octet_length(artifact_xml) <= 10485760),
    UNIQUE (model_id, revision_number)
);

CREATE INDEX idx_revisions_model
    ON bpmn_modeler.revisions (model_id, revision_number DESC);

COMMIT;
