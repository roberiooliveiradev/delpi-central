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

## Log de execução — 2026-11-04 (DEC-VAL-032, reteste independente consumidor ChatGPT)

**Publicação confirmada via GitHub:** HEAD `7d5b3667fd51d90a96211b885cf38643edb18605`. **Deploy SHA `0d18a76bbf` foi reportado por Devin, não verificado de modo independente no host pelo ChatGPT.** Conectado ao MCP EVA do usuário, via `analyze(product.drawing_analysis,{product_code,compose_understanding:true})`, seguido de `analyze(...,job_id)` com mesma identidade: ambos os jobs retornaram o relatório final tipado, sem `job_not_found` nem `product.detail forbidden`. Os hashes de PDFs no índice original não foram reconferidos nesta execução; não declarar que arquivos oficiais não mudaram.

| Produto | Job ID | Resultado consumidor | Cobertura e achados | Estado |
|---|---|---|---|---|
| `90264017` | `aj-db90f319b8df4895` | `INCONCLUSIVE`; 0 divergências; 0 `DRAWING_ONLY 10080535` | 14/14 `pages_ocr_ok`, 8/8 tabelas verificadas, 87 códigos de tabela, 72/96 ocorrências BOM correspondidas; 2 contextuais, `complete_for_requested_scope=false` por relações ainda não comprovadas | `MCP_CHATGPT_CRITICAL_PASS`; validação técnica final pendente |
| `90264030` | `aj-af52bd893b9d4a63` | `DIVERGENCES_CANDIDATES`; 10 achados; 0 `PARENT_RELATION_MISMATCH` | 13/13 `pages_ocr_ok`, 11/11 tabelas; 80 códigos; 77/82 BOM correspondidas; 5 `DRAWING_ONLY`: `10081686` p7 e `10080535` p9,p10,p11,p12; 5 `BOM_ONLY`: `10080292` sob `70260049` e `10080438` sob `70260050/51/52/53`. Todos são candidatos pendentes de owner; `complete_for_requested_scope=false`, com 5 relações pai-filho não verificadas | `MCP_CHATGPT_CRITICAL_PASS` de transporte; `ENGINEERING_FINDINGS_REVIEW=PENDING` |

**Importante:** todas as páginas processadas por OCR ≠ análise estrutural completa. A presença dos dez findings tipados em `90264030` não comprova divergências reais no desenho. Não converter em NC ou aprovação automática. Demais **11 desenhos não foram reexecutados pelo consumidor ChatGPT nesta rodada**: `TEST_NOT_RUN`, ainda que Devin reporte regressão backend anterior. Preservar todas as entradas e logs históricos.

## Log de execução — 2026-11-04 (DEC-VAL-032, bateria de 11 PDFs restantes via ChatGPT MCP)

**Escopo:** uso da conexão EVA `get_context` + `analyze(product.drawing_analysis,{product_code,compose_understanding:true})` com `RUNNING+job_id` e poll para o resultado. Esta rodada complementa o log dos 2 PDFs críticos `90264017/90264030` acima, formando **13 produtos invocados pelo consumidor no total**. Não foram reconferidos neste turno os SHA-256 dos PDFs baixados historicamente; hashes anteriores são referências, não prova de identidade dos arquivos atuais. Deploy `0d18a76bbf` reportado por Devin; versão do host não foi verificada por acesso direto. Status `INCONCLUSIVE` preservado como estado técnico, e `0 divergências` não implica desenho aprovado.

