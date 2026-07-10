# Docker — plugins com bibliotecas compartilhadas

## Problema que este padrão evita

Plugins MFE importam pacotes irmãos via alias Vite ou Module Federation. O build local funciona porque `plugins/` está completo no disco. O **Docker** só enxerga o que o `Dockerfile` copia — esquecer uma pasta quebra o `vite build` no CI/produção.

## `@delpi/plugin-ui` — Module Federation (padrão obrigatório)

**Todo MFE novo** consome `@delpi/plugin-ui` como remote runtime — rollout concluído (jul/2026).

| Aspecto | Detalhe |
|---------|---------|
| Container | `delpi-plugin-ui` (nginx:alpine) |
| Remote | `/apps/plugin-ui/assets/remoteEntry.js` |
| Consumidor | `remotes: pluginUiRemote()` + `await preparePluginUiRemote()` — **sem** `COPY plugin-ui` |
| Checklist | [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md) |
| Doc MF | [plugin-ui/docs/module-federation.md](../plugin-ui/docs/module-federation.md) |

```bash
docker compose -f infra/docker-compose.dev.yml --profile plugins up -d plugin-ui meu-plugin
```

Helpers: [`plugins/vite/federation.shared.ts`](../vite/federation.shared.ts) · [`plugins/vite/federationShareScope.ts`](../vite/federationShareScope.ts)

Compose: usar anchor `<<: *plugin-ui-federated` (inclui `depends_on: plugin-ui`).

## Modo bundled (legado) — COPY / shared builder

Apenas **`@delpi/tv-dashboard-presentation`** permanece bundled (`public-hub`, `tv-dashboard`).

### Problema de RAM no build

Com `up --build` em massa, repetir `npm install` da lib bundled multiplica memória e tempo.

| Abordagem | Runtime | Build |
|-----------|---------|-------|
| COPY por Dockerfile | OK | N× npm install |
| **`delpi-plugins-shared-builder:local`** | OK | 1× npm install (tv-dashboard-presentation) |

```bash
./infra/scripts/build-plugins-shared-base.sh
export COMPOSE_PARALLEL_LIMIT=2
docker compose -f infra/docker-compose.dev.yml --profile plugins build dashboard-production
```

Compose (profile `build-base`):

```yaml
plugins-shared-builder:
  image: delpi-plugins-shared-builder:local
  build:
    context: ../plugins
    dockerfile: docker/Dockerfile.shared-libs-builder
```

## Regras

1. **Manifesto canônico:** [`shared-libraries.manifest.json`](../shared-libraries.manifest.json) — `consumptionMode`: `federation-remote` ou `bundled`.
2. **Contexto Compose:** `context: ../plugins` (raiz `plugins/`), não o subdiretório do plugin isolado.
3. **Dockerfile bundled:** `FROM delpi-plugins-shared-builder:local` **ou** `COPY <biblioteca>/`.
4. **Dockerfile federado:** `COPY vite ./vite` + `remotes` em `vite.config.ts` — **sem** COPY de `plugin-ui`.
5. **Gate CI:** `scripts/ci/check_plugin_docker_shared_libraries.py --check`.

## Referências

| Artefato | Uso |
|----------|-----|
| [`Dockerfile.shared-libs-builder`](./Dockerfile.shared-libs-builder) | Build bundled (`tv-dashboard-presentation` apenas) |
| [`Dockerfile.plugin.mfe`](./Dockerfile.plugin.mfe) | Template MFE com shared builder |
| [`controle-retrabalhos/Dockerfile`](../controle-retrabalhos/Dockerfile) | Piloto MF (sem plugin-ui no build) |
| [`plugin-ui/Dockerfile`](../plugin-ui/Dockerfile) | Remote runtime |

## Novo consumidor de `@delpi/plugin-ui`

**Obrigatório: Module Federation** — seguir [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md).

Legado bundled (`COPY plugin-ui`) **não** é mais aceito para MFEs novos.

## Nova biblioteca compartilhada

1. Criar pasta em `plugins/nome-biblioteca/`.
2. Registrar em `shared-libraries.manifest.json` (`directory`, `markers`, `consumptionMode`).
3. Bundled: incluir em `Dockerfile.shared-libs-builder`.
4. Rebuild shared base se bundled.
5. Documentar README da biblioteca.
