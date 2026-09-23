-- Lista de coleta passa a ser um item por produto (soma entre bancadas),
-- com local de retirada (BZ_MPLOCAL) fotografado na geração.
-- Listas anteriores são descartadas: a feature ainda era nova e a unique key muda.

DELETE FROM production_control.line_feeder_pick_items;
DELETE FROM production_control.line_feeder_pick_plans;

ALTER TABLE production_control.line_feeder_pick_items
    ADD COLUMN IF NOT EXISTS pickup_location VARCHAR(30) NOT NULL DEFAULT '';

ALTER TABLE production_control.line_feeder_pick_items
    ALTER COLUMN work_center DROP NOT NULL;

ALTER TABLE production_control.line_feeder_pick_items
    ALTER COLUMN production_order DROP NOT NULL;

ALTER TABLE production_control.line_feeder_pick_items
    ALTER COLUMN operation_code DROP NOT NULL;

ALTER TABLE production_control.line_feeder_pick_items
    DROP CONSTRAINT IF EXISTS uq_pc_line_feeder_pick_items_key;

ALTER TABLE production_control.line_feeder_pick_items
    ADD CONSTRAINT uq_pc_line_feeder_pick_items_product
        UNIQUE (plan_id, product_code);

DROP INDEX IF EXISTS production_control.ix_pc_line_feeder_pick_items_plan;

CREATE INDEX IF NOT EXISTS ix_pc_line_feeder_pick_items_plan
    ON production_control.line_feeder_pick_items (plan_id, product_code);

COMMENT ON COLUMN production_control.line_feeder_pick_items.pickup_location IS
    'Local de retirada (SBZ010.BZ_MPLOCAL) na filial do plano, no momento da geração.';
COMMENT ON COLUMN production_control.line_feeder_pick_items.work_center IS
    'Legado; a lista atual é por produto e não preenche bancada.';
COMMENT ON COLUMN production_control.line_feeder_pick_items.production_order IS
    'Legado; a lista atual é por produto e não preenche OP.';
COMMENT ON COLUMN production_control.line_feeder_pick_items.operation_code IS
    'Legado; a lista atual é por produto e não preenche operação.';
