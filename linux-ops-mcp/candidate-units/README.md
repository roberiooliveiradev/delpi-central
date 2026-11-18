# ATLAS HML candidate systemd units (NOT installed by deploy)

These files are **candidates for future authorized installation** on `srv-api`.

- Extension: `.candidate` (never `.service` / `.socket` / `.timer` in this tree).
- Every unit includes `RefuseManualStart=yes` and an impossible `ConditionPathExists`.
- No `[Install]` section. Deploy scripts MUST NOT copy these into `/etc/systemd/system`.
- `review-only/*.review` remain the lexical non-runnable blueprints; this tree is the
  separate candidate area required by Etapa 68.
- Activation requires explicit owner authorization, change-control, and host evidence.

`ExecStart` paths below are **placeholders** reviewed as design intent. They do not
become operational until a later authorized packaging step replaces `/usr/bin/false`
or a pinned wrapper under owner change-control.
