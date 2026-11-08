# DÉLIA — Plano mestre de adoção global de PromptedOutput nativo (C3 / R01)

**Data:** 2026-11-08. **Estado:** PLANNED — plano de implementação aprovado quanto à direção; nenhuma alteração funcional ou deploy realizada neste registro. **BASE_HEAD verificado antes da escrita:** `cb425fbb3161a2ec29815a687521400654e25c3f`. **Owner:** DÉLIA (investigation e model invocation); **fase:** C3 sujeita à revalidação da autoridade 16/ledger. **Decisão de coordenação:** validar tecnicamente `PromptedOutput` e, se passar, migrar **todas as superfícies de structured output elegíveis no mesmo ciclo de execução**, com exceções apenas mediante prova de incompatibilidade e decisão explícita. Não deixar mistura permanente por conveniência.

## 1. Autoridade, precedência e escopo

Toda execução começa com `HEAD/git status → Project Instructions/.cursor → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → arquitetura técnica → product spec → spec temática → ledger`. Registrar SHA, owner, CP/RQ e gates antes de alterar código. As fontes canônicas são superiores a este plano; conflitos exigem `EXECUTION_DRIFT` ou `ARCHITECTURE_DECISION_REQUIRED`, nunca reconciliação implícita.

Documento de decisão precedente: `docs/12-roadmap-e-evolucao/delia/corrections/mcp-contextual-intelligence-orchestration/r01-native-structured-output-decision.md`. Estado R01 e dependências: `docs/12-roadmap-e-evolucao/delia/evidence/teo-delia-seven-residuals-backlog-2026-11-08.md`. Estado de execução: `docs/12-roadmap-e-evolucao/delia/evidence/execution-ledger.md`. Leia os documentos temáticos de Pydantic AI e a política permanente de eliminação de legado.

Escopo: somente runtime e testes da DÉLIA para Agents que exigem **structured output**. Fora de escopo: outras aplicações do monorepo, plain text legítimo, domínio, TÉO/MCP contracts, frontend, auth, tool limits R03, snapshot R04, credenciais R06, falhas preexistentes R07, migrations e deploy de produção.

## 2. Objetivo e decisão padrão

Adotar o recurso nativo do Pydantic AI 2.50.0 (revalidar versão no HEAD/runtime):

```python
from pydantic_ai.output import PromptedOutput
# em cada Agent elegível, usar diretamente:
output_type=PromptedOutput(ExistingPydanticModel)
```

Não criar `OutputStrategyFactory`, novo registry, serializer, parser, reparador de JSON, novo planner, adapter universal, retry engine, fallback por modelo ou configuração de política divergente. Permanecem: Pydantic AI Agent, MCPToolset, ProcessHistory quando presente, Pydantic schemas existentes, output validators, model invocation contracts, Evidence, Policy, acceptor/Outcome, AuthZ live e limites bounded. `PromptedOutput` melhora a solicitação e validação estruturada; **não garante resposta válida, tool call ou Outcome**, e não elimina fallback honesto após falhas esgotadas.

**Adoção global não é cegueira:** todos os Agents elegíveis migram após gate de compatibilidade. Incompatibilidade comprovada implica STOP/decision gate, não manutenção silenciosa de estratégias mistas.

## 3. Inventário inicial comprovado e residual search obrigatório

### Superfície A — Investigation (PROVEN)
- `delia-api/app/infrastructure/orchestration/pydantic_ai_investigation.py` — `Agent(..., output_type=InvestigationAnswer, toolsets=[agent_toolset], ...)`; o tipo representa decisão de investigação e a ferramenta MCP é parte crítica. Migrar para `PromptedOutput(InvestigationAnswer)`.
- `delia-api/tests/test_pydantic_ai_native_first_consolidation.py`, `delia-api/tests/test_g1_native_structured_output.py`, `delia-api/tests/support/native_mcp_fixtures.py`; localizar testes adicionais.
- Branch R01 anterior: retry one-shot no `output_validator` para COMPLETE/PARTIAL sem evidence; reavaliar se causa redundância e falso retry conceitual por teste comportamental, não por grep.

### Superfície B — Model Invocation (PROVEN)
- `delia-api/app/infrastructure/model_invocation/pydantic_ai_adapter.py` — `Agent(..., output_type=_proposal_model(tuple(request.expected_fields)), instructions=stage_instructions)` com model dinâmico. Migrar para `PromptedOutput(_proposal_model(...))` após testes de consumidores/contrato; preservar prior_context, `instructions` (não trocar por `system_prompt`), timeout absoluto, limite de output, campos esperados e payload existente.
- Inspecionar testes reais, erros de validação, serialização, casos sem campos, histórico e chamadas de consumidores.

