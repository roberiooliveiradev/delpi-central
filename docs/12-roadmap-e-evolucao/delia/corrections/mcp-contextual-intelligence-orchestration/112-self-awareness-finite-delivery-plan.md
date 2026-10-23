# 112 — Plano executivo fechado: autoconhecimento e responsabilidades DÉLIA
Data: 2026-10-23. TRACK_ID: DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01.
Status: PLANNED; não concede automaticamente autorização de código, fase ou deploy.
Owner: coordenação de arquitetura; execução bounded: Devin; aceite: coordenação.

## 1. Autoridades e links
Sequência obrigatória para cada etapa, no HEAD vigente:
[16 Plano Mestre](../../16-execution-master-plan.md) → [50 Arquitetura](../../50-standalone-copilot-application-architecture.md) → [17 Ownership](../../17-component-and-contract-map.md) → [49 Padrões](../../49-architecture-and-design-patterns-standard.md) → [51 Baseline](../../51-platform-integration-baseline.md) → [52 Bootstrap](../../52-standalone-repository-and-bootstrap-plan.md) → [21 Estado](../../21-data-and-state-model.md) → [20 Testes](../../20-testing-and-acceptance-matrix.md) → [25 Rastreabilidade](../../25-requirements-traceability.md).
Complementos: [24 Product](../../24-product-specification.md), [03 Capability Model](../../03-capability-model.md), [60 MCP/A2A](../../60-agent-interoperability-mcp-a2a-and-tool-protocols.md), [ADR 58](./58-adr-llm-semantic-decision-ownership.md), [Roadmap finito 59](./59-orchestrator-refactoring-finite-execution-roadmap.md), auditorias 56–57 e relatórios 109–111; ledger `docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md`; regras .cursor e Project Instructions.

ADR 58: LLM interpreta intenção/contexto e propõe seleção semântica; determinístico valida contratos, autorização, evidência, segurança e outcomes. Preserve selection-only / MODEL_AUTHORED_FACTUAL_PROSE=NONE (ledger §6.145). Roadmap 59 §22: Q03 encerrado ACCEPT_WITH_RESIDUAL, B1 unresolved; NÃO reabrir Q01–Q03 ou alterar gates de fase sem autoridade superior. Preserve 60/3/300, Core/Domain, READ != ACT. Em conflito: EXECUTION_DRIFT ou ARCHITECTURE_DECISION_REQUIRED e STOP.

## 2. Problema, começo/meio/fim e critérios de produto
Evidência PO 2026-10-23: D4 pergunta por especialistas e recebe insuficiência; D5 pergunta por formatos de visualização e recebe schema entities.playlist; D8 consulta material 10080043 corretamente mas apresenta labels em inglês. Capturas demonstram UX, não telemetria completa. RC1+RC2 já remediados nos relatórios 110/111; não reabrir sem defeito novo provado.

Objetivo final: DÉLIA explica identidade (product spec), capabilities/especialistas realmente elegíveis (projeção viva aprovada) e limites de atuação do usuário (Core/Domain), distingue metapergunta de execução, produz relevância e apresentação PT-BR fiel a evidências. Nada de SelfAwarenessEngine, segundo planner, catálogo shadow ou heurísticas por DAVI/VISTA/TÉO.

Módulos existentes para priorizar: `delia-api/app/application/capability_provision/{orchestration.py,conversational_response.py,outcome_assessment.py,contracts.py}`, `delia-api/app/domain/capability_catalog/model.py`, `delia-api/app/infrastructure/openapi/capability_catalog_adapter.py`, `delia-api/app/application/interaction/workspace_context.py`. Subáreas `capabilities/expertise/knowledge/evidence` no doc 52 são candidatos PLANNED, não criação obrigatória.

## 3. RQ e AC locais (não criar CP canônicos)
- RQ-SA01 / AC01: identidade DÉLIA explicada conforme 24 e 50, sem capacidades inventadas.
- RQ-SA02 / AC02: D4 lista/explana especialistas fundamentados em contratos elegíveis; sem catálogo paralelo. Fontes 03,17,25 CP-071/073/074/086/151/263 e 60.
- RQ-SA03 / AC03: distingue capacidade publicada, disponibilidade efetiva e permissão atual; negative AuthZ. Fontes 17,21,49.
- RQ-SA04 / AC04: D5 responde com formato autoritativamente publicado OU insuficiência específica, não schema entities.playlist irrelevante. Fontes 49,58,59,20.
- RQ-SA05 / AC05: D8 em PT-BR, labels naturais e dados/IDs/unidades rigorosamente preservados. Fontes 24 §6,20,49.
- RQ-SA06 / AC06: selection-only e provenance conservados; sem model-authored factual prose não autorizada. Fontes ADR58,59,ledger.
- RQ-SA07 / AC07: funções de orquestração redistribuídas somente para owner/módulo legítimo, caller parity. Fontes 49,52,56–59.
- RQ-SA08 / AC08: generalização com perguntas inéditas, reformulações, renomeação/remoção de capability e multiturno; outcome no SHA/model/config avaliado. Fontes 20,25,59.
- RQ-SA09 / AC09: injection/AuthZ/READ!=ACT seguros, sem fuga de metadata. Fontes 17,49,60.

