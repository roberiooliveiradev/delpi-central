# 13 — P6 — Administração e Configuração

## Contrato da página

A especificação completa de UX, rotas, contracts lógicos, plugin-ui, estados, AuthZ, auditoria e testes da superfície administrativa está em [28-administracao.md](./28-administracao.md).

Este documento permanece authority das regras funcionais P6.

## Template mestre

```text
DRAFT
→ REVIEW
→ PUBLISH
→ EFFECTIVE_FROM
```

Salvar não publica.

## Snapshot

Competência aberta continua associada à versão vigente na abertura.

Nova publicação não altera:
- competência aberta;
- histórico;
- pacote existente.

## Inativação

Sem delete físico.

```text
ACTIVE → INACTIVE_FROM(date)
```

Exige motivo, ator, timestamp e vigência.

## Publicação

Um MANAGE pode publicar sozinho com auditoria/versionamento.

Segundo MANAGE não é obrigatório no target atual.

## Catálogos configuráveis

- bancos/contas;
- checklist items;
- requirement;
- origin;
- recipients;
- operational responsible;
- validator;
- satisfaction rule;
- validation scope;
- notification targets;
- attachment roles;
- extensões de motivos;
- vigência.

`CONFIGURABLE != FREE_FORM_EVERYWHERE`.

ACCESS usa opções existentes; MANAGE administra.

## Lista bancária

```text
BANK_LIST = CONFIGURABLE
HARDCODE = NO
```

E01 define seed/owner, não arquitetura.

## Motivos de rejeição

Núcleo estável + extensões MANAGE.

Inativação é prospectiva; histórico preserva códigos usados.

## Attachment roles

Catálogo reutilizável.

Anexo genérico continua permitido quando não houver role formal obrigatório.

## Auditoria

- TEMPLATE_DRAFT_CREATED
- TEMPLATE_DRAFT_UPDATED
- TEMPLATE_VERSION_PUBLISHED
- MASTER_ITEM_CREATED
- MASTER_ITEM_UPDATED
- MASTER_ITEM_INACTIVATED
- CONFIG_CATALOG_ITEM_CREATED
- CONFIG_CATALOG_ITEM_INACTIVATED
