# 249 — DÉLIA · Auditoria integral de infrastructure/model_invocation

**TASK_ID:** DELIA-C3-INFRASTRUCTURE-MODEL-INVOCATION-FILE-BY-FILE-NATIVE-CLEANUP-01  
**DATA:** 2026-11-05  
**HEAD AUDITADO:** `da30f51c3bdc153eb11d8ab30ba3334eab265c74`  
**STATUS:** AUDIT / PLANNED — NENHUM CÓDIGO REMOVIDO NESTA TAREFA  
**SCOPE:** `delia-api/app/infrastructure/model_invocation/` — 4/4 arquivos lidos integralmente via GitHub no mesmo SHA  
**RELATED:** docs 239–248, especialmente 242, 243, 245, 246; canonical authorities e execution-ledger  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED

## 1. Diagnóstico

O diretório já **não contém** `openai_compatible_adapter.py` (antiga inferência legada). Ele possui um adapter nativo Pydantic AI para o `ModelInvocationPort`, um test double determinístico, um adapter de transcrição de voz (boundary distinta) e `__init__.py`. A composição efetiva em `root_composer.py` instancia `PydanticAiModelInvocationAdapter` para chamadas textuais reais, `DeterministicTestAdapter` somente no caminho de teste, e `OpenAICompatibleTranscriptionAdapter` na ditado/transcrição. **Não tratar os três adapters como três motores semânticos concorrentes**: são contratos/consumidores diferentes. No entanto, o adapter nativo ainda conserva bastante mecânica de estágios antigos e merece limpeza agressiva coordenada com doc245.

Documentação de início do `__init__.py` está obsoleta: afirma que não existe provider real; já existe e está conectado. Corrigir comentário.

**EXISTING_EQUIVALENT:** YES Pydantic AI Agent/output_type, adapter ModelInvocationPort, single runtime JSON doc243, test support nativo TestModel, Port SpeechTranscriptionPort e serviço de dictation; TO_INVENTORY para equivalência do test double e uso direto SDK para STT (não assumir).  
**REUSE_DECISION:** REUSE/SHRINK `pydantic_ai_adapter` onde ainda há consumer legítimo; REUSE test doubles realmente necessários; KEEP voice boundary; REMOVE stages legados e comentários falsos; não criar adapter novo sem comprovação.

**Reancoragem exigida antes de qualquer mudança:** git status/HEAD/origin → Project Instructions/.cursor → authorities 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → spec temática → ledger, docs 239–249. Audit via GitHub não executou `git status`, suíte nem runtime local; search 0 não comprova ausência de consumo.

## 2. Matriz 4/4 arquivos

| Arquivo | Linhas API | Bytes | Funções/classes inspecionadas | Consumidores evidenciados | Decisão |
|---|---:|---:|---|---|---|
| `__init__.py` | 6 | 156 | Só docstring | pacote Python | KEEP, UPDATE stale documentation |
| `deterministic_test_adapter.py` | 246 | 9427 | `DeterministicTestAdapter.__init__`, `invoke`, `_structured_understanding_payload`, props `adapter_kind`/limits/exposure | `root_composer.py` teste explícito; `test_model_invocation_foundation.py`, `test_model_invocation_architecture.py` | **TEST_ONLY KEEP/SHRINK or REPLACE** with Pydantic AI TestModel *where parity proven*; not production legacy |
| `openai_compatible_transcription_adapter.py` | 297 | 10757 | `OpenAICompatibleTranscriptionAdapter.transcribe`, `stream_transcribe`, `_map_delta`, `_check_status`, `_map_body` | `root_composer.py` instancia em dictation (linhas ~620 e ~660), `SpeechTranscriptionPort` e testes de dictation | **KEEP independent STT**; refactor only proven duplicate transport/limits; avoid merging voice config with intelligence agent JSON |
| `pydantic_ai_adapter.py` | 351 | 13280 | `_structured_output_directive`, `_proposal_model`, `PydanticAiModelInvocationAdapter.invoke`, `_map_usage`, `_map_error` | `root_composer.py::_wire_real_provider_handler` (linhas ~677–711), `InvokeModel`, `test_pydantic_ai_adapter.py` (380 lines) | **PRIORITY SHRINK / NATIVE CONSOLIDATION**; possibly remove obsolete stage-call adapter only after verified consumers and migration to one native Agent, doc245 |

