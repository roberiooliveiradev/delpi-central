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

## Log de execução — 2026-11-04 (pós-implementação OCR/localized recheck e parent provenance, reteste ChatGPT)

**Publicação GitHub confirmada:** `daf0a8e56401ce923f2c1a87b777e3e946a9b2ba` (código) e `1408f51881d429c69ee1094cc595c2800446bc09` (docs). Deploy/runtimes e testes in-container **reportados pelo Devin**, sem acesso independente ao host nesta execução. Conexão real EVA MCP: `analyze(product.drawing_analysis,{product_code,compose_understanding:true})` → job → `analyze(...,job_id)`. Não houve download e recálculo dos hashes de PDFs nesta rodada; usar SHA do corpus como referência anterior.

**`90264030` — MCP COMPLETED / `DIVERGENCES_CANDIDATES` / 13/13 páginas / 10 findings.** Os cinco `DRAWING_ONLY` agora portam **parent correto e evidência de provenance**: `10081686 → 70260049` p7 `row_group`; `10080535 → 70260050` p9 `set_span`, `70260051` p10 `row_group`, `70260052` p11 `set_span`, `70260053` p12 `set_span`. Nos cinco, `evidence.parent_verified=true` e `evidence.parent_source` preenchido. **`PARENT_PROVENANCE=PASS (5/5 no consumidor)`.** Os cinco `BOM_ONLY` permanecem como candidatos: `10080292` sob `70260049`, e `10080438` sob `70260050/51/52/53`, com BOM occurrence IDs `O0047/O0057/O0064/O0071/O0078`. `ENGINEERING_APPROVAL=PENDING`, nenhum achado virou NC.

**`90263572` — 1ª tentativa MCP `product.drawing source_unavailable 502 timeout`; nova tentativa isolada `aj-f9dd827901474c49` COMPLETED, `INCONCLUSIVE`, 2/2 páginas, `matched_occurrences=32/56`, `bom_only=0`, `bom_occurrences_unverified=24`, `divergences=0`. Fail-closed preservado. **Ressalva importante na evidência disponível ao consumidor:** inspeção da `report.guided_investigations.occurrence_results[0]` para `O0001 / 10080004` mostrou `component_code_in_drawing.state=AMBIGUOUS`, `observed_value=null`, `candidate_rows=[]`, `similar_candidates=[10060004]`, `search_history=EXISTING_EVIDENCE INCONCLUSIVE; CONTEXTUAL_SEARCH NO_CANDIDATE_REGION`. Busca estruturada no relatório retornado **não encontrou uma observação `observed_raw_value=10080004` com método `localized_ocr_recheck` associada a O0001**; embora outros códigos possuam `localized_ocr_recheck`, o consumidor não recebeu prova de recuperação de `10080004`. **Conclusão estrita:** `OCR_A1_BACKEND_RECOVERY=REPORTED_PASS`, porém `OCR_A1_CHATGPT_REPORT_GROUNDING=INCONCLUSIVE/NOT_PROVEN`, e `BOM_ONLY_FP_SUPPRESSION=PASS`. Não confundir ausência de `BOM_ONLY` com presença visual confirmada via percepção da EVA. Hipóteses: a evidência perceptual recuperada não foi propagada ao relatório/projeção guiada, ou ocorreu divergência na integração/limites; investigar sem hardcode, preservando provenance/page/box se disponível, e reconcile de OCR esperado vs observado.

**Bloqueio operacional:** primeira tentativa `90263572` falhou 502 na fonte; subsequente concluiu. Não classificar flutuação de disponibilidade como regressão de OCR. **Estados:** `PARENT_PROVENANCE=PASS`, `BOM_ONLY_VALIDATION=CANDIDATES_KEPT`, `MCP_CRITICAL_TWO_COMPLETED=PASS_AFTER_RETRY`, `OCR_A1_PERCEPTUAL_PROOF_IN_CONSUMER=PENDING`, `VAL01_TECHNICAL_APPROVAL=PENDING`.

**Próximo gate:** localizar o evento `recovery[{code:10080004,page:2,confidence:0.9999,method:localized_ocr_recheck}]` alegado em runtime e provar que chega pelo contrato do consumidor com relação ao código, página, região, evidência de OCR e identidade do PDF, sem usar o código da BOM para criar a evidência. Retestar a partir do consumidor após correção/observabilidade. Preservar os dez findings como candidatos à revisão da Engenharia.

## Log adicional — 2026-11-04 (EVA #131 / DEC-VAL-034 — evidência perceptual reconciliada ao relatório)

**Contexto:** reteste independente anterior achou `O0001/10080004` `AMBIGUOUS` + `NO_CANDIDATE_REGION` no `guided_investigations`, apesar do backend recuperar o código — a evidência saía apenas ao comparador (`drawing_tokens`), nunca ao universo da investigação guiada. Commit **`6a7fdc65c1`**.

**Correção:** `localized_recovery` no `drawing_understanding` + consumo na I-01 (`_check_component_code`) + `code_contexts` enriquecido + `box` do token OCR real lido (`box=null` era attr errado). Contrato RQ-VAL-052 com nulos explícitos, nada inventado.

**Verificado em produção (`6a7fdc65c1`, `delpi-engineering-api` healthy):** `O0001/10080004` → `MATCH_CANDIDATE`, `observed_value=10080004`, `page=2`, `region_box=[20,248,909,1038]@110dpi`, `bounding_box` quad real em espaço de página, `method=localized_ocr_recheck`, `confidence=0.9999`, `document_sha256=9021fce0…28d3e`. Sem contradição `CODE_OBSERVED`×`NO_CANDIDATE_REGION`.

**Suíte:** 107/107 PASS. Gate DEC-VAL-033 e corpus preservados. `REGRESSION_13_MCP` e `CHATGPT_CONSUMER_PASS` permanecem **PENDING** até reteste independente do relatório MCP.

## Log de execução — 2026-11-04 (DEC-VAL-034: reteste independente ChatGPT)

**GitHub PROVEN:** commit de código `6a7fdc65c16132726749c1ebfccd3415a0ecdd63` e docs `dee768d94f339587abdc83cff48286f7e108e257` encontrados. Deploy produtivo do SHA foi reportado por Devin; **o ChatGPT não consultou diretamente o host/container** e não pode garantir que o processo MCP que respondeu está nesse SHA.

