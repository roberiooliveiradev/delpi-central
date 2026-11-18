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

## Etapa 70: DAC estrito do signer

O diretorio `/run/atlas-hml-signer-socket` tera owner `atlas-hml-signer`, grupo `atlas-hml-bridge`, modo **02750** (setgid). O processo signer cria `sign.sock` somente apos tornar-se nao-root; o socket herda GID `atlas-hml-bridge` e usa modo `0660`, sem `chown` ou fallback para GID primario. O grupo bridge nao tem permissao de escrita no diretorio. Chave e estado continuam separados. Estes arquivos permanecem nao instalaveis.

## Etapa 74: criacao no boot sem reparo silencioso

As cinco entradas de layout tmpfiles usam o prefixo ':' nos campos mode,
user e group. O systemd-tmpfiles os aplica apenas a inodes recem-criados,
nao altera permissao ou dono de diretorios ja existentes. Isso nao garante
que o serviço seja impedido de iniciar: a validacao posterior por FD, ACL e
identidades permanece obrigatoria e falha fechada. A configuracao .candidate
nao tem extensao .conf nem esta instalada no sistema. Nao executar
systemd-tmpfiles no srv-api sem autorizacao operacional especifica.
