-- NC sandbox bootstrap (ISOLATED development dataset only).
-- Reproduces the effective schema of api-delpi migrations
-- plugins/engineering V001-V009 for the lmp_nonconformities family.
-- Canonical migrations remain owned by the migration runner until
-- ADR-NC-OWNERSHIP transfer is approved. Never apply against
-- shared/production postgres-plugins.

CREATE SCHEMA IF NOT EXISTS engineering;

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    registered_at TIMESTAMPTZ NOT NULL,
    occurrence_date DATE NOT NULL DEFAULT CURRENT_DATE,
    sale_number VARCHAR(20),
    lmp_number VARCHAR(40),
    customer_name VARCHAR(200),
    launch_date DATE,
    last_revision_date DATE,
    executed_by VARCHAR(200),
    released_by VARCHAR(200),
    status VARCHAR(40) NOT NULL DEFAULT 'open',
    defect_description TEXT,
    corrective_actions TEXT,
    technical_opinion TEXT,
    created_by VARCHAR(120),
    updated_by VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT ck_lmp_nonconformities_status CHECK (
        status IN ('open', 'in_progress', 'done')
    )
);

CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_registered_at
    ON engineering.lmp_nonconformities (registered_at DESC);
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_occurrence_date
    ON engineering.lmp_nonconformities (occurrence_date DESC);
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_status
    ON engineering.lmp_nonconformities (status);
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_sale_number
    ON engineering.lmp_nonconformities (sale_number)
    WHERE sale_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_lmp_number
    ON engineering.lmp_nonconformities (lmp_number)
    WHERE lmp_number IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_customer_name
    ON engineering.lmp_nonconformities (customer_name)
    WHERE customer_name IS NOT NULL;
CREATE INDEX IF NOT EXISTS ix_lmp_nonconformities_launch_date
    ON engineering.lmp_nonconformities (launch_date DESC)
    WHERE launch_date IS NOT NULL;

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformity_products (
    nonconformity_id UUID NOT NULL,
    product_code VARCHAR(60) NOT NULL,
    product_description VARCHAR(255),
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

CREATE TABLE IF NOT EXISTS engineering.lmp_problem_tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    label VARCHAR(80) NOT NULL,
    created_by VARCHAR(120),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_lmp_problem_tags_label_ci UNIQUE (label)
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_lmp_problem_tags_label_lower
    ON engineering.lmp_problem_tags (LOWER(TRIM(label)));

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformity_problem_tags (
    nonconformity_id UUID NOT NULL,
    tag_id UUID NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT pk_lmp_nc_problem_tags
        PRIMARY KEY (nonconformity_id, tag_id),

    CONSTRAINT fk_lmp_nc_problem_tags_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES engineering.lmp_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT fk_lmp_nc_problem_tags_tag
        FOREIGN KEY (tag_id)
        REFERENCES engineering.lmp_problem_tags (id)
        ON UPDATE RESTRICT
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_lmp_nc_problem_tags_tag
    ON engineering.lmp_nonconformity_problem_tags (tag_id);

CREATE TABLE IF NOT EXISTS engineering.lmp_nonconformity_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nonconformity_id UUID NOT NULL,
    event_type VARCHAR(40) NOT NULL,
    changes JSONB NOT NULL DEFAULT '{}'::jsonb,
    actor_user_id VARCHAR(100) NOT NULL,
    actor_email VARCHAR(255),
    actor_name VARCHAR(300),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT fk_lmp_nc_history_nc
        FOREIGN KEY (nonconformity_id)
        REFERENCES engineering.lmp_nonconformities (id)
        ON UPDATE RESTRICT
        ON DELETE CASCADE,

    CONSTRAINT ck_lmp_nc_history_event_type CHECK (
        event_type IN ('created', 'updated')
    )
);

CREATE INDEX IF NOT EXISTS ix_lmp_nc_history_nc_created
    ON engineering.lmp_nonconformity_history (nonconformity_id, created_at DESC);

CREATE OR REPLACE FUNCTION engineering.prevent_lmp_nc_history_mutation()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'DELETE'
       AND lower(coalesce(current_setting('app.allow_lmp_nc_history_delete', true), ''))
           = 'true' THEN
        RETURN OLD;
    END IF;

    RAISE EXCEPTION 'lmp_nonconformity_history is append-only';
END;
$$;

DROP TRIGGER IF EXISTS trg_lmp_nc_history_no_mutation
    ON engineering.lmp_nonconformity_history;

CREATE TRIGGER trg_lmp_nc_history_no_mutation
    BEFORE UPDATE OR DELETE ON engineering.lmp_nonconformity_history
    FOR EACH ROW
    EXECUTE PROCEDURE engineering.prevent_lmp_nc_history_mutation();

INSERT INTO engineering.lmp_problem_tags (label)
SELECT v.label
  FROM (VALUES
    ('Medida'),
    ('Desenho'),
    ('Terminal'),
    ('Tolerância'),
    ('Material'),
    ('Acabamento'),
    ('Posição')
  ) AS v(label)
 WHERE NOT EXISTS (
     SELECT 1
       FROM engineering.lmp_problem_tags t
      WHERE LOWER(TRIM(t.label)) = LOWER(TRIM(v.label))
 );
