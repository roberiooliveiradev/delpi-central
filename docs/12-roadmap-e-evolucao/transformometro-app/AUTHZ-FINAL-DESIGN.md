# Portal Transforma+ — desenho final de autorização

> **Status:** desenho para revisão. Não é runtime.  
> **AUTHZ_FINAL_DESIGN = READY_FOR_ARCH_REVIEW.**  
> **IMPLEMENTATION = NOT AUTHORIZED.**  
> Base: `5c975e2916802a59639693b5b789266affd828d1`.  
> Inventário anterior: [AUTHZ-SIMPLIFICATION.md](./AUTHZ-SIMPLIFICATION.md). As decisões de negócio daquele arquivo que ainda estavam abertas ficam fechadas aqui.

Keycloak autentica. Core atribui capability e quais unidades do Portal o principal pode usar. A unidade é objeto do Portal Transforma+, não do Core. O Transformômetro resolve esse objeto e aplica a regra de domínio. Frontend não autoriza. Cargo e perfil não autorizam.

## 1. Permissions funcionais finais

Somente:

- `transformometro.access` — uso normal dentro do escopo autorizado.
- `transformometro.manage` — administração e configuração do produto.

`manage` não é escrita irrestrita de processo, não é escopo de todas as unidades e não é superadmin.

## 2. Unidade do Portal e quem guarda o acesso

A unidade, também chamada filial, é objeto do Portal Transforma+. Dono: Transformômetro. Tabela `transformometro.filiais`, com `filial_id` e `codigo_filial`. Instância, setor, ata e dashboard apontam para esse objeto. O Core não cadastra, não renomeia e não generaliza unidade para outros apps. Não nasce catálogo organizacional no Core.

O que falta não é o objeto. Falta registrar, fora da permission, quais objetos unidade daquele portal um principal pode usar.

CONFIRMADO: Core tem usuário, grupo, papel, permission e as tabelas de assignment. `GET /me` não devolve unidades. Não há tabela de scope. Papel não serve: o mesmo papel teria de ser copiado por conjunto de unidades. Grupo não serve: o nome do grupo não é unidade.

**ARCHITECTURE_GAP:** o vínculo principal → unidades do Portal Transforma+. O objeto unidade não é gap.

Menor capability, no Core, sem virar dono do objeto:

- sujeito: usuário ou grupo;
- aplicação: `transformometro`;
- modo explícito;
- quando o modo é conjunto, referências estáveis da unidade do portal (`codigo_filial`), resolvidas só pelo Transformômetro para `filial_id`.

Sem FK do Core para `transformometro.filiais`. São bancos diferentes. Código desconhecido no catálogo do portal é negado.

Modos:

- `none` — nenhuma unidade do portal. Default. Ausência de registro é `none`, nunca todas.
- `units` — um ou mais objetos unidade já existentes no portal.
- `all` — todas as unidades do catálogo do portal, inclusive as que o portal criar depois. Gravado de propósito.

União dos vínculos de grupo e do vínculo direto. `all` vence `units`.

Não é permission por filial, não é role Keycloak, não é tabela local de RBAC no Transformômetro. Unidade nova entra no catálogo do portal e, no modo `all`, passa a valer sem código novo de permission. No modo `units`, alguém inclui aquela unidade no vínculo.

## 3. Contrato para as APIs de domínio

Pergunta que o contrato responde: quais unidades do Portal Transforma+ este principal pode usar?

`GET /me` já é a projeção que `load_user_rbac` consome. Estender essa projeção, não criar um segundo canal. Para o app `transformometro`, o modo e, quando for conjunto, os códigos das unidades do portal. O payload não leva o objeto filial. O Transformômetro carrega `filiais` e descarta código que não existe. Nomes de campo não estão congelados.

Dono da projeção: Core. Dono do objeto: Transformômetro. Consumidor: `shared/delpi_auth` e o interpreter do portal. Frescor: o mesmo cache de `/me` (`DELPI_AUTH_RBAC_CACHE_TTL_SECONDS`, default 60s). Se o Core falhar, o middleware já zera permissions. Escopo ausente nessa falha é nenhuma unidade, não todas.

## 4. Processo, instância, revisão, medição

O playbook de modelagem diz que o processo-mestre guarda identidade e não carrega filial operacional, e que a instância é filial × setor, com revisão e cálculo presos à instância. O schema também tem `processos.todas_filiais_ativas` e `processo_filiais`. Isso é overlay atual de listagem, não uma segunda permission.

Regra final:

- Mestre: identidade compartilhada. Leitura com `access` se alguma instância, ou o overlay `processo_filiais`, cruza o escopo. `todas_filiais_ativas` no mestre torna o mestre visível para quem tem ao menos uma unidade, sem abrir as outras unidades.
- Escrita do mestre: `access` somente se todas as unidades ligadas ao processo estão dentro do escopo, ou se o escopo é `all`. Usuário de uma unidade não altera mestre compartilhado com outra.
- Instância, revisão, medição e dado operacional: a unidade vem da instância. Fora do escopo, nega. Instância `todas_filiais_ativas` só é escrita com escopo `all`. A leitura projeta só as unidades autorizadas.

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

| Atribuição | Capability | Escopo | Estado |
|---|---|---|---|
| cada um dos 4 usuários do papel | `access` ou `manage` | `units` ou `all` | UNCLASSIFIED |
| grupo Supervisor Engenharia | não inferir pelo nome | não inferir | UNCLASSIFIED |

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

1. Core grava o vínculo com as unidades do Portal Transforma+ e projeta no `/me`. O cadastro `filiais` não muda de dono. Sem esse vínculo, filial continua representada por permission.
2. Transformômetro interpreta o escopo do Core. Enquanto a projeção não vier, não há fallback para `all`.
3. Manifesto ganha `access` e `manage` sem apagar os códigos atuais.
4. Backend entende código novo ou antigo na janela curta. Falta de código não libera.
5. Matriz humana preenchida. Só então copiar assignments. Não apagar os antigos.
6. Rotas do portal passam para `access` e `manage`.
7. MCP e Actions no mesmo gate, com os contratos atuais.
8. Aceite negativo entre unidades.
9. Remover aliases `atas.*`, `view.filial-*`, `manage.filial-*`.
10. Remover permissions granulares de domínio.
11. Remover `branch.*` e `view.consolidated` depois que a fase 2 estiver provada em runtime.

Rollback de cada fase: o código antigo e o assignment antigo permanecem até o aceite. Não resetar Keycloak. Não apagar linha de papel antes da prova. Reverter a projeção do Core não pode transformar escopo ausente em `all`.

## 13. Matriz de teste

`access` + `01`; `access` + `02`; `access` + `01` e `02`; `manage` + `01`; `manage` + `01` e `02`; sem access; `access` sem unidade; `manage` sem unidade; recurso de outra unidade; leitura e escrita do mestre; instância; revisão; medição; ver ata; editar ata; assinar ata; transferência; recálculo; consolidado. Em todos: não-signatário negado, menu oculto não substitui a API, cargo não abre unidade.

## 14. Gaps que a revisão precisa aceitar

O objeto unidade já existe no portal. O vínculo no Core não existe. Os nomes de campo do `/me` não estão congelados. A matriz dos 4 usuários está vazia de propósito. `processos.todas_filiais_ativas` precisa entrar na interseção do mestre, mesmo o playbook tratando o mestre como identidade. Homologação não foi inventariada.
