-- PRC-CONVERSATION FIX-03 — mensagem composta só por anexos (Issue
-- #207). A invariante passa a ser "texto não vazio OU pelo menos um
-- anexo válido" — garantia aplicada no caso de uso (criação composta
-- valida todos os arquivos antes de inserir; edição/remoção de anexo
-- não pode deixar a mensagem vazia). No banco, o corpo canônico para
-- mensagem só-anexo é string vazia exata; corpos whitespace-only
-- continuam rejeitados.

ALTER TABLE engineering.product_registration_comments
    DROP CONSTRAINT prc_comment_body_nonempty;

ALTER TABLE engineering.product_registration_comments
    ADD CONSTRAINT prc_comment_body_nonempty CHECK (
        body = '' OR length(btrim(body)) > 0
    );

COMMENT ON CONSTRAINT prc_comment_body_nonempty
    ON engineering.product_registration_comments IS
    'PRC-CONVERSATION FIX-03: body vazio só é canônico quando a mensagem carrega anexos — invariante aplicada no use case (sem comentário vazio definitivo).';
