BEGIN;

-- MES-DOWNTIME-ALERTS (Etapa 6) — deduplicação persistida de alertas.
--
-- Guarda a última assinatura notificada por (regra, filial, sujeito) —
-- a mesma condição só dispara novo dispatch quando o estado relevante
-- muda (nova parada, backlog alterado, novo dia de atraso). Não é uma
-- fonte paralela de fatos: os fatos continuam em downtime_events /
-- mes_downtime_treatments; esta tabela só impede notificações
-- repetitivas (RQ-6.7).

CREATE TABLE IF NOT EXISTS production_control.mes_downtime_alert_dispatches (
    -- Identidade natural do alerta: regra + filial + sujeito.
    alert_key           TEXT        PRIMARY KEY,
    branch              VARCHAR(2)  NOT NULL CHECK (branch IN ('01', '02')),
    rule                VARCHAR(60) NOT NULL,
    subject_key         TEXT        NOT NULL,
    -- Assinatura do estado relevante — mudança reabre a notificação.
    signature           TEXT        NOT NULL,
    first_seen_at       TIMESTAMPTZ NOT NULL,
    last_dispatched_at  TIMESTAMPTZ NOT NULL,
    dispatch_count      INTEGER     NOT NULL DEFAULT 1
        CHECK (dispatch_count > 0),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMENT ON TABLE production_control.mes_downtime_alert_dispatches IS
    'Dedup persistido de alertas gerenciais MES (Etapa 6): um alerta só '
    'redispara quando a assinatura do estado relevante muda.';

COMMIT;
