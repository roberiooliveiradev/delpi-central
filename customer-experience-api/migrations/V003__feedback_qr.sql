-- QR próprio para a página pública de feedback (separada da página de agradecimento).
ALTER TABLE customer_experience.participants
    ADD COLUMN IF NOT EXISTS feedback_qr_filename TEXT;
