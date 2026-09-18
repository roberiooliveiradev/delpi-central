# Portal Transforma+ — desenho final de autorização

> **Status:** desenho para revisão. Não é runtime.  
> **AUTHZ_FINAL_DESIGN = READY_FOR_ARCH_REVIEW.**  
> **IMPLEMENTATION = NOT AUTHORIZED.**  
> Base: `5c975e2916802a59639693b5b789266affd828d1`.  
> Inventário anterior: [AUTHZ-SIMPLIFICATION.md](./AUTHZ-SIMPLIFICATION.md). As decisões de negócio daquele arquivo que ainda estavam abertas ficam fechadas aqui.

Keycloak autentica. A Core API é a autoridade de permissão e do vínculo de escopo. O Transformômetro não concede permissão. Ele é dono dos objetos e pode negar uma operação já autorizada pelo Core quando a regra de negócio falha. Não pode liberar o que o Core negou. Frontend, TÉO, MCP e GPT Actions não autorizam.

## 1. Permissions funcionais finais

Somente:

- `transformometro.access` — uso normal dentro do escopo autorizado.
- `transformometro.manage` — administração e configuração do produto.

`manage` não é escrita irrestrita de processo, não é escopo de todas as unidades e não é superadmin.

## 2. Unidade do Portal e quem guarda o acesso

A unidade, também chamada filial, é objeto do Portal Transforma+. Dono: Transformômetro. Tabela `transformometro.filiais`, com `filial_id` e `codigo_filial`. Instância, setor, ata e dashboard apontam para esse objeto. O Core não cadastra, não renomeia e não generaliza unidade para outros apps. Não nasce catálogo organizacional no Core.

O que falta não é o objeto. Falta registrar, fora da permission, quais objetos unidade daquele portal um principal pode usar.

CONFIRMADO: `PermissionResolver` une permissões de papéis diretos e de papéis dos grupos. Override em `user_permissions` acrescenta se `granted` ou retira se não. Não há implicação `manage` ⇒ `access`. Quem administra recebe os dois códigos, explícitos.

O escopo segue a mesma herança, sem virar permission. Uma linha de escopo por papel, grupo ou usuário, para a aplicação `transformometro`. Vários papéis ou grupos: união. Qualquer `all` na união resulta em `all`. Override direto do usuário substitui a união. Não soma com ela. Sem nenhuma linha, o modo é ausência, não `all`. Na janela de migração, ausência ainda lê os códigos `branch.*`. Linha presente, inclusive `none`, corta o legado. Não há união entre escopo novo e filial antiga.

O identificador opaco é `codigo_filial`. O Core não guarda nome, status nem FK. `SET ["01","02"]` não é `all`: a unidade `03` futura entra só em `all`.

**ARCHITECTURE_GAP:** ainda não existe tabela desse vínculo. O objeto unidade não é gap.

O vínculo fica no banco do Core, uma linha por sujeito e aplicação. Sujeito é papel, grupo ou usuário, no mesmo desenho de `role_permissions` / `group_roles` / `user_permissions`. Aplicação é o id do manifesto, `transformometro`. Modo: `none`, `units` ou `all`. Em `units`, só a lista de `codigo_filial`. Sem nome, sem status, sem FK, sem SQL no schema `transformometro`, sem import de `tm_app`.

Resolução efetiva, igual à das permissions, com uma diferença no override:

1. se o usuário tem linha direta para o app, ela substitui o resto;
2. senão, união das linhas dos papéis do usuário e dos papéis dos grupos;
3. na união, `all` absorve `units`;
4. nenhuma linha no caminho resolvido significa ausência.

Ausência no estado final é `none`. Durante a fase 3, ausência ainda usa `branch.*`. Linha `none` não cai no legado.

Código que o Transformômetro não acha em `filiais` ativas é ignorado e registrado como referência obsoleta. Não abre outras unidades. Não derruba as unidades válidas da mesma lista. `99` ao lado de `01` autoriza `01` e nada mais.

Auditoria reusa `audit_logs`: ator, principal, aplicação, escopo anterior, escopo novo. Sem payload de filial.

O resolver de permissão não chama o Transformômetro. A tela administrativa, no futuro, lista unidades pelo contrato já existente `list_filiais`, que hoje filtra pelo escopo de quem chama. Atribuir unidade que o administrador não possui continua gap de jornada, não de hot path.

## 3. Contrato para as APIs de domínio

Pergunta que o contrato responde: quais unidades do Portal Transforma+ este principal pode usar?

`GET /me` já é a projeção que `load_user_rbac` consome. Estender essa projeção, não criar um segundo canal. Para o app `transformometro`, o modo e, quando for conjunto, os códigos das unidades do portal. O payload não leva o objeto filial. O Transformômetro carrega `filiais` e descarta código que não existe. Nomes de campo não estão congelados.

