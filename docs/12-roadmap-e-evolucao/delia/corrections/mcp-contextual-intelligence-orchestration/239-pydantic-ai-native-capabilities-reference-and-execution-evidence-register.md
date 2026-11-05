# 239 — DÉLIA · Pydantic AI Native-First — Biblioteca de recursos e registro cumulativo de evidências

**DATE:** 2026-11-04  
**STATUS:** REFERENCE / PLANNED ADOPTION — documentação, não implementação nova  
**LAST VERIFIED IMPLEMENTATION:** `0b40e42af6d3bb6b6f7d2e185fe92db92e70b46d` — execução do Documento 238  
**PREDECESSORS:** documentos 220, 226, 228–238; plano 235 e rework 237; ledger  
**PIN OBSERVED:** `pydantic-ai[openai]==2.50.0` (revalidar no HEAD)  
**VIDEO:** https://www.youtube.com/watch?v=vxnGi9WTHM0 — **NOT_REVIEWED**, sem conteúdo/transcrição comprovados; não atribuir conclusões deste documento ao vídeo.

## 0. Direção e autoridade

A DÉLIA é standalone Continuous Operational Intelligence. O usuário informa objetivo, não roteiro de ferramentas. O agente Pydantic AI pode fazer READ A, observar, escolher READ B de outro MCP, analisar, perguntar ao usuário e continuar, sem workflows hardcoded por domínio. **Native-first ≠ delegar autorização ou verdade factual ao LLM**. Keycloak autentica, Core AuthZ live autoriza, Domain APIs são autoridade de negócio, DÉLIA verifica Evidence/Policy/Decision/Outcome, Automation Hub executa tecnicamente; MCP/A2A são interop e dados não confiáveis. SDK do Pydantic AI pertence à infraestrutura, não ao Domain/Application. Nunca criar novo planner, registry, engine, fluxo LangGraph paralelo, branches provider-specific ou comparação fixa para cada intenção.

Reancorar antes de executar: HEAD/git status → Project Instructions/.cursor → 16→50→17→49→51→52→21→20→25 → arquitetura técnica → product spec → docs temáticos → ledger. Em conflito, STOP e `EXECUTION_DRIFT`/`ARCHITECTURE_DECISION_REQUIRED`. Para cada escolha, registrar `EXISTING_EQUIVALENT` e `REUSE_DECISION`.

## 1. Biblioteca oficial de Pydantic AI — documentação para consulta

Links da documentação pública (versão corrente pode diferir do pacote 2.50.0); consultar também README e fonte instalada antes de cada adoção:

- Agent e tool loop: https://ai.pydantic.dev/agents/
- Tools e tool arguments: https://ai.pydantic.dev/tools/
- Toolsets / FunctionToolset: https://ai.pydantic.dev/toolsets/
- Dynamic/deferred toolsets: https://ai.pydantic.dev/toolsets/#dynamic-toolsets
- Tool search: https://ai.pydantic.dev/tool-search/
- MCP client: https://ai.pydantic.dev/mcp/client/
- Dependencies/RunContext: https://ai.pydantic.dev/dependencies/
- Structured output / validators: https://ai.pydantic.dev/output/
- Message history: https://ai.pydantic.dev/message-history/
- Retries: https://ai.pydantic.dev/retries/
- Testing: https://ai.pydantic.dev/testing-evals/
- Evals: https://ai.pydantic.dev/evals/
- Observability: https://ai.pydantic.dev/logfire/

**Nota:** URL/feature = referência de pesquisa, não prova de presença na versão fixada ou no provider Ollama. Se qualquer link mudou, localizar a seção oficial equivalente antes de registrar API como `PROVEN`. Não atualizar dependência sem teste de compatibilidade.

## 2. Matriz de capacidades: framework → código atual → experimento necessário

