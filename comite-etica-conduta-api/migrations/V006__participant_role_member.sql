-- Papéis do comitê corporativo (`member`) + aliases legados da CIPA.
BEGIN;

ALTER TABLE comite_etica.meeting_minute_participants
    DROP CONSTRAINT IF EXISTS meeting_minute_participants_role_in_meeting_check;

ALTER TABLE comite_etica.meeting_minute_participants
    ADD CONSTRAINT meeting_minute_participants_role_in_meeting_check
    CHECK (role_in_meeting IN (
        'president',
        'secretary',
        'member',
        'guest',
        'other',
        'vice_president',
        'titular_member',
        'alternate_member',
        'action_owner'
    ));

COMMIT;
