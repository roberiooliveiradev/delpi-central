# ATLAS HML pilot activation checklist — REVIEW ONLY

**NOT AUTHORIZATION.** Completing this checklist does not install units,
enable PREPARE/ACT, or authorize srv-api changes.

## Preconditions
- [ ] PR #283 merged (Etapa 74) and boot/packaging package merged
- [ ] DELPI Verifier ACCEPT / ACCEPT_WITH_RESIDUAL on exact SHA
- [ ] CI SUCCESS on exact SHA
- [ ] Owner operational window, commands, baseline and rollback approved in writing

## Host preflight (authorized observation only)
- [ ] Stage74/76 classified tmpfiles audit + Stage75 gate (fixture then `--host-readonly`)
- [ ] Critical tmpfiles codes empty; info-class OS baselines documented
- [ ] No conflicting tmpfiles / ATLAS units already present
- [ ] Identities atlas-hml / bridge / signer present; no docker primary group
- [ ] DAC/ACL/setgid match policy; reject if tmpfiles success left drift

## Install sequence (only after written authorization)
1. Backup inventory of ATLAS-only paths and absence of units
2. Install reviewed tmpfiles `.conf` derived from candidate (create-only)
3. Re-run post-create validation; STOP on any DRIFT
4. Install candidate units only after ExecStart packaging authorization
5. Start signer then bridge under identities; never root for signer
6. Validate socket 0660, peer UID/GID, signed snapshot, continuity
7. PROD health before/after observation (read-only)

## STOP conditions
- DIRECTORY_POLICY_MISMATCH
- DOCKER_ENGINE_IMPACT
- NON_ATLAS_SERVICE_IMPACT
- SIGNER_PEER_AUTH_FAILURE
- CONTINUITY_REGRESSION
- OWNER_WINDOW_MISSING

## Rollback
Remove only ATLAS-only components listed by stage75 inventory; never touch shared Docker/PROD units.
