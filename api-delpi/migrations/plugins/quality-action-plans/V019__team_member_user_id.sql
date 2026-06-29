-- Vínculo opcional com usuário Delpi na equipe de análise 8D (Minha fila / notificações).

ALTER TABLE quality.quality_analysis_team_members
    ADD COLUMN IF NOT EXISTS member_user_id VARCHAR(100);

CREATE INDEX IF NOT EXISTS ix_quality_analysis_team_members_user
    ON quality.quality_analysis_team_members (member_user_id)
    WHERE member_user_id IS NOT NULL AND trim(member_user_id) <> '';
