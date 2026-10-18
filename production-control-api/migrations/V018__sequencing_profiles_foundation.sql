BEGIN;

-- V018 — Fundação das Regras de Sequenciamento por Centro de Trabalho.
--
-- Catálogo administrativo do PCP: perfis de critérios ordenados (ex.: data de
-- entrega do PA + agrupamento por cabo) vinculáveis a filial + centro de
-- trabalho. Nesta etapa a configuração é APENAS administrativa — nenhuma
-- tabela aqui altera a fila WORKING/PUBLISHED nem o motor de otimização.
--
-- Independência proposital:
--   * sem FK para machine_load_snapshots/publications: o perfil sobrevive a
--     refresh, nova geração e resequenciamentos;
--   * ON DELETE RESTRICT no vínculo e nas revisões: perfil com histórico ou
--     em uso não pode ser apagado silenciosamente;
--   * revision é o token de concorrência otimista (UPDATE ... WHERE revision).
--
-- Auditoria: sequencing_profile_revisions guarda o snapshot completo a cada
-- revisão; sequencing_profile_binding_events guarda bound/rebound/unbound.
-- Ambas são append-only e escritas na MESMA transação da mutação — sem write
-- principal, não existe evento.

CREATE TABLE IF NOT EXISTS production_control.sequencing_profiles (
    id           UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    name         VARCHAR(120) NOT NULL,
    description  TEXT         NULL,
    status       VARCHAR(20)  NOT NULL DEFAULT 'draft',
    revision     INTEGER      NOT NULL DEFAULT 1,
    criteria     JSONB        NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    created_by   VARCHAR(120) NULL,
    updated_at   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_by   VARCHAR(120) NULL,

    CONSTRAINT chk_pc_sequencing_profiles_status CHECK (
        status IN ('draft', 'active', 'archived')
    ),
    CONSTRAINT chk_pc_sequencing_profiles_revision CHECK (revision > 0),
    -- criteria é array não vazio de objetos {type, params} — a semântica dos
    -- tipos é validada no domínio; aqui só a forma estrutural.
    CONSTRAINT chk_pc_sequencing_profiles_criteria CHECK (
        jsonb_typeof(criteria) = 'array' AND jsonb_array_length(criteria) > 0
    )
);

COMMENT ON TABLE production_control.sequencing_profiles IS
    'Perfis de sequenciamento do PCP — catálogo administrativo. Não altera a fila: o motor consome estas regras apenas em etapas futuras.';

COMMENT ON COLUMN production_control.sequencing_profiles.revision IS
    'Token de concorrência otimista: updates exigem expected_revision igual à vigente; divergência = 409.';

CREATE TABLE IF NOT EXISTS production_control.sequencing_profile_revisions (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id  UUID        NOT NULL
        REFERENCES production_control.sequencing_profiles (id) ON DELETE RESTRICT,
    revision    INTEGER     NOT NULL,
    action      VARCHAR(20) NOT NULL,
    snapshot    JSONB       NOT NULL,
    actor       VARCHAR(120) NULL,
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_pc_sequencing_profile_revision UNIQUE (profile_id, revision),
    CONSTRAINT chk_pc_sequencing_profile_rev_action CHECK (
        action IN ('created', 'updated')
    )
);

COMMENT ON TABLE production_control.sequencing_profile_revisions IS
    'Histórico append-only: uma linha por revisão do perfil, com snapshot completo, ator e timestamp.';

CREATE INDEX IF NOT EXISTS idx_pc_sequencing_profile_revisions_profile
    ON production_control.sequencing_profile_revisions (profile_id, revision DESC);

CREATE TABLE IF NOT EXISTS production_control.sequencing_profile_bindings (
    branch       VARCHAR(2)  NOT NULL CHECK (branch IN ('01', '02')),
    work_center  VARCHAR(40) NOT NULL,
    profile_id   UUID        NOT NULL
        REFERENCES production_control.sequencing_profiles (id) ON DELETE RESTRICT,
    assigned_by  VARCHAR(120) NULL,
    assigned_at  TIMESTAMPTZ  NOT NULL DEFAULT NOW(),

    -- Identidade do vínculo é filial + CT — nunca o CT sozinho como chave
    -- global. Um CT pertence a no máximo um perfil; um perfil serve a vários
    -- CTs (vinculação explícita por linha).
    CONSTRAINT pk_pc_sequencing_profile_bindings PRIMARY KEY (branch, work_center)
);

COMMENT ON TABLE production_control.sequencing_profile_bindings IS
    'Vínculo perfil ↔ (filial, CT). Um perfil pode servir a vários CTs; cada CT tem no máximo um perfil.';

-- Consulta reversa: onde este perfil está vinculado.
CREATE INDEX IF NOT EXISTS idx_pc_sequencing_profile_bindings_profile
    ON production_control.sequencing_profile_bindings (profile_id);

CREATE TABLE IF NOT EXISTS production_control.sequencing_profile_binding_events (
    id                  UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    branch              VARCHAR(2)  NOT NULL,
    work_center         VARCHAR(40) NOT NULL,
    profile_id          UUID        NULL
        REFERENCES production_control.sequencing_profiles (id) ON DELETE RESTRICT,
    previous_profile_id UUID        NULL
        REFERENCES production_control.sequencing_profiles (id) ON DELETE RESTRICT,
    action              VARCHAR(20) NOT NULL,
    actor               VARCHAR(120) NULL,
    occurred_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_pc_sequencing_binding_event_action CHECK (
        action IN ('bound', 'rebound', 'unbound')
    )
);

COMMENT ON TABLE production_control.sequencing_profile_binding_events IS
    'Auditoria append-only das vinculações: bound/rebound/unbound com ator e timestamp.';

CREATE INDEX IF NOT EXISTS idx_pc_sequencing_binding_events_scope
    ON production_control.sequencing_profile_binding_events (
        branch, work_center, occurred_at DESC
    );

COMMIT;
