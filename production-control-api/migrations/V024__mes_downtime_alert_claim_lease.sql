BEGIN;

-- MES-DOWNTIME-ALERTS (revisão corretiva Etapa 6) — claim com lease e
-- confirmação de entrega.
--
-- V023 marcava a assinatura como notificada já no claim: uma falha
-- transitória de dispatch perdia o alerta para sempre. Agora o claim
-- reserva (pending_signature + claimed_at com lease), a assinatura só
-- vira "entregue" após dispatch confirmado, e falha libera o claim
-- para retry seguro — sem duplicar entrega entre avaliadores.

ALTER TABLE production_control.mes_downtime_alert_dispatches
    ADD COLUMN IF NOT EXISTS pending_signature TEXT,
    ADD COLUMN IF NOT EXISTS claimed_at TIMESTAMPTZ,
    ALTER COLUMN signature DROP NOT NULL,
    ALTER COLUMN last_dispatched_at DROP NOT NULL,
    ALTER COLUMN dispatch_count DROP NOT NULL,
    ALTER COLUMN dispatch_count SET DEFAULT 0,
    DROP CONSTRAINT IF EXISTS mes_downtime_alert_dispatches_dispatch_count_check,
    ADD CONSTRAINT mes_downtime_alert_dispatches_dispatch_count_check
        CHECK (dispatch_count >= 0);

COMMENT ON COLUMN production_control.mes_downtime_alert_dispatches.pending_signature IS
    'Assinatura reservada por um claim em andamento — só migra para signature após dispatch confirmado.';
COMMENT ON COLUMN production_control.mes_downtime_alert_dispatches.claimed_at IS
    'Lease do claim: impede claim concorrente; expirado permite retry após falha/crash do avaliador.';

COMMIT;
