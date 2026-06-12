-- Transformômetro — revisoes.instancia_id + backfill estrutural a partir de processos legados
BEGIN;

ALTER TABLE transformometro.revisoes
    ADD COLUMN IF NOT EXISTS instancia_id UUID;

INSERT INTO transformometro.processo_instancias (processo_id, filial_id, setor_id)
SELECT p.processo_id, f.filial_id, s.setor_id
FROM transformometro.processos p
JOIN transformometro.filiais f ON f.codigo_filial = p.filial_id AND f.deletado = FALSE
JOIN transformometro.setores s ON s.codigo_setor = p.setor_id AND s.deletado = FALSE
WHERE p.deletado = FALSE
ON CONFLICT (processo_id, filial_id, setor_id) DO NOTHING;

UPDATE transformometro.revisoes r
SET instancia_id = pi.instancia_id
FROM transformometro.processos p
JOIN transformometro.processo_instancias pi ON pi.processo_id = p.processo_id AND pi.deletado = FALSE
WHERE r.processo_id = p.processo_id
  AND r.instancia_id IS NULL
  AND r.deletado = FALSE;

ALTER TABLE transformometro.revisoes
    ADD CONSTRAINT fk_revisoes_instancia
        FOREIGN KEY (instancia_id)
        REFERENCES transformometro.processo_instancias (instancia_id);

CREATE INDEX IF NOT EXISTS idx_revisoes_instancia
    ON transformometro.revisoes (instancia_id)
    WHERE deletado = FALSE;

COMMIT;
