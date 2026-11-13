# 167 — Tempo real do Lançamento de Notas Fiscais (WebSocket na BFF)

| Campo | Valor |
|---|---|
| Status | **CONTRACT_DRAFT** |
| Data | 2026-11-13 |
| Decisor | owner do produto |
| Baseline de evidência | W0 no HEAD `7f332cb39b`; rebaseline W1 no HEAD `ce96027440` (sem diff desde a W0 em `controllership-finance-api`, `plugins/lancamento-notas-fiscais`, `plugins/plugin-ui/src/realtime` e `gateway`) |
| ADR | [ADR-002](./adr/ADR-002-tempo-real-lnf-websocket-bff.md) |
| Trilha de hospedagem | [165](./165-trilha-execucao-migracao-lnf-ate-clara.md) — este documento não a altera |

Este arquivo é contrato. Não autoriza código, gateway, compose nem deploy.

## 2.1 Objetivo, escopo e não-escopo

Atualizar as telas abertas do app `lancamento-notas-fiscais` quando outra pessoa, a CLARA ou a conciliação que já existe mudar uma solicitação. O canal é WebSocket na `controllership-finance-api`, módulo LNF. O evento só avisa. A tela relê pelo HTTP que já existe.

Escopo: fila, detalhe, formulário de edição e produtos sem código Delpi, nas rotas `/apps/lancamento-notas-fiscais/filial-01` e `/filial-02`.

Não-escopo:

- controle otimista (ETag, versão de linha, `If-Match`);
- emitir `divergence_detected` (a coluna existe; não há writer);
- job periódico de conciliação (fica na W7, com decisão própria, depois do F5c);
- mudanças no sino da Core (Socket.IO, categorias, poll de 60s);
- broker, Redis ou fan-out entre processos;
- compartilhar hub com o Fechamento ou com o Socket.IO da Core.

## 2.2 Decisões e o que a W0 já travou

| Id | Decisão | Evidência |
|---|---|---|
| D-W1 A | JWT na query `token` do handshake, igual aos WS de produto. A location nova do gateway redige `token` no access log, com o mesmo formato das locations de TV (`gateway/nginx.conf:25-40`, usado em `:805`). | Owner, 2026-11-13. Padrão: `requests-api/.../realtime_routes.py:112-116`, `engineering-api/.../realtime_routes.py:109-113`, `plugins/plugin-ui/src/realtime/engineeringRealtime.ts:50-54`. |
| D-W2 A | Hub na memória do processo da BFF. Workers ou réplicas > 1 exigem broker antes; até lá o realtime fica desligado. | Owner. Hoje a BFF é 1 processo, sem `--workers` (`controllership-finance-api/Dockerfile:38`) e sem `replicas` no compose. Os hubs de requests e engineering também são `dict` no processo. |
| D-W3 C | Sem job novo. Todo refresh e todo run que já rodam emitem aviso para as telas da filial. | Owner. Refresh só na abertura da fila (`plugins/lancamento-notas-fiscais/src/ui/pages/QueuePage.tsx:135-146`); run é `manage` e o MFE não chama (`router.py:1194-1198`). |
| D-W4 A | DEV e HML agora. PROD só com F5c DONE. | Owner. Quadro da trilha 165: F5c `IN_PROGRESS`. |
| W0 | Dono do canal = BFF, módulo LNF. Não usar Socket.IO da Core. Não compartilhar hub com o Fechamento. | W0. Core emite `admin.changed` para o sino (`core-api/.../dispatch_notifications_use_case.py:183-197`). Outbox da BFF é do fechamento, não do LNF. |
| W0 | Evento = aviso + refetch HTTP. Sem dados de negócio. | Padrão Engineering: `plugins/plugin-ui/src/realtime/engineeringRealtime.ts:1-6`. |
| W0 | Salas por filial e por solicitação, autorizadas na assinatura com `Actor` + `branch_view_allowed`. | `branch_access.py:36-50`, `router.py:187-201`. |
| W0 | Emissão depois do commit, best-effort. Falha ao emitir não muda o HTTP. | Mesma regra do DANFE/unmapped: falha posterior não desfaz a solicitação (`unmapped_supplier_product_service.py:1-5`). |
| W0 | Canal aditivo. A tela nasce do HTTP e funciona sem socket enquanto F6 da trilha 165 não estiver DONE. | Default do MFE ainda é api-delpi se `VITE_LNF_API_BASE` não vier no build (`invoicePostingApi.ts:20-25`). |
| W0 | O servidor fecha a conexão no exp do JWT. | Engineering já faz isso (`engineering-api/.../realtime_routes.py:141-152`, hub `:151-157`). Ajuste de código e folga na §2.5. |
| W0 | Location de gateway nova e estreita só para `/realtime`. O prefixo `/apps/controllership-finance-api/` permanece como está (sem Upgrade, timeout 300s). | `gateway/nginx.conf:708-721`, `nginx.dev.conf:551-559`, `snippets/hml-proxy-locations.conf:198-210`. |

