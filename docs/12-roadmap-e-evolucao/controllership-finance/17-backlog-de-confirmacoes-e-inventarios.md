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

Necessário para Q22.

Confirmar:
- canal;
- formato;
- comprovante;
- aceite;
- segurança;
- capability disponível.

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

Mapear:
- API/event;
- templates;
- destinatários;
- preferences;
- e-mail;
- delivery status;
- retry/failure;
- deep links.

## T03 — Cutoff / STOCK_CLOSED

Verificar estado canônico do owner.

Se não existir/for incompatível → EXECUTION_DRIFT.

## T04 — Capability corporativa de envio

Inventariar serviços para:
- documentos;
- e-mail;
- tracking;
- retry;
- proof of delivery.

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
