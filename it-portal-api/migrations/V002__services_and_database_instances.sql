-- Portal de TI — Etapa 2A (IT-PORTAL-INVENTORY-E2A).
-- Serviços/aplicações, instâncias de banco de dados e vínculos com servidores.
-- Migration aditiva: nenhuma tabela/coluna da V001 é removida e nenhum dado
-- existente é alterado. Nenhuma coluna guarda credenciais.

-- Auditoria: eventos de serviços e bancos nem sempre pertencem a um servidor.
-- `subject_ids` lista todos os recursos afetados pelo evento (ex.: serviço e
-- servidor de um vínculo), para que o histórico de cada um encontre o evento.
ALTER TABLE it_portal.audit_events ALTER COLUMN server_id DROP NOT NULL;
ALTER TABLE it_portal.audit_events
    ADD COLUMN subject_ids UUID[] NOT NULL DEFAULT '{}'::uuid[];
ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer'
    )
);
CREATE INDEX audit_events_subject_ids_idx
    ON it_portal.audit_events USING GIN (subject_ids);
CREATE INDEX audit_events_entity_idx
    ON it_portal.audit_events (entity_id, occurred_at DESC);

-- Serviço/aplicação lógica. A execução em um servidor (container, processo,
-- serviço do SO) é registrada em `service_hostings`, não aqui.
CREATE TABLE it_portal.services (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    description TEXT,
    service_kind VARCHAR(30) NOT NULL,
    service_type VARCHAR(30) NOT NULL,
    technology VARCHAR(120),
    environment VARCHAR(20) NOT NULL,
    unit_code VARCHAR(2) NOT NULL,
    port INT,
    criticality VARCHAR(20) NOT NULL,
    responsible VARCHAR(160) NOT NULL,
    administrative_status VARCHAR(30) NOT NULL,
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
    CONSTRAINT services_kind_chk CHECK (
        service_kind IN ('business_application', 'platform_service')
    ),
    CONSTRAINT services_type_chk CHECK (
        service_type IN (
            'web_application', 'api', 'identity_access', 'reverse_proxy', 'cache',
            'messaging', 'file_storage', 'scheduler', 'monitoring', 'erp', 'other'
        )
    ),
    CONSTRAINT services_environment_chk CHECK (
        environment IN ('production', 'staging', 'development')
    ),
    CONSTRAINT services_unit_code_chk CHECK (unit_code IN ('01', '02')),
    CONSTRAINT services_port_chk CHECK (port IS NULL OR port BETWEEN 1 AND 65535),
    CONSTRAINT services_criticality_chk CHECK (
        criticality IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT services_administrative_status_chk CHECK (
        administrative_status IN (
            'planned', 'in_operation', 'maintenance', 'decommissioning'
        )
    ),
    CONSTRAINT services_responsible_chk CHECK (length(btrim(responsible)) > 0),
    CONSTRAINT services_revision_chk CHECK (revision >= 1),
    CONSTRAINT services_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX services_active_identity_uq
    ON it_portal.services (unit_code, environment, lower(name))
    WHERE archived_at IS NULL;
CREATE INDEX services_listing_idx
    ON it_portal.services (archived_at, unit_code, environment, criticality);

-- Instância do serviço em um servidor (hospedagem). Remover o vínculo nunca
-- remove o serviço nem o servidor.
CREATE TABLE it_portal.service_hostings (
    id UUID PRIMARY KEY,
    service_id UUID NOT NULL REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    runtime VARCHAR(30) NOT NULL,
    instance_name VARCHAR(160),
    notes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT service_hostings_runtime_chk CHECK (
        runtime IN ('container', 'native_process', 'os_service', 'virtual_machine', 'other')
    ),
    CONSTRAINT service_hostings_pair_uq UNIQUE (service_id, server_id)
);

CREATE INDEX service_hostings_server_idx ON it_portal.service_hostings (server_id);

-- Instância de SGBD hospedada em um servidor do inventário.
CREATE TABLE it_portal.database_instances (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    dbms VARCHAR(30) NOT NULL,
    version VARCHAR(60),
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    port INT,
    environment VARCHAR(20) NOT NULL,
    purpose VARCHAR(160),
    criticality VARCHAR(20) NOT NULL,
    responsible VARCHAR(160) NOT NULL,
    administrative_status VARCHAR(30) NOT NULL,
    technical_notes TEXT,
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
    CONSTRAINT database_instances_dbms_chk CHECK (
        dbms IN (
            'postgresql', 'sql_server', 'mysql', 'mariadb', 'oracle', 'mongodb',
            'sqlite', 'other'
        )
    ),
    CONSTRAINT database_instances_port_chk CHECK (port IS NULL OR port BETWEEN 1 AND 65535),
    CONSTRAINT database_instances_environment_chk CHECK (
        environment IN ('production', 'staging', 'development')
    ),
    CONSTRAINT database_instances_criticality_chk CHECK (
        criticality IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT database_instances_administrative_status_chk CHECK (
        administrative_status IN (
            'planned', 'in_operation', 'maintenance', 'decommissioning'
        )
    ),
    CONSTRAINT database_instances_responsible_chk CHECK (length(btrim(responsible)) > 0),
    CONSTRAINT database_instances_revision_chk CHECK (revision >= 1),
    CONSTRAINT database_instances_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX database_instances_active_identity_uq
    ON it_portal.database_instances (server_id, lower(name))
    WHERE archived_at IS NULL;
CREATE INDEX database_instances_server_idx ON it_portal.database_instances (server_id);
CREATE INDEX database_instances_listing_idx
    ON it_portal.database_instances (archived_at, environment, criticality);

-- Serviço que consome uma instância de banco (sem dados de conexão).
CREATE TABLE it_portal.database_consumers (
    id UUID PRIMARY KEY,
    database_instance_id UUID NOT NULL
        REFERENCES it_portal.database_instances (id) ON DELETE RESTRICT,
    service_id UUID NOT NULL REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    notes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT database_consumers_pair_uq UNIQUE (database_instance_id, service_id)
);

CREATE INDEX database_consumers_service_idx ON it_portal.database_consumers (service_id);
