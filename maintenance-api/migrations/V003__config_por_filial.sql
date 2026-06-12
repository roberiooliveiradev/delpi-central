BEGIN;

ALTER TABLE maintenance.motivos
    ADD COLUMN IF NOT EXISTS filial VARCHAR(2) NOT NULL DEFAULT '01'
        CHECK (filial IN ('01', '02'));

ALTER TABLE maintenance.status_peca
    ADD COLUMN IF NOT EXISTS filial VARCHAR(2) NOT NULL DEFAULT '01'
        CHECK (filial IN ('01', '02'));

INSERT INTO maintenance.motivos (descricao, filial)
SELECT m.descricao, '02'
FROM maintenance.motivos m
WHERE m.filial = '01'
  AND m.excluido = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM maintenance.motivos existing
      WHERE existing.filial = '02'
        AND existing.excluido = FALSE
        AND lower(existing.descricao) = lower(m.descricao)
  );

INSERT INTO maintenance.status_peca (descricao, operador, percentual, filial)
SELECT s.descricao, s.operador, s.percentual, '02'
FROM maintenance.status_peca s
WHERE s.filial = '01'
  AND s.excluido = FALSE
  AND NOT EXISTS (
      SELECT 1
      FROM maintenance.status_peca existing
      WHERE existing.filial = '02'
        AND existing.excluido = FALSE
        AND lower(existing.descricao) = lower(s.descricao)
  );

CREATE INDEX IF NOT EXISTS idx_motivos_filial_ativo
    ON maintenance.motivos (filial, descricao)
    WHERE excluido = FALSE;

CREATE INDEX IF NOT EXISTS idx_status_peca_filial_ativo
    ON maintenance.status_peca (filial, percentual DESC)
    WHERE excluido = FALSE;

COMMIT;
