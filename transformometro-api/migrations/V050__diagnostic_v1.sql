-- Transformômetro — Diagnostic V1 aggregate persistence.
-- Aggregate root: transformometro.diagnostics. Child tables mirror the
-- domain kernel (tm_app/domain/diagnostic) 1:1; no sub-entity repositories.
-- Revision is a contextual anchor: soft-deleted revisions never remove
-- historical diagnostics, so the FK intentionally uses NO ACTION (default).

BEGIN;

CREATE TABLE IF NOT EXISTS transformometro.diagnostics (
    diagnostic_id UUID PRIMARY KEY,
    revision_id UUID NOT NULL
        REFERENCES transformometro.revisoes (revisao_id),
    problem_statement TEXT NOT NULL,
    version INTEGER NOT NULL,
    provenance_origin VARCHAR(16),
    provenance_detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostics_problem_statement_not_blank
        CHECK (btrim(problem_statement) <> ''),
    CONSTRAINT diagnostics_version_positive CHECK (version >= 1),
    CONSTRAINT diagnostics_provenance_origin
        CHECK (provenance_origin IN ('USER', 'TEO'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostics_revision
    ON transformometro.diagnostics (revision_id);

CREATE TABLE IF NOT EXISTS transformometro.diagnostic_findings (
    finding_id UUID PRIMARY KEY,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    statement TEXT NOT NULL,
    epistemic_state VARCHAR(16) NOT NULL,
    role VARCHAR(16),
    provenance_origin VARCHAR(16),
    provenance_detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_findings_statement_not_blank
        CHECK (btrim(statement) <> ''),
    CONSTRAINT diagnostic_findings_epistemic_state
        CHECK (epistemic_state IN ('OBSERVED', 'CALCULATED')),
    CONSTRAINT diagnostic_findings_role CHECK (role IN ('SYMPTOM')),
    CONSTRAINT diagnostic_findings_provenance_origin
        CHECK (provenance_origin IN ('USER', 'TEO'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_findings_diagnostic
    ON transformometro.diagnostic_findings (diagnostic_id);

CREATE TABLE IF NOT EXISTS transformometro.diagnostic_hypotheses (
    hypothesis_id UUID PRIMARY KEY,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    statement TEXT NOT NULL,
    -- VALIDATED != FACT: a hypothesis stays INFERRED even when validated.
    epistemic_state VARCHAR(16) NOT NULL DEFAULT 'INFERRED',
    lifecycle VARCHAR(16) NOT NULL,
    effective_validation VARCHAR(32) NOT NULL,
    provenance_origin VARCHAR(16),
    provenance_detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_hypotheses_statement_not_blank
        CHECK (btrim(statement) <> ''),
    CONSTRAINT diagnostic_hypotheses_epistemic_state
        CHECK (epistemic_state = 'INFERRED'),
    CONSTRAINT diagnostic_hypotheses_lifecycle
        CHECK (lifecycle IN ('DRAFT', 'VALIDATED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT diagnostic_hypotheses_effective_validation
        CHECK (effective_validation IN
            ('CURRENT', 'STALE_EVIDENCE', 'REVALIDATION_REQUIRED')),
    CONSTRAINT diagnostic_hypotheses_provenance_origin
        CHECK (provenance_origin IN ('USER', 'TEO'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_hypotheses_diagnostic
    ON transformometro.diagnostic_hypotheses (diagnostic_id);

CREATE TABLE IF NOT EXISTS transformometro.diagnostic_causal_links (
    link_id UUID PRIMARY KEY,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    source_hypothesis_id UUID NOT NULL
        REFERENCES transformometro.diagnostic_hypotheses (hypothesis_id),
    -- Polymorphic target: finding OR hypothesis of the same diagnostic.
    -- Membership within the aggregate is a domain invariant enforced on
    -- rehydration; a FK to a single table cannot express it.
    target_id UUID NOT NULL,
    relation VARCHAR(32) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_causal_links_relation
        CHECK (relation = 'CONTRIBUTES_TO'),
    CONSTRAINT diagnostic_causal_links_no_self_reference
        CHECK (source_hypothesis_id <> target_id)
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_causal_links_diagnostic
    ON transformometro.diagnostic_causal_links (diagnostic_id);

CREATE TABLE IF NOT EXISTS transformometro.diagnostic_evidence_links (
    link_id UUID PRIMARY KEY,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    evidence_id UUID NOT NULL
        REFERENCES transformometro.revisao_evidencias (evidencia_id),
    relation VARCHAR(32) NOT NULL,
    -- Optional target: finding / hypothesis / conclusion of the aggregate.
    target_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_evidence_links_relation
        CHECK (relation IN ('SUPPORTS', 'CONTRADICTS', 'CONTEXTUALIZES'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_evidence_links_diagnostic
    ON transformometro.diagnostic_evidence_links (diagnostic_id);

CREATE TABLE IF NOT EXISTS transformometro.diagnostic_conclusions (
    conclusion_id UUID PRIMARY KEY,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    statement TEXT NOT NULL,
    rationale TEXT,
    epistemic_state VARCHAR(16) NOT NULL DEFAULT 'INFERRED',
    lifecycle VARCHAR(16) NOT NULL,
    -- RootCauseDesignation is a reference, not an entity: the hypothesis it
    -- designates must exist; ownership/subset/effective invariants stay in
    -- the domain kernel.
    root_cause_hypothesis_id UUID
        REFERENCES transformometro.diagnostic_hypotheses (hypothesis_id),
    provenance_origin VARCHAR(16),
    provenance_detail TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_conclusions_statement_not_blank
        CHECK (btrim(statement) <> ''),
    CONSTRAINT diagnostic_conclusions_epistemic_state
        CHECK (epistemic_state = 'INFERRED'),
    CONSTRAINT diagnostic_conclusions_lifecycle
        CHECK (lifecycle IN ('DRAFT', 'VALIDATED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT diagnostic_conclusions_provenance_origin
        CHECK (provenance_origin IN ('USER', 'TEO'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_conclusions_diagnostic
    ON transformometro.diagnostic_conclusions (diagnostic_id);

-- Defense in depth of the domain invariant: at most one VALIDATED
-- conclusion per diagnostic. SUPERSEDED/REJECTED/DRAFT coexist freely.
CREATE UNIQUE INDEX IF NOT EXISTS uq_diagnostic_conclusions_validated
    ON transformometro.diagnostic_conclusions (diagnostic_id)
    WHERE lifecycle = 'VALIDATED';

-- Typed references only: hypothesis_ids / finding_ids of a conclusion.
CREATE TABLE IF NOT EXISTS transformometro.diagnostic_conclusion_refs (
    conclusion_id UUID NOT NULL
        REFERENCES transformometro.diagnostic_conclusions (conclusion_id),
    ref_kind VARCHAR(16) NOT NULL,
    ref_id UUID NOT NULL,
    ordem INTEGER NOT NULL DEFAULT 0,
    CONSTRAINT diagnostic_conclusion_refs_pk
        PRIMARY KEY (conclusion_id, ref_kind, ref_id),
    CONSTRAINT diagnostic_conclusion_refs_kind
        CHECK (ref_kind IN ('hypothesis', 'finding'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_conclusion_refs_conclusion
    ON transformometro.diagnostic_conclusion_refs (conclusion_id);

-- ValidationSnapshot history for hypotheses and conclusions.
-- claim_id is intentionally not an FK: it targets one of two tables
-- (hypotheses or conclusions) depending on claim_kind; writers run inside
-- the aggregate save transaction, and rehydration validates membership.
CREATE TABLE IF NOT EXISTS transformometro.diagnostic_claim_snapshots (
    claim_kind VARCHAR(16) NOT NULL,
    claim_id UUID NOT NULL,
    diagnostic_id UUID NOT NULL
        REFERENCES transformometro.diagnostics (diagnostic_id),
    ordem INTEGER NOT NULL,
    from_lifecycle VARCHAR(16),
    to_lifecycle VARCHAR(16) NOT NULL,
    effective_validation VARCHAR(32) NOT NULL,
    note TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT diagnostic_claim_snapshots_pk
        PRIMARY KEY (claim_kind, claim_id, ordem),
    CONSTRAINT diagnostic_claim_snapshots_kind
        CHECK (claim_kind IN ('hypothesis', 'conclusion')),
    CONSTRAINT diagnostic_claim_snapshots_from_lifecycle
        CHECK (from_lifecycle IN
            ('DRAFT', 'VALIDATED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT diagnostic_claim_snapshots_to_lifecycle
        CHECK (to_lifecycle IN
            ('DRAFT', 'VALIDATED', 'REJECTED', 'SUPERSEDED')),
    CONSTRAINT diagnostic_claim_snapshots_effective
        CHECK (effective_validation IN
            ('CURRENT', 'STALE_EVIDENCE', 'REVALIDATION_REQUIRED'))
);

CREATE INDEX IF NOT EXISTS idx_diagnostic_claim_snapshots_diagnostic
    ON transformometro.diagnostic_claim_snapshots (diagnostic_id);

COMMENT ON TABLE transformometro.diagnostics IS
    'Diagnostic V1 aggregate root. ProblemStatement é composition, não entity.';
COMMENT ON COLUMN transformometro.diagnostics.version IS
    'Optimistic concurrency: UPDATE ... WHERE version = expected_version.';
COMMENT ON COLUMN transformometro.diagnostic_hypotheses.effective_validation IS
    'Frescor da validação (CURRENT/STALE/REVALIDATION). lifecycle != effective_validation.';
COMMENT ON TABLE transformometro.diagnostic_claim_snapshots IS
    'Histórico de transições lifecycle por claim (hypothesis|conclusion).';

COMMIT;
