# 248 — DÉLIA · Auditoria integral de infrastructure/interoperability + MCP

**TASK_ID:** DELIA-C3-INFRASTRUCTURE-INTEROPERABILITY-MCP-FULL-FOLDER-AUDIT-AND-CLEANUP-01  
**DATA:** 2026-11-05  
**HEAD AUDITADO:** `eb1859de12cf68bed6d4fd7458e32858eaaf164b`  
**STATUS:** AUDIT / PLANNED, NÃO IMPLEMENTADO  
**ESCOPO:** `delia-api/app/infrastructure/interoperability/` (inclui `mcp/`) — **7/7 arquivos** lidos integralmente da mesma revisão GitHub  
**CORRELATOS:** docs 239–247, decisão canônica MCP/interop e ledger  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED

## 1. Diagnóstico principal e reancoragem

Diferentemente de `infrastructure/openapi` (doc247), **esta infraestrutura MCP é efetivamente composta no runtime**: `app/composition/root_composer.py` importa `specialist_connections_from_settings`, `KeycloakDelegatedCredentialProvider` e `McpSpecialistAdapter`, os instancia e injeta em `SpecialistInterop`. O `McpSpecialistAdapter` usa `DelpiMcpTransport` como transporte real. Portanto **não classificar os arquivos principais como legados, órfãos ou removíveis por tamanho**. A remoção integral desse pacote quebraria autenticação delegada e READ real dos owners.

A auditoria foi feita por GitHub API. A leitura das autoridades canônicas 16→50→17→49→51→52→21→20→25, git status local, testes e consumers dinâmicos não foram executados nesta sessão. Antes de qualquer diff reancorar na ordem obrigatória e confirmar fase/CP/RQ, decisões congeladas e SHA. Busca vazia não prova ausência de consumidores.

**EXISTING_EQUIVALENT:** YES para Keycloak/SSO, SpecialistInteropPort, autenticação delegada RFC 8693, transporte MCP existente; TO_INVENTORY para implementação oficial SDK MCP compartilhada e equivalência rigorosa com contrato DELPI JSON-RPC, SSE, bearer, deadline, delegated token; YES para contexto experimental de snapshots no runtime opcional. **REUSE_DECISION:** KEEP/SHRINK dos boundaries reais; REMOVE recursos experimentais somente com decisão formal de retirada; EXTEND apenas o menor diff comprovado. Não criar novo adapter paralelo nem transferir autorização a Pydantic AI.

## 2. Matriz 7/7 arquivos

| Arquivo | Linhas | Funções e responsabilidades atuais | Consumidores comprovados | Decisão alvo |
|---|---:|---|---|---|
| `__init__.py` | 2 | marcador de pacote | imports de config, delegation, mcp | KEEP |
| `config.py` | 78 | `SpecialistConnectionProfile`, `specialist_connections_from_settings`, URLs, flags, timeouts, resource audiences / IDs | `root_composer.py`, `mcp/adapter.py`, `delegation.py` | KEEP/SHRINK; centralizar apenas variáveis de configuração legítimas, sem segredos; não confundir com JSON exclusivo de runtime Pydantic AI |
| `delegation.py` | 429 | `DelegatedCredentialProvider` Protocol, JWT payload checks, `InMemoryDelegatedTokenCache`, `KeycloakDelegatedCredentialProvider`, `_exchange`, `_validated_token`; RFC 8693, subject/audience/scope/expiry, invalidation | `root_composer.py`, `mcp/adapter.py`, testes de credentials | **KEEP SECURITY CRITICAL**, revisar duplicações com Auth/keycloak sem apagar validações independentes |
| `mcp/__init__.py` | 2 | marcador de pacote | imports MCP | KEEP |
| `mcp/adapter.py` | 384 | `McpSpecialistAdapter`, `list_remote_tools`, `call_remote_tool`, `_connect`, `_require_invocable`, `_map_outcome`, revalidação live `tools/list` | `root_composer.py`, `mcp/transport.py`, SpecialistInterop | **KEEP OPERATIONAL**, revisar duplicações e custos de listar live em cada chamada, sem abrir autoridade |
| `mcp/catalog_store.py` | 248 | `McpCatalogStore` SQLite; `canonicalize`, `contract_hash`, `diff_tools`, `active/history/version/activate/verify` | `root_composer.py` quando `mcp_catalog_mode=snapshot_experiment`; `snapshot_interop.py`, `scripts/mcp_catalog_sync.py`, testes | **EXPERIMENTAL / DECISION REQUIRED**, não é órfão; decidir aposentadoria do modo snapshot, ou manter separado da execução live |
| `mcp/transport.py` | 351 | `DelpiMcpTransport`, `initialize`, `list_tools`, `call_tool`, `_rpc`, `_send`, `_parse_body`, `_parse_sse`; HTTP JSON-RPC + SSE + timeout/bounds | `mcp/adapter.py` usa por default | **KEEP OPERATIONAL**; avaliar reuso real de MCP SDK existente em vez de transporte caseiro, só após provar paridade completa e boundary |

