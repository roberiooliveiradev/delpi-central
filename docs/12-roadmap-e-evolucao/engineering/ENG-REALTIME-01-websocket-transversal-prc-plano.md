# ENG-REALTIME-01 — Tempo real transversal da Engineering API (PRC como primeiro consumidor)

> **Data da decisão de planejamento:** 2026-11-12
> **Status:** **IMPLEMENTADO (backend + ambos os MFEs) — evidência de execução na seção 11.**
> **Issue de coordenação:** [delpi-central#154](https://github.com/roberiooliveiradev/delpi-central/issues/154).
> **Repo:** \`roberiooliveiradev/delpi-central\`, branch \`main\`.
> **Owner:** Engenharia / Engineering API; **consumers iniciais:** \`plugins/engineering\` e \`plugins/my-requests\`.
> **Objetivo:** atualizar automaticamente listas, detalhes, histórico e transições do cadastro de produtos/matérias-primas (PRC), reutilizando o padrão de WebSocket já existente em Minhas Solicitações, com infraestrutura **reutilizável por outros fluxos da Engineering API**.
> **Regra:** inteligência ampla + autoridade estreita, explícita e governada. WebSocket é transporte de invalidação, não source of truth, permissão, workflow ou canal de gravação.

## 1. Contexto e decisão funcional

Quando uma pessoa cria um caso PRC em Minhas Solicitações, um analista inicia/devolve/conclui no Portal Engenharia, ou o solicitante corrige e reenvia, os dois MFEs deverão atualizar sua UI **sem F5**. A publicação ocorre **somente depois de escrita oficial persistida**; o cliente recebe um aviso leve e executa **HTTP refetch autorizado**.

**Não criar outro cadastro, workflow, BFF, fonte de verdade ou runtime dependente dos internals de \`requests-api\`.** PRC permanece na **Engineering API**, acessada pelos dois MFEs. O WebSocket da \`requests-api\` continua atendendo aos chamados do bounded context de Requests; o evento da \`requests-api\` não representa alteração do caso PRC.

**Decisão de extensibilidade:** o mecanismo de conexões, assinatura, validação, roteamento, publicação, telemetria e reconexão na Engineering API será transversal. O PRC provê o **primeiro adapter de domínio real**. Futuras LMPs/solicitações/outros fluxos só aderem mediante contrato e authorization policy de seus respectivos owners. **Não** inventar enums, handlers de negócio ou salas futuras antes de consumer real.

## 2. Inventário factual (PROVEN por inspeção do código em 12/11/2026; revalidar HEAD antes de execução)

| Componente | Fonte canônica | Evidência / limite |
|---|---|---|
| WebSocket em Requests API | \`requests-api/requests_app/application/services/requests_realtime_{hub,notify,protocol}.py\`; \`interface/http/routes/realtime_routes.py\` | Hub nativo FastAPI com \`user:{sub}\`, \`work-queue\`, \`request:{id}\`, subscribe/unsubscribe, ping, AuthN/RBAC/escopo no join, eventos \`request.created/changed/timeline\` |
| Contrato / documentação existente | \`requests-api/docs/architecture/realtime-requests.md\` | \`WS hint + debounce + HTTP refetch\`; diferenciado de outbox → sino Core; \`REQUESTS_REALTIME_ENABLED\`; porta/gateway WS |
| Cliente My Requests | \`plugins/my-requests/src/app/MyRequestsRealtimeProvider.tsx\`; \`constants/realtime.ts\` | 25 s ping, 4 s reconexão, 400 ms debounce, join/leave de caso, rejoin após reconnect, eventos de criação/alteração/histórico, \`client_id\` para suprimir toast próprio |
| Lista unificada My Requests | \`plugins/my-requests/src/pages/MinePage.tsx\` | \`useMyRequestsListSync\` reage apenas ao provider Requests, embora a lista agregue \`requests-api\` + PRC via Engineering API |
| Detalhe PRC My Requests | \`plugins/my-requests/src/features/product-registration/PrcCasePage.tsx\`; \`prcApi.ts\` | Carrega caso/timeline/anexos por HTTP da Engineering API; não foi encontrada subscription WS PRC |
| Fila/detalhe Engenharia | \`plugins/engineering/src/features/product-registration/pages/PrcQueuePage.tsx\`, \`PrcDetailPage.tsx\` | \`fetchPrcQueue\` e função \`load\` do detalhe; atualização hoje por navegação/ação/refetch manual, sem WS PRC identificado |
| Escritas PRC | \`engineering-api/engineering_app/application/use_cases/product_registration/service.py\` | Repositório oficial implementa criação, transições, rascunho, devolução, correção, reenvio, informação, flags, anexo, revisão etc.; CAS/idempotência em operações críticas |
| FastAPI Engineering | \`engineering-api/engineering_app/main.py\`, \`middleware/auth_middleware.py\`, \`interface/http/routes/product_registration_routes.py\` | Nenhum WS PRC/hub identificado nesse inventário; AuthN por \`delpi_auth\` e regras PRC próprias |
| Gateway | \`gateway/nginx.conf\`, \`gateway/nginx.dev.conf\` | Rotas \`/apps/engineering-api/\` já têm headers Upgrade e timeouts WS; validar HML/produção e handshake real |
| Core Socket.IO | \`docs/01-arquitetura/event-driven-e-socket.md\` | Plataforma possui eventos pós-commit e Socket.IO para necessidades Core; **não** autoriza substituir ownership da Engineering API nem depender de eventos administrativos para PRC |

**Importante:** os nomes de salas, DTOs, paths e flags PRC citados adiante são **TARGETs candidatos**, a congelar em contrato após levantamento de multi-worker, escopo e mecanismo real pós-commit. A existência de \`RequestsRealtimeHub\` é **referência técnica**, não licença para import entre APIs.

## 3. Arquitetura e ownership

\`\`\`text
Keycloak (identidade)                  Core (RBAC/permissões)
      │                                       │
      └───────────────┬───────────────────────┘
                      ▼
  Engineering API — autoridade das operações PRC
      │ Use case/domain PRC → repository/UoW → commit e versão
      │                      │
      │                      └─ event intent / adapter neutro pós-commit
      ▼
  Realtime port + adapter da Engineering API (sem dependência Domain→FastAPI/WS)
      │ authorize subscription (policy do domínio)
      │ hub/rooms/publish/fan-out/observabilidade
      ▼
  Gateway WS (/apps/engineering-api/...)
      ├─────────────────────────────┐
      ▼                             ▼
  MFE Engineering              MFE My Requests
  queue / case / timeline      lista unificada / caso PRC
      └──────── HTTP refetch autorizado ───────┘

  requests-api → Requests WS existente → My Requests (outros chamados)
  Core/outbox → sino/notifications persistentes (canal separado)
\`\`\`

**Ownership preservado:**
- Keycloak: AuthN/SSO; Core: RBAC; Engineering API: AuthZ por objeto/escopo, transições/estado, dados, versão e emissão PRC; MFE Engineering: operação legítima de analista; My Requests: entrada/acompanhamento do solicitante; gateway: upgrade; \`@delpi/plugin-ui\`: apresentação neutra, **não hospeda** socket, tokens nem regras de negócio.
- No backend, Domain/Application **não** dependem de FastAPI, WebSocket, SDK, DB ou \`requests-api\`; contrato/port neutro + adapter de infraestrutura somente se necessário (Abstraction Gate).
- Event bus corporativo, broker, Redis ou Redis Streams **não entram por padrão**; inventariar topologia e equivalente já existente. Caso precise nova infraestrutura, formalizar decisão de arquitetura antes de criar autoridade/ownership.

## 4. Contrato alvo de tempo real (a fechar antes de codificar)

### 4.1 Transporte e sessão
- Adotar WebSocket nativo FastAPI **como o Requests existente**, não criar Socket.IO PRC separado. Endpoint candidato, por exemplo \`/apps/engineering-api/v1/realtime/ws\`, sujeito a prefixos reais, política de segurança e documentação OpenAPI/infra.
- Handshake JWT validado pelo mecanismo oficial, load de permissões Core em tempo de conexão **e** guardas fail-closed. Não confiar em claims/permissões apenas do frontend, token query/provider scope ou em presença de sala.
- Revisar transporte do token: padrão Requests usa \`token\` na query; se reutilizado, limitar exposição em logs, traces, URLs de observabilidade, gateway e documentação; não persistir token em armazenamento/telemetria.
- \`ping/pong\`, heartbeat, reconexão, limpeza de sockets mortos, subscribe/unsubscribe e rejoin; tratar token expirado/renovação e logout.
- Feature flag específica do serviço (candidata \`ENG_REALTIME_ENABLED\`), com fallback para HTTP/manual refresh, sem causar falha de transação de negócio se o transporte estiver indisponível.

### 4.2 Salas e AuthZ
- Salas conceituais: \`user:{sub}\`, \`engineering:<domain>:queue\`, \`engineering:<domain>:case:{uuid}\`. **Namespacing final sujeito ao contrato**. Não reaproveitar o namespace de \`requests-api\` como se fosse a mesma fonte.
- \`subscribe\`/ \`unsubscribe\` com confirmação/erro, UUID e resourceType válidos, limite de assinaturas/rate limit e verificação de live AuthZ **por objeto** ao entrar na sala.
- Para fila, verificação de permissão de leitura/atendimento **e escopo real**; nunca broadcast aberto de case IDs/status de objetos não autorizados. Se for impossível definir room segura para uma fila de escopos mistos, segmentar por policy ou usar hints direcionados por destinatário autorizado.
- Revogação/perda de acesso: estratégia explícita para revalidação periódica/antes de entrega, fechamento/expulsão de sala, respostas HTTP 403/404 após refetch; teste de revogação sem reconectar.
- Diferenciar autorização do requester e do analista, pessoas de dupla role, filial quando aplicável e fontes permitidas; emissão não transfere direito de leitura.
- Nenhum cliente publica eventos de negócio. Socket aceita apenas subscribe/unsubscribe/keepalive e controles explicitamente autorizados.

### 4.3 Envelope leve
Contrato conceitual, não um DTO implementado:
\`\`\`json
{
  "type": "engineering.resource.changed",
  "domain": "product-registration",
  "resourceType": "request",
  "resourceId": "uuid",
  "reason": "correction_resubmitted",
  "version": 5,
  "eventId": "opaque-id",
  "occurredAt": "2026-11-12T10:00:00Z"
}
\`\`\`
- Reutilizar \`request.created\`/\`request.changed\`/\`request.timeline\` como **semântica de referência**, sem colisão ambígua com os eventos Requests. Validar compatibilidade e nomes antes de definir.
- Publicar somente IDs/versão/motivo classificado; **não** transportar ficha, Part Number, fornecedores, documentos, razões sensíveis, usuários não autorizados, tokens ou conteúdo técnico.
- \`eventId\`/versão ajudam dedupe/ordenação, mas se não houver evidência de necessidade de campo novo, manter envelope mínimo; o backend HTTP é sempre a verdade.
- Suprimir toast duplicado da própria aba via identificador de client, quando disponível; **não** suprimir o refetch que garanta consistência.

### 4.4 Entrega e pós-commit
- **Persistir primeiro; sinalizar depois que o commit é confirmado**. Não publicar se 4xx, CAS 409, rollback, write falhou ou idempotent replay sem novo outcome.
- Investigar todas as escritas PRC e seu retorno \`replayed\`: intake; \`PATCH /draft\`; transições \`start/resume/return\`; devolução; \`PATCH /returned-fields\`; reenvio; rodadas de esclarecimento; verificações/flags; anexos; conclusão/rejeição; revisões. Classificar impacto \`list\`, \`detail\`, \`timeline\` por operação (não enviar um evento por tecla/campo).
- Distinguir \`commit persistido\` de \`HTTP 200 devolvido\`. Se a publicação no service ocorrer antes da persistência durável, reestruturar o hook/port para **after commit**. Em múltiplas réplicas, coordenar estratégia de fan-out/durabilidade com infraestrutura já governada, sem dupla escrita ou dependência do banco da Requests API.
- Falha de publicar WS não desfaz mutação confirmada; registrar métrica/error e recuperar por refetch em reconexão/foco/manual. Não prometer exactly-once; trabalhar com at-least-once/best-effort conforme decisão de topologia.
- Não duplicar notificações Core: WS atualiza UI aberta; sino permanece um canal separado e governado.

## 5. Aplicação no frontend — reutilização sem acoplamento

### 5.1 Base existente
\`plugins/my-requests/src/app/MyRequestsRealtimeProvider.tsx\`:
- \`ping\` ~25 s, reconnect ~4 s, debounce ~400 ms, join/leave e rejoin por \`requestId\`; hooks \`useMyRequestsListSync\` / \`useMyRequestsDetailSync\`.
- Mantê-lo **intacto para Requests**, salvo extração neutra justificada com testes; PRC **não** deve se inscrever no socket Requests e esperar evento que lá não existe.

### 5.2 Componentização candidata
- Preferência: **um cliente de transporte/hook neutro reutilizável**, se o Abstraction Gate comprovar owner, consumers e ausência de equivalente. Extração dos mecanismos comuns (connect/reconnect/heartbeat, desired subscriptions, debounce, evento hint). Não mover regras de AuthZ, notificação ou APIs para \`plugin-ui\`.
- \`plugins/engineering\`: provider/adaptador de realtime Engineering escopado ao MFE, com assinatura do caso/fila e refetch pelos clients HTTP existentes.
- \`plugins/my-requests\`: mantém provider Requests **e** integra fonte Engineering PRC ao contexto/lista unificada; não uma conexão extra por card/componente, mas uma por serviço com ciclo controlado. Resolver coexistência de tokens, reconexões, visibilidade e limpeza no unmount.
- Não introduzir dependência runtime de \`engineering\` em \`my-requests\` ou vice-versa. Contrato compartilhado apenas se a neutralidade e ownership estiverem comprovados.

### 5.3 UX e consistência
- **Engineering fila:** invalidar \`fetchPrcQueue\`; manter filtros URL, paginação, sort, kanban/tabela e seleção sem reset; debounce e anti-race.
- **Engineering detalhe:** invalidar \`fetchPrcRequest\`, timeline, verificações, anexos/revisões impactados; preservar aba, seleção e texto não salvo.
- **My Requests lista:** invalidar a parte PRC da lista **sem destruir** os estados Requests; garantir composição/paginação consistente após mudança remota.
- **My Requests PRC detalhe:** chamar loader HTTP existente para caso, timeline, documentos, apenas quando autorizado; mostrar novas permissões/estados devolvidos sem F5.
- **Edição aberta:** nunca sobrescrever draft local silenciosamente. Sinalizar que há versão remota, proteger formulário, oferecer recarregar/descartar de forma explícita; CAS continua validando writes.
- **Reconnect/visibility:** rejoin das salas e refetch de reconciliação no connect/reconnect e retorno à aba, não depender de replay completo de eventos.
- **Eventos própria aba:** evitar toast duplicado; não eliminar invalidação que mantenha outras abas e listas coerentes.
- **Falha WS:** interface segue utilizável por HTTP, manual refresh e retry, sem falso indicador de atualização garantida.

## 6. Matriz de eventos e invalidação (TARGET)

| Operação PRC | Engenharia fila | Engenharia detalhe | My Requests lista | My Requests PRC detalhe |
|---|---|---|---|---|
| Intake CREATE/UPDATE | refetch | se aberto | refetch | se aberto |
| Start/resume/transição/status | refetch | refetch | refetch | refetch |
| Editar draft em submitted | conforme impacto | refetch | conforme impacto | refetch |
| Devolver para correção | refetch | refetch | refetch | refetch |
| Salvar alvos devolvidos | conforme impacto | refetch | conforme impacto | refetch |
| Reenviar correção | refetch | refetch | refetch | refetch |
| Solicitar/responder esclarecimento | refetch | refetch | refetch | refetch |
| Anexo/comentário/evento histórico | conforme impacto | timeline/docs | conforme impacto | timeline/docs |
| Verificação, flag, revisão | conforme impacto | seção afetada | conforme impacto | seção afetada |
| Completar/rejeitar | refetch | refetch | refetch | refetch |

**Contrato alvo de eficiência:** categorizar \`created\`, \`changed\`, \`timeline\` ou equivalente e \`reason\`, deduplicar eventos para evitar múltiplos GETs; evitar recarregar catalogs/reference-data estáticos a cada evento quando não impactados.

## 7. Topologia/gateway — gates antes de escrever código

**TO_INVENTORY:**
1. Workers/replicas por serviço em DEV/HML/PROD: instância única vs escala horizontal, persistência e idempotency storage. O hub Requests é **process-local**; não assumir broadcast entre processos.
2. Equivalente de pub/sub, Core event bus, Redis/infra da plataforma já disponíveis; escolher solução mínima que preserve entrega entre instâncias, se necessária.
3. Compatibilidade \`gateway/nginx.conf\`, \`nginx.dev.conf\`, \`nginx.hml.conf\`: Upgrade, Connection, rota, timeout e buffering; proxy correto para WebSocket e TLS.
4. Lifetime de JWT e política Core AuthZ revogação, suporte de browser ao envio seguro de credenciais no handshake.
5. Logs/observabilidade (nunca registrar query/token), limite de sockets/conexões, número máximo de rooms, idle timeout, limitação de mensagens, backlog, reconexões.
6. Possibilidade de reutilizar contratos neutros oficiais de conexão em \`packages\` ou infraestrutura atual. Se não houver, reutilizar padrão sem dependência entre APIs.

**DECISION GATE:** se a única solução confiável exigir novo broker/owner ou transferir authority, classificar \`ARCHITECTURE_DECISION_REQUIRED\` e voltar à Coordination; executar partes independentes seguras.

## 8. Sequência de implementação proposta

1. **F0 Inventário e contrato:** HEAD/status/authorities; mapear fontes, writers, lifecycle, idempotência, perfis AuthZ, gateways, escala e equivalentes compartilhados; matriz RQ/AC.
2. **F1 Port/contrato:** abstração mínima de evento/realtime (domain-neutral) e policies por domínio, sem importar FastAPI/Requests em domain/application; mensagem, erro, subscribe/ack, versões/limites e testes de contrato.
3. **F2 Engineering API:** endpoint WS com AuthN/RBAC/live object AuthZ; hub e transporte; adapter de publisher pós-commit nas escritas PRC, feature flag, métricas; testes de replay, CAS, não-evento em falha e revogação.
4. **F3 Frontend compartilhado:** extrair somente conexão/subscribe/reconnect/debounce úteis do padrão My Requests, se contrato real o justificar; não quebrar o provider Requests.
5. **F4 Engineering MFE:** contexto realtime e sync de fila e detalhe, resguardando edição ativa, filtros, abas e races.
6. **F5 My Requests MFE:** integrar provider de Engineering à lista unificada/detalhe PRC, mantendo Requests WS atual sem duplicação de conexões nem notificações.
7. **F6 Testes/entrega:** backend positivo/negativo e concorrência, frontend unit/integração, três identidades (A criador, B terceiro, C analista), 2 abas, reconexão, token expire, revogação, multi-instância quando aplicável, smoke gateway e E2E autenticado, documentação/issue/ledger. \`TEST_NOT_RUN\` quando não executado.

## 9. Critérios de aceite (PENDING)

- **AC-01:** operações PRC persistidas publicam eventos leves, corretos, **após commit**, sem falso evento em erro/rollback/CAS/idempotent replay.
- **AC-02:** PRC usa Engineering API como owner, sem espelhar na Requests API; nenhuma importação cross-bounded-context.
- **AC-03:** endpoint AuthN fail-closed, subscribe de caso com live AuthZ, usuário terceiro negado, fila segmentada pelo escopo.
- **AC-04:** revogação em conexão ativa é bloqueada, incluindo entrega futura; teste de perda de acesso sem reconectar.
- **AC-05:** Engineering fila e detalhe refletem status/histórico sem F5 e sem perda de filtros/abas/draft.
- **AC-06:** My Requests lista unificada recebe sinais das **duas fontes**, e detalhe PRC atualiza sem F5; eventos Requests não sofrem regressão.
- **AC-07:** reconexão, resubscribe e refetch de reconciliação; fallback HTTP quando WS cai.
- **AC-08:** no máximo a quantidade necessária de sockets por serviço/microfrontend; debounce/dedupe e ausência de loops de refetch.
- **AC-09:** sem toast próprio duplicado; separação WS vs notificações Core persistidas.
- **AC-10:** gateway DEV/HML compatível; política para escala multi-worker explícita e comprovada (ou bloqueio de escala até solução).
- **AC-11:** AuthZ do refetch continua backend-first, eventos não carregam ficha/dados confidenciais nem tokens; observabilidade sanitizada.
- **AC-12:** tests unitários, integração, browser autenticado e matriz A/B/C/duas abas + controle de concorrência no SHA efetivo; reportar evidência por \`PASS|FAIL|PENDING|TEST_NOT_RUN|INCONCLUSIVE\`.
- **AC-13:** contrato e infra de realtime Engineering podem admitir um segundo domínio real sem reescrever hub/handshake/protocolo (testado com adapter neutro simulado, **sem implantar fluxo fictício**).
- **AC-14:** ausência de regressão nas policies PRC REF-022/023: \`submitted\`, \`in_progress\`, \`needs_correction\`, estado terminal, requestId, CAS e idem.

## 10. Segurança / antiobjetivos

- Não criar novo módulo de Engineering, novo bounded context, novo BFF ou API paralela.
- Não usar \`requests-api\` como transport relay PRC sem contrato e autorização governados.
- Não publicar para toda fila com escopos heterogêneos; não confiar em room membership estática para revogação.
- Não emitir antes do commit, no replay idempotente ou após erro HTTP.
- Não transportar payload técnico completo ou secrets em eventos.
- Não acoplar hub genérico a \`supplierCode\`, Part Number, estado específico REF-022, banco PRC ou imports de TSX.
- Não transformar WebSocket em autorização ou canal de escrita.
- Não criar persistência de eventos/broker/Redis sem evidência e decisão de owner.
- Não sobrescrever edição local nem supor exactly-once.
- Não confundir Socket.IO Core (plataforma) com WebSocket FastAPI Requests (referência concreta).

## 11. Evidência e status

| Item | Estado |
|---|---|
| Requests WS e provider frontend | **PROVEN** (código inspecionado; preservado intacto) |
| Gateway headers Engineering em DEV/PROD | **PROVEN** (configuração textual; handshake real em gateway \`TEST_NOT_RUN\`) |
| Engineering API WS transversal | **PROVEN** — \`engineering_app/interface/http/routes/realtime_routes.py\` (\`/v1/realtime/ws?token&client_id\`), hub \`application/services/engineering_realtime_hub.py\`, protocolo \`engineering_realtime_protocol.py\`, port \`application/ports/realtime.py\`, feature flag \`ENG_REALTIME_ENABLED\` |
| Publisher PRC pós-commit | **PROVEN** — emissão em \`service.py\` após mutação + \`save_idempotent\`; replay idempotente não reemite; falhas de validação/concorrência não emitem |
| AuthZ de subscription + revogação | **PROVEN** — \`can_observe\` do service reexecutado na assinatura e a cada entrega; \`tests/test_eng_realtime.py\` cobre A/B/C, revogação em conexão ativa e payload mínimo |
| Cliente neutro \`@delpi/plugin-ui\` | **PROVEN** — \`plugin-ui/src/realtime/{realtimeSocket,engineeringRealtime}.ts\` (ping 25 s, reconnect 4 s, rejoin, dedupe por \`eventId\`, debounce) |
| Portal Engenharia fila/detalhe | **PROVEN** — \`EngineeringRealtimeProvider\` + \`usePrcQueueSync\`/\`usePrcCaseSync\`; refetch HTTP oficial; rascunho preservado durante edição |
| My Requests lista/detalhe | **PROVEN** — \`PrcRealtimeProvider\` separado (socket Engineering); \`usePrcListSync\` no \`MinePage\` e \`usePrcCaseSync\` no \`PrcCasePage\`; provider Requests intacto |
| Testes backend | **PROVEN** — \`tests/test_eng_realtime.py\` 14 testes (hub, protocolo, AuthZ, revogação, replay, validação, payload); regressão PRC 203 passed |
| Testes frontend | **PROVEN** — \`realtimeSocket.test.ts\` 5 testes (heartbeat, reconnect, rejoin, dedupe/debounce); MFEs: eng 364/364, my-requests 190/192 (2 falhas \`process-issue\` pré-existentes, fora do escopo) |
| E2E autenticado A/B/C no browser | **TEST_NOT_RUN** — não executado; fluxo coberto por testes de integração TestClient |
| Multi-instância | **BLOCKED** — hub é process-local (1 worker uvicorn, mesma premissa do Requests); scale-out exige decisão arquitetural (\`ARCHITECTURE_DECISION_REQUIRED\`) |

**Definition of Done:** revalidar SHA, contratos, owners, código e políticas na execução; testes em SHA efetivo, residual search, docs/issue e outcome real. Este documento **não é autorização para alterar runtime**, não é promessa de entrega, nem substitui as authorities atuais. Se houver mudança de owner/authority, \`ARCHITECTURE_DECISION_REQUIRED\`.

## 12. Fontes de consulta

- [Requests WS existente](../../../requests-api/docs/architecture/realtime-requests.md).
- [Padrão event-driven e Socket.IO Core](../../01-arquitetura/event-driven-e-socket.md) — fonte canônica: \`docs/01-arquitetura/event-driven-e-socket.md\`.
- \`requests-api/requests_app/application/services/requests_realtime_hub.py\`
- \`requests-api/requests_app/application/services/requests_realtime_notify.py\`
- \`requests-api/requests_app/interface/http/routes/realtime_routes.py\`
- \`plugins/my-requests/src/app/MyRequestsRealtimeProvider.tsx\`
- \`plugins/my-requests/src/pages/MinePage.tsx\`
- \`plugins/my-requests/src/features/product-registration/PrcCasePage.tsx\`
- \`plugins/engineering/src/features/product-registration/pages/PrcQueuePage.tsx\`
- \`plugins/engineering/src/features/product-registration/pages/PrcDetailPage.tsx\`
- \`engineering-api/engineering_app/application/use_cases/product_registration/service.py\`
- \`engineering-api/engineering_app/interface/http/routes/product_registration_routes.py\`
- \`engineering-api/engineering_app/main.py\`
- \`gateway/nginx.conf\`, \`gateway/nginx.dev.conf\`, \`gateway/nginx.hml.conf\`.
