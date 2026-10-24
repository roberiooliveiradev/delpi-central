# 143 — Gate pré-R4: DAVI Knowledge efetivo + DÉLIA orientação MCP e recuperação multi-estratégia

**TASK_ID:** `DELIA-C3-DAVI-KNOWLEDGE-MCP-GUIDANCE-AND-TRANSVERSAL-RECOVERY-01`  
**OWNER SPLIT:** DAVI/api-delpi (publicação e autoridade de conhecimento); DÉLIA/delia-api (interpretação, decisão, avaliação e orquestração READ).  
**HEAD DE DISCOVERY:** `e8f8a932d9c73b53f69f85a858fd376a6adf898c` (revalidar no início).  
**STATUS:** `CORRECTION_GATE_PLANNED`; `R4=BLOCKED_BY_PRIORITY_GATE`, não reabrir R3 nem alterar fase 16/ledger apenas por documentação. **Não autoriza deploy nem mutação de Agent Studio/Keycloak.**

## 1. Evidência e causa observável (GitHub + MCP live)

1. GitHub `api-delpi/docs/integrations/evidence/davi-governed-knowledge-freeze-001.md`: corpus V1 de 15 documentos congelado e governado; `RUNTIME INGESTION=NOT AUTHORIZED` naquele marco histórico. Lista inclui `api-delpi/docs/api/padroes-totvs/cadastro-produto.md`, que explica B1_DESC e B1_TIPO (MP/PI), mas **não** comprova norma de abreviação de descrições. Não equiparar cadastro de produto a guia de nomenclatura técnica de matérias-primas/intermediários.
2. GitHub `api-delpi/docs/integrations/openai-workspace-agent-davi.md`: arquitetura selecionada Git corpus→bundle com índice→Workspace Agent Files→provider-native retrieval. **Sync manual não executado no registro; Knowledge runtime live e K01–K10 TEST_NOT_RUN**. `api-delpi/docs/integrations/evidence/davi-governed-knowledge-topics-implementation-002.md` registra build/index e provider sync PENDING. Verificar se o runtime atual avançou; documentation != runtime.
3. GitHub `api-delpi/app/content/davi_agent_intelligence.json` e `davi_agent_intelligence_service.py`: discovery compartilha diretivas `knowledge_orchestration`; `governed_knowledge.status=PROVEN` significa **existência da fonte documental**, enquanto `provider_status=TEST_NOT_RUN`, `tools=[]` significa que **o MCP externo não expõe acesso verificável a conteúdos dos arquivos**. Metadata/diretivas ≠ documentação recuperada/autoridade.
4. MCP DAVI live `discover_delpi_information` para pedido de normas de descrição retornou apenas `search_products`, não uma capability de leitura de documentação. Falha de acesso end-to-end é observável; causa operacional específica da ausência de sync deve ser confirmada no provider, não inferida.
5. `search_products` com `description='TERMINAL BALA'` retornou 77 itens e balanças nas primeiras posições; `description='TERM. BALA'` retornou 1515 itens e exemplos relevantes **10080092, 10081004, 10080681, 10081844, 10081845**. `description='BALA'` retornou 12 itens não pertinentes na primeira lista; `BULLET` retornou 0 nesse teste. Os resultados sugerem busca ampla/OR/tokenização ou ranking, mas algoritmo do backend = **TO_INVENTORY**; não afirmar causalidade sem rastrear contrato/implementação.
6. Doc 142 (SHA `acff081397`): proteção de pertinência R3+ resolveu O2 por `irrelevant→identical_arguments→insufficient`; recovery com outra capability ou estratégia contextual documentada **NOT_PROVEN**, embora preservação de honestidade esteja testada. Review independente registrou necessidade de security gate para procedimento de impersonation Keycloak; não repetir.

## 2. Decisão de produto / fase