**`90263572` — reteste MCP COMPARISON COMPLETED, mas AC perceptual NÃO PASSOU:** `analyze(product.drawing_analysis,{product_code:"90263572",compose_understanding:true})` → `aj-1aa5353a7a1d45af`, polling → relatório `INCONCLUSIVE`, 2/2 páginas, `matched=32/56`, `bom_only=0`, `bom_occurrences_unverified=24`, `divergences=0`. Porém em `report.guided_investigations.occurrence_results[0]` (O0001/10080004): `overall_state=INCONCLUSIVE`, `component_code_in_drawing.state=AMBIGUOUS`, `observed_value=null`, `evidence_refs=[]`, similar `10060004`, `search_history=EXISTING_EVIDENCE INCONCLUSIVE; CONTEXTUAL_SEARCH NO_CANDIDATE_REGION`. Inspeção completa da resposta JSON mostrou **zero ocorrências da chave `localized_recovery`** no relatório; `localized_ocr_recheck` aparece em investigações de outros códigos, mas **não há evidência perceptual nova vinculada a O0001**. O PDF SHA no audit foi `9021fce05c608655e538f67cdaac08c7484ebbe16a8888e83fbeec9ecaa28d3e`. `OCR_A1_CHATGPT_CONSUMER_PASS=FAIL`; `FALSE_BOM_ONLY_SUPPRESSION=PASS`. Não afirmar causa: considerar código/worker distinto, caminho de composição/projeção ou dados da job store; requer correlação segura build SHA/process and stage diagnostics.

**`90264030` — reteste MCP COMPLETED/PASS da hierarquia:** `aj-87f924d241334b17`, 13/13 páginas, `DIVERGENCES_CANDIDATES`, 10 findings preservados. 5 `DRAWING_ONLY`: `10081686→70260049` p7 `row_group`; `10080535→70260050/51/52/53` p9–12 (`set_span,row_group,set_span,set_span`), todos com `evidence.parent_verified=true`. 5 `BOM_ONLY`: `10080292→70260049` e `10080438→70260050/51/52/53` preservados como candidatos; nenhuma publicação NC. `PARENT_PROVENANCE_PASS`, `FINDINGS_GOVERNED_PASS`.

**Estado independente:** `GITHUB_COMMITS=PASS`; `MCP_E2E_TWO_REPORTS=PASS`; `OCR_A1_MCP_EVIDENCE=FAIL`; `BOM_ONLY_FAIL_CLOSED=PASS`; `PARENT_PROVENANCE=PASS`; `VAL01_FINAL_APPROVAL=PENDING`. Não declarar DEC-VAL-034 pronta para aceite pelo ChatGPT até reproduzir `O0001 MATCH_CANDIDATE` com `observed_value=10080004`, método, página e `evidence_refs` genuínos nesse consumidor.

## Log adicional — 2026-11-05 (DEC-VAL-034 aceite — diagnóstico 502/NameError)

O consumidor ChatGPT encontrou `502 upstream_error` e depois erro interno. Diagnóstico real (logs `delpi-engineering-api`): `NameError: 'out'` no retorno de `product.drawing_understanding` + `ClientDisconnect`/timeout upstream na primeira tentativa (pipeline síncrono). Corrigido em `9976f441a6` — `document`/`same_document_verified` passam a viver no envelope `understanding`. A primeira tentativa sem resposta era timeout de gateway (análise leva minutos); caminho canônico de longa duração permanece `product.drawing_analysis` com `job_id` + poll.

## Log adicional — 2026-11-05 (DEC-VAL-034 rev2 — PATH_DRIFT corrigido)

O `drawing_understanding` síncrono nunca executava `recover_absent_table_cells` (só `product.drawing_analysis`). `apply_localized_recovery` agora roda em ambos os caminhos (`abcdcc63f6`). Verificado em prod: `O0001/10080004` → `MATCH_CANDIDATE` + `evidence_refs` completos (método, página, region_box, box real, SHA `9021fce0…`, conf 0.9999). 772/773 overlay (1 falha fixture lmp_domain não relacionada). `CHATGPT_CONSUMER_PASS` permanece PENDING até reteste independente.

## Log adicional — 2026-11-05 (Framework-First SLANet — F1 trace + 2 fixes mínimos)

Trace produtivo comprovado: células SLANet alimentam apenas o resumo do relatório; a grade `i//8` é código morto semântico (component_table vem de understanding.py). Defeitos reais corrigidos (`00befcff78`/`2cb89f61a3`): `association` (OCR↔célula) propagada — estava calculada e descartada; fallback de crop fixo → `NO_TABLE_REGION` fail-closed. 101/101 overlay. `90263572`/`90264030` comportamento de percepção inalterado (SLANet cells não entram no component_table). `CHATGPT_CONSUMER_PASS` PENDING.

## Log adicional — 2026-11-06 (percepção nativa SLANet na imagem `6ffae36e`)

Medição lateral no container `delpi-engineering-api` após o deploy de `9c59bab3ef` (checkout `92ae661d04`). Não é comparador BOM nem consumidor MCP. SHA de cada PDF coincidiu com este catálogo. A página pedida foi a processada. Grade HTML consistente em todos. `multi_code_cells` conta células com dois ou mais códigos de 8–11 dígitos; não é precisão.

| Produto | Página | Linhas HTML | Células | Células com 2+ códigos |
|---|---:|---:|---:|---:|
| `90264302` | 1 | 4 | 36 | 1 |
| `90264161` | 1 | 5 | 31 | 2 |
| `90263520` | 1 | 15 | 174 | 1 |
| `90261606` | 1 | 9 | 47 | 0 |
| `90263572` | 2 | 44 | 252 | 1 |
| `90264178` | 1 | 19 | 156 | 6 |
| `90480120` | 1 | 6 | 36 | 2 |
| `90264004` | 1 | 12 | 94 | 2 |
| `90264014` | 1 | 7 | 60 | 3 |
| `90264017` | 9 | 5 | 21 | 1 (três códigos na mesma célula) |
| `90264030` | 2 | 1 | 5 | 2 |
| `90264043` | 1 | 11 | 122 | 4 |
| `90264050` | 1 | 4 | 12 | 3 |

`90264017` página 9: `70260008` está numa célula `rowspan=16` misturada com as letras de item. Status `INCONCLUSIVE`, sem pai inventado. Recortes `title_block` da mesma página e de outros desenhos também receberam grade do mesmo SLANet, sem VAL-02. Uma sequência contínua de OCR falhou com `RuntimeError` do Paddle depois de dois arquivos; a repetição em processo novo concluiu o restante. `CORPUS_BOM_REGRESSION=TEST_NOT_RUN`. `MCP_E2E=TEST_NOT_RUN`. `VAL01_COMPLETED=false`.

## Log adicional — 2026-11-06 (DEC-VAL-036 — recorte por colunas conectadas)

`90264017` p9 antes: célula `rowspan=16` misturando itens+códigos+carimbo. Depois (`native_slanet_v2`): recorte `[1,56,1273,303]` derivado das colunas de códigos; 11 linhas; `10081389`/`10081685`/`10091368` separados; `70260008` isolado; histórico excluído. Residual: item/qtd denso colapsa parcialmente. Deploy `47be2a8e0d` healthy.

