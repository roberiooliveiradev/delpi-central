-- G2-S4-S1: identidade exclusiva por workstation; NENHUMA credencial em banco.
-- Somente reserva de client desabilitado no Keycloak. Nao habilita ingestao nem remoto.
CREATE TABLE it_portal.workstation_agent_identities (
    workstation_id UUID PRIMARY KEY REFERENCES it_portal.workstations(id) ON DELETE RESTRICT,
    client_id VARCHAR(100) NOT NULL UNIQUE,
    keycloak_client_uuid UUID UNIQUE,
    state VARCHAR(20) NOT NULL DEFAULT 'preparing',
    created_by_id UUID NOT NULL,
    created_by_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workstation_agent_identities_state_chk CHECK (state IN ('preparing', 'prepared', 'failed', 'revoked')),
    CONSTRAINT workstation_agent_identities_client_chk CHECK (client_id ~ '^itp-ws-[0-9a-f]{32}$'),
    CONSTRAINT workstation_agent_identities_uuid_chk CHECK (
        (state = 'prepared' AND keycloak_client_uuid IS NOT NULL) OR state <> 'prepared'
    )
);
CREATE INDEX workstation_agent_identities_state_idx ON it_portal.workstation_agent_identities(state, updated_at);

CREATE TABLE it_portal.workstation_agent_identity_events (
    id UUID PRIMARY KEY,
    workstation_id UUID NOT NULL REFERENCES it_portal.workstation_agent_identities(workstation_id) ON DELETE RESTRICT,
    actor_id UUID NOT NULL,
    actor_name VARCHAR(200) NOT NULL,
    event_type VARCHAR(35) NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT workstation_agent_identity_event_chk CHECK (
        event_type IN ('identity_reserved', 'identity_prepared', 'identity_prepare_failed')
    )
);
CREATE INDEX workstation_agent_identity_events_idx
    ON it_portal.workstation_agent_identity_events(workstation_id, occurred_at DESC);
COMMENT ON TABLE it_portal.workstation_agent_identities IS
    'G2-S4: Clients Keycloak desabilitados para preparacao de inventario Windows; nenhuma senha/token, nunca concede controle remoto.';
