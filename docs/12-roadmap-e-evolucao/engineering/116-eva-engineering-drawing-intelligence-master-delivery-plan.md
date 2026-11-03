# 116 — EVA Engineering Drawing Intelligence | Master Delivery Plan (M0–M5)

**Status:** PLANNED — proposta de programa, não implementação nem aprovação técnica.  
**Data-base:** 2026-11-02.  
**Owner de coordenação:** EVA — Architecture / Coordination.  
**Domínio e aprovação de qualidade:** responsáveis técnicos de Engenharia DELPI (nomes, GT e thresholds: TO_INVENTORY).  
**Referência de execução:** R9.9, docs 107–115, especialmente doc 115; HEAD de implementação e runtime devem ser revalidados antes de cada marco.  
**Tipo de mudança:** documentação de roadmap; nenhuma alteração de código, API, RBAC, infraestrutura ou feature gate.

## 1. Decisão de direcionamento

Parar de conduzir a evolução por prompts individuais de correção. Adotar um programa de **seis marcos finitos (M0 a M5)**, com escopo definido, contratos, métricas, responsáveis e critérios objetivos de entrada/saída. A mesma task executora contém diagnose → fix → tests → eval → review; falhas reproduzíveis não se tornam novos programas. Escalação ocorre para bloqueios comprovados, decisões de autoridade ou mudança material de escopo.

**Objetivo de produto:** analisar desenhos técnicos DELPI e de clientes, dentro de famílias de documentos explicitamente suportadas, para produzir observações estruturadas e relatórios **DRAFT/CANDIDATE** com fonte, revisão, região, evidência, incerteza e comparação autorizada com dados oficiais. Não implica análise universal de qualquer desenho, decisão técnica autônoma, publicação ou aprovação.

**Princípio:** inteligência ampla + autoridade estreita, explícita e governada. O PDF, OCR, modelo, MCP e relatório candidato nunca são fontes oficiais de produto/BOM/roteiro/inspeção ou autoridade de aprovação.

## 2. Linha de base factual e pendências

### PROVEN por teste independente em ChatGPT (escopo limitado)

Chamadas autenticadas de `product.drawing_understanding` pelo conector EVA retornaram:
- `90264302`: PDF SHA-256 `f33447b271a3518643559582d79cf54527b85778537cfb1e20a5ccf5d989f0ef`; 92 tokens OCR; SLANet `executed=true`; 34 células; 22 com texto; score ~0,9595; estado `CANDIDATE_GENERATED`.
- `90264161`: PDF SHA-256 `8d9fe28a19cae334abd6eaa3b0fb13059aecad715672b0dfd6aaf10462b85195`; 126 tokens OCR; SLANet `executed=true`; 44 células; 29 com texto; score ~0,9385; estado `CANDIDATE_GENERATED`.
- MCP respondeu sem `no_ocr_evidence` ou 500 na última verificação independente; `table_structure_engines` expôs execução real e células OCR. Os números não são prova de correção de engenharia.

### REPORTED / requer verificação no owner

- Infraestrutura R9.9 usa volume persistente de modelos PaddleX/OCR + symlink; sete modelos provisionados. Builds/restarts/recreates foram reportados PASS em doc 115; o chat não executou um recreate independente.
- Baseline produtiva como default, BOM fail-closed, isolamento CPU e AuthZ inalterada constam nos relatórios anteriores; revalidar no SHA e runtime de cada release.
- Token refs de células estavam vazios no aceite R9.8 apesar do texto associado; providenciar rastreabilidade token→célula. Houve ambiguidades em células; não confundir associação geométrica com tipagem semântica.
- Modelo SLANet/estrutura não implica competência comprovada em cotas, tolerâncias, símbolos, materiais, revisões ou BOM.

### TO_INVENTORY

Repositório/HEAD efetivo ao iniciar M0, ledger atual, owners de GT, contratos de fontes de revisão/roteiro/inspeção, diversidade de desenhos e direitos de uso de desenhos de clientes, runtime/volume hashes integrais, cobertura e qualidade semântica, limites de recursos em carga.

## 3. Outcome e limites de escopo