| Produto | Fluxo MCP neste turno | Páginas OCR | Match BOM | Findings estruturais | Classificação do reteste |
|---|---|---:|---:|---|---|
| `90263520` | COMPLETED, INCONCLUSIVE | 1/1 | 20/20 | 0; nenhum `DRAWING_ONLY 50213064` | **`EXECUTION_DRIFT` em baseline de BOM:** hoje `50213064` consta como filho oficial de `50230893` (confirmado tanto no relatório `bom_occurrences O0011` quanto em `read(product,structure)`). Baseline anterior exigia `DRAWING_ONLY 50213064` porque a BOM antiga não continha o PI. **Não atribuir a ausência do finding automaticamente a falso negativo:** reavaliar `as_of`/versão da estrutura oficial e fixar ground truth válido para comparação temporal. |
| `90263572` | COMPLETED, DIVERGENCES_CANDIDATES | 2/2 | 32/56 | 1 `BOM_ONLY 10080004` | **`REVIEW_REQUIRED / POSSIBLE_REGRESSION`**: teste anterior era INCONCLUSIVE e registrava ambiguidade OCR `10060004≈10080004`; esta rodada afirma ausência com `complete_for_requested_scope=false`, 23 presenças `token_only` e 10 códigos extraídos sem célula tipada. Necessária conferência visual página/célula antes de confirmar ausência. |
| `90264178` | COMPLETED, INCONCLUSIVE | 1/1 | 38/40 | 0 | PASS negativo: não retornou falso `DRAWING_ONLY 10090014`; excesso de ocorrência do código ainda é limitação. |
| `90264161` | COMPLETED, INCONCLUSIVE | não disponível | não executado | 0 | **INCONCLUSIVE por `bom_unavailable 502`**; fonte indisponível na execução, não considerar PASS do comparador. Retry com mesmos parâmetros reaproveitou o job e retornou mesmo status; exige nova execução após disponibilidade/invalidação autorizada. |
| `90264302` | COMPLETED, INCONCLUSIVE | 1/1 | 6/6 | 0 | PASS para verificação conservadora. |
| `90261606` | COMPLETED, INCONCLUSIVE | 1/1 | 11/12 | 0 | PASS para verificação conservadora; `10080147` ainda `extracted_but_unclassified`. |
| `90480120` | COMPLETED, INCONCLUSIVE | 2/2 | 10/10 | 0 | PASS conservador. |
| `90264004` | COMPLETED, INCONCLUSIVE | 1/1 | 14/14 | 0 | PASS conservador. |
| `90264014` | COMPLETED, INCONCLUSIVE | 1/1 | 16/16 | 0 | PASS conservador; `10380042` relação pai inferida não verificada. |
| `90264043` | COMPLETED, INCONCLUSIVE | 1/1 | 19/20 | 0 | PASS conservador; 3 relações de pai não verificadas, `10090023` sem célula tipada. |
| `90264050` | COMPLETED, INCONCLUSIVE | 2/2 | 7/7 | 0 | PASS conservador depois de retry: primeiro job retornou erro tipado `drawing_pdf_unavailable 502`; nova execução obteve PDF e relatório. |

**Ocorrências operacionais:** alguns starts retornaram `403 forbidden` sob concorrência; novas chamadas individuais recuperaram o start autorizado. `90264161` teve `bom_unavailable 502` persistente no resultado idempotente do job. Nenhum desses eventos deve ser contado como divergência técnica. Os jobs não garantem recuperação após restart (registro process-local) e seus resultados COMPLETED podem ficar cacheados por TTL, inclusive `INCONCLUSIVE` por erro de fonte; propor retry autorizado sem reaproveitamento indevido de evidência stale.

**Síntese 13/13:** 13 produtos invocados no consumidor; **12 relatórios com comparador efetivamente executado**, incluindo os dois críticos, e 1 (`90264161`) sem BOM devido a erro de fonte. As duas novas questões técnicas são (a) **mudança demonstrada da BOM oficial em `90263520`**, invalidando a expectativa temporal antiga sem versionamento do dado; (b) `BOM_ONLY 10080004` no `90263572` com cobertura estrutural ainda incompleta, exigindo visual/manual. Os 10 findings de `90264030` continuam candidatos pendentes de owner. **`MCP_TRANSPORT_E2E=PASS` para resultados recuperados; `CORPUS_REGRESSION_FULL=INCONCLUSIVE`, `VAL01_FINAL_APPROVAL_PENDING`.**

### Evidência visual adicional — 2026-11-04, `90263572` `10080004` (**FALSE_POSITIVE_CONFIRMED**)

