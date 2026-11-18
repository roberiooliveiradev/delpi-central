# GT-01 — Pacote de Revisão de Balões (B1+B2+B3)

**Status:** `DRAFT` · `OWNER_BLOCKED` · `METRICS_STATUS=EXPLORATORY_ONLY`
**Task:** `EVA-E1-VAL01-BALLOON-GT01-GROUND-TRUTH-INTEGRATED-EVALUATION-AND-ACCEPTANCE-01`

Este pacote entrega à Engenharia o material de decisão para homologação da
capacidade de análise de balões. Nada aqui é GT aprovado, threshold aprovado
ou prova de detecção de trocas reais.

## 1. Artefatos

| Artefato | Papel | SHA-256 |
|---|---|---|
| `annotations-balloon/90261723_p1.json` | GT draft — 4 ocorrências | ver `overlays/gt01-artifact-hashes.txt` |
| `annotations-balloon/90261731_p1.json` | GT draft — 4 ocorrências | idem |
| `annotations-balloon/90264311_p1.json` | GT draft — 6 ocorrências | idem |
| `synthetic-balloon/` | Fixtures sintéticos de troca (2 casos) | idem |
| `scripts/eval_balloon_gt01.py` | Avaliador offline reproduzível | idem |
| `balloon-gt01-corpus-manifest.json` | Corpus, SHAs, splits, exposição | idem |
| `overlays/gt01-balloon-eval-report.json` | Relatório de métricas executado | idem |

## 2. Corpus e separação

- **DEVELOPMENT** (3 com GT draft + 4 do G1 dev): 90261723, 90261731, 90264311,
  90264026, 90264004, 90264017, 90264135.
- **VALIDATION_EXPOSED** (11, sondados, sem GT): 90264302, 90264161, 90263520,
  90261606, 90263572, 90264178, 90480120, 90264014, 90264030, 90264043, 90264050
  (111 balões / 72 líderes candidatos no inventário do manifesto).
- **TRUE_UNSEEN_HOLDOUT = NOT_AVAILABLE.** Todos os documentos avaliados foram
  expostos a saídas da EVA; nenhum pode ser declarado holdout cego.
- Fileserver possui ~4.841 PDFs; seleção de holdout exige decisão do owner.

## 3. Resultados integrados (conjunto de desenvolvimento, 14 ocorrências)

| Métrica | Valor | Denominador | Status |
|---|---|---|---|
| DETECTION_PRECISION | 1.0 | 14/14 | EXPLORATORY_ONLY |
| DETECTION_RECALL | 1.0 | 14/14 | EXPLORATORY_ONLY |
| TABLE_ASSOCIATION_ACCURACY | 1.0 | 12/12 | EXPLORATORY_ONLY |
| LEADER_DETECTION_RATE | 1.0 | 14/14 | EXPLORATORY_ONLY |
| TARGET_ASSOCIATION_ACCURACY | 1.0 | 6/6 SINGLE | EXPLORATORY_ONLY |
| AMBIGUITY_PRESERVATION_RATE | 1.0 | 8/8 | EXPLORATORY_ONLY |
| CONFLICT_PRECISION | — | 0 | INCONCLUSIVE_NO_DENOMINATOR |
| CONFLICT_RECALL | — | 0 | INCONCLUSIVE_NO_DENOMINATOR |
| FALSE_ALERT_RATE | 0.0 | 0/14 | EXPLORATORY_ONLY |
| FALSE_NEGATIVE_RATE | — | 0 | INCONCLUSIVE_NO_DENOMINATOR |
| ABSTENTION_RATE | 0.857 | 12/14 | EXPLORATORY_ONLY |

- **Casos reais de balão trocado: 0.** Não há denominador para recall de
  conflito — a pergunta central da homologação permanece **INCONCLUSIVE**.
- **Casos sintéticos:** 2 (A→terminal, B→barra de cabo), ambos
  `TRUE_CONFLICT` na maquinaria do avaliador. São fixtures do avaliador,
  **não** evidência de detecção em desenho real.
