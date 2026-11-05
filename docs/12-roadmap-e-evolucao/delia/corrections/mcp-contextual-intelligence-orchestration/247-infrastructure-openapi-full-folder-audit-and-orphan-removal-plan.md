# 247 — DÉLIA · Auditoria integral de app/infrastructure/openapi e decisão de remoção

**TASK_ID:** `DELIA-C3-INFRASTRUCTURE-OPENAPI-FULL-FOLDER-AUDIT-AND-ORPHAN-CLEANUP-01`  
**DATA:** 2026-11-05  
**HEAD INSPECIONADO:** `cfa6e939e35539516b7d8d211d22bce22dc1792d`  
**STATUS:** AUDIT / PLANNED / CODE NOT CHANGED  
**ESCOPO:** `delia-api/app/infrastructure/openapi/` — 3/3 arquivos completos lidos no mesmo SHA; consumidores selecionados inspecionados  
**DOCUMENTOS CORRELATOS:** 239, 241–246, ledger e decisão `DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-01` já citada no código  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## 1. Diagnóstico novo e importante

**A integração OpenAPI direta com DELPI já foi explicitamente retirada da composição do runtime.** O `root_composer.py` atual, linhas ~383–401, constrói `McpCapabilityProvider` a partir de specialist connections habilitadas e declara: domínio DELPI chega à DÉLIA exclusivamente por DAVI/MCP, não por binding OpenAPI direto. `settings.py`, linhas ~289–317, documenta remoção de variáveis e source-binding OpenAPI, incluindo `DELIA_OPENAPI_TIMEOUT_SECONDS`; seu ramo de configuração não compõe OpenAPI.

**Portanto, este diretório OpenAPI parece ser infraestrutura residual sem wiring de produção na composição examinada**. Isso é mais relevante que o tamanho. O serviço de código vivo `app/application/capability_provision/openapi_provider.py` (248 linhas) também parece não ser composto. **Não declarar UNUSED global sem busca residual completa em repo/scripts/test/dynamic import, e sem conferir decisões canônicas**. Testes ainda importam e exercitam parte da infraestrutura — não são prova de uso produtivo.

**EXISTING_EQUIVALENT:** YES para o caminho autorizado de domínio DELPI via DAVI/MCP + SpecialistInterop; TO_INVENTORY para usuários OpenAPI externos legítimos e plano cross-provider canônico. **REUSE_DECISION:** REUSE DAVI/MCP; DELETE código OpenAPI se não houver outro consumer/contrato ativo; KEEP only demonstrated independent legitimate owner, not speculative future integrations. Do not automatically replace an inactive OpenAPI adapter with a new generic loader.

## 2. Matriz arquivo a arquivo

| Arquivo | Tamanho | Linhas API | Funções e classes | Uso / contrato real | Decisão |
|---|---:|---:|---|---|---|
| `capability_catalog_adapter.py` | 13.765 B | 333 | `CapabilityDeclaration`, `ProjectionRejection`, `OpenApiCatalogProjection`, `project_openapi_document`; 7 parser helpers | Projeção de operações OpenAPI para `CapabilityProjection`; semantic declaration obrigatória, operação não concede AuthZ. Consumido por `source_loader`; testes `test_capability_catalog_foundation.py` e `test_openapi_capability_provider.py` | **CANDIDATE DELETE**, se nenhum adapter/runtime canônico o consumir; domínio `CapabilityProjection` não deve ser excluído só porque este adapter foi |
| `http_invoker.py` | 11.412 B | 329 | `fetch_openapi_document`, `HttpOpenApiInvoker.__call__`, `_owner_not_found_hint`, `_owner_recoverable_rejection_hint`, `_now_utc` | Busca `/openapi.json`, GET-only, bearer sujeito efêmero, timeout e envelope de owner; consumido por `source_loader` e teste `test_openapi_capability_provider.py` | **CANDIDATE DELETE**, se sem runtime legítimo; não apagar governança MCP/DAVI por similaridade |
| `source_loader.py` | 6.439 B | 192 | `load_declarations`, `build_openapi_source`, closure `projector` | Lê declarations JSON e produz `OpenApiCapabilitySource`, composto pelos dois outros módulos; **não encontrei wiring em root_composer atual** | **PRIORITY DELETE CANDIDATE** após search de todos os callers e canon/ledger; sem consumer legítimo não manter loader para integração especulativa |

