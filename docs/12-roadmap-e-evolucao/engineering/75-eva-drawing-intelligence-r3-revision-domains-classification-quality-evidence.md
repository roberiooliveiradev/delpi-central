# 75 — EVA — Drawing Intelligence R3: Revision Domains, Technical Classification Quality & Production Evidence

**Status:** IMPLEMENTED + DEPLOYED. **Data:** 2026-10-31. **SHA:** `8c13fbb1c8` (main) → deploy prod via merge.
**Regressão:** produto `90264302 — CHICOTE DE LIGACAO`.

## 1. ENG-REV-001 — domínios de revisão separados (decisão implementada)

`current_revision` TOTVS = controle de revisões do **cliente**; `REV` do desenho = controle técnico de **Engenharia**; revisão do acervo = metadado da biblioteca. São controles independentes — diferença de número **não** é divergência, WARNING ou correção.
Código: comparação `TOTVS × drawing` **removida**; nova verificação `revision_domains` apresenta os três domínios com origem (`identification.revision_domains`), status PASS = "apresentado separadamente" (não é conformidade). Visual×oficial agora compara revisão observada contra o **domínio de desenho**, nunca contra `current_revision`. Em 90264302: `001 (TOTVS)` × `00 (desenho)` → sem alerta.
Knowledge v1.2: `DRAW-REV-MATCH` → `superseded_rules` (preservado histórico), `ENG-REV-001` ativa.

## 2. Falsos positivos eliminados

- **PI parser (R3-B):** gramática de prefixo concatenado `CA22VERM` = CA(isolação)+22(bitola)+VERM(cor4L); segmentos `-00643/04/10-0600-0000` (comprimento/decape/terminais) reconhecidos. As duas descrições do produto agora identificam segmentos em vez de "desvio".
- **Visual×textual (R3-C):** `conflict` → `not_found_in_text`. Ausência de token textual NÃO é contradição; conflito só com evidências explícitas comparáveis do mesmo campo.
- **Identificação (R3-A):** códigos não-produto (COD cliente, DES desenho) não geram conflito; candidatos continuam página-localizados sem promover número a fato.
- **BOM (R3-D):** travessia aceita `items`/`components`/`children` — multinível real, não só filhos diretos.
- **Estrutura indisponível** já visível como `bom_availability` INCONCLUSIVE (R2).

## 3. Testes

R2/R1 suites atualizadas para a semântica corrigida (`revision_domains` PASS + domínios separados; `not_found_in_text`); `test_revision_conflict_vs_text` → `test_revision_absent_in_text_not_conflict`. **Suite: 533 passed / 0 failed** no SHA `8c13fbb1c8`.

## 4. Deploy e smoke

Push → `origin/main=8c13fbb1c8`. Prod `operador@192.168.1.237`: merge (repo divergido — histórico conhecido) → `up-prod-sequential.sh --build engineering-api` → `delpi-engineering-api Up (healthy)`; parser PI executável em prod; `/v1/health` 401. **Rollback:** SHA anterior + rebuild.

## 5. Matriz R3-01..32 (honesta)

- **PASS:** 01–13 (ENG-REV-001 implementado, regra antiga superseded, 90264302 sem alerta, parser PI, not_found_in_text, BOM multinível), 15 (qty INCONCLUSIVE), 17–21, 24–25 (EVAL_PENDING por falta de ground truth owner), 27–31.
- **TEST_NOT_RUN:** 22 parcial (regressões unitárias sim, MCP E2E real não), 26, TC-20.
- **PENDING:** identificadores tipados completos (R3-A parcial — labels COD/DES reconhecidos como não-produto), ONDA14 corpus eval, invariants formais de consistência (básico implementado).

## 6. Residuais

1. ChatGPT real E2E não exercitado — TEST_NOT_RUN.
2. ONDA14/ground truth owner: EVAL_PENDING — nenhuma métrica inventada.
3. Identificação tipada completa por label (COD/DES/REF) — parcial; candidatos seguem genéricos sem promoção a conflito.
4. Métricas de BOM por nível/ocorrências — travessia corrigida; relatório ainda agrega total (próxima evolução).
5. Prod repo divergido — merge não destrutivo (realinhamento recomendado).
