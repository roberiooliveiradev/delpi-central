# E14 — Menção leitura (M-07) / escrita (M-23)

> Evidência E14 (leitura) + M-23 (escrita). Complementa [`12-conteudo-da-mensagem.md`](../12-conteudo-da-mensagem.md).

| Item | Estado | Motivo |
|---|---|---|
| M-07 chip na bolha | **IMPLEMENTADO** | `enrichGlpiUserMentionSpans` no plugin-ui; BFF allowlista attrs |
| M-23 `@` no compositor | **IMPLEMENTADO** | `RichTextEditor` + `detectActiveMention` + `MentionMenu`; hits de `GET /users`; insert `span[data-user-mention][data-user-id]` (só dígitos). Create + reply via `HelpdeskRichTextField enableMentions`. Sem `MentionComposer` das salas. |

## Cadeia escrita (M-23)

```text
@query no RichTextEditor
  → onMentionQueryChange (debounce)
  → listUsers / GET /users
  → MentionMenu
  → insert span data-user-id
  → POST ticket/followup (sanitizer preserva attrs)
  → leitura M-07 chipa
```

Catálogo por id **PROVEN** em [`e0-assignee-gates.md`](./e0-assignee-gates.md).
