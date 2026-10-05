# 12 — P5 — Pacote, Finalização e Envio

## Invariante

```text
READY_TO_FINALIZE
!= PACKAGE_FINALIZED
!= PACKAGE_SENT
!= MONTHLY_CLOSING_COMPLETED
```

## Finalizar

Finalizar cria snapshot/version.

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED_V1
```

Não envia e não conclui o mês.

## Correção antes do envio

```text
FINALIZED_V1
→ REOPEN_WITH_REASON
→ WORKING_COPY
→ FINALIZED_V2
```

V1 permanece histórica.

## Pacotes por destinatário

Uma competência permanece única e gera pacotes/visões por destinatário.

Exemplos:
- Contábil;
- Fiscal.

Cada pacote avança independentemente.

## Envio parcial

Permitido por destinatário.

Enviar Fiscal não implica Contábil enviado.

## Canal

Q22 = PENDING_IMPLEMENTATION.

Depende:
- E04 canal real;
- T04 capability corporativa.

Não assumir e-mail, pasta, Teams ou mecanismo próprio.

## Aceite do destinatário

Não obrigatório no target atual.

Read/ack opcional não bloqueia conclusão.

## Esclarecimentos

Por destinatário:

```text
PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ CLARIFICATION_RESOLVED
```

## Correção após envio

Pacote enviado é imutável.

```text
PACKAGE_SENT_V1
→ COMPLEMENT_OR_NEW_VERSION
→ LINK_TO_V1
→ NEW_DELIVERY
```

Motivo obrigatório.

## Conclusão

```text
ALL_APPLICABLE_RECIPIENT_PACKAGES_SENT
AND
NO_OPEN_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Sem botão independente de força.

## Auditoria

- PACKAGE_VERSION_CREATED
- PACKAGE_FINALIZED
- PACKAGE_REOPENED
- PACKAGE_SENT
- CLARIFICATION_OPENED
- CLARIFICATION_RESOLVED
- PACKAGE_COMPLEMENT_CREATED
- MONTHLY_CLOSING_COMPLETED

## Edge cases

- destinatário sem itens;
- READY_TO_FINALIZE com source falha;
- envio parcial;
- reabertura antes do envio;
- correção pós-envio;
- falha de canal;
- destinatário sem aceite formal.
