# 17 — Backlog de Confirmações e Inventários

```text
PENDING_IMPLEMENTATION != OPEN_PRODUCT_DESIGN
```

## E01 — Lista bancária inicial

Confirmar seed, banco/conta, unidade/empresa e owner.

Já decidido: lista configurável, sem hardcode.

Não fazer union silencioso de fontes históricas divergentes.

## E02 — Correção pós-sacramentação

**Estado Gate V2:** `DECISION_REQUIRED / DOCUMENTATION_BLOCKER`.

Reclassificação em 06/10/2026:
- a evidência AS-IS/TÉO atual confirma sacramentação do estoque;
- a decomposição/process docs consultados não definem reabertura, retificação ou correção depois de `STOCK_CLOSED`;
- portanto E02 pode alterar lifecycle P3/P5 e não pode permanecer escondido como mero binding de implementação.

Precisa fechar antes de `A10 = READY_FOR_IMPLEMENTATION_BRIEF`:
- existe reabertura?
- quem autoriza?
- quais correções são possíveis?
- o que precisa revalidar?
- como fica a competência?
- impacto em pacote finalizado/enviado;
- qual evidência/auditoria?
- se não existir correção/reabertura no Portal V1, formalizar `STOCK_CLOSED` como terminal para o Portal e preservar correções exclusivamente no owner.

Não escolher uma alternativa por preferência arquitetural.

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
