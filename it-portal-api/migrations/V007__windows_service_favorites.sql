-- #1583: favoritos compartilhados do inventario Windows SCM.
-- Entidade independente do coletor: os batches continuam atualizando somente host_services.
CREATE TABLE it_portal.host_service_preferences (
    id UUID PRIMARY KEY,
    server_id UUID NOT NULL,
    service_key VARCHAR(200) NOT NULL,
    is_favorite BOOLEAN NOT NULL DEFAULT false,
    criticality VARCHAR(12) NOT NULL DEFAULT 'normal'
        CHECK (criticality IN ('normal', 'high', 'critical')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_by_id UUID NOT NULL,
    updated_by_name VARCHAR(200) NOT NULL,
    CONSTRAINT host_service_preferences_unique UNIQUE (server_id, service_key),
    CONSTRAINT host_service_preferences_service_fk
        FOREIGN KEY (server_id, service_key)
        REFERENCES it_portal.host_services (server_id, service_key)
        ON DELETE RESTRICT
);

CREATE INDEX host_service_preferences_favorites_idx
    ON it_portal.host_service_preferences (server_id, service_key)
    WHERE is_favorite;

-- Auditoria do que foi marcado/classificado: identidade humana revalidada
-- pelo Core; nunca inclui comandos, caminhos ou credenciais do servidor.
ALTER TABLE it_portal.audit_events DROP CONSTRAINT audit_events_entity_type_chk;
ALTER TABLE it_portal.audit_events ADD CONSTRAINT audit_events_entity_type_chk CHECK (
    entity_type IN (
        'server', 'server_note', 'action_plan',
        'service', 'service_hosting', 'database_instance', 'database_consumer',
        'network', 'server_network_link', 'integration', 'service_dependency',
        'host_service_preference'
    )
);
