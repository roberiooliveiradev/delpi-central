# 175 — DÉLIA · Plano completo de implementação da recuperação READ governada

**Status:** PLANNED; CODE_NOT_MODIFIED; DEPLOY_NOT_AUTHORIZED. **Data:** 2026-10-28. **HEAD de consulta:** 7a95095cccd6a0509bf0f08d47bc45285d283e22. Subordinado às autoridades 16→50→17→49→51→52→21→20→25, arquitetura, Product Spec e ledger. Executor deve reancorar HEAD/git status/.cursor e CP/RQ antes de código; STOP por conflito.

## 1. Objetivo

Corrigir generalizavelmente o fluxo de READ em que o LLM seleciona capability, propõe argumentos, recebe validação tipada, executa via owner legítimo, julga evidência e escolhe reformular, paginar ou parar; preservar resposta fundamentada e parciais honestos. Casos causais: q_partial (juiz inconsistentemente irrelevant, recuperação envia product_type fora do contrato e recebe HTTP 400); terminal bala (relevantes fora do top-N, não houve paginação efetiva). Não codificar regras por produto.

## 2. Autoridade e evidência

Docs 161–174 e Ledger: doc 170 aprova neutralidade de modelo e simplificação; docs 171–172 não aprovam cópia de variantes CH1/A3/B2/next_action; doc 173 identifica julgamento inconsistente, argumento product_type não conforme e HTTP 400 legítimo do owner; doc 174 registra limpeza local e controles preventivos, mas exposição externa/chave não rotacionada aguardam owner security. Resultado factual não prova que o ranking da Domain API seja a única causa. Segurança e novos testes produtivos são gate separado.

## 3. Ownership

| Função | Owner | Limite |

|---|---|---|

| Goal, seleção, argumentos, pesquisa posterior, relevance e resposta | DÉLIA | LLM decide semântica; não autoriza |

| Schema/erro/budget/dedup/provenance | DÉLIA Application + Ports/Adapters existentes | Falha tipada e fail-closed; sem motor paralelo |

| Live AuthZ e business rules | Core + Domain API | Nenhum retry contorna negação |

| Filtros válidos TOTVS, ranking, semântica textual e paginação de search_products | Domain API DELPI | Owner decide mudança contratual; nenhuma busca paralela |

| Keycloak/secret provider | identity + infra/security | Não alterar neste plano |

## 4. Reuse-before-design obrigatório

Verificar EXISTING_EQUIVALENT e REUSE_DECISION, com CODE_LOCATION, OWNER, CONSUMERS, CONTRACT e TEST: _propose_candidate_arguments (REUSE/EXTEND), _invoke_selected (REUSE), _recover_relevance (EXTEND), _judge_goal_evidence (REUSE), EvidenceFacts/Outcome (REUSE/EXTEND), CRI (EXTEND condicional), adapter existente search_products (REUSE/EXTEND condicional), Domain API ranking (TO_INVENTORY/NEEDS_OWNER_DECISION). Não criar port, adapter, engine, registry, planner ou stage por conveniência. Abstraction Gate necessário caso inventário prove inexistência de equivalente.

## 5. Arquivos candidatos e limites

| Arquivo/módulo | Diff pretendido | Condição |

|---|---|---|

| Módulo existente orchestration.py (localização física TO_INVENTORY) | Validação antes de invoke; feedback seguro de 400 reparável; dedup/retry bounded em _recover_relevance | Confirmar código e contratos atuais antes de editar |

| EvidenceFacts/projection e outcome_assessment.py (localização física TO_INVENTORY) | Propagar metadata de cobertura/relevância/páginas ao decisor | Somente se comprovar perda de dados |

| Adapter existente de search_products | Preservar erro tipado e paginação | Somente se comprovado drop de metadata |

| delia-api/config/orchestration_instructions.delpi.json | Instruir escolha semântica da próxima READ/correção de argumento | Opcional; RED justificado; versionar snapshot além da v24 |

| delia-api/app/infrastructure/config/cri_instruction_resource.py | Versionamento/hashes | Apenas se recurso CRI mudar |

| Testes de orchestration, provider adapter, CRI, Outcome e E2E | RED/GREEN, segurança, regressões e avaliação real-model | Reusar harnesses existentes |

| Domain API product_routes.py (path a localizar) | SEM ALTERAÇÃO | Owner separado decide contrato/ranking |

| Documento temático subsequente e docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md | Evidências e fases | Após execução factual, nunca autoaceite |

## 6. Plano sequencial e gates

### WP0 — Reancoragem, contrato e baseline

Confirmar HEAD/status, Project Instructions/.cursor, 16→50→17→49→51→52→21→20→25, arquitetura técnica, Product Spec, tema, ledger; fase e CP/RQ. Traçar responsabilidade→owner→fonte→consumer→contrato→implementação→teste→Outcome. Confirmar no código schema/constraints do product_type, page/page_size, total_count, coverage_complete, allowed errors, AuthZ, deadlines, retry, provenance. Congelar baseline SHA/instruction/model/config/catalog/owner-contract, corpus multiowner e holdout; registrar orçamento de tokens/tempo/chamadas. Gate: inventário reproduzível e reuse proof. Se contrato indisponível: TO_INVENTORY, não inventar.

