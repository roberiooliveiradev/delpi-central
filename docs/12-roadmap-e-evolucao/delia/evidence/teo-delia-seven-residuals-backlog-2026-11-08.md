# DÉLIA × TÉO — Backlog controlado dos sete residuais (2026-11-08)

**STATUS:** DISCOVERY/COORDINATION ONLY — sem autorização implícita de código, deploy, alteração de fase ou contratos.
**BASE_HEAD consultado:** `cd20df27a96846dfb865673c4e76d64800f9fd6f`.
**Evidência principal:** `docs/12-roadmap-e-evolucao/delia/evidence/teo-persistent-deploy-real-integration-rework-01.md` e execution-ledger da task `DELIA-C3-TEO-PERSISTENT-DEPLOY-AND-REAL-INTEGRATION-REWORK-01`.
**Referências técnicas:** `transformometro-api/tm_app/interface/mcp/server.py`; `transformometro-api/tm_app/application/services/dashboard_view_scope_service.py`; `delia-api/config/pydantic_ai.runtime.delpi.json`; `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py`.

## Método de trabalho e autoridade

Resolver **um item por vez**, por ordem de dependência, sem ampliar o escopo das tasks. A cada task: HEAD/git status → Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → arquitetura técnica → product spec → spec temática → ledger. Identificar CP/RQ, owner e contrato antes da implementação. Tratar fatos documentados separadamente de observações em runtime; o código e o ledger não substituem os testes. **Não confundir GROUNDED, HTTP 200, execução de ferramenta ou modelo sem erro com Outcome empresarial completo.**

Para cada correção: RESPONSABILIDADE → OWNER → FONTE CANÔNICA → CONSUMERS → CONTRATO → IMPLEMENTAÇÃO → TESTE → OUTCOME EVIDENCE. Registrar `EXISTING_EQUIVALENT=YES|NO|TO_INVENTORY` e `REUSE_DECISION=REUSE|EXTEND|NEW` antes de novas abstrações; preferir reutilizar frameworks e contracts existentes. Sem branches semânticos específicos de modelo/owner na DÉLIA. Writes governados; sem deploy implícito. Estados permitidos: `PROVEN|TO_INVENTORY|PLANNED|TARGET`, testes `PASS|FAIL|PENDING|INCONCLUSIVE|TEST_NOT_RUN|STALE_EVIDENCE`.

## Backlog de sete itens (nenhum considerado resolvido por este documento)

### R01 — Qwen não seleciona ferramentas no cenário C1 [P1]

- **Evidência observada (PROVEN no eval):** C1 Qwen r1/r2 `0 invokes`, resposta conceitual `NON_GROUNDED`; baseline histórico C1 Qwen `3 calls/0 fails` com `GROUNDED`. Não chamar de regressão de código comprovada: run/contexto/configuração precisam de comparação.
- **Owner inicial:** DÉLIA — model invocation/investigation; limitação de modelo é hipótese, não conclusão automática.
- **Diagnóstico bounded:** reexecutar C1 com mesma pergunta e fingerprint; inspecionar admissão, tool catalog visível ao modelo, instruções v41, tool choice, contexto/truncamento, resposta e contexto do snapshot. Comparar com baseline, Kimi e a versão do runtime.
- **Aceite:** causa ou fronteira divergente documentada; READ correto quando o cenário exigir e fontes autorizadas estiverem disponíveis, ou limitação honesta e causa classificada; testes de generalização/repetições; segurança e Outcome.
- **Estado:** OPEN; `FAIL` do caminho operacional observado; root cause `INCONCLUSIVE`.

### R01 — (resolução) Seleção de tools/zero-tool outcome — v. 2026-11-08