Regra de parada do R1: **não acionada.** O ENG-REALTIME-01 está `IMPLEMENTADO` e o “transversal” é interno à Engineering API (PRC como primeiro consumidor). Não é ADR da plataforma e não contradiz D-W1..D-W4. Ver §2.16.

## 2.3 Arquitetura

```text
use case LNF
  → repositório (commit)
  → InvoicePostingChangeNotifier   (port de aplicação; domain não importa)
        ├─ NoOp                         se LNF_REALTIME_ENABLED estiver off
        └─ InMemoryInvoicePostingRealtimeHub + rota FastAPI
              → gateway location /realtime
              → MFE refetch HTTP
```

Nomes pela convenção do módulo (`InvoicePosting*` em `domain/invoice_posting/ports.py`), não pelo prefixo solto `Lnf*`:

| Peça | Nome |
|---|---|
| Port | `InvoicePostingChangeNotifier` |
| Hub | `InMemoryInvoicePostingRealtimeHub` |
| Nulo | `NoOpInvoicePostingChangeNotifier` |

Domain não ganha import de WebSocket, FastAPI nem logger de socket. O port é chamado pelos use cases **depois** que o método de repositório retorna (o commit já ocorreu). Exceção engolida no notifier: a resposta HTTP da escrita permanece a que o use case já decidiu.

Flags:

| Flag | Onde | Default | Efeito |
|---|---|---|---|
| `LNF_REALTIME_ENABLED` | BFF | `false` | Só monta a rota se também `LNF_HOSTED_ENABLED=true`. Off = rota inexistente (não 1008). |
| `VITE_LNF_REALTIME_ENABLED` | build do MFE | desligado | Off, ou base ainda em `/apps/api-delpi/lancamento-notas-fiscais`: o MFE não abre socket e não mostra erro. |

Restrição D-W2: se o Dockerfile passar a ter `--workers` > 1 ou o compose ganhar réplicas, a flag fica `false` até existir broker. Um hub em memória não atravessa processo.

## 2.4 Endpoint e handshake

```text
WS {gateway}/apps/controllership-finance-api/lancamento-notas-fiscais/realtime?token=<JWT>
```

- Assinatura e `exp` por `delpi_auth` (`validate_token`), o mesmo validador do HTTP.
- Permissões efetivas pelo Core `GET /me`, o caminho de `load_user_rbac` (`shared/delpi_auth/middleware/fastapi_auth.py:104-148`).
- Permissão mínima para **entrar**: qualquer item de `LANCAMENTO_NOTAS_FISCAIS_READ_PERMISSIONS` (a de `GET /requests`, `router.py:644-645`) **ou** `lancamento-notas-fiscais.review-unmapped-products`. O “ou” é ajuste do R4: a leitura de produtos sem código não está na lista do GET da fila (`permissions.py:9-24` e `router.py:576`). Sem isso, quem só tem a permission daquela tela não conecta. Assinar sala de filial ou de solicitação continua exigindo `branch_view_allowed`. Quem só tem a permission de unmapped e tenta a sala da filial recebe `forbidden_room`.
- **Origin:** requests e engineering não checam `Origin` no handshake. Checar o host do portal é endurecimento local do LNF, não padrão herdado.
- O servidor agenda o fechamento no `exp` do token, com a folga de 5s que a Engineering já usa (`realtime_routes.py:141-144`), para o refresh do portal conseguir o handshake seguinte. Código na §2.5.
- Log de aplicação não imprime o token, a query string nem o header `Authorization`. Pode registrar `user_id` e o código de fechamento.

