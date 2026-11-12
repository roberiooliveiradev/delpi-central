# 313 — INT-1 | Revisão de coordenação: requisitos, primeira divergência e fechamento finito

**Data:** 2026-11-12  
**Tipo:** COORDINATION / DOCUMENTATION ONLY  
**TASK_ID:** DELIA-C3-T2-INT1-COORDINATION-REQUIREMENTS-AND-CAUSAL-CLOSURE-REVIEW-01  
**BASE_HEAD_REVIEWED:** `a832b5318dfa388903a998ff8609d3dbf7931db1`  
**STATUS:** REVIEW / SEM ALTERAÇÃO DE RUNTIME  
**AUTORIDADE:** Documentos 16/293, ledger, residual register e decisões congeladas superiores. Este registro não substitui essas fontes nem aceita a etapa automaticamente.

## 1. Decisão de coordenação e disciplina causal

O PO reforça como regra de execução: **jamais atribuir a falha ao LLM por exclusão ou intuição**. Para cada defeito, demonstrar a primeira fronteira divergente e testar causas alternativas em: `USER OBJECTIVE → ADMISSION → MODEL-VISIBLE CONTRACT (B1/B2/B3) → MODEL SELECTION → ARGUMENT CONSTRUCTION / LOCAL MUTATION / SCHEMA VALIDATION → AUTHZ → MCP → OWNER / DOMAIN → EVIDENCE PROJECTION → COVERAGE / SUFFICIENCY → OUTCOME → USER PRESENTATION`. A presença de descrição no código não prova que chegou ao modelo; `tools/list` não prova execução; `HTTP 200` e `GROUNDED` não provam satisfação. A inferência real não prova ausência de defeitos determinísticos. Instrumentar entradas/saídas e SHA/config com dados sanitizados; não expor secrets, tokens nem chain-of-thought.

Classificar cada alegação `PROVEN | TO_INVENTORY | PLANNED | TARGET`; testes `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`. Identificar owner e contrato antes da correção. Aplicar `EXISTING_EQUIVALENT` e `REUSE_DECISION`; preferir o menor diff, RED/GREEN, outcome real e comparação baseline/candidato. Não criar Agent, router, resolver, catálogo, permissão ou autoridade paralela.

## 2. Reancoragem do estágio e da decisão original

- **C3/T2:** a liberação histórica de implementação e o deploy histórico não equivalem a homologação funcional aceita. Em 2026-11-10, PO manual FAIL (P1/P2/P3) levou à trilha subordinada INT-0/INT-1; Documento 16 §2026-11-10 preserva `T2_FUNCTIONAL_ACCEPTANCE=REWORK`, sem avanço.
- **Decisão sobre Agent:** o Documento 16 definiu **quatro responsabilidades cognitivas** (compreensão, investigação, avaliação de suficiência, síntese), **não quatro Agents**. INT-1 reutilizou/estendeu **um Agent Pydantic AI** e MCPToolset/interop/evidence/finalization existentes; outros Agents ou avaliação separada não foram aprovados.
- **Última evidência:** Documento 312 / implementação commit `342092217d07e6fc5d97c991f9dbd94a3794ecfd` (não confundir com HEAD posterior com commits de outras áreas). Perfil real `qwen/qwen3-14b`, instrução v2-2 fingerprint `3692299dac74c26e`, provas em ambiente DEV isolado. Produção não recebeu automaticamente os últimos ajustes.
- **Estado canônico preservado:** `INT1_STAGE_ACCEPTANCE=PENDING_COORDINATION_REVIEW`, `INT1_CLOSED=NO`, `INT2/INT3/T3=NOT_AUTHORIZED`, `PRODUCTION_DEPLOY=NOT_AUTHORIZED`. **NEXT:** revisão independente dos requisitos e evidências; nenhuma promoção por documentação.

## 3. Matriz de requisitos versus evidências