- **Causa isolada:** resposta COMPLETE/PARTIAL declarada com ZERO chamadas de owner e ZERO observações coletadas passava pelo `output_validator` sem a retry de insuficiência (que só cobria INSUFFICIENT/NO_EVIDENCE/EMPTY). Primeira fronteira divergente: validação de saída / continuação.
- **Fix mínimo (DÉLIA, provider-neutral):** extensão do `insufficiency_retry` one-shot existente em `pydantic_ai_investigation.py` — COMPLETE/PARTIAL com `tool_calls==0` + `collected==[]` + catálogo exposto → um `ModelRetry` nativo limitado, sem `tool_choice=required`, sem lógica por modelo, sem novo planner.
- **Evidência real:** teste de contrato novo + 70 focused tests PASS; eval real Qwen: B1 passou a usar tools (3 invokes, GROUNDED, dados reais dept engenharia); C1 ainda 0-call NON_GROUNDED honesto (modelo local produziu prosa; retry bounded engajou 2ª passada sem conversão) — melhoria parcial, não eliminação; Kimi não regridido em runs anteriores.
- **Causal rework (2026-11-08, b25c→0521c):** instrumentação live no validator provou que a resposta C1 falha NUNCA entra no `output_validator` — o modelo retorna prosa simples (não `InvestigationAnswer`; `declared_answer=null`; 2 passes = retry nativo de parse esgotado). Logo o branch COMPLETE/PARTIAL+zero-evidence não alcança essa classe de falha; B1 melhorou por caminho distinto (produziu structured output + tools). Fronteira real da falha: **modelo local emite prosa em vez de structured output/tool call** — recuperação nativa de parse já ocorre e falha idem; outcome final honesto NON_GROUNDED.
- **Decisão arquitetural (2026-11-08):** spike real pydantic_ai 2.50.0 — `PromptedOutput` e `NativeOutput` produzem `InvestigationAnswer` tipado válido em C1 (baseline ToolOutput vaza prosa). DECISÃO: `PromptedOutput` — provider-neutral, 1 parâmetro, latência ok; NativeOutput degradou >15min em Ollama. Doc: corrections/mcp-contextual-intelligence-orchestration/r01-native-structured-output-decision.md. Implementação = task seguinte (~2 linhas no Agent).
- **Migração executada e revertida (2026-11-08):** `PromptedOutput` aplicado globalmente reprovou no gate de coexistência — **0 invokes MCP em todos os cenários** (Qwen C1×3, Kimi C1/B1×2; live_catalog=12 ofertado; solo+template tool-use-first idem). Modelo emite declaração tipada em vez de investigar — âncora comportamental provada, não bloqueio de ferramenta. Rollback aplicado; veredicto ARCHITECTURE_DECISION_REQUIRED no plano mestre §8.
- **Causal definitivo (2026-11-08, instrumentação wire):** captura dos requests reais no C1 Qwen provou que TODAS as chamadas do run foram estágios `InvokeModel` (`REQ_FIELDS`: `requires_owner_surface`/`interaction_class`/`answer`, `N_FN=0` por design). A resposta de admission foi `requires_owner_surface=false` → `owner_required=False` → caminho conversacional → **o Agent de investigação com toolsets nunca executou** — 0 tools ofertadas, não ignoradas. A falha é de **classificação de admission** (modelo classifica pergunta operacional como conversational/explanation), não de output strategy, validator ou toolset. Explica tudo: declared_answer=null, mcp_invoke_targets=[], llm_runs=2 (admission+synthesis), variância histórica, Kimi ok.
- **Remediação admission v42 (2026-11-09, DELIA-C3-R01-SEMANTIC-ADMISSION-OPERATIONAL-CLASSIFICATION-REMEDIATION-01):** causa semântica PROVEN — C1 `processos na engenharia` (sintagma nominal com escopo organizacional) era classificado como `explanation`/`requires=false` sob v41. Correção no contrato existente `delia.capability_orchestration.interaction_admission` (v41→v42): object-first + owner path por default para sujeitos registráveis; `explanation` restrito a asks definicionais sem escopo de inventário; sem keyword routing, sem classificador novo, sem branch por modelo. Testes comportamentais de roteamento + harness `scripts/r01_admission_semantic_eval.py`. Eval real (one-off overlay, PRODUCTION_DEPLOY=NOT_AUTHORIZED): OpenRouter `qwen/qwen3-14b` C1 5/5 owner_path + matriz 7/7; Kimi C1 3/3 + matriz 7/7; baseline v41 C1 Qwen variava/falhava. Qwen local `qwen3:4b-instruct` TEST_NOT_RUN (Ollama cgroup/timeout CPU). Full MCP Outcome TEST_NOT_RUN (`invalid_grant` nas credenciais DEV_PORTAL disponíveis). Suíte backend delia-api PASS.
- **E2E autenticado DEV (2026-11-09, DELIA-C3-R01-ADMISSION-V42-NATIVE-MCP-ENDTOEND-OUTCOME-VALIDATION-01):** stack local (`b03ea2f1eb69_delpi-delia-api`, instruction v42 fp `8fed7885b7864b4b`, TEO MCP healthy, password-grant `rober` via gateway local). Auth prod permanece `invalid_grant` (senha DEV_PORTAL não sincronizada com KC prod) — contornado por ambiente DEV, sem bypass/reset. Perfil eval `openrouter_qwen` adicionado ao runtime JSON (default continua `local_ollama`). Matriz live `native_mcptoolset_direct_eval` + admission-only:
  - **Kimi** (`moonshotai/kimi-k3`): admission C1/B1/SIPOC 3/3; C1/B1 GROUNDED com MCP (8 invokes cada); SIPOC/PDCA 0 tools NON_GROUNDED; OPS_NON_TEO_1/2 + MULTITURN_TEO GROUNDED com MCP.
  - **Qwen14B** (`qwen/qwen3-14b`): admission C1/B1/SIPOC 3/3; C1 GROUNDED (2 MCP); B1 owner-path PROVEN (4 MCP) mas Outcome NON_GROUNDED (`filial_id`/clarification — residual R02/R03-class, não admission); SIPOC/PDCA 0 tools; OPS/MULTITURN com MCP (OPS_NON_TEO_1 NON_GROUNDED parcial).
  - **Qwen4B local** (`qwen3:4b-instruct-2507-q4_K_M`): admission C1 FAIL (2/2 `explanation`/owner_path=false); B1/SIPOC OK; E2E C1 0 MCP — residual de capacidade do modelo local na admissão, não regressão v42 nos modelos alvo.
  - Testes: `test_interaction_admission_routing` 8 PASS; suíte ampla delia-api 1 FAIL pré-existente (`g4` fixture path no container) fora do escopo. PRODUCTION_DEPLOY=NOT_AUTHORIZED.