Após executar os 13 testes, foi baixado novamente o **PDF oficial atual** `90263572.pdf` pela EVA `read(product,drawing_download)`. Sua resposta declarou SHA-256 **`9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e`**, **igual ao hash previamente catalogado**. O PDF de **2 páginas** foi renderizado e inspecionado visualmente. **Página 2**, tabela grande de componentes, **primeira linha do bloco superior à direita, referência `A1`, coluna `Componente`**: o código **`10080004`** está **visivelmente impresso**, com descrição de terminal luva `1,30-2,60MM2`. O código também consta na BOM oficial corrente como MP N1 sob `90263572` (`bom_occurrences O0001`). Portanto, o finding automático da rodada DEC-VAL-032 **`BOM_ONLY 10080004` é falso positivo comprovado por evidência documental**, independentemente da antiga ambiguidade de OCR. 

**Regressão obrigatória:** reconhecer `10080004` como presença válida na célula de componente na p2; nunca emitir `BOM_ONLY 10080004` para essa versão do desenho e BOM, mesmo com `complete_for_requested_scope=false`. Investigar por que OCR/tabular extraction informou `component_table_codes=55` / `matched_occurrences=32/56` mas deixou o item fora das ocorrências estruturais válidas; distinguir erro de token, limite de tabela, célula `A1`, segmentação e integração. Não resolver por hardcode do código. Exigir testes sintéticos com tabelas densas, coluna auxiliar A1, e tabelas com múltiplos blocos/linhas. **Status atualizado deste caso: `FP_PROVEN / VAL01_REGRESSION_FAIL`.** A conclusão geral da rodada permanece `CORPUS_REGRESSION_FULL=FAIL/INCONCLUSIVE` (há 1 erro de fonte no `90264161` e achados candidatos de `90264030` aguardando owner). A revisão dos outros dez candidatos de `90264030` não está incluída nesta inspeção.

## Log de execução — 2026-11-04 (DEC-VAL-033, reteste independente ChatGPT após deploy reportado `f5f27499c7`)

**HEAD publicado confirmado** via GitHub: `d0dc0617a8` (SHA completo `d0dc0617a86e2b7743725f23b781751ba920c0f1`). O SHA do runtime `f5f27499c7` foi **reportado por Devin**, não checado no host por este consumidor. Conexão EVA MCP real: `get_context` + `analyze(product.drawing_analysis,{product_code,compose_understanding:true})`, seguido de poll com `job_id`. **13/13 produtos acionados**; seis produziram comparação estrutural recuperável e sete finalizaram com erro tipado de fonte `product.drawing: source_unavailable 502 (timeout)`. Algumas consultas intermitentes retornaram `403 Forbidden`, mas houve recuperação posterior de jobs autorizados. Não tratar ausência de relatório causada por fonte como PASS nem FAIL da lógica.

| Produto | Resultado nesta rodada pelo ChatGPT | Evidência |
|---|---|---|
| `90263572` | **PASS do gate conservador / INCONCLUSIVE técnico** | 2/2 páginas, 32/56 ocorrências BOM tipadas, `bom_only=0`, `divergences=0`, `bom_occurrences_unverified=24`, limitação explícita `bom_only_unverified` e `presence_by_token_only=23`. **Falso `BOM_ONLY 10080004` não reapareceu.** A célula `10080004` **continua não reconhecida pelo OCR** — correção de decisão, não correção perceptiva. PDF de referência SHA `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e` foi revalidado no turno anterior, não baixado novamente nesta execução. |
| `90263520` | INCONCLUSIVE, gate conservador | 1/1 OCR, 20/20 matched, zero findings; BOM corrente já contém `50213064` (drift do antigo baseline). |
| `90264178` | INCONCLUSIVE, gate conservador | 1/1 OCR, 38/40 matched, zero findings; não reapareceu falso `DRAWING_ONLY 10090014`. |
| `90264161` | INCONCLUSIVE, **comparação executada** | 1/1 OCR, 8/8 matched, zero findings. **Melhoria operacional sobre a rodada anterior** que retornara `bom_unavailable 502`; resultado atual não prova cobertura funcional integral. |
| `90264302` | INCONCLUSIVE, gate conservador | 1/1 OCR, 6/6 matched, zero findings. |
| `90261606` | INCONCLUSIVE, gate conservador | 1/1 OCR, 11/12 matched, zero findings. |
| `90264017` | SOURCE_UNAVAILABLE, **sem comparação** | Job falhou com `product.drawing source_unavailable 502 timeout`; baseline 14p não retestado nesta rodada. |
| `90264030` | SOURCE_UNAVAILABLE, **sem comparação** | Job falhou com `product.drawing source_unavailable 502 timeout`; os dez achados anteriores continuam candidatos pendentes do owner. |
| `90480120` | SOURCE_UNAVAILABLE, sem comparação | `product.drawing source_unavailable 502 timeout`. |
| `90264004` | SOURCE_UNAVAILABLE, sem comparação | `product.drawing source_unavailable 502 timeout`. |
| `90264014` | SOURCE_UNAVAILABLE, sem comparação | `product.drawing source_unavailable 502 timeout`. |
| `90264043` | SOURCE_UNAVAILABLE, sem comparação | `product.drawing source_unavailable 502 timeout`. |
| `90264050` | SOURCE_UNAVAILABLE, sem comparação | `product.drawing source_unavailable 502 timeout`. |