Dono da projeção: Core. Dono do objeto: Transformômetro. Consumidor: `shared/delpi_auth` e o interpreter do portal. Frescor: o mesmo cache de `/me` (`DELPI_AUTH_RBAC_CACHE_TTL_SECONDS`, default 60s). Se o Core falhar, o middleware já zera permissions. Escopo ausente nessa falha é nenhuma unidade, não todas.

## 4. Processo, instância, revisão, medição

O playbook de modelagem diz que o processo-mestre guarda identidade e não carrega filial operacional, e que a instância é filial × setor, com revisão e cálculo presos à instância. O schema também tem `processos.todas_filiais_ativas` e `processo_filiais`. Isso é overlay atual de listagem, não uma segunda permission.

Regra final:

- Mestre: identidade compartilhada. Leitura com `access` se alguma instância, ou o overlay `processo_filiais`, cruza o escopo. `todas_filiais_ativas` no mestre torna o mestre visível para quem tem ao menos uma unidade, sem abrir as outras unidades.
- Escrita do mestre: `access` somente se todas as unidades ligadas ao processo estão dentro do escopo, ou se o escopo é `all`. Usuário de uma unidade não altera mestre compartilhado com outra.
- Processo sem instância: leitura e escrita da identidade exigem `access` e não abrem dado de unidade. Atribuir a primeira unidade exige `access` e essa unidade no escopo. Ausência de instância não é acesso irrestrito.
- Instância, revisão, medição e investimento: a unidade vem da instância. Fora do escopo, nega. Instância `todas_filiais_ativas` só é escrita com `all`. Leitura projeta só as unidades autorizadas. Unidade `deletado` ou `status_filial` diferente de `ativo` não autoriza, mesmo se o código ainda estiver no vínculo. O Core não apaga o código por isso.

## 5. Visão consolidada

Não existe `view.consolidated` no alvo. Consolidado é a agregação do escopo autorizado.

- escopo `01` → consolidado de `01`;
- escopo `01` e `02` → os dois;
- escopo `all` → todas as unidades do catálogo do Portal Transforma+, inclusive as futuras.

## 6. Semântica congelada

| Operação | Regra |
|---|---|
| Uso normal, atas, processos, revisões, medições, investimentos | `access` + escopo + regra do recurso |
| Administração, configurações, recursos compartilhados, recálculo pedido pelo usuário, exportar/importar | `manage` + escopo |
| Assinar ata | `access` + é signatário + unidade da ata no escopo + estado assinável + ainda não assinou |
| Sem capability | nega |
| Sem escopo | nenhum dado de unidade |
| Unidade desconhecida | nega |
| `manage` sem unidade | não abre unidade |
| Menu, perfil, cargo | não autorizam |

Import/replace que apaga cadastro fora do escopo é negado. Replace do catálogo inteiro só com escopo `all`. O CLI de operador continua fora dessa policy.

## 7. Papéis de produção

O papel `Transforma Mais` tem os 21 códigos, as duas filiais, 4 usuários e o grupo `Supervisor Engenharia`. Não mapear esse papel inteiro para `access` + `manage`.

Matriz obrigatória, uma linha por atribuição, preenchida por decisão humana. Cargo não preenche a linha.

| Principal ou grupo | access | manage | Modo | Unidades | Aprovador | Status |
|---|---|---|---|---|---|---|
| 4 usuários do papel Transforma Mais | — | — | — | — | — | UNCLASSIFIED |
| grupo Supervisor Engenharia | — | — | — | — | — | UNCLASSIFIED |

Sem essa matriz, a fase de migração de assignment não começa.

## 8. Modelo transitório

Não é o modelo final. Só a janela de rollout, se a fase 2 ainda não consumir o agregado do Core:

- `transformometro.access`
- `transformometro.manage`
- `transformometro.branch.filial-01`
- `transformometro.branch.filial-02`
- `transformometro.view.consolidated`

`branch.*` nessa janela continua sendo a representação temporária do escopo. Some na fase 11.

## 9. Remoção

Cada código sai só quando o substituto está atribuído, o escopo novo está provado e o teste negativo passou. Busca residual no repositório é condição de saída, não o texto do manifesto.

| Código atual | Alvo | Compatibilidade temporária | Sai quando |
|---|---|---|---|
| `view` | `access` | dual-read | assignments migrados |
| `processes.manage`, `revisions.manage`, `measurements.manage`, `investments.manage` | `access` + domínio | dual-read | writes do domínio no novo gate |
| `meeting-minutes.view` | `access` + escopo | dual-read | lista e detalhe no novo gate |
| `meeting-minutes.manage` | `access` + regra do recurso | dual-read | edição de ata no novo gate |
| `meeting-minutes.sign` | `access` + signatário + estado | dual-read | teste de não-signatário |
| `atas.*` | alias dos três acima | sim, até os canônicos saírem | nenhum consumidor nas tuplas |
| `shared-resources.manage` | `manage` | dual-read | catálogo no gate de manage |
| `dashboard.recalculate` | `manage` | dual-read | HTTP, MCP e GPT na mesma policy |
| `data.transfer` | `manage` + escopo | dual-read | backup não escreve fora do escopo |
| `view.consolidated` | projeção do escopo | só no transitório | fase 11 |
| `branch.filial-*` | agregado do Core | só no transitório | fase 2 provada |
| `view.filial-*`, `manage.filial-*` | alias de branch | sim | fase 11, depois dos canônicos de filial |

