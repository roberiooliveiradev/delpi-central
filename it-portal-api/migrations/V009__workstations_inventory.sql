-- Delpi Remote G1-API: inventario curado de computadores, sem canal remoto.
-- Migration imutavel; historico separado de servidores.
CREATE TABLE it_portal.workstations (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    hostname VARCHAR(253) NOT NULL,
    ip_address VARCHAR(45),
    unit_code VARCHAR(2) NOT NULL,
    device_kind VARCHAR(20) NOT NULL,
    department VARCHAR(120),
    location VARCHAR(160),
    responsible VARCHAR(160),
    operating_system VARCHAR(120),
    administrative_status VARCHAR(30) NOT NULL,
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
    CONSTRAINT workstations_name_chk CHECK (length(btrim(name)) > 0),
    CONSTRAINT workstations_unit_chk CHECK (unit_code IN ('01', '02')),
    CONSTRAINT workstations_kind_chk CHECK (device_kind IN ('desktop','notebook','mini_pc','workstation')),
    CONSTRAINT workstations_status_chk CHECK (
        administrative_status IN ('planned','in_operation','maintenance','decommissioning')
    ),
    CONSTRAINT workstations_revision_chk CHECK (revision >= 1),
    CONSTRAINT workstations_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL AND archived_by_name IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL AND archived_by_name IS NOT NULL)
    )
);

-- Cadastro ativo univoco por unidade e hostname, independente de IP mutavel.
CREATE UNIQUE INDEX workstations_active_identity_uq
    ON it_portal.workstations (unit_code, lower(hostname))
    WHERE archived_at IS NULL;
CREATE INDEX workstations_list_idx
    ON it_portal.workstations (archived_at, unit_code, device_kind, administrative_status);
CREATE INDEX workstations_updated_idx
    ON it_portal.workstations (updated_at DESC, seq DESC);

-- A audit_events ja permite server_id NULL desde V002. Nao atrelar estacoes
-- a servidores para conseguir auditar seu proprio ciclo de vida.
ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer',
        'network', 'server_network_link', 'integration', 'service_dependency',
        'host_service_preference', 'host_service_action', 'workstation'
    )
);
