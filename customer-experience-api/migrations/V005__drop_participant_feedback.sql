-- Remove o feedback antigo atrelado ao participante. O feedback passa a ser
-- coletado pelo módulo de Formulários (estilo Google Forms), independente do
-- fluxo de agradecimento.
DROP TABLE IF EXISTS customer_experience.feedback;

ALTER TABLE customer_experience.participants
    DROP COLUMN IF EXISTS feedback_qr_filename;
