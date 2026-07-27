-- Catálogo de tags «Problema identificado» + vínculo N:N com NCs LMP.
-- ``defect_description`` permanece texto livre (descrição do caso).

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

COMMENT ON TABLE engineering.lmp_problem_tags IS
    'Catálogo compartilhado de tags de problema identificado (NC LMP).';
COMMENT ON TABLE engineering.lmp_nonconformity_problem_tags IS
    'Vínculo N:N entre NC LMP e tags de problema identificado.';
COMMENT ON COLUMN engineering.lmp_nonconformities.defect_description IS
    'Descrição livre do caso (texto do usuário). Tags de classificação ficam em lmp_nonconformity_problem_tags.';

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