### Superfícies adicionais (TO_INVENTORY)
- Executar busca residual em **todo o runtime DÉLIA e testes**, abrangendo `Agent(`, `output_type=`, `ToolOutput`, `NativeOutput`, `PromptedOutput`, `TextOutput`, `_proposal_model`, `output_validator` e construções indiretas. A busca é discovery, não prova de ausência; verificar runtime/imports e consumidores. Inspecionar scripts e harnesses para evitar substituir código de benchmark/histórico sem consumidor produtivo.
- Para cada hit documentar `owner|consumer|pydantic_type|output_mode|eligibility|reason|decision|evidence`.
- Se houver outros Agents estruturados elegíveis, migrá-los nesta mesma execução. `TextOutput`/texto legítimo não deve ser transformado em structured output por decreto.

**EXISTING_EQUIVALENT=YES** para output estruturado nativo; **REUSE_DECISION=REUSE**. Se isso mudar por evidência nova, STOP para gate de decisão.

## 4. Plano executável — gates sequenciais, com entrega de código

### G0 — Reancorar/limpar scope
Provar HEAD, worktree, autoridades, fase e SHA base. Preservar trabalho concorrente; isolamentos de commit. Definir previamente budget bounded de avaliação real, recursos e credenciais autorizadas. Identificar contratos/consumers para cada Agent.

### G1 — Testes RED comportamentais (obrigatório ANTES do diff)
Usar TestModel/FunctionModel ou fixtures nativas do Pydantic AI em **caminho produtivo**, não testes que fazem `open(source).read()` e procuram strings. Cobrir:
1. Investigation: resultado `InvestigationAnswer` válido chega ao validator/acceptor; refs inválidas não viram FACT.
2. Prosa inválida: parsing/retries nativos/timeout limitados, fallback honesto e sem falsa completude.
3. MCP coexist: Agent invoca ferramenta autorizada, recebe resultado, depois entrega `InvestigationAnswer`; pode não chamar tools em pergunta puramente conceitual.
4. Zero-call COMPLETE/PARTIAL: branch de retry anterior realmente dispara no path tipado apropriado; não ocorre loop, nem forçagem desnecessária de MCP ou falsa conclusão.
5. Model invocation dinâmico: expected_fields presentes/tipados, erros corretos, prior history e stage instructions preservados, respeito ao absolute timeout.
6. Unauthorized capability: fail-closed, sem tools criadas por retry, nenhuma tentativa de write.
7. Proteção contra regressão de ambos os Agents e respectivos consumidores.
Registrar provas RED no path real, não artificialmente desconectar o Agent.

### G2 — Validar estratégia antes da expansão
Na branch/dev isolada, aplicar primeiro somente à investigação, e rodar suíte comportamental + **avaliação real mínima** Qwen C1 e B1, Kimi C1 ou B1, controle conceitual. Prioridade inegociável: coexistência MCP+PromptedOutput **que ficou TEST_NOT_RUN no spike**, além de saída tipada e ausência de regressão. A comparação deve manter SHA/config/pergunta/identity/catálogo/tool fingerprint. Se a estratégia bloquear calls, alterar permissões, gerar regressão grave ou incompatibilidade contratual → rollback e `ARCHITECTURE_DECISION_REQUIRED`; NÃO prosseguir com mistura parcial.

### G3 — Migração global de todas as superfícies elegíveis
Se G2 passar, migrar superfície B e todos os demais Agents produtivos elegíveis descobertos. Utilizar diretamente `PromptedOutput(Model)` em cada ponto, mantendo schemas Pydantic, prompts de negócio e contracts. Evitar introduzir um comutador por env/modelo em produção. Se houver código duplicado ou workaround criado exclusivamente para modos antigos, comprovar falta de consumer e remover em menor diff. Não apagar harnesses legítimos sem avaliação de owner. Não trocar `system_prompt/instructions`, cancelamento de timeout ou error types sem evidência.

### G4 — Regressão por consumidor e suíte completa
Rodar testes RED→GREEN, focused de investigation/model_invocation/composition/evidence/auth/policy/structured output, e **suíte backend DÉLIA completa** pelo comando canônico. Reportar exit codes e contagens, falhas preexistentes vs novas. Falha de suíte implica FAIL/PENDING, nunca PASS. Não ajustar expectativas para mascarar comportamentos.