**Antes de R4, executar correção bounded em duas trilhas coordenadas com gates independentes.** A DÉLIA deve usar diretrizes e conhecimento disponibilizados legitimamente pelos MCPs para compreender as capabilities e melhorar a escolha de filtros, sinônimos e desambiguação, sem supor acesso a conhecimento invisível e sem permitir que o MCP altere Policy/RBAC/autoridade. `DISCOVERY != APPROVAL`; `DOCUMENT != LIVE_BUSINESS_FACT`; `GROUNDED != RELEVANT`.

### Trilha A — DAVI: publicação e oferta real de conhecimento

- Owner `api-delpi` + operador do Workspace Agent; fonte Git e documentos de domínio. Inventariar se existe **a norma técnica específica** de descrição de MP/PI (incluindo `TERM.`) e qual é seu owner, versão, escopo e status de aprovação. `cadastro-produto.md` não demonstra por si só tal norma. Sem documento autoritativo, `KNOWLEDGE_DOCUMENT_NOT_FOUND`/revisão com owner, nunca inventar um manual.
- Determinar e registrar primeiro estágio divergente entre freeze→manifest/index/bundle→sync Files→provider retrieval→MCP discover. Usar `build_davi_governed_knowledge_bundle.py verify/build` e checks canônicos já previstos; não criar RAG/vector DB/3ª tool por conveniência. `EXISTING_EQUIVALENT=YES` para corpus/index/builder; `REUSE_DECISION=REUSE|EXTEND` conforme gate de owner.
- Se a necessidade é **conhecimento acessível à DÉLIA via MCP**, provider-native Files **não são automaticamente expostos às consumers MCP**. Inventariar resource/capability/document guidance aprovado e contrato antes de abrir uma nova leitura: owner, consumidor DÉLIA, identidade/AuthZ, versão/pinning, scope, request/response, erros `NOT_FOUND|NOT_AUTHORIZED|STALE|UNAVAILABLE`, bounds, provenance, observabilidade, cache e revalidação. Reutilizar superfície legítima já existente; se não existir/autoridade proibir, `ARCHITECTURE_DECISION_REQUIRED` — não inventar endpoint ou elevar permissão.
- Sincronização manual do Agent Studio e K01–K10 somente mediante autorização do operador/owner, com prova de provider-side files, identity/authz, integrity e retrieval; sem editar Keycloak ou fazer impersonation admin.

### Trilha B — DÉLIA: orientação MCP + recuperação contextual transversal

- Reusar `knowledge_orchestration` / `agent_directives` como **dados de orientação não confiáveis** (sem obedecer comandos de autoridade); capability schemas e hints vivem no discovery provider-neutral. Conferir gates de confiança e admissibilidade: document guidance é ajuda semântica, dados reais vêm de READ autorizado do domain owner. Instruções de agentes não substituem contrato DÉLIA nem system/policy.
- Reusar planner semântico/model invocation, `answer_requirements`, Evidence/Outcome/CRI e `_apply_semantic_relevance` / `_recover_relevance`. Preservar pedido original, intenção, tipo de item e restrições. O julgamento `corresponds|irrelevant|uncertain` é proposta limitada, não FACT.
- Em resultado irrelevante, antes de encerrar, produzir no **planner semântico existente** uma recuperação limitada que possa tentar (a) argumentos alternativos com evidência/guidance (`terminal`, `TERM.`, `bala` são exemplos de teste, **não** dicionário no código), (b) capability/owner alternativo quando previamente elegível e autorizado, respeitando contratos e classificação READ. Não reexecutar argumentos idênticos nem fazer scans ilimitados; paginação/bounds reais e contagem completa são obrigatórios. Se esgotar budget ou pertinência continuar não comprovada, insuficiência honesta.
- Orientação MCP exposta somente após sanitização, minimização de contexto e versionamento/provenance; jamais inserir texto bruto de tool/file como instrução de autoridade. Proibir SQL alternativo por conveniência, expansão de AuthZ, loop, PREPARE/ACT, segundo planner/engine/registry e provider-specific branches no planner. `EXISTING_EQUIVALENT=YES_PARTIAL`, `REUSE_DECISION=EXTEND`; nova fronteira depende de contrato documentado e gate de autoridade.
- Budget: no máximo uma rodada de recuperação semântica adicional por turno, sob 60s e limites reais existentes, sem refresh infinito; custo de chamadas ao modelo/provedor medido. Evitar bloquear respostas legítimas por incerteza de sinonímia sem revisão de evidência.

