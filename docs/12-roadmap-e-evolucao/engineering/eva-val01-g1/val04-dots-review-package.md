# VAL-04R — Dot Terminator Evidence Review Package

> Escopo: canal aditivo `graphic_primitives.dots` + integração B2
> (leader termination, inclusive por ramo). Toda evidência é
> `DEVIN_VISUAL_OBSERVATION`; nada aqui é GT homologado, aprovação de
> desenho ou identidade de componente.

## Identidade

| Campo | Valor |
|---|---|
| Produto | `90480120` |
| Documento | `90480120.pdf` |
| PDF SHA-256 | `9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8` |
| Páginas | 2 |
| BASE_SHA | `6eaa8bc890` (= origin/main) |
| DIFF_FINGERPRINT_SHA256 | `cc1bd570274d1a17666a9e55440f83853883c5a1e2b933dae8ba20c16fa33af7` |
| Estado | working tree — release bloqueado (verificador INCONCLUSIVE) |

## Pacote auditável do diff (RQ-VAL04R-02)

Diretório de evidência no host executor: `~/eva-val04-evidence/`

- `val04r_code_diff.patch` — diff íntegro (4 arquivos, ~+564/−16).
- `val04r_diff_stat.txt`, `val04r_diff_manifest.json` — BASE_SHA,
  BASE_TREE_SHA, fingerprint, paths, contratos alterados, executor,
  instrução de reprodução (`git checkout <BASE> && git apply`).
- Reprodução: `git checkout 6eaa8bc890 && git apply val04r_code_diff.patch`.

## Auditoria dos 148 candidatos (RQ-VAL04R-03/04)

- `dot_audit_90480120.json` — matriz por candidato: `dot_id`, `page`,
  `center`, `radius`, `source`, `assoc` (ocorrências), métricas
  (`diskiness`, `circularity`, `fill`), `in_text_box`.
- `dot_audit_sheet_p1.png` / `dot_audit_sheet_p2.png` — contact sheets
  48×48 de todos os candidatos (`*`=associado a líder).
- `dots_overlay_p1.png` / `dots_overlay_p2.png` — overlay da página
  (verde=associado, âmbar=não-associado).

| Categoria | n | Classe |
|---|---|---|
| Associados a líderes | 19 | `LIKELY_TERMINATOR` |
| Não-associados dentro de caixa OCR | 78 | `LIKELY_NON_TERMINATOR` (fragmentos de glifo: pingos de 'i', miolos, partes densas) |
| Não-associados fora de texto | 51 | `LIKELY_NON_TERMINATOR` (pontas de seta de cota, features da peça) — `AMBIGUOUS` para revisão |
| Duplicatas | 0 observadas | — |

**Discriminação (AC-04):** métricas geométricas (diskiness,
circularity, fill) **não separam** associados de não-associados —
sobreposição quase total. Text-overlap removeria 2 terminadores reais
(a1 p1 ×2) → **nenhum filtro seguro demonstrado**; nenhum candidato
removido. A discriminação efetiva permanece a jusante (contato
geométrico com o líder), por design do contrato `CANDIDATE`.

## Resultados-chave (90480120 — run fresco com branch_terminations)

- Dots: p1=81, p2=67 (como VAL-04).
- `DOT_TERMINATED`: A1 p1 ×2, AA p1/p2, A8 p2, A4 p2 (endpoint físico
  inalterado).
- `branch_terminations` por raiz (ocorrências AMBIGUOUS):
  - **A5 p1:** `[DOT_OVERSHOOT, DOT_TERMINATED, DOT_TERMINATED, OPEN]`
    — ramo do meio atravessa o dot e segue ~61 px por aresta da peça
    (observação VAL-03 agora anotada por raiz, estado AMBIGUOUS
    preservado).
  - **A9 p2:** `[OPEN, DOT_OVERSHOOT]` — dot (2002,1086) compartilhado
    com E; ambiguidade preservada.
  - **E p2:** 9 ramos anotados; A3/a6/a2/a7 idem.
- Irmãos: `90261723`/`90261731` B×2 `DOT_TERMINATED`; `90264311` A1 +
  A4×2 `DOT_TERMINATED`, **A2 `DOT_OVERSHOOT` 61 px** (controle
  positivo validado visualmente), A3×2 `OPEN` — sem término fabricado.
- B1/tabela/B3 inalterados; `automatic_approval=false`.

## Reprodução

```bash
docker run --rm -v "$PWD/engineering-api:/app" -v "$PWD/shared:/shared" \
  -v ~/eva-val04-evidence:/ev -v ~/ocr-models:/opt/ocr-models:ro \
  -e ENG_DRAWING_OCR_MODEL_DIR=/opt/ocr-models -w /app \
  infra-engineering-api:latest \
  python /ev/val04r_probe.py /ev/90480120.pdf 90480120 /ev
```

Timing observado: `benchmark_extract` ≈97 s; `understanding` <1 s.

## Suíte (ambiente correto — container com cv2/paddle)

- `python -m pytest tests` no container (mounts /app /shared /docs
  /api-delpi): **1721 pass / 21 skip / 0 fail**.
- 7 falhas iniciais = mounts ausentes (`/docs`, `/api-delpi`) —
  resolvidas remontando; as 6 falhas do venv local (worker sem
  cv2/paddle) não ocorrem no container. **Nenhuma regressão real.**

## Perguntas ao reviewer (por ocorrência)

`BALLOON_LABEL_CORRECT? LEADER_PATH_CORRECT? ENDPOINT_CORRECT?
TERMINATOR_DOT_CORRECT? BRANCH_TERMINATION_CORRECT?
TARGET_REGION_CORRECT? COMPONENT_ASSOCIATION_CORRECT?`

## Limitações

- `branch_terminations` usa o segmento mesclado por raiz (mesma
  representação do `segments_px` ambíguo) — continuação além do cluster
  não é encadeada por ramo (consistente com a representação vigente).
- 51 candidatos fora de texto permanecem `CANDIDATE`/`AMBIGUOUS` de
  revisão — majoritariamente pontas de seta de cota.
- Verificação independente `INCONCLUSIVE` r1 (cursor usage limit até
  02/12/2026); release bloqueado até motor disponível ou exceção.
