# G083 — Cobertura e reconciliação

Corpus: `1fd4c8b0`→`9b2f318f`→**`5782708a` local / `c3a66e97` produtivo** (2.208 itens/88 fontes — +1 item por segmentação após fix_lines).

## Pipeline

| Estágio | Quantidade |
|---|---|
| EXTRACTED | 13.479 afirmações de 2.208 itens |
| CLASSIFIED | 88 CURRENT_VERIFIED · 1.312 HISTORICAL_ONLY · 237 NOT_APPLICABLE · 571 UNVERIFIED |
| AUTHORITY_CHECKED | consistent 260+ · dated-verified ~1.150 · authority_not_needed ~10.7k · not_checkable ~450 · source_evidence ~890 |
| REVIEWED | automático 13.450 · **manual 29 decisões individuais** (hash-keyed, `g083-manual-decisions.json`) |
| RESOLVED | 0 STALE/REVIEW/MIXED residuais |

## G083-A — 1.341 afirmações pendentes → disposição individual (`g083-claim-authority-matrix.jsonl`)

- **806 NOT_APPLICABLE** — especificação TARGET/contrato aprovado (não afirma runtime).
- **346 VALID_HISTORICAL** — evidência AS-IS TO_INVENTORY (proveniência TÉO, não afirmação de runtime).
- **189 PENDING_AUTHORITY** — afirmação sem autoridade conclusiva; permanecem declaradas como pendências (não PASS), majoritariamente em docs datados/registro — nenhuma constitui afirmação de estado corrente contraditória detectada.

## G083-B — exposição histórica

22 correções (`g083-corrections.jsonl`): D1/D2 (G082-RW02) + 20 fix_lines G083 (doc-00/86/88/90/100/111/117/119/121/122) — afirmações datadas superadas anotadas com verdade vigente; originais em SUPERSEDED (141 itens de trilha). Varredura integral: 0 padrão superado PUBLISHED.

## G083-C — conversacional

TEST_NOT_RUN — protocolo em `g083-conversational-115.md` + doc152 §14.6.

## Limitações

PENDING_AUTHORITY declarado (não homologação universal). "Zero stale" = zero superado identificado na leitura claim-level + padrões conhecidos — não prova universal.
