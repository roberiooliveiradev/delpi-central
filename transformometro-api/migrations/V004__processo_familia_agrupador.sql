-- Fase 4: agrupamento por família / ferramenta para rateio e relatórios
BEGIN;

ALTER TABLE transformometro.processos
    ADD COLUMN IF NOT EXISTS familia_processo VARCHAR(64),
    ADD COLUMN IF NOT EXISTS agrupador_ferramenta VARCHAR(128);

CREATE INDEX IF NOT EXISTS idx_processos_familia
    ON transformometro.processos (familia_processo)
    WHERE deletado = FALSE AND familia_processo IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_processos_agrupador
    ON transformometro.processos (agrupador_ferramenta)
    WHERE deletado = FALSE AND agrupador_ferramenta IS NOT NULL;

COMMIT;
