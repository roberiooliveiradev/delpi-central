-- V011 — Auditoria append-only das ações MES (Etapa 05).
--
-- Registra quem executou cada transição relevante (operador ou sistema),
-- sem tokens/segredos. A linha é escrita na MESMA transação da transição:
-- se a ação principal sofre rollback, a auditoria não existe.

CREATE TABLE IF NOT EXISTS production_control.mes_audit_events (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    branch          TEXT        NOT NULL,
    work_center     TEXT        NOT NULL,
    run_id          UUID        NULL
        REFERENCES production_control.production_runs(id) ON DELETE RESTRICT,
    action          TEXT        NOT NULL,
    actor_type      TEXT        NOT NULL
        CHECK (actor_type IN ('operator', 'system')),
    actor_ref       TEXT        NULL,
    occurred_at     TIMESTAMPTZ NOT NULL,
    details         JSONB       NOT NULL DEFAULT '{}'::jsonb,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_pc_mes_audit_run
    ON production_control.mes_audit_events (run_id, occurred_at);

CREATE INDEX IF NOT EXISTS ix_pc_mes_audit_ct
    ON production_control.mes_audit_events (branch, work_center, occurred_at DESC);
