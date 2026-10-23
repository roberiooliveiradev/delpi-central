BEGIN;

-- PC-MES-CT-AUTONOMOUS-DOWNTIME — cursor durável do monitoramento autônomo.
--
-- Guarda o ESTADO DE OBSERVAÇÃO do contador Pulse por (branch, work_center)
-- quando nenhum run MES está ativo: último contador/epoch vistos, baseline
-- do último incremento real e saúde do vínculo. Não duplica fatos — os
-- fatos operacionais continuam exclusivamente em work_center_state_events
-- e downtime_events (com run_id NULL quando autônomos).
--
-- Uma linha por CT monitorado: PK (branch, work_center). A linha é o
-- cursor que sobrevive a restart da API e serializa contra replay de
-- snapshots (contador monotônico por device+epoch).

CREATE TABLE IF NOT EXISTS production_control.work_center_pulse_observers (
    branch              VARCHAR(2)  NOT NULL CHECK (branch IN ('01', '02')),
    work_center         VARCHAR(40) NOT NULL,
    -- Identidade do contador observado; troca/reset realinha o cursor
    -- (counter_epoch + device_id fazem parte da identidade da âncora).
    device_id           UUID,
    counter_epoch       BIGINT      NOT NULL DEFAULT 0,
    last_counter        BIGINT      NOT NULL DEFAULT 0,
    -- Baseline do monitoramento: instante do último incremento observado.
    -- NULL enquanto nenhum pulso foi visto — sem baseline, nenhuma parada
    -- é criada (AC-10: nada retroativo inventado).
    last_increment_at   TIMESTAMPTZ,
    baseline_established_at TIMESTAMPTZ,
    -- Saúde da observação: ok / degraded (offline, ambíguo, sem vínculo).
    device_online       BOOLEAN     NOT NULL DEFAULT FALSE,
    degraded_reason     VARCHAR(60),
    last_seen_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (branch, work_center)
);

COMMENT ON TABLE production_control.work_center_pulse_observers IS
    'Cursor durável do monitoramento autônomo de paradas por CT (sem run MES).';

COMMIT;
