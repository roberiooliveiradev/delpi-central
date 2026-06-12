BEGIN;

DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'maintenance'
          AND table_name = 'motivos'
          AND column_name = 'motivo_id'
          AND data_type = 'integer'
    ) THEN
        ALTER TABLE maintenance.reposicoes
            DROP CONSTRAINT IF EXISTS reposicoes_motivo_id_fkey;

        ALTER TABLE maintenance.motivos
            ADD COLUMN motivo_id_uuid UUID;

        UPDATE maintenance.motivos
        SET motivo_id_uuid = gen_random_uuid()
        WHERE motivo_id_uuid IS NULL;

        ALTER TABLE maintenance.reposicoes
            ADD COLUMN motivo_id_uuid UUID;

        UPDATE maintenance.reposicoes r
        SET motivo_id_uuid = m.motivo_id_uuid
        FROM maintenance.motivos m
        WHERE m.motivo_id = r.motivo_id;

        ALTER TABLE maintenance.reposicoes
            DROP COLUMN motivo_id;

        ALTER TABLE maintenance.reposicoes
            RENAME COLUMN motivo_id_uuid TO motivo_id;

        ALTER TABLE maintenance.reposicoes
            ALTER COLUMN motivo_id SET NOT NULL;

        ALTER TABLE maintenance.motivos
            DROP CONSTRAINT motivos_pkey;

        ALTER TABLE maintenance.motivos
            DROP COLUMN motivo_id;

        ALTER TABLE maintenance.motivos
            RENAME COLUMN motivo_id_uuid TO motivo_id;

        ALTER TABLE maintenance.motivos
            ADD PRIMARY KEY (motivo_id);

        ALTER TABLE maintenance.motivos
            ALTER COLUMN motivo_id SET DEFAULT gen_random_uuid();

        ALTER TABLE maintenance.reposicoes
            ADD CONSTRAINT reposicoes_motivo_id_fkey
                FOREIGN KEY (motivo_id) REFERENCES maintenance.motivos (motivo_id);
    END IF;

    IF EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_schema = 'maintenance'
          AND table_name = 'status_peca'
          AND column_name = 'status_id'
          AND data_type = 'integer'
    ) THEN
        ALTER TABLE maintenance.status_peca
            ADD COLUMN status_id_uuid UUID;

        UPDATE maintenance.status_peca
        SET status_id_uuid = gen_random_uuid()
        WHERE status_id_uuid IS NULL;

        ALTER TABLE maintenance.status_peca
            DROP CONSTRAINT status_peca_pkey;

        ALTER TABLE maintenance.status_peca
            DROP COLUMN status_id;

        ALTER TABLE maintenance.status_peca
            RENAME COLUMN status_id_uuid TO status_id;

        ALTER TABLE maintenance.status_peca
            ADD PRIMARY KEY (status_id);

        ALTER TABLE maintenance.status_peca
            ALTER COLUMN status_id SET DEFAULT gen_random_uuid();
    END IF;
END $$;

COMMIT;
