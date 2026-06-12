BEGIN;

CREATE OR REPLACE VIEW maintenance.vw_motivos_ativos AS
SELECT
    motivo_id,
    descricao,
    filial,
    excluir_preventiva,
    data_criacao,
    data_alteracao
FROM maintenance.motivos
WHERE excluido = FALSE;

CREATE OR REPLACE VIEW maintenance.vw_status_peca_ativos AS
SELECT
    status_id,
    descricao,
    operador,
    percentual,
    filial,
    data_criacao,
    data_alteracao
FROM maintenance.status_peca
WHERE excluido = FALSE;

CREATE OR REPLACE VIEW maintenance.vw_reposicoes_detalhe AS
SELECT
    r.reposicao_id,
    r.filial,
    r.codigo_ferramenta,
    r.codigo_peca,
    r.data_reposicao,
    r.data_ultima_reposicao,
    r.golpes,
    r.motivo_id,
    m.descricao AS motivo_descricao,
    m.excluir_preventiva,
    r.observacao,
    r.data_criacao,
    r.data_alteracao
FROM maintenance.reposicoes r
INNER JOIN maintenance.motivos m
    ON m.motivo_id = r.motivo_id
   AND m.excluido = FALSE
WHERE r.excluido = FALSE;

CREATE OR REPLACE VIEW maintenance.vw_reposicoes_preventiva AS
SELECT
    r.reposicao_id,
    r.filial,
    r.codigo_ferramenta,
    r.codigo_peca,
    r.data_reposicao,
    r.data_ultima_reposicao,
    r.golpes,
    r.motivo_id
FROM maintenance.reposicoes r
INNER JOIN maintenance.motivos m
    ON m.motivo_id = r.motivo_id
   AND m.excluido = FALSE
   AND m.excluir_preventiva = FALSE
WHERE r.excluido = FALSE;

CREATE OR REPLACE VIEW maintenance.vw_reposicoes_ultima_por_par AS
SELECT DISTINCT ON (filial, codigo_ferramenta, codigo_peca)
    reposicao_id,
    filial,
    codigo_ferramenta,
    codigo_peca,
    data_reposicao,
    golpes
FROM maintenance.vw_reposicoes_preventiva
ORDER BY filial, codigo_ferramenta, codigo_peca, data_reposicao DESC;

CREATE INDEX IF NOT EXISTS idx_reposicoes_ativas_filial_ferramenta_peca
    ON maintenance.reposicoes (filial, codigo_ferramenta, codigo_peca, data_reposicao DESC)
    WHERE excluido = FALSE;

COMMENT ON VIEW maintenance.vw_motivos_ativos IS
    'Motivos ativos por filial — listagens e selects de configuração.';
COMMENT ON VIEW maintenance.vw_status_peca_ativos IS
    'Regras de status preventivo ativas por filial.';
COMMENT ON VIEW maintenance.vw_reposicoes_detalhe IS
    'Reposições ativas com descrição do motivo — histórico da ferramenta.';
COMMENT ON VIEW maintenance.vw_reposicoes_preventiva IS
    'Reposições que entram no cálculo preventivo (motivo sem excluir_preventiva).';
COMMENT ON VIEW maintenance.vw_reposicoes_ultima_por_par IS
    'Última reposição preventiva por par filial/ferramenta/peça.';

COMMIT;