**Conclusões:** `FALSE_POSITIVE_BOM_ONLY_10080004=FIXED_BY_FAIL_CLOSED` **PASS observado**, mas `OCR_CELL_RECOGNITION_10080004=NOT_FIXED`; `MCP_CHATGPT_PRIMARY_CASE=PASS`; `CORPUS_13_COMPARISON=INCONCLUSIVE (6/13 comparações; 7 fontes timeout)`; `VAL01_FINAL_APPROVAL_PENDING`. A condição 0 findings não é aprovação de desenho; `complete_for_requested_scope` e a quantidade de matches continuam essenciais. A bateria paralela apresentou indisponibilidade de fontes: próxima rodada deve controlar a concorrência (batches pequenos/serializados) e separar comportamento de rate limit da fonte, lifecycle do job e permissão de usuário, sem mascarar 502.

**Proveniência:** este log registra resultados da conexão live observados pelo ChatGPT; fingerprints novos de PDFs/BOM não foram coletados para os treze nesta rodada. Preservar baselines históricos e revisão de Engenharia pendente.

## Log adicional — 2026-11-04 (reteste controlado dos 7 `source_unavailable` + revisão visual `90264030`)

**Contexto:** continuação da bateria DEC-VAL-033. Repetição com concorrência reduzida (inicialmente um job, depois até dois), por `EVA.analyze(product.drawing_analysis,{product_code,compose_understanding:true})` + polls do mesmo `job_id`. A primeira tentativa para `90264017` teve `job_not_found` no poll, mas novo START criou outro job e este concluiu; anotar intermitência de lifecycle/roteamento (não declarar correção permanente). **Todos os 7 produtos antes impedidos por `product.drawing source_unavailable 502` concluíram agora a comparação.** A fonte de metadados `read(product,drawing)` estava acessível para os sete na rodada.

| Produto | Job final | Cobertura | Match BOM | Findings | Estado |
|---|---|---|---|---|---|
| `90264017` | COMPLETED | 14/14 páginas | 72/96 | 0; `bom_occurrences_unverified=24` | INCONCLUSIVE; sem falso `DRAWING_ONLY 10080535` |
| `90264030` | COMPLETED | 13/13 páginas | 77/82 | 10: cinco `DRAWING_ONLY`, cinco `BOM_ONLY` | DIVERGENCES_CANDIDATES; revisão visual parcial detalhada abaixo |
| `90480120` | COMPLETED | 2/2 | 10/10 | 0 | INCONCLUSIVE |
| `90264004` | COMPLETED | 1/1 | 14/14 | 0 | INCONCLUSIVE |
| `90264014` | COMPLETED | 1/1 | 16/16 | 0 | INCONCLUSIVE; relação `10380042` não verificada |
| `90264043` | COMPLETED | 1/1 | 19/20 | 0 | INCONCLUSIVE; três relações não verificadas |
| `90264050` | COMPLETED | 2/2 | 7/7 | 0 | INCONCLUSIVE |