| Recurso | Uso recomendado na DÉLIA | Evidência atual | Próxima verificação |
|---|---|---|---|
| `Agent` + tool loop | Escolher A→B→C dinamicamente, sem sequenciador próprio | **PROVEN:** runtime Pydantic AI; E02 READ real no doc 238 | E03/E04/E05/E10 multi-etapas e generalização |
| `FunctionToolset` / `add_function` | Expor capabilities live como ferramentas semânticas nativas | **PROVEN:** doc 238, 10 caps projetadas, `davi.discover_delpi_information` invocado | Verificar visibilidade equilibrada de muitos MCPs, limite e schema |
| Tool schemas/typed args | Evitar JSON manual; validar schema real no owner boundary | **PARTIAL:** `arguments: dict` + `query` fallback; Pydantic superficial | Provar native schema específico, schema inválido, revoked AuthZ e payloads adversariais |
| Toolsets dinâmicos / `prepare` | Filtrar/expor capabilities úteis conforme request/identidade sem construir registry paralelo | **PARTIAL:** projeção live + dynamic add_function | Comparar seleção e latência com catalog JSON-only |
| Deferred tools / tool search | Descoberta escalável para catálogos grandes, se versão/modelo suportarem | **TO_INVENTORY** | Inspecionar SDK 2.50.0 e Ollama; piloto pequeno com avaliação A/B |
| `MCPToolset` | Reusar transporte se compatível com gates existentes | **EVALUATE ONLY** | Não expor MCP bruto contornando Domain/Core/Policy/candidate |
| `RunContext`, deps tipadas | Correlation, contexto, orçamento, handles e observações | **PROVEN em código** `InvestigationDeps` | Testar cancelamento e contexto entre turns sem tratar memória como autoridade |
| `output_type`, output validators | Síntese tipada: claims, evidence refs, limites, esclarecimento | **TARGET** | Reusar contracts de Interaction/Evidence; validação factual determinística após output |
| Retries nativos / validation errors | Corrigir argumentos inválidos sem loops próprios duplicados | **PARTIAL** `retries=1`; doc 238 fallback schema | Avaliar erros reais do modelo Ollama e custo de reparo |
| Histórico de mensagens | Continuidade entre investigação e pergunta do usuário | **PARTIAL** `prior_turns` + obs handles | Verificar follow-up vivo e freshness de SourceRefs; sem chain-of-thought persistida |
| Clarification/deferred interaction | Perguntar antes de prosseguir quando faltam identificadores | **PARTIAL** `request_user_clarification` | E07 follow-up real, estado recuperado sem duplicar persistence |
| UsageLimits, tracing, telemetry | Limites, token/latência, first-owner READ, tool calls | **PARTIAL** E02 metrics | Medir custo e fechamento de todo ciclo, timeout/cancel |
| Testing/FunctionModel/TestModel/Evals | Separar contratos, decisões do modelo e business outcome | **PARTIAL** testes GREEN doc 238 | Dataset multi-MCP, paraphrases e negativos em modelo real |
| Stream / NDJSON | Atividade coerente e único terminal | **PROVEN PARCIAL** doc 238 NDJSON 11 linhas | Matriz completa JSON/NDJSON, erro e cancelamento |
| Approval/deferred tools/durable exec | Só usar se atender writes governados e interação legítima | **NOT ADOPTED** | Não substituir Core/Policy/Decision/Automation Hub |

## 3. Exemplos de uso — didáticos, NÃO integração empresarial

### Exemplo A: loop de ferramentas sem fluxo específico

```python
from pydantic_ai import Agent, FunctionToolset
tools = FunctionToolset()

@tools.tool_plain
def consultar_pedido(numero: str) -> dict:
    return {"pedido": numero, "material_pendente": "MAT-100"}

@tools.tool_plain
def consultar_material(codigo: str) -> dict:
    return {"codigo": codigo, "fornecedor": "FORN-20"}

agent = Agent(
    "openai:gpt-4.1",
    toolsets=[tools],
    instructions="Investigue o objetivo usando ferramentas quando necessário.",
)
# Exemplo com dados fictícios: ferramentas reais DÉLIA devem passar
# por ports governados, live AuthZ e autoridade da Domain API.
# result = agent.run_sync("Por que o pedido 123 atrasou?")
```

### Exemplo B: interface tipada e governada

