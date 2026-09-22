# E4 — M-23 menção @ (regressão + evidência)

Data: 22/09/2026

| Caso | Resultado | Evidência |
|---|---|---|
| Kit: `@An` abre query | PASS | `richTextUserMention.test.ts` + `RichTextEditor.test.tsx` |
| Kit: insert `data-user-id` | PASS | mesmo |
| Kit negativo: `@` no meio da palavra | PASS | `detectActiveMention("email@An")` → null |
| Kit sibling: segundo `@` | PASS | `Oi @Ana @Br` |
| Sanitizer: span numérico preservado | PASS | `prepare_outbound_message_html` no container `delpi-helpdesk-api` |
| Sanitizer negativo: `data-user-id=abc` strip | PASS | mesmo |
| Sibling ids 10/20 | PASS | mesmo |
| Structural MFE enableMentions + listUsers | PASS | `HelpdeskListUx.structural.test.ts` |
| Help tooltips `@` | PASS | `helpTooltips.test.ts` |

Live UI Colaborador (create/reply → chip M-07): após deploy remote→mfe (E5).
Smoke deploy 22/09/2026: `delpi-plugin-ui` + `delpi-helpdesk` Up; `remoteEntry.js` 200; bundle kit contém `data-user-mention`; MFE contém `enableMentions`. Hard refresh em `/apps/helpdesk` para validar `@` no create/reply.
