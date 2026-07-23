BEGIN;

ALTER TABLE maintenance.programas_maquina_produtos
    ADD COLUMN IF NOT EXISTS descricao_intermediario VARCHAR(255),
    ADD COLUMN IF NOT EXISTS data_ativacao TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS usuario_ativacao_nome VARCHAR(200),
    ADD COLUMN IF NOT EXISTS usuario_ativacao_sub TEXT;

COMMENT ON COLUMN maintenance.programas_maquina_produtos.descricao_intermediario IS
    'Descrição do intermediário (snapshot no cadastro / ativação).';
COMMENT ON COLUMN maintenance.programas_maquina_produtos.data_ativacao IS
    'Momento da última ativação do produto no cadastro de programas.';
COMMENT ON COLUMN maintenance.programas_maquina_produtos.usuario_ativacao_nome IS
    'Nome de exibição de quem ativou o produto no programa.';

UPDATE maintenance.programas_maquina_produtos
SET
    data_ativacao = COALESCE(data_ativacao, data_criacao),
    usuario_ativacao_sub = COALESCE(usuario_ativacao_sub, usuario_sub)
WHERE excluido = FALSE
  AND data_ativacao IS NULL;

COMMIT;
