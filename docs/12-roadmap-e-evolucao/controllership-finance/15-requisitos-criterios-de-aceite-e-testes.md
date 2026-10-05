# 15 — Requisitos, Critérios de Aceite e Testes

O ledger detalhado por página está em [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md). Os ACs específicos de paridade P3 permanecem em [15.1-p3-criterios-paridade-monetaria.md](./15.1-p3-criterios-paridade-monetaria.md).

## Famílias de requisitos

### P1
Cobrir competência/unidade, eixos independentes, blockers, freshness, deep links, histórico, IA e experience states.

### P2
Cobrir snapshot, requirement/origin/scope, recipients, satisfaction, anexos, validação, N/A, rejeição, substituição, multi-anexo, item excepcional, correção estrutural, notificações e ACCESS/MANAGE.

### P3
Cobrir preliminary, cutoff, revalidação, conciliação, readiness e canonical STOCK_CLOSED.

### P4
Cobrir sugestão, confirmação humana, filas, claim/reassign, states, resolução e dismiss.

### P5
Cobrir package version, finalize, reopen, recipient packages, partial send, clarification, correction after send e completion.

### P6
Cobrir draft/publish/effective_from, snapshot immutability, inactivation, catalogs, audit e permission.

## Critérios indispensáveis

- STOCK_CLOSED + REQUIRED pendente → pacote incompleto;
- último documento satisfeito → não auto-send;
- pre-cut zero → não final;
- source indisponível → não zero;
- PACKAGE_SENT + clarification → não complete;
- mudança mestre → snapshot intacto;
- rejected evidence → preservada;
- replacement → nova validação;
- OPTIONAL rejected → não blocker global;
- WHOLE_SET alterado → aceite anterior não reaproveitado;
- nova versão após rejeição → reversal antiga bloqueada;
- correction request stale → sem auto-apply;
- CANCELLED → sem delete/reativação;
- PACKAGE_SENT → imutável.

## Matriz de testes

### Positive
Happy path e transições válidas.

### Sibling
Outra unidade/item/destinatário não deve ser afetado indevidamente.

### Negative
Permission, scope, state e payload inválidos.

## Segurança

Testar:
- sem ACCESS;
- ACCESS sem MANAGE;
- cross-unit;
- validator indevido;
- MANAGE fora do scope;
- IA fora do scope;
- tentativa de delete de histórico;
- tentativa de contornar state machine.

## Experiência

Por página:
- loading;
- empty;
- partial;
- unavailable source;
- error;
- 403;
- 404;
- desktop/mobile;
- claro/escuro;
- teclado/foco;
- deep link/F5 quando aplicável.

## Evidência de execução

Reportar:
- BASE HEAD;
- FINAL HEAD;
- STATUS;
- FACTS PROVEN;
- TO_INVENTORY;
- EXECUTION_DRIFT;
- arquivos;
- contratos;
- testes;
- segurança;
- cobertura RQ/AC;
- residual search;
- unresolved;
- next step.