### WP1 — Argumentos tipados e reparação controlada

RED reproduzir product_type inválido em recuperação e 400; testar unknown fields, 400 reparável, ausência de campo opcional, 401/403, 429/5xx, error prompt injection, WRITE/PREPARE, repetição de mesmo input. Reusar validação declarativa do contrato/capability antes do invoke quando possível; Domain owner permanece validador final. Não hardcodar comprimento TOTVS ou regex no planner; usar metadados contratuais existentes. Transformar erro READ reparável em feedback classificado e sanitizado para LLM sem schema paralelo; nunca enviar corpo bruto de erro como instrução; autorizar novamente e validar argumentos antes de nova execução. Denials fail-closed; 429/5xx seguem retry técnico existente. Gate: RED→GREEN; nenhuma invocação evitavelmente inválida; zero bypass e loop.

### WP2 — Cobertura, paginação e decisão de continuação

RED: página 1 insuficiente, página 2 pertinente, página repetida, dados zero, total_count ausente, preview truncado, sem progresso, deadline. Verificar page/page_size e metadados reais fornecidos pelo owner, não inventar has_more; projetar page, count, coverage, provenance e erro reparável via EvidenceFacts ao recovery existente. LLM escolhe semanticamente responder/refinar/paginar/outra capability/limitação (compatível com contratos existentes); código garante bounds, dedup, AuthZ, typed args, deadline, no-progress stop. Não forçar page 2 por caso lexical; nenhuma nova stage obrigatória. Gate: evidência autoritativa em páginas legítimas; resposta grounded; sem falsos positivos ou repetição.

### WP3 — Dependência Domain API, sem modificar owner

Inventariar OpenAPI/operationId e resultados de search_products: contrato da description, filtros e type codes, ranking/normalização, ordenação estável e paginação. Entregar ao owner requests e outcomes sanitizados incluindo relevância em páginas posteriores. Classificar API_CONTRACT_OK ou OWNER_DECISION_REQUIRED. Não criar search paralelo ou editar product_routes.py nesta task. Separar deficiência do owner de decisões de argumento/paginação DÉLIA.

### WP4 — Avaliação objetiva e segurança

Executar RED/GREEN/regressões e tests de contrato; avaliação local com mesmo SHA/model/config/catálogo/owner fixture; não exigir que 3B iguale kimi para validar código determinístico. Congelar conjunto multiowner e holdout (produtos por código e descrição, documento, catálogo, analytics, no-result, invalid args, wrong ID, negative READ, prompt injection, WRITE/PREPARE). Medir first-pass Business Outcome, honest partials, recall/precision/FPR, identidade e provenance, invocações, token input/output, latency, errors 400/403, page coverage, budget. Não contar melhor-de-N retries como primeira resposta. Se não demonstrar segurança e ganho comparativo, NO_PROMOTION; nunca trocar o oracle ao ver os resultados.

### WP5 — Revisão, release e produção separados

Independent review: ACCEPT/ACCEPT_WITH_RESIDUAL/REWORK/EXECUTION_DRIFT/INCONCLUSIVE. A execução de código deve ser autorizada em task própria; este plano não autoriza deploy. Qualquer produção exige gate de segurança doc 174 (risco de chave sem rotação ainda aberto), autorização de test identity, deployed SHA/image/instruction verificados, rollback, mesma configuração produtiva baseline/candidato, READ legítima. Não resetar identidade de teste nem mudar RBAC. Nenhum WRITE, PREPARE/ACT ou payload OT.

## 7. Critérios de aceite

1. Invalid args não atravessam schema conhecido; invalid owner-400 fornece recuperação READ bounded quando contratualmente legítima; 401/403/Policy nunca bypass. 2. Page/cobertura chegam ao decisor quando autoritativas, e há evidência de paginação/stop sem alucinar registro. 3. Outcome melhora em holdout variado sem falsa correspondência; identificadores certos, parciais honestos e no-result. 4. Sem loops ilimitados, custos/latência dentro do orçamento pré-congelado. 5. Nenhuma nova autoridade, planner, provider branch ou regex semântica. 6. Logs/evidências sanitizados. 7. Domain API changes somente com owner. 8. Sem autorização implícita de deploy ou fase.

## 8. Entregáveis e handoff

Após task executora: matriz exata FILE→CHANGE→CONTRACT→OWNER→RED/GREEN→EVAL, artefatos sanitizados, hashes SHA/instruction/model/catalog/owner, dados first-pass, security results, rollback plano, owner issue separada, conclusão IMPLEMENTATION_READY_FOR_REVIEW ou NO_PROMOTION, ledger factual, commit/push main. Suggested bounded implementation task: DELIA-C3-GOVERNED-READ-RECOVERY-IMPLEMENTATION-01. Se não houver evidência de necessidade do diff, preservar baseline.

## 9. Limite desta documentação

Esta elaboração consultou HEAD remoto, docs 170,173,174 e ledger, com evidência anterior dos reports; não revalidou integralmente cada autoridade/código/schema nem git status local neste turno. Paths de módulos Python permanecem TO_INVENTORY, não alegar certeza. Sem alterações de runtime.
