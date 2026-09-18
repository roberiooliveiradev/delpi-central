# Core app unit scope — implementation packet

> Fase 1 apenas. **IMPLEMENTATION = NOT AUTHORIZED.**  
> ADR: [`adr-core-authorization-portal-units.md`](../../../transformometro-api/docs/architecture/adr-core-authorization-portal-units.md)

## Goal

Gravar, no Core, o vínculo de quais unidades do Portal Transforma+ um papel, grupo ou usuário pode usar. Sem catálogo de filial. Sem mudar o manifesto.

## Owner

Core API. Persistência no banco do Core. Projeção em `GET /me`, já consumido por `load_user_rbac`.

## Canonical source

`PermissionResolver` une papéis diretos e papéis de grupo. `user_permissions.granted` faz override de permission, não de escopo. `audit_logs` já guarda ator, ação, entidade e payload. Apps entram pelo manifesto, id `transformometro`.

## Current state

Não há tabela de escopo. `/me` devolve permissions, roles, groups e `is_superadmin`. Filial vive só em `transformometro.filiais` (`deletado`, `status_filial`).

## Target state

Uma linha por sujeito e aplicação. Sujeito: role, group ou user. Aplicação: id opaco do manifesto. Modo: `none` | `units` | `all`. Em `units`, lista de `codigo_filial` sem metadata. Nomes de tabela e coluna seguem o estilo das tabelas de assignment já existentes. Não estão congelados neste texto.

## Domain model

O Core não ganha entidade Filial. O valor é um identificador opaco. `all` e `units` são modos diferentes. Override de usuário substitui a união de papéis e grupos. União entre papéis: `all` absorve listas.

## Application use cases

Atribuir escopo. Ler escopo efetivo do principal. Não validar existência da filial.

## Ports

Repositório novo no Core, ao lado dos repositórios de permission. Nenhum port do Transformômetro.

## Persistence

Migration nova no Core. Sem FK para outro banco. Sem SQL em `transformometro`.

## Migration

Tabela vazia. Não copiar `branch.filial-*` nesta fase. Copiar assignment é fase 7, depois da matriz humana.

## API / projection

Estender o JSON de `/me` com o modo e, se `units`, os códigos. Sem objeto filial. Nome do campo na implementação, olhando o contrato atual de `/me`.

## Authorization

Só quem já administra RBAC no Core altera o vínculo. O resolver de permission não chama HTTP do Transformômetro.

## Audit

`audit_logs`: quem alterou, principal, aplicação, escopo anterior, escopo novo.

## Core /me impact

Um bloco pequeno por aplicação que tenha linha. Cache atual, default 60s (`DELPI_AUTH_RBAC_CACHE_TTL_SECONDS`). Revogação usa o mesmo invalidate do resolver de permission. Cache não é eterno. Falha do Core continua zerando permissions. Escopo ausente nessa falha é nenhuma unidade.

## Transformômetro consumer contract

Fase 3. Se `/me` trouxer linha, usar só ela. Se não trouxer, usar `branch.*`. Nunca unir. Código desconhecido ou filial inativa: ignorar e logar. Não abrir o resto.

## Compatibility

Fase 1 não muda o comportamento do portal. O consumer ainda não lê o campo.

## Dual-read precedence

Definida para a fase 3. Fase 1 não ativa dual-read.

## Tests

Sem linha não projeta `all`. `units` não vira `all`. Override substitui. Dois papéis unem. `all` absorve. Revogação sai do cache dentro do TTL ou no invalidate.

## Negative tests

Código opaco não é consultado no banco do portal. Request de permissão não chama o Transformômetro. Rollback da projeção não liga `all`.

## Runtime acceptance

Fora desta fase. Fase 1 termina com teste do Core e `/me` em ambiente de review, sem deploy obrigatório deste pacote.

## Rollback

Parar de projetar o campo e deixar de escrever a tabela. Assignments de permission não são apagados. Ausência volta a significar “consumer ainda não migrou”, não “todas as unidades”.

## Risks

Cache de 60s atrasa revogação, igual às permissions de hoje. Administrador sem a unidade no próprio escopo não a vê em `list_filiais`.

## Gaps

Nomes físicos de coluna. Jornada de UI para atribuir unidade fora do escopo de quem administra.

## DoR

| Gate | Estado |
|---|---|
| CORE OWNER | PROVEN |
| SCOPE MODEL | DECIDED |
| PERSISTENCE OWNER | PROVEN |
| NO CROSS DB | PROVEN como restrição |
| CONTRACT | DECIDED na semântica |
| PRECEDENCE | DECIDED |
| AUDIT | DECIDED |
| MIGRATION | READY para tabela vazia |
| TESTS | READY no papel |
| ROLLBACK | READY |
| TRANSFORMOMETRO CONSUMER | DECIDED para a fase 3 |

**CORE_UNIT_SCOPE_PHASE_1 = READY_FOR_IMPLEMENTATION_REVIEW.** Implementação ainda não autorizada.
