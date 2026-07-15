-- Guias e Procedimentos — schema e tabelas (V001)

CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS guias_procedimentos.departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(120) NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    icon VARCHAR(64) NOT NULL DEFAULT 'book-open',
    active BOOLEAN NOT NULL DEFAULT TRUE,
    order_index INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100),
    created_by_name VARCHAR(200),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200),

    CONSTRAINT uq_guias_procedimentos_departments_slug UNIQUE (slug),
    CONSTRAINT ck_guias_procedimentos_departments_name_not_blank
        CHECK (char_length(btrim(name)) > 0),
    CONSTRAINT ck_guias_procedimentos_departments_slug_not_blank
        CHECK (char_length(btrim(slug)) > 0),
    CONSTRAINT ck_guias_procedimentos_departments_icon_not_blank
        CHECK (char_length(btrim(icon)) > 0)
);

CREATE TABLE IF NOT EXISTS guias_procedimentos.procedures (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL
        REFERENCES guias_procedimentos.departments (id)
        ON DELETE RESTRICT,
    title VARCHAR(500) NOT NULL,
    slug VARCHAR(160) NOT NULL,
    summary TEXT NOT NULL DEFAULT '',
    content_html TEXT NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    reading_time_minutes INTEGER,
    order_index INTEGER NOT NULL DEFAULT 0,
    published_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by_user_id VARCHAR(100),
    created_by_name VARCHAR(200),
    updated_by_user_id VARCHAR(100),
    updated_by_name VARCHAR(200),

    CONSTRAINT uq_guias_procedimentos_procedures_slug UNIQUE (slug),
    CONSTRAINT ck_guias_procedimentos_procedures_title_not_blank
        CHECK (char_length(btrim(title)) > 0),
    CONSTRAINT ck_guias_procedimentos_procedures_slug_not_blank
        CHECK (char_length(btrim(slug)) > 0),
    CONSTRAINT ck_guias_procedimentos_procedures_status
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT ck_guias_procedimentos_procedures_reading_time
        CHECK (reading_time_minutes IS NULL OR reading_time_minutes >= 0)
);

CREATE INDEX IF NOT EXISTS idx_guias_procedimentos_departments_active_order
    ON guias_procedimentos.departments (active, order_index, name);

CREATE INDEX IF NOT EXISTS idx_guias_procedimentos_procedures_department_status_order
    ON guias_procedimentos.procedures (department_id, status, order_index, title);

CREATE INDEX IF NOT EXISTS idx_guias_procedimentos_procedures_status
    ON guias_procedimentos.procedures (status);
