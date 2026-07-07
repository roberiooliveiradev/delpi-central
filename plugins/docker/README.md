# Docker — plugins com bibliotecas compartilhadas

## Problema que este padrão evita

Plugins MFE importam pacotes irmãos via alias Vite (`@delpi/plugin-ui`, `@delpi/tv-dashboard-presentation`).  
O build local funciona porque `plugins/` está completo no disco. O **Docker** só enxerga o que o `Dockerfile` copia — esquecer uma pasta quebra o `vite build` no CI/produção.

## Regras

1. **Manifesto canônico:** [`shared-libraries.manifest.json`](../shared-libraries.manifest.json) — pastas, markers de import e contexto obrigatório.
2. **Contexto Compose:** `context: ../plugins` (raiz `plugins/`), não o subdiretório do plugin isolado.
3. **Dockerfile:** `COPY <biblioteca>/` + `npm install` para cada dependência detectada.
4. **Gate CI:** `scripts/ci/check_plugin_docker_shared_libraries.py` — falha se consumidor não declarar `COPY`.

## Fragmento pronto

[`shared-libraries.Dockerfile.fragment`](./shared-libraries.Dockerfile.fragment)

Referência completa: [`tv-dashboard/Dockerfile`](../tv-dashboard/Dockerfile).

## Novo consumidor de `@delpi/plugin-ui`

1. Alias em `vite.config.ts` + `import "../../plugin-ui/src/styles.css"` no `main.tsx`.
2. Adicionar bloco `COPY plugin-ui` no `Dockerfile` (ou usar fragmento).
3. Confirmar `context: ../plugins` no `infra/docker-compose*.yml`.
4. Rodar:

```bash
python3 scripts/ci/check_plugin_docker_shared_libraries.py --check
cd plugins/meu-plugin && npm run build
```

## Nova biblioteca compartilhada

1. Criar pasta em `plugins/nome-biblioteca/`.
2. Registrar entrada em `shared-libraries.manifest.json` (`directory`, `markers`).
3. Documentar em `plugins/nome-biblioteca/README.md`.
4. Atualizar gate se necessário (markers bastam na maioria dos casos).
