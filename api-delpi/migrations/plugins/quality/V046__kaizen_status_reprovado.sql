-- V046 — status 'reprovado' no Kaizômetro (ideia não aprovada no comitê).
-- Acompanhado por api-delpi kaizen_status_date_rules (exige date_committee_approved).

ALTER TABLE quality.kaizens
    DROP CONSTRAINT ck_quality_kaizens_status,
    ADD CONSTRAINT ck_quality_kaizens_status
        CHECK (status IN ('recebido', 'aprovado', 'reprovado', 'implantado', 'descontinuado', 'cancelado'));

ALTER TABLE quality.kaizen_revisions
    DROP CONSTRAINT ck_kaizen_revision_version_status,
    ADD CONSTRAINT ck_kaizen_revision_version_status
        CHECK (version_status IN ('recebido', 'aprovado', 'reprovado', 'implantado', 'descontinuado', 'cancelado', 'substituido'));
