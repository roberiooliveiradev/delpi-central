# 26 — Sala de Interação

## Estado

**TARGET / CONTRACT_INVENTORY_REQUIRED**

## Objetivo

A **Sala de interação** é a superfície de comunicação contextual do Portal Controladoria & Finanças.

Ela deve permitir colaboração vinculada ao contexto de trabalho, sem criar um chat genérico paralelo e sem se tornar owner das regras do processo.

## Referência de plataforma

O Portal Comercial possui uma superfície `interaction-rooms` com inbox + detalhe de sala.

Para este Portal, o padrão pode ser reutilizado em arquitetura de informação, navegação inbox/detalhe, experiência, realtime quando aplicável e componentes compartilháveis.

Não copiar regras do domínio Comercial.

## Rota lógica

```text
/apps/controllership-finance/interaction-rooms
/apps/controllership-finance/interaction-rooms/{roomId}
```

Ambas usam `controllership-finance.access`.

## Modelo conceitual

```text
InteractionRoom
├── context
├── participants
├── messages
├── references
├── events
└── audit metadata
```

O contrato físico ainda é `TO_INVENTORY`.

## Contextos possíveis

Uma sala pode estar ligada, quando o contract aprovado permitir, a competência de fechamento, checklist item, evidência/documento, pendência, classificação, pacote, esclarecimento ou outro objeto futuro do Portal.

A relação precisa ser explícita por referência estável.

## Invariantes

```text
MESSAGE != BUSINESS_DECISION
COMMENT != VALIDATION
COMMENT != APPROVAL
COMMENT != STOCK_CLOSURE
COMMENT != PACKAGE_SEND
```

Uma mensagem não altera estado de negócio por si só.

Ações de processo continuam nas páginas owners.

## Composição lógica

```text
InteractionInbox
→ RoomList
→ RoomWorkspace
→ ContextSummary
→ MessageTimeline
→ ReferencePanel
→ ContextualHelp
```

## Inbox

Deve permitir localizar salas relevantes ao usuário.

Filtros só podem existir quando suportados pelo contract, como contexto, status, participante e período.

Não criar estados/SLA sem regra aprovada.

## RoomWorkspace

Deve mostrar contexto vinculado, participantes, timeline, autor/timestamp, referências e estado de disponibilidade do contexto.

Se o objeto referenciado não puder mais ser acessado, não vazar dados via mensagem/cache.

## Participantes e segurança

Acesso à sala deve respeitar `controllership-finance.access`, resource ownership/context access e business rule aplicável.

Não criar permission por sala.

Participar de uma sala não concede automaticamente acesso ao recurso vinculado.

## Realtime

Realtime é capability técnica, não requisito de negócio por si só.

Inventariar o padrão da plataforma antes de decidir WebSocket/SSE, polling, eventos, presença e notificações.

Se realtime não estiver disponível, a experiência deve continuar funcional com estratégia suportada pelo padrão vigente.

## Notificações

Notificações relacionadas à Sala devem usar a capability canônica da Minha DELPI.

Não criar preference store ou SMTP próprio.

## IA

Pode resumir conversa autorizada, localizar decisões explicitamente registradas, sugerir investigação e ligar mensagens a evidências autorizadas.

Não pode transformar conversa em decisão de negócio automaticamente.

## Auditoria

Registrar, quando aplicável, criação de sala, mudança de participantes, mensagem, referência vinculada, mudança de contexto e correlation.

Política de edição/exclusão de mensagens é `TO_INVENTORY`; não inventar.

## Estados

Cobrir `LOADING`, `EMPTY`, `ERROR`, `FORBIDDEN`, `NOT_FOUND`, recovery de conexão quando houver realtime e contexto referenciado indisponível.

## Help

Explicar o que é Sala de interação, diferença entre mensagem e ação do processo, como abrir o contexto, visibilidade/participantes e limites da IA.

## Inventário obrigatório

Antes da implementação:
- inventariar a capability `interaction-rooms` do Portal Comercial;
- identificar se existe serviço/contrato reutilizável ou se é domínio local;
- identificar modelo de realtime atual;
- identificar ownership de mensagens/attachments;
- identificar notificações relacionadas;
- definir política de retenção/edição com authority adequada.

Se o padrão Comercial estiver acoplado ao domínio Comercial, reutilizar apenas experiência/componente, não persistence/domain.