| Requisito / risco | Evidência conhecida | Estado de coordenação | Lacuna para fechar |
|---|---|---|---|
| INT-1: reuse/extend do Agent investigativo existente, sem novo router | Docs 310–312: Agent único, Pydantic AI nativo, contratos MCP live | **PROVEN_IN_CODE** | Revisão independente do diff e da autoridade congelada |
| Compreender objeto e selecionar capability semanticamente | Doc 310 G1/P1/M1 DAVI-first 3/3; Doc 311 IG1–IG4 adequação first tool 4/4 | **PASS_IN_SAMPLE** | Não extrapolar para todos os objetivos / providers / schemas |
| Contratos recebidos pelo modelo | Docs 307/312 B1/B2/B3 (provider request pré-HTTP, tool count 15) | **PASS_IN_SAMPLE** | Evidência não inclui bytes HTTP nem todos os schemas possíveis |
| Usar identificadores empresariais naturais | Doc 312 R1 código PROC-0034 e R2 título via search→UUID; owner TÉO reutiliza `ProcessoRepository.get` | **PASS_IN_SAMPLE** | Árvores grandes continuam truncadas |
| Argumentos válidos e feedback de erro | Doc 312 B4: helper DÉLIA injetava `query` fora do schema; gating por declared_properties + explain_arguments; RED/GREEN | **CAUSE_PROVEN / FIX_TESTED** | Revalidar regressões e schemas aninhados complexos sem retries cegos |
| Resultado negado comunicado sem bypass | Doc 310 AUTH-DENY real; Doc 312 R4 TÉO permitido+DAVI negado | **PASS_IN_SAMPLE** | Garantir apresentação de conteúdo autorizado com proveniência em todos os partial paths |
| Completude de árvore/decomposição e cobertura de identificadores | Doc 312 R1 `result_truncated`; helper `_attempt_identifier_roots` aceita valores escalares estruturados | **OPEN_MATERIAL_REVIEW** | Verificar falsa cobertura por menção incidental; inventariar paginação/continuação do owner; não aumentar budget arbitrariamente |
| Satisfação final das perguntas originais PO | P1 produto positivo em avaliações posteriores; P2 processos e P3 formatos eram motivadores do FAIL; docs posteriores têm vários probes, não uma homologação consolidada equivalente | **PENDING_CONSOLIDATED_EVIDENCE** | Reconciliar evidência posterior por objetivo, usuário, SHA, ambiente, resposta final; testar somente gaps reais |
| Renamed-tool / mudança de provider/schema | Documento 16 registrou `TEST_NOT_RUN` no gate inicial; provas posteriores cobrem casos novos, não substituem automaticamente a matriz específica | **TO_VERIFY** | Determinar DoD canônico e evidência aplicável; só executar se bloqueador |
| Regressão completa, segurança e Outcomes da trilha T2 | Documento 293 L/A/O/R impõe gates cumulativos; Doc 312 relata 2 testes de baseline pré-existentes | **NOT_ACCEPTED_AS_FULL_GATE** | Reconciliar L/A/O/R e owner da dívida; evitar declarar PASS para suíte com falhas |
| Generalização | Docs 311–312 samples pequenos e independentes, alguns resultados parciais | **PROVEN_IN_SAMPLE_ONLY** | Nenhuma generalização estatística / universal demonstrada |

**Atenção:** statuses `PASS_IN_SAMPLE` e `PROVEN_IN_CODE` são descrições da evidência, não novos estados canônicos de aceite. `L/A/O/R` do Documento 293 são uma trilha de fechamento mais ampla e **não** devem ser confundidos com gates cognitivos INT-1.

## 4. Causas de código já comprovadas (não culpar modelo)