## 4. Etapas finitas e sequência
**S0 — Freeze de contratos e responsabilidades (COMEÇO):** reancorar HEAD/git status/origin e authorities; verificar owner/consumer/fonte/contrato, mapear função por função apenas nos grupos afetados de orchestration.py; conferir se Core/Portal/MCP/CapabilityProjection oferecem listagem autoritativa para D4 e formatos para D5. Reusar auditorias 56–59, sem inventários repetidos. Produzir matriz `RESPONSIBILITY→OWNER→SOURCE→CONSUMERS→CONTRACT→CURRENT_PATH→KEEP|MOVE|EXTEND`, EXISTING_EQUIVALENT e REUSE_DECISION por grupo, golden D4/D5/D8, baseline RED e gap de contrato. AC-S0: 100% dos grupos-alvo mapeados, gaps tipados, sem código. Gate: coordenação ACCEPT ou ACCEPT_WITH_RESIDUAL não bloqueante.

**S1 — Autoconhecimento (MEIO A):** autorizado somente após gate S0. Reutilizar identidade de produto, catálogo vivo semanticamente projetado, expertise/contexto e LLM atual; D4 correto, honestidade sem fonte, negativos de acesso, provedores renomeados/adicionados/removidos sem patch. Se não houver owner/contrato legítimo para listar especialistas, STOP subescopo e ARCHITECTURE_DECISION_REQUIRED, nunca fabricar. AC-S1: RQ-SA01–03, 06,09 + generalização.

**S2 — Pertinência e suficiência (MEIO B):** autorizado após S1. Corrigir classificação de evidência versus vocabulário técnico com mecanismos existentes, sem regra VISTA e sem filtrar entities.playlist globalmente. D5 deve trazer informação autoritativa ou explicitar lacuna em PT-BR; D8 segue íntegro. AC-S2: RQ-SA04,06,08,09 + regressão D4/D5/D8.

**S3 — Apresentação PT-BR (MEIO C):** autorizado após S2. Reutilizar `conversational_response.py` e os contratos vigentes para rótulos humanos, unidades e prosa determinística fiel; impedir JSON cru irrelevante. Não autorizar LLM a redigir novos fatos empresariais: se imprescindível, STOP somente nesse subescopo e requerer ADR. AC-S3: RQ-SA05,06,09, D5/D8 e apresentação segura de markdown.

**S4 — Redistribuição de responsabilidades (MEIO D):** autorizado após S3 e com matriz S0 atualizada. Extrair apenas funções mal posicionadas com destino/consumers comprovados em módulos existentes; preservar assinaturas, testes, adapters, DB/HTTP boundaries. Nenhuma refatoração estética por LOC; `SKIP_WITH_DECISION` quando extração desnecessária ao outcome. AC-S4: RQ-SA07, caller parity, segurança e suíte completa.

**S5 — Homologação/encerramento (FIM):** autorizado após S1–S4 aceitos ou S4 formalmente dispensado. Testar suíte completa, negativas de segurança, Ollama local sem LLM pago, generalização e turnos reais com PO e deploy governado/autorizado em etapa distinta. Correlacionar SHA, prompt/config/model, capability selection, provenance, tokens reais quando disponíveis, task outcomes. Não criar usuário produtivo. AC-S5: RQ-SA01–09 cobertos; D4/D5/D8 e variações com outcomes sustentados; nenhuma regressão material; review independente. Encerrar como PLAN_COMPLETE só após ACCEPT formal e ledger.

## 5. Protocolo de aceite e rework anti-loop
Para cada S0–S5: HEAD/status + authorities/ledger → reuse gate → RED → menor mudança permitida → unit/regression/security/eval/outcome → residual search → docs/ledger → commit/push main comprovado → DÉLIA EXECUTION REPORT → parecer **da coordenação**. Teste verde ≠ business outcome; documentação não avança fase.

