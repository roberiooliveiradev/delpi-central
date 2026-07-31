# MDD — Minha Delpi Deck

**Padrão oficial de exportação/importação de programações e slides** do Painéis TV.

| | |
|--|--|
| **Sigla** | MDD |
| **Nome** | Minha Delpi Deck |
| **Extensão** | `.mdd` (arquivo ZIP) |
| **Manifest `format`** | `minha_delpi_deck` |
| **Schema** | `1.0` |
| **Especificação técnica** | [`tv-dashboard-api/docs/architecture/tv-deck-package-v1.md`](../../../tv-dashboard-api/docs/architecture/tv-deck-package-v1.md) |

---

## Por que existe

O mercado (PPTX/OOXML, Figma, OPF) usa **pacote com manifest + JSON + binários** quando o objetivo é portabilidade fiel entre contas. PNG/PDF/PPTX no editor são **saídas de consumo**; o **MDD** é a **fonte de verdade portátil** da programação DELPI (slides, seções, mídias e bindings operacionais).

Use MDD quando precisar:

- copiar uma programação para **outra conta** Minha Delpi;
- arquivar / versionar um deck fora do banco;
- editar o conteúdo com **ferramentas de IA** ou scripts (JSON legível);
- reimportar com preview de conflitos (bindings, checksums).

---

## Formas de exportação no Painéis TV

| Formato | Escopo | Fidelidade nativa | Inter-conta | Editável por IA | Uso recomendado |
|--------|--------|-------------------|-------------|-----------------|-----------------|
| **MDD (`.mdd`)** | Programação completa (seções + slides + mídias + bindings) | Alta | Sim | Sim (ZIP → JSON) | **Padrão** de interchange / backup / template portátil |
| PNG | Slide atual (captura) | Visual | — | Não | Imagem / e-mail / mural |
| PDF | Slide atual (captura em página) | Visual | — | Não | Impressão / anexo |
| PPTX (MVP) | Slide atual (blocos básicos) | Parcial | Limitada | Parcial | Abrir no PowerPoint; **não** substitui MDD |

Duplicar playlist **dentro da mesma conta** continua sendo atalho rápido (não copia mídia em disco). Para portabilidade completa, use **Exportar MDD**.

---

## Onde na UI

| Ação | Onde |
|------|------|
| **Exportar MDD** | Home → menu de contexto da programação → «Exportar MDD» |
| **Importar MDD** | Home → card «Importar MDD» → upload → preview → confirmar |
| **Templates de slide (`.mdd`)** | Editor → Templates → Exportar / Importar MDD; arquivos em `tv-dashboard-api/tv_app/content/slide_templates/` |

Fluxo de importação (programação): **preview → apply** (token de curta duração). A programação importada nasce **inativa**, com novo `publicToken` e novos UUIDs.

### Templates de slide (pasta versionada)

| | |
|--|--|
| Pasta | `tv-dashboard-api/tv_app/content/slide_templates/` |
| Manifest | `kind: slide_template` + `template.{key,label,description,…}` |
| Serviço | `slide_template_mdd_service.py` + loader em `slide_preset_service.py` |
| API | `GET /slide-presets/{key}/export` · `POST /slide-templates/export` · `POST /slide-templates/import` |

Ciclo de edição: aplicar template no editor → ajustar → Exportar MDD → colocar/substituir o arquivo na pasta → commit.

---

## API

| Método | Rota | Descrição |
|--------|------|-----------|
| `GET` | `/apps/tv-dashboard-api/playlists/{id}/export` | Download `.mdd` |
| `POST` | `/apps/tv-dashboard-api/playlists/import/preview` | `multipart` arquivo → relatório + `importToken` |
| `POST` | `/apps/tv-dashboard-api/playlists/import/apply` | Cria programação a partir do token |

Apply (corpo JSON):

```json
{
  "importToken": "…",
  "nameOverride": "Nome opcional",
  "activateAfterImport": false,
  "bindingPolicy": "lenient"
}
```

- `lenient` — avisos de binding (rota ausente no catálogo, params) **não** bloqueiam.
- `strict` — qualquer warning/error de binding bloqueia o apply.

---

## Conteúdo do pacote (resumo)

```text
manifest.json
deck/playlist.json
deck/sections.json
deck/slides.json
deck/media.json
deck/data_bindings_index.json
media/{sourceAssetId}{ext}
```

Na importação: novos IDs de playlist/seção/slide/mídia; `assetId` reescrito; `operationId` de `dataBinding` mantido e validado contra `tv_data_routes.json` da conta destino. Alias legado `delpi_tv_deck` ainda é aceito no preview.

---

## Ferramentas de IA

1. Descompactar o `.mdd` (é ZIP).
2. Ler/editar `deck/*.json` (textos, frames, `operationId`, params).
3. Opcionalmente substituir arquivos em `media/`.
4. Reempacotar e importar via UI ou `import/preview` + `import/apply`.

Detalhe do schema: [tv-deck-package-v1.md](../../../tv-dashboard-api/docs/architecture/tv-deck-package-v1.md).

---

## Implementação

| Peça | Caminho |
|------|---------|
| Serviço | `tv-dashboard-api/tv_app/application/services/tv_deck_package_service.py` |
| Collector de `assetId` | `tv_deck_asset_collector.py` |
| Validação de bindings | `tv_deck_binding_validator.py` |
| Rotas | `playlist_routes.py` (`/export`, `/import/preview`, `/import/apply`) |
| UI | `DeckImportModal.tsx`, home `PlaylistsPage.tsx` |
| Testes | `tv-dashboard-api/tests/test_tv_deck_package_service.py` |
| Limite | `TV_DECK_PACKAGE_MAX_BYTES` (default 500 MB) |
