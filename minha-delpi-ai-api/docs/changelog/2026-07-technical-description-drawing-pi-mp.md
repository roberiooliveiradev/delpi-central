# Changelog — descrição técnica MP/50xx e classificação no desenho (jul/2026)

## Resumo

A skill **`technical-description-delpi`** passou a cobrir **matérias-primas (1001–1025)** e **intermediários (50xx)**. O vocabulário `technical_description_vocabulary.json` alimenta também o pipeline de desenho via `ChatDrawingProductFamilyClassificationService`, reduzindo falsos erros de estrutura (PI fantasma, OCR 10↔50, MP no roteiro, length/qtd de consumível).

## API / skills

| Item | Doc |
|------|-----|
| Skill MP + intermediários | [`../api/11-skills.md`](../api/11-skills.md) |
| Intent + RAG | [`../architecture/chat-intelligence-base.md`](../architecture/chat-intelligence-base.md) § Descrição técnica |
| Limitações desenho (V8) | [`../architecture/chat-drawing-skill-limitations.md`](../architecture/chat-drawing-skill-limitations.md) § PI × MP |
| Catálogo de conteúdo | [`../architecture/assistant-content-catalog.md`](../architecture/assistant-content-catalog.md) |
| Smoke N15–N17 | [`../testing/smoke-operacional-manual.md`](../testing/smoke-operacional-manual.md) |

## Commits de referência

- `b49d53601` — skill intermediários 50xx
- `60f90e89b` — classificação PI/MP/consumível no desenho
- `645ee73c3` — reconciliação OCR BOM
- `7efb8b731` — MP fora do guide_structure_extra
- `019953386` — falso 50xx fora de length/decape/qtd

## Deploy

```bash
./infra/scripts/up-prod-sequential.sh --cpu --fase api --build minha-delpi-ai-api
```

Admin: `GET /admin/skills` bootstrapa a skill no banco se ainda não existir.
