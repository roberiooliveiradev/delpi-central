# Portal Transforma+ — autorização final

> **Status:** desenho corrigido. Não é runtime.
> **IMPLEMENTATION = NOT AUTHORIZED.**
> **AUTHZ_MIGRATION = READY_FOR_IMPLEMENTATION_REVIEW.**
> A fase de assignment continua bloqueada até a matriz humana ser aprovada.

## EXECUTION_DRIFT

Premissa anterior, em `680b24a62` e `ce458acf2`: principal → aplicação → unidades autorizadas.

**Invalidada.** O Portal Transforma+ é multiunidade e não segrega autorização por unidade. Quem tem acesso vê todos os processos. Unidade é objeto e filtro analítico, não escopo de permissão.

O pacote [CORE-APP-UNIT-SCOPE-PACKET.md](./CORE-APP-UNIT-SCOPE-PACKET.md) está **CANCELLED_BY_BUSINESS_DECISION**. O ADR anterior fica superado: [`adr-core-authorization-portal-units.md`](../../../transformometro-api/docs/architecture/adr-core-authorization-portal-units.md).

## Autoridade

Keycloak autentica. A Core API decide `transformometro.access` e `transformometro.manage`. O Transformômetro não concede permissão. Ele valida a operação de domínio e pode negar o que o Core autorizou. Não pode liberar o que o Core negou.

Filial não entra nessa decisão. `transformometro.filiais` continua só no Transformômetro. O Core não cadastra, não referencia, não audita e não projeta unidade. `GET /me` não ganha campo de unidade.

Frontend, TÉO, MCP e GPT Actions não autorizam. Não há tool nem Action nova.

`manage` não implica `access`. O `PermissionResolver` não tem hierarquia. Quem administra recebe os dois códigos.

## Permissions finais

Só estas:

- `transformometro.access` — uso normal do portal, em todas as unidades.
- `transformometro.manage` — administração e configuração do produto.

Saem, no alvo: processo, revisão, medição, investimento, recurso, ata, assinatura, recálculo, transferência, filial e consolidado.

Sem `access`, nega. Com `access`, o produto inteiro, inclusive processos de qualquer unidade. Código `branch.*` não participa. Não se restaura «sem filial → vê tudo» como regra de escopo. A capability é que abre o produto.

## Filial

Objeto de domínio. Na Visão geral, o filtro Todas / 01 / 02 / futuras muda a consulta. Não muda quem pode ver. O catálogo do filtro vem de `filiais`. Sem chamada de autorização ao Core.

Consolidado é Todas. `view.consolidated` sai. Não é capability.

## Domínio

Processos: `access` lista todos. «Meus processos» é o nome da área, não a lista das unidades do usuário. Cargo, perfil e departamento não filtram.

Mestre: `access` mais a regra de negócio. Não há interseção de unidades nem exigência de escrever só se todas as unidades ligadas estiverem no escopo.

Sem instância: `access` lê. Escrita normal é `access` mais a regra de negócio. Não há fallback de filial.

Instância, revisão, medição e investimento continuam ligados à unidade como contexto do dado. Isso não autoriza nem esconde.

Ata: `access`. Assinar exige ser signatário, estado assinável e ainda não ter assinado. A unidade da ata não limita a permissão.

Exportar/importar, recálculo pedido pelo usuário, recursos compartilhados, filiais, departamentos e configurações: `manage`. Preview, validação, confirmação de replace e read-back permanecem. O hook interno de recálculo depois de uma escrita não é esse comando.

`manage` sem `access` não abre a raiz do portal. Rotas de administração exigem `manage`. Os dois códigos são explícitos.

## O que o código faz hoje

`FilialAccessScopeService` está no caminho de autorização. Consumidores: `branch_access_http` (`check_*`, `filter_rows_for_access`, `require_unrestricted_catalog_admin`), `crud_routes`, `dashboard_routes`, `meeting_minutes_service`, `transformometro_routes` (`/options`), `dispatch_service`, `process_context_service`, `orchestrator`. Testes em `test_branch_access_scope_service.py`.

