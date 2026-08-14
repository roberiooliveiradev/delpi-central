-- Contatos do perfil Commercial (telefone / celular / WhatsApp).

ALTER TABLE commercial.commercial_user_profiles
    ADD COLUMN IF NOT EXISTS phone_e164 TEXT,
    ADD COLUMN IF NOT EXISTS mobile_e164 TEXT,
    ADD COLUMN IF NOT EXISTS whatsapp_e164 TEXT;
