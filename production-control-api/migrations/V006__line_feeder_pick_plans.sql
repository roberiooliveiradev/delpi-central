-- Lista de coleta do alimentador de linha.
-- Controle operacional da plataforma: nada é escrito no Protheus. A necessidade
-- é recalculada a cada leitura a partir da fila congelada + empenhos + saldos; o
-- que persiste aqui é a decisão do alimentador (o que ele vai buscar e o que já
-- entregou na bancada).

CREATE TABLE IF NOT EXISTS production_control.line_feeder_pick_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    branch VARCHAR(2) NOT NULL,
    -- Horário de corte da fábrica que gerou a lista (data + hora programadas).
    cutoff_at TIMESTAMP NOT NULL,
    -- NULL = lista de todas as bancadas do corte.
    work_center VARCHAR(40),
    status VARCHAR(16) NOT NULL DEFAULT 'open',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by VARCHAR(120),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(120),
    CONSTRAINT ck_pc_line_feeder_pick_plans_status
        CHECK (status IN ('open', 'closed'))
);

COMMENT ON TABLE production_control.line_feeder_pick_plans IS
    'Listas de coleta do alimentador de linha; a necessidade é recalculada, só a decisão persiste.';
COMMENT ON COLUMN production_control.line_feeder_pick_plans.cutoff_at IS
    'Horário de corte da fábrica (hora local programada na carga máquina), não UTC.';

CREATE INDEX IF NOT EXISTS ix_pc_line_feeder_pick_plans_branch_status
    ON production_control.line_feeder_pick_plans (branch, status, created_at DESC);

CREATE TABLE IF NOT EXISTS production_control.line_feeder_pick_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL
        REFERENCES production_control.line_feeder_pick_plans (id) ON DELETE CASCADE,
    work_center VARCHAR(40) NOT NULL,
    production_order VARCHAR(30) NOT NULL,
    operation_code VARCHAR(10) NOT NULL,
    product_code VARCHAR(30) NOT NULL,
    description VARCHAR(200) NOT NULL DEFAULT '',
    unit VARCHAR(10) NOT NULL DEFAULT '',
    -- Fotografia do cálculo no momento em que a lista foi gerada: o alimentador
    -- precisa saber o que pediram, mesmo que a fila mude depois.
    required_qty NUMERIC(18, 6) NOT NULL DEFAULT 0,
    point_of_use_qty NUMERIC(18, 6) NOT NULL DEFAULT 0,
    to_deliver_qty NUMERIC(18, 6) NOT NULL DEFAULT 0,
    status VARCHAR(16) NOT NULL DEFAULT 'pending',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by VARCHAR(120),
    CONSTRAINT ck_pc_line_feeder_pick_items_status
        CHECK (status IN ('pending', 'picked', 'delivered')),
    CONSTRAINT uq_pc_line_feeder_pick_items_key
        UNIQUE (plan_id, work_center, production_order, operation_code, product_code)
);

COMMENT ON TABLE production_control.line_feeder_pick_items IS
    'Itens da lista de coleta com transição pending -> picked -> delivered.';

CREATE INDEX IF NOT EXISTS ix_pc_line_feeder_pick_items_plan
    ON production_control.line_feeder_pick_items (plan_id, work_center, product_code);
