# 264 — DÉLIA · Revisão independente G5 e handoff G6 HTTP/STT

**DATA:** 2026-11-05  
**TASK_ID:** `DELIA-C3-G5-MCP-OPENAPI-SNAPSHOT-BOUNDARY-CLEANUP-01`  
**BASE_SHA:** `cb9668c2cfaca0c8ea438b428762156913c0c80e`  
**REVIEWED_SHA:** `9596570a8a46736b671ea4903d72105a2f935d0b`  
**VEREDITO:** **ACCEPT_WITH_RESIDUAL** (fix de boundary; G7 integration pendente).  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED. **E01–E10:** TEST_NOT_RUN.

## Evidências conferidas no GitHub

- Um commit DÉLIA com `app/application/specialist_interop/snapshot_interop.py` +124/-109, `app/composition/root_composer.py` +4/-1, `tests/test_mcp_catalog_experiment.py` +169/-166; atualizações do doc256 e ledger.
- Application deixou de importar `app.infrastructure.interoperability.mcp.catalog_store`. `_SnapshotCatalogStore(Protocol)` expõe somente `active(owner_id, scope)`; `contract_hash` é injetado, com as dependências concretas construídas pelo composition root. `SnapshotDiscoverInterop` mantém override de `_remote_tools` e não sobrescreve `invoke`, que permanece no fluxo live governado.
- Snapshot ausente/hash divergente falha fechado com `SpecialistInteropError(MCP_UNAVAILABLE)`. Metadados de ferramentas são reconstruídos em `RemoteToolDescriptor`, não dão permissão de execução.
- Os 9 testes de `test_mcp_catalog_experiment.py` cobrem store version/rollback, INVALID, idempotência, diff schema, serve, missing/tampered, equivalência de projeção e payload injection. Executor reportou 9/9 PASS e suíte backend PASS; reviewer **não executou testes**.
- `openapi_provider.py` e foundation de `infrastructure/openapi` não mudaram neste commit, coerente com decisão C3-T5 aprovada. Executor relata 46/46 testes OpenAPI; não reexecutados.
- Os componentes MCP live, transport e delegation não foram modificados nesta task. Isto não prova behavior do MCP deployado, mas preserva caminhos por diff.
- Snapshot **aprovado/deployado**, persistência `/data/delia/mcp_catalog.db` e redução de discovery ~11s→~0ms são **executor-reported**, não revalidados por reviewer em runtime/infra; classificar como evidência reportada, não PROVEN por este review.
- Source review não encontra razão para apagar capacidade congelada C3-T5 ou snapshot experimental aprovado. `EXISTING_EQUIVALENT=YES`, `REUSE_DECISION=KEEP+FIX_BOUNDARY`.

## Residuais e aceitação

1. G7: fluxo real end-to-end com owner MCP, autorização live, mudança de tool class, metadata untrusted, provable Owner Outcome, SourceRefs e performance antes/depois; testes de snapshot A/B no ambiente homologado.
2. A assinatura de `_SnapshotCatalogStore.active` retorna `Mapping|None` não estritamente tipado. Evitar refatoração especulativa; se houver bug de payload/keys observável, validar boundary fail-closed com testes e contrato existente.
3. Não considerar sucesso de discovery por snapshot uma autorização ou um business outcome. Não mudar frozen decisions sem `ARCHITECTURE_DECISION_REQUIRED`.
4. E01–E10 real model = TEST_NOT_RUN e deploy de produção não autorizado neste plano de limpeza.

## Próxima task concreta: G6

**TASK_ID:** `DELIA-C3-G6-HTTP-DEADLINE-AND-INCREMENTAL-STT-BOUNDED-TRANSPORT-01`.

Reancorar git HEAD/status/origin + Project Instructions/.cursor → autoridades 16→50→17→49→51→52→21→20→25 → técnica/produto/spec voice/MCP → ledger → docs251/254/256/264. Não repetir inventário global.

**Escopo:** `infrastructure/http/{bounded_request,deadline_transport,dns_resolver}.py`, `infrastructure/model_invocation/openai_compatible_transcription_adapter.py`, `application/ports/speech_transcription_port.py`, root wiring e testes existentes. KEEP transport autorizado que governa DNS/TCP/TLS/headers/body deadline absoluto, sem troca por mero timeout de inatividade; STT streaming incremental é um caminho conhecido com `requests.post` direto a caracterizar e corrigir se bypass confirmado. Reutilizar infraestrutura real com smallest diff, sem segundo HTTP engine, sem nova abstraction especulativa.

1. Isolar caminho incremental real STT e os limites de stream, tamanho, autenticação/secret, disconnect/cancel, deadline e comportamento de POST. Criar testes RED para bypass ou timeout que não limita corpo/stream, SSE partial, limites de bytes, cancelamento, autenticação e log privacy.
2. Aplicar smallest fix através do transporte governado/adapters existentes; se transporte atual não suporta streaming e contrato verdadeiro exige uma extensão, provar necessidade/owner/consumer antes de EXTEND. Não prejudicar downloads de voz nem inferência de modelo de texto; não pôr configuração STT no JSON único de inteligência.
3. Revalidar explicitamente que `SpeechTranscriptionPort` segue legitimo e que credenciais não passam para prompt, context, logs ou NDJSON de conteúdo indevido; preservar redaction, bounded buffering e fail-closed.
4. Executar testes focados RED→GREEN e suíte backend/arquitetura/segurança, residual search e testes de conexão com owner quando ambiente estiver disponível; não afirmar produção PASS sem outcome.
5. Registrar paths/linhas modificadas, LOC, tracing, retry/deadline físico, SHA/model/config, CI/testes, gaps e CP/RQ de G6. Commit/push, docs/ledger somente após evidência. **NO PRODUCTION DEPLOY**.

**G7 carryover:** end-to-end PydanticAiInvestigationEngine native retries/usage, E01–E10, snapshot live, OpenAPI fixture and owner SourceRef evidence, authorized security/Outcome. **G8:** residual and independent final review.

**STATUS:** Esta revisão alterou somente documentação no GitHub; não executou testes nem alterou código de runtime.