```python
from dataclasses import dataclass
from typing import Protocol
from pydantic_ai import Agent, FunctionToolset, RunContext

class GovernedReadPort(Protocol):
    async def invoke(self, capability_id: str, args: dict) -> dict: ...

@dataclass
class Deps:
    port: GovernedReadPort
    correlation_id: str

toolset = FunctionToolset()

@toolset.tool
async def read(ctx: RunContext[Deps], capability_id: str, args: dict) -> dict:
    return await ctx.deps.port.invoke(capability_id, args)
```

**Cautela:** esses são exemplos de API e responsabilidade, não código drop-in aprovado: validar assinatura exata na versão instalada; não copiar interfaces se ports existentes já atendem.

### Exemplo C: output tipado

```python
from pydantic import BaseModel, Field

class Claim(BaseModel):
    text: str
    evidence_handles: list[str] = Field(default_factory=list)

class InvestigationResponse(BaseModel):
    claims: list[Claim]
    gaps: list[str] = Field(default_factory=list)
    clarification_question: str | None = None
```

**Não basta** um claim referir `obs:1`; a Application deve comprovar que `obs:1` existe, tem provenance adequada, corresponde ao objeto correto e realmente sustenta a afirmação, aplicando domínio e obrigações originais. Nenhuma LLM output vira FACT.

## 4. Registro dos prompts e resultados efetivamente recebidos

| Plano / prompt | Execução e SHA | Resultado provado/reportado | Residual aberto |
|---|---|---|---|
| Doc 231 → doc 232 | `d989ab3716` implementation, `9c963db5f6` docs | LangGraph retirado, Pydantic AI agente+tool loop; unit/backend GREEN reportado | Legacy semantic wrapping; live E2E não rodou |
| Rework doc 232 → doc 233 | `d8fdc646fd45c6a617bd9ff70f158c2c1a30e070` | Removeu `run_governed_investigation` e fallback do agente; finalizer introduzido | REF05/cobertura semântica e live E2E |
| Rework doc 233 → doc 234 | `5cf2e975adb70cfa2900b30b3c059b7f04dc06cd` docs | Identidade por raiz owner, plano tipado e obrigações; backend GREEN reportado | E2E stale; obrigações heterogêneas ainda não generalizadas |
| Plano doc 235 → doc 236 | `57ca0e26842aeb0d55ce5da21d93e42afe887cd3` impl; `3830bd5b94d3002b4277b41103508f6729941264` docs | Tool args dict, declare opcional, esclarecimento, compose opcional, SHA-matched local runtime | **E02 owner READs=0**; list-only, ~8977ms, 1422/29 tokens; E03/E04/E05/E10 unbound |
| Rework doc 237 → doc 238 | `0b40e42af6d3bb6b6f7d2e185fe92db92e70b46d` | **E02 REAL GROUNDED / OBSERVATION**; discovery→execute→get_product_structure; catalog 10; pytest GREEN reportado; NDJSON 11 linhas | E03/E04/E05/E10 NÃO atingiram outcome grounded. E07/8 honest NON_GROUNDED; E06 parcial. |

Não confundir `EXECUTED` com `ACCEPT`. A leitura do doc 238 e diff do commit foi realizada nesta coordenação; **não reexecutei pessoalmente o E2E nem a suíte**. O relatório declara `EVALUATED_SHA==LOCAL_RUNTIME_SHA` e aproximadamente **41.140 ms** E02, tokens **input≈3197/output≈76** parciais. Revalidar no runtime antes do aceite integral. E02 é **FUNCTIONAL_ACCEPTANCE_CANDIDATE=YES somente para o gate E02**. Segurança e generalização integradas ainda requerem evidência.

### Causas E02 reveladas pelo doc 238 e lições gerais

1. Catálogo não estava vazio (10 capabilities live; `api-delpi:2`, `transformometro-api:4`, `tv-dashboard-api:4`); o modelo encerrava após `list_read_capabilities`.
2. Com tools nativas por capability, discovery alcançava Application e chained READ, mas resultado real era marcado `discovery_metadata_observation` e descartado na finalização.
3. `query` omitida e `candidate_arguments` frágil no modelo local abortavam cadeias; correções schema/utterance bindings foram adicionadas.
4. O sucesso E02 demonstra o *caminho técnico* do primeiro owner READ, não generalização para investigações dependentes ou claims múltiplos.