O primeiro release assistido, dentro de famílias de desenhos aprovadas, deve conseguir:
1. Identificar documento/produto/revisão quando presentes, marcando ausência/ambiguidade.
2. Segmentar regiões: title block, tabela, revisão, notas, vista e campo desconhecido.
3. Extrair item/quantidade/código/descrição da tabela correta, com vínculos espaciais e token de origem.
4. Distinguir componente de metadado administrativo; não usar texto de cabeçalho como componente.
5. Tratar cotas, unidades, tolerâncias e notas técnicas somente nas classes de símbolos/representações formalmente incluídas no M3.
6. Comparar candidatos com produto/BOM oficiais por contracts e live AuthZ; não inventar divergências pela ausência de OCR.
7. Entregar relatório candidato: observações, concordâncias, divergências, UNKNOWN/AMBIGUOUS/NOT_COMPARABLE, fonte, revisão, boxes, confidence metodológica e limitações.

**Fora do aceite inicial:** CAD/DWG generation, aprovação/publicação automática, extração universal sem suporte, inferência silenciosa de material/cota/tolerância, escrita em sistemas oficiais, substituição de owners e acoplamento ao Chat legado. Capacidades não previstas não bloqueiam o encerramento do programa.

## 4. Ownership, authority e boundaries

| Responsabilidade | Owner/authority | Regra |
|---|---|---|
| Identidade/SSO | Keycloak | identidade não autoriza |
| Apps, rotas, RBAC, policy | Core | AuthZ live, backend-first |
| Host e navegação | Portal | apresentação não autoriza |
| Produtos, BOM, roteiro, inspeção, desenho oficial | Domain APIs e sistemas de Engenharia | source of truth e contrato de leitura |
| Experiência e workflow | Portal Engenharia | separa fonte, candidato e aprovação |
| Perception, reasoning, análise candidata | EVA | observação != fato |
| Aprovação técnica e GT | Engineering owners | decisão governada |
| Execução técnica quando aplicável | Automation Hub / operação autorizada | idempotência, limites, rollback |
| Integração semântica | MCP/A2A | interoperabilidade, não authority |

Arquitetura padrão: Clean Architecture, Ports & Adapters, DDD pragmático. Domain/Application não dependem de HTTP, banco, framework, SDK de LLM/CAD/MCP ou internals de outros contextos. Reusar `PerceptionEnginePort`, `drawing_perception_candidate.v1`, `drawing_understanding.v1` e adapters enquanto válidos. Novo contrato/serviço/registry só após Abstraction Gate; mudança de owner, SoT, bounded context ou authority = `ARCHITECTURE_DECISION_REQUIRED`.

Pipeline lógico (não necessariamente novos módulos):
`SOURCE → PERCEPTION (PDF/OCR/SLANet) → EVIDENCE → ENGINEERING UNDERSTANDING → GOVERNED DOMAIN CROSS-CHECK → ANALYSIS CANDIDATE → HUMAN REVIEW → APPROVAL/PUBLICATION by owner`.

## 5. Plano por marcos

### M0 — Evaluation Foundation (OBRIGATÓRIO ANTES DE EXPANDIR)

**Pergunta:** quais acertos, erros, tipos de desenho e falhas são mensuráveis hoje?

**RQ-M0**
- Inventariar código, HEAD, ledger, contratos, fontes, permissões, modelos, configurações, casos, testes e capacidade instalada.
- Versionar dataset, hashes, revisão, direitos de acesso, critérios de seleção e separação train/dev, validation e holdout; proibir contaminar holdout durante tuning.
- Proposta inicial: **20 desenhos** — 2 conhecidos + 5 tabelas variadas + 3 revisões/admin + 5 cotas/tolerâncias + 5 desenhos de clientes. Os 18 adicionais são **TARGET**, não disponíveis comprovados. Representatividade e quantidade final sujeitas a aprovação do GT owner.
- Definir formato de anotação com ID do documento/revisão, página, região/box, célula, token, campo, relação, valor, unidade, estado, expectativa, ambiguidade, anotador, revisor e versão.
- Estabelecer critérios de anotação, dupla revisão de campos críticos, conflitos e adjudicação por Engenharia.
- Construir harness offline/reproduzível de avaliação (SHA do código/modelo/dataset/config, outputs expected vs actual, overlays, falhas por classe, custo CPU/RSS/latência).
- Medir baseline R9.9 antes de qualquer mudança semântica; registrar métricas e limitações sem substituir accuracy por confidence.

