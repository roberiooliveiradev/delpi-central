-- Histórico de produtos da NF-e sem código Delpi reconhecido.
-- Schema: lancamento_notas_fiscais
-- Não bloqueia a solicitação. A linha some só se a solicitação for apagada
-- na compensação do anexo.

CREATE TABLE IF NOT EXISTS lancamento_notas_fiscais.invoice_posting_unmapped_products (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID NOT NULL,
    branch_code VARCHAR(2) NOT NULL,
    supplier_code VARCHAR(6) NOT NULL,
    supplier_store VARCHAR(2) NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    supplier_product_code VARCHAR(60) NOT NULL,
    supplier_product_description VARCHAR(120),
    quantity NUMERIC(18, 4),
    unit VARCHAR(6),
    mapping_status VARCHAR(20) NOT NULL,
    document_number VARCHAR(9) NOT NULL,
    series VARCHAR(3) NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lnf_unmapped_product_request
        FOREIGN KEY (request_id)
        REFERENCES lancamento_notas_fiscais.invoice_posting_requests (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lnf_unmapped_product_branch
        CHECK (branch_code IN ('01', '02')),

    CONSTRAINT ck_lnf_unmapped_product_status
        CHECK (mapping_status IN ('unmapped', 'ambiguous')),

    CONSTRAINT ck_lnf_unmapped_product_code
        CHECK (btrim(supplier_product_code) <> '')
);

CREATE INDEX IF NOT EXISTS ix_lnf_unmapped_products_created
    ON lancamento_notas_fiscais.invoice_posting_unmapped_products (created_at DESC, id DESC);

CREATE INDEX IF NOT EXISTS ix_lnf_unmapped_products_supplier_code
    ON lancamento_notas_fiscais.invoice_posting_unmapped_products (
        supplier_code,
        supplier_store,
        supplier_product_code
    );

CREATE INDEX IF NOT EXISTS ix_lnf_unmapped_products_request
    ON lancamento_notas_fiscais.invoice_posting_unmapped_products (request_id);

COMMENT ON TABLE lancamento_notas_fiscais.invoice_posting_unmapped_products IS
    'Ocorrências de produto da NF-e sem código Delpi reconhecido, para análise do cadastro Produto x Fornecedor.';
