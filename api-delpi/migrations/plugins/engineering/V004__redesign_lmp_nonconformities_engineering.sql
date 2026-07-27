-- Redesign NC LMP: domínio engenharia (OV/LMP), remove campos de recebimento.

-- Cabeçalho: novos campos de engenharia
ALTER TABLE engineering.lmp_nonconformities
    ADD COLUMN IF NOT EXISTS customer_name VARCHAR(200),
    ADD COLUMN IF NOT EXISTS launch_date DATE,
    ADD COLUMN IF NOT EXISTS last_revision_date DATE,
    ADD COLUMN IF NOT EXISTS executed_by VARCHAR(200),
    ADD COLUMN IF NOT EXISTS released_by VARCHAR(200);

-- Remover modelo de recebimento/inspeção (não aplicável a LMP)
ALTER TABLE engineering.lmp_nonconformities
    DROP COLUMN IF EXISTS material_code,
    DROP COLUMN IF EXISTS supplier_name,
    DROP COLUMN IF EXISTS purchase_order,
    DROP COLUMN IF EXISTS invoice_number,
    DROP COLUMN IF EXISTS qty_received,
    DROP COLUMN IF EXISTS qty_accepted,
    DROP COLUMN IF EXISTS qty_rejected,
    DROP COLUMN IF EXISTS branch_code;

DROP INDEX IF EXISTS engineering.ix_lmp_nonconformities_material_code;
DROP INDEX IF EXISTS engineering.ix_lmp_nonconformities_branch_code;

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_customer_name
    ON engineering.lmp_nonconformities (customer_name)
    WHERE customer_name IS NOT NULL;

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_launch_date
    ON engineering.lmp_nonconformities (launch_date DESC)
    WHERE launch_date IS NOT NULL;

-- Produtos: descrição (snapshot TOTVS / edição manual)
ALTER TABLE engineering.lmp_nonconformity_products
    ADD COLUMN IF NOT EXISTS product_description VARCHAR(255);

COMMENT ON COLUMN engineering.lmp_nonconformities.sale_number IS
    'Número da OV (= identificador da LMP).';
COMMENT ON COLUMN engineering.lmp_nonconformities.customer_name IS
    'Cliente (snapshot editável; tipicamente hidratado do TOTVS).';
COMMENT ON COLUMN engineering.lmp_nonconformities.launch_date IS
    'Data de lançamento da LMP/OV (snapshot editável).';
COMMENT ON COLUMN engineering.lmp_nonconformities.last_revision_date IS
    'Data da última revisão (snapshot editável).';
COMMENT ON COLUMN engineering.lmp_nonconformities.executed_by IS
    'Quem executou (texto livre).';
COMMENT ON COLUMN engineering.lmp_nonconformities.released_by IS
    'Quem liberou (texto livre).';
COMMENT ON COLUMN engineering.lmp_nonconformities.registered_at IS
    'Data/hora automática do registro da NC (servidor).';
COMMENT ON COLUMN engineering.lmp_nonconformities.defect_description IS
    'Problema identificado.';
COMMENT ON COLUMN engineering.lmp_nonconformity_products.product_code IS
    'Código do material/produto Protheus na linha da NC.';
COMMENT ON COLUMN engineering.lmp_nonconformity_products.product_description IS
    'Descrição do produto (snapshot).';