## 2.5 Close codes

Ajuste do R3 (detalhe na §2.16). Requests e engineering recusam o handshake com **1008** tanto para token inválido quanto para falta de permissão. Não existe 4401 nesses módulos. Idle e o fim do JWT na Engineering fecham com **1000**, não com 4401 nem 1001.

| Situação | Código | Cliente |
|---|---|---|
| Token ausente na URL | o MFE não abre o socket | — |
| Token inválido ou expirado **no handshake** | **1008** | não entra em loop com o mesmo token; quando `getAccessToken()` devolver outro valor (refresh do portal), reconecta |
| Sem a permissão mínima do handshake | **1008** | o token não muda → permanece desconectado e mostra «Atualização automática indisponível» |
| JWT chega no `exp` com a conexão já aceita | **1000** | reconecta; a URL nova leva o token renovado |
| Idle sem `ping` | **1000** | reconecta com backoff (o cliente envia `ping` para não cair aqui) |
| Erro interno inesperado | **1011** | reconecta com backoff. Não há esse código nos hubs de requests/engineering; fica o da base deste contrato |
| Shutdown do processo | **1001** | reconecta com backoff. Também não há padrão nos hubs atuais |

Flag off não usa close code: a rota não existe.

## 2.6 Protocolo

O `RealtimeSocketClient` (`plugins/plugin-ui/src/realtime/realtimeSocket.ts:126-130`) envia o texto `ping` e trata o corpo das outras mensagens como string opaca. O servidor LNF segue isso.

Cliente → servidor:

| Mensagem | Formato |
|---|---|
| ping | texto `ping` (não JSON) |
| subscribe | `{"type":"subscribe","room":"<sala>"}` |
| unsubscribe | `{"type":"unsubscribe","room":"<sala>"}` |

Servidor → cliente:

| Mensagem | Formato |
|---|---|
| pong | `{"type":"pong"}` |
| subscribed | `{"type":"subscribed","room":"<sala>"}` |
| unsubscribed | `{"type":"unsubscribed","room":"<sala>"}` |
| error | `{"type":"error","code":"forbidden_room"\|"unknown_room","room":"<sala>"}` |
| evento | envelope da §2.8 |

Assinatura negada responde `error` e **não** fecha a conexão. Sala malformada → `unknown_room`. Solicitação inexistente → `forbidden_room` (não revela existência).

O envelope `{type, code}` e o fato de a negação não derrubar o socket são o padrão (`engineering_realtime_protocol.py:8-10`, `requests_realtime_protocol.py:63-69`). Os códigos `forbidden_room` e `unknown_room` são do LNF: a plataforma usa códigos do domínio dela (`accessDenied`, `resourceIdInvalid`, `domainUnsupported`), não um enum único.

`engineeringRealtime.ts` **não** serve para o LNF: a URL, o `domain` e o tipo `engineering.resource.changed` são da Engineering. O cliente genérico só transporta. A política de backoff e de close code do LNF não cabe nele sem alterá-lo — ver §2.16, opção do R2. A W4 usa wrapper local no MFE.

## 2.7 Salas e autorização na assinatura

A autorização usa o mesmo `Actor` do HTTP e `branch_view_allowed`. Não há sala global.

