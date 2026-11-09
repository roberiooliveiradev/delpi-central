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


---

# ANEXO A — Playbook operacional do Devin por marco (M0–M5)

**Natureza:** detalhamento executivo do plano aprovado para documentação; tarefas futuras propostas, não evidência de execução. **Regra de precedência:** este anexo complementa os gates e responsabilidades das seções 1–12. Autoridades do repositório, owners e contratos efetivos prevalecem sobre sugestões de arquivos/classes/implementações. Não criar convenções paralelas.

## A.1 Contrato de execução comum — válido em todos os marcos

**Antes de trabalhar:** ler \`AGENTS.md\`, rules, plano 116, docs 107–115, ledger e artefatos canônicos; coletar \`HEAD\`, branch, status, worktrees, \`origin/main\`, versões de modelos e runtime. Inventariar equivalentes antes de abstrair. Para cada tarefa registrar \`RQ → AC → owner → source → consumer → contract → implementation → tests/evals → outcome\`.

**Pacote fechado do Devin:**
1. \`INVENTORY\`: mapa de arquivos/contratos/executáveis, dados e owners de cada capability.
2. \`SPEC\`: RQ/AC verificáveis, matriz de risco, dataset e critério de conclusão.
3. \`DESIGN GATE\`: demonstrar por que mudança é necessária, onde pertence e por que o contrato existente não resolve; mapear read/write e draft/publish.
4. \`IMPLEMENT\`: menor diff correto; sem import cross-context, DB de outro owner ou dependência do Chat legado.
5. \`TEST\`: unit/contract/integration/negative/regression + eval real e holdout, conforme fase; testados no mesmo SHA/config/model.
6. \`VALIDATE\`: comparar expected vs actual; registrar falsos positivos, falsos negativos, ambiguidade, evidência, erro e limitação; não confundir confidence com accuracy.
7. \`FIX\`: corrigir causas reproduzíveis sob autoridade do executor; regressões reiniciam gates afetados.
8. \`HANDOFF\`: somente após AC obrigatórios PASS, ou BLOCKED com causa, owner, evidência e ação requerida. Limite de gestão de **até três ciclos de correção por incremento**; se não convergir, exigir decisão de Coordination (não é PASS parcial).
9. \`DEPLOY\`: apenas se necessário ao marco e autorizado pelas regras vigentes de operação; testar pré-deploy e pós-deploy, hash/digest, resource fit, baseline/fallback e postcondition.
10. \`INDEPENDENT ACCEPT\`: ChatGPT verifica MCP onde disponível; responsável de Engenharia valida conteúdo técnico. Executor não se autoaprova.

**A cada marco, o Devin entrega** um changelog com SHA, RQ/AC matrix (PASS/FAIL/BLOCKED/TEST_NOT_RUN), diff, teste executável + comando, dataset/model/config SHA, matriz por desenho e por campo, exemplos de erros, overlays/evidence references, segurança, recursos, testes negativos, relatório de regressão, residual search, status de deploy e limitações. Preferir anexos pequenos e referenciados a um relatório sem evidências.

**Stop-the-line:** erro de autenticação/autorização, output técnico fabricado, contaminação de holdout, alteração de fonte oficial, teste crítico FAIL ou regressão produtiva => interromper promoção e recuperar/rollback conforme processo autorizado.

## A.2 M0 — Evaluation Foundation: backlog executável

**Entrada:** R9.9 funcional reportado/testado pelo ChatGPT em dois desenhos, mas sem GT aprovado, threshold nem cobertura de generalização. **Dono de execução:** Devin / Engineering Intelligence; **aprovação:** GT owner de Engenharia + Coordination.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M0-T01 | Inventariar arquivos e contratos de desenho, OCR, SLANet, understanding, métricas, API/MCP e scripts. Localizar GT/eval harness existente antes de criar algo. | capability/source/owner map; referências de arquivo e SHA |
| M0-T02 | Executar baseline read-only nos dois PDFs conhecidos e congelar entradas SHA, revisão, modelo, flags, latência, RSS, CPU e JSON candidato. | baseline manifest + raw results sanitizados |
| M0-T03 | Levantar com o owner candidatos a 18 desenhos adicionais e autorizações para DELPI/cliente; evitar usar conteúdo confidencial em fixtures públicas. | document selection register: família, layout, revisão, acesso, status |
| M0-T04 | Propor split desenvolvimento/validação/holdout por família e revisão (evitar desenhos quase idênticos em splits diferentes). Travar holdout e suas regras de acesso. | dataset v1 manifest, split rationale, hash e política anti-leak |
| M0-T05 | Elaborar annotation guideline com classes de região, células/spans, token references, código/item/qtd/descrição, revisão, dimensões, conflitos e UNKNOWN. | annotation schema + examples positivos/negativos |
| M0-T06 | Definir protocolo de anotação: anotador, revisor de Engenharia, adjudicação, versão, discrepâncias e trilha de decisão. | owner/annotation workflow aprovado ou OWNER_BLOCKED |
| M0-T07 | Implementar/adaptar harness offline sem acesso de escrita a dados oficiais; gerar overlay, diff expected/observed, métricas com denominadores e relatório por classe. | testes do harness + relatório reproduzível por SHA |
| M0-T08 | Executar baseline contra GT disponível; marcar ausência de referência como EVAL_PENDING, nunca accuracy PASS. | scorecard inicial + failure taxonomy |
| M0-T09 | Propor thresholds por criticidade (ex.: componente/quantidade/cota) e regras de abstenção, depois obter decisão explícita do owner. | threshold matrix versionada e decisão |
| M0-T10 | Auditar segurança do corpus, retention, secrets, permissão de cliente e rastreabilidade de revisão. | data access/privacy gate |

**Testes M0:** determinismo do harness em execuções repetidas; hash/split leakage; anotações conflitantes; GT incompleto; ausência de PDF; dataset version mismatch; overlay crop→página; controle de acesso; qualidade de métricas. Exigir checks sobre nenhum caso com expected vazio contado como acerto.

**AC de saída M0:** (a) versão e fonte das amostras aprovadas; (b) GT validado ao menos para o escopo inicial acordado; (c) harness reproduzível; (d) baseline scorecard por família/classe; (e) thresholds e metodologia aprovados; (f) release/test split guardado; (g) ledger atualizado. **Dependência externa:** se GT/owner não estiver disponível, concluir apenas inventário PREPARED e registrar M0 BLOCKED — não iniciar tuning M1 para declarar qualidade.

**Não fazer no M0:** implementar novo OCR, novo modelo, novo serviço, tipagem de BOM ou modificar contrato produtivo sem defeito demonstrado.

## A.3 M1 — Document Structure: backlog executável

**Entrada:** M0 com dataset/GT e thresholds region/table aprovados.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M1-T01 | Medir no GT onde o current understanding confunde title block, revision, component table, notes e drawing area. | confusion matrix por região/layout |
| M1-T02 | Formalizar coordenadas px/página/crop, escala, rotação, page index, offsets e versões; testar transformações bidirecionais. | coordinate invariants + image overlays |
| M1-T03 | Normalizar regiões candidatas com estados DETECTED/AMBIGUOUS/UNKNOWN, sem transformá-las em áreas oficiais. | contrato compatível + testes |
| M1-T04 | Validar SLANet grid, rows/cols, spans e bbox, inclusive células parcialmente fora do crop e conteúdo administrativo na mesma banda. | grid/topology metrics e casos específicos |
| M1-T05 | Reconciliar tokens OCR completos com regiões/células, armazenando IDs/ref e justificativas de conflitos/unassigned em output candidato. | token→cell trace e contagens reproduzíveis |
| M1-T06 | Melhorar apenas falhas comprovadas de segmentação e topologia; não reclassificar arbitrariamente uma região para inflar recall. | fixes ligados a casos e diffs de eval |
| M1-T07 | Comparar baseline anterior vs implementação em validation e holdout, separando aumento de células de acurácia estrutural. | benchmark with matched PDF/config, FP/FN |
| M1-T08 | Executar regressão MCP, contratos v1, OCR/SLANet model load, budget e read-only. | E2E + operational safety report |

**Testes M1:** layouts com múltiplas tabelas, title block perto da tabela, colunas mescladas, rotação, multipágina quando suportada, OCR vazio, escala/crop variados, overlaps e offsets inválidos. Guardar overlays por caso para auditoria humana.

**AC de saída M1:** regiões corretas dentro dos limites aprovados; estrutura de células/spans GT; referência espacial verificável; menos falsos positivos de admin como tabela; preservação de baseline e contrato; holdout satisfaz thresholds. **Não sair de M1** por “SLANet reconheceu mais células”.

## A.4 M2 — Typed Semantic Extraction: backlog executável

**Entrada:** M1 aprovado; ground truth de campos por tipo de tabela, origem da revisão e owner da semântica definidos.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M2-T01 | Inventariar padrões reais de item, código, quantidade e descrição nas famílias de desenhos. Registrar variantes e ambiguidades sem inventar regra empresarial. | field taxonomy aprovada ou TO_INVENTORY |
| M2-T02 | Definir estrutura candidata compatível: table_id, row_id, cell_id, token_refs, raw/normalized text, field_type, association_status, confidence metodológica e provenance. | contrato/compatibilidade + serialização |
| M2-T03 | Detectar cabeçalhos e mapear semanticamente colunas (item, quantity, code, description), sem assumir posição fixa; distinguir área administrativa e BOM candidate. | header mapping cases e GT diffs |
| M2-T04 | Associar itens, quantidades, códigos e descrições por linha/spans; tratar multilinear, rótulos quebrados, páginas múltiplas no escopo e duplicidades. | row linkage tests |
| M2-T05 | Definir normalização lossless: nunca sobrescrever texto original ou converter unidades/códigos sem regra validada; reportar transform rules. | normalized vs raw audit |
| M2-T06 | Emitir UNKNOWN/AMBIGUOUS/NOT_EXTRACTED para campos faltantes ou associação insegura, sem completar a partir da BOM oficial. | ambiguity negative cases |
| M2-T07 | Rodar field-level evaluation e linked-row accuracy; mensurar falso componente e falso valor de quantidade por criticidade. | field scorecard por classe e família |
| M2-T08 | Revisar com Engenharia amostras difíceis; congelar regras aceitas e erros conhecidos. | adjudication log + approved cases |
| M2-T09 | Validar MCP retorno candidate e backward compatibility, segurança e regressão dos dois desenhos de referência. | contract/E2E evidence |

**Testes M2:** texto administrativo parecido com código, várias quantidades na mesma região, itens repetidos, colunas invertidas, spans, OCR incompleto, descrições quebradas, unidades misturadas, quantidade ilegível e código sem item. Verificar todos os claims com token_ref ou span de origem.

**AC de saída M2:** campos tipados e linhas associados conforme thresholds por risco, falso componente crítico dentro do limite aprovado, nenhuma inferência não sustentada, cobertura e abstenção medidas e revisão humana em amostra. Não criar BOM oficial nem gravar dados.

## A.5 M3 — Technical / Geometric Interpretation: backlog executável

**Entrada:** M2 aprovado; Engenharia define classes e severidade técnicas. **Não presumir** que todo desenho tem geometria interpretável a partir de raster.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M3-T01 | Inventariar famílias de cotas, unidades, tolerâncias, notas e símbolos presentes no corpus e o que a infraestrutura atual suporta. | supported/unsupported matrix |
| M3-T02 | Submeter escopo inicial fechado e riscos à Engenharia (por exemplo cotas explícitas em texto versus associação à geometria). | scope decision |
| M3-T03 | Criar/estender observações candidatas diferenciando TEXT_DETECTED, GEOMETRY_LINKED, VERIFIED_BY_RULE e UNKNOWN, conforme contrato aprovado. | state semantics tests |
| M3-T04 | Extrair valor numérico/unidade e tolerância somente quando explicitamente suportados, sem transformar OCR em medição geométrica validada. | unit/tolerance parsing suite |
| M3-T05 | Associar anotação a dimensão/vista/feature somente quando regras e GT permitirem; conflito de setas e vistas requer abstenção. | association overlays e error cases |
| M3-T06 | Tratar indicação de revisão, nota e conflito de cotas com provenance; não inferir material/norma ausente. | failure taxonomy e case review |
| M3-T07 | Avaliar dimensional correctness, unsupported claims, revision correctness, precision/recall por classe e qualidade da abstenção. | risk-weighted scorecard |
| M3-T08 | Executar avaliação humana em amostras críticas e regressão funcional das etapas anteriores. | review record e E2E |

**Testes M3:** tolerâncias simétricas/assimétricas, unidades implícitas não autorizadas, números em notas confundidos com cotas, ângulos/diâmetros, marcas gráficas ambíguas, multipágina/revisões divergentes e simbologia fora do escopo. Marcar classe não suportada \`NOT_CHECKED\` em vez de fingir interpretação.

**AC de saída M3:** apenas classes aprovadas cumprem thresholds técnicos e revisão humana; erros críticos não geram parecer afirmativo; classes restantes são exclusões explícitas. Se uma classe não convergir, ela pode ser retirada do release **por decisão formal de escopo antes do gate**, nunca por omissão silenciosa.

## A.6 M4 — Official Cross-check: backlog executável

**Entrada:** M2/M3 aprovados no escopo de comparação; contratos reais e owners oficiais inventariados.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M4-T01 | Inventariar API/autorização/freshness/error semantics de cadastro de produto, BOM e revisão; classificar roteiros/inspeção/standards sem contrato como owner-blocked. | owner-source-contract matrix |
| M4-T02 | Elaborar matriz de correspondência entre documento/revisão/component_code/qty e campos oficiais disponíveis; exigir autorização de leitura e versionamento. | mapping specification |
| M4-T03 | Implementar comparação multiplicity-aware de itens e quantidade, nunca apenas set-membership; não alterar BOM oficial. | duplicates/quantity comparison tests |
| M4-T04 | Distinguir MATCH, CONFLICT, UNKNOWN, NOT_COMPARABLE, NOT_CHECKED e erro de fonte; OCR omisso não significa componente ausente no desenho. | decision table e negative eval |
| M4-T05 | Testar identificação errada do desenho, revisão divergente, PDF sem revisão, source unavailable e BOM indisponível; preservar faixas de permissão. | source/error matrix |
| M4-T06 | Medir precisão/recall de conflitos contra GT, incluindo falsos alarmes de componente e de quantidade. | conflict scorecard |
| M4-T07 | Executar testes de AuthZ negativa, ausência de escalada via MCP, proteção de documento de cliente e fail-closed. | security test results |
| M4-T08 | Testar E2E nos casos oficiais autorizados com provenance cruzada drawing×source e revisão técnica do owner. | comparison candidate report |

**AC de saída M4:** contratos verificados, comparação correta no escopo, nenhum dado oficial modificado, falsos positivos críticos dentro do limite aprovado, permissões negativas PASS e NOT_COMPARABLE preservado. Faltando contrato oficial, bloquear esse subescopo e escalar; não criar um “source of truth” substituto.

## A.7 M5 — Governed Release: backlog executável

**Entrada:** M0–M4 aceitos no escopo do release; decisões de risco e owners registradas.

| ID | Ação específica do Devin | Evidência de saída |
|---|---|---|
| M5-T01 | Consolidar relatório candidato estruturado: documento/revisão/hash, observações tipadas, evidência por claim, fontes oficiais, estados, conflitos e limitações. | report candidate schema + samples |
| M5-T02 | Integrar na superfície legítima do Portal/EVA sem ocultar origem ou permitir aprovação por UI; loading/empty/error/permission states claros. | UI/contract review e E2E |
| M5-T03 | Instrumentar correlação, métricas de recursos e qualidade, erro tipado, payload bounded, no secrets; manter logs sanitizados. | observability/security evidence |
| M5-T04 | Congelar versão de release, datasets e thresholds; executar avaliação final no holdout sem tuning retroativo e com review de Engenharia. | final eval package |
| M5-T05 | Executar suite completa: unit/contract/integration/architecture/regression/negative/permission/safety/prompt injection/real drawings, incluindo rollback/recreate. | SHA-bound acceptance results |
| M5-T06 | Validar CPU/RSS/latência/concurrency no ambiente elegível e planejar gate shadow/assistido sem trocar baseline por omissão. | capacity/gating report |
| M5-T07 | Obter aprovação técnica para uso assistido no escopo, decisão de Core/Domain quando aplicável e autorização operacional do rollout. | sign-off / explicit BLOCKED |
| M5-T08 | Implantar por procedimento canônico autorizado, validar image digest + runtime SHA, flags, fallback, smoke e E2E MCP autenticado. | deployment manifest + postconditions |
| M5-T09 | ChatGPT executa verificação independente pelo contrato EVA, e Engineering owner valida amostras técnicas. | dual acceptance record |
| M5-T10 | Produzir runbook de incidentes, rollback, limites conhecidos, versionamento de models e critérios de monitoring/exit. | operational playbook |

**AC de saída M5:** relatório candidato correto e rastreável; todos gates essenciais PASS; holdout cumpre thresholds; security e AuthZ PASS; revisão humana do owner; deployment sem regressão; ChatGPT E2E independente PASS; não publicar como desenho aprovado ou alterar cadastro/BOM por automação.

## A.8 Matriz de gates, responsáveis e stop conditions

| Gate | Quem decide | Bloqueia se |
|---|---|---|
| Escopo/RQ/AC | Coordination + Product owner | requisito crítico não especificado |
| Dataset/GT | Engineering owner | GT ausente, anotação não validada ou direitos de uso ausentes |
| Contrato/boundary | Engineering API/Core owners + Coordination conforme impacto | authority deslocada, API inexistente, breaking não aprovado |
| Qualidade/permissões | Engineering reviewer + Security | falsos claims técnicos críticos, vazamento, bypass |
| Recursos/deploy | Operação autorizada | resource fit insuficiente, rollback inviável ou postcondition falha |
| Chat E2E | ChatGPT via EVA conectada | operação retorna erro, motor/contrato não demonstrado |
| Release assistido | Engineering owner + Coordination | thresholds, qualidade, segurança ou aceites não atendidos |

**Regra de descida:** M1 precisa M0 aceito; M2 precisa M1; M3 pode ser subdividido por classe técnica, mas o escopo prometido deve estar fechado; M4 somente sobre campos suficientemente confiáveis e contratos oficiais disponíveis; M5 não libera subescopo que falhou. Preparação paralela e inventário são permitidos, mas não promoção implícita.

## A.9 Planejamento concreto de entregas do Devin (sem cronograma fictício)

- **Pacote 0 — M0 inventory/spec:** sem mudança produtiva; obter owner/GT/dataset, localizar harness e congelar baseline.
- **Pacote 1 — M0 eval harness:** diff limitado ao tooling de eval; executar baseline, obter revisão de GT/threshold.
- **Pacote 2 — M1 region + cell provenance:** corrigir somente falhas de regiões/topologia observadas em baseline.
- **Pacote 3 — M2 typed table:** produzir tabelas tipadas e verificação por campo.
- **Pacote 4 — M3 technical class 1:** trabalhar uma classe de cotas/tolerâncias por vez, se aprovada; demais NOT_CHECKED.
- **Pacote 5 — M4 official comparison:** vincular contrato a campos tipados em leitura autorizada.
- **Pacote 6 — M5 release:** holdout, sign-offs, produção, ChatGPT E2E e runbook.

Cada pacote tem commit/diff/testes/AC próprios. Se uma alteração requer novo owner/source ou breaking contract, **parar e retornar à Coordination**. Critérios não podem ser relaxados para “fechar” o pacote.

## A.10 Template padrão de task do Devin

\`\`\`text
TASK:
MILESTONE:
BASE_HEAD:
OWNER:
OBJECTIVE:
IN_SCOPE:
OUT_OF_SCOPE:
CANONICAL_SOURCES:
CONSUMERS:
CONTRACTS:
RQ:
AC:
DATASET_VERSION_AND_SPLITS:
EXPECTED_GT_AND_THRESHOLDS:
SECURITY_AUTHZ_AND_RESOURCE_LIMITS:
FILES_TO_INVENTORY:
IMPLEMENTATION_BOUNDARY:
TEST_MATRIX:
E2E_DRAWINGS:
NEGATIVE_CASES:
MAX_INTERNAL_CORRECTION_CYCLES: 3
BLOCKER_ESCALATION:
DEPLOY_GATE:
INDEPENDENT_ACCEPTANCE:
REQUIRED_EVIDENCE:
\`\`\`

**Template de conclusão:**
\`\`\`text
EVA EXECUTION REPORT
TASK:
BASE_HEAD:
FINAL_HEAD:
TESTED_SHA:
PUSHED_SHA:
DEPLOYED_SHA:
DATASET_VERSION:
GROUND_TRUTH_OWNER_AND_VERSION:
RQS_AND_ACS:
TESTS_UNIT_CONTRACT_INTEGRATION_REGRESSION:
EVAL_METRICS_EXPECTED_VS_OBSERVED:
HOLDOUT_RESULTS:
NEGATIVE_SECURITY_PERMISSION_TESTS:
RESOURCE_MEASUREMENTS:
PROVENANCE_AND_EXAMPLES:
FAILED_CASES_AND_ROOT_CAUSES:
ITERATIONS_EXECUTED:
RESIDUAL_SEARCH:
EXECUTION_DRIFT:
OWNER_BLOCKERS:
ARCHITECTURE_DECISION_REQUIRED:
FINAL_STATUS:
NEXT_MILESTONE_GATE:
\`\`\`

**Não confundir:** aceite de funcionalidade (OCR/SLANet rodando) não é aceite de qualidade técnica; aceite de GT não autoriza publicação; documentação de deploy não comprova runtime. O programa termina quando o escopo versionado estiver tecnicamente validado, não quando toda funcionalidade futura de engenharia estiver implementada.

---

# ADENDO B — Replanejamento de entrega: relatório funcional primeiro, validação técnica progressiva

**Decisão de produto (2026-11-03):** reordenar o programa para entregar **agora** um relatório de análise de desenho funcional na EVA, recuperando comportamento útil do relatório que existia no Minha DELPI Chat legado. A validação de regras específicas de Engenharia permanece uma trilha posterior de qualidade; **não bloqueia** implementar, testar e publicar uma funcionalidade **read-only, assistida e rotulada DRAFT/CANDIDATE**, desde que seus limites sejam evidentes, os controles de autorização sejam respeitados e não existam afirmações técnicas injustificadas.

**Precedência:** este adendo substitui a interpretação de dependência rígida de GT aprovado como pré-requisito para **todo** código e deploy de M1–M5. Não elimina nem reduz gates de owner, AuthZ, segurança, contrato, resource fit, qualidade mínima observável, aceite técnico de capacidades que se apresentem como validadas ou aprovação de artefato oficial. Os marcos M0–M5 continuam válidos, mas as atividades de relatório funcional podem avançar em paralelo às avaliações e aprovações específicas. Nenhuma seção anterior deve ser interpretada como permissão para declarar qualidade técnica comprovada antes da avaliação de Engenharia.

## B.1 Objetivo imediato e escopo do primeiro release

**Release alvo:** `EVA.DRAWING.REPORT.CANDIDATE.V1` (TARGET, sujeito ao inventário/contrato antes de materializar nome de API).

**História de usuário:** usuário autorizado pede análise de um desenho oficial de produto, recebe **relatório estruturado e legível** com identificação, informações extraídas, tabelas e componentes candidatos, dados oficiais autorizados quando disponíveis, estado de comparação, observações, ambiguidades, lacunas, fontes e revisão. A experiência equivalente funcional já existia no Chat legado e precisa ser **inventariada antes de ser recriada**.

**Princípios de produto:**
- Não depender de catálogo M3 completo, GT de todos os desenhos nem dataset de ~20 para fornecer relatório assistido inicial.
- Não chamar resultado de “aprovado”, “correto por Engenharia” ou “divergência confirmada” sem suporte explícito.
- Relatório inclui apenas classes de conteúdo efetivamente suportadas; detalhes de cotas/tolerâncias não validadas aparecem como `NOT_CHECKED` / `PENDING_ENGINEERING_VALIDATION`, nunca como características técnicas inventadas.
- Desenho oficial, BOM e cadastro não são alterados. Relatório é `DRAFT/CANDIDATE`; publicação/aprovação continua com owner.
- MVP funcional não equivale a encerramento de M0–M5: aprovação de qualidade, generalização, casos complexos e classes M3 seguem avaliações e decisões próprias.

## B.2 Prioridade zero — inventário do relatório do Minha DELPI Chat legado

**Regra de reutilização:** o Chat legado serve exclusivamente de **referência de comportamento, conteúdo e fluxo**. É vedado criar dependência de runtime em agents, prompts, services, tabelas, bancos ou APIs internas do Chat; qualquer reuso exige extração neutra, contrato, ownership na Engenharia e testes.

**B0-T01** Localizar no repositório atual e demais fontes canônicas autorizadas o fluxo legado de análise/relatório de desenhos: pontos de entrada, exemplos, prompts, builders/renderers, services, adapters, templates, formatos JSON/Markdown/PDF, chamadas ao domínio e decisões de negócio. Não presumir a localização; não importar código entre bounded contexts.
**B0-T02** Reproduzir exemplos legados no ambiente controlado, quando disponível. Capturar 1–3 exemplos sanitizados e diferenciar `PROVEN` (código + teste), `TO_INVENTORY` (referência) e `PLANNED` (capacidade desejada). Quando não houver acesso ao legado, registrar `LEGACY_REFERENCE_UNAVAILABLE`, não inventar saídas e continuar a implementação com contrato definido a partir do comportamento aprovado neste adendo e da EVA atual.
**B0-T03** Montar matriz `legacy section → purpose → source of truth → new consumer → EVA/Domain API contract → evidence → status → reusability`. Eliminar qualquer parte que dependia de autoridade indevida, LLM sem grounding ou consultas diretas a dados de outro domínio.
**B0-T04** Identificar renderização/UX preexistentes no Portal Engenharia; preferir estendê-las em vez de criar um segundo host ou fluxo.
**B0-T05** Registrar decision log sobre reuso extraído, partes substituídas e limitações. Se extrair módulo com mudança de owner/authority, abrir `ARCHITECTURE_DECISION_REQUIRED` e não executar essa mudança sem decisão.

## B.3 Backlog de implementação do relatório funcional

**B1 — Contrato candidato antes da implementação.**
Inventariar contratos reais `drawing_understanding.v1`, `drawing_perception_candidate.v1`, `table_structure_engines`, BOM e interfaces de relatório; definir schema **aditivo ou composição de saída existente**, com `source_document_sha256`, `product_code`, `revision` (quando disponível), `generation_run_id`, `source_refs`, `sections`, `observations`, `comparison_status`, `warnings`, `limitations`, `state=DRAFT/CANDIDATE`. Definir owner, consumer, request/response, erros, AuthN/AuthZ, campos nulos, bounded payload, idempotência de leitura/geração, compatibility, observability e postcondition. Não materializar nova API se a composição do endpoint semântico existente for suficiente. Não expor tokens/secrets/PDF bruto em resposta comum ou logs.

**B2 — Coleta e preparação governada.**
Recuperar PDF e metadados pela fonte oficial autorizada; conferir documento, revisão, SHA e política de acesso; executar OCR/SLANet da baseline R9.9; preservar texto original e localização; não copiar PDF para Chat legado nem fazer rede não autorizada.

**B3 — Estrutura documental e evidência.**
Usar os resultados atuais de regiões/tabelas. Classificar `title_block`, `component_table_candidate`, `revision`, `notes`, `other/unknown` no escopo suportado. Criar vínculo rastreável `token→cell→row→field`, com `token_refs` ou `source_spans` efetivamente resolúveis; quando não comprovado, `UNKNOWN/AMBIGUOUS` com box e texto bruto, nunca ID fabricado. Resolver confusão de linhas de componentes com cabeçalhos administrativos por regras testadas e GT provisório rotulado como tal.

**B4 — Extração tipada no escopo atual.**
Candidatos: produto/documento, cliente, revisão, item, quantidade, código e descrição; manter `raw_value`, `normalized_value`, `field_status`, `evidence`, `confidence` (se suportada, não tratada como accuracy), `missing_fields`. Evitar assumir posição fixa de colunas. Se não houver evidência inequívoca, deixar campo ausente/ambíguo. Não produzir cotas, materiais, normas e tolerâncias ausentes; categorias M3 não validadas aparecem como `NOT_CHECKED`.

**B5 — Cruzamento com dados oficiais (read-only).**
Consultar cadastro/BOM/revisão somente via contratos oficiais existentes e permissão live. Separar `drawing_observation` de `official_source_fact` e `comparison_candidate`. Aplicar estados `MATCH/CONFLICT/UNKNOWN/NOT_COMPARABLE/NOT_CHECKED`; preservar BOM gate fail-closed, duplicidade e quantidade, versões e indisponibilidade de fonte; sem banco cross-context, escrita ou remapeamento silencioso.

**B6 — Composição do relatório.**
Produzir estrutura legível com no mínimo, quando houver evidência:
1. Cabeçalho: produto/desenho, revisão, PDF SHA, data/run e `DRAFT/CANDIDATE`.
2. Resumo: o que foi analisado; resultados observados; confiança/limitações explicadas.
3. Documento: identificação e cliente/revisão candidatos.
4. Regiões: identificação, tabela(s), notas e áreas não verificadas.
5. Componentes: linhas candidatas com item, quantidade, código, descrição e referência à origem.
6. Comparação oficial: fontes, revisão, status e divergências *candidatas* explicadas ou `NOT_COMPARABLE`.
7. Características técnicas: somente classes suportadas; demais `NOT_CHECKED`.
8. Alertas: ambiguidades, campos ausentes, conflitos de fonte, OCR limitado.
9. Evidências: páginas, caixas, spans/token refs, origem e versão do pipeline.
10. Limitações e próximo passo: revisão humana requerida; nenhuma aprovação/publicação.

**B7 — Experiência de usuário.**
Expor a operação no Portal Engenharia/EVA por superfície existente e permissões legítimas. Renderizar relatório com estados loading/empty/error/permission, navegação até evidências quando tecnicamente suportado, linguagem que distingue fonte oficial de candidato. Não inventar frontend como autoridade. Se o fluxo do produto já é via MCP, preservar a mesma semântica e entregar também saída consumível no chat; quando o Portal exigir mudança, implementar adapter/consumer correto em vez de acoplar diretamente ao provider.

**B8 — Observabilidade e operação.**
Traces `source→OCR→SLANet→understanding→comparison→report→MCP/UI`; corr IDs, duração, RAM/CPU, tamanho da resposta, erro tipado e modelo/config SHA; segurança e sanitização. Manter persistência governada dos modelos e cronograma de rollback. Não aceitar `health=true` como prova de E2E.

## B.4 Gates funcionais de release — sem esperar validação definitiva das regras

**G-F01:** relatório gerado de ponta a ponta para `90264302` e `90264161` via caminho autorizado, usando PDFs com hashes canônicos e modelos atuais.
**G-F02:** seção de componentes contém texto real e, quando a linha é tipada, associação auditável e sem falsos dados administrativos apresentados como componentes confirmados; campos incertos ficam candidatos/UNKNOWN.
**G-F03:** cada afirmação técnica do relatório tem evidência, ou aparece explicitamente `NOT_CHECKED/UNKNOWN`; nenhuma cota/tolerância/material/norma inventada.
**G-F04:** fontes oficiais diferenciadas de observações; comparação preserva BOM gate, `NOT_COMPARABLE`, identidade/revisão e live AuthZ.
**G-F05:** resposta é estruturada/serializável, bounded, retrocompatível e legível no consumer EVA/Portal existente.
**G-F06:** testes unit, contracts, integration, negative, permissions e regressão reais PASS; falhas de OCR/SLANet/source produzem erro tipado e não sucesso enganoso.
**G-F07:** deploy canônico governado, SHA/digest confirmado, pre/post-deploy E2E read-only, capacidade dentro do orçamento, restart/recreate e rollback plano/teste.
**G-F08:** execução autenticada por consumidor independente quando disponível; caso executor não disponha de OAuth, `TEST_NOT_RUN` em vez de PASS. O aceite ChatGPT permanece independente.
**G-F09:** relatório e UI explicitam `DRAFT/CANDIDATE — NÃO VALIDADO TECNICAMENTE PELA ENGENHARIA`. Sem publicação/aprovação/alteração oficial.
**G-F10:** legado não é dependência de runtime, sem import ou rede para suas tabelas/agents/services; testes de boundary/residual search PASS.

**Regra de bloqueio:** para implementar e implantar relatório candidato, **não se exige** GT aprovado para o catálogo completo de Engenharia, threshold universal ou dataset de ~20. Exigem-se todos os gates de segurança/contrato/read-only/operacional e os gates funcionais demonstráveis. Não converter parte não testada em PASS; não declarar acurácia de Engenharia.

## B.5 Reinterpretação dos marcos M0–M5 e sequenciamento executável

| Marco | Trabalho agora (sem GT final) | Gate de qualidade técnica que permanece pendente |
|---|---|---|
| M0 | dataset manifest, schema, eval harness efetivo, baseline, pacote de anotação para Engenharia | GT revisado, corpus representativo, thresholds de acurácia |
| M1 | regions, source spans e token→cell candidate; correções comprovadas com testes | métricas estruturais em GT/holdout |
| M2 | typed fields e row linkage de tabelas suportadas; abstenção para ambíguos | precisão/recall e revisão técnica por classe |
| M3 | inventário/catalogação e `NOT_CHECKED` para dimensões/tolerâncias não validadas | catálogo técnico aprovado, GT dimensional e classes suportadas |
| M4 | compare read-only com Domain APIs e BOM gate fail-closed no escopo atual | taxa de conflitos falsos/true positivos e validação do owner |
| M5 | relatório candidato funcional e integração Portal/EVA, E2E, deploy governado, observabilidade | aceite da Engenharia para uso como análise tecnicamente validada |

**Recomposição do fluxo de entrega:** `LEGACY INVENTORY → R9.9 PERCEPTION → CANDIDATE FIELD MAPPING → OFFICIAL READ-ONLY CROSS-CHECK → REPORT CANDIDATE → E2E → GOVERNED PRODUCTION DEPLOY`. Ao mesmo tempo, preparar GT/evals sem obrigar qualidade futura para habilitar o relatório read-only atual.

**Critério de conclusão do release inicial:** `FUNCTIONAL_REPORT_V1_PASS` somente com G-F01..F10 demonstrados no nível aplicável, com G-F08 claramente independente; `ENGINEERING_QUALITY_APPROVAL=PENDING` até owner. `PROGRAM_M0_M5_COMPLETION` continua `IN_PROGRESS` até os gates originais de qualidade serem concluídos. Não confundir os dois estados.

## B.6 Protocolo do Devin — implementação e deploy com continuidade

1. Ler authorities, verificar HEAD/status/worktrees/origin, docs 116/117 e legado real, inventariar adapters/templates/report existentes e estabelecer contrato antes de código.
2. Executar todo o trabalho técnico sob autoridade existente sem interromper após cada bug: `diagnose→fix→unit→contract→integration→E2E→regression`; evitar nova rodada de prompts para problema solucionável.
3. Em paralelo, preparar GT/annotation/eval e a tabela de assuntos que exigirão Engenharia, sem tratá-los como bloqueadores de código funcional candidato.
4. Não reabrir o que R9.9 provou sem teste de regressão que indique necessidade. Não fazer substituição arquitetural nem introduzir runtime Chat legado.
5. Commit/push/deploy seguem `AGENTS.md`, incluindo `main`, fast-forward e script canônico. Nenhum atalho em branches, chaves, AuthZ, feature gates e rollback. Se o código falhar no gate pré-deploy, corrigir antes de publicar; se falhar pós-deploy, rollback autorizado e novo ciclo.
6. Exibir relatório final separado por `LEGACY_RECOVERY, FUNCTIONAL_REPORT, OCR/SLANET_REGRESSION, OFFICIAL_COMPARISON, MCP_E2E, PORTAL_UI, DEPLOY_SHA/DIGEST, ENGINEERING_GT_PENDING, RESIDUALS`.
7. Se legado inacessível, declarar `LEGACY_REFERENCE_UNAVAILABLE` e ainda entregar a experiência candidata compatível com as fontes atuais. Se uma authority real bloquear uma operação específica, continuar o restante sem fabricar sucesso.
8. O objetivo é **entregar o relatório utilizável em produção**, não mais um documento descrevendo por que o projeto não avançou. Porém nenhum executor pode conceder a si próprio aprovação técnica ou de produção fora das políticas vigentes.
9. Correção da VAL-01 destinada à produção só encerra o ciclo com testes pré-deploy, deploy canônico e validação no runtime pelo consumidor autorizado. Commit sem deploy é entrega parcial. Deploy sem essa validação fica pendente de aceite. Falha de segurança, contrato, integridade ou regressão crítica impede o deploy. Esta regra não cria publicação automática a cada commit.

## B.7 RQ/AC de produto para a task única de implementação

**Task executora recomendada:** `EVA.DRAWING.REPORT.LEGACY.RECOVERY.FUNCTIONAL.V1.PRODUCTION`.

- `RQ-REPORT-01`: inventário funcional do relatório legado, proveniência e contrato neutro.
- `RQ-REPORT-02`: composição de relatório candidato com dados R9.9 e campos tipados quando suportados.
- `RQ-REPORT-03`: comparação oficial read-only sob AuthZ e BOM gate.
- `RQ-REPORT-04`: report UX/consumer na superfície legítima Portal/EVA.
- `RQ-REPORT-05`: provenance, estado, incerteza, revisão e limitações em todos os claims.
- `RQ-REPORT-06`: segurança, desempenho, modelos persistentes e observabilidade.
- `RQ-REPORT-07`: testes unitários, contratuais, regressão, negativos e E2E dos dois PDFs.
- `RQ-REPORT-08`: deploy canônico autorizado, SHA/digest/rollback e aceite independente.

**Entrega mínima:** relatório funcional demonstrado em runtime real para os dois desenhos, exemplares sanitizados, API/contrato e UI/consumidor em produção quando aplicável, testes e evidência de deploy, e backlog de GT/qualidade não bloqueante claramente separado.

**Nota de status:** este adendo é uma **decisão de planejamento** e não afirma que a funcionalidade já foi implementada, que o legado foi localizado, que o GT está aprovado ou que a produção está modificada.


## B.8 Diretriz transversal — percepcao tabular reutilizavel (2026-11-06)

**Decisao de arquitetura e planejamento, nao implementacao.** Referencia executavel unica: **Doc 119 §39.17 (DEC-VAL-036)**, mantido como plano central da VAL-01 e acompanhado pela Issue #131. Este adendo somente alinha o plano mestre M1/M2/M4 ao requisito de **reuso da percepcao estrutural**; nao cria tarefa, novo bounded context, engine, microservico, source of truth nem novo documento.

**Capability horizontal:** a mesma observacao de tabela (regiao, linhas/colunas, celulas, spans, texto OCR associado, posicoes, confianca, proveniencia e incerteza) deve ser aproveitavel por consumidores semanticos diferentes. O consumer **BOM/component_table** permanece no escopo ativo E1; **carimbo/title_block, historico de revisao e futuras tabelas** sao exemplos de reuso e permanecem em suas fases congeladas. "Carimbo e um tipo de tabela" e uma hipotese de reuso de **estrutura visual**, nao equivalencia de campos, revisao, regras oficiais ou approval entre regioes.

**Framework-first:** testar SLANet/PaddleOCR/PDFium ja presentes e o uso real das celulas pelo Understanding; somente se a qualidade medida nao bastar, comparar recursos nativos da versao instalada de PaddleOCR (incluindo PP-TableMagic quando disponivel) e, condicionalmente, PP-StructureV3. Nenhum framework adicional aprovado para producao ate benchmark e gates. Evitar regex/heuristicas por produto como mecanismo primario de parser de tabelas. Dominio/application consomem representacao neutra por contratos/adapters existentes.

**Gates de aceite:** rastrear a primeira perda no fluxo PDF→render→OCR→estrutura tabular→celulas/associacoes→consumidor semantico→comparacao; medir precisao de linhas/colunas, spans, relacoes campo-ocorrencia, duplicacoes/fusoes, ambiguidade, generalizacao por layouts nao vistos e custo operacional; preservar `DRAFT/CANDIDATE`, `NOT_APPROVED`, `automatic_nc=false`, AuthZ e rules do Engineering owner. Um artefato estrutural de carimbo pode ser usado como teste de independencia sem iniciar VAL-02. Regressao dos 13 PDFs e GT/threshold/aceite tecnicos ainda pendentes.

**Estado:** `PLANNED`; `BENCHMARK=TEST_NOT_RUN`; `VAL01_COMPLETED=false`; E2–E7 congeladas. O detalhamento e a execucao ficam somente no Doc 119 §39.17.
