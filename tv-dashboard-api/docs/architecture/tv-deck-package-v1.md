# Pacote portátil MDD (Minha Delpi Deck) — v1.0

> **Padrão oficial** de exportação de programações e slides do Painéis TV.  
> Guia de produto / uso: [`docs/12-roadmap-e-evolucao/tv-dashboard/MDD-MINHA-DELPI-DECK.md`](../../../docs/12-roadmap-e-evolucao/tv-dashboard/MDD-MINHA-DELPI-DECK.md)

Formato canônico para exportar/importar uma **programação completa** (playlist + seções + slides + mídias + bindings) entre contas.

| | |
|--|--|
| **Sigla** | MDD |
| **Nome** | Minha Delpi Deck |
| **Extensão** | `.mdd` (conteúdo = ZIP) |
| **`format` no manifest** | `minha_delpi_deck` |

Importação ainda aceita o alias legado `delpi_tv_deck`.

PNG, PDF e PPTX (MVP) no editor são **exportações de consumo** do slide atual; **não** substituem o MDD como formato de interchange.

## Estrutura

```
manifest.json
deck/playlist.json
deck/sections.json
deck/slides.json
deck/media.json
deck/data_bindings_index.json
media/{sourceAssetId}{ext}
```

## `manifest.json`

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `format` | string | `minha_delpi_deck` (MDD) |
| `schemaVersion` | string | `1.0` |
| `source` | object | `{ playlistId, playlistName, exportedBy, exportedAt }` (informativo) |
| `entries` | object | `path → { sha256, size_bytes }` |
| `stats` | object | `{ slideCount, sectionCount, mediaCount, bindingCount }` |

Checksums cobrem todos os arquivos listados em `entries` (exceto o próprio `manifest.json`).

## `deck/playlist.json`

Metadados portáteis:

- `sourceId`, `name`, `description`
- `viewportProfile`, `transitionStyle`, `defaultDurationSec`, `globalRefreshSec`
- `dataDefaults`, `masterConfig`

**Omitidos:** `publicToken`, `ownerUserId`, `revision`, `viewCount`, `shares`, `history`, `isActive`.

## `deck/sections.json`

Array de seções com `sourceId`, `name`, `sortOrder`, `isCollapsed`, `isActive`, `isMain`, `defaultDurationSec`, `transitionStyle`, `masterConfig`.

## `deck/slides.json`

Array de slides com `sourceId`, `sourceSectionId`, `sortOrder`, `slideType`, `durationSec`, `title`, `nativeScreenKey`, `nativeConfig`, `externalUrl`, `externalSandbox`, `isActive`, `transitionStyle`.

IDs de bloco / `dataSourceId` no `nativeConfig` são preservados no pacote.

## `deck/media.json`

Índice de mídias referenciadas:

```json
[
  {
    "sourceAssetId": "uuid",
    "originalName": "logo.png",
    "mimeType": "image/png",
    "mediaKind": "image",
    "archivePath": "media/<uuid>.png"
  }
]
```

## `deck/data_bindings_index.json`

Lista de `{ operationId, params, slideSourceId, blockId, blockType }` para auditoria e preview.

## Importação

1. `POST /playlists/import/preview` — valida ZIP, checksums, schema e bindings.
2. `POST /playlists/import/apply` — cria playlist **inativa** com novos UUIDs; remapeia `sectionId` e `assetId`.

Política de binding:

- `lenient` (padrão): warnings de rota/param permitem apply.
- `strict`: qualquer binding inválido bloqueia apply.

## Segurança

- Anti zip-slip: apenas paths relativos seguros sob `deck/` e `media/`.
- Limite de tamanho: `TV_DECK_PACKAGE_MAX_BYTES` (default 500 MB).
- Volume de mídia: `TV_DASHBOARD_MEDIA_UPLOAD_DIR` (persistente no Compose).

## Uso por ferramentas de IA

O miolo é JSON texto + pasta `media/`. Descompactar o `.mdd` (ZIP), editar os JSON e reempacotar permite round-trip com assistentes e scripts.
