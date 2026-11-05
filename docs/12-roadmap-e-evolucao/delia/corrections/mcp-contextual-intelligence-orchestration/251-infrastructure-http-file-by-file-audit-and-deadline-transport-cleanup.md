# 251 — DÉLIA · Auditoria integral de infrastructure/http e limpeza de transporte governado

**TASK_ID:** DELIA-C3-INFRASTRUCTURE-HTTP-FULL-FOLDER-AUDIT-AND-BOUNDED-TRANSPORT-CLEANUP-01  
**DATE:** 2026-11-05  
**HEAD AUDITADO:** `3a09c45ac228b66570bff5ff31ccbf7be28d1f7f`  
**STATUS:** AUDIT / PLANNED — NO SOURCE CODE CHANGED, TEST_NOT_RUN  
**SCOPE:** `delia-api/app/infrastructure/http/` (4/4 arquivos integralmente lidos no HEAD)  
**RELATED:** docs 239–250, especially 247 OpenAPI, 248 MCP, 249 model invocation/STT, 250 config; canonical decisions LOOP-03R2A-R2/R3/R4/R5  
**PRODUCTION_DEPLOY:** NOT_AUTHORIZED.

## 1. Resultado principal

Diferente de `infrastructure/openapi`, este pacote é **ativo e transversal**. O código atual implementa uma defesa específica contra timeouts por inatividade renováveis em `requests`/urllib3, incluindo DNS, TCP, TLS, status line, headers e leitura de body. Testes de socket real existem. **Não remover por volume nem pressupor que Pydantic AI/MCP SDK substituam os deadlines governados.** HTTP transport é infraestrutura legítima, não motor semântico ou antigo CRI.

**EXISTING_EQUIVALENT:** YES para `requests`/urllib3, `bounded_request`, `deadline_http_get/post`, `dns_resolver` próprios já ativos; TO_INVENTORY para suporte equivalente em SDK/HTTPX existente com deadline verdadeiramente absoluto em toda a fase e sem threads pendentes; YES para política de execução e timeout da Application. **REUSE_DECISION:** REUSE/SHRINK controles atuais; EXTEND para consumidores fora do caminho bounded (ex. STT streaming); NEW=NO. Não criar segundo HTTP stack sem equivalência provada.

Reanchor obrigatório antes de editar: local HEAD/status/origin → Project Instructions/.cursor → authorities 16→50→17→49→51→52→21→20→25 → arquitetura/product spec → spec temática → ledger e docs 239–251; conflitos são ARCHITECTURE_DECISION_REQUIRED ou EXECUTION_DRIFT, jamais reconciliação silenciosa. Inspeção foi GitHub API-only, sem checkout/status ou avaliação local.

## 2. Matriz integral 4/4

| Arquivo | Linhas extraídas | Principais símbolos | Consumidores reais | Decisão |
|---|---:|---|---|---|
| `__init__.py` | 1 (vazio) | marcador de package | imports de módulos | KEEP |
| `bounded_request.py` | 222 | `bounded_request`, `BoundedHttpResponse`, `BoundedHttpTimeout`, `BoundedHttpTransportError`, `BoundedHttpTooLarge`, `_drain_body`, `_tighten_socket_timeout` | `root_composer.py`, `delegation.py`, `mcp/transport.py`, `openapi/http_invoker.py`, STT | **KEEP/SHRINK**, gateway factual de limites |
| `deadline_transport.py` | 646 | `deadline_scope`, `deadline_http_get/post`, `_DeadlineSocket`, `_DeadlineHTTP(S)Connection`, `_BoundedConnectMixin`, `_DeadlineHTTPAdapter`, `_deadline_session`, `_bounded_tls_handshake` | `bounded_request`, MCP transport, delegation via wrapper, root_composer, STT | **KEEP/REVIEW NATIVE ALTERNATIVE**, segurança crítica e integração urllib3 sensível à versão |
| `dns_resolver.py` | 136 | `BoundedDnsResolver`, `dns_resolver`, `DnsResolverSaturatedError` | `deadline_transport.py::_bounded_connect` | **KEEP**, arquitetura explicitamente aprovada para DNS bounded; revisão de lifecycle |
| **Total** | **1005** | | | |

Contagens feitas em texto GitHub via `split("\n")`; medir `wc -l` no checkout para baseline definitivo.

## 3. `bounded_request.py` (222)

