-- Transformômetro — setores com PK UUID + codigo_setor; setor_filiais com FKs UUID
-- Backfill estrutural de filiais referenciadas (não é seed de catálogo novo).
BEGIN;

INSERT INTO transformometro.filiais (codigo_filial, nome_filial)
SELECT DISTINCT src.codigo_filial, src.nome_filial
FROM (
    SELECT sf.filial_id AS codigo_filial,
           CASE sf.filial_id
               WHEN '01' THEN 'Matriz'
               WHEN '02' THEN 'Filial'
               ELSE sf.filial_id
           END AS nome_filial
    FROM transformometro.setor_filiais sf
    UNION
    SELECT p.filial_id AS codigo_filial,
           CASE p.filial_id
               WHEN '01' THEN 'Matriz'
               WHEN '02' THEN 'Filial'
               ELSE p.filial_id
           END AS nome_filial
    FROM transformometro.processos p
    WHERE p.filial_id IS NOT NULL AND p.filial_id <> ''
) AS src
WHERE src.codigo_filial IS NOT NULL
  AND src.codigo_filial <> ''
  AND NOT EXISTS (
      SELECT 1
      FROM transformometro.filiais f
      WHERE f.codigo_filial = src.codigo_filial
  );

ALTER TABLE transformometro.setores
    ADD COLUMN IF NOT EXISTS codigo_setor VARCHAR(64);

UPDATE transformometro.setores
SET codigo_setor = setor_id
WHERE codigo_setor IS NULL OR codigo_setor = '';

ALTER TABLE transformometro.setores
    ADD COLUMN IF NOT EXISTS setor_uuid UUID;

UPDATE transformometro.setores
SET setor_uuid = gen_random_uuid()
WHERE setor_uuid IS NULL;

ALTER TABLE transformometro.setores
    ALTER COLUMN setor_uuid SET NOT NULL,
    ALTER COLUMN codigo_setor SET NOT NULL;

ALTER TABLE transformometro.setores
    DROP CONSTRAINT IF EXISTS uq_setores_uuid_migration;

ALTER TABLE transformometro.setores
    ADD CONSTRAINT uq_setores_uuid_migration UNIQUE (setor_uuid);

DROP TABLE IF EXISTS transformometro.setor_filiais_new;

CREATE TABLE transformometro.setor_filiais_new (
    setor_id UUID NOT NULL,
    filial_id UUID NOT NULL,
    PRIMARY KEY (setor_id, filial_id),
    CONSTRAINT fk_setor_filiais_setor
        FOREIGN KEY (setor_id)
        REFERENCES transformometro.setores (setor_uuid)
        ON DELETE CASCADE,
    CONSTRAINT fk_setor_filiais_filial
        FOREIGN KEY (filial_id)
        REFERENCES transformometro.filiais (filial_id)
        ON DELETE CASCADE
);

INSERT INTO transformometro.setor_filiais_new (setor_id, filial_id)
SELECT s.setor_uuid, f.filial_id
FROM transformometro.setor_filiais sf
JOIN transformometro.setores s ON s.setor_id = sf.setor_id
JOIN transformometro.filiais f ON f.codigo_filial = sf.filial_id
ON CONFLICT DO NOTHING;

DROP TABLE transformometro.setor_filiais;
ALTER TABLE transformometro.setor_filiais_new RENAME TO setor_filiais;

CREATE INDEX IF NOT EXISTS idx_setor_filiais_filial
    ON transformometro.setor_filiais (filial_id);

ALTER TABLE transformometro.setores DROP CONSTRAINT setores_pkey;
ALTER TABLE transformometro.setores DROP COLUMN setor_id;
ALTER TABLE transformometro.setores RENAME COLUMN setor_uuid TO setor_id;
ALTER TABLE transformometro.setores DROP CONSTRAINT IF EXISTS uq_setores_uuid_migration;
ALTER TABLE transformometro.setores ADD PRIMARY KEY (setor_id);
ALTER TABLE transformometro.setores
    ADD CONSTRAINT uq_setores_codigo_setor UNIQUE (codigo_setor);

COMMIT;
