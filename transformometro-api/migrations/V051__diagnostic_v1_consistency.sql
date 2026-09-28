-- Transformômetro — Diagnostic V1 consistency corrections.
-- 1) DiagnosticConclusion gains effective_validation: historical lifecycle
--    is independent from current validation freshness. A VALIDATED
--    conclusion stays VALIDATED when its designated root cause degrades.
-- 2) Same-diagnostic ownership via composite FKs (simple relational only;
--    polymorphic targets remain domain/rehydration responsibility).

BEGIN;

ALTER TABLE transformometro.diagnostic_conclusions
    ADD COLUMN IF NOT EXISTS effective_validation VARCHAR(32)
        NOT NULL DEFAULT 'CURRENT';

-- Backfill from the designated root cause state, mirroring the domain
-- propagation semantics. Conclusions without a root cause stay CURRENT.
UPDATE transformometro.diagnostic_conclusions c
SET effective_validation = CASE
    WHEN h.lifecycle = 'VALIDATED'
         AND h.effective_validation = 'CURRENT' THEN 'CURRENT'
    WHEN h.lifecycle = 'VALIDATED'
         AND h.effective_validation = 'STALE_EVIDENCE' THEN 'STALE_EVIDENCE'
    ELSE 'REVALIDATION_REQUIRED'
END
FROM transformometro.diagnostic_hypotheses h
WHERE c.root_cause_hypothesis_id = h.hypothesis_id;

ALTER TABLE transformometro.diagnostic_conclusions
    ADD CONSTRAINT diagnostic_conclusions_effective_validation
    CHECK (effective_validation IN
        ('CURRENT', 'STALE_EVIDENCE', 'REVALIDATION_REQUIRED'));

-- Composite ownership: children must reference hypotheses owned by the
-- same diagnostic. UNIQUE required before composite FKs can target it.
ALTER TABLE transformometro.diagnostic_hypotheses
    ADD CONSTRAINT diagnostic_hypotheses_diagnostic_hypothesis_key
    UNIQUE (diagnostic_id, hypothesis_id);

ALTER TABLE transformometro.diagnostic_causal_links
    ADD CONSTRAINT diagnostic_causal_links_source_ownership_fkey
    FOREIGN KEY (diagnostic_id, source_hypothesis_id)
    REFERENCES transformometro.diagnostic_hypotheses
        (diagnostic_id, hypothesis_id);

ALTER TABLE transformometro.diagnostic_conclusions
    ADD CONSTRAINT diagnostic_conclusions_root_cause_ownership_fkey
    FOREIGN KEY (diagnostic_id, root_cause_hypothesis_id)
    REFERENCES transformometro.diagnostic_hypotheses
        (diagnostic_id, hypothesis_id);

COMMENT ON COLUMN transformometro.diagnostic_conclusions.effective_validation
    IS 'Frescor atual da validação; independente do lifecycle histórico.';

COMMIT;