**TOTAL:** 7 arquivos, **1494 linhas** pelos contadores de extração (2+78+429+2+384+248+351). Mensurar com `wc -l` no checkout para baseline definitivo.

## 3. Revisão funcional detalhada

### 3.1 config.py

`CANONICAL_MCP_CLIENT_IDS`, `CANONICAL_MCP_RESOURCE_AUDIENCES` vêm de `_SPECIALIST_IDENTITY`; `SpecialistConnectionProfile` guarda endpoint, enabled, timeout, exchange_audience, resource_audience e host_header. `specialist_connections_from_settings` combina configuração em `Settings` com algumas variáveis `DELIA_MCP_{SPECIALIST}_*` via `os.getenv`. Estes valores representam **identidade de recurso/interop**, não limites de LLM. Não forçar inclusão de secrets ou client/resource auth no JSON `pydantic_ai.runtime.delpi.json` do doc243. Revisar duplicação entre Settings e leitura direta de env, tratamento de valores desconhecidos, lista de specialist IDs e fonte canônica `_SPECIALIST_IDENTITY`. Não usar metadata MCP para descobrir audience ou autorização.

**TARGET:** apenas eliminar defaults/duplicações realmente comprovados e manter configuração governada source-of-truth; falhas de configuração devem ser fail-closed.

### 3.2 delegation.py

`DelegatedCredentialProvider` é port de credentials necessário; `KeycloakDelegatedCredentialProvider` realiza exchange e validação de subject, scopes, audiences, expiration e cache por contexto de subject. Há interface de `invalidate` usada para invalidar token quando owner nega. Não é arquitetura agentiva legada; não apagar para “usar Pydantic AI”. Revisar se já existe componente oficial de troca de token reutilizável com mesmo contrato (Keycloak / shared auth), e comparar cuidadosamente proteção, cache, JWT validation e reentrância. **O resultado do decode local de claims não substitui validação de JWT assinada ou Core AuthZ**; identificar o validador de origem e documentar as garantias. Verificar nenhuma chave/token vai a prompt/log. Se troca puder migrar a shared owner legítimo sem perda de garantias, EXTEND por adapter, nunca remover segurança.

### 3.3 mcp/adapter.py

`McpSpecialistAdapter` implementa `SpecialistInteropPort`; `list_remote_tools` mapeia `tools/list`, `_meta.delpi/toolClass` e schema; `_call_remote_tool` e `_require_invocable` exigem owner listado ao vivo antes do call; source class UNKNOWN/ausente bloqueia. O adapter é realmente ligado em composição. Isso não confere Core/Domain permissions por metadata: owner tool class é untrusted e só classifica/filtra superfície. Testar prompt injection via descrição/schema, model-proposed arbitrary tool names, live revocation, token scope, write class gates. Investigar custo de `initialize`+`list_tools` em cada call, mas não cachear autorização sem contrato explícito.

**TARGET:** KEEP e eventualmente SHRINK neutralizando mapeamento/normalização redundante, sem novo planner ou provider registry.

### 3.4 mcp/transport.py

Transporte implementa manualmente JSON-RPC, bounded requests, timeout total, session-id echo e SSE defensivo. É o candidato a substituição por **SDK MCP oficial já instalado** se equivalência funcional, autenticação por request e deadline forem demonstradas. O Pydantic AI possui integração MCP nativa, mas **não autoriza substituição direta** sem preservar SpecialistInterop, delegated credentials, Core/Domain live authority, approved specialist registry, owner tool classes e PREPARE/ACT. Reusar SDK apenas como mecânica de transporte no adapter governado, não entregar MCPToolset diretamente ao Agent se isso driblar controles. Conferir versões/pacotes realmente instalados, comportamento streamable_http json_response/stateless, scopes, timeout, sessão, cancelamento, size cap e controle de erro.

**TARGET:** KEEP ou REPLACE WITH EXISTING VERIFIED transport; proibir nova implementação própria alternativa. Remoção só após RED/GREEN e E2E com o owner real.

### 3.5 mcp/catalog_store.py

É um snapshot store SQLite de `tools/list` para **SNAPSHOT_EXPERIMENT**, não o catálogo live padrão e não um segundo planner. `root_composer.py` aceita `mcp_catalog_mode="snapshot_experiment"`, exige `mcp_catalog_db` e cria `SnapshotDiscoverInterop(adapter, McpCatalogStore(...))`. `SnapshotDiscoverInterop` continua invoke live; o sync manual está em `scripts/mcp_catalog_sync.py`; `tests/test_mcp_catalog_experiment.py` (167 linhas) cobre experimento.