Envolve o callable `send` (`deadline_http_get/post` ou callable injetado), define deadline monotônico, usa `deadline_scope`, aplica `stream=True`, drena corpo sob budget e size cap `DEFAULT_MAX_BODY_BYTES=4MiB`, devolve `BoundedHttpResponse` com `text/json`. Tipos de erro são úteis para adapters de owner e nunca devem ser convertidos em sucesso.

**Candidatos de redução/verificação:**
- `_READ_SLICE_SECONDS=0.5`, `_BODY_CHUNK_BYTES=65536` e `_tighten_socket_timeout` refletem fallback de `requests`/urllib3; verificar se são necessários ainda quando o `_DeadlineSocket` controla todas as fases. Não retirar até teste contra trickle pre-body/body, stalled TLS e DNS.
- `_tighten_socket_timeout` navega em detalhes internos do response.raw socket: risco de quebra por versão, não incidente comprovado. Manter se teste comprovar necessidade; preferir API documentada se possível, sem degradar deadline.
- Payload `json()` e `text` são compatibilidade de response; verificar consumer de cada propriedade antes de simplificar. Não modificar semântica de erros ou limite do corpo.

**KEEP:** total wall-clock budget, response-byte bound, fail closed em timeout/erro, não logar headers/token/payload. Evitar usar `requests` raw diretamente nos consumidores que exigem deadline.

## 4. `deadline_transport.py` (646)

O maior arquivo da pasta. Implementa `ContextVar` do deadline; wrapper de socket que re-calibra timeout antes de recv/send; DNS+connect por orçamento compartilhado; TLS handshake nonblocking via `select`; conexões/pools/adapter HTTP(S) próprios, sob Requests/urllib3. Deny proxy fail-closed. **Não é HTTP stack completo alternativo**: depende da pilha Requests/urllib3 e usa seus contratos de certificado/pooling, mas toca APIs privadas de urllib3.

**Candidatos de limpeza:**
- Subclasses `_DeadlineHTTPConnection`, `_DeadlineHTTPSConnection`, connection pools e pool manager (linhas ~396–580) representam peso e acoplamento. Provar equivalência com implementação já disponível (Requests/HTTPX/httpcore, MCP SDK) em timeout **total**, nunca apenas read-idle timeout. Não substituir por `requests.get(timeout=N)` ou `urllib3.Timeout(total=N)`, que não passam os probes declarados.
- `_bounded_tls_handshake` e o wrapper de socket são segurança contra fragmentação e cliente preso; sua exclusão requer fixtures com TLS real, proxy, redirect, connect stalls, end-to-end total timeout, certificado e hostname validation.
- Inspecionar dependência de atributos privados `urllib3` e contrato de versão/pinning do projeto; evitar upgrades sem regression e testes. `GOVERNED_HTTP_PROXY_POLICY=DIRECT_ONLY_CURRENT_SCOPE` é decisão documentada, não desabilitar por conveniência.
- `_deadline_session` cria sessão e adapters governados. Inventariar resource close/pool lifecycle, reuse e thread-safety. Candidato a reuse de sessão se provar menor overhead e correção sob contextvar/request; não configurar sessão global com bearer reutilizado.
- Timeout não equivale a cancelamento de remote business action: preservar PREPARE/ACT gates e idempotência, nunca alegar que chamada abortada reverte owner.

**DECISÃO:** KEEP agora, possível substituição native somente por equivalência forte e com review de arquitetura específico; sem “simplificação” que reabra trickle.

## 5. `dns_resolver.py` (136)

Contrato governado explícito `ARCHITECTURE_DECISION_DNS_DEADLINE=APPROVED` e `DNS_STRATEGY=BOUNDED_RESOLVER_EXECUTOR`. Apenas `socket.getaddrinfo(host,port,family,socktype)` ocorre em pool limitado `MAX_DNS_RESOLVER_WORKERS=4`, `MAX_DNS_RESOLVER_OUTSTANDING=8`; resultados após deadline são descartados, zero connect pós-expiração. Resultado não recebe credenciais.

**KEEP.** `ThreadPoolExecutor` pode ainda ter chamadas DNS presas em background até o libc retornar; isto é exceção de design documentada, não “leak” provado. Avaliar shutdown, saturação, pressão de memória, worker-count e reuso do mesmo resolver; evitar fila ilimitada ou cancelamento falso. Só remover se houver bounded DNS equivalente aprovado pela autoridade, com provas de timeout storm/zero connect after expiry. Não adicionar threads para HTTP inteiro.

## 6. Consumidores rastreados no SHA

