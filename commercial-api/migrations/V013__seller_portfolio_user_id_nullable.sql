-- Carteira name-first: permite criar sem responsável (órfã).
-- O 1º usuário adicionado vira owner e preenche user_id (sync no UC/repo).
-- NÃO editar V001/V005 — só esta migration nova.

ALTER TABLE commercial.seller_portfolios
    ALTER COLUMN user_id DROP NOT NULL;
