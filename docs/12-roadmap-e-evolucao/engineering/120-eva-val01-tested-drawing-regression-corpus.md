# EVA VAL-01 — Catálogo permanente de desenhos já testados e corpus de reteste

**Owner funcional:** Engenharia. **Contexto:** EVA/Portal Engenharia, única frente VAL-01. **Iniciado:** 2026-11-04. **Issue:** [#131](https://github.com/roberiooliveiradev/delpi-central/issues/131). **Fonte detalhada:** [Doc 119](119-eva-drawing-validation-catalog-and-nc-prioritization.md), §§16–26.

## Regra de governança do catálogo

Este é o **índice canônico cumulativo de PDFs já usados em testes**, inclusive os que falharam, para reteste de regressão e generalização. Ao testar **qualquer novo PDF**: acrescentar linha única por código+SHA (sem apagar rodadas anteriores), registrar fonte oficial, tamanho/páginas/hash, cenários, verificações manuais, achados backend/MCP, estado da evidência, commit/runtime e data. Em caso de alteração do PDF oficial, **criar nova versão de registro com novo SHA**, preservar o anterior como `STALE_EVIDENCE` para comparações de regressão e jamais presumir que o PDF atual é idêntico ao previamente examinado.

**Importante:** o GitHub guarda **metadados e referências de fonte, não uma cópia dos PDFs oficiais ou conteúdo sigiloso**. A fonte canônica segue `Engineering API GET /v1/products/{code}/drawing/pdf` com AuthZ delegated; a estrutura corrente via API owner. Recuperar por `EVA read(product,drawing_download,ref=code)` e verificar SHA; se a fonte tiver mudado, reestabelecer ground truth com Engenharia. Se a organização aprovar futuro **acervo controlado de fixtures binários**, governá-lo separadamente com owner, permissões/licenças, retenção e controle de versão, sem colocar documentos proprietários indiscriminadamente em GitHub. Nem GitHub, nem este catálogo tornam-se source of truth do desenho ou da BOM.

**Status do ground truth:** os itens abaixo incluem **conferência visual assistida pelo ChatGPT**, não validação formal pela Engenharia; portanto `VISUAL_REVIEW_CANDIDATE` salvo se o owner aprovar. Comparar somente escopo efetivamente coberto; notas de hierarquia e quantidades são limitadas. `BOM_ONLY` exige cobertura suficiente, `DRAWING_ONLY` exige posição real em tabela corrente, nunca mera menção no histórico. `NO_DIVERGENCE_DETECTED` jamais equivale a aprovação do desenho.

## Índice de 13 PDFs oficiais testados

| Código | Páginas | SHA-256 do PDF examinado | Referência/cenário visual | Expectativa de reteste | Evidência |
|---|---:|---|---|---|---|
| `90264302` | 1 | `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef` | 2 PI N1 e filhos presentes; OCR token-only; parcial | INCONCLUSIVE; sem finding | Doc119 §21/§25 |
| `90264161` | 1 | `8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195` | 50090001 sob 90350410 na BOM; desenho é ambíguo quanto ao pai | PARENT_RELATION_MISMATCH candidato, precisa owner; jamais fato só por inferência | Doc119 §21/§25 |
| `90263520` | 1 | `08bf68690401438ab09c0e7ffcd1126bf98b238de776bc680db587704e4fb200` | 5 PI no desenho vs 4 PI N1 na BOM; 50213064 extra; MPs compartilhadas | EXIGIR DRAWING_ONLY 50213064, nenhum falso MP | Doc119 §17/§20/§25 |
| `90261606` | 1 | `1c1f1412fb6cac22e8e44893dc27a39f45be806c6819bc12856ea4adb3580cd1` | 3 PI 50222382/83/84, filhos e etiquetas distintos; pai parcial | INCONCLUSIVE sem falso finding | Doc119 §21/§25 |
| `90263572` | 2 | `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e` | Tabela extensa na p2; 16 MP+10 PI N1 observados; 49 ocorrências não verificadas; OCR 10060004≈10080004 | INCONCLUSIVE, zero BOM_ONLY na cobertura parcial, não produzir DRAWING_ONLY por OCR ambíguo | Doc119 §21/§25 |
| `90264178` | 1 | `1a78693bd335371f192daceecf7f14f91637443bf03045f0aebec33bd7332fa8` | 6 MP N1+10 PI N1; 10090014 presente desenho/BOM; column/pai ambíguos | INCONCLUSIVE sem DRAWING_ONLY 10090014 nem mismatches inferidos | Doc119 §21/§25 |
| `90480120` | 2 | `9b64ae2095fa551e6c3b12fa1f6d232646725b2ab9c31eb489abedd972555cd8` | 10 MP N1 em tabela p1; p2 desenho/inspeção; cobertura hierarquia parcial | INCONCLUSIVE, 10/10 presença N1 | Doc119 §21/§25 |
| `90264004` | 1 | `5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4` | 8 MP N1 + 2 PI N1; estrutura 14 ocorrências incluindo filhos | INCONCLUSIVE, 0 findings; 14/14 códigos presentes por matching | Doc119 §26 |
| `90264014` | 1 | `8e3626181f8696fd6f7f47c83c9014b30f0e0a9d0591abe26c218087fa0bdaa8` | 2 MP N1+7 PI N1; 16 ocorrências incluindo filhos; pai 10380042 requer confirmação | INCONCLUSIVE, 0 findings | Doc119 §26 |
| `90264017` | 14 | `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee` | 10080535 em REVISION_HISTORY p2 'ALT. TERM. 10080535 P/ 10080438'; 10080438 ativo; não é current BOM row. Só páginas [1,2] lidas pelo backend | REGRESSION NEGATIVA: não emitir DRAWING_ONLY 10080535; exigir página válida e região component_table real; incompleto para 14p | Doc119 §26 |
| `90264030` | 13 | `909b440a84fb00868ead4825f8c558ccf2c233b673655941bb7d32b6d1c59692` | PA 70260010 no desenho p2 contém PI 50225512; BOM contém mesma relação; apenas páginas [1,2,3] pelo backend | REGRESSION NEGATIVA: não emitir PARENT_RELATION_MISMATCH 50225512 como raiz, degradar pai ambíguo | Doc119 §26 |
| `90264043` | 1 | `fa391e18d929de426498482605bf8a55e48a8fecf0ed3d4019eecadb414a9973` | 2 MP N1+5 PI N1, 20 BOM ocorrências; 10090023 fora célula | INCONCLUSIVE, 0 findings; 19/20 correspondências observadas | Doc119 §26 |
| `90264050` | 2 | `e98f718397e9bd23587b49ae1ea20cd0f286255d984045d7919db18007ffcffb` | 3 MP N1+2 PI N1+2 filhos; p2 instruções de inspeção | INCONCLUSIVE, 0 findings; 7/7 correspondências | Doc119 §26 |

## Matriz de regressão por risco

**Fixo positivo 1 — `90263520`:** manter `DRAWING_ONLY 50213064`, com página 1/célula comprovada; rejeitar desvios inventados de `10400040` e `10400035` por deslocamento de linha/PI.

**Fail-closed 2 — `90263572`:** não criar `BOM_ONLY` de linhas que OCR não leu; página 2 e 49 não verificadas precisam permanecer visíveis; `10060004≈10080004` é ambiguidade, não novo componente.

**Fail-closed 3 — `90264178`:** não emitir `DRAWING_ONLY 10090014`; não promover pai inferido a mismatch quando fronteira não confiável.

**Document region 4 — `90264017`:** separar `revision_history` de `component_table` em cada página e não converter código substituído `10080535` em MP do desenho atual. Um finding com `drawing_page=null` deve ser rejeitado quando não há proveniência visual suficiente. Cobertura parcial das 14 páginas permanece inconclusiva.

**Hierarchy 5 — `90264030`:** preservar subestrutura `90264030 → 70260010 → 50225512`; se a célula/linha do pai não for demonstrável, devolver `INCONCLUSIVE`, sem erro de associação afirmado. Cobertura parcial das 13 páginas permanece inconclusiva.

**Generalização e baseline 6:** `90264004/14/43/50`, `90264302`, `90261606`, `90480120` testam múltiplos padrões de tabela, MP diretas, PIs e documentos com 1–2 páginas. `90264161` valida tratamento de `50090001` como candidato de hierarquia, a ser decidido pelo owner.

## Protocolo de cada nova rodada

1. Inventariar PDF oficial atual de cada código, `size`, `pages`, `sha256`, versão do contrato, `as_of` BOM; comparar o SHA com o índice.
2. Executar `product.drawing_analysis` pelo backend **e** pelo MCP consumidor autorizado; capturar o resultado tipado (`status`, `coverage`, `findings[]`, `limitations`, `report provenance`).
3. Conferir independentemente, por amostragem explícita ou todas as páginas no caso de auditoria integral, a região exata e o relacionamento com a BOM. Não repassar a observação manual ao backend durante o teste de generalização.
4. Registrar `PASS/FAIL/INCONCLUSIVE/TEST_NOT_RUN` por RQ/AC, falsos positivos e falsos negativos conhecidos. Distinguir falha AuthZ e fonte 502 de erro do comparador.
5. Medir `precision` de finding, `recall` da extração, exatidão de pai-filho, cobertura visual e taxa de inconclusivos **apenas onde existir ground truth**, segmentando por layout e páginas.
6. Preservar **holdout não utilizado no ajuste de heurísticas**; desenhos usados no desenvolvimento viram conjunto de regressão e não podem medir generalização não vista.
7. Após cada bateria: atualizar este índice, Doc119 e Issue #131 com SHA runtime/commit e resultados; nunca sobrescrever evidência histórica.

## Próximo pacote técnico — melhoria de análise sem frontend

**RQ-VAL-027 (separação semântica de regiões):** `revision_history`, `notes`, `title_block` e `component_table` têm proveniência espacial e escopo próprios; ocorrências só são comparáveis como componente vigente se de uma linha real da tabela correspondente. Detectar históricos repetidos em 14 páginas; não promover tokens isolados de histórico a `DRAWING_ONLY`.

**RQ-VAL-028 (hierarquia multinível):** preservar raízes/conjuntos `70xx`, PI `50xx`, MP `10xx` na árvore com células/grupos/linhas ancorados e multiplicidade; não atribuir pai raiz quando evidência indicar subgrupo `70260010`. Sem evidência suficiente, relacionamento `INCONCLUSIVE`, não `PARENT_RELATION_MISMATCH`.

**RQ-VAL-029 (documentos extensos):** planejar cobertura por páginas/tabelas dentro de limites de custo e memória; analisar todas as regiões pertinentes ou declarar páginas não verificadas; não chamar documento de 13/14 páginas de integralmente analisado após 2/3.

**Gate:** preservar os 13 casos atuais, adicionar casos sintéticos positivos/negativos com ground truth, exercitar E2E real em produção após deploy correto. Não implementar MFE/visual nem outras verificações do desenho enquanto esta etapa estiver ativa. `ARCHITECTURE_DECISION_REQUIRED` para mudança de owner/boundary/source of truth.

---

## Log de execução — 2026-11-04 (DEC-VAL-029 implementação)

Runtime de diagnóstico em `srv-api` (código patcheado via overlay `/tmp/eva_app`, serviço intacto; worker legado — cobertura multipágina real depende do deploy). Commits locais `c220937cc5`+`427020a61a`+`ad2838c0cb`, não publicados (push bloqueado: SSH GitHub negado).

| Produto | Antes (baseline srv-api) | Depois (patched) | Resultado |
|---|---|---|---|
| `90264017` | `DIVERGENCES_CANDIDATES` — falso `DRAWING_ONLY 10080535` (`drawing_page=null`) | `DIVERGENCES_CANDIDATES`, `drawing_only: 0`; `10080535` em `contextual_codes` (title_block p2); `10080438` reconhecido | **PASS** — AC-01/AC-02 |
| `90264030` | `DIVERGENCES_CANDIDATES` — falso `PARENT_RELATION_MISMATCH 50225512` | `INCONCLUSIVE`, `divergences: 0`; `10110676→50225512` em `unverified_parent_relations` | **PASS** — AC-03/AC-04 |

Demais 11 produtos: `TEST_NOT_RUN` na rodada patched (bateria integral condicionada ao deploy canônico com worker atualizado — pages cap/sample/sha efetivos). Cobertura multipágina: `tables_by_page`/`pages_not_processed`/`evidence_truncated` agora declarados; `90264017` manteve `complete_for_requested_scope=false` (14p não integrais).

## Log de execução — 2026-11-04 (DEC-VAL-029 produção, SHA `6876f6f535`)

Bateria em runtime produtivo `srv-api` deployado (worker com caps novos). 11/13 produtos: `divergences: 0`, `INCONCLUSIVE` honesto, sem falsos positivos nem `BOM_ONLY` fabricado. Os dois documentos extensos:

| Produto | Baseline | Produção `6876f6f535` | Resultado |
|---|---|---|---|
| `90264017` (14p) | `DRAWING_ONLY 10080535` FP, 2/14 páginas | **14/14 páginas**, 8 tabelas, `drawing_only: 0`, `divergences: 0`, `contextual_codes: 2` | **PASS** — AC-01/02/05 |
| `90264030` (13p) | `PARENT_RELATION_MISMATCH 50225512` FP, 3/13 | **13/13 páginas**, 11 tabelas, `mismatches: 0`; `DRAWING_ONLY 10080535`×4 p9-12 + `10081686` p7 (linhas tipadas, candidatos reais `PENDING_HUMAN_REVIEW`); `BOM_ONLY 10080438`×4+`10080292` (ausência declarada apenas com cobertura integral) | **PASS** — AC-03/04/05; candidatos pendentes de revisão humana |

`DRAWING_ONLY`/`BOM_ONLY` emitidos são candidatos com proveniência de página — aprovação final cabe à Engenharia. `unverified_parent_relations` preserva evidências (ex.: `10110676→50225512` ≠ BOM `70260010`).