Vereditos: `ACCEPT | ACCEPT_WITH_RESIDUAL | REWORK | EXECUTION_DRIFT | INCONCLUSIVE`.
- ACCEPT: AC obrigatórios PASS; NEXT apenas por autorização explícita.
- ACCEPT_WITH_RESIDUAL: residual não material documentado; NEXT somente se não bloquear pré-condições.
- REWORK: **máximo um por etapa**, escopo restrito ao AC falho com regressões; nunca nova arquitetura implícita.
- Segundo FAIL, owner/contrato inexistente ou mudança congelada: STOP, Product Master/coordenação decide; sem ciclo infinito.
- INCONCLUSIVE/TEST_NOT_RUN: não marcar PASS; obter evidência faltante somente com autorização.
- EXECUTION_DRIFT: parar e reancorar decisão.
S0=PLANNED; S1–S5=NOT_AUTHORIZED. O plano não é autorização de implementação nem de deploy.

## 6. Report padrão
```text
TRACK_ID=DELIA-C3-SELF-AWARENESS-FINITE-DELIVERY-01
STEP=S0|S1|S2|S3|S4|S5
BASE_HEAD= FINAL_HEAD= ORIGIN_MAIN= PUSH_VERIFIED=
AUTHORITIES_READ= LEDGER_REFERENCE= CP_RQ=
EXISTING_EQUIVALENT= REUSE_DECISION=
OWNER_SOURCE_CONTRACT_CONSUMERS=
FILES_CHANGED= RED_GREEN= FULL_REGRESSION=
EVAL_SHA_MODEL_CONFIG= SECURITY= OUTCOME_EVIDENCE=
RQ_AC_COVERAGE= RESIDUAL_SEARCH= MATERIAL_GAPS=
EXECUTION_DRIFT= EXECUTOR_VERDICT=
COORDINATION_REVIEW_REQUIRED=YES
```
Após review registrar VERDICT, REWORK_USED 0|1, NEXT_ALLOWED_STEP e evidência no ledger. Devin NÃO salta gates por conta própria.

## 7. Autorização Product Owner — S0 (2026-10-23)

**PO_DECISION=S0_AUTHORIZED_READ_ONLY.** O Product Owner autorizou explicitamente a execução apenas da etapa S0 deste plano. O executor Devin pode reancorar, inspecionar sources, contratos, consumers e testes, produzir goldens e relatório/matriz S0, documentar evidências e fazer commit/push documental governado. Nenhuma mudança de runtime, deploy, novo engine, nova autoridade, alteração de contrato ou avanço automático S1–S5 está autorizada. **S1–S5=NOT_AUTHORIZED.** Ao concluir S0, retornar à coordenação com DÉLIA EXECUTION REPORT para veredito independente e decisão do próximo gate. Esta decisão de produto não implica aceite de S0 nem avanço de fase.

## 8. Autorização Product Owner — execução contínua S1–S5 (2026-10-23)

**PO_DECISION=S1_TO_S5_CONTINUOUS_EXECUTION_AUTHORIZED_WITH_GATES.** O PO autorizou expressamente todas as etapas restantes e solicitou execução contínua, sem novas interrupções administrativas entre etapas. Esta autorização **substitui apenas o estado de entrada S1–S5 NOT_AUTHORIZED** deste documento e da nota de S0 §7; **não modifica** authorities superiores, ADR 58, roadmap 59, contratos congelados ou gates materiais de segurança.

**Entrada:** S0 ACCEPT_WITH_RESIDUAL documentado no [113](./113-s0-contract-freeze-and-responsibility-matrix.md), reviewed commit `5dfdb095c2`, parecer `274bd790e260494b2ebc75076493706c2d8ba61d`. S1–S5 podem ocorrer sequencialmente sem nova mensagem do PO, desde que cada etapa conclua seus AC e obtenha revisão independente quando disponível. Não confundir autorização antecipada com aceite antecipado.

**Execução coordenada sem pausas:** Devin executa S1→S2→S3→S4→S5, entrega relatório e documentação de cada etapa no GitHub, revisa diffs/evidence contra cada AC, aplica **no máximo um rework** bounded se necessário e prossegue quando os gates do plano estiverem satisfeitos. Se a revisão independente de coordenação for indisponível durante a execução, registrar `INDEPENDENT_REVIEW_PENDING`; não alegar ACCEPT emitido pelo executor. Para evitar interrupções administrativas, pode concluir o trabalho tecnicamente independente das etapas seguintes em sequência, mas não promover o estado de aceite nem executar mudanças que dependam de uma decisão congelada sem aprovação legítima.

**Limites invioláveis:** nenhuma nova autoridade, shadow catalog, novo planner/engine, inference de AuthZ, ACT material, relaxamento de selection-only/model-authored factual prose ou alteração de Core/Domain sem gate próprio; nenhuma implantação em produção sem validação formal de release/rollout e rollback, nem uso de credenciais reais de terceiros. Ausência de contrato owner ou subescopo dependente de ADR: STOP apenas o subescopo afetado e continue itens independentes; registre `ARCHITECTURE_DECISION_REQUIRED`. Evidência inconclusiva não vira PASS e jamais justifica bypass.

