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

**Estado:** `DECISION_REQUIRED / INVENTORY_COMPLETE_FOR_DECISION`.

Inventário documentado em:
- [36-e04-t04-package-delivery-decision-packet.md](./36-e04-t04-package-delivery-decision-packet.md).

Proven:
- necessidade de encaminhar package por recipient no processo;
- Microsoft Graph e-mail + file attachments no runtime;
- Message Trace `delivered/bounced/unknown` em CIPA/Transformômetro;
- Core Notifications existe, mas `NOTIFICATION_DISPATCHED != PACKAGE_SENT`;
- Delpi Reports envia relatórios por e-mail, mas não é generic package-delivery contract.

Não provado:
- canal AS-IS atual;
- owner corporativo único de package delivery;
- generic delivery service reutilizável;
- semântica aprovada de `PACKAGE_SENT` entre Graph accepted vs Message Trace delivered.

Decisões abertas:
- `D-P5-DELIVERY-OWNER`;
- `D-P5-PACKAGE-SENT-OUTCOME`.

Recomendação ainda **não aplicada**:
- owner/orchestration em P5/BFF;
- Graph + Message Trace como adapters;
- `PACKAGE_SENT` somente após `DELIVERED`.

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
NOTIFICATION_DISPATCHED != PACKAGE_SENT
```

T02 não fecha E04/T04.

## T03 — Cutoff / STOCK_CLOSED

Verificar estado canônico do owner.

Se não existir/for incompatível → EXECUTION_DRIFT.

## T04 — Capability corporativa de envio

**Estado:** `INVENTORY_COMPLETE_FOR_DECISION`.

Resultado:
- transport Graph com attachments = PROVEN;
- retry de transport = PROVEN;
- Message Trace = PROVEN em bounded contexts reais;
- generic package delivery owner/service = NOT_PROVEN;
- Delpi Reports generic delivery = NOT_PROVEN;
- Core Notifications como package-delivery owner = NOT_PROVEN.

T04 deixa de ser busca aberta e passa a sustentar a decisão E04.

Authority:
- [36-e04-t04-package-delivery-decision-packet.md](./36-e04-t04-package-delivery-decision-packet.md).

## T05 — Core RBAC

Mapear:
- ACCESS;
- MANAGE;
- resource ownership/context access;
- effective permissions;
- fail-closed quando a resolução do Core estiver indisponível.

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
- E04/T04 não suportarem envio;
- T05 conflitar com ACCESS/MANAGE;
- owner não for identificável;
- nova evidência invalidar TARGET.
