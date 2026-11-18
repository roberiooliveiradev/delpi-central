# ATLAS HML packaging-review — NOT INSTALLABLE

**AUTHORIZED_INSTALL_ONLY** — these wrappers are review artifacts for a future
owner-authorized installation window. They are deliberately separate from
`candidate-units/*.candidate`, which remain non-installable (`RefuseManualStart`,
impossible `ConditionPathExists`, `ExecStart=/usr/bin/false`).

## Rules

- Never copy these files into `/etc/systemd/system` from CI or deploy scripts.
- Entrypoints require `--disposable-fixture` and `ATLAS_HML_RUNTIME_MODE=disposable-fixture`.
- Host mode is denied. PREPARE/ACT remain OFF.
- Passing local tests is not srv-api attestation.
