-- Delpi Remote G1-OWNER: vinculo opcional a identidade canonica do usuario Core.
-- V010 aditiva: preserva responsible textual legado e auditoria anteriores.
-- Core e banco independente: sem FK externa entre bancos.
ALTER TABLE it_portal.workstations
    ADD COLUMN responsible_user_id UUID;

COMMENT ON COLUMN it_portal.workstations.responsible_user_id IS
    'ID canonico do usuario ativo no Core, validado na atribuicao; NULL para uso compartilhado ou legado.';

CREATE INDEX workstations_responsible_user_idx
    ON it_portal.workstations (responsible_user_id)
    WHERE responsible_user_id IS NOT NULL;