| Sala | Regra |
|---|---|
| `lnf:branch:01`, `lnf:branch:02` | `branch_view_allowed` para aquela filial (`branch_access.py:36-50`). `view`, `process` ou `manage` passam nas duas. Só `view.filial-01` passa na 01. |
| `lnf:request:{uuid}` | Carrega a filial da solicitação e aplica `branch_view_allowed`. Id inválido ou solicitação ausente → `forbidden_room`. |
| `lnf:unmapped-products` | `lancamento-notas-fiscais.review-unmapped-products`, a mesma de `GET /unmapped-products` (`router.py:573-576`). |

Teste negativo obrigatório: usuário só com `view.filial-01` não assina `lnf:branch:02` nem `lnf:request` de solicitação da 02, e nenhum evento da 02 chega nesse socket.

## 2.8 Catálogo de eventos

Envelope comum:

```json
{
  "type": "lnf.request.changed",
  "eventId": "<uuid>",
  "occurredAt": "<UTC ISO-8601>",
  "branch": "01"
}
```

Proibido no payload: fornecedor, valor, nome de pessoa, texto de comentário, justificativa, chave fiscal, número do documento.

| type | Campos além do envelope | Salas |
|---|---|---|
| `lnf.request.changed` | `requestId`, `reason`, `actorOrigin` | `lnf:branch:{branch}` e `lnf:request:{requestId}` |
| `lnf.queue.reconciled` | `updatedCount` (inteiro > 0) | `lnf:branch:{branch}` daquela filial |
| `lnf.unmapped-products.changed` | nenhum campo de negócio | `lnf:unmapped-products` |

`reason` de `lnf.request.changed`: `created` | `updated` | `status_changed` | `cancelled` | `manual_posted` | `purchase_order_linked` | `comment_added` | `reconciled`.

`actorOrigin`: `user` ou `system`, o mesmo eixo da timeline. Start, block e resume são `status_changed` (não existem `event_type` `started`/`blocked`/`resumed`).

`lnf.queue.reconciled` só sai quando `updatedCount > 0` **naquela filial**. Um lote que atualiza as duas filiais gera um aviso por filial. Refresh e run emitem. O PATCH que chama `try_reconcile_requests` (`use_cases.py:1078` e `:1549`) também, porque já é conciliação em execução, não um job novo.

## 2.9 Tabela de emissão

O notifier ainda não existe. A coluna «momento» é o ponto em que a W2 o chama: depois do commit daquela escrita. A CLARA entra pelas mesmas rotas (`invoice_posting_bridge` → router); emite igual, com `actorOrigin=user`.

| Escrita | Onde a timeline/gravação nasce | Evento | reason | Salas | Momento |
|---|---|---|---|---|---|
| Criar | `use_cases.py:340-342` | `lnf.request.changed` | `created` | filial + request | após o insert da solicitação retornar |
| PATCH | `use_cases.py:1046-1047` | `lnf.request.changed` | `updated` | filial + request | após `update_request_with_history` retornar |
| PATCH que casa no SF1 | `use_cases.py:1078` → `:1549` e batch `:798` | `lnf.request.changed` e, se a filial teve post, `lnf.queue.reconciled` | `reconciled` | filial + request; aviso de fila só na filial com contagem > 0 | após o commit do batch |
| Start | `use_cases.py:1122-1127` | `lnf.request.changed` | `status_changed` | filial + request | após o update retornar |
| Block | `use_cases.py:1187-1192` | `lnf.request.changed` | `status_changed` | filial + request | após o update retornar |
| Resume | `use_cases.py:1246-1250` | `lnf.request.changed` | `status_changed` | filial + request | após o update retornar |
| Cancel | `use_cases.py:1327-1328` | `lnf.request.changed` | `cancelled` | filial + request | após o update retornar |
| Já lançada | `use_cases.py:1383-1384` | `lnf.request.changed` | `manual_posted` | filial + request | após o update retornar |
| Vínculo de PC na criação | `use_cases.py:430-431` | `lnf.request.changed` | `purchase_order_linked` | filial + request | após o commit desse vínculo |
| Vínculo de PC depois | `use_cases.py:855-856` | `lnf.request.changed` | `purchase_order_linked` | filial + request | após o commit desse vínculo |
| Comentário | use case `:1426`; history em `postgres_invoice_posting_repository.py:1121-1122` | `lnf.request.changed` | `comment_added` | filial + request | após `add_comment` retornar |
| Match SF1 no refresh | `use_cases.py:1631-1636` chama o batch; history `:798-799` (`actor_origin=system`) | `lnf.request.changed` por solicitação e `lnf.queue.reconciled` por filial com contagem > 0 | `reconciled` | filial + request; fila por filial | após `mark_reconciled_posted_batch` retornar |
| Match SF1 no run | rota `router.py:1198-1205`; mesmo batch | igual ao refresh | `reconciled` | igual | após o batch retornar |
| Produtos sem código | `UnmappedSupplierProductRecorder.record` grava em `unmapped_supplier_product_service.py:120`, chamado depois do create em `received_invoice_attachment_service.py:126-153`. Não há job nem update dessa tabela. | `lnf.unmapped-products.changed` só se o insert persistiu ao menos uma linha | — | `lnf:unmapped-products` | após o insert retornar. Falha do insert não emite e não desfaz a solicitação |