- `root_composer.py`: `bounded_request` + `deadline_http_get/post`, inclusive fluxo Core e delegação.
- `infrastructure/interoperability/delegation.py`: `bounded_request` para Keycloak token exchange.
- `infrastructure/interoperability/mcp/transport.py`: `bounded_request` com `deadline_http_post` em MCP.
- `infrastructure/openapi/http_invoker.py`: `bounded_request`, mas **integração direta OpenAPI já desconectada no root**, sujeito a doc247 remoção; eliminar consumer se arquivo for realmente removido.
- `infrastructure/model_invocation/openai_compatible_transcription_adapter.py`: caminho `transcribe` chama `bounded_request`, `stream_transcribe` usa `requests.post` direto. **Confirmed gap in shared governed-transport consumption**: fluxo incremental usa checagem monotônica entre linhas, mas `iter_lines()` pode bloquear enquanto read timeout se renova com trickle; provar deadline total sob stalled/trickle stream antes de mover; manter atualização parcial e protocolo SSE seguro.
- Model text inference Pydantic AI usa SDK/HTTPX internamente e não chama `bounded_request` diretamente; **não presumir** que esse gateway cobre a inferência de modelo. Doc249 identifica timeout separado via thread daemon.

**TO_INVENTORY**: outros consumidores, imports dinâmicos e env, resource ownership e SDK candidate compatibility por AST + `rg` global.

## 7. Testes existentes e risco de apagar cobertura

`delia-api/tests/test_http_absolute_deadline.py` tem ~1202 linhas de testes, incluindo: status-line trickle, header trickle, first-byte stall, body trickle, TLS handshake trickle real, connect multi-address, DNS slow/late/timeout-storm/saturation, redirects no orçamento global, proxy reject, gzip e case-insensitive headers. `test_delegated_credentials.py`, `test_mcp_adapter.py`, testes de transcrição e ditado exercitam consumidores.

**Não apagar testes desses comportamentos sob pretexto de remover “legacy”**. A limpeza deverá manter regressões equivalentes **no SHA final**, executar com rede local de teste, verificar p95/cancel/transport contract quando aplicável. Nenhum teste foi executado durante esta auditoria.

## 8. Plano executável da limpeza

1. Reanchor e inventariar TODOS os consumidores e deployment pin de Requests/urllib3/HTTPX; caracterizar path direto, SDK, MCP, Core, Keycloak, STT e eventual OpenAPI residual.
2. Traçar testes RED para STT streaming lento/trickle, timeout pre-body/body, certificate/hostname, DNS zero-connect, proxy reject, redirect sharing budget, negative timeout, response-too-large, secrets never logged.
3. **Primeira correção funcional recomendada:** encaminhar ditado incremental para o bounded transport existente ou uma primitive de streaming que forneça o mesmo deadline absoluto **sem copiar** a implementação de HTTP; streaming progressivo deve continuar NDJSON e sem buffering integral.
4. Revisar redundância de `_tighten_socket_timeout` e connection wrappers contra resultado de testes; remover somente com equivalência; não trocar pela opção `timeout=...` do requests.
5. Eliminar referencias do adapter OpenAPI se a remoção doc247 for executada e sua ausência for comprovada; não apagar transport geral.
6. Quando versão e paridade comprovadas, avaliar library-native transport alternative via POC bounded, como decisão arquitetural explícita, nunca silenciosa.
7. Executar suite HTTP real + MCP + credential + STT + backend completo + real Pydantic E01–E10 no runtime reconstruído quando possível. Invalid/unauth/expired token, no sensitive logs, provenance, SourceRef e Outcome.
8. Residual search, atualizações docs 247–251, ledger e próximo execution report; commit/push main preservando concorrência, não deploy produtivo.

## 9. Resultado de review

**PROVEN:** 4/4 arquivos lidos no HEAD, funções enumeradas, arquitetura DNS bounded explicitamente aprovada em código, consumidores nomeados ativos, testes de socket real presentes, STT streaming fora do gateway bounded.

**TO_INVENTORY:** execução real/efetiva dos testes no SHA, validação integral de pin de lib/SDK e network behavior, consumers dinâmicos, autoridades/ledger canônicos.

**REUSE_DECISION:** REUSE/SHRINK existing governed HTTP transport; KEEP critical deadline/DNS. **Não existe evidência para exclusão integral da pasta.**

**TEST_NOT_RUN:** sem alterações de fonte nem testes nesta auditoria; documentação não é implementação.