**AC-M0 (gate de saída):** corpus versionado e autorizado; GT inicial revisado; split protegido; avaliações reproduzíveis no SHA; métricas e thresholds *propostos por risco* e aprovados pelo owner; resultados baseline publicados; gaps de fontes/permissões classificados. Sem GT técnico, M0 não pode receber PASS completo.

**Entrega:** Dataset Manifest v1 + Annotation Guide v1 + Evaluation Harness + Baseline Scorecard + RQ/AC ledger.

### M1 — Document Structure

**RQ-M1:** identificar e distinguir regiões de quadro administrativo, revisão, tabela de componentes, notas, vistas e UNKNOWN; suportar detecção e topologia de linhas/células/colspan/rowspan dentro das classes de layout do corpus; alinhar boxes e coordenadas crop→página; referenciar tokens por ID persistente, sem confiar só em `_tokens_sample`.

**AC-M1:** matriz por região e família; table structure/cell matching contra GT; sobreposições e ambiguidades explicitadas; falsos positivos em quadros administrativos medidos; overlays auditáveis; generalização no holdout; zero regressão de contrato/MCP/baseline.

**Entrega:** Regions/Structure Candidate v1 + avaliação por layout + taxonomia de erros.

### M2 — Typed Semantic Extraction

**RQ-M2:** transformar tokens/células em campos `item, qty, component_code, component_description, document_id, revision, customer` conforme GT e formato autorizado; tratar multilinhas, spans, duplicidades, colunas trocadas e tabelas parciais; distinguir texto administrativo; preservar raw text, normalized text, token_refs, page/region, source/revision, transform, uncertainty; nunca imputar campos críticos faltantes.

**AC-M2:** precisão/recall por campo, por classe e por família; vínculos item↔qty↔code↔description verificados; métricas de associação/abstenção; sem hallucinated components nos casos críticos; amostra GT com revisão humana e holdout satisfaz thresholds aprovados.

**Entrega:** Typed Table Candidate v1 (aditivo/compatível, se aprovado) + field-level scorecard + exemplos de falhas.

### M3 — Technical / Geometric Interpretation

**RQ-M3:** definir inicialmente um catálogo suportado (ex. texto de cotas/unidades, tolerâncias explícitas, notas e símbolos selecionados) mediante inventário e revisão de Engenharia; separar detecção de texto de associação à geometria; verificar revisão/contexto/página; validar consistência dimensional onde for possível; casos não suportados retornam UNKNOWN/NOT_CHECKED, nunca valor presumido.

**AC-M3:** avaliação por categoria e gravidade, dimensional correctness em amostras GT, taxa de afirmação não suportada, comportamento com fonte conflituosa e revisão divergente, aprovação humana de casos críticos. Classe não validada permanece fora do escopo do release.

**Entrega:** catálogo técnico suportado + Technical Observations Candidate + scorecard validado.

### M4 — Governed Official Cross-check

**RQ-M4:** inventariar owner/source/contract/AuthZ/freshness/errors para cadastro, BOM, revisões e somente demais domínios efetivamente autorizados; comparação multiplicity-aware em itens, quantidades e componentes; distinguir MATCH, CONFLICT, UNKNOWN, NOT_COMPARABLE e NOT_CHECKED; não transformar ausência de token em ausência de componente; preservar versionamento e divergência entre fontes.

**AC-M4:** integração por Domain APIs oficiais, permissões negativas/fail-closed, contratos e regressões, precisão de divergência/false alarm medida com GT, cenários duplicados/MP/PI, revision mismatch, PDF ausente, BOM indisponível e NOT_COMPARABLE preservados. Sem contrato oficial, declarar owner-blocked; não criar proxy paralelo ou cross-db join.

**Entrega:** comparison candidate + contract matrix + conflict evals + traceability.

### M5 — Governed Product Release

