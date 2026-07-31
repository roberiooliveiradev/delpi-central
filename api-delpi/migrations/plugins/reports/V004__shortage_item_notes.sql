-- Delpi Reports — notas de acompanhamento por item de ruptura (V004)
-- Não ocultam o e-mail: só enriquecem a coluna Observação (Fases 2–3 da API).

CREATE TABLE IF NOT EXISTS reports.shortage_item_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    definition_id UUID NOT NULL,
    branch VARCHAR(2) NOT NULL,
    product_code VARCHAR(30) NOT NULL,
    note_text TEXT NOT NULL,
    expected_receipt_date DATE,
    author_user_id VARCHAR(100) NOT NULL,
    author_display_name VARCHAR(200) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_reports_shortage_item_notes_definition
        FOREIGN KEY (definition_id)
        REFERENCES reports.report_definitions (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_reports_shortage_item_notes_branch
        CHECK (branch IN ('01', '02')),
    CONSTRAINT ck_reports_shortage_item_notes_product_not_blank
        CHECK (char_length(btrim(product_code)) > 0),
    CONSTRAINT ck_reports_shortage_item_notes_text_not_blank
        CHECK (char_length(btrim(note_text)) > 0),
    CONSTRAINT ck_reports_shortage_item_notes_author_id_not_blank
        CHECK (char_length(btrim(author_user_id)) > 0),
    CONSTRAINT ck_reports_shortage_item_notes_author_name_not_blank
        CHECK (char_length(btrim(author_display_name)) > 0)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_reports_shortage_item_notes_def_branch_product
    ON reports.shortage_item_notes (definition_id, branch, product_code);

CREATE INDEX IF NOT EXISTS idx_reports_shortage_item_notes_definition_branch
    ON reports.shortage_item_notes (definition_id, branch);