| Superfície | Hoje | Alvo | Migrar |
|---|---|---|---|
| Lista de processos | filtra pela filial do papel | `access` vê todos | sim |
| Dashboard | `check_dashboard_filial_access` | filtro analítico, sem negar unidade | sim |
| Atas | `can_view_filial` / `can_manage_filial` | `access`; assinar pela regra do signatário | sim |
| `/options` | esconde filial fora do papel | catálogo para o filtro, com `access` | sim |
| Writes de instância | `check_manage_filial_access` | `access` + regra de domínio | sim |
| Catálogo de filial | `require_unrestricted_catalog_admin` | `manage` | sim |
| GPT/MCP | os mesmos helpers | o mesmo contexto do HTTP | sim |

O serviço sai da autorização. Se sobrar helper só de filtro de consulta, não pode se chamar de autorização. Não apagar no mesmo diff da fundação se ainda houver caller.

## OLD → NEW

| Atual | Alvo |
|---|---|
| `view` | `access` |
| `processes.manage`, `revisions.manage`, `measurements.manage`, `investments.manage` | `access` + regra de domínio |
| `meeting-minutes.view`, `meeting-minutes.manage` | `access` + regra de domínio |
| `meeting-minutes.sign` | `access` + signatário e estado |
| `atas.*` | sai com os canônicos de ata |
| `shared-resources.manage`, `dashboard.recalculate`, `data.transfer` | `manage` |
| `view.consolidated` | sai; é o filtro Todas |
| `branch.filial-*`, `view.filial-*`, `manage.filial-*` | sai |

## Manifesto proposto

Não aplicar.

Raiz `/apps/transformometro`, label Portal Transforma+, `access`, `showInMenu: true`. Visão geral, Meus processos, atas, minha assinatura e, quando existirem, sala, tarefas e ajuda: `access`. Administração, configurações e exportar/importar: `manage`.

A TopBar não cria permission e não muda com a filial. Uso normal: `access`. Administração: `manage`.

## Papéis

Produção, inventário anterior: papel Transforma Mais, 21 códigos, 4 usuários, grupo Supervisor Engenharia, zero grant direto. Não reconsultar neste passe. Não inferir `manage` pelo nome.

| Principal ou grupo | access | manage | Aprovador | Status |
|---|---|---|---|---|
| 4 usuários do papel Transforma Mais | — | — | — | UNCLASSIFIED |
| grupo Supervisor Engenharia | — | — | — | UNCLASSIFIED |

## Transição

Janela curta. Sem dual-read de unidade.

`access` efetivo se houver `access` ou um código legado de uso: `view`, `meeting-minutes.view`, `atas.view`, `meeting-minutes.sign`, `atas.sign`, `meeting-minutes.manage`, `atas.manage`, `processes.manage`, `revisions.manage`, `measurements.manage`, `investments.manage`, `view.consolidated`, `branch.*`, `view.filial.*`, `manage.filial.*`.

`manage` efetivo se houver `manage` ou `shared-resources.manage` ou `dashboard.recalculate` ou `data.transfer`.

Ausência dos dois lados nega. A janela fecha na fase 12. Não fica OR eterno.

## Fases

1. Manifesto ganha `access` e `manage` e mantém os 21.
2. Backend entende os códigos novos com o mapa acima.
3. Tira filial do caminho de autorização.
4. Filial permanece filtro da Visão geral e dimensão do dado.
5. Matriz humana aprovada.
6. Migra papéis, grupos e usuários. Não apaga os códigos antigos antes do aceite.
7. Rotas do portal.
8. MCP e Actions no mesmo contexto. Sem contrato novo.
9. Aceite: um usuário `access` vê processo da 01 e da 02, filtra a visão geral nas duas e no consolidado, e toma 403 na administração.
10. Aliases `atas.*` e `view/manage.filial.*`.
11. Permissions granulares.
12. `branch.*` e `view.consolidated`.
13. Busca residual.

Rollback de cada fase não reabre «sem capability → vê tudo». Reverter a fase 3 devolve o filtro antigo de filial, que é regressão conhecida e temporária, não o alvo.

## Testes

Sem access, 403. Com access, todos os processos, filtro 01, filtro 02, consolidado, administração negada, transferência negada, recálculo de usuário negado. `manage` sem `access` não abre a raiz. `access` + `manage` abre administração. Não-signatário não assina. Estado inválido não assina. Menu e cargo não autorizam. MCP e HTTP iguais.

Não testar «unidade A não vê B». Esse requisito não existe.

## Gaps

A matriz continua vazia. A fase 6 não começa sem ela. Homologação não foi reconsultada. O nome do helper que sobrar para filtro de dashboard ainda não foi escolhido. Isso não bloqueia a revisão do desenho.