- **Estado:** RESOLVED_WITH_RESIDUAL — admission→Agent→MCP→Evidence→Outcome PROVEN em DEV para Kimi e Qwen14B (C1); residual = (a) Qwen4B local ainda falha admission em C1; (b) qualidade Outcome parcial em alguns braços Qwen14B (escopo/filial/tool budget), ortogonal ao contrato v42.

### R02 — Argumentos READ inválidos / possível lacuna de metadata MCP [P1]

- **Evidência (PROVEN):** Qwen tentou `read(action=get)` sem `id` (três erros em B1); Kimi enviou filtros `q`, `page` ou `page_size` rejeitados como `INVALID_FIELD` (duas ocorrências registradas). A descrição diz `get uses id`, mas filtros admissíveis por entidade precisam de inventário.
- **Owner inicial:** TÉO — contrato `read` e Domain API; DÉLIA somente consumidora; comportamento de modelo permanece possível.
- **Diagnóstico bounded:** correlacionar description/schema em `tools/list` com validador real por entidade/action; distinguir erro de modelo de descrição ambígua. Não duplicar validação do domínio nem introduzir filtro universal fictício.
- **Aceite:** schema/descrição publicados e validados por testes positivos/negativos + B1/C1 real; queda de erros evitáveis com Outcome preservado.
- **Resolução (4f9→fcf3ae9):** causa = **Case A** — domínio validava corretamente (`ENTITY_FILTERABLE_FIELDS`: department só `filial_id`, branch nenhum, process `q`/`page`/`page_size`), mas a descrição `read` não declarava o contrato por entidade nem que `get` exige `params.id`. Fix mínimo: descrição publicada (server.py) declara `search|get`, `get` requer `params.id`, campos por entidade, INVALID_FIELD para campos não suportados, get_context entity=<name>. `_sig_kwargs` mantido (descarte limitado à assinatura; INVALID_FIELD vem do validador autoritativo). Default `get` preservado (compat).
- **Evidência:** teste contratual novo PASS; 89 MCP tests PASS; tools/list wire desc hash `b5e88a85c17854af`; prod imagem `31c2fa932dc1` deployed health 200. Evals reais: Kimi B1 8/0, B1_r2 8/0, C1 8/2 (classes diferentes: page_size-range, scope), C1_r2 8/0 — **0 INVALID_FIELD, 0 get-sem-id** (baseline: 3 get-sem-id Qwen, 2 INVALID_FIELD Kimi); Qwen B1 0-call NON_GROUNDED (R01 variance), C1 idem.
- **Estado:** RESOLVED_WITH_RESIDUAL — contrato corrigido e publicado; erros-alvo R02 zerados nos runs Kimi; comportamento de não-uso de tools do Qwen é R01, não R02.

