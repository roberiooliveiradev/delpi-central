# 17 — Backlog de Confirmações e Inventários

```text
PENDING_IMPLEMENTATION != OPEN_PRODUCT_DESIGN
```

## E01 — Lista bancária inicial

Confirmar seed, banco/conta, unidade/empresa e owner.

Já decidido: lista configurável, sem hardcode.

Não fazer union silencioso de fontes históricas divergentes.

## E02 — Correção pós-sacramentação

**Estado Gate V2:** `CLOSED / PRODUCT_DECISION`.

Decisão aprovada em 09/10/2026:

```text
STOCK_CLOSED
= terminal no lifecycle P3 do Portal V1
```

Contrato:
- Portal V1 não reabre estoque após `STOCK_CLOSED`;
- Portal V1 não desfaz sacramentação;
- Portal V1 não cria workflow local de retificação pós-fechamento;
- qualquer correção posterior pertence ao owner canônico/ERP;
- histórico do fechamento original permanece imutável no Portal;
- eventual novo estado/artefato posterior só pode ser refletido quando fornecido pelo owner;
- suporte futuro a reabertura/retificação exige novo gate de produto e revisão P3/P5.

Classificação:

```text
OPEN_PRODUCT_DESIGN = NO
IMPLEMENTATION_INVENTORY = NO
FUTURE_EXPANSION = NEW_GATE_IF_REQUIRED
```

## E03 — Executor/permissões de sacramentação

Confirmar roles, scopes, rotina owner e segregações.

## E04 — Canal real de envio

**Estado:** `CLOSED / PRODUCT_CLARIFICATION`.

Decisão/clarificação:
- package permanece dentro da Minha DELPI;
- "Enviar" = submeter/disponibilizar para reviewers autenticados;
- e-mail é somente notification channel;
- nenhum package attachment é enviado por e-mail na V1.

Authority:
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md).

```text
EXTERNAL_PACKAGE_DELIVERY = NOT_REQUIRED_IN_V1
```

## D-P5-REVIEW-COMPLETION — C2 aprovada pelo PO

**Estado:** `CLOSED / PO_APPROVED_C2_P5-A..J_DEC-01..04`, sem escolha C1/C2/C3 pendente. C1 e C3 permanecem apenas histórico.

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED_FOR_REVIEW
AND EVERY_REQUIRED_AREA_ACCEPTED_CURRENT_PACKAGE_VERSION
AND NO_OPEN_CLARIFICATION
AND NO_TERMINAL_COMPETENCE_REJECTION
→ MONTHLY_CLOSING_COMPLETED
```

A área obrigatória é configurada no P6 por tipo de pacote e congelada no snapshot da submissão; um único aceite válido por área/versão satisfaz quórum. `REVIEW_REJECTED` pela área não encerra automaticamente competência: decisão formal DEC-01/02 do coordenador com ACCESS/vínculo/scope e motivo. Sem confirmação fica pendente; erro de aceite não possui reversão de UI/endpoint V1 (DEC-03). Core T05 grupo/função e binding de P6 permanecem técnicos `TO_INVENTORY`. Authority [37](./37-p5-submissao-e-revisao-no-portal.md).

## E05 — Attachment roles reais

Modelo configurável já fechado.

Confirmar seed e obrigatoriedade.

## E06 — Cobertura dos motivos de rejeição

Modelo núcleo + extensões já fechado.

Confirmar seed inicial.

## T01 — DAVI / api-delpi

Mapear:
- endpoints;
- campos;
- sources;
- freshness;
- erros;
- scope;
- owner.

Não inventar campos físicos.

## T02 — Notificações Minha DELPI

**Estado:** `CAPABILITY_PROVEN / PRODUCT_ADAPTER_TO_INVENTORY`.

Rebaseline de 09/10/2026 no Core:

- `POST /integrations/notifications` existe;
- S2S via service token;
- rate limit existe;
- recipients e filtros por effective permissions existem;
- `sourceApp` e action target existem;
- inbox/history/preferences do usuário existem.

Não criar capability paralela.

Inventariar por evento do Controladoria:
- category/template;
- destinatários/recipient resolution;
- payload e dados permitidos;
- `sourceApp=controllership-finance` ou valor canônico aprovado;
- action target/deep link;
- required permission filter usando apenas permission codes canônicos;
- delivery status/retry/failure aplicável ao Core adapter.

Invariantes:

```text
NOTIFICATION_FAILURE != BUSINESS_STATE_CHANGE
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
```

T02 não fecha E04/T04.

## T03 — Cutoff / STOCK_CLOSED

Verificar estado canônico do owner.

Se não existir/for incompatível → EXECUTION_DRIFT.

## T04 — Capability corporativa de envio

**Estado:** `CLOSED / NOT_REQUIRED_IN_V1`.

A investigação de Graph/Reports/Message Trace permanece como evidence histórica no documento 36, mas não é requisito P5.

O capability relevante à V1 é T02:
- Core Notifications;
- inbox Minha DELPI;
- e-mail de notification quando habilitado.

## T05 — Core RBAC

Mapear:
- ACCESS e MANAGE como códigos distintos;
- Core effective permissions S2S, grupos RBAC existentes e a fonte/contrato **corporativo** de grupo/função para área elegível P5;
- vínculo operacional do coordenador DEC-01 e resource scope/ownership na BFF;
- fail-closed quando Core/elegibilidade/função não puderem ser resolvidos.

**PROVEN no HEAD:** endpoint S2S de effective-access responde permission codes, mas não envia grupos/funções; `GET /me/access-profile` traz grupos para o titular. **TO_INVENTORY:** contrato S2S de elegibilidade corporativa adequado ao P5. Não copiar banco/roles Core nem criar permission por reviewer.

Decisão de produto já fechada:

```text
BRANCH_PERMISSION_CODES = NO
UNIT_SCOPE_PERMISSION_MODEL = NOT_APPLICABLE
```

Filial/unidade pode ser filtro/dimensão do dado, mas não permission code dedicado deste Portal.

## Stop conditions

Parar e escalar quando:
- E02 contradizer state model;
- T03 invalidar canonical state;
- P5 tentar depender de entrega externa de anexos (E04/T04 NOT_REQUIRED_IN_V1);
- T05 conflitar com ACCESS/MANAGE;
- owner não for identificável;
- nova evidência invalidar TARGET.