## Log adicional — 2026-11-06 (poll do job MCP — erro interno)

Diagnóstico: job RUNNING virou erro no poll por store process-local (restart às 16:03 descartou) ou falha tipada silenciosa no delegated fetch (janela 401). Fix `63211b907d`/`8494379aeb`: `job_not_found` retriável + log de `DrawingAnalysisError`. 142/142. Reteste consumidor: criar NOVO job, aguardar COMPLETED, validar resultado + erro tipado se FAILED.

## Log adicional — 2026-11-06 (event loop — offload asyncio.to_thread)

Forense: `proc.communicate` síncrono no loop congelava a API inteira durante OCR isolado. Fix `5a9b86c6d2`: benchmarks via `to_thread`. Prod healthy. Reteste consumidor pendente — polls RUNNING durante OCR é o aceite funcional.

## Log adicional — 2026-11-06 (multipage OCR lifecycle — batch isolation)

Sequência 4-OK→RuntimeError→9×MemoryError: um filho só com RLIMIT_AS 12GB + reset de engine sem liberação nativa. Fix `216ee5fd8d`: batches de 4 páginas por filho (memória devolvida por morte do processo) + merge determinístico + coverage_status. Deploy healthy. Regressão 13 PDFs pendente no consumidor.

## Log adicional — 2026-11-06 (estabilidade nativa — batch=1 + RLIMIT 16GB)

Medição provou que VMS Paddle só é devolvido por morte do processo (reset in-process inútil: 16.1GB). Fix `cf4c4362d3`: filho por página + cap 16GB. Job anterior provou 12/14 com PARTIAL honesto; batch=1 isola falha por página. Regressão 13 PDFs pendente no consumidor.

## Log adicional — 2026-11-08 (DEC-VAL-037 — integridade documental SLANet, `a9fa4e6307`)

**Causa-raiz do `PdfiumError: Data format error` no job `aj-03ac71384ba140f9` (página 9):** refetch redundante do PDF após o OCR; falha chegava como dict sem `content` → `b""` → PDFium. Corrigido por **reuso dos bytes oficiais do benchmark** (um fetch por execução, SHA idêntico por construção) + gates tipados de entrada (`DOCUMENT_CONTENT_MISSING`/`DOCUMENT_HASH_MISMATCH`/`DOCUMENT_CONTENT_INVALID`/`PDF_OPEN_FAILED`) + cleanup de tmp na abertura.

**Deploy `a9fa4e6307`** (imagem `sha256:253de3fb…`, healthy): prova in-container sobre PDF oficial `90264017` (SHA `5452aabd…32ee` conferido com o índice): `component_table` p9 → **68 células nativas**, `error_kind=None`, `pdf_sha_match=true`. Corpus de 13 PDFs no novo SHA e job MCP autenticado pós-deploy: `TEST_NOT_RUN` neste executor — próxima rodada pelo consumidor ChatGPT.

## Log adicional — 2026-11-08 (DEC-VAL-038 — reconstrução geométrica de linhas SLANet)

Diagnóstico visual p9 `90264017`: células `rowspan` fundiam item/qtd de duas linhas (`"C 6 D 3"`). Correção `84b87d636b`: `line_texts` por bandas Y + distribuição pelo rowspan nativo. Caso sintético `C/6/10081389`+`D/3/10081685` PASS. Regressão 13 PDFs, balões e job MCP autenticado no SHA novo: `TEST_NOT_RUN` — próxima rodada pelo consumidor.

## Log adicional — 2026-11-08 (DEC-VAL-039 — fix real da reconstrução de linhas)

Bugs quad (`bb[3]-bb[1]=0`) impediam `line_texts`; fix `0a6d468f07` (cy/h por min/max + contenção em faixa-Y). Prova real p9 `90264017`: C/6/10081389, D/3/10081685, E/2/10091368 reconstruídos; F/G/K INCONCLUSIVE; FALSE_PROMOTED=0. 13 PDFs + job MCP: TEST_NOT_RUN (consumidor).


## Log adicional — 2026-11-08 (DEC-VAL-040 — evidência MCP 14p + 1p, plano de regressão de grade lógica)

