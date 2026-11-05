# 254 — DÉLIA · Auditoria integral de application/ports e consolidação contratual

**TASK_ID:** DELIA-C3-APPLICATION-PORTS-FILE-BY-FILE-AUDIT-AND-CONTRACT-CONSOLIDATION-01  
**DATE:** 2026-11-05  
**AUDITED_HEAD:** `91a462210319b8cc1cd93f8085c5e39d7e4dcb26`  
**SCOPE:** `delia-api/app/application/ports/` — 5/5 arquivos lidos integralmente via GitHub na mesma revisão  
**STATUS:** AUDIT / PLANNED; CODE_NOT_CHANGED; TEST_NOT_RUN; PRODUCTION_DEPLOY=NOT_AUTHORIZED  
**RELATED:** docs 239–253, especialmente 245, 248, 249, 252, 253; authorities e ledger.

## 1. Diagnóstico

Esta pasta contém **quatro ports concretamente justificados por consumers existentes**, além de `__init__.py`. Não é legado removível em bloco: os contratos protegem as fronteiras Application/Infrastructure e impedem que Domain/Application conheçam SDKs, HTTP, Keycloak, MCP ou provider audio. O tamanho aproximado é 178 linhas de texto extraído (4+57+25+56+36), portanto o objetivo é corrigir gaps de contrato e **não** reduzir linhas artificialmente.

**EXISTING_EQUIVALENT:** YES para `ModelInvocationPort`, `PlatformAccessPort`, `SpecialistInteropPort`, `SpeechTranscriptionPort`, adapters existentes e contracts DTO. TO_INVENTORY para o consumidor da interface de acesso à plataforma em todos os pontos da composição e para tipos de streaming já existentes em outro bounded context.  
**REUSE_DECISION:** REUSE/EXTEND os ports atuais, nunca NEW ou segundo port por conveniência. Eliminar interface somente quando não houver consumer legítimo após refactor aprovado.

**Limite da evidência:** HEAD consultado e todos os cinco arquivos lidos integralmente. Foram inspecionados consumidores selecionados (`InvokeModel`, `SpecialistInterop`, `CorePlatformAccessAdapter`, `TranscribeDictation`, `IncrementalDictationService`, transcrição Infrastructure, composition/test paths). Esta tarefa não executou git status local, reancoragem integral das authorities, AST/rg global, testes ou produção. O executor deve reancorar HEAD/status → Project Instructions/.cursor → docs 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → spec temática → ledger.

## 2. Matriz de todos os arquivos

| Arquivo | Linhas GitHub | Responsabilidade comprovada | Consumo/implementação | Decisão |
|---|---:|---|---|---|
| `__init__.py` | 4 | marcador do pacote | imports dos ports | KEEP |
| `model_invocation_port.py` | 57 | `ModelInvocationPort`: `adapter_kind`, `exposure_class`, `context_window_tokens`, `default_max_output_units`, `invoke` | `InvokeModel` Application; `PydanticAiModelInvocationAdapter` Infrastructure; `DeterministicTestAdapter` TEST_ONLY | **KEEP/SHRINK** condicionado a docs245/249/253; rever propriedades e docstrings com premissas antigas |
| `platform_access_port.py` | 25 | `PlatformAccessPort.resolve` + `AuthenticationError`, `AuthorityUnavailableError` | `CorePlatformAccessAdapter.resolve`, camada HTTP/middleware | **KEEP**, Core é autoridade efetiva; exceções e port não são provider metadata |
| `specialist_interop_port.py` | 56 | `SpecialistInteropPort.list_remote_tools/call_remote_tool`, `adapter_kind` | `SpecialistInterop`, `McpSpecialistAdapter`; `SnapshotDiscoverInterop` usa base interop | **KEEP** boundary governado MCP/A2A, conferir versão de texto e write gates |
| `speech_transcription_port.py` | 36 | `SpeechTranscriptionRequest`, `SpeechTranscriptionPort.transcribe`, `adapter_kind` | `TranscribeDictation`, `OpenAICompatibleTranscriptionAdapter`; incremental `IncrementalDictationService` usa `stream_transcribe` em `port` não tipado | **EXTEND existing contract** para streaming incremental ou reutilizar interface tipada já existente, sem duplicação |

**TOTAL:** ~178 linhas (contagem textual inclui linha final). Verificar `wc -l` no worktree.

## 3. Observações funcionais e mudanças mínimas

### 3.1 ModelInvocationPort — 57 linhas

**PROVEN:** `InvokeModel` recebe o port; `root_composer.py` injeta `PydanticAiModelInvocationAdapter`, teste explícito usa `DeterministicTestAdapter`. O port não tem conhecimento de Pydantic AI: mantém Application provider-neutral. Duas properties opcionais têm defaults `return None` no Protocol, hoje usadas por `context_budget` para janela efetiva e reserva de output. Não são necessariamente duplicação inútil. `adapter_kind` e `exposure_class` têm gate de Application (`InvokeModel._enforce_exposure_policy`); mantenha autorização de provider, não promova metadata do modelo a policy.

**Cleanup:** docstrings `TEST_ONLY until gate PROVEN` e `future approved provider kind` estão desatualizadas porque Pydantic AI já é composto em runtime real; alinhar a status factual. Após docs245/249/253, inventariar se o `ModelInvocationPort` permanece necessário para chamadas conversacionais/stage. Se as chamadas forem absorvidas por Agent nativo sem duplicação semântica, encolher interface/converter consumers sem deixar adapter paralelo morto. **Não remover uma interface com consumer ativo para colocar Pydantic AI SDK na Application.** Verificar `context_window_tokens` e `default_max_output_units` após native usage/budget changes.

### 3.2 PlatformAccessPort — 25 linhas