1. Doc 307: `EnvelopeHintedToolset` não preservava dicas no ciclo Pydantic AI; schemas `anyOf/oneOf` nullable exigiram correção.
2. Docs 304/310: descrições e semântica dos contratos DAVI/TÉO eram insuficientes para distinguir hierarquia de produto e processo; owner corrigiu descrições.
3. Doc 308→309: sujeito DEV e grants/cache Core provocaram `AUTHZ_DENIED`; negativa legítima não é falha do LLM.
4. Doc 310: `AUTHORIZATION_DENIED` não era preservado até projeção/finalização de forma suficiente; fluxo de retry podia tratar negativa como NO_PROGRESS.
5. Doc 311→312: TÉO fazia cast UUID onde o processo já tinha resolução canônica por código.
6. Doc 311→312: `focus_arguments_on_next_identifier` inseria `query` não declarado nos argumentos e causava suas próprias rejeições de schema (7×; 0 invocações MCP).
7. Doc 312: a projeção de cobertura estava acoplada ao formato DAVI `data.root.code`; ajuste por valores estruturados exige segurança contra cobertura incidental.

Para defeitos novos, **prova de primeira divergência precede prompt engineering, atribuição ao Qwen e modificação de instrução**. Resposta model-authored não é fonte de fato/autoridade.

## 5. Próxima decisão finita e escopo congelado

**Passo único da coordenação (DOC/REVIEW, sem runtime):** consolidar em uma matriz de aceite INT-1 cada requisito do Documento 16 e contrato aplicável, SHA/config/prova real e classificação: `SATISFIED_PROVEN | FAILED_MATERIAL | INCONCLUSIVE | NOT_RUN | OUT_OF_SCOPE_ACCEPTED` (rótulos de análise, não status automáticos). Reconciliar explicitamente as perguntas P1/P2/P3 originais e a generalização exigida; não repetir testes com evidências válidas equivalentes.

**Se permanecerem bloqueadores materiais:** apenas uma task bounded orientada aos residuais já identificados: (a) completude de árvores / paginação owner e correspondência de evidência ao objetivo; (b) apresentação autoritativa de resposta parcial, se a matriz demonstrar lacuna real; (c) testes originais PO/renamed tool somente onde a evidência de aceite estiver faltando. Para cada defeito: primeira divergência → owner → contrato existente → RED/GREEN → Qwen real somente no cenário afetado → outcome. Questões DAVI `NEEDS_*_PROJECTION` e dívida de testes têm owners separados; não incorporá-las automaticamente ao INT-1 se não bloquearem critério canônico.

**Regra anti-loop:** nenhuma bateria nova genérica, reescrita livre de instructions ou expansão em cascata. Um único registro de bloqueadores com owner, SHA, teste faltante e condição objetiva de fechamento. Quando o conjunto de evidências já satisfizer os requisitos, submeter decisão independente de `ACCEPT | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`; não avançar fase sem decisão canônica e ledger. Se houver decisão de arquitetura requerida, STOP no slice.

## 6. Checklist mínimo para aceite

- Requisitos e status referenciados ao Documento 16/ledger no HEAD; comparação da evidência original PO com as correções posteriores.
- Nenhuma falha material atribuída ao LLM sem confronto com contrato B1/B2/B3, mutação/validação local, resposta owner, projeção, coverage/outcome e frontend.
- Evidências no SHA/config avaliado; testes determinísticos reais e Qwen DEV nos casos que o DoD exige; classificar `TEST_NOT_RUN`/inconclusivo de forma honesta.
- Security/AuthZ fail-closed: Core/Domain autoridade; denied explícito; partial sem leak e sem bypass; nenhum grant para maquiar eval.
- Completude correta ou parcial explicitamente comunicada (sem falso `OBJECTIVE_SATISFIED`).
- Revisão independente antes de `INT1_CLOSED=YES`; INT2/INT3/T3 e deploy seguem bloqueados até autorização superior.

**NEXT=COORDINATION_INT1_REQUIREMENTS_EVIDENCE_MATRIX_AND_FINITE_ACCEPTANCE_DECISION**.
