BEGIN;

-- V015 — Fundação da publicação da Carga Máquina (WORKING x PUBLISHED).
--
-- machine_load_snapshots passa a ser a fila WORKING (em preparação pelo PCP).
-- A nova machine_load_publications guarda a fila PUBLISHED (a oficial das
-- bancadas): uma cópia independente e durável da geração que foi enviada.
--
-- generation_id identifica o conteúdo-base de um refresh da Carga Máquina:
--   WORKING.generation_id = PUBLISHED.generation_id → fila sincronizada (LIVE)
--   WORKING.generation_id <> PUBLISHED.generation_id → carga nova em preparação
-- Por isso NÃO há FK de publications.generation_id para snapshots: depois de
-- um refresh novo, o WORKING avança para a geração seguinte enquanto a
-- publicação precisa continuar existindo com a geração anterior.

-- DEFAULT só protege a janela mixed-version (código antigo inserindo sem a
-- coluna): o upsert do refresh sempre sobrescreve com a geração explícita.
ALTER TABLE production_control.machine_load_snapshots
    ADD COLUMN generation_id UUID DEFAULT gen_random_uuid();

-- Toda fila existente já representa uma geração válida em uso pelas bancadas.
UPDATE production_control.machine_load_snapshots
SET generation_id = gen_random_uuid()
WHERE generation_id IS NULL;

ALTER TABLE production_control.machine_load_snapshots
    ALTER COLUMN generation_id SET NOT NULL;

COMMENT ON COLUMN production_control.machine_load_snapshots.generation_id IS
    'Identifica a geração do refresh que originou a fila WORKING; muda a cada POST /machine-load/refresh, nunca em update_payload.';

CREATE TABLE IF NOT EXISTS production_control.machine_load_publications (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    branch                VARCHAR(2)   NOT NULL,
    generation_id         UUID         NOT NULL,
    start_date            DATE         NOT NULL,
    end_date              DATE         NOT NULL,
    payload_json          JSONB        NOT NULL,
    schema_version        SMALLINT     NOT NULL DEFAULT 1,
    source                VARCHAR(40)  NOT NULL DEFAULT 'api-delpi',
    source_refreshed_at   TIMESTAMPTZ  NOT NULL,
    source_refreshed_by   VARCHAR(120) NULL,
    published_at          TIMESTAMPTZ  NOT NULL,
    published_by          VARCHAR(120) NULL,

    CONSTRAINT uq_pc_machine_load_publications_branch UNIQUE (branch)
);

COMMENT ON TABLE production_control.machine_load_publications IS
    'Fila PUBLISHED da carga máquina: uma publicação atual por filial, cópia durável da geração enviada às bancadas. Independe do WORKING (sem FK de geração).';

COMMENT ON COLUMN production_control.machine_load_publications.source_refreshed_at IS
    'Quando o TOTVS foi atualizado (refreshed_at do WORKING no momento da publicação) — fato distinto de published_at.';

COMMENT ON COLUMN production_control.machine_load_publications.published_at IS
    'Quando a fila foi enviada às bancadas. No backfill inicial não existe histórico de publicação, então deriva de refreshed_at.';

-- Backfill: cada fila WORKING existente vira a publicação vigente, preservando
-- geração, payload e metadados — nenhuma bancada perde a fila no deploy.
INSERT INTO production_control.machine_load_publications (
    branch,
    generation_id,
    start_date,
    end_date,
    payload_json,
    schema_version,
    source,
    source_refreshed_at,
    source_refreshed_by,
    published_at,
    published_by
)
SELECT
    branch,
    generation_id,
    start_date,
    end_date,
    payload_json,
    schema_version,
    source,
    refreshed_at,
    refreshed_by,
    refreshed_at,
    refreshed_by
FROM production_control.machine_load_snapshots
ON CONFLICT (branch) DO NOTHING;

COMMIT;