**TARGET / DECISION:** Se docs 16/ledger/autorização de fase encerrarem o experimento, remover de forma atômica: `mcp/catalog_store.py`, `application/specialist_interop/snapshot_interop.py`, `scripts/mcp_catalog_sync.py`, config `DELIA_MCP_CATALOG_MODE/DB` e testes exclusivamente de snapshot, preservando testes de segurança do catálogo live. Se o experimento ainda é decisão congelada ou avaliação ativa, manter explicitamente **EVAL_ONLY**, sem promover snapshot a autoridade e sem interferir no live. Não apagar silenciosamente.

### 3.6 __init__.py e mcp/__init__.py

KEEP marcadores do pacote, sem relevância para redução de lógica.

## 4. Consumidores e evidência

**PROVEN:**
- `root_composer.py` importa e instancia `specialist_connections_from_settings`, `KeycloakDelegatedCredentialProvider`, `McpSpecialistAdapter` e, condicionalmente, `McpCatalogStore` com `SnapshotDiscoverInterop`.
- `mcp/adapter.py` importa `DelpiMcpTransport` e o cria por default; também consome perfis e provider delegado.
- `scripts/mcp_catalog_sync.py` importa o store; `test_mcp_catalog_experiment.py` o instancia.
- Testes existentes `test_delegated_credentials.py`, `test_mcp_adapter.py`, `test_mcp_catalog_experiment.py`, `test_specialist_interop_architecture/security/usecase/domain.py` e `real_mcp_interop_eval.py`.
- GitHub recursive tree `truncated=false` identifica 27 paths MCP/interop/snapshot relacionados (lista obtida neste SHA), mas **não comprova callgraph global**.
- `mcp/transport.py` já depende de `requests` + `bounded_request` + `deadline_http_post`; nenhuma migração para SDK foi comprovada nesta auditoria.
  
**TO_INVENTORY:** todo uso via import dinâmico, config de prod, versão do SDK MCP e client Pydantic AI, equivalência de transport behavior, se snapshot experimento foi descontinuado por authority, validação criptográfica live de token exchange, todas as chamadas/consumers e seus testes.

## 5. Ordem de execução recomendada

1. Reanchor git status/HEAD, authorities 16→50→17→49→51→52→21→20→25, arquitetura/product spec, ledger, docs 239–248 e decisões especializadas de MCP, Keycloak e Snapshot. Inventariar consumers com rg + AST + runtime traces.
2. **NÃO excluir** config/delegation/adapter/transport por princípio de zero legado: eles são governança e interop real, não motores de inteligência paralelos. Eliminar apenas partes sem consumers ou duplicações concretas.
3. Decidir `SNAPSHOT_EXPERIMENT` com authority; se não houver consumer permitido/experimento ativo, remover pacote de snapshot por inteiro com config, script e testes de implementação, sem alterar live path.
4. Verificar substituição do transporte custom por MCP SDK existente, em Infrastructure e sem desvio de `SpecialistInteropPort`. Se paridade não comprovada, KEEP e registrar gap; não reescrever uma terceira transport stack.
5. Revisar profiles e delegation contra componentes legítimos de Keycloak compartilhados; nenhuma duplicação de authorizations; credentials audit e fail-closed.
6. RED/GREEN: list/invoke real; unknown tool; unknown class; denied/unauth/expired/mismatched audience; token revocation; 401/403; GET/SSE/JSON RPC; timeout/stream/bounds; candidate provenance/injection; audit, write gates, source availability.
7. Full backend suite + model-native E01–E10 on local rebuilt SHA; SourceRef, outcomes, JSON/NDJSON, cancel, token/scope negatives. `TEST_NOT_RUN` if runtime unavailable, not PASS.
8. Atualizar relatório doc249, docs 239/246/248, ledger com factual results; commit/push main preserving WIP, no prod deploy.

## 6. Veredito e critérios

**PROVEN:** 7/7 arquivos lidos integralmente; os paths principais estão conectados ao runtime; store experimental tem consumer condicional; não é pasta órfã.

**REVIEW:** `KEEP/SHRINK` 4 módulos operacionais; `KEEP` package markers; `DECISION_REQUIRED` para snapshot store; `REUSE_BEFORE_NEW` para transporte MCP SDK. Nenhum motivo comprovado para eliminar a pasta inteira.

**TEST_NOT_RUN:** nenhuma edição ou teste executado nesta auditoria; somente documentação.

**ACCEPTANCE:** código operacional mínimo, sem runtime/adapter duplicado, autenticação delegada e authorization gates intactos, apenas snapshot permitido pelo ledger, suíte/E2E sem regressões e zero informação secreta em modelo/memory/logs.