Transação revertida: o notifier não é chamado. `divergence_detected`: N/A, sem writer.

## 2.10 Comportamento do MFE

Estado de tela continua `useState` + carga HTTP. Sem React Query, sem polling novo, sem `POST /reconciliation/refresh` disparado por evento (isso faria laço refresh → evento → refresh).

| Fluxo | Sala | Ao receber | O que não fazer |
|---|---|---|---|
| Fila | `lnf:branch:{filial da rota}` | em `lnf.request.changed` ou `lnf.queue.reconciled`, debounce ~1s e refazer só `GET /requests` com os filtros e a página atuais. Atualizar «Fila carregada em» e o rótulo de conciliação. Preservar filtros, página e rolagem. | não chamar refresh; não trocar de página |
| Detalhe | `lnf:request:{id}` | refetch do detalhe. Se o rascunho do comentário tiver texto, ou se block/cancel/post-manual estiver aberto, mostrar aviso discreto e aplicar ao fechar. | não apagar rascunho nem fechar modal |
| Edição | `lnf:request:{id}` | banner «Esta solicitação foi alterada por outra pessoa» com ação Recarregar. | não sobrescrever o que está sendo digitado |
| Produtos sem código | `lnf:unmapped-products`, só com a permission | refetch da página e dos filtros atuais | não assinar sem a permission |
| Notas recebidas, downloads, PCs em aberto no modal, sino | — | sem canal | busca sob demanda, blob sob clique, e o sino segue no shell |

A própria ação também gera evento. Debounce e dedupe por `eventId` (janela curta) evitam o segundo refetch. `createEventDispatcher` em `realtimeSocket.ts:157-189` já faz dedupe por `eventId`; o wrapper pode usá-lo sem mudar o plugin-ui.

Conexão:

- backoff exponencial com jitter, de 1s até 30s;
- na reconexão, refetch da tela atual e reenvio das salas desejadas;
- aba oculta: **igual ao `RealtimeSocketClient`, que não olha `document.hidden`**. A conexão e o `ping` (~25s, o intervalo default do cliente em `realtimeSocket.ts:24`) continuam. Não inventar pausa de aba.
- indicador discreto: «Ao vivo» / «Reconectando…» / «Atualização automática indisponível». Não bloqueia a tela. PT-BR, claro/escuro, foco visível, `aria-live` polido.
- Não existe componente de indicador de conexão no plugin-ui. `StateBanner` é o banner de falha do kit (`padrao-visual-portais-minha-delpi.md:362`), não um selo «Ao vivo». O selo fica no MFE. O estado indisponível pode usar `StateBanner` se couber sem cobrir a fila. Não criar primitivo novo no plugin-ui nesta frente.
- Base no api-delpi ou `VITE_LNF_REALTIME_ENABLED` off: zero tentativas de conexão e sem mensagem de erro.

