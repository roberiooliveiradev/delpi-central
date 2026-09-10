BEGIN;

-- Campos marcados na devolução (needs_information). Limpos no resubmit.
ALTER TABLE my_requests.requests
    ADD COLUMN IF NOT EXISTS correction_targets TEXT[] NOT NULL DEFAULT '{}';

COMMENT ON COLUMN my_requests.requests.correction_targets IS
    'Chaves de campos/seções a corrigir após return; vazio quando não aplicável.';

COMMIT;