Alvo residual no manifesto: só `access` e `manage`.

## 10. Manifesto proposto

Não aplicar.

```json
{
  "permissions": [
    {
      "code": "transformometro.access",
      "name": "Acessar Portal Transforma+",
      "description": "Uso normal do Portal Transforma+ dentro do escopo autorizado."
    },
    {
      "code": "transformometro.manage",
      "name": "Administrar Portal Transforma+",
      "description": "Administração e configuração do produto. Não concede unidade nem escrita irrestrita de processo."
    }
  ],
  "routes": [
    { "path": "/apps/transformometro", "label": "Portal Transforma+", "permission": "transformometro.access", "showInMenu": true },
    { "path": "/apps/transformometro/dashboard", "label": "Visão geral", "permission": "transformometro.access", "showInMenu": false },
    { "path": "/apps/transformometro/processes", "label": "Meus processos", "permission": "transformometro.access", "showInMenu": false },
    { "path": "/apps/transformometro/meeting-minutes", "label": "Atas", "permission": "transformometro.access", "showInMenu": false },
    { "path": "/apps/transformometro/my-signature", "label": "Minha assinatura", "permission": "transformometro.access", "showInMenu": false },
    { "path": "/apps/transformometro/administration", "label": "Administração", "permission": "transformometro.manage", "showInMenu": false },
    { "path": "/apps/transformometro/settings/units", "label": "Configurações", "permission": "transformometro.manage", "showInMenu": false },
    { "path": "/apps/transformometro/data", "label": "Exportar/Importar", "permission": "transformometro.manage", "showInMenu": false }
  ]
}
```

Ajuda, Sala de interação e Minhas tarefas, quando existirem, usam `access`. A TopBar não cria permission. Itens atuais da barra: Início, Visão geral, Meus processos, Administração. Sala, tarefas e Ajuda continuam fora da barra até existirem.

## 11. MCP e GPT Actions

Nenhuma tool nova, nenhuma Action nova, nenhum aumento de OpenAPI. Os checks internos passam a chamar a mesma policy: `access` ou `manage`, mais escopo, mais regra do recurso. Recálculo e backup usam `manage`. Leitura e escrita de domínio usam `access`. Assinatura não consulta `meeting-minutes.sign`.

## 12. Fases

Pacote da fase 1: [CORE-APP-UNIT-SCOPE-PACKET.md](./CORE-APP-UNIT-SCOPE-PACKET.md). ADR: [`adr-core-authorization-portal-units.md`](../../../transformometro-api/docs/architecture/adr-core-authorization-portal-units.md).

0. Este desenho. Sem código.
1. Persistência do vínculo no Core e contrato da projeção. Sem remover permission.
2. Projeção no `GET /me`, no mesmo cache já existente. Sem chamada ao Transformômetro no resolver.
3. Transformômetro consome o vínculo. Se houver linha, só ela vale. Se não houver, valem os `branch.*` atuais. Nunca união. Nunca ausência vira `all`.
4. Manifesto ganha `access` e `manage` sem apagar os 21.
5. Policies entendem os códigos novos. Quem tem `manage` também precisa de `access` no assignment, porque o resolver não implica.
6. Matriz humana aprovada. Quatro usuários e o grupo continuam UNCLASSIFIED até lá.
7. Migrar assignments. Não apagar os antigos antes do aceite.
8. Rotas do portal.
9. MCP e Actions, mesmos contratos.
10. Negativo entre unidades.
11. Aliases.
12. Permissions granulares.
13. `branch.*` e `view.consolidated`.
14. Busca residual e aceite de runtime.

Não juntar a fase 1 com a remoção do legado. Rollback de cada fase não transforma `none` em `all`.

## 13. Matriz de teste

Core: sem linha; `set` 01; `set` 02; `set` 01 e 02; `all`; código desconhecido; unidade removida; escopo vindo de papel; de grupo; override direto que substitui; vários papéis em união; revogação; sem access; access; manage; access e manage.

Portal: access com 01, com 02, com as duas, com nenhuma; manage com nenhuma, com 01, com `all`; sem access; mestre; processo sem instância; instância; revisão; medição; investimento; ver, editar e assinar ata; dashboard; consolidado; transferência; recálculo; configuração. HTTP, MCP e Actions com o mesmo resultado. Botão visível não substitui a API. Cargo não abre unidade.

## 14. Gaps

Nomes de coluna e de campo do `/me` saem na implementação, seguindo o padrão do Core, não neste texto. `list_filiais` filtra pelo escopo de quem chama. Não serve, sozinho, para um administrador atribuir unidade que ele mesmo não tem. Isso fica para um contrato de leitura futuro, não para o resolver. Homologação não foi inventariada. A matriz humana está vazia.
