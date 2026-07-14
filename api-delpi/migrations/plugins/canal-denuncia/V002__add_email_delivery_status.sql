-- Canal de Denúncia — status de entrega de e-mail (Microsoft Graph)

ALTER TABLE canal_denuncia.denuncias
    ADD COLUMN IF NOT EXISTS email_status TEXT NOT NULL DEFAULT 'pending',
    ADD COLUMN IF NOT EXISTS email_attempts INTEGER NOT NULL DEFAULT 0,
    ADD COLUMN IF NOT EXISTS email_last_error TEXT NULL,
    ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMPTZ NULL,
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'ck_canal_denuncia_email_status'
          AND conrelid = 'canal_denuncia.denuncias'::regclass
    ) THEN
        ALTER TABLE canal_denuncia.denuncias
            ADD CONSTRAINT ck_canal_denuncia_email_status
            CHECK (email_status IN ('pending', 'sent', 'failed'));
    END IF;
END $$;