**TOTAL:** 4 arquivos, ~900 linhas de fonte (6+246+297+351) e 33.620 bytes informados pela API (soma dos tamanhos na listagem). Confirmar números por `wc -l` no checkout da task.

## 3. Revisão detalhada de cada arquivo

### 3.1 `pydantic_ai_adapter.py` — 351 linhas

**Real, não órfão.** Ativado no `root_composer.py` como `PydanticAiModelInvocationAdapter`, por meio de `InvokeModel(adapter)` e `ModelInvocationPort`. Não apagar abruptamente.

**Achados comprovados no código:**
- `_structured_output_directive` escreve instrução própria de `Respond ONLY with a single JSON object` e enumera `expected_fields`. A especificação do contrato pode exigir enumeração, mas o SDK já suporta `output_type`. **TARGET:** eliminar redundância de prompt quando schema nativo estrito demonstrar paridade; não mascarar campo ausente.
- `_proposal_model` faz `create_model("StageProposal", __config__=ConfigDict(extra="allow"))`, com atributos essencialmente `Any | None` e alguns opcionais para `applicable=false`. É saída pouco tipada; validação real ocorre depois em `InvokeModel`. **TARGET:** substituir por Pydantic models tipados de cada contrato realmente vigente (admission / evidence_composition / structured response); reduzir o uso de `Any` e `extra=allow` sem perder abstention, limitations, output shape e tipos. Priorizar schema existente; não criar registry de schemas.
- `invoke` instancia **um Agent por chamada** e usa `run_sync` (sem tools), com output_type baseado em required-fields; ver se o caminho ainda atende chamada legítima de admissão/composição/resposta da interação ou é etapa LLM paralela após doc245. **TARGET:** reutilizar Agent nativo, sem segundo semantic controller nem dual output pipelines; se `ModelInvocationPort` tem consumidores reais fora da investigação, manter menor adapter conforme contrato.
- Timeout absoluto: cria uma **thread daemon por invoke**, chama `worker.join(timeout)` e retorna TIMEOUT se a thread persistir. Isso impede bloqueio da thread chamada, **mas não demonstra que a inferência/HTTP na thread seja cancelada**. Possível trabalho zombie/uso de recursos, **TO_VERIFY**, não afirmar vazamento comprovado. Investigar cancelamento native/async/SDK com deadline real e lifecycle; manter fail-closed e não permitir tarefas/material writes após expiração.
- `_map_usage` utiliza `getattr(..., "input_tokens", None) or getattr(..., "request_tokens", None)`: se 0, troca por fallback; não inventar tokens, reportar números efetivos/NOT_MEASURED. Consolidar telemetria do Pydantic AI agent e model port se mesmo owner.
- `_map_error` baseia-se em nome de exceção/string e em `status_code`; preferir exceções tipadas do SDK quando realmente suportadas; preservar sanitização (sem segredos, raw body, prompts).
- `ADAPTER_KIND="OPENAI_COMPATIBLE"` identifica protocolo de modelo, apesar de ser adapter Pydantic AI. Registrar claramente diferença de runtime e transporte; não tratar como validação de autoridade. Analisar testes que dependem da nomenclatura.
- Construtor ainda possui comentário `mirrors legacy adapter`; docstring `__init__.py` diz `Real provider adapter = NONE`, ambos stale. Remover comentários/docstrings inexatos.
- Limites `default_max_output_units`, `context_window_tokens`, `timeout_seconds` já são fornecidos a partir do JSON único `pydantic_ai.runtime.delpi.json` por `Settings`/Composition (doc243). **Não criar segundo JSON nem reintroduzir variáveis de ambiente independentes**.
- `ModelSettings(timeout=..., max_tokens=...)`, source `model_impl` e history mapping são integrações reais; não excluir até confirmar testes e compatibilidade com SDK versão instalada.

**AC:** Native typed `output_type` + `output_validator` quando apropriado, schema estrito, no second controller, bounded timeouts, no thread leakage on timeout, correct usage, platform AuthZ independent, no model result becomes FACT; `InvokeModel` consumers still work.

