# Config SearXNG

Os arquivos em `infra/searxng/` são montados no container com volume **rw** e podem ser sobrescritos pelo processo (root). Não versionar `settings.yml` / `limiter.toml`.

**Primeiro deploy ou após clone:**

```bash
mkdir -p infra/searxng
cp infra/config/searxng/settings.yml.example infra/searxng/settings.yml
cp infra/config/searxng/limiter.toml.example infra/searxng/limiter.toml
# Produção: defina SEARXNG_SECRET no .env (sobrescreve secret_key do YAML)
```

Ou rode `infra/scripts/searxng-apply-dev-settings.sh` com o container em execução.