**Planejamento canônico:** Doc 119 §50 (\`DEC-VAL-040\`). **Status:** \`PLANNED\` para a correção geral; não representa implementação ou aprovação técnica. Os SHAs abaixo foram verificados no consumidor ao executar os documentos oficiais; os dados de linhas são **candidatos**, com revisão visual assistida e sem aprovação formal pelo owner.

| Produto | SHA PDF conferido | Job MCP autenticado | Resultado de percepção | Limitações de associação |
|---|---|---|---|---|
| \`90264017\` (14p) | \`5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee\` | \`aj-8e1513f273cf44ec\` | \`COMPLETED\`, OCR FULL 14/14; SLANet p9 68 células tabela + 14 carimbo, erro nulo; C/6/\`10081389\`, D/3/\`10081685\`, E/2/\`10091368\` tipados | \`description=null\`, \`association_status=INCONCLUSIVE\` mesmo em C/D/E; F/9 separado do código \`10110676\`, G/K inconclusivos. **Correção local parcial, generalização não demonstrada** |
| \`90264004\` (1p) | \`5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4\` | \`aj-69310253b0f842d4\` | \`COMPLETED\`, OCR FULL 1/1, 172 tokens; SLANet 60 células tabela + 20 carimbo, erro nulo, SHA correspondente | \`item=null\`, \`quantity=null\`, \`description=null\` em linhas; A7/A8: native col4 \`10110092/10110093\`, native col5 contém descrições \`ETIQUETA ACETATO DE RAYON 1TB1/1TB2\`, mas saída tipa **descrição como component_code**. **Semantic column role=FAIL** |

**Inspeção visual direta do PDF oficial \`90264004\`:** as seis colunas lógicas são \`Código | Descrição | Item | QTD. | Comp. | Descrição\`. **Ground truth candidato sujeito a Engenharia:** A1/1/\`10110081\`, A2/1/\`10110082\`, A3/1/\`10110083\`, A4/1/\`10110087\`, A5/1/\`10110088\`, A6/1/\`10110091\`, A7/1/\`10110092\`, A8/1/\`10110093\`, com descrições distintas de etiquetas. Subconjunto \`50225478\` abrange A9/2/\`10080065\` e AA/2/\`10400035\`; subconjunto \`50225479\` abrange A9/6/\`10080065\` e AA/6/\`10400035\`. São **ocorrências candidatas separadas**, não prova de vínculos na BOM oficial.

**Matriz focal de regressão a executar (não confundir com resultado atual):**

| Caso | Falha baseline a reproduzir | Critério de aceite com ground truth aprovado |
|---|---|---|
| \`90264017\` p9 | C/D/E recuperados parcialmente; F/G/K e descrições sem associação completa | Não regredir C/D/E; resolver outros campos somente com divisórias/tokens/células que sustentem a associação; ambiguidades restantes explícitas |
| \`90264004\` A1–A8 | Item/qtd/descrição nulos e A7/A8 com descrição projetada como código | Identificar papéis funcionais apesar da troca de índices SLANet; separar \`10110092/10110093\` das descrições; zero falso código |
| \`90264004\` grupos | \`50225478\` e \`50225479\` com itens A9/AA repetidos | Preservar pai **candidato**, grupo, quantidade e identidade de cada ocorrência; não agregar por código |
| Demais desenhos (13 PDFs Doc120) | Layouts, células mescladas, colunas variáveis e tabelas extensas | Executar regressão por SHA/runtime, coletar erros por tipo/false promotions e separar holdouts; ausência de GT implica \`INCONCLUSIVE\`, não PASS |

**Gates do plano:** fixture real red→green pré-deploy, inspeção visual revisável, classes positivas/negativas, integração PDF original, teste de AuthZ/contratos, corpus 13 e holdouts, \`FALSE_PROMOTED_ASSOCIATIONS=0\`, aceite MCP pós-deploy para 1p+14p. Se os gates críticos não forem satisfeitos, **não fazer deploy**. Balões/E4, E2–E7 e VAL-02 permanecem congelados. \`ENGINEERING_APPROVAL=NOT_APPROVED\`; \`VAL01_COMPLETED=false\`.

**Evidências de conversa registradas na Issue #131:** comentários \`6727567112\`, \`6727591666\`, \`6727617764\`. Este log é aditivo: não sobrescreve entradas antigas nem transforma resultados históricos em execução do corpus no SHA atual.

## Log adicional — 2026-11-08 (DEC-VAL-040 — reconstrução lógica, `862b12ce34`)

Fixtures reais: 90264004 (A7/A8 descrição→código) e 90264017 (F/G/K). Prova: A2–A8 completos, A9/AA por grupo, descrições vinculadas; C/D/E preservados. Resíduo: A1/A5, F/G/K, 13 PDFs, job MCP — TEST_NOT_RUN.

## Log adicional — 2026-11-09 (DEC-VAL-040 — integridade de associação)

**HEAD ao iniciar:** `f1f4767b30`. **Código da associação antes do diff:** ainda o de `862b12ce34`. **Deploy:** não realizado — corpus dos 13 PDFs e holdouts `TEST_NOT_RUN` (PDF oficial ausente neste workspace; motor não reexecutado).

| product_code | pdf_sha256 | pages | ocr / slanet nesta rodada | resultado da fixture geométrica | regressão de corpus |
|---|---|---|---|---|---|
| `90264017` | `5452aabd3ddf94d5d004fe5c4d27c2daca9fcf8759a0c1b849b415d4769e32ee` | 14 | `TEST_NOT_RUN` (sem PDF local) | tupla G/9/`10110676` rejeitada; E/F/G/K separados quando o token do código está na banda | `TEST_NOT_RUN` |
| `90264004` | `5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4` | 1 | `TEST_NOT_RUN` | A2 não recebe `CHICOTE DE LIGACAO`; A7 descrição não vira código; A9 não cruza grupo | `TEST_NOT_RUN` |

Holdouts do Doc 120 não foram usados para ajustar a regra. Ausência de divergência com BOM não foi medida. `FALSE_PROMOTED` na fixture focal = 0 para G/9 e para a descrição de grupo. Precisão de campo sem ground truth da Engenharia: não declarada. `VAL01_COMPLETED=false`.

## Log adicional — 2026-11-09 (DEC-VAL-040 — corpus oficial no código `adceb6b5fa`)

Execução read-only no acervo `/mnt/fileserver/desenhos`, container descartável com teto de 5 GiB, pipeline PDFium + PaddleOCR + SLANet + `rows_from_native_cells` do commit `adceb6b5fa`. Os 13 SHAs conferem com este índice. `90264004` e `90264017` são o conjunto usado para diagnosticar a classe; os outros 11 são holdout e não ajustaram a regra. Não há ground truth aprovado pela Engenharia para precisão de campo: a coluna de precisão permanece não declarada. `false_g9` é a tupla completa G/9/`10110676`. `chicote_item` é descrição de conjunto publicada em linha que tem item.

| Produto | Papel | OCR | Tokens | Células SLANet | Linhas | Conflitos | false_g9 | chicote_item | Precisão |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| `90264302` | holdout | FULL 1/1 | 92 | 65 | 5 | 0 | 0 | 0 | não declarada |
| `90264161` | holdout | FULL 1/1 | 126 | 62 | 7 | 0 | 0 | 0 | não declarada |
| `90263520` | holdout | FULL 1/1 | 170 | 124 | 15 | 2 | 0 | 0 | não declarada |
| `90261606` | holdout | FULL 1/1 | 178 | 65 | 8 | 2 | 0 | 0 | não declarada |
| `90263572` | holdout | FULL 2/2 | 386 | 256 | 45 | 7 | 0 | 0 | não declarada |
| `90264178` | holdout | FULL 1/1 | 245 | 205 | 30 | 1 | 0 | 0 | não declarada |
| `90480120` | holdout | FULL 2/2 | 207 | 85 | 10 | 0 | 0 | 0 | não declarada |
| `90264004` | desenvolvimento | FULL 1/1 | 172 | 80 | 12 | 0 | 0 | 0 | não declarada |
| `90264014` | holdout | FULL 1/1 | 149 | 90 | 9 | 2 | 0 | 0 | não declarada |
| `90264017` | desenvolvimento | FULL 14/14 | 1852 | 737 | 94 | 5 | 0 | 0 | não declarada |
| `90264030` | holdout | FULL 13/13 | 1573 | 653 | 77 | 4 | 0 | 0 | não declarada |
| `90264043` | holdout | FULL 1/1 | 155 | 107 | 15 | 0 | 0 | 0 | não declarada |
| `90264050` | holdout | FULL 2/2 | 151 | 57 | 5 | 1 | 0 | 0 | não declarada |

Grades nativas inconsistentes, não usadas para substituir linhas: `90264017` página 11 e `90264030` página 9. Tempo somado da bateria: cerca de 318 s. `ru_maxrss` final do processo: 511248 KB. Nenhum dos 13 reproduziu a tupla falsa G/9/`10110676` nem promoveu `CHICOTE` a descrição de item. A imagem depois implantada é `sha256:1fded63c13df79d06009f6a28f6161c0aa2ad28ffd793f32f72b22e857f79bef` (git `0e452c20dc`). Job MCP autenticado desta rodada: `CONSUMER_MCP_ACCEPTANCE=PENDING`.

## Log adicional — 2026-11-09 (DEC-VAL-040 — recuperação A9 em célula agregada)

Correção em `rows_from_native_cells`: prefixo item via `_ITEM_TAIL`/`_ITEM_QTY` antes do skip de contexto de grupo; Y do item na banda-X. Integração oficial `90264004`: dois A9 publicados (2/`10080065`/`50225478` e 6/`10080065`/`50225479`). `90264017` p9: C–K preservados, `false_g9=0`. Bateria 13 PDFs (módulo candidato, container 5 GiB):

| Produto | Papel | OCR | Tokens | Células | Linhas | complete | conflicts | false_g9 | chicote_item |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `90264302` | holdout | FULL 1/1 | 92 | 65 | 5 | 1 | 0 | 0 | 0 |
| `90264161` | holdout | FULL 1/1 | 126 | 62 | 7 | 5 | 0 | 0 | 0 |
| `90263520` | holdout | FULL 1/1 | 170 | 124 | 15 | 8 | 4 | 0 | 0 |
| `90261606` | holdout | FULL 1/1 | 178 | 65 | 8 | 2 | 2 | 0 | 0 |
| `90263572` | holdout | FULL 2/2 | 386 | 256 | 44 | 32 | 9 | 0 | 0 |
| `90264178` | holdout | FULL 1/1 | 245 | 205 | 30 | 15 | 1 | 0 | 0 |
| `90480120` | holdout | FULL 2/2 | 207 | 85 | 10 | 9 | 0 | 0 | 0 |
| `90264004` | desenvolvimento | FULL 1/1 | 172 | 80 | 12 | 12 | 0 | 0 | 0 |
| `90264014` | holdout | FULL 1/1 | 149 | 90 | 9 | 8 | 2 | 0 | 0 |
| `90264017` | desenvolvimento | FULL 14/14 | 1852 | 737 | 94 | 38 | 6 | 0 | 0 |
| `90264030` | holdout | FULL 13/13 | 1573 | 653 | 77 | 47 | 5 | 0 | 0 |
| `90264043` | holdout | FULL 1/1 | 155 | 107 | 15 | 9 | 1 | 0 | 0 |
| `90264050` | holdout | FULL 2/2 | 151 | 57 | 5 | 3 | 1 | 0 | 0 |

SHA de todos os 13 conferem com o índice. Precisão de campo: não declarada (sem GT aprovado). Holdouts não ajustaram a regra. Alguns holdouts registram +1–2 `conflicts` tipados vs. bateria anterior (fail-closed); zero falsa promoção G/9 ou CHICOTE→item.


## Log adicional — 2026-11-09 (Handoff visual A9/AA, DEC-VAL-040, Doc 119 §53)

**Tipo:** observação visual do usuário + triagem da evidência MCP já comprovada. **Não é novo processamento OCR**, alteração de código, GT homologado ou deploy. Referência canônica: Doc 119 §53. **Documento oficial:** `90264004`, SHA `5b6717dfa7b8dcdc18f81b4657e1dcdf3410b9af42c8cf3109214df2f66719f4`, 1 página. Captura visual da tabela anexada à conversa (não armazenada no Git).

**Descrição da organização da tabela na captura:** seis colunas funcionais `Código | Descrição | Item | QTD. | Comp. | Descrição`. Célula mesclada de grupo `90264004 / CHICOTE DE LIGACAO` ocupa A1–A8; textos superiores azuis. Dois grupos inferiores com duas linhas cada: `50225478 / CF20AZUL-00290/10/05-0000-6500` e `50225479 / CF20AZUL-00240/10/05-0000-6500`; códigos/descrições de grupo azuis, campos dos componentes em vermelho. Separadores horizontais de linha estão visíveis.

| Grupo visual | Item visível | Quantidade visível | Código do componente visível | Observação |
|---|---|---:|---|---|
| `50225478` | `A9` | 2 | `10080065` | Primeira ocorrência de A9, texto vermelho |
| `50225478` | `AA` | 2 | `10400035` | Primeira ocorrência de AA, texto vermelho |
| `50225479` | `A9` | 6 | `10080065` | Segunda ocorrência de A9, texto vermelho |
| `50225479` | `AA` | 6 | `10400035` | Segunda ocorrência de AA, texto vermelho |

**Discrepância MCP:** consumidor autenticado `aj-c47df5e5efdb445a` `COMPLETED`, OCR FULL 1/1, SLANet tabela 60 células + carimbo 20; os códigos `10080065` e as quantidades 2/6 apareceram sob grupos diferentes, mas o identificador `A9` ficou ausente nos dois registros. Itens A1–A8 e AA tiveram recuperação melhor; A5–A8 `INCONCLUSIVE` por ambiguidade na percepção original. **A9 é visível na captura, mas não foi demonstrado se seu token está presente no OCR.**

**Hipóteses separadas, não comprovadas:** H1 contraste/cor vermelha altera reconhecimento de texto; H2 células mescladas de grupo com 2 linhas alteram a estrutura nativa; H3 espaçamento e divisórias causam fusão/associação errada; H4 token A9 existe, mas é descartado na associação ou qualificação de ambiguidade. A captura não demonstra causalidade. Próximo passo: inspeção instrumentada de `PDFium → PaddleOCR(tokens/quad/conf) → SLANet(células/spans) → rows_from_native_cells → understanding/MCP`, comparando A9×AA×A8 com PDFs oficiais SHA idêntico. Experimentos controlados colorido/grayscale/contraste **apenas diagnósticos**, sem alterar produção antes de validação cruzada.

**Gates futuros:** fixture real red→green, validação dos dois grupos sem achatamento, proteção de C–K no `90264017`, corpus 13 e holdouts, AuthZ/contratos/recursos, deploy canônico e reteste MCP quando houver correção e gates críticos PASS. Sem dados/GT oficiais aprovados para métricas gerais de precisão. **`A9_ROOT_CAUSE=TO_INVENTORY`; `COLOR_CAUSALITY=INCONCLUSIVE`; `CODE_CHANGED=false`; `DEPLOY_PERFORMED=false` nesta rodada; `ENGINEERING_APPROVAL=NOT_APPROVED`; `VAL01_COMPLETED=false`.**


## Log adicional — 2026-11-09 (VAL-01, amostra exploratória inédita; ChatGPT visual vs MCP EVA)

Amostra nova fora das 13 linhas do corpus original; **aditiva**, sem substituir regressão. PDFs oficiais obtidos via gateway delegado `drawing_download`, materializados e verificados por SHA no contexto de avaliação (não versionar PDF proprietário no Git). Fonte/estado de referência: Doc119 §55.

| Produto | Páginas | SHA-256 | Inspeção visual direta | EVA MCP | Avaliação |
|---|---:|---|---|---|---|
| `90264026` | 1 | `4d0c2e2f173cb2a427bb8de9b890018f9ca496b09b803b92e52ac0bf075dfec4` | Tabela inferior com 6 itens, 6 códigos de componente e descrições | `aj-a449624cde06485d`: COMPLETED, OCR FULL 1/1, 75 tokens, 6 rows | **FAIL de projeção de campo:** linha B mistura `90264026 10090010` em `component_code`; descrições `null` em todas as seis linhas, embora células tragam texto. BOM compare INCONCLUSIVE; não é NC. |
| `90264135` | 13 | `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` | Alternância de páginas de desenho e tabela, bloco principal e subconjuntos; p12 tem seis grupos `50225701/02/03/04/40/41` | `aj-1a368df473284c0d`: RUNNING na checagem inicial | **PENDING** validação estrutural do consumidor; inspeção humana parcial e não homologada. |

A amostragem é exploratória, sem critério de aleatorização estatística; PDFs não usados para ajustar regras até a decisão bounded correspondente. No novo PDF 90264026, zero divergências de BOM não significa fidelidade na coluna Componente. Conclusões de estrutura são `DRAFT/CANDIDATE`, sem GT aprovado da Engenharia.


### Resultado terminal da nova amostra — `90264135` (2026-11-09)

Job autenticado `aj-1a368df473284c0d` `COMPLETED` / `result_ready=true` no mesmo PDF oficial SHA256 `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3`. OCR `FULL 13/13`, 2.775 tokens, `quality_gate=EVAL_PENDING`; 294 linhas candidatas ao longo das páginas 2/4/6/8/10/12/13. Resumo das páginas tabulares:

| Página física | Linhas candidatas | Tuplas com item+qtd+código+descrição preenchidos | Linhas sem código | Linhas com conflito tipado |
|---:|---:|---:|---:|---:|
| 2 | 42 | 12 | 4 | 6 |
| 4 | 54 | 26 | 12 | 9 |
| 6 | 53 | 20 | 13 | 7 |
| 8 | 46 | 24 | 8 | 5 |
| 10 | 48 | 30 | 4 | 5 |
| 12 | 29 | 1 | 21 | 5 |
| 13 | 22 | 3 | 7 | 6 |

Métrica de preenchimento **não é precisão**; todos os status globais continuam candidatos. Exemplos verificáveis no payload MCP: p10 `component_code='10080192 10090316'`, p12 `component_code='50225702'` em linha com informação de conjunto agregada, p13 `component_code='4 5'`; p12 `A9` e `AA` têm descrição mas quantidade/código ausentes na mesma linha lógica. `bom_structure_comparison=INCONCLUSIVE` pois a fonte retornou `structure_not_provided`, não por correspondência validada. Esse desenho introduz um **residual de segmentação multipágina e de contexto de grupo** para investigação bounded em E1/VAL-01. Inspeção visual do ChatGPT foi parcial (páginas selecionadas) e não equivale a ground truth do owner. PDF oficial materializado e hash conferido localmente; não versionar binário no repositório.

### Log experimental — DEC-VAL-041 (2026-11-09) — perfis A/B/C/D

Investigação offline instrumentada; **sem deploy**, **sem mudança de lógica produtiva de associação**. HEAD `e94496503c8771eab87107c4d3d0dfeedb022295`. Detalhe canônico: Doc 119 §56.1.

| MODEL_OR_FRAMEWORK | VERSION / CONFIG | PDF_SHA | PAGE | RESULTADO MEDIDO |
|---|---|---|---:|---|
| Baseline A — PDFium+PaddleOCR+SLANet+Understanding | paddle 3.2.2 / paddleocr 3.3.0 / SLANet cached; isolation=inprocess | `4d0c2e2f…fec4` | 1 | 75 tokens; 40 células; `structure_consistent=false` (`span_conflict`); fallback `component_code="90264026 10090010"`; native cells separam grupo×código |
| Baseline A — idem | idem | `af47dd4c…edf3` | 10 | 295 células; `structure_consistent=true`; célula nativa já traz `10080192 10090316`; linhas boas coexistentes |
| Baseline A — idem | idem | `af47dd4c…edf3` | 12 | 200 células; `structure_consistent=true`; fragmentação `A9 1 10120148` em célula única |
| Baseline A — idem | idem | `af47dd4c…edf3` | 13 | 115 células; `structure_consistent=true`; `4 5` e `10080182 10090316` agregados |
| B — PPStructureEngine (PP-StructureV3) | símbolo AVAILABLE; pipeline create → `UNAVAILABLE` deps; `crop_box` TypeError no adapter | `4d0c2e2f…fec4` | 1 | **NOT_AVAILABLE operacional** — não comparado |
| B — PP-TableMagic | — | — | — | **NOT_AVAILABLE** |
| C — Ollama `qwen2.5vl:7b` | Q4_K_M; container mem 4.4 GiB | crop p1 região tabela | 1 | Load pede 12.4 GiB → HTTP 500; `VLM_BENCHMARK=BLOCKED_RESOURCE_OR_PERMISSION` |
| D — hipótese prefer-native + `rows_from_native_cells` | fixture `test_dec041_visual_table_diagnostic.py` | n/a (célula sintética espelhando medição) | 1 | 4/4 testes PASS; recupera `B→10090010` sem tokens inventados |

**Precisão de campo:** `TEST_NOT_RUN` / `INCONCLUSIVE` — sem GT owner. Completude MCP prévia permanece como no log acima; não reinterpretar completude como precisão.

**Negativos preservados:** suite `test_association_integrity_dec040.py` = 12 passed na imagem `infra-engineering-api:latest` (inclui A9/AA/A2 e falsa associação G/9). `CODE_CHANGED_PRODUCTIVE=false` nesta rodada.

### Log experimental — DEC-VAL-042 (2026-11-09) — gate nativo + descrição

Correção determinística em `apply_native_table_observations` / `native_cells_preferable`. **Deploy não autorizado.** Validação offline com bind do módulo Understanding sobre imagem `infra-engineering-api:latest` (digest pré-deploy A9 `sha256:2662390f…`). Detalhe: Doc 119 §57.

| PDF | SHA | Antes (DEC-041 / baseline) | Depois (candidato) | Gates |
|---|---|---|---|---|
| `90264026` | `4d0c2e2f…fec4` | B=`90264026 10090010`; desc null; topo fallback | B=`10090010`; desc `ISOLADOR…`; `span_conflict_tolerated`; fused=0 | `PASS` |
| `90264004` | `5b6717df…19f4` | A9×2 / AA×2 / false_g9=0 | A9=2 AA=2 false_g9=0 chicote=0; 12/12 codes+desc | `PASS` |
| `90264017` p9 | `5452aabd…32ee` | C–K corretos; false_g9=0 | C–K `PASS`; false_g9=0; conflicts tipados preservados | `PASS` |
| `90264135` p10–13 | `af47dd4c…edf3` | fusões nativas | residual `fused_codes=5`; false_g9=0 | `PASS` (não forçado) |

**Corpus 13 (Doc 120):** 13/13 `sha_match=true`; `false_g9` soma 0; `chicote_on_item` soma 0; inconsistências SLANet em p11 (`90264017`) e p9 (`90264030`) sem reabrir G/9. Precisão global **não declarada** (sem GT owner).

**Testes:** `test_dec042_native_table_gate.py` + `test_dec041_visual_table_diagnostic.py` + `test_association_integrity_dec040.py` + `test_table_perception_native.py` → 35 passed no harness com o patch.

### Log experimental — DEC-VAL-043 (2026-11-09) — preservação + deploy

Correção de perda silenciosa sob `span_conflict_tolerated` parcial (`reconcile_native_and_fallback_rows`). Detalhe: Doc 119 §58.

| PDF | Antes (DEC-042) | Depois (DEC-043) | Gate |
|---|---|---|---|
| `90264026` | 5 linhas nativas (perda vs 6 fallback); B ok | **6 linhas**; B=`10090010`+ISOLADOR; C/D preservados; topo `native_partial_over_fallback` | `PASS` |
| `90264004` | A9×2 AA×2 false_g9=0 | igual; 12/12 | `PASS` |
| `90264017` p9 | C–K; false_g9=0 | igual | `PASS` |
| Corpus 13 | false_g9=0 chicote=0 | 13/13 sha_match; Σ false_g9=0; Σ chicote=0 | `PASS` |

**Testes:** `test_dec043_native_preservation.py` + suites 041/042/040/native + PDF/MCP auth → 39+63 passed no harness com patch.

**Deploy canônico (2026-11-09):** `git pull --ff-only` → `./infra/scripts/up-prod-sequential.sh --build engineering-api` no `srv-api`. HEAD `e59a13f68885576b418dc91121b2c1ab7df53bc9`. Imagem anterior `sha256:2662390f…` tag `infra-engineering-api:pre-dec043-e59a13f688-rollback`. Imagem publicada `sha256:1c99c4bdae4aa5e6e26718d144102902c4e1b6f4e3563dadb5d9fd991f7ecf71`; container healthy; runtime prova `reconcile_native_and_fallback_rows` + `span_conflict_tolerated_partial`. Reteste na imagem publicada: 90264026 B=`10090010`+ISOLADOR, 6 linhas, topo parcial; 90264004/017 críticos PASS. MCP autenticado: `401` sem identidade → `CONSUMER_MCP_ACCEPTANCE=PENDING` (sem fabricar credencial).

### Log G0 — Baseline lock / rehash corpus (2026-11-09)

**TASK:** `EVA-VAL01-G0-FRAMEWORK-INVENTORY-BASELINE-LOCK`. Sem mudança de código produtivo, sem GT novo, sem benchmark de frameworks, sem deploy. Detalhe executivo: Doc 119 §59.5.

**Repositório:** `HEAD=ebd0a3533d20d93c001a2151fd9e567e9f116f85` = `origin/main`. **Runtime prod revalidado:** image `sha256:1c99c4bdae4aa5e6e26718d144102902c4e1b6f4e3563dadb5d9fd991f7ecf71`; `understanding.py` sha256 `3c06cdcfae469facc12905828899ef59c16bbaf599ab06e18079898ceca98f8b` (local = container).

**CONFIG_HASH (fingerprint G0):** `9b2e314e82dedd5c4dea047962ab1bfba1b8a09dbe856667186252a3c2c25e77` — paddle 3.2.2 / paddleocr 3.3.0 / paddlex 3.3.13 / pypdfium2 4.30.1 / PDFium 133.0.6899.0 / SLANet pdiparams sha256 `9d33d47b174bcb9fb63f94dac54a4d01a974da6d0c56ddb51cf0e38ed43f7a60` / DPI 200 / `TABLE_PERCEPTION_REVISION=native_slanet_v3`.

**Rehash fileserver `/mnt/fileserver/desenhos`:** 13 PDFs do índice + diagnósticos `90264026` (`4d0c2e2f…fec4`) e `90264135` (`af47dd4c…edf3`) → **15/15 MATCH**. Códigos do índice oficial inalterados. PDFs **não** montados no filesystem do container nesta inspeção (`SOURCE` = host fileserver).

**Baseline tests (read-only, imagem publicada):** `test_drawing_perception_r9` + `test_slanet_document_integrity` + `test_dec041_*` + `test_dec042_*` + `test_dec043_*` + `test_association_integrity_dec040` → **49 passed**. Reexecução MCP/OCR live do corpus 13: `TEST_NOT_RUN` (fora do orçamento G0).

**Holdout / GT:** nenhum ground truth homologado pela Engenharia neste log; split holdout formal permanece gap para G1. `VAL01_COMPLETED=false`; `ENGINEERING_APPROVAL=NOT_APPROVED`.

### Log G1 — Anotação visual 90264135 + split/holdout (2026-11-09)

**TASK:** `EVA-VAL01-G1-VISUAL-GROUND-TRUTH-AND-HOLDOUT`. Sem código, sem tuning, sem deploy. Ledger: Doc 119 §60. Artefatos: `docs/12-roadmap-e-evolucao/engineering/eva-val01-g1/`.

**PDF `90264135`:** SHA `af47dd4cfbbbd25c0530948e2454ed9a4f6fb9a3ce2aeef0c6ceeb050d98edf3` reconfirmado no fileserver; páginas físicas **10 / 12 / 13** anotadas em DRAFT (`annotations/90264135_p*.json`). Overlays raster **não versionados** (`.local/eva-val01-g1-overlays/`); hashes em `overlays/overlay-registry.json`.

**Contrastes (não GT):** p10 fusão `10080192 10090316`; p12 `50225702` como código de linha; p13 `component_code='4 5'`.

**Split:** development=`90264026/004/017/135`; validation_exposed=demais 11 do índice; **`TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE`**. `GT_APPROVAL_STATUS=OWNER_BLOCKED`. `VAL01_COMPLETED=false`.

### Log G1 — Completude estrutural geométrica 90264135 (2026-11-09)

**TASK:** `EVA-VAL01-G1-STRUCTURAL-GT-COMPLETION-AND-OWNER-HANDOFF`. Sem código produtivo, sem tuning, sem deploy. Ledger: Doc 119 §60.1.

**Fonte:** SHA `af47dd4c…edf3` `MATCH`. Render DPI 200; PNG p10/p12/p13 hashes `f0cef06a…` / `cf9cb4f5…` / `7e2f80f0…` (registry local).

**Anotações geométricas DRAFT (reescritas com grade completa no escopo selecionado):**

| Página | coverage | rows×cols | cells | annotation SHA-256 |
|---|---|---|---|---|
| 10 | `COMPLETE_SELECTED_REGION` | 15×6 | 64 | `98d39af4d1f6c3b84c03069bca117fa9da750aa85d66ce1b200170ba9e26333c` |
| 12 | `COMPLETE_SELECTED_REGION` | 16×7 | 82 | `73a27e2a2ebd76cacaf6b1aca21b7608b8e5f35f858ff1571871d53a23cf3551` |
| 13 | `COMPLETE_SELECTED_REGION` | 19×6 | 86 | `31b557512109e0695fc93d41bd1f2bc7d335368b207cd3b2c71f86618f8181aa` |

**Overlays de células:** `p10/12/13_cells_overlay.png` SHA `e9c5a7c4…` / `eb61979f…` / `4ee45099…` (`.local/`, não no Git).

**Validador offline:** `scripts/validate_g1_annotations.py` → PASS. Expected isento de fusões `10080192 10090316` e `4 5`. Holdout: `TRUE_UNSEEN_HOLDOUT=NOT_AVAILABLE`. `GT_APPROVAL_STATUS=OWNER_BLOCKED`. `VAL01_COMPLETED=false`.

### Log G2 — First-loss 90264135 + inventário Totus (2026-11-09)

**TASK:** `EVA-VAL01-G2-FIRST-LOSS-AND-TOTUS-STRUCTURE-CONTRACT-INVENTORY`. Sem código produtivo, sem G3/G4, sem deploy. Ledger: Doc 119 §61. Artefatos: `docs/.../eva-val01-g2/`.

**PDF:** SHA `af47dd4c…edf3` `MATCH`. Trace read-only no container `delpi-engineering-api` (dumps `.local/eva-val01-g2/`, hashes em `evidence-registry.json`).

**First-loss PROVEN:**

| Caso | Fronteira | Evidência |
|---|---|---|
| p10 A2/A3 | SLANet cell merge → Understanding funde campo | OCR tokens separados; célula `10080192 10090316` + `line_texts` |
| p12 50225702→AE/AH/AG | SLANet rowspan=11 → Understanding sem parent | OCR OK; subset tipado como `component_code` |
| p13 `4 5` | OCR rodapé `4`+`5` (seq. 1…8) → SLANet célula → `component_code` | não é componente Totus |

**Totus:** inventário `get_product_structure` / SG1010+SB1010; `CONTRACT_GAP` occurrence_id e revisão PDF; live 90264135 `TEST_NOT_RUN` (AUTH).  
**Decisão:** SLANet isolado insuficiente nestes layouts; G3 recomendado após ack; fix não implementado. `VAL01_COMPLETED=false`.

### Log G3 — Benchmark framework-first 90264135 (2026-11-09)

**TASK:** `EVA-VAL01-G3-NATIVE-TABLE-FRAMEWORK-BENCHMARK`. Sem código produtivo, sem G4, sem deploy. Ledger: Doc 119 §62. Artefatos: `docs/.../eva-val01-g3/`.

**PDF:** SHA `af47dd4c…edf3` `MATCH`. GT=`DRAFT`. SLANet operacional; PP-StructureV3 / TRPV2 / TableCellsDetection **não operacionais** (sem pesos/deps; probe de download limpo — cache G0 restaurado).

**Achados estruturais:** crop Understanding amplo vs crop G1 DRAFT — P13 elimina `4 5`; P12 elimina rowspan monolítico e preserva AE/AH/AG+códigos; P10 permanece fundido no SLANet com `line_texts`.  
**Decisão:** SLANet suficiente como motor geométrico com crop correto; resíduos = integração (regioner + Understanding). G4 candidato: crop hardening + `line_texts`/papéis — **sem** novo framework. Smoke `90264026` OK (não holdout). `VAL01_COMPLETED=false`.

### Log G4 — Integração mínima tabelas (2026-11-09)

**TASK:** `EVA-VAL01-G4-MINIMAL-TABLE-INTEGRATION-FIX`. Código candidato Understanding/regioner; **sem deploy**. Ledger: Doc 119 §62.2. Artefatos: `docs/.../eva-val01-g4/`.

**PDF evidência (replay G2 dumps, SHA af47dd4c…edf3):** célula SLANet p10 com `line_texts` → códigos separados; p13 `4 5` não promovido; crop exclui strip de índices. Hierarquia subset em fixture rowspan PASS; giant cell u_crop p12 permanece residual (depende crop correto — G3).

**Regressão unitária:** DEC-040–043 + percepção/SLANet + G4 = 64 passed. **Corpus 13 live:** `TEST_NOT_RUN`. Não declarar generalização; GT G1 `OWNER_BLOCKED`. `VAL01_COMPLETED=false`.

### Log G4 closeout — pipeline real 90264135 (2026-11-09)

**TASK:** `EVA-VAL01-G4-INTEGRATION-REAL-PDF-REGRESSION-CLOSEOUT`. Sem deploy. PDF SHA `af47dd4c…edf3` MATCH via srv-api `/mnt/fileserver/desenhos`.

**Real:** p10 A2/A3 códigos+qtd separados PASS; p13 sem promoção `4 5` PASS; p12 hierarquia `50225702→AE/AH/AG` **não demonstrada** no crop Understanding (RESIDUAL). Unit 82 passed. Corpus 13 live `TEST_NOT_RUN`. GT DRAFT. `VAL01_COMPLETED=false`.

### Log G4 P12 structural boundary repair (2026-11-10)

**TASK:** `EVA-VAL01-G4-P12-STRUCTURAL-BOUNDARY-REPAIR`. Sem deploy. PDF SHA `af47dd4c…edf3` MATCH.

**First-loss:** crop Understanding page-wide → SLANet perde hierarquia; crop G1 sem coluna do pai rejeitado.  
**Fix:** `hierarchical_code_columns` (gate >70% largura) + override Y de grupo + split de qty repetida por índice.  
**Real p12:** pai `50225702` → AE/10010028/1, AH/10080897 (qty UNKNOWN — célula SLANet sem qty), AG/10110676/2.  
**Regressão:** p10 A2/A3 PASS (connected); p13 sem falso código PASS. Unit G4+DEC040–043+SLANet/perception **68 passed**. Corpus 13 live `TEST_NOT_RUN`. `VAL01_COMPLETED=false`.

### Log G4 field association completeness (2026-11-10)

**TASK:** `EVA-VAL01-G4-FIELD-ASSOCIATION-COMPLETENESS`. Sem deploy. PDF SHA `af47dd4c…edf3` MATCH.

**AH qty:** OCR `2@788` órfão (1,5px fora da célula) → fill por banda Y da linha; empate abstém.  
**P10 desc:** mixed não bloqueia description; split multilinha em 2ª passagem.  
**Real:** p12 AE/AH/AG qty+desc PASS; p10 A2/A3 descrições PASS; p13 sem `4 5`. Unit **72 passed**. Corpus 13 `TEST_NOT_RUN`. `VAL01_COMPLETED=false`.