**TOTAL:** 854 linhas por API e aproximadamente 31.616 bytes informados pela listagem; medir `wc -l` no checkout do executor para base final.

## 3. Auditoria por função

### 3.1 capability_catalog_adapter.py (333 linhas)

- `CapabilityDeclaration.__post_init__`: identidade semântica declarada, operation_id e operation_character — não é decisão semântica do LLM; protege contra heurística de URL/verbo.
- `ProjectionRejection`, `OpenApiCatalogProjection.grants_authorization=False`: boa proteção conceitual mas sem consumer ativo é código residual.
- `project_openapi_document`: projeta contratos HTTP e falha fechada para missing/duplicate operationId, missing declaration, schema/security unsupported; depende exclusivamente de semantic declarations. Não executa operação nem resolve permissão.
- `_source_contract_ref`, `_declaration_map`, `_iter_operations`, `_input_descriptors`, `_response_descriptors`, `_response_schema_identity`, `_schema_identity`, `_security_descriptors`: parser/conversor proprietário de OpenAPI. Verificar se a capacidade nativa do Pydantic AI ou adapter existente cobre realmente este contrato **somente se houver consumer aprovado**. Não inferir autorização ou operação de path/method.
- **TARGET:** se a integração foi legitimamente aposentada, delete parser inteiro e seus testes de implementação, mantendo testes transversais de segurança/arquitetura que preservem o mesmo contrato nos consumidores ainda ativos. Não preservar `OpenApiCatalogProjection` apenas para facilitar teste morto.

### 3.2 http_invoker.py (329 linhas)

- `fetch_openapi_document`: GET de `/openapi.json`; `bounded_request` e exceções projetadas como source unavailable, não catálogo vazio. Verificar se existe consumer externo à pasta (e.g. health checks, scripts, tests).
- `HttpOpenApiInvoker`: GET-only, bearer por request, argumentos path/query declarados e response `SpecialistOutcome`; **não é LLM planner** nem duplicação semântica Pydantic AI, mas execução técnica potencialmente sem consumer.
- `_owner_not_found_hint` e `_owner_recoverable_rejection_hint`: parser local de erros do owner; comparar com contrato genérico `SpecialistInterop` de erro. Se o adapter inteiro for removido, remover handlers. Se retido por owner legítimo, consolidar respostas sem quebrar typed error semantics.
- **Pontos para verificar antes de qualquer preservação/reescrita:** `MAX_OPENAPI_RESPONSE_CHARS=64000`, fetch timeout=10s, call timeout=15s, path params substituídos com `str()` sem percent-encoding de segmento, response text truncado enquanto `structured=response.json()` é integral, GET path construído por concatenação, mapeamento de 401/403 para códigos `mcp_*` em adapter HTTP. Esses são **candidate risks / TO_VERIFY**, não incidentes provados; se adapter for realmente morto, excluir evita manter superfície técnica desnecessária. Se retido, exigir testes URL encoding/path injection, bounded structured payload, timeout, error taxonomy e bearer privacy.
- **TARGET:** excluir junto com loader órfão; não substituir desnecessariamente por outro HTTP invoker.

### 3.3 source_loader.py (192 linhas)

- `load_declarations`: parse de arquivo JSON governado com whitelist de campos, até 64 declarações. Verificar duplicação com config loaders e contratos existentes.
- `build_openapi_source`: devolve `None` em config ausente, realiza log de erro e monta source com projector live + GET invoker.
- `projector`: timeout limitado e `project_openapi_document`, sem gerar novo owner authority.
- **TARGET:** se nenhum consumer no runtime, deletar integralmente em vez de deixar wiring desconectado. Se houver consumer legítimo não contemplado em root_composer, reavaliar owner/contract antes de decidir.
- Atenção: omissão de declarations quando acima de MAX_DECLARATIONS é truncamento silencioso; risco contratual se usar uma fonte real. Preferir fail-closed ou explicit partial status; não alterar se arquivo será removido.

## 4. Consumidores e evidências — PROVEN versus TO_INVENTORY

