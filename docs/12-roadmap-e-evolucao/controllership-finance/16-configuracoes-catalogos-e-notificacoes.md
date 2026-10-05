# 16 — Configurações, Catálogos e Notificações

## Princípio

Listas operacionais mutáveis não devem ser hardcoded.

Configuração deve ser versionável e auditável.

## Catálogos

### Bancos/contas
Configurável por empresa/unidade.

E01 define seed/owner.

### Motivos de rejeição
Núcleo padrão + extensões MANAGE.

### Attachment roles
Reutilizáveis, com anexo genérico quando permitido.

### Validator / responsible / recipient
Selecionáveis dentre opções autorizadas.

### Notification targets
- OPERATIONAL_RESPONSIBLE
- UPLOADER
- CONFIGURED_ROLE_OR_RECIPIENT

## Notificações

Superfície canônica: **Minha DELPI**.

O Portal gera o evento/notificação de negócio.

O e-mail reutiliza a configuração existente da plataforma.

```text
PORTAL_NOTIFICATION != EMAIL_IMPLEMENTATION
```

Não criar SMTP próprio ou opt-in paralelo.

## Eventos V1

Além de rejeição/reversão:
- STRUCTURAL_CORRECTION_REQUESTED;
- STRUCTURAL_CORRECTION_APPROVED;
- STRUCTURAL_CORRECTION_REJECTED;
- REVALIDATION_REQUIRED;
- WAITING_FOR_THIRD_PARTY;
- PACKAGE_READY;
- PACKAGE_SENT.

`READY_TO_FINALIZE` é estado do pacote. `PACKAGE_READY` é evento de notificação emitido quando esse estado é alcançado; não é um segundo estado.

## Reversão de rejeição

A notificação de reversão usa os mesmos destinatários efetivos da rejeição original.

Não apagar a notificação anterior.

## Falha de entrega

Falha de e-mail/notificação:
- não altera estado de negócio;
- não reverte rejeição;
- não cancela correção;
- permanece auditável.

## Sem SLA formal

```text
FORMAL_SLA = NO
DUE_DATE = NO
OVERDUE = NO
SLA_BREACH = NO
TIME_BASED_ESCALATION = NO
PENDING_SINCE = YES
```

Mostrar "pendente desde" e idade factual.

Não mostrar atraso/SLA sem nova decisão.

## Acknowledgement

Não obrigatório no V1.

Se a plataforma registrar leitura, ela é informativa e não bloqueia.

## Auditoria

Registrar triggering event, destinatário resolvido, timestamp, delivery status e correlation quando disponível.
