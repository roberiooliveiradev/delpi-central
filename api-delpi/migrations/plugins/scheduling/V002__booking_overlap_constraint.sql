-- Impede reservas confirmadas sobrepostas no mesmo recurso (concorrência segura).

CREATE EXTENSION IF NOT EXISTS btree_gist;

ALTER TABLE scheduling.bookings
    DROP CONSTRAINT IF EXISTS ex_scheduling_bookings_no_overlap;

ALTER TABLE scheduling.bookings
    ADD CONSTRAINT ex_scheduling_bookings_no_overlap
    EXCLUDE USING gist (
        resource_id WITH =,
        tstzrange(start_at, end_at, '[)') WITH &&
    )
    WHERE (status = 'confirmed');