`resolve(bearer_token)` obtém `PlatformAccessContext` Core-backed, e as duas exceções são tipos semânticos. `CorePlatformAccessAdapter` fornece `resolve`, valida token com validador compartilhado e consulta `Core /me`. **KEEP**: nem JWT claims, nem model, nem frontend state conferem RBAC. Verificar que middleware/injeção dependam do Protocol no boundary correto, não da implementação Infrastructure, e que AuthN/AuthZ falhem fechados quando Core indisponível. Se revisão mostrar um segundo contrato idêntico, escolher owner canônico e eliminar o duplicado, não construir novo.

### 3.3 SpecialistInteropPort — 56 linhas

Port legitimo para `list_remote_tools` e `call_remote_tool`, implementado por `McpSpecialistAdapter` e consumido por `SpecialistInterop`. `RemoteToolDescriptor` é não confiável, operação tipada não é permissão. `call_remote_tool` é governado: confirmação PREPARE/ACT, Core/domain AuthZ e postcondition continuam fora do MCP metadata. **KEEP**, atualize docstring com especialistas atuais e sem supor DAVI/TÉO/VISTA exclusivos; esse contrato se mantém provider-neutral e pode receber A2A se houver owner/capability aprovado. Não acoplar SDK MCP/A2A ao Protocol. Auditar duplicação com `capability_provision/ports.py` por **responsabilidade**, não por assinatura superficial: provider catalog e specialist tool transport são boundaries diferentes a princípio.

### 3.4 SpeechTranscriptionPort — 36 linhas

**GAP PROVEN:** port declara somente `transcribe(request) -> str`, enquanto `IncrementalDictationService` define `port` sem annotation e chama `self._port.stream_transcribe(request)` (linha ~338). `OpenAICompatibleTranscriptionAdapter` implementa ambos `transcribe` e `stream_transcribe`. Existe feature incremental com consumidores e testes. Isso não é bug runtime comprovado, mas **incompletude de contrato estático**: o uso de stream não está representado em interface tipada da Application, podendo escapar a type checking e substituição por outro adapter.

**TARGET:** reusar `SpeechTranscriptionPort` e, após inventário de consumidor, optar por: (a) estender port com `stream_transcribe` caso todo provider suportado deva implementar ambos; ou (b) introduzir um Protocol pequeno **apenas se** o boundary streaming for realmente independente e já aprovado, preferindo interface existente; considerar capacidade opcional explícita com type gate fail-closed. Anotar `IncrementalDictationService.port`, preservar `SpeechTranscriptionRequest` (audio_bytes, provider_format, language_hint, timeout_hint_ms) e contrato de texto **untrusted**, SSE incremental, timeout/cancel. **Não criar novo serviço/engine nem fazer Application depender de SDK**. Evitar `@runtime_checkable` sem benefício concreto.

### 3.5 __init__.py — 4 linhas

KEEP, não justifica alterações materiais.

## 4. Dependências e risco de remoção

```text
InvokeModel                         → ModelInvocationPort → PydanticAiModelInvocationAdapter / TestAdapter
HTTP middleware / Core adapter      → PlatformAccessPort → CorePlatformAccessAdapter
SpecialistInterop                   → SpecialistInteropPort → McpSpecialistAdapter
TranscribeDictation                 → SpeechTranscriptionPort → OpenAICompatibleTranscriptionAdapter.transcribe
IncrementalDictationService         → untyped port.stream_transcribe → same infrastructure adapter
```

Não misturar `SpeechTranscriptionPort` com `ModelInvocationPort`: texto transcrito é entrada não confiável, não resposta factual do Agent. Não misturar `PlatformAccessPort` com provider metadata. A redução da orquestração nos docs245/246 não autoriza eliminar gates de interop/autorização.

## 5. Plano de implementação e testes

1. Reanchor fully current HEAD/status/authorities/ledger; compare docs 245–253 and check drift.
2. `rg`/AST total consumers of 4 Protocols and all adapters; classificar ACTIVE/TEST_ONLY/OBSOLETE. Confirm absence of duplicate ports before edit.
3. RED testes: `IncrementalDictationService` com port tipado, contract/static typecheck, stream partial/final/cancel/error, wrong implementation rejected; tests for Core failure, no JWT AuthZ, model output no FACT, MCP unknown tool/metadata not permission, PREPARE/ACT gates.
4. Minimal diff: repair speech streaming contract via existing interface, fix stale docstrings; no changes to SDK boundary. If further redundancy verified, shrink only after consumers migrated and tests.
5. Tests focus: typing, `test_dictation_transcription.py`, `test_incremental_dictation.py`, `test_platform_access.py`, `test_mcp_adapter.py`, `test_model_invocation_foundation.py` and architecture. Full backend suite, real native Agent eval E01–E10 if relevant, NDJSON, security negatives.
6. Residual search; record before/after LOC, SHA, evaluated config, test/eval statuses and any architecture decision requirement. Update docs 249/252/253/254 and ledger; commit/rebase/push main; no production deploy.

## 6. Veredito

**PROVEN:** 5/5 source files read on same SHA, ports are real canonical Application boundaries, consumers/implementations inspected; `stream_transcribe` is called on a dynamically typed port but absent from `SpeechTranscriptionPort`.  
**TO_INVENTORY:** full repo consumer callgraph and alternative interface types, canon/ledger, typed static regression, runtime/eval status, middleware injection patterns.  
**TEST_NOT_RUN:** no source changes or automated tests were run during audit.  

**Recommendation:** **KEEP all four ports**, **EXTEND existing SpeechTranscriptionPort or reuse a currently approved streaming port**, update stale model-interoperability documentation, only shrink if consumer migration justifies.
