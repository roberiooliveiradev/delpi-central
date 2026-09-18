# Portal Transforma+ — autorização final

> **Status:** modelo final. Duas permissions. Sem autorização por unidade.
> **FINAL PERMISSION COUNT = 2.**
> **ACCESS** = uso normal completo do Portal Transforma+, em todas as unidades.
> **MANAGE** = administração do portal (equipe, grupos, acessos). Não faz CRUD do domínio e não implica `access`.
> **UNIT AUTHORIZATION = none.**
> **CORE** = autoridade de permission, role, group e assignment.
> **TRANSFORMÔMETRO** = autoridade do domínio. Não cria RBAC.
> **LEGACY AUTH = removed** do runtime. Histórico fica no Git.

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

Ata: `access`. Assinar exige ser signatário, estado assinável e ainda não ter assinado. A unidade da ata não limita a permissão. Não existe `meeting-minutes.sign` no alvo.

Processo, instância, revisão, medição, investimento, melhoria, diagrama, decomposição, recurso compartilhado, filial e departamento: CRUD normal é `access` mais a regra de domínio. Não há permission de escrita por entidade.

Recálculo pedido na Visão geral é uso normal. Reconstrói cache depois de medição ou revisão. Não é gestão de equipe. Alvo: `access`. O hook interno depois de escrita continua fora desse gate.

Exportar e importar é backup do cadastro do produto, não gestão de acessos. Alvo: `access`. Preview, validação, confirmação de replace e read-back permanecem. `data.transfer` sai.

`manage` é a Administração do portal. Não implica `access` e não edita processo, revisão, medição, investimento, ata nem backup.

Configurações é subárea de Administração, não área principal. O CRUD dos catálogos de unidade, departamento e recurso compartilhado exige `manage`. A consulta desses catálogos para operar um processo continua `access`. O vínculo de um recurso a uma revisão é uso normal e continua `access`. Equipe, grupos e acessos seguem contrato da Core; o Transformômetro não os duplica.

## O que o código faz hoje

O backend só conhece `transformometro.access` e `transformometro.manage`. `FilialAccessScopeService` foi removido. Unidade não autoriza. Administração de equipe, grupo e acesso continua contrato da Core; a rota `/administration` exige `manage`. O Transformômetro não implementa essa gestão.

| Superfície | Hoje | Alvo | Migrar |
|---|---|---|---|
| Lista de processos | filtra pela filial do papel | `access` vê todos | sim |
| Dashboard | `check_dashboard_filial_access` | filtro analítico, sem negar unidade | sim |
| Atas | `can_view_filial` / `can_manage_filial` | `access`; assinar pela regra do signatário | sim |
| `/options` | esconde filial fora do papel | catálogo para o filtro, com `access` | sim |
| Writes de instância | `check_manage_filial_access` | `access` + regra de domínio | sim |
| Catálogo de filial | `access` | `access` | feito na policy |
| Recurso, backup, recálculo de usuário | `access` | `access` | feito na policy |
| Administração de equipe, grupo e acesso | ainda não existe no app | `manage`, via Core | rota depois do assignment |
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
| `shared-resources.manage`, `dashboard.recalculate`, `data.transfer` | `access`. São dado ou operação normal do produto |
| `view.consolidated` | sai; é o filtro Todas |
| `branch.filial-*`, `view.filial-*`, `manage.filial-*` | sai |

## Manifesto

Os códigos `access` e `manage` foram adicionados. Os 21 antigos permanecem. As rotas do portal ainda usam os códigos legados. O `ProtectedRoute` compara o código exato. Trocar a rota antes do assignment novo bloquearia quem ainda não tem `access`.

Alvo, ainda não aplicado:

| Rota | Permission |
|---|---|
| `/apps/transformometro` | `access` |
| dashboard, processes, settings/units, meeting-minutes, my-signature, data | `access` |
| administration | `manage` |

Início, Visão geral, Sala, Minhas tarefas, Meus processos e Ajuda são `access`. Administração é `manage`. A filial não entra na TopBar.

## Catálogo da Core

Leitura autoritativa em `delpi-postgres-core`, app `transformometro`, versão `0.5.0`, nome ainda `Transformômetro`. 21 códigos. Os dois novos não estão lá. Zero grant direto. O `PUT` de manifesto recusa mudança de permission. O `POST /admin/apps/register` da mesma versão devolve `plugin.version_already_exists`. Um register de versão nova preserva UUID dos códigos que permanecem e apaga o que sair do manifesto. Os 21 atuais estão no manifesto do Git, então um register futuro inseriria 2 e apagaria 0. O mesmo register recria rotas e a identidade do app. Produção tem 6 rotas e o nome antigo. O manifesto do Git tem 7 rotas, inclusive Administração, e o nome Portal Transforma+. Isso não é sync só de código. Não houve write. Não houve ator `apps.manage` nesta sessão. Homologação: **TO_INVENTORY**.

## Papéis

Releitura de 2026-09-18. Um papel, um grupo, quatro pessoas, zero grant direto. Três pessoas têm o papel direto. Uma tem o papel direto e também o grupo. Não criar papel novo. A menor write futura é no papel que já existe. `manage` não foi inferido.

| Principal ou grupo | Efeito atual | access proposto | manage proposto | Fonte | Status |
|---|---|---|---|---|---|
| papel Transforma Mais `86a058d2-aeb3-4c85-b103-d52ba0ac22e9` | 21 códigos, inclusive `view` e os manages de uso | adicionar `access` | não propor | o papel já abre o portal pelo legado de uso | PROPOSED |
| grupo Supervisor Engenharia `5585f5f3-27f0-4d31-a032-91279d21f4f4` | herda o mesmo papel | nenhum grant novo | nenhum | o grupo não é a única via | PROPOSED |
| quatro pessoas ligadas ao papel | superadmin da plataforma, além do papel | nenhum grant direto | UNCLASSIFIED | superadmin não decide `manage` do produto | UNCLASSIFIED |

## Transição

Janela curta. Sem dual-read de unidade.

`access` efetivo se houver `access` ou um código legado de uso do domínio: `view`, `processes.manage`, `revisions.manage`, `measurements.manage`, `investments.manage`, `shared-resources.manage`, `dashboard.recalculate`, `data.transfer`, `meeting-minutes.view`, `atas.view`, `meeting-minutes.manage`, `atas.manage`.

Não entram em `access`: `branch.*`, `view.filial-*`, `manage.filial-*`, `view.consolidated`, `meeting-minutes.sign`, `atas.sign`. Sign continua só na ação de assinar e no detalhe pendente.

`manage` efetivo é só `transformometro.manage`. Nenhum código antigo de entidade vira administração do portal. Ausência nega. A janela fecha quando os assignments novos estiverem comprovados e os 21 saírem. Não fica OR eterno.

## Gap de semântica

**DOMAIN_AUTHORIZATION_SEMANTICS_GAP:** escrita normal de processo, revisão, medição, investimento e conteúdo de ata passou a depender de `access` (ou do legado de uso) mais as validações de domínio que já existiam. Não há regra de domínio separada que substitua o antigo `processes.manage` contra `view`. Não se inventou regra. Unidade não foi usada como substituto.

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
