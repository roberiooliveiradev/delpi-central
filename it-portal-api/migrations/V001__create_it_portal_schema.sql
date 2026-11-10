-- Portal de TI — Etapa 1 (IT-PORTAL-MVP-E1).
-- Schema próprio `it_portal` no postgres-plugins; nenhum outro contexto
-- lê ou escreve estas tabelas.

CREATE SCHEMA IF NOT EXISTS it_portal;

CREATE TABLE it_portal.servers (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    hostname VARCHAR(253) NOT NULL,
    ip_address VARCHAR(45),
    unit_code VARCHAR(2) NOT NULL,
    location VARCHAR(160),
    environment VARCHAR(20) NOT NULL,
    server_type VARCHAR(20) NOT NULL,
    purpose VARCHAR(160),
    operating_system VARCHAR(120),
    criticality VARCHAR(20) NOT NULL,
    administrative_status VARCHAR(30) NOT NULL,
    responsible VARCHAR(160),
    description TEXT,
    revision INT NOT NULL DEFAULT 1,
    archived_at TIMESTAMPTZ,
    archived_by_id UUID,
    archived_by_name VARCHAR(200),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by_id UUID NOT NULL,
    updated_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT servers_unit_code_chk CHECK (unit_code IN ('01', '02')),
    CONSTRAINT servers_environment_chk CHECK (
        environment IN ('production', 'staging', 'development')
    ),
    CONSTRAINT servers_server_type_chk CHECK (
        server_type IN ('physical', 'virtual', 'cloud')
    ),
    CONSTRAINT servers_criticality_chk CHECK (
        criticality IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT servers_administrative_status_chk CHECK (
        administrative_status IN (
            'planned', 'in_operation', 'maintenance', 'decommissioning'
        )
    ),
    CONSTRAINT servers_revision_chk CHECK (revision >= 1),
    CONSTRAINT servers_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL)
    )
);

-- Identidade do servidor: hostname é único por unidade + ambiente entre os
-- cadastros ativos. Arquivados preservam o histórico sem bloquear recadastro.
CREATE UNIQUE INDEX servers_active_identity_uq
    ON it_portal.servers (unit_code, environment, lower(hostname))
    WHERE archived_at IS NULL;

CREATE INDEX servers_listing_idx
    ON it_portal.servers (archived_at, unit_code, environment, criticality);
CREATE INDEX servers_created_at_idx ON it_portal.servers (created_at DESC);

CREATE TABLE it_portal.server_notes (
    id UUID PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    body TEXT NOT NULL,
    author_id UUID NOT NULL,
    author_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT server_notes_body_chk CHECK (length(btrim(body)) > 0)
);

CREATE INDEX server_notes_server_idx
    ON it_portal.server_notes (server_id, created_at, id);

CREATE TABLE it_portal.action_plans (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    title VARCHAR(160) NOT NULL,
    description TEXT,
    responsible VARCHAR(160),
    priority VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    due_date DATE,
    completed_at TIMESTAMPTZ,
    revision INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by_id UUID NOT NULL,
    updated_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT action_plans_priority_chk CHECK (
        priority IN ('low', 'medium', 'high', 'urgent')
    ),
    CONSTRAINT action_plans_status_chk CHECK (
        status IN ('pending', 'in_progress', 'done', 'cancelled')
    ),
    CONSTRAINT action_plans_revision_chk CHECK (revision >= 1),
    CONSTRAINT action_plans_completion_chk CHECK (
        (status = 'done') = (completed_at IS NOT NULL)
    )
);

CREATE INDEX action_plans_server_idx
    ON it_portal.action_plans (server_id, created_at);
CREATE INDEX action_plans_open_due_idx
    ON it_portal.action_plans (status, due_date);

-- Trilha de auditoria do domínio: quem alterou o quê e quando.
CREATE TABLE it_portal.audit_events (
    id UUID PRIMARY KEY,
    entity_type VARCHAR(30) NOT NULL,
    entity_id UUID NOT NULL,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    event_type VARCHAR(40) NOT NULL,
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_id UUID NOT NULL,
    actor_name VARCHAR(200) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT audit_events_entity_type_chk CHECK (
        entity_type IN ('server', 'server_note', 'action_plan')
    )
);

CREATE INDEX audit_events_server_idx
    ON it_portal.audit_events (server_id, occurred_at DESC);