### R03 — Limite compartilhado de oito tool calls interrompe investigações [P2]

- **Evidência (PROVEN em alguns runs):** B1 Kimi r1/r3 atingiu `tool_calls_limit` depois de READs e retries; histórico com 5/6 cenários densos tocando limite. Não inferir que aumentar de 8 resolverá.
- **Owner inicial:** DÉLIA — política comum de execução/governança.
- **Dependência:** tratar R02 e caracterizar chamadas produtivas antes de alterar limites. Não adaptar orçamento por modelo.
- **Aceite:** classificação trace por chamada (progresso, retry, discovery improdutivo), experimento bounded com uma única variável e oracle empresarial; aumento só se ganho líquido sem regressões em custos, segurança, latência e Outcome; teste anti-divergência permanece PASS.
- **Estado:** OPEN; efeito em casos específicos `PROVEN`; ajuste `PENDING`.

### R04 — Snapshot experimental de catálogo TÉO obsoleto [P2]

- **Evidência (PROVEN no relatório):** snapshot de 2026-11-02 em `DELIA_MCP_CATALOG_MODE=snapshot_experiment`, com descrição `analyze` antiga, afeta `discover_delpi_information`; MCPToolset de invoke usa tools/list live.
- **Owner inicial:** DÉLIA — catálogo/discovery, com TÉO autoridade de descrição.
- **Diagnóstico bounded:** validar consumo real e o owner do snapshot, mecanismo aprovado de refresh/retirement, versão/lineage, risco de drift; verificar se é apenas EVAL_ONLY. Não atualizar manualmente nem criar sincronização paralela.
- **Aceite:** snapshot atualizado/aposentado por boundary autorizado; discovery coerente com contrato TÉO; smoke/regressão e prova de que invoke live não foi alterado.
- **T2 decision package (2026-11-09):** prod ainda `snapshot_experiment` com DB ~2026-11-03; recomendação `RETIRE_FULL_SET`.
- **T2 ampliada execução (2026-11-09, PO RETIRE_FULL_SET):** código snapshot removido (interop/store/sync/tests); Settings fail-closed; compose limpo; live SpecialistInterop only. **Código R04/L-06:** CLOSED_PROVEN. **Prod flag:** ainda `PENDING_OPS` (sem mutação prod nesta task) — R04 só `CLOSED_PROVEN` após pós-condição ops verificada.
- **Estado:** `PENDING_OPS` (código retired; prod drift aberto).

### R05 — Kimi ainda repete erro de escopo ocasionalmente [P2]