### G5 — Matriz real Kimi e Qwen, múltiplos owners
Repetir com as versões exatas e ferramentas autorizadas:
- Qwen C1 ×3, B1 ×2; Kimi C1 ×2, B1 ×2;
- controle conceitual sem MCP ×1 por modelo;
- holdout operacional de ao menos 1 owner **não TÉO** ×1 por modelo;
- model_invocation dinâmica ×1 por provider/modelo quando contrato exigir uso real.
Verificar instrumento de avaliação e budget predefinido; se bloqueado registrar `TEST_NOT_RUN` e não autorizar migração como validada. Logs sem secrets, chain-of-thought ou payload confidencial. Traces: `EVALUATED_SHA, model/digest, provider, instruction_version, PromptedOutput strategy, output_valid, validator_entered, retries, offered_tools, tool_calls, invalid_calls, evidence_refs, grounded, outcome, latency, tokens(if available), cost`.
Gates independentes `STRUCTURED_OUTPUT`, `MCP_TOOL_USE`, `OPERATIONAL_OUTCOME`, `GENERALIZATION`, `SECURITY`, `MODEL_INVOCATION_COMPATIBILITY`. Qwen C1 `NOT_ACHIEVED` não é sucesso operacional só por retornar JSON tipado. Falta de dados ou capability deve finalizar honesta e segura.

### G6 — Remoção de legado e residual search
Buscar todos os `Agent(...)` do runtime, inclusive imports indiretos e todo `output_type`; comprovar que **nenhum Agent estruturado elegível usa modo implícito/alternativo não aprovado**. Exceções necessitam evidência de incompatibilidade + aprovação de owner; sem isso impedir ACCEPT global. Remover flags de spike (`DELIA_OUTPUT_STRATEGY` se tiver sido persistida), branches mortos, parsing redundante e documentações de fluxo antigas que prescrevam modo já retirado; preservar código e documentação histórica como evidência, com supersession explícita em vez de apagá-los. Sem novo layer de padronização.

### G7 — Resultado e merge documental
Somente após evidências reais atualizar doc de decisão, este plano, ledger, backlog R01 (sem fechar se C1 continuar `NOT_ACHIEVED`), docs de contratos e testes. Commits pequenos e separados por escopo, push para origin/main conforme governança, verificar SHA e diff final. **PRODUCTION_DEPLOY=NOT_AUTHORIZED**.

## 5. Rollback, stop conditions e validação de conclusão

- Rollback técnico: reverter parâmetros `output_type` e imports nos Agents alterados, testes correspondentes e qualquer remoção de workaround com consumidores comprovados; rollback seguro no SHA/commit conhecido, sem afetar trabalho concorrente.
- STOP imediato se: contrato empresarial quebrado, MCP não coexistir, AuthZ violado, saída inválida aceita como FACT, Kimi regressão grave, model invocation consumidores quebrados, alteração exige arquitetura além do padrão nativo, ou decisão canônica conflitante.
- Definição de pronto para **padronização técnica global**: todos Agents elegíveis inventariados e migrados, exceções explicitamente aprovadas, suíte completa e comportamental PASS, MCP+Prompted comprovado em uso real, Kimi/Qwen comparados, negócio/segurança intactos, nenhum legado funcional sem owner, busca residual limpa e GitHub/ledger atualizados.
- **R01 é distinto do padrão técnico:** ainda `OPEN` se Qwen C1 não realizar investigação operacional e Outcome verdadeiro; `PromptedOutput` não autoriza encerrar por melhorar formato.

## 6. Evidências pré-existentes e limites

Spike da decisão R01: `ToolOutput` atual falhou com prosa no C1; `PromptedOutput` produziu `InvestigationAnswer` tipado `INSUFFICIENT` sem tool calls e C1 permaneceu `NOT_ACHIEVED`; `NativeOutput` tipou C1, mas B1 Ollama ficou >15min. **Tools×Prompted TEST_NOT_RUN**, **Kimi×Prompted TEST_NOT_RUN**, **model invocation×Prompted TEST_NOT_RUN**, **full regression TEST_NOT_RUN** nessa decisão. Não herdar PASS inexistente.

## 7. Relatório de execução e aceitação

