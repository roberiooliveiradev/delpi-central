# E14 — Menção leitura (M-07) / park escrita (M-23)

> Evidência E14.S2. Complementa [`12-conteudo-da-mensagem.md`](../12-conteudo-da-mensagem.md) §15b.

| Item | Estado | Motivo |
|---|---|---|
| M-07 chip na bolha | **IMPLEMENTADO** | `enrichGlpiUserMentionSpans` no plugin-ui; BFF já allowlistava attrs |
| M-23 `@` no compositor | **BLOQUEADO** | sem path HLAPI de mencionáveis por **id**; proibido casar por nome; sem `MentionComposer` |

Não abrir UI de `@` até gate PROVEN + plano novo.
