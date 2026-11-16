# DEV env unblock (DAVI)

`delpi-api-delpi` was unhealthy due to checksum divergence on
`api-delpi/migrations/plugins/engineering/V024__prc_record_flags.sql`.

Live `engineering.schema_migrations` V024 checksum =
`8f9c975396366117722a4f1a48c86217902a41fc54c3318eb95d607cad0cf73e`.

HEAD had been rewritten to `817a70…` by commit `3a95d6a3e7` (incorrect
restore). File restored to applied content from `e94e3f9989`; local
`docker restart delpi-api-delpi` → healthy; DAVI catalog 4 capabilities.

Not a production deploy. No DB checksum mutation.
