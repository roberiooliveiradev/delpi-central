# ADR-002 — Tempo real do LNF por WebSocket na BFF

| Campo | Valor |
|---|---|
| Status | **ACCEPTED** |
| Data | 2026-11-13 |
| Decisor | owner do produto |
| Contexto | Lançamento de Notas Fiscais hospedado na `controllership-finance-api` |
| Relacionados | [Doc 167](../167-lnf-tempo-real-websocket.md) `CONTRACT_DRAFT` · [ADR-001](./ADR-001-hospedagem-lancamento-notas-fiscais.md) · [Trilha 165](../165-trilha-execucao-migracao-lnf-ate-clara.md) |

O contrato de mensagens, salas e fases está no doc 167. Este ADR só registra a decisão e as alternativas recusadas.

## Contexto

A W0 (HEAD `7f332cb39b`) mostrou que a plataforma já tem WebSocket FastAPI por API de produto (aviso + refetch HTTP, hub na memória do processo, JWT na query) e um Socket.IO da Core só para o sino. O LNF não tem nenhum dos dois. A fila só atualiza na carga e no `POST /reconciliation/refresh` de quem abriu a tela. O F6 da trilha 165 ainda não acabou: o MFE precisa continuar correto apontando para a api-delpi.

## Decisão

Tempo real do LNF por WebSocket nativo na BFF, no módulo de lançamento de notas, como canal aditivo de invalidação.

| Id | Decisão |
|---|---|
| D-W1 A | O JWT vai na query `token` do handshake. A location do gateway que servir esse path redige `token` no access log, no mesmo formato das locations de TV. |
| D-W2 A | O hub fica na memória do processo da BFF. Subir workers ou réplicas acima de 1 exige broker antes; até lá a flag de realtime permanece desligada. |
| D-W3 C | Não nasce job de conciliação agora. Refresh e run que já existem emitem aviso para as telas da filial. Job periódico é a W7, com decisão própria, depois do F5c. |
| D-W4 A | DEV e HML agora. PROD só depois que o quadro da trilha 165 marcar F5c DONE. |

Completam a decisão, pela evidência da W0 e sem reabrir:

- o dono do canal é a BFF, não a Core e não o hub do Fechamento;
- o evento carrega identificadores, e a tela relê por HTTP;
- a sala é autorizada na assinatura com a mesma regra do HTTP;
- a emissão é depois do commit e best-effort;
- sem socket, o app permanece o de hoje, obrigatório até o F6;
- o servidor encerra a conexão no `exp` do JWT;
- a location de gateway é nova e estreita, só no path `/realtime`.

## Alternativas rejeitadas

| Alternativa | Por que não |
|---|---|
| Socket.IO da Core | O Core entrega o sino (`admin.changed`). Não conhece solicitação nem filial do LNF e não é o owner do módulo. |
| Ticket de uso único no lugar do JWT | Não é o padrão dos WS de produto. O owner escolheu a query `token` com redação de log. |
| `Sec-WebSocket-Protocol` para carregar o token | O mesmo: o padrão vigente é a query, e o browser que esses MFEs usam já manda o token assim. |
| Redis (ou outro broker) agora | A BFF roda em um processo. Broker novo seria outra autoridade sem necessidade atual. A restrição fica escrita para o dia em que houver workers ou réplicas. |
| Job periódico de conciliação agora | A detecção de NF lançada no Protheus continua na abertura da fila e no run manual. Automatizar isso é outra decisão (W7), depois do hypercare. |
| Publicar em PROD durante o F5c | O corte da trilha 165 ainda está em estabilização. O realtime em PROD espera F5c DONE. |

## Consequências

- W2–W6 implementam o doc 167. Este ADR não autoriza o diff sozinho.
- O rollback do canal é desligar `LNF_REALTIME_ENABLED` e `VITE_LNF_REALTIME_ENABLED`.
- O rollback da trilha 165 (MFE de volta à api-delpi, BFF do LNF desligada) continua válido: o MFE não tenta socket quando a base não é a BFF.
- Close codes e o cliente seguem os ajustes do doc 167 §2.16: a plataforma usa 1008 no handshake e 1000 ao expirar a conexão já aceita; o `RealtimeSocketClient` não implementa o backoff do LNF, então o MFE usa wrapper local em vez de alterar o plugin-ui nesta frente.
- Quem só tem `lancamento-notas-fiscais.review-unmapped-products` entra no socket por causa dessa permission, e não assina sala de filial sem `branch_view_allowed`.