**PROVEN:**
- `root_composer.py` linhas ~383–401: compõe somente `McpCapabilityProvider`, declara explicitamente direct DELPI OpenAPI removed.
- `settings.py` linhas ~290–317: flags de source OpenAPI DELPI removidas; nenhuma source composta por settings.
- `source_loader.py` importa `capability_catalog_adapter.py` e `http_invoker.py`.
- `test_capability_catalog_foundation.py` importa `capability_catalog_adapter.py`; 13 testes de capability projection.
- `test_openapi_capability_provider.py` (~934 linhas) importa `openapi_provider.py`, `capability_catalog_adapter.py`, `http_invoker.py`, cobrindo invocação GET, bearer, error envelope, denied, timeout, no direct DELPI wiring. Testes finais (~892–934) confirmam intencionalmente ausência do binding direto. `source_loader.py` não apareceu como import explícito nesse teste.
- `test_capability_catalog_architecture.py` testa invariantes de domínio, não demanda necessariamente o adapter OpenAPI concreto.
- Recursive Git tree não truncada (`truncated=false`) mostra os 3 arquivos, `app/application/capability_provision/openapi_provider.py` e testes relacionados. Isso **não é callgraph**.
- Busca GitHub `search` retornou 0 para `build_openapi_source`, `project_openapi_document`, `HttpOpenApiInvoker`; por contrato **0 results != ausência**.

**TO_INVENTORY:**
- Toda a árvore repo, imports dinâmicos, testes adicionais, comandos, scripts de CI e jobs; confirmar com `rg -n` e AST no checkout, incluindo referências à classe `OpenApiCapabilitySource`, contratos em docs, configs e DLCs.
- Se OpenAPI permanece previsto por decisão canônica para outros owners que não DELPI, remover agora pode ser drift. Verificar docs 16→50→17→49→51→52→21→20→25, spec, ledger antes de implementação.

## 5. Decisão prática e sequência da limpeza

1. Reanchor git status/HEAD/origin e authorities em ordem; verificar `DELIA-C3-REMOVE-DIRECT-DELPI-BOUNDARY-01`, docs 239–247 e ledger.
2. Provar no código real todas as referências a `app.infrastructure.openapi.*`, `OpenApiCapabilityProvider`, `OpenApiCapabilitySource`, `CapabilityDeclaration`, `project_openapi_document`, `build_openapi_source`, `HttpOpenApiInvoker` e envs/config OpenAPI; incluir `rg` e AST e eventuais imports dinâmicos.
3. Se a integração OpenAPI está de fato sem consumer runtime e nenhum owner/capability aprovado depende dela, **remover os 3 arquivos e a pasta**. Verificar também `app/application/capability_provision/openapi_provider.py`: provável quarto arquivo relacionado candidato a exclusão (fora do diretório solicitado). Não deixar adapter paralelo inativo só para uso futuro.
4. Ajustar imports, wiring, dependências, infra/env, testes antigos. Preservar testes universais de contract/auth/provenance em paths reais MCP/DAVI. Não deletar testes que protegem invariantes ainda necessários apenas por importarem OpenAPI.
5. Se houver integração legítima e documentada, manter o menor adapter real possível, sem generic new services. Corrigir riscos de path/content/error/timeouts e documentar `EXISTING_EQUIVALENT`/owner/consumers. **Não** criar API direta para DELPI em contradição com decisão anterior.
6. Run full backend tests at SHA final, interface/security tests, import graph, architecture-boundary tests, real Pydantic AI tool catalog READ/DAVI MCP and E01–E10 at local rebuilt runtime. Reports: PASS|FAIL|TEST_NOT_RUN; no HTTP200 as business Outcome.
7. Residual search, updates docs 239/246/247, ledger and next numbered execution report. Commit/rebase/push main preserving WIP. No production deployment.

**Acceptance:** closed idle OpenAPI integration either physically removed (proven no owner) or explicitly retained with owner+active contract+coverage. No parallel capability authority. All live readings use approved MCP/Domain interop, Core AuthZ live, provenance. Tests verified against evaluated SHA. No speculative adapter retention.

## 6. Review verdict

- **PROVEN:** all 3 files read end-to-end, function inventory, intra-package dependencies, direct DELPI OpenAPI composition removed in current root, historical tests exist.
- **STRONG CANDIDATE DELETE:** all 3 files + `app/application/capability_provision/openapi_provider.py` because direct source is not composed and no other runtime consumer was found in inspected paths.
- **TO_INVENTORY:** independent consumers or frozen cross-provider OpenAPI decision outside inspected paths; dynamic import and full-callgraph.
- **TEST_NOT_RUN:** no local checkout execution or QA performed.
- **NOT IMPLEMENTED:** documentation-only; no source was removed.
