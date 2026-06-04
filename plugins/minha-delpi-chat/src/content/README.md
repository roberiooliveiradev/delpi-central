# Conteúdo compartilhado com a API

`product_operational_content.json` é cópia de `minha-delpi-ai-api/app/content/pt-BR/assistant/product_operational_content.json`.

Após alterar o JSON na API, sincronize no MFE:

```bash
npm run sync:product-operational-content
```

O build Docker usa apenas este arquivo local (sem dependência do monorepo no contexto da imagem).
