-- Portal de TI — Etapa 2B (IT-PORTAL-INVENTORY-E2B).
-- Redes, conectividade servidor↔rede, integrações e dependências operacionais.
-- Migration aditiva: nenhuma tabela/coluna da V001/V002 é removida e nenhum
-- dado existente é alterado. Nenhuma coluna guarda credenciais ou payloads.
--
-- Tipos de relacionamento do inventário (cada um com tabela própria e id estável):
--   hospedagem          → service_hostings (V002), database_instances.server_id (V002)
--   consumo             → database_consumers (V002), integrations (V003)
--   conectividade       → server_network_links (V003)
--   dependência operac. → service_dependencies (V003)

ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer',
        'network', 'server_network_link', 'integration', 'service_dependency'
    )
);

-- Rede lógica cadastrada manualmente (sem varredura). `network_scope` é a
-- classificação explícita: redes internas de runtime de containers não são
-- redes corporativas permanentes.
CREATE TABLE it_portal.networks (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    cidr VARCHAR(64) NOT NULL,
    vlan_id INT,
    gateway VARCHAR(64),
    unit_code VARCHAR(2) NOT NULL,
    location VARCHAR(160),
    purpose VARCHAR(160),
    environment VARCHAR(20) NOT NULL,
    zone VARCHAR(80),
    network_scope VARCHAR(30) NOT NULL,
    criticality VARCHAR(20) NOT NULL,
    responsible VARCHAR(160) NOT NULL,
    notes TEXT,
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
    CONSTRAINT networks_cidr_chk CHECK ((cidr::cidr) IS NOT NULL),
    CONSTRAINT networks_gateway_in_cidr_chk CHECK (
        gateway IS NULL OR (gateway::inet) <<= (cidr::cidr)
    ),
    CONSTRAINT networks_vlan_chk CHECK (vlan_id IS NULL OR vlan_id BETWEEN 1 AND 4094),
    CONSTRAINT networks_unit_code_chk CHECK (unit_code IN ('01', '02')),
    CONSTRAINT networks_environment_chk CHECK (
        environment IN ('production', 'staging', 'development')
    ),
    CONSTRAINT networks_scope_chk CHECK (
        network_scope IN ('corporate', 'container_runtime')
    ),
    CONSTRAINT networks_criticality_chk CHECK (
        criticality IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT networks_responsible_chk CHECK (length(btrim(responsible)) > 0),
    CONSTRAINT networks_revision_chk CHECK (revision >= 1),
    CONSTRAINT networks_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX networks_active_name_uq
    ON it_portal.networks (unit_code, lower(name))
    WHERE archived_at IS NULL;
-- Faixas de containers se repetem por host; só redes corporativas têm CIDR único.
CREATE UNIQUE INDEX networks_active_corporate_cidr_uq
    ON it_portal.networks (unit_code, cidr)
    WHERE archived_at IS NULL AND network_scope = 'corporate';
CREATE INDEX networks_listing_idx
    ON it_portal.networks (archived_at, unit_code, environment, criticality);

-- Conectividade: servidor presente em uma rede. O IP do servidor na rede é
-- validado contra o CIDR pela aplicação (sob lock da rede).
CREATE TABLE it_portal.server_network_links (
    id UUID PRIMARY KEY,
    server_id UUID NOT NULL REFERENCES it_portal.servers (id) ON DELETE RESTRICT,
    network_id UUID NOT NULL REFERENCES it_portal.networks (id) ON DELETE RESTRICT,
    ip_address VARCHAR(64),
    interface_name VARCHAR(60),
    notes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT server_network_links_ip_chk CHECK (ip_address IS NULL OR (ip_address::inet) IS NOT NULL),
    CONSTRAINT server_network_links_pair_uq UNIQUE (server_id, network_id)
);

CREATE INDEX server_network_links_network_idx ON it_portal.server_network_links (network_id);

-- Integração entre serviços cadastrados ou com um sistema externo nomeado
-- explicitamente (sem criar aplicação fictícia). Cada ponta é exatamente um:
-- serviço do inventário OU nome externo. Pelo menos uma ponta é interna.
CREATE TABLE it_portal.integrations (
    id UUID PRIMARY KEY,
    seq BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    name VARCHAR(120) NOT NULL,
    source_service_id UUID REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    source_external_name VARCHAR(160),
    target_service_id UUID REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    target_external_name VARCHAR(160),
    protocol VARCHAR(30) NOT NULL,
    direction VARCHAR(30) NOT NULL,
    purpose VARCHAR(160),
    criticality VARCHAR(20) NOT NULL,
    responsible VARCHAR(160) NOT NULL,
    administrative_status VARCHAR(30) NOT NULL,
    notes TEXT,
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
    CONSTRAINT integrations_source_one_chk CHECK (
        num_nonnulls(source_service_id, source_external_name) = 1
    ),
    CONSTRAINT integrations_target_one_chk CHECK (
        num_nonnulls(target_service_id, target_external_name) = 1
    ),
    CONSTRAINT integrations_one_internal_chk CHECK (
        source_service_id IS NOT NULL OR target_service_id IS NOT NULL
    ),
    CONSTRAINT integrations_not_self_chk CHECK (
        source_service_id IS NULL OR target_service_id IS NULL
        OR source_service_id <> target_service_id
    ),
    CONSTRAINT integrations_protocol_chk CHECK (
        protocol IN (
            'http_api', 'soap', 'grpc', 'smb', 'nfs', 'file_transfer', 'email_smtp',
            'ldap', 'message_queue', 'webhook', 'other'
        )
    ),
    CONSTRAINT integrations_direction_chk CHECK (
        direction IN ('source_to_target', 'bidirectional')
    ),
    CONSTRAINT integrations_criticality_chk CHECK (
        criticality IN ('low', 'medium', 'high', 'critical')
    ),
    CONSTRAINT integrations_administrative_status_chk CHECK (
        administrative_status IN (
            'planned', 'in_operation', 'maintenance', 'decommissioning'
        )
    ),
    CONSTRAINT integrations_responsible_chk CHECK (length(btrim(responsible)) > 0),
    CONSTRAINT integrations_revision_chk CHECK (revision >= 1),
    CONSTRAINT integrations_archive_consistency_chk CHECK (
        (archived_at IS NULL AND archived_by_id IS NULL)
        OR (archived_at IS NOT NULL AND archived_by_id IS NOT NULL)
    )
);

CREATE UNIQUE INDEX integrations_active_endpoints_uq
    ON it_portal.integrations (
        COALESCE(source_service_id::text, 'external:' || lower(source_external_name)),
        COALESCE(target_service_id::text, 'external:' || lower(target_external_name)),
        protocol
    )
    WHERE archived_at IS NULL;
CREATE INDEX integrations_source_idx ON it_portal.integrations (source_service_id);
CREATE INDEX integrations_target_idx ON it_portal.integrations (target_service_id);
CREATE INDEX integrations_listing_idx
    ON it_portal.integrations (archived_at, criticality, protocol);

-- Dependência operacional explícita: o serviço dependente precisa do serviço
-- requerido para operar. Não é presumida a partir de outros vínculos.
CREATE TABLE it_portal.service_dependencies (
    id UUID PRIMARY KEY,
    dependent_service_id UUID NOT NULL REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    required_service_id UUID NOT NULL REFERENCES it_portal.services (id) ON DELETE RESTRICT,
    notes VARCHAR(500),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT service_dependencies_not_self_chk CHECK (
        dependent_service_id <> required_service_id
    ),
    CONSTRAINT service_dependencies_pair_uq UNIQUE (dependent_service_id, required_service_id)
);

CREATE INDEX service_dependencies_required_idx
    ON it_portal.service_dependencies (required_service_id);
