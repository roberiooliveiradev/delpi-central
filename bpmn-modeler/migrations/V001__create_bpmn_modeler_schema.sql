-- V001 — BPMN Modeler schema (frozen in SECURITY-PERSISTENCE-RUNTIME-SPEC-FREEZE §4.3/4.4)
-- Executed by the migration role bpmn_modeler_admin (database owner).

CREATE TABLE public.models (
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
    ON public.models (archived_at, updated_at DESC);
CREATE INDEX idx_models_name_lower
    ON public.models (lower(display_name));

CREATE TABLE public.revisions (
    id               uuid PRIMARY KEY,
    model_id         uuid NOT NULL REFERENCES public.models(id) ON DELETE RESTRICT,
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
    ON public.revisions (model_id, revision_number DESC);

-- Least-privilege grants for the runtime role (opt-in per object; no
-- ALTER DEFAULT PRIVILEGES). schema_migrations receives no grants.
GRANT SELECT, INSERT, UPDATE ON TABLE public.models    TO bpmn_modeler_app;
GRANT SELECT, INSERT         ON TABLE public.revisions TO bpmn_modeler_app;
