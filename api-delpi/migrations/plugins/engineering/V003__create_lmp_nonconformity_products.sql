-- Produtos amarrados a uma NC LMP (códigos Protheus; referência lógica)

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformity_products (
    nonconformity_id UUID NOT NULL,
    product_code VARCHAR(60) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_lmp_nonconformity_products
        PRIMARY KEY (nonconformity_id, product_code),

    CONSTRAINT fk_lmp_nonconformity_products_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES engineering.lmp_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformity_products_code
    ON engineering.lmp_nonconformity_products (product_code);
