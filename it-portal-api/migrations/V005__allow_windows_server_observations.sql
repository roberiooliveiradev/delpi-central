-- E4.S3 - Autoriza a origem Windows nas observacoes automaticas do Portal de TI.
-- A V004 ja aplicada permanece imutavel (checksum do runner).
-- Mantem a origem Linux e todas as observacoes existentes.
-- Executada atomicamente pelo runner de migrations do it-portal-api.

ALTER TABLE it_portal.server_observations
    DROP CONSTRAINT server_observations_source_chk;

ALTER TABLE it_portal.server_observations
    ADD CONSTRAINT server_observations_source_chk
    CHECK (source IN ('linux_host_collector', 'windows_host_collector'));