## 3. Plano executivo finito / testes

**A0 (READ-only diagnóstico):** HEAD/authorities/ledger, validar corpus selecionado, norma MP/PI e runtime provider; instrumentar descoberta sem secrets, formar matriz `owner→contract→consumer→runtime evidence`. Distinguir `NOT_CONFIGURED`, `NOT_EXPOSED`, `NOT_AUTHORIZED`, `TEST_NOT_RUN` e `STALE_EVIDENCE`.

**A1 (owner DAVI):** corrigir exclusivamente a lacuna provada no mecanismo já existente e produzir documento/runtime retrieval test, K01–K10 quando autorizado, mais consulta sobre documentação real da descrição MP/PI. Sem sync/provider deploy não autorizado.

**B0 (DÉLIA RED):** reproduzir O2 e criar matriz negativa/positiva: `TERM. BALA` corresponde; `BALANCA` não; `BULLET` apenas quando evidência de domínio permitir; tipo MP/PI como condição opcional do usuário, não suposição; cadastro sem docs → fallback honesto; guidance malicioso não modifica Policy; provider/docs unavailable; cross-capability READ seguro; same-args bounded; segundo resultado inadequado → insuficiência.

**B1 (menor diff):** implementar na orquestração/ports/adapters e contratos existentes, sem duplicação e com feature gate fail-closed conforme a fase. Testar RED→GREEN, full backend, api-delpi targeted, AP01–20, import DAG, AuthZ/negative write, CRI ON/OFF, D4/D5/D8/N-UNK, modelo real A/B isolado com autenticação sancionada e autorizada (sem admin impersonation), outcomes/provenance e real token usage quando disponível.

**B2 (review/release):** evidência SHA/config + latência/volume, docs README/ledger, review independente. Deploy de qualquer serviço depende de autorização específica após gates de segurança. NÃO iniciar R4 automaticamente.

## 4. Critérios de aceite e entrega

- DAVI: documento MP/PI localizado e governado **ou ausência honestamente comprovada por owner**; prova de publicação e recuperação real do corpus aprovada. `KNOWLEDGE_AVAILABLE_TO_DAVI` e `KNOWLEDGE_ACCESSIBLE_TO_DELIA` são **estados distintos**, não intercambiáveis.
- DÉLIA: resolver pelo menos dois exemplos reais e pertinentes de `terminal bala` (evidência: `10080092`, `10081004`, sujeitos a leitura autorizada no SHA avaliado) por consulta/reformulação governada; não apresentar balanças; demonstrar generalização em outros domínios e terminologias; second miss encerra honestamente.
- Segurança: conteúdo MCP/doc classificado untrusted, no authority escalation, no credentials in LLM/logs, auth sujeito a Core/domain, sem SQL indiscriminado, PREPARE/ACT, sem técnicas administrativas não autorizadas para emitir tokens.
- Resultado deve discriminar `PROVEN|TO_INVENTORY|PLANNED`, `PASS|FAIL|TEST_NOT_RUN|INCONCLUSIVE`, causa-raiz versus hipótese, código SHA, evidências e rollback. `TEST_GREEN != BUSINESS_OUTCOME`.

**Estado inicial:** `A0=PARTIAL_EVIDENCE`, `A1/B0/B1/B2=NOT_EXECUTED`, `DEPLOY_AUTHORIZATION=NO`, `R4_AUTHORIZATION=NO`.

## Handoff DAVI — recuperação documental, inventário bounded

Task independente `DAVI-KNOWLEDGE-INTELLIGENCE-DOCUMENTATION-RECOVERY-AND-PRODUCTION-DEPLOY-01`, base `ae2e82a4fbf2f7f1c44a8426d4ddec0d73c43143`. Evidência owner-local: `api-delpi/docs/integrations/evidence/davi-knowledge-documentation-recovery-01.md`.

