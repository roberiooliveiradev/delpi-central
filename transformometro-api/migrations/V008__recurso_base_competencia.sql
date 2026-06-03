BEGIN;

ALTER TABLE transformometro.recursos_compartilhados
    ADD COLUMN IF NOT EXISTS base_competencia VARCHAR(30) NOT NULL DEFAULT 'mensal_cheio';

ALTER TABLE transformometro.recursos_compartilhados
    DROP CONSTRAINT IF EXISTS chk_recursos_compartilhados_base_competencia;

ALTER TABLE transformometro.recursos_compartilhados
    ADD CONSTRAINT chk_recursos_compartilhados_base_competencia
    CHECK (base_competencia IN ('mensal_cheio', 'proporcional_dias'));

COMMENT ON COLUMN transformometro.recursos_compartilhados.base_competencia IS
    'Define como o custo mensal do recurso entra na competência: mensal_cheio ou proporcional_dias.';

COMMIT;
