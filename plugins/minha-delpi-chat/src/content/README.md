# Conteúdo compartilhado com a API

| Arquivo local | Origem na API |
|---------------|---------------|
| `product_operational_content.json` | `minha-delpi-ai-api/app/content/pt-BR/assistant/product_operational_content.json` |
| `presentation_vocabulary.json` | `minha-delpi-ai-api/app/content/pt-BR/assistant/presentation_vocabulary.json` |

Após alterar o JSON na API, sincronize no MFE:

```bash
npm run sync:product-operational-content
npm run sync:presentation-vocabulary
```

O build Docker usa apenas este arquivo local (sem dependência do monorepo no contexto da imagem).
