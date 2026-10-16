# 16 — Configurações, Catálogos e Notificações

A superfície de gestão desses catálogos está especificada em [28-administracao.md](./28-administracao.md). Este documento permanece authority das regras de configuração/notificação.

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

Rebaseline de plataforma em 09/10/2026:

```text
CORE_NOTIFICATION_CAPABILITY = PROVEN
```

O Core atual expõe integração S2S `POST /integrations/notifications`, protegida por service token e rate limit, com recipients, `sourceApp`, action target e filtros por effective permissions.

Isso fecha a existência da capability de notificação. Ainda é necessário, por evento do produto, definir adapter/payload/template/category/deep-link e recipient resolution.


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
- PACKAGE_SUBMITTED_FOR_REVIEW.

`READY_TO_FINALIZE` é estado do pacote. `PACKAGE_READY` é evento de notificação emitido quando esse estado é alcançado; não é um segundo estado.

## Reversão de rejeição

A notificação de reversão usa os mesmos destinatários efetivos da rejeição original.

Não apagar a notificação anterior.

## Falha de entrega

```text
NOTIFICATION_DISPATCHED != PACKAGE_SUBMITTED_FOR_REVIEW
NOTIFICATION_FAILURE != BUSINESS_STATE_CHANGE
```

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


## P5 — notifications de review

Após `PACKAGE_SUBMITTED_FOR_REVIEW`, P5 emite evento para Core Notifications.

A plataforma pode entregar:
- inbox Minha DELPI;
- e-mail conforme configuração/preferência/capability vigente.

Contrato:

```text
EMAIL = NOTIFICATION_CHANNEL
EMAIL != PACKAGE_TRANSPORT
EMAIL_ATTACHMENT_PACKAGE = NO
NOTIFICATION_FAILURE != PACKAGE_SUBMISSION_FAILURE
```

O action target aponta para deep link interno do recipient package. O acesso é reautorizado no Portal/BFF.