**RQ-M5:** relatório candidato legível com trechos/boxes/origem, scores somente defensáveis, conflitos, lacunas e explicações; UX que diferencia fato oficial, observação e hipótese; revisão técnica humana com decisão no owner; logs sanitizados, performance, observabilidade e rollback; segurança, prompt injection em PDFs/OCR, Core/domain AuthZ e generalização.

**AC-M5:** todos os AC obrigatórios M0–M4 no escopo do release; holdout sem tuning retrospectivo; testes reais de produto, segurança e performance; owners aprovam qualidade para *uso assistido*; operações read-only no contrato governado; deploy com SHA/digest verificáveis, smoke/E2E autenticado e aceite independente por ChatGPT; métricas pós-release e fallback. Aprovação técnica formal permanece fora do modelo.

**Entrega:** release candidate + relatório de aceite técnico + runbook + matriz de limitações + decision record de go/no-go.

## 6. Quality model, métricas e política de thresholds

Métricas mínimas: region precision/recall, table structure accuracy (células, spans e grid), token→cell precision/recall, field precision/recall, linked row accuracy, revision correctness, dimensional correctness por categoria, unsupported-claim rate, abstention/UNKNOWN correctness, conflict detection precision/recall, permission-boundary outcomes, task outcome humano, CPU/RSS/wall-clock.

**Thresholds:** definidos pelo owner de Engenharia no M0, por classe de risco, antes de olhar o holdout. Nunca inventar um 95% genérico. Separar false positive crítico, missing evidence e erro de OCR. Score SLANet `~0.96` não é precisão de Engenharia. Métricas precisam de denominadores, amostras, intervalos quando viável, dataset SHA e configuração.

**Confiabilidade operacional:** hard gates para ausência de writes não autorizados, bypass AuthZ, erro silencioso, vazamento de secrets, regressão do baseline e publicação sem owner. Testes unitários verdes são necessários, não suficientes.

## 7. Protocolo de execução para parar iterações infinitas

Para cada marco, antes de código:
1. `HEAD → branch/status/worktrees → origin/main → authorities/rules → ledger → source/owner/consumer/contract → RQ/AC → baseline/evidence`.
2. Aplicar Abstraction Gate e definir menor diff; separar contrato aditivo de mudança comportamental ou breaking.
3. Executar um único pacote bounded por marco, com testes unit/contract/integration/architecture/regression e E2E real, além das evals de IA correspondentes.
4. Ciclo local `REPRODUCE → ROOT CAUSE → FIX → TEST → EVAL → VALIDATE` até PASS. **Limite de gestão sugerido: três ciclos de correção por incremento**; não é autorização para PASS parcial. Ao atingir limite sem progresso, escalar com evidência e opção de mudança de abordagem/escopo — não gerar automaticamente novo prompt.
5. Falha reproduzível dentro do escopo/autoridade do executor deve ser resolvida internamente antes da entrega. Sem OAuth/GT/owner, status `BLOCKED` ou `TEST_NOT_RUN` explícito.
6. Release somente após AC obrigatórios PASS, thresholds e contratos aprovados, resultados de holdout, segurança e capacidade operacional, e autorização pertinente. Fazer deploy pelo procedimento canônico do repo; não equiparar push a deploy.
7. Aceite independente ChatGPT verifica contrato e runtime por ferramentas EVA; owner de Engenharia aprova qualidade técnica. Nenhum executor se autoaprova.

**Status permitidos:** fatos `PROVEN | TO_INVENTORY | PLANNED | TARGET`; execução `PASS | FAIL | PENDING | INCONCLUSIVE | TEST_NOT_RUN | STALE_EVIDENCE`; desvio `EXECUTION_DRIFT`; review `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`. Um requisito obrigatório não pode ser aceito como residual. `ACCEPT_WITH_RESIDUAL` apenas quando residual não bloqueante, explícito e com owner.

## 8. Entregáveis e evidência por marco