## 2.11 Gateway (desenho; implementação na W3)

Location **mais longa** que o prefixo atual, para o `^~` existente não capturar o socket:

```text
location ^~ /apps/controllership-finance-api/lancamento-notas-fiscais/realtime
```

Nos três arquivos: `gateway/nginx.conf` (PROD), `gateway/nginx.dev.conf` (DEV), `gateway/snippets/hml-proxy-locations.conf` (HML).

Nessa location, e só nela:

- `proxy_http_version 1.1`;
- `Upgrade` e `Connection` iguais às locations que já falam WS (ex.: requests, `nginx.conf:451-453`);
- `proxy_read_timeout 86400`;
- `proxy_buffering off`;
- `access_log` com `tv_access_sanitized`, que já redige o parâmetro `token` (`nginx.conf:29-40`).

O bloco `location ^~ /apps/controllership-finance-api/` não muda.

W3 publica DEV e HML. O bloco de PROD entra no arquivo, mas não sobe para o servidor enquanto a W6 não tiver F5c DONE.

## 2.12 Ajuda

Na W4, `plugins/lancamento-notas-fiscais/src/content/helpTooltips.ts` ganha o significado do indicador e o fato de a fila se atualizar sozinha. Hoje o arquivo só tem `newRequest` e `unmappedProducts`.

Não há artigo `/help` do app (busca no plugin, no portal e em docs de help na W0, reconfirmada na W1). Criar esse artigo é decisão separada, fora desta frente.

## 2.13 Critérios de aceite

BFF:

- sem token, o cliente não conecta; token inválido ou expirado no handshake → 1008;
- sem permissão mínima → 1008 e o cliente não reconecta enquanto o token for o mesmo;
- só `view.filial-01` assinando `lnf:branch:02` → `forbidden_room`, conexão aberta;
- `lnf:request` de solicitação da outra filial, ou id inexistente → `forbidden_room`;
- evento da 02 não é entregue a socket que só assinou a 01;
- rollback da transação → nenhum evento;
- exceção do notifier não muda o status HTTP da escrita;
- conexão aceita fecha no `exp` (+ folga de 5s) com 1000;
- `LNF_REALTIME_ENABLED` off, ou hosted off → rota inexistente.

Gateway (DEV e HML):

- handshake recebe 101 Switching Protocols;
- a linha de access log dessa location não contém o JWT.

MFE, duas sessões, dois usuários:

- ação em A aparece em B em até 2s, em cada fluxo da §2.10 que tem sala;
- rascunho de comentário e formulário em edição não são sobrescritos;
- reconexão refaz a tela atual;
- base no api-delpi, ou flag do MFE off → zero tentativas de WebSocket;
- socket derrubado → fila, detalhe e ações HTTP seguem iguais a hoje.

## 2.14 Fases

Cada fase: brief → execução → report → revisão. Este contrato não executa nenhuma.

| Fase | Entrega | Ambiente |
|---|---|---|
| W2 | Port, hub, rota, emissão pós-commit, testes da §2.13 no BFF | DEV |
| W3 | Location dos três arquivos de gateway; publicar só DEV e HML | DEV/HML; PROD só no arquivo |
| W4 | MFE: fila → detalhe → formulário → produtos sem código, mais `helpTooltips.ts` | DEV |
| W5 | Ensaio com dois usuários e o negativo de filial | HML |
| W6 | PROD | entrada = F5c DONE no quadro da trilha 165 |
| W7 | Job periódico de conciliação | decisão própria, depois do F5c |

## 2.15 Riscos e rollback

Desligar `LNF_REALTIME_ENABLED` e `VITE_LNF_REALTIME_ENABLED` volta ao comportamento atual: HTTP na carga e nas ações.