### 3.2 `deterministic_test_adapter.py` — 246 linhas

**Uso:** `root_composer.py` usa `DeterministicTestAdapter` em composição explícita TEST_ONLY (`testing` path), test files validam negative security: secret/COT/tool calls, provider failure, lineage, epistemic class, SHA/eval boundaries. Portanto **não é rollback de produção** e não deve ser excluído sob regra de zero legacy sem substituição testável.

**Limpeza candidata:**  `_structured_understanding_payload` guarda payloads codificados de domínio `c3t4.` (status máquina fictícia); outros branches `behavior` scriptados por case e string. Validar se esses testes correspondem a contratos ainda existentes; substituir onde possível por Pydantic AI `TestModel`, `FunctionModel` ou fixtures tipadas existentes **sem perder a prova de negações e de falha segura**. Não manter simulações específicas de engine aposentada nem permitir `TEST_ONLY` em runtime real. Versões do SDK e assinatura real devem ser inspecionadas.

**Decisão:** KEEP/SHRINK (ou DELETE após migração dos consumidores de teste), não TARGET delete antes da prova.

### 3.3 `openai_compatible_transcription_adapter.py` — 297 linhas

**Uso:** `root_composer.py` cria `OpenAICompatibleTranscriptionAdapter` para `SpeechTranscriptionPort` e incremental dictation. Isso é **áudio→texto**, não segunda inteligência conversacional. Testes `test_dictation_transcription.py` (~490 linhas) e `test_incremental_dictation.py` (~463 linhas) validam auth, formato, payload, SSE, errors/NDJSON.

**Achados concretos:**
- `transcribe` usa `bounded_request` e provider `/chat/completions` com `input_audio`, modelo STT próprio e `temperature=0`, `max_tokens=2048`, `stream=False`.
- `stream_transcribe` usa **`requests.post` diretamente** com `timeout=(min(10,timeout), timeout)` e checagem de relógio durante `iter_lines` para stream; diferente do caminho bounded `transcribe`. **TO_VERIFY** deadline total no cenário de stream lento/trickle: o timeout de leitura se reinicia e o check somente executa quando chegam lines. Testar comportamento com stream sem novas linhas.
- `max_tokens=2048` aparece duplicado nos dois paths. É parâmetro STT, **não migrar cegamente ao JSON único de tuning do Pydantic AI**, cuja fonte é exclusiva de inteligência agentiva; centralizar no owner de dictation config se policy exigir ajustável, ou manter como teto fixo intencional justificado. Eliminar duplicação entre streaming e non-streaming sem criar outra config de IA.
- `_TRANSCRIPTION_INSTRUCTION` constante produz transcrição verbatim pt-BR; não há evidência de substituição nativa sem regressões. Validar provider audio behavior, MIME, fail closed, no raw audio/credentials logged.

**Decisão:** KEEP e reduzir duplicação real; Pydantic AI native speech/transcription reuse somente após equivalência comprovada no provider real, não pressupor.

### 3.4 `__init__.py` — 6 linhas

Docstring stale `Real provider adapter = NONE`. Atualizar para especificar `PydanticAiModelInvocationAdapter` nativo, `DeterministicTestAdapter` TEST_ONLY e transcrição como boundary separada. Nenhum code path a excluir.

## 4. Visão de consumidores e fluxos

```text
root_composer
 ├─ normal text interaction → PydanticAiModelInvocationAdapter
 │    → ModelInvocationPort → InvokeModel → HandleInteractiveConversationTurn
 ├─ PydanticAiInvestigationOrchestrator (separate native Agent tool loop)
 │    → Application governed gates → owners / Evidence
 ├─ explicit tests → DeterministicTestAdapter (TEST_ONLY, denied in production)
 └─ dictation routes → SpeechTranscriptionPort → OpenAICompatibleTranscriptionAdapter
      ├─ transcribe (bounded sync)
      └─ stream_transcribe (SSE incremental)
```