**PDF oficial do `90264030` conferido novamente:** `read(product,drawing_download)` retornou `90264030.pdf` de 13 páginas, SHA-256 `909b440a84fb00868ead4825f8c558ccf2c233b673655941bb7d32b6d1c59692`, igual ao baseline histórico. Renderizadas páginas 2, 7 e 9–12, com inspeção das tabelas. **Evidência visual direta:** código `10080535` efetivamente está na coluna `Componente` / item B de cada tabela das páginas **9, 10, 11 e 12**, sob os conjuntos **`70260050`, `70260051`, `70260052`, `70260053`**, respectivamente; não são meras menções em revision_history. Página 7, tabela do conjunto `70260049`, contém em célula de componente o código candidato `10081686` (a leitura é visível em região pequena; guardar referência visual e, antes de homologação técnica, confirmar os dígitos em resolução apropriada). **Defeito/limitação adicional constatado:** os cinco `DRAWING_ONLY` no relatório MCP tiveram `parent_code=90264030` (raiz), mas a tabela impressa explicita pais de conjunto `70260049/50/51/52/53`. O vínculo **deve ser investigado e tratado como relação de parentesco não comprovada**, não corrigido arbitrariamente com dados da BOM. Não declarar relação com a raiz se a tabela fornece conjunto interno.

**Cinco `BOM_ONLY` continuam sem confirmação visual de ausência:** `10080292` sob `70260049`; `10080438` sob `70260050/51/52/53`. São candidatos de comparação estrutural, mas ausência exige examinar todas as regiões relevantes e qualidade de OCR, inclusive possíveis variantes de revisão; não homologar como NC a partir do finding isolado. A ocorrência `10080535` na página 7 não substitui prova da ausência de `10080292`. **Nenhuma publicação de NC ou desenho oficial.**

**Resultado operacional:** `SEVEN_BLOCKED_RETEST=PASS (7/7 jobs completed)`; `CORPUS_MCP_COMPARISON=13/13` **somando as duas rodadas DEC-VAL-033 no mesmo dia** (seis completados antes + sete agora). `VAL01_TECHNICAL_APPROVAL=PENDING`, com OCR da célula `A1/10080004` do `90263572` ainda não corrigido, falsa ausência já bloqueada por fail-closed e dez candidatos de `90264030` ainda sob revisão. Nenhuma mudança de código/deploy foi executada pelo ChatGPT. Esta rodada não recoletou fingerprint de BOM para cada produto, logo não afirmar igualdade temporal das fontes.

## Log adicional — 2026-11-04 (EVA #131, execução Devin — correção perceptiva real + proveniência de parentesco)

**Contexto:** retomada da Issue #131 após o registro anterior constatar que a recuperação de células do commit `67caa4875f` **não percebia** a célula real (o falso `BOM_ONLY 10080004` estava bloqueado pelo gate fail-closed, mas o código não era reconhecido — `recovery=[]` em execução in-container). Commit da evolução: **`daf0a8e564`** (`feat(engineering-api): EVA#131 — percepção de células densas + proveniência de parentesco (DEC-VAL-033 evolução 2)`).

**Causa-raiz confirmada (cadeia completa, evidência in-container sobre PDF oficial):**
1. `PdfiumExtractionAdapter.render_region` passava `crop=(left, top, right, bottom)` como retângulo, mas pypdfium2 interpreta `crop` como **quantidade cortada de cada borda** `(left, bottom_cut, right_cut, top_cut)` — todo crop recortava a região errada e podia lançar `Crop exceeds page dimensions` (que não era capturado e derrubava a análise).
2. `reference_dpi` único com fallback 200, mas páginas são renderizadas em dpi próprio (p2 do `90263572` a 110 dpi, 910×1287) — espaço de coordenadas inconsistente.
3. Região de recovery = união só das células tipadas (x∈[20,285]) — a célula A1/`10080004` vive no bloco direito (`Item|QTD|Componente`, x≈340–900) que a segmentação não tipou.
4. Margem do crop não era contabilizada na estimativa de pixels do orçamento.

