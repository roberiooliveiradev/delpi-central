# VAL-04 — Dot Terminator Evidence Review Package

> Escopo: canal aditivo `graphic_primitives.dots` + integração B2
> (leader termination). Toda evidência é `DEVIN_VISUAL_OBSERVATION`;
> nada aqui é GT homologado, aprovação de desenho ou identidade de
> componente.

## Identidade

| Campo | Valor |
|---|---|
| Produto | `90480120` |
| Documento | `90480120.pdf` |
| PDF SHA-256 | `9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8` |
| Páginas | 2 |
| Base HEAD | `2dbe75b51a` (escopo limpo vs `a3d4b8c8d5`) |
| Diff | working tree (release bloqueado — verificador INCONCLUSIVE) |

## Artefatos (host — não versionados por serem desenho de cliente)

- `/tmp/val04_rec_90480120.json` — run record fresco (benchmark
  pdfium+paddleocr in-process, 207 tokens, `graphic_primitives` com
  canal `dots`).
- `/tmp/val04_full_u_90480120.json` — understanding completo
  (`balloon_candidates[*].leader_line` com `terminator_dots_px` e
  `termination`).
- `/tmp/val04_u_90480120.json` — resumo (timing, dots/página, leaders).
- `/tmp/a2_90264311.png` — recorte do caso `DOT_OVERSHOOT`
  (90264311-A2): dot verde no vértice da peça, aresta preta continua.
- `/tmp/val04_probe.py` — sonda reproduzível.

## Reprodução

```bash
docker run --rm \
  -v "$PWD/engineering-api:/app" -v "$PWD/shared:/shared" \
  -v /tmp:/tmp -v ~/ocr-models:/opt/ocr-models:ro \
  -e ENG_DRAWING_OCR_MODEL_DIR=/opt/ocr-models -w /app \
  infra-engineering-api:latest \
  python /tmp/val04_probe.py /tmp/90480120.pdf 90480120
```

Timing observado: `benchmark_extract` ≈97 s (render+OCR+primitivas),
`understanding` 0.78 s.

## Resultados-chave (90480120)

- Dots: p1=81 (`saturation_opening`), p2=67 (64 `saturation_opening`
  + 3 `distance_transform`).
- `DOT_TERMINATED`: A1 p1 ×2, AA p1/p2, A8 p2, A4 p2 (endpoint físico
  inalterado — distinção borda/centro preservada).
- `AMBIGUOUS` preservado: A5 (3 dots do leque), A9 e E (dot
  compartilhado 2002,1086 recuperado por `distance_transform`), A3.
- Irmãos: zero diff de estado/endpoint; `90264311-A2`
  `DOT_OVERSHOOT` 61 px confirmado visualmente (overshoot real).
- B1/tabela/B3 inalterados; `automatic_approval=false`.

## Perguntas ao reviewer (por ocorrência)

`BALLOON_LABEL_CORRECT? LEADER_PATH_CORRECT? ENDPOINT_CORRECT?
TERMINATOR_DOT_CORRECT? TARGET_REGION_CORRECT?
COMPONENT_ASSOCIATION_CORRECT?`

## Limitações

- Overshoot é anotado apenas em cadeia CANDIDATE escolhida; em
  AMBIGUOUS multi-raiz o dot atravessado aparece em
  `terminator_dots_px` sem anotação de overshoot por raiz.
- Dots não associados a raiz (ex.: (205,517), (157,539)) permanecem
  `CANDIDATE` expostos — não promovidos.
- Verificação independente `INCONCLUSIVE` (cursor usage limit até
  02/12/2026); release bloqueado até motor disponível ou exceção da
  Coordination.
