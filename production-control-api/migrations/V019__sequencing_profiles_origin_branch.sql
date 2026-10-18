-- V019 — Regras de Sequenciamento: filial de origem do perfil.
--
-- Perfis são catálogo global reutilizável, mas edição exige autorização numa
-- filial afetada: a filial de origem ou uma filial onde o perfil está
-- vinculado. Sem esta coluna não é possível decidir quem edita um perfil
-- ainda não vinculado (proteção cross-branch).
--
-- Aditiva sobre V018 (já aplicada — intocável). Linhas legadas ficam com
-- origin_branch NULL: só voltam a ser editáveis após vínculo, que concede
-- autorização à filial do vínculo.

ALTER TABLE production_control.sequencing_profiles
    ADD COLUMN origin_branch TEXT;

ALTER TABLE production_control.sequencing_profiles
    ADD CONSTRAINT sequencing_profiles_origin_branch_check
    CHECK (origin_branch IS NULL OR origin_branch IN ('01', '02'));