`ModelInvocationPort` ainda atende Application genérica, que pode ser legado conversacional ou contrato legítimo para admissão e resposta. **Decisão de coordenação requerida após consumer tracing:** evitar duas composições semânticas concorrentes (Agent normal e interaction fallback), mas não cortar respostas gerais nem segurança sem testes. `PydanticAiModelInvocationAdapter` é Pydantic AI, não engine antiga; coexistência de duas invocações Agent não prova sozinha duplicação semântica. Auditar efetiva árvore de chamadas.

**Contrato externo que não pertence ao JSON do Agent:** dictation/STT pode possuir limites, endpoints, modelo e segurança próprios. Não trazer áudio, segredos, user data nem bearer para `pydantic_ai.runtime.delpi.json`.

## 5. Evidência e limites

**PROVEN:** todos os 4 arquivos lidos integralmente; composição `root_composer.py` importa e usa os três adapters conforme contexto; `Settings` lê JSON `pydantic_ai.runtime.delpi.json`; testes importam adapters; antigo runtime de modelo foi fisicamente retirado da pasta; código manual da `_proposal_model`, `_structured_output_directive` e daemon-thread existe; STT tem dois caminhos HTTP; `__init__.py` está stale.

**TO_INVENTORY:** callgraph total de `ModelInvocationPort` e consumo do handler genérico em produção, reconciliação com doc245/246, uso de API Pydantic AI TestModel/FunctionModel versão instalada, contratos canon/fase/ledger, comprovante de cancelamento real de threads e SSE, resultados do runtime local.

**TEST_NOT_RUN:** suite, E01–E10, dictation STT real, source edit. Documentação não prova runtime.

## 6. Sequência executável (implementação bounded e sem 'nova auditoria infinita')

1. Reancorar HEAD/status/authorities/ledger + docs239–249, confirmar SHA e demandas de remoção doc245/246.
2. `rg` e AST dos consumers de `ModelInvocationPort`, `InvokeModel`, `PydanticAiModelInvocationAdapter`, generic-handler vs native Agent, TestAdapter, TranscriptionAdapter; classificar effective path vs test-only/dormant.
3. RED testes para conformidade `output_type` tipado / validator, abstention, missing/extras, prompt injection, malformed structured, provider errors, deadline cancel e usage; regressões ditado/stream/exposure; zero FACT modelo.
4. Refatorar o adapter native: reduzir schema dinâmico `Any/extra=allow` e prompt duplicado onde contratos Pydantic tipados existentes bastem; remover docstrings legadas; preservar ModelInvocationPort somente com consumidor real. Não introduzir outro stage planner/response engine.
5. Remover daemon-timeout que retorne sem cancelar a inferência **somente quando alternativa native comprovadamente satisfizer deadline total**; caso contrário registrar risco e gate de hardening, não degradar segurança.
6. Consolidar TEST_ONLY em fixtures nativas se os negativos continuarem provados; não apagar testes legítimos. Evitar semântica de produto/máquina fixa no runtime.
7. Revisar streaming STT com testes lentos/silenciosos; deduplicar payload/limites e garantir cancelamento/timeouts, sem forçar STT na configuração Pydantic AI.
8. Executar full backend tests final SHA, architecture isolation, dictation/NDJSON, JSON config profile, no inference fallback, native agent E01–E10 em runtime local reconstruído se possível.
9. Documentar alterações, destino de cada arquivo, linhas antes/depois, valores reais de config usados, testes, model/usage, gaps, SHA; atualizar docs 239/243/245/246/249, ledger e relatório de execução no próximo número disponível. Commit/rebase/push main preservando WIP; sem production deploy.

## 7. Veredito

| Arquivo | Veredito |
|---|---|
| `pydantic_ai_adapter.py` | **PRIORITY SHRINK / EXTEND native typed output**, nenhuma remoção integral automática enquanto `InvokeModel` consumer existir |
| `deterministic_test_adapter.py` | **TEST_ONLY; KEEP/SHRINK**, candidato a migrar para Pydantic TestModel depois de parity |
| `openai_compatible_transcription_adapter.py` | **KEEP LEGITIMATE STT**, corrigir riscos de timeout SSE e payloads duplicados |
| `__init__.py` | **KEEP + corrigir docstring** |

**No code changed, no tests run, no production deploy.**
