-- Agendamento público (public-hub): flag + token opaco no recurso; contato do solicitante na reserva

ALTER TABLE scheduling.resources
    ADD COLUMN IF NOT EXISTS public_booking_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS public_token VARCHAR(64);

ALTER TABLE scheduling.bookings
    ADD COLUMN IF NOT EXISTS requester_email VARCHAR(320),
    ADD COLUMN IF NOT EXISTS requester_phone VARCHAR(40);

CREATE UNIQUE INDEX IF NOT EXISTS uq_scheduling_resources_public_token
    ON scheduling.resources (public_token)
    WHERE public_token IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_scheduling_resources_public_enabled
    ON scheduling.resources (public_booking_enabled)
    WHERE public_booking_enabled = TRUE AND active = TRUE;
