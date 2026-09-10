# Conteúdo compartilhado com a API

| Arquivo local | Origem na API |
|---------------|---------------|
| `product_operational_content.json` | `minha-delpi-ai-api/app/content/pt-BR/assistant/product_operational_content.json` (sync remove `presentation.routeTitles` / `routeFraming` — MFE render-only) |
| `presentation_vocabulary.json` | `minha-delpi-ai-api/app/content/pt-BR/assistant/presentation_vocabulary.json` |
| `message_composer.json` | `minha-delpi-ai-api/app/content/pt-BR/assistant/message_composer.json` |

## Ajuda do admin (MFE)

| Arquivo | Uso |
|---------|-----|
| `adminHelpTooltips.ts` | Única fonte de Ajuda in-app do console admin e do Studio (`pages`, `fields`, `kpis`, `studio`, `shell`). Consumir com `getAdminHelp("fields.documents.search")` ou `ADMIN_HELP.pages.overview`. |
| `auditAdminHelpCoverage.mjs` | Gate estrutural: `helpHint`/`hint` em headers, campos nativos, KPIs e checkboxes. |

Após alterar o JSON na API, sincronize no MFE:

```bash
npm run sync:product-operational-content
npm run sync:presentation-vocabulary
npm run sync:message-composer-content
```

O build Docker usa apenas este arquivo local (sem dependência do monorepo no contexto da imagem).