Isso continua compatível com o rollback da trilha 165 até o F6. Se a BFF do LNF for desligada e o MFE voltar para api-delpi, o socket não é tentado.

Escalar a BFF sem broker e com a flag ligada perderia eventos entre processos. A restrição da §2.3 existe para isso.

## 2.16 Ajustes por causa de R1–R4

### R1 — ENG-REALTIME-01

Status no documento: **IMPLEMENTADO**, não DRAFT nem ACCEPTED (`ENG-REALTIME-01-websocket-transversal-prc-plano.md:3`). Escopo: Engineering API, reutilizável por outros fluxos **dessa** API; PRC é o primeiro consumidor (`:8` e `:17`). O Socket.IO da Core fica de fora (`:32`).

Protocolo que ele fixa e que este contrato acompanha onde não colide com o LNF:

- WebSocket FastAPI, hint + refetch, publicação depois da escrita persistida (`:13`, `:71`);
- `ping` texto / `pong` JSON; subscribe e unsubscribe em JSON; erro de sala não fecha o socket (`engineering_realtime_protocol.py:1-10`, hub `:139-140`);
- fechamento no `exp`, com +5s (`realtime_routes.py:141-144`);
- flag do serviço, default capaz de ficar off sem derrubar a transação (`ENG-REALTIME-01` §4.1).

Não é protocolo de salas do LNF. Lá a sala é `domain` + `resourceId`, não `lnf:branch`.

### R2 — `RealtimeSocketClient`

`realtimeSocket.ts` é transporte genérico: `buildUrl()` opaca, subscribe como string opaca, ping fixo, reconnect com intervalo fixo default 4s (`:25` e `:91-97`), dedupe por `eventId` no helper ao lado. Não lê token, não aplica jitter, não lê close code, não olha aba oculta.

`engineeringRealtime.ts` está acoplado à Engineering (path `/v1/realtime/ws`, domínio PRC, tipo `engineering.resource.changed`).

Não há indicador de conexão no plugin-ui (busca em `plugins/plugin-ui/src` por componente de realtime: só o cliente e o helper da Engineering).

**Opções, sem escolher mudança no plugin-ui nesta frente:**

| Opção | O que é | Por que não é o default da W4 |
|---|---|---|
| Generalizar `RealtimeSocketClient` | backoff com jitter, respeito a 1008, política de token renovado | mexe no kit compartilhado com Engineering e PRC; esta frente não autoriza esse diff |
| Wrapper local no MFE | WebSocket próprio com o protocolo da §2.6 e a política da §2.10; pode importar `createEventDispatcher` | é o caminho que cumpre o contrato sem alterar `plugin-ui` |

A W4 implementa o wrapper local. Generalizar o kit fica para uma decisão posterior, se um segundo consumidor pedir a mesma política.

### R3 — close codes encontrados

| Código | Onde aparece | Uso |
|---|---|---|
| 1008 | `requests-api/.../realtime_routes.py:53-119`, `engineering-api/.../realtime_routes.py:65-116` | token inválido, sem permissão, flag do engineering off |
| 1000 | hubs, idle e `_close_at` do engineering (`engineering_realtime_hub.py:137` e `:157`) | conexão já aceita que encerra |
| 4401 | não está no código desses módulos | — |
| 1011, 1001 | não estão nos hubs; 1011 é default do Starlette em endpoint que estoura | — |

Por isso a §2.5 troca 4401 por 1008 e o exp por 1000. 1011 e 1001 permanecem só onde o R3 não achou padrão (erro interno e shutdown).

### R4 — produtos sem código

Writer único: `UnmappedSupplierProductRecorder.record` (`unmapped_supplier_product_service.py:71-134`), insert em `:120`, chamado no fim do create com NF-e (`received_invoice_attachment_service.py:126-153`). Sem job e sem update. Leitura: `GET /unmapped-products` exige `lancamento-notas-fiscais.review-unmapped-products` (`router.py:573-576`). O evento da §2.8 existe por causa desse writer.