- **Evidência (PROVEN):** B1 após contrato corrigido: `7 calls/2 scope fails`, `6/0`, `7/1` (último erro de READ, não de escopo). Houve redução expressiva de 5 erros de escopo históricos, não eliminação garantida; C1 Kimi fez READ department→IDs→3 analyze válidos.
- **Owner inicial:** investigação DÉLIA/modelo; TÉO somente se nova deficiência de metadata for demonstrada.
- **Dependência:** primeiro R02 e R04, separar falhas `scope` de `INVALID_FIELD`.
- **Aceite:** reproduções bounded, traces contendo feedback e payload visível ao modelo, explicação causal da repetição; reduzir churn sem hardcode, sem prompt por modelo, sem alterar controle de autoridade; Outcome verificável.
- **Estado:** OPEN; repetição residual `PROVEN`, causa exclusiva do modelo `INCONCLUSIVE`.

### R06 — Falta tools/list autenticado no endpoint MCP de produção [P3, gate operacional]

- **Evidência (TEST_NOT_RUN):** imagem persistente/health e tools/list autenticado em dev verificados; prod sem bearer → 401; falta credencial legítima de usuário prod, não inventar serviço-account nem usar dev credential no realm prod.
- **Owner inicial:** TÉO MCP + identidade/Keycloak/operador de produção; Core/domain preservam AuthZ.
- **Execução bounded:** obter credencial/token de curta duração pelo processo existente e autorizado, sem pedir/registrar senha em chat, prompts, logs ou GitHub; verificar initialize + tools/list do endpoint real e hash da descrição; garantir que DÉLIA consumer usa mesma metadata.
- **Aceite:** resposta autorizada de produção, descrição `analyze` correta, teste negativo 401 e auditoria sem segredo exposto; sem deploy adicional.
- **Estado:** OPEN; `TEST_NOT_RUN` por credencial.

### R07 — Dez falhas preexistentes na suíte completa do TÉO [P3, débito independente]

- **Evidência (FAIL):** `scripts/ci-transformometro-api.sh` teve 2040 PASS, 56 SKIP, 10 FAIL; executor reproduziu os mesmos 10 sem a correção MCP por stash. Grupos: bootstrap_filiais×2, dashboard_live×4, gpt_validation×1, process_instance_repo×1, shared_resource_scope×1, sign_invite_mail_trace×1.
- **Owner inicial:** TÉO e owners de testes/domínios respectivos, a confirmar por caso.
- **Diagnóstico bounded:** caracterizar cada falha por fixture, ambiente, contrato ou defeito real, sem atribuí-las ao MCP; planejar correção separada sem misturar com R01–R06.
- **Aceite:** suíte completa PASS ou residual explicitamente aceito por autoridade competente com evidência por falha; evitar ajustar teste para esconder bug.
- **Estado:** OPEN; `FAIL` preexistente confirmado pelo relatório, não corrigido.

## Sequência de tratamento

Ordem operacional sugerida: **R02 → R01 → R04 → R05 → R03**, pois metadata/READ e discovery podem contaminar a inferência sobre seleção e orçamento. **R06** é um gate independente e deve ser agendado assim que houver identidade autorizada. **R07** é débito independente e requer trilha própria.

Somente um item funcional ativo por vez; ao concluir, atualizar o status no ledger e nesta trilha com SHA de código, testes, generalização, outcome e decisão de aceite. Não prometer que correções contratuais vão automaticamente resolver comportamento do modelo.

## Definição de pronto para cada item

1. Causa e owner verificados; contrato existente consultado.
2. Alteração mínima somente se necessária, acompanhada de RED→GREEN.
3. Testes de regressão e avaliação real quando houver efeito em MCP/modelo.
4. Segurança, provenance e Outcome avaliados sem falso PASS.
5. Documentar evidência, diff, SHA, residual, rollback (quando aplicável) e revisão `ACCEPT|ACCEPT_WITH_RESIDUAL|REWORK|EXECUTION_DRIFT|INCONCLUSIVE`.
6. Não iniciar o item seguinte sem revisão do anterior.

**NEXT SINGLE BOUNDED STEP:** R02 — examinar e corrigir, se comprovado, o contrato READ do TÉO. Nenhuma alteração de código/deploy autorizada por este backlog isoladamente.