**Medidas antirregressão:** nunca remover execução/provenance de uma READ já obtida por engano de metadata; nunca classificar sucesso de tool como business outcome; medir chain per-stage; manter catalog e tool visibility auditáveis; preferir capacidades Pydantic AI a selectors próprios; não adicionar hardcode para E03/E04.

## 5. Próximos experimentos dirigidos por evidência — sem outra arquitetura

**P0 — REASON do E03/E04/E05/E10:** capturar modelo, tool choices e turn traces: após primeira READ ele decide esclarecer/parar; distinguir limite, output curto, schema, contexto/truncamento, instruction budget, ferramentas omitidas e erros de reasoning. Não atribuir ao modelo sem prova e não presumir que ferramenta dinâmica resolve por si só. A/B `FunctionToolset` preparado, descrições/schema/payload/structured output com versão instalada; testar Ollama e alternativa autorizada somente se já prevista, sem provider branches.

**P1 — Multi-step heterogêneo:** cenários reais `READ A→B`, `A→B→C`, cross-owner e discovery-first, com fonte A determinando a tool B. Registrar relevant source identity, authorization, task outcome e false grounding. Confirmar que o agente não inventa token/candidate.

**P2 — Evidence synthesis:** outputs tipados com claims/references e validadores existentes. Corrigir E3 obrigação omitida, partial compose, classificação indevida por metadata, multi-source last-only; sem novo Evidence Engine. Verificar que regras de identidade são owner/schema-specific **somente no adapter/verifier legítimo**, não no planner.

**P3 — Continuidade:** testar esclarecimento e segundo turno com evidências anteriores verificadas, sem confiar em memória, logs ou cache como autorização. Não criar nova persistência se os contratos existentes bastam.

**P4 — Escala/observabilidade:** tool search/deferred tools conforme SDK+provider efetivos; compare large catalog vs native dynamic tools; medir token, latency, first-owner READ, call counts, failure rates, grounding, success/safety. Sem Pydantic Evals obrigatório se custo/benefício não provado: validar com datasets existentes primeiro.

**P5 — Legado:** após outcomes reais, considerar remoção do `DELIA_ORCHESTRATION_ENGINE=delia` rollback e código `_governed_owner_path` sem consumidores. Remover somente com matriz de parity, contrato, testes e fallback operacional autorizado. Não confundir remoção de code com prova de resultado.

## 6. Contrato de acompanhamento dos próximos prompts

Toda task subsequente precisa entregar:
- `TASK_ID, BASE_HEAD, EVALUATED_SHA, LOCAL_RUNTIME_SHA, FINAL_SHA, PUSH_VERIFIED`;
- `AUTHORITIES_READ, CP_RQ, EXISTING_EQUIVALENT, REUSE_DECISION, EXECUTION_DRIFT`;
- `SDK_VERSION, FEATURE_API_MATRIX (signature), NATIVE_VS_CUSTOM, files removed/retained`;
- `MODEL_CONFIG, tool catalogue, tool calls, owner READ count, cross-owner sequence, continuation`;
- `E01–E10 individual task outcomes, false GROUNDED, RC-B, RC-C, REF05, E1–E4`;
- `MODEL_CALLS, INPUT_TOKENS, OUTPUT_TOKENS, TIME_TO_FIRST_READ, TOTAL_LATENCY`;
- `TESTS (unit/integration/live), security/AuthZ/Policy, NDJSON, consumer regressions`;
- `UNRESOLVED, next bounded step, outcome evidence, verdict`.
When not measured: `NOT_MEASURED`, `TEST_NOT_RUN`, `INCONCLUSIVE`, never PASS. A task's report enters numbered docs + execution ledger and this reference matrix gets updated **only with new actual evidence**, never with predictions.

## 7. Execution direction and safety

Next implementation should be one bounded executor task, with first objective **real multi-step E03/E04/E05/E10**, using Pydantic AI native tools and genuine owners, no branch by query shape and no new agent framework. Formal phase/NEXT stays tied to authority 16+ledger in real HEAD. `PRODUCTION_DEPLOY=NOT_AUTHORIZED` unless separately authorized. Local isolated build/E2E is allowed with legitimate access; no prod script, prod volumes, impersonation or secrets in prompts.