```text
TASK_ID=DELIA-C3-PYDANTIC-AI-PROMPTED-OUTPUT-GLOBAL-MIGRATION-01
BASE_HEAD=
FINAL_HEAD=
ORIGIN_MAIN=
PUSH_VERIFIED=
AUTHORITIES_REANCHORED=
PHASE=
CP_RQ=
EXISTING_EQUIVALENT=
REUSE_DECISION=
AGENTS_INVENTORIED=
AGENTS_ELIGIBLE=
AGENTS_MIGRATED=
AGENTS_EXCEPTED_WITH_APPROVAL=
CONSUMERS_VERIFIED=
FILES_CHANGED=
RED_BEHAVIORAL_TESTS=
GREEN_BEHAVIORAL_TESTS=
FOCUSED_REGRESSION=
FULL_BACKEND_REGRESSION=
MCP_TOOL_COEXISTENCE=
QWEN_C1_3RUN=
QWEN_B1_2RUN=
KIMI_C1_2RUN=
KIMI_B1_2RUN=
CONCEPTUAL_CONTROLS=
NON_TEO_HOLDOUTS=
MODEL_INVOCATION_REAL=
STRUCTURED_OUTPUT_VERDICT=
MCP_TOOL_USE_VERDICT=
MODEL_INVOCATION_COMPATIBILITY_VERDICT=
OPERATIONAL_OUTCOME_VERDICT=
SECURITY_VERDICT=
GENERALIZATION_VERDICT=
R01_STATUS=
RESIDUAL_SEARCH=
LEGACY_REMOVAL=
ROLLBACK=
PRODUCTION_DEPLOY=NOT_AUTHORIZED
BACKLOG_UPDATED=
LEDGER_UPDATED=
EXECUTION_VERDICT=
NEXT_BOUNDED_STEP=
```

**Norma de coordenação:** validação inicial pode ser sequencial para evitar risco; **a entrega e aceite final serão globais**, não uma migração opcional permanente por partes. Se G2 falhar, interromper e reportar evidência; se G2 passar, executar G3–G7 no mesmo escopo. Não aceitar documentação-only, teste de strings ou alegação de que uma saída tipada equivale a conclusão empresarial.


## 8. RESULTADO DA EXECUÇÃO — gate G2 falhou (rollback executado)

**Data:** 2026-11-08 | **Commits:** migração `b30d8b3`, rework/fixtures, rollback `ver HEAD`.

- **Migração aplicada:** os 2 Agents produtivos (investigation, model_invocation) migrados para `PromptedOutput`; fixtures de teste adaptadas (final_result→texto JSON, custom_output_args→custom_output_text); suíte focada verde (~148 testes).
- **Gate G2 — MCP×Prompted coexistência: FALHOU (PROVEN).** Em eval real (dev stack, identidade autorizada, `live_catalog=12` capabilities confirmadas ofertadas): Qwen C1×3, Kimi C1×2, Kimi B1×2, controle conceitual — **0 invokes MCP em todos os cenários**. O modelo emitia `InvestigationAnswer` tipada `insufficient`/`clarification` (narrando intenção em vez de executar) — inclusive Kimi B1 que no baseline ToolOutput fazia 6-8 invokes GROUNDED. Repetido: runs solo sem contenção, e variante `template=` com instrução tool-use-first — ainda 0 invokes. Retry bounded existente disparou (2 passes) sem conversão.
- **Causa caracterizada:** `PromptedOutput` dá ao modelo um caminho de resposta final em texto que valida imediatamente — o modelo emite a declaração tipada no 1º turno em vez de investigar. Não é bloqueio de ferramenta (tools presentes e chamáveis — `request_user_clarification` foi usada); é âncora comportamental do modo de saída nesta família de modelos.
- **Ação:** ROLLBACK conforme §5 stop-condition — arquivos produtivos e fixtures restaurados ao baseline `14179184` (output_type original). Nenhuma mistura parcial mantida.
- **Veredicto:** `ARCHITECTURE_DECISION_REQUIRED` — globalização de `PromptedOutput` reprovada no gate de coexistência por evidência real. Opções para coordenação: (a) manter ToolOutput implícito e tratar o gap de prosa só quando tipado (status atual — honesto NON_GROUNDED); (b) instrução/contrato que force investigação antes de resposta tipada (risco de ancoragem provado); (c) avaliar `NativeOutput` por-provider no adapter legítimo (latência Ollama documentada); (d) combinação investigação-forçada + output nativo sob nova spike. **R01 permanece OPEN.**
