-- Catálogo de submódulos do schema quality (extensível: kaizen, audit_5s, ppm, …)

CREATE TABLE IF NOT EXISTS quality.submodules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT uq_quality_submodules_code UNIQUE (code),
    CONSTRAINT ck_quality_submodules_sort_order CHECK (sort_order >= 0)
);

INSERT INTO quality.submodules (code, name, description, sort_order)
VALUES
    (
        'kaizen',
        'Kaizen',
        'Melhorias contínuas e economia (tempo, material, financeiro ou qualitativo).',
        10
    ),
    (
        'audit_5s',
        'Auditoria 5S',
        'Avaliação operacional 5S por filial (PostgreSQL).',
        20
    ),
    (
        'ppm',
        'PPM',
        'Parts per million — indicadores de qualidade (futuro).',
        30
    ),
    (
        'nonconformity',
        'Não conformidades',
        'NC operacionais integradas ao módulo qualidade (futuro).',
        40
    )
ON CONFLICT (code) DO NOTHING;
