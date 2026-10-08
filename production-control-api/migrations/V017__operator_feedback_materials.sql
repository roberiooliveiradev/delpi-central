BEGIN;

-- V017 — Materiais estruturados do Operator Feedback (C5).
--
-- Filha de operator_feedbacks (V016): quando o motivo é missing_material, o
-- operador seleciona materiais REAIS da OP (SD4) e o backend congela o
-- snapshot (descrição, unidade, quantidades e empenhos) — o navegador nunca
-- é autoridade sobre esses dados.
--
-- Lifecycle próprio e independente do feedback:
--   pending -> picked -> delivered  (sem retorno nesta fase)
--   feedback open|acknowledged|resolved continua governando o impedimento.
-- Material delivered NÃO resolve o feedback — o PCP decide quando encerrar.
-- Feedback resolved tira o material da fila ativa do Alimentador sem apagar
-- o histórico (a fila filtra por feedback ativo).
--
-- Não é pick plan: line_feeder_pick_plans/items seguem sendo o fluxo
-- planejado por corte. Esta tabela é a solicitação urgente da bancada.

CREATE TABLE IF NOT EXISTS production_control.operator_feedback_materials (
    id                UUID          PRIMARY KEY DEFAULT gen_random_uuid(),

    feedback_id       UUID          NOT NULL
        REFERENCES production_control.operator_feedbacks (id) ON DELETE RESTRICT,

    -- Snapshot SD4 congelado no reporte — o frontend envia só os códigos.
    product_code      VARCHAR(40)   NOT NULL,
    description       VARCHAR(160)  NOT NULL DEFAULT '',
    unit              VARCHAR(10)   NOT NULL DEFAULT '',
    original_qty      NUMERIC(15,6) NOT NULL DEFAULT 0,
    open_qty          NUMERIC(15,6) NOT NULL DEFAULT 0,
    consumed_qty      NUMERIC(15,6) NOT NULL DEFAULT 0,
    commitment_count  INTEGER       NOT NULL DEFAULT 0,

    status            VARCHAR(20)   NOT NULL DEFAULT 'pending',

    created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    picked_at         TIMESTAMPTZ   NULL,
    picked_by         VARCHAR(120)  NULL,
    delivered_at      TIMESTAMPTZ   NULL,
    delivered_by      VARCHAR(120)  NULL,

    CONSTRAINT chk_pc_feedback_materials_status CHECK (
        status IN ('pending', 'picked', 'delivered')
    ),
    CONSTRAINT chk_pc_feedback_materials_picked CHECK (
        status <> 'picked' OR picked_at IS NOT NULL
    ),
    CONSTRAINT chk_pc_feedback_materials_delivered CHECK (
        status <> 'delivered' OR delivered_at IS NOT NULL
    ),
    CONSTRAINT chk_pc_feedback_materials_timeline CHECK (
        (picked_at IS NULL OR picked_at >= created_at)
        AND (delivered_at IS NULL OR picked_at IS NULL
             OR delivered_at >= picked_at)
    ),
    -- Um material por código dentro do mesmo impedimento.
    CONSTRAINT uq_pc_feedback_materials_code UNIQUE (feedback_id, product_code)
);

COMMENT ON TABLE production_control.operator_feedback_materials IS
    'Materiais SD4 informados como faltantes pelo operador (C5). Fila urgente do Alimentador de Linha — separada das pick lists planejadas. delivered não resolve o feedback.';

COMMENT ON COLUMN production_control.operator_feedback_materials.open_qty IS
    'Saldo em aberto na SD4 no instante do reporte — snapshot informativo, não quantidade operacional a transportar.';

-- Fila urgente do Alimentador: materiais pendentes/em separação.
CREATE INDEX IF NOT EXISTS idx_pc_feedback_materials_status
    ON production_control.operator_feedback_materials (status, created_at);

CREATE INDEX IF NOT EXISTS idx_pc_feedback_materials_feedback
    ON production_control.operator_feedback_materials (feedback_id);

COMMIT;
