-- Revisões versionadas de kaizens (versões/melhorias no tempo)
-- Combina snapshot JSONB (padrão PAC) + tipo de mudança semântico (padrão transformômetro)
-- + vigência temporal (ESPECIFICACAO-REVISOES.md) para cálculo retrospectivo do dashboard.

CREATE TABLE IF NOT EXISTS quality.kaizen_revisions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    kaizen_id UUID NOT NULL,
    revision_number INT NOT NULL,

    -- Semântica de versão (inspirada no transformômetro)
    change_type VARCHAR(30) NOT NULL DEFAULT 'melhoria',
    change_summary VARCHAR(500),
    change_reason TEXT,

    -- Vigência temporal
    effective_from DATE NOT NULL,
    effective_until DATE,

    -- Snapshot completo dos campos de negócio (JSONB)
    snapshot JSONB NOT NULL,
    snapshot_schema_version INT NOT NULL DEFAULT 1,

    created_by_user_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_kaizen_revisions_kaizen
        FOREIGN KEY (kaizen_id)
        REFERENCES quality.kaizens (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT uq_kaizen_revision_number UNIQUE (kaizen_id, revision_number),

    CONSTRAINT ck_kaizen_revision_change_type CHECK (
        change_type IN (
            'baseline', 'implantacao', 'melhoria', 'correcao', 'descontinuacao', 'restauracao'
        )
    ),

    CONSTRAINT ck_kaizen_revision_dates CHECK (
        effective_until IS NULL OR effective_until >= effective_from
    )
);

CREATE INDEX IF NOT EXISTS ix_kaizen_revisions_kaizen_effective
    ON quality.kaizen_revisions (kaizen_id, effective_from, effective_until);

ALTER TABLE quality.kaizens
    ADD COLUMN IF NOT EXISTS current_revision_number INT NOT NULL DEFAULT 0;

-- Backfill: revisão 1 para kaizens já existentes (snapshot = estado atual)
INSERT INTO quality.kaizen_revisions (
    kaizen_id,
    revision_number,
    change_type,
    change_summary,
    effective_from,
    effective_until,
    snapshot,
    created_by_user_id,
    created_at
)
SELECT
    k.id,
    1,
    CASE WHEN k.status = 'implantado' THEN 'implantacao' ELSE 'baseline' END,
    'Revisão inicial (backfill do cadastro existente)',
    COALESCE(k.date_implemented, k.created_at::date),
    NULL,
    jsonb_build_object(
        'branch_code', k.branch_code,
        'title', k.title,
        'accountable', k.accountable,
        'sector', k.sector,
        'investment', k.investment,
        'savings_type', k.savings_type,
        'seconds_per_occurrence', k.seconds_per_occurrence,
        'occurrences_per_day', k.occurrences_per_day,
        'hourly_cost', k.hourly_cost,
        'quantity_saved_per_day', k.quantity_saved_per_day,
        'unit_material_cost', k.unit_material_cost,
        'fixed_daily_savings', k.fixed_daily_savings,
        'daily_savings', k.daily_savings,
        'annual_savings', k.annual_savings,
        'status', k.status,
        'date_implemented', k.date_implemented,
        'date_discontinued', k.date_discontinued,
        'notes', k.notes
    ),
    COALESCE(k.created_by_user_id, 'system'),
    k.created_at
FROM quality.kaizens k
WHERE NOT EXISTS (
    SELECT 1 FROM quality.kaizen_revisions r WHERE r.kaizen_id = k.id
);

UPDATE quality.kaizens k
   SET current_revision_number = 1
 WHERE current_revision_number = 0
   AND EXISTS (SELECT 1 FROM quality.kaizen_revisions r WHERE r.kaizen_id = k.id);