**Fechamento:** voltar à coordenação com uma única consolidação final S1–S5, SHAs, RQ/AC por etapa, eventuais reworks, testes/evals/outcome, gaps/decisões exigidas, evidência de runtime se realmente implantado, e `COORDINATION_REVIEW_REQUIRED=YES`. `PLAN_COMPLETE` só após parecer independente final.

## 9. Diretriz vinculante PO — Clean Code, presentation resource e limites de regras (2026-10-23)

**Contexto:** durante S3, revisão visual de `_FIELD_CLAUSE_LABELS` sendo ampliado em `capability_provision/orchestration.py`. Esta diretriz explicita como executar os gates já definidos em S3/S4; **não cria etapa, fase, novo engine ou alteração de ADR**. A partir de agora, antes de qualquer decisão/código/prompt, reancorar GitHub authorities/ledger conforme §1; comentário do executor ou screenshot não substitui diff no HEAD.

**EXISTING_EQUIVALENT=YES (mecanismo de apresentação):** `delia-api/config/cri_presentation.delpi.json` (vocabulário governado v3), `delia-api/app/infrastructure/config/cri_instruction_resource.py` (loader e validação versionada) e `delia-api/app/application/capability_provision/conversational_response.py` (compositor leaf), com os consumidores CRI e não CRI de `orchestration.py`. **REUSE_DECISION=EXTEND sob gate de contrato/consumers**, sem criar registry/engine/serviço paralelo.

**S3 — conteúdo e idioma:** textos user-facing, templates e rótulos semânticos declarados pertencem preferencialmente ao recurso JSON governado já existente, com owner, versão, schema e limites; não aumentar indefinidamente constantes de tradução hardcoded na orquestração. JSON não é destino de algoritmos, Policy, AuthZ, safety gates ou classificadores. Evoluir `field_labels` somente após verificar os consumers e compatibilidade do contrato atual: loader rejeita versions/sections não previstas, portanto adicionar chaves ao JSON sem schema/validator/testes é FAIL. Se for mudança material de contrato congelado: STOP subescopo, `ARCHITECTURE_DECISION_REQUIRED`.

**S4 — responsabilidade física:** `orchestration.py` deve coordenar; resolução de rótulos e construção de frases user-facing devem residir em componente de apresentação existente/legítimo, sem imports circulares. Reutilizar uma única projeção de rótulos para CRI, baseline, detalhe, lista e comparação onde houver equivalência contratual comprovada. Mover somente funções com owner, consumers e regressão mapeados no doc 113; não mover por LOC ou estética. Registrar `SKIP_WITH_DECISION` quando não existir destino legítimo sem inventar abstração.

**Separação obrigatória:** uma tabela fechada de labels contratados é apresentação determinística permitida pelo `selection-only`; NÃO significa que Python deva interpretar intenção, descobrir capabilities por palavras-chave, traduzir livremente domínios ou inferir significados empresariais. Um campo desconhecido deve permanecer fiel e ter apresentação neutra (sem afirmar tradução/semântica não comprovada); valores empresariais, códigos, unidades, datas, descrição e provenance copiados verbatim. Não colocar metadados de controle, `agent_directives`, schema de API, keys de transporte ou operações técnicas na resposta comum. LLM existente interpreta intenção; gates determinísticos verificam.

**AC adicionais obrigatórios de S3/S4, sem criar CP novo:** (a) JSON versionado correto carrega; versão/seção/formato/tamanho inválidos falham closed; (b) rótulos PT-BR são consistentes em CRI e caminho não CRI, para campos conhecidos; (c) campo desconhecido não vira significado inventado; (d) D8 preserva código 10080043, descrição, medidas, unidades e fonte; (e) D5 não despeja schema ou `entities.playlist` irrelevante; (f) D4 mantém superfície viva e permissão declarada sem catalog shadow; (g) regressão completa e negatives injection/AuthZ/READ!=ACT, parity caller e ausência de duplicação; (h) nenhuma prosa factual empresarial model-authored fora da ADR 58; (i) qualquer nova entrada no vocabulário é justificável por contrato/semântica reconhecida, não por fixture isolada.

**Política de rework e execução contínua permanece §8:** não interromper para autorização administrativa entre etapas, mas não autoaceitar; somente 1 rework bounded por etapa; conflito de owner/contrato ou authority congelada causa STOP do subescopo e relato factual. Documentar decisões, diffs, testes, SHA/config/model e resultado real em cada report; S5 só fecha após review independente. Esta diretriz substitui qualquer interpretação de que crescer `_FIELD_CLAUSE_LABELS` dentro de `orchestration.py` seja o destino final aprovado de S3/S4.
