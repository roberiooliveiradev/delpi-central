BEGIN;

-- V016 — Fundação do Operator Feedback (impedimentos do chão de fábrica).
--
-- Canal pelo qual o operador informa ao PCP que uma OP/operação não pode ser
-- produzida (ex.: falta de material). É um fato de COMUNICAÇÃO — NÃO é parada
-- de máquina, downtime MES, mudança de estado producing/stopped nem apontamento.
-- A máquina pode seguir executando outra OP enquanto esta tem impedimento aberto.
--
-- Independência proposital:
--   * sem FK para machine_load_snapshots/publications: o feedback sobrevive a
--     refresh, nova geração, withdraw e transferência de CT;
--   * sem FK para bench sessions e run_id com ON DELETE SET NULL: o registro
--     existe mesmo sem run ativo — é contexto, não dependência;
--   * reported_work_center congela o CT no instante do reporte; transferências
--     posteriores não reatribuem o feedback.
--
-- Lifecycle: open -> acknowledged -> resolved (terminal). open -> resolved direto
-- também é válido. Reabertura não existe nesta fase.
--
-- Duplicidade: o índice parcial uq_pc_operator_feedbacks_active impede no BANCO
-- um segundo impedimento ativo (open|acknowledged) para a mesma
-- branch + OP + operação + tipo + motivo. Registros resolved não bloqueiam
-- um impedimento novo equivalente — é a proteção contra duplo clique, retry,
-- duas bancadas e requests concorrentes (nunca SELECT-then-INSERT).

CREATE TABLE IF NOT EXISTS production_control.operator_feedbacks (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identidade funcional da OP/operação (histórica, sem FK de snapshot).
    branch                VARCHAR(2)   NOT NULL CHECK (branch IN ('01', '02')),
    production_order      VARCHAR(30)  NOT NULL,
    operation_code        VARCHAR(10)  NOT NULL,

    -- CT no instante do reporte — não segue transferências futuras.
    reported_work_center  VARCHAR(40)  NOT NULL,

    -- Extensível por domínio: novos tipos/motivos entram via código + migration
    -- de check opcional; a tabela não prende o catálogo para não travar a C2+.
    feedback_type         VARCHAR(40)  NOT NULL,
    reason_code           VARCHAR(40)  NOT NULL,

    note                  TEXT         NULL,

    -- Contexto do operador no instante do reporte.
    operator_code         VARCHAR(30)  NOT NULL,
    operator_name         VARCHAR(120) NOT NULL,
    bench_session_id      UUID         NULL,
    run_id                UUID         NULL
        REFERENCES production_control.production_runs (id) ON DELETE SET NULL,

    status                VARCHAR(20)  NOT NULL DEFAULT 'open',

    -- Snapshot histórico do contexto da OP (congelado no reporte).
    product_code          VARCHAR(40)  NULL,
    product_description   VARCHAR(160) NULL,
    pa_product_code       VARCHAR(40)  NULL,
    due_date              DATE         NULL,

    created_at            TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    acknowledged_at       TIMESTAMPTZ  NULL,
    acknowledged_by       VARCHAR(120) NULL,
    resolved_at           TIMESTAMPTZ  NULL,
    resolved_by           VARCHAR(120) NULL,
    resolution_note       TEXT         NULL,

    CONSTRAINT chk_pc_operator_feedbacks_status CHECK (
        status IN ('open', 'acknowledged', 'resolved')
    ),
    -- Coerência do lifecycle: o status exige o carimbo correspondente.
    CONSTRAINT chk_pc_operator_feedbacks_ack_status CHECK (
        status <> 'acknowledged' OR acknowledged_at IS NOT NULL
    ),
    CONSTRAINT chk_pc_operator_feedbacks_res_status CHECK (
        status <> 'resolved' OR resolved_at IS NOT NULL
    ),
    CONSTRAINT chk_pc_operator_feedbacks_timeline CHECK (
        (acknowledged_at IS NULL OR acknowledged_at >= created_at)
        AND (resolved_at IS NULL OR resolved_at >= created_at)
        AND (acknowledged_at IS NULL OR resolved_at IS NULL
             OR resolved_at >= acknowledged_at)
    )
);

COMMENT ON TABLE production_control.operator_feedbacks IS
    'Impedimentos comunicados pelo operador ao PCP. Não é downtime MES: não altera estado da máquina nem depende de run/snapshot da carga máquina.';

COMMENT ON COLUMN production_control.operator_feedbacks.reported_work_center IS
    'CT no instante do reporte (histórico): transferência posterior da OP não reatribui o feedback.';

COMMENT ON COLUMN production_control.operator_feedbacks.run_id IS
    'Run ativo no instante do reporte, quando existia — contexto opcional, nunca dependência (SET NULL preserva o feedback).';

-- Um impedimento ativo (open|acknowledged) por chave lógica; resolved libera.
CREATE UNIQUE INDEX IF NOT EXISTS uq_pc_operator_feedbacks_active
    ON production_control.operator_feedbacks (
        branch, production_order, operation_code, feedback_type, reason_code
    )
    WHERE status IN ('open', 'acknowledged');

-- Inbox do PCP por filial/status (C3) e leitura em lote por CT (C4).
CREATE INDEX IF NOT EXISTS idx_pc_operator_feedbacks_branch_status
    ON production_control.operator_feedbacks (branch, status, created_at);

CREATE INDEX IF NOT EXISTS idx_pc_operator_feedbacks_reported_wc
    ON production_control.operator_feedbacks (branch, reported_work_center, status);

CREATE INDEX IF NOT EXISTS idx_pc_operator_feedbacks_operation
    ON production_control.operator_feedbacks (branch, production_order, operation_code);

COMMIT;