**Correção (canônica e genérica, sem regra de produto):** `render_region` usa semântica correta de borda + clamp à página; `recover_absent_table_cells` expande a faixa vertical da tabela tipada por tokens na mesma faixa (captura blocos de colunas não segmentados), normaliza quadriláteros de 8 pontos (`_rect_of`), resolve `reference_dpi_by_page`, adapta dpi ao orçamento com margem contabilizada, e tolera falha de render/OCR sem derrubar o job. `_targeted_recheck` agora usa a página da ocorrência (antes fixa p1). Bridge propaga `reference_dpi_by_page` do pipeline vencedor.

**Evidência `90263572` (SHA `9021fce0…28d3e`, in-container sobre o código produtivo `daf0a8e564`):** `recover_absent_table_cells` retornou `10080004` página 2, `method=localized_ocr_recheck`, confiança 0.9999. O OCR de página lera `10060004`; o crop vetorial localizado lê `10080004`. **Aceite Frente 1 = ATENDIDO** (célula real reconhecida, sem uso do código esperado como evidência, sem regra específica de produto).

**Parentesco `90264030` (SHA `909b440a…9692`):** confirmado no dump real que `70260049–53` aparecem na região `component_table` das próprias folhas — em colunas tipadas como `description`/`quantity`, não `component_code`, por isso `set_col` nunca era detectado e `parent_code` caía na raiz fabricada. Correção: família `CONJ` (prefixo 7) como âncora de agrupamento — mesma linha (`row_group`, verificado) ou conjunto único da folha (`set_span`, verificado); `DRAWING_ONLY` sem pai comprovado agora carrega `parent_code=null` com `parent_source`/`parent_verified` explícitos em vez da raiz. Resultado sobre o dump real: `10081686→70260049` (p7), `10080535→70260050/51/52/53` (p9–12) — os cinco parentescos agora evidenciados pelo próprio desenho.

**BOM_ONLY `90264030`:** `10080292` e `10080438` **não aparecem em nenhum token/célula/contexto das páginas 7 e 9–12** (verificado sobre `code_contexts` completo do dump, 1436 tokens) — com tabelas lidas integralmente (cobertura completa), ausência permanece candidata legítima de divergência. **Permanecem candidatos pendentes de revisão da Engenharia — não promovidos a NC.**

**Confiabilidade MCP/jobs:** `job_not_found` isolado + retry OK é consistente com store process-local (TTL 3600s, restart recria registry) e/ou fingerprint de owner diferente — comportamento correto de isolamento, documentado no Doc 119; `502 timeout` sob bateria paralela = timeout de 30s do fetch delegado sob concorrência (fonte/latência downstream), resolvido com concorrência reduzida — sem mudança arquitetural (sem causa-raiz para Abstraction Gate).

**Testes:** `test_drawing_cell_recovery_eva131.py` novo (6 casos: quad 8pt, expansão de região por tokens, dpi por página, dpi adaptativo, falha de render, negativo) + `DRAWING_ONLY` sem raiz fabricada; 3 fixtures legados corrigidos para o gate ≥0.9 da DEC-VAL-033 (falhavam já na base). **Suite engineering-api: 102/102 PASS** (executado in-container contra o código do commit).

**Deploy:** `srv-api`, `git pull --ff-only` → `up-prod-sequential.sh --build engineering-api`; container `delpi-engineering-api` recriado e **healthy** com HEAD `daf0a8e564`.

**Resultado:** `OCR_CELL_RECOVERY_10080004=FIXED_PERCEPTUAL (conf 0.9999, localized_ocr_recheck)`; `PARENT_PROVENANCE_90264030=FIXED (5/5 com pai do desenho verificado)`; `BOM_ONLY_VALIDATION=5 candidatos mantidos (ausência provada, revisão pendente)`; `JOB_NOT_FOUND_ROOTCAUSE=DOCUMENTED (process-local store, comportamento correto)`; `502_TIMEOUT_ROOTCAUSE=downstream fetch 30s sob concorrência — resolvido serializando, sem mudança arquitetural`; `REGRESSION_SUITE=102/102 PASS`. `REGRESSION_13_MCP` pós-deploy e `CHATGPT_CONSUMER_PASS` permanecem **PENDING** até reteste independente.