- **Casos de abstenção correta:** 12/14 (ambiguidades preservadas + NOT_COMPARABLE).
- **Casos compatíveis corretos:** 2/2 (`A`→barra alongada de cabo nos 723/731).

## 4. Diagnóstico de limites (RQ-GT01-09)

1. **Linhas diagonais:** 0 detectadas no inventário de 13 documentos. Porém
   `leader=None`/ausente pode esconder diagonais não reconhecidas — o detector
   só produz `CANDIDATE` para caminhos eixo-alinhados. **Gap não resolvido:**
   documentos com 19+ balões e poucos líderes (90263572: 32→13, 90264178:
   23→10) sugerem perdas que podem incluir geometria diagonal.
2. **Regiões ambíguas:** 8/8 preservadas no conjunto avaliado; junções
   cabo/terminal/luva/protetor são o padrão dominante. Nenhuma ambiguidade foi
   resolvida por proximidade — comportamento correto.
3. **shape_class é proxy geométrico:** barra alongada saturada é consistente
   com corpo de cabo mas não prova identidade. Regiões `mixed` (vistas
   compostas do 64311) abstêm-se corretamente.
4. **Cor:** `fill_semantics=schematic_or_unknown` em todo o corpus →
   `COLOR_COMPARISON=NOT_COMPARABLE` preservado. Hue dominante divergiu entre
   desenhos irmãos (60 vs 30) confirmando que preenchimento esquemático não é
   cor de material.
5. **Worker isolado:** `worker_bad_response:rc=0` reproduzido — PaddleOCR/
   Paddlex emite saída de progresso não-JSON no stdout, violando o contrato do
   subprocesso. O OCR completa in-process; as sondas reais usaram
   `isolation=inprocess` (workaround de diagnóstico, **não** prova de
   produção). Correção exige escopo/owner próprios — não alterada nesta task.

## 5. Thresholds propostos (RQ-GT01-08) — `THRESHOLDS_PROPOSED`, nenhum aprovado

| # | Critério | Proposta | Racional | Denominador mínimo | Falha crítica |
|---|---|---|---|---|---|
| T1 | Falsos conflitos em desenhos reais | **0 tolerados** (zero-tolerance) | falso alarme de troca erosiona confiança | ≥30 ocorrências anotadas em VALIDATION+HOLDOUT | alertar troca inexistente |
| T2 | Recall de trocas reais | **owner-defined** — propor ≥ 0.9 quando houver casos | sem casos reais, não há número honesto | ≥5 casos reais confirmados | perder troca real |
| T3 | Falsos positivos de detecção | **0 tolerados** em HOLDOUT | balão inventado quebra cadeia | ≥20 ocorrências | alucinação visual |
| T4 | Preservação de ambiguidade | **100%** — nunca resolver por proximidade | ambiguidade é fato visual | ≥8 casos | falsa precisão |
| T5 | Abstenção justificada | sem teto rígido; reportar taxa por família | abstenção honesta > veredito inventado | por família | mascarar cobertura |
| T6 | Detecção recall em HOLDOUT | owner-defined após holdout existir | depende de famílias | ≥20 ocorrências | perder balão real |
| T7 | Reprodutibilidade | mesmo SHA + config → métricas idênticas | gate de release | rerun completo | resultado não reproduzível |

Aprovação desses valores é decisão da Engenharia — **não** do executor.

## 6. Decisões pendentes do owner

1. Aprovar/revisar as 3 anotações draft (14 ocorrências) — ou designar anotador.
2. Selecionar holdout real dentre os ~4.824 PDFs não sondados.
3. Obter casos reais documentados de balão trocado (NC histórica) — sem eles,
   `CONFLICT_RECALL` permanece INCONCLUSIVE.
4. Aprovar ou rejeitar thresholds T1–T7.
5. Decidir escopo/owner da correção do worker isolado.
6. Decidir se ambiguidade de junção exige evolução do B2 (ex.: refinamento de
   endpoint por primitiva) ou permanece abstenção.