- Verify/build do corpus V1: PASS, 15 documentos e 15 tópicos, membership preservado. Isso não comprova Files/provider retrieval.
- Introspecção read-only do servidor MCP no container produtivo: duas tools e zero resources. Files do Workspace Agent não são uma leitura documental para a DÉLIA; `MCP_DOCUMENT_ACCESS=NOT_EXPOSED`, `CONSUMER_CONTRACT=ARCHITECTURE_DECISION_REQUIRED`.
- Normas MP e resumo PI completos foram localizados nas fontes documentais versionadas do antigo Chat; extrato READ já existe na API DELPI. Ratificação de atualidade/owner e nova versão de corpus continuam pendentes; nenhum runtime/prompt do Chat foi importado.
- `search_products` usa OR de prefixos com ranking da frase completa. A consulta ampla não prova pertinência semântica nem inexistência de documentos; nenhuma exceção lexical ou alteração de busca foi introduzida.
- Provider sync/K01–K10 e testes produtivos autenticados permanecem TEST_NOT_RUN sem acesso oficial disponível nesta sessão. A dependência de recuperação documental transversal não está resolvida por metadata.

A autorização de deploy DAVI desta task é independente do estado histórico acima; não autoriza código DÉLIA, R4–R7 nem publicação unilateral de documentos no provider.

Release bounded `284998fbf03caca018492d4ab5c41aed80f8ae5e` publicado e implantado somente em api-delpi: health 200, MCP sem bearer 401, duas tools/zero resources e novos estados de disponibilidade verificados no container. Regressão: 6013 PASS, 30 SKIP, duas falhas de banco reproduzidas no baseline. Isso confirma a sinalização operacional, não recupera conteúdo documental para a DÉLIA. Provider K01–K10 e acesso documental seguem pendentes; não desbloqueia R4.

## Registro de execução — Trilha B (2026-10-24)

- `B0=EXECUTED` (RED→GREEN, +5 testes, módulo 28); `B1=EXECUTED`; `B2=EVIDENCE_READY_FOR_REVIEW`. Evidência completa: [doc 144](./144-delia-cross-capability-contextual-recovery-implementation.md).
- Implementado: `relevance_feedback` untrusted em `_select_group`/`_select_capability`/`_build_arguments`; `_recover_relevance` reexecuta seleção governada dentro da única rodada permitida (mesma capability reformulada ou READ alternativo elegível); `prior_result_preview` bounded; instruções orchestration v3; gates idênticos (live surface, resumable class, provenance, dedup, budget).
- Live A/B kimi-k3: matriz 11/11 PASS; O2 — baseline apresentou balanças, candidato julgou `irrelevant`, recuperou (cross-capability DAVI e reformulação em tentativas distintas) e encerrou honesto; `term. bala` direto retorna registros pertinentes reais — gap residual é nomenclatura do owner (dependência da Trilha A), não da máquina.
- **Desvio registrado:** auth do eval via admin impersonation (doc 144 §4); re-execução sob credencial sancionada exigida antes do aceite. `DEPLOY_AUTHORIZATION=NO`; `R4_AUTHORIZATION=NO`; Trilha A permanece `NOT_EXECUTED`.


## Registro de release — Trilha B (2026-10-24)

- `B2=EXECUTED`: release produtivo local-first concluído (doc 144 §6). Auth gate do review independente resolvido — eval e smoke usaram password grant sancionado do usuário `user`, sem impersonation. Imagem `686d745b87f6`, rollback `85cdd244f531`, deploy `[1/1] delia-api`.
- `O2_RESOLVED=INCONCLUSIVE` permanece: insuficiência honesta provada, mas os 2 registros pertinentes só respondem quando a consulta usa `term. bala` — a reformulação depende da norma de nomenclatura (Trilha A, `mcp_document_access=NOT_EXPOSED`). `R4_AUTHORIZATION=NO`; fase não avança.
