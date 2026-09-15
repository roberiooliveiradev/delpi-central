-- Modelo 3D vigente por produto da OP (PI ou PA). Um GLB por código DELPI.

CREATE TABLE IF NOT EXISTS production_control.product_3d_models (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    product_code VARCHAR(30) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(80) NOT NULL,
    content_type VARCHAR(80) NOT NULL DEFAULT 'model/gltf-binary',
    byte_size BIGINT NOT NULL,
    uploaded_by VARCHAR(120),
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pc_product_3d_models_product_code UNIQUE (product_code),
    CONSTRAINT ck_pc_product_3d_models_byte_size CHECK (byte_size > 0)
);

COMMENT ON TABLE production_control.product_3d_models IS
    'Modelo 3D (.glb) do produto da ordem de produção; um arquivo vigente por código DELPI.';

COMMENT ON COLUMN production_control.product_3d_models.product_code IS
    'Código DELPI do produto da OP (PI ou PA), normalizado em maiúsculas.';

CREATE INDEX IF NOT EXISTS ix_pc_product_3d_models_uploaded
    ON production_control.product_3d_models (uploaded_at DESC);