Cada relatório deve conter:
- TASK, scope, owner, fontes canônicas, consumidores, contracts, RQ/AC e decisões.
- BASE_HEAD/FINAL_HEAD/TESTED_SHA/PUSHED_SHA/DEPLOYED_SHA/image digest quando aplicável.
- Dataset ID/hash, splits, expected outputs, model IDs/checksums, threshold version, metrics, failure taxonomy, overlays e revisão humana.
- Teste E2E sobre documentos oficiais autorizados, casos negativos, generalização e regressão; RAM/CPU/latência/concurrency.
- Security/AuthZ/no-writes/no-egress, BOM gate, data provenance, document revision, limitations, postcondition, residual search, drift.
- ITERATIONS/ROOT_CAUSES/FIXES e sinais de escalonamento.
- Evidência PASS sem rótulo hipotético; TEST_NOT_RUN se não foi executado.

## 9. Dependências e riscos explícitos

| Risco/dependência | Mitigação / condição |
|---|---|
| GT não aprovado | bloquear aceite de acurácia; obter owner e annotation guide M0 |
| Dataset estreito (dois PDFs repetidos) | amostra diversa e holdout controlado |
| OCR confunde admin/componente | M1 region grounding + M2 typed extraction; medição de falso positivo |
| Cota detectada sem geometria | M3 separar texto de associação e declarar UNKNOWN |
| Fonte BOM/revisão indisponível | M4 NOT_COMPARABLE/NOT_CHECKED + owner blocker |
| Prompts e modelos superajustados | blind holdout, RQ/AC e thresholds congelados |
| Modelos/cache/infra falham após recreate | manifest/hashes + build/recreate E2E + rollback |
| E2E MCP não testado pelo executor | manter TEST_NOT_RUN, ChatGPT independente antes de aceite |
| Cross-boundary authorization | live Core/domain AuthZ fail-closed, nenhum SDK/tool como authority |
| Crescimento arquitetural não justificado | Abstraction Gate; nenhuma nova abstração por conveniência |
| Dados sensíveis de cliente | acesso legitimado, isolamento, retenção e sanitização |

## 10. Critérios de conclusão do programa

`PROGRAM_ACCEPTED` somente se:
1. Classes de desenhos, campos e funções suportados estiverem declarados e versionados.
2. M0–M5 obrigatórios estiverem PASS no escopo acordado, sem gap material.
3. GT aprovado pelo owner e holdout demonstrar os thresholds acordados.
4. Nenhuma característica crítica inexistente for inventada.
5. Relatório candidato separar evidência, inferência, conflito e ausência.
6. Comparação oficial usar AuthZ live e owners corretos, sem promover inferência a dado oficial.
7. Produção e MCP passarem testes autorizados independentes, com rollback e baselines.
8. Responsáveis técnicos aprovarem uso assistido, sem aprovação/publicação automática.
9. Capacidades fora de escopo forem registradas como roadmap futuro, sem manter a entrega eternamente aberta.

## 11. Primeiro bounded step autorizado por este plano

**Somente planejamento/inventário M0**, não implementar M1–M5 por interpretação deste documento.

Produzir: current-head/ledger reanchor, lista proposta de desenhos e autorizações, definição de owners/anotadores, contrato de GT, matriz RQ/AC-M0, harness existente vs gaps, método de métricas e scorecard baseline. O início de coleta/rotulagem de desenhos de clientes depende de acesso e owner; publicação de GT depende de revisão técnica. Depois submeter M0 à Coordination antes de mudanças materiais.

## 12. Handoff entre chats

- **Coordination:** aprova roadmap, mudanças de escopo, thresholds propostos e arquitetura cross-cutting.
- **Foundation / Inventory:** fontes e datasets existentes.
- **Engineering Intelligence / Drawings / Multimodal:** percepção, GT, evals e semântica de desenho.
- **Product / BOM / Routing / Inspection Integrations:** fontes oficiais e contratos.
- **Integration / Acceptance / Evals:** gates independentes, generalização e outcome.
- **Security / AuthZ / Governance:** limites de acesso e safety.
- **Documentation / Architecture Review:** ledger, traceability e status.

**Próxima tarefa recomendada:** `EVA.M0.DRAWING.EVAL.FOUNDATION.INVENTORY.AND.CONTRACT`.

---
**Nota de evidência:** este documento registra a proposta e os resultados de chat anteriormente observados. Não declara novo código executado, avaliação técnica validada, novo deploy, GT existente ou release aprovado.
