# 29 — Ajuda

## Estado

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED      = PASS
CONTRACT_DEFINED         = PASS
AUTHZ_DEFINED            = PASS
PLUGIN_UI_REUSE_DEFINED  = PASS
STATES_DEFINED           = PASS
TEST_MATRIX_DEFINED      = PASS
```

Runtime do Portal Controladoria & Finanças: **NOT_IMPLEMENTED**.

A fase atual é exclusivamente documental:

```text
PORTAL_REVIEW_PHASE       = ACTIVE
IMPLEMENTATION_AUTHORIZED = NO
```

Este documento fecha o **Item 7 — Ajuda** no nível de UX, arquitetura de conteúdo, reuso do `@delpi/plugin-ui`, navegação, deep links, feature gating, Help contextual, governança de sincronização, acessibilidade e testes futuros.

---

## Objetivo

**Ajuda** é o manual de usuário canônico do Portal Controladoria & Finanças.

Ela deve responder:

> O que é cada conceito, onde faço cada ação, como uso cada página e o que determinado estado significa?

Princípio:

```text
USER_FACING_CHANGE
→ HELP_SYNC
→ FEATURE ACCEPTANCE
```

A Ajuda é parte do produto.

Ela não é documentação técnica, changelog, backlog ou roadmap.

---

## Responsabilidade, owners e non-goals

A Ajuda owns **conteúdo user-facing versionado do Portal**, não estado de negócio nem documentação técnica.

| Elemento | Owner |
|---|---|
| conteúdo do manual | MFE / content registry do Portal |
| chrome/TOC/FAQ/glossário | `@delpi/plugin-ui` |
| feature/route catalog | MFE/router do Portal |
| effective permissions | Core; consumidas pelo Portal/BFF/session |
| regra explicada | documento/owner da feature correspondente |
| Help contextual target | página/feature + registry do manual |

Não pertence à Ajuda:
- BFF próprio de Help;
- DB/CMS/editor;
- permissão nova;
- source of truth de regra de negócio;
- feature flag improvisada;
- publicação de roadmap como capability;
- busca própria V1;
- conteúdo técnico de endpoints/SQL/infra para usuário final.

## Decisões congeladas

### D-HELP-01 — usar manual canônico do plugin-ui

```text
MANUAL_CHROME = @delpi/plugin-ui
LOCAL_MANUAL_FRAME = FORBIDDEN
```

Usar `createDashboardUserManual`.

### D-HELP-02 — conteúdo fica no MFE

V1:

```text
HELP_CONTENT
= VERSIONED FRONTEND CONTENT
!= DATABASE CMS
!= BFF OWNED CONTENT
!= ADMIN EDITABLE CONTENT
```

Não criar:
- tabela de manual;
- API de Help;
- editor WYSIWYG;
- catálogo administrativo de artigos;
- storage de Markdown;
- permission de edição de Help.

O conteúdo acompanha o código da feature e o mesmo gate de aceite.

### D-HELP-03 — Help só documenta runtime existente

```text
PLANNED FEATURE
!= PUBLISHED HELP CAPABILITY
```

Documentação TARGET deste repositório pode descrever futuro.

O manual runtime não pode prometer:
- página ainda inexistente;
- botão ainda não implementado;
- catálogo ainda não publicado;
- integration ainda bloqueada;
- ação que o usuário não pode executar.

### D-HELP-04 — Help contextual aponta para seção canônica

Tooltips explicam algo curto.

O manual contém orientação completa.

```text
SHORT FIELD HINT
→ HelpTooltip

PAGE / PROCESS GUIDANCE
→ /help#manual-{sectionId}
```

Não duplicar parágrafos longos em tooltips.

### D-HELP-05 — conteúdo respeita capabilities

Rota da Ajuda exige:

```text
controllership-finance.access
```

Seção de Administração:

```text
requires = controllership-finance.manage
```

Usuário sem `manage` não recebe instruções de operação administrativa como capability disponível.

Conceitos gerais podem mencionar que existe Administração, mas sem expor ações internas não autorizadas.

### D-HELP-06 — sem busca própria na V1

O kit atual fornece TOC/navegação do manual, não search engine.

```text
HELP_SEARCH_V1 = NOT_INCLUDED
```

A busca global da TopBar continua separada.

Se no futuro o kit ganhar busca de manual:
- adotar no `plugin-ui`;
- não criar busca local paralela agora.

---

## Rota

```text
/apps/controllership-finance/help
```

Permission:

```text
controllership-finance.access
```

Deep link por seção:

```text
/apps/controllership-finance/help#manual-concepts
/apps/controllership-finance/help#manual-start
/apps/controllership-finance/help#manual-home
/apps/controllership-finance/help#manual-overview
/apps/controllership-finance/help#manual-interaction-room
/apps/controllership-finance/help#manual-my-tasks
/apps/controllership-finance/help#manual-administration
/apps/controllership-finance/help#manual-closing
/apps/controllership-finance/help#manual-user-profile
/apps/controllership-finance/help#manual-faq
/apps/controllership-finance/help#manual-glossary
```

Hash é navegação local segura.

Não colocar conteúdo sensível em query/hash.


## Contrato TARGET da Ajuda

O conteúdo base é local/versionado no MFE:

```text
Portal content registry
→ createDashboardUserManual
→ sections filtered by implemented capability + viewer authorization
```

Não existe contract BFF de conteúdo na V1.

A rota continua sujeita ao guard normal do Portal:

```text
authenticated
AND effective_permission(controllership-finance.access)
```

A seção Administração exige, além da rota ACCESS:

```text
effective_permission(controllership-finance.manage)
```

### Capability registry

Cada seção/link operacional deve referenciar um destino tipado conhecido pelo Portal:

```text
sectionId
source contract/page
routeId quando aplicável
runtimeEnabled
requiredCapability
contextualHelpTargets[]
```

Regras:
- `runtimeEnabled=false` → não publicar instrução executável;
- rota ausente → não publicar tool link;
- MANAGE-only → esconder conteúdo operacional para ACCESS-only;
- conceito geral pode permanecer quando necessário para entendimento, sem expor ação não autorizada;
- Help não executa fetch/AuthZ paralelo apenas para descobrir permissions se o Portal já possui effective access resolvido;
- se effective access necessário ao filtering estiver indisponível, fail-closed para conteúdo restrito.

### MFE / BFF boundary

A Ajuda não chama `api-delpi`, Core ou outros owners diretamente para renderizar conteúdo base.

Dados/runtime links eventuais são derivados do catálogo/estado já autorizado do Portal. Nova necessidade de conteúdo dinâmico server-side exige decisão/contract separado; não antecipar API de Help.


---

## Família visual

```text
VISUAL_FAMILY     = USER_MANUAL
PRIMARY_FACTORY   = createDashboardUserManual
PLUGIN_UI_FIRST   = REQUIRED
REFERENCE         = Commercial + Supplies
```

Comercial e Suprimentos já usam o mesmo padrão:

```text
PagePath
→ PageHero
→ Manual.Scope
→ Manual.Layout / TOC
→ Manual.Section
→ SectionCard
→ Concepts / GuideTable / FAQ / Glossary
```

Controladoria deve seguir a mesma família visual.

A TopBar pertence ao shell. A Ajuda usa `PagePath` porque o manual apresenta retorno explícito ao Início e navegação contextual por hash; não recriar breadcrumb local.

---

## Reuso obrigatório de @delpi/plugin-ui

Import preferencial:

```ts
import {
  createDashboardUserManual,
  createDashboardPageHero,
  createDashboardPagePath,
  createDashboardSectionCard,
  HelpTooltip,
  FieldLabel,
  SectionHintLabel,
  ActionButton,
  StateBanner,
  EmptyState,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

Factory:

```ts
const Manual = createDashboardUserManual({
  prefix: "cf",
});
```

O kit fornece:

```text
Manual.Frame
Manual.Eyebrow
Manual.Scope
Manual.Layout
Manual.Section
Manual.Concepts
Manual.GuideTable
Manual.Faq
Manual.Glossary
Manual.classNames
```

### DO NOT RECREATE

- frame do manual;
- TOC;
- concepts grid;
- guide table;
- FAQ chrome;
- glossary chrome;
- tool-link styling;
- help tooltip;
- PageHero/PagePath/SectionCard;
- light/dark/mobile CSS do kit.

---

## Wireframe — desktop

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda       │
│                                      Buscar | Favoritos | [avatar] Usuário │
└──────────────────────────────────────────────────────────────────────────────┘

← Início / Ajuda

┌──────────────────────────────────────────────────────────────────────────────┐
│ AJUDA                                                     [Voltar ao Início]│
│ Manual do usuário                                                            │
│ Conceitos, caminhos, dúvidas frequentes e termos do Portal.                  │
└──────────────────────────────────────────────────────────────────────────────┘

Este manual mostra somente funcionalidades disponíveis para o seu acesso.

┌───────────────────────┐  ┌──────────────────────────────────────────────────┐
│ NESTA PÁGINA          │  │ CONCEITOS QUE NÃO MISTURE                       │
│ Conceitos             │  │ Competência | Snapshot | Evidência | ...       │
│ Comece por aqui       │  └──────────────────────────────────────────────────┘
│ Visão geral           │
│ Sala de interação     │  ┌──────────────────────────────────────────────────┐
│ Minhas tarefas        │  │ QUERO… → ONDE IR → COMO                         │
│ Administração*        │  │ ...                                              │
│ Central de Fechamento │  └──────────────────────────────────────────────────┘
│ Página do usuário     │
│ FAQ                   │  [...]
│ Glossário             │
└───────────────────────┘

* somente com MANAGE
```

---

## Wireframe — mobile

```text
TOPBAR COMPACTA

← Início

Ajuda
Manual do usuário

Este manual mostra somente funcionalidades disponíveis para o seu acesso.

[Nesta página ▼]
- Conceitos
- Comece por aqui
- Visão geral
- Sala de interação
- Minhas tarefas
- Administração*
- Central de Fechamento
- Página do usuário
- FAQ
- Glossário

[seção selecionada]
```

A estratégia mobile real do `Manual.Layout` deve ser preservada.

Se o TOC atual precisar evolução de UX mobile:
- evoluir o kit;
- não recriar manual local.

---

## Hero

Eyebrow:

```text
Ajuda
```

Título:

```text
Manual do usuário
```

Descrição:

```text
Conceitos, caminhos, dúvidas frequentes e termos do Portal Controladoria & Finanças.
```

CTA:

```text
Voltar ao Início
```

Não usar Hero para:
- versão técnica;
- SHA;
- status de deployment;
- backlog.

---

## Scope note

Texto TARGET:

```text
Este manual mostra somente funcionalidades disponíveis no Portal e compatíveis com o seu acesso.
```

Quando algum recurso ainda não estiver implementado:
- não aparece como instrução executável;
- não aparece como `Onde ir`;
- não vira link.

---

## Arquitetura de conteúdo

Ordem canônica:

```text
1. Conceitos
2. Comece por aqui
3. Visão geral
4. Sala de interação
5. Minhas tarefas
6. Administração [MANAGE]
7. Central de Fechamento
8. Página do usuário
9. Perguntas frequentes
10. Glossário
```

A ordem privilegia:
- entendimento;
- navegação;
- páginas comuns;
- processo operacional;
- referência.

---

# 1. Conceitos

Título:

```text
Conceitos que não misture
```

Itens mínimos:

### Portal Controladoria & Finanças

Produto multi-macroprocesso da Minha DELPI.

A Central de Fechamento é a primeira funcionalidade, não o Portal inteiro.

### Central de Fechamento

Conjunto de páginas que suporta o processo de fechamento mensal da Controladoria.

### Competência

Recorte mensal do fechamento.

Não é sinônimo de data de consulta.

### Snapshot

Cópia governada da configuração aplicável à competência quando ela é aberta.

Mudança posterior do mestre não altera silenciosamente esse snapshot.

### Preliminary vs final

Resultado preliminar ainda depende de cutoff, source, revalidação ou outra condição material.

```text
PRELIMINARY != FINAL
```

### Source / freshness

Source é a origem autorizada do dado.

Freshness indica quando aquele dado foi obtido/calculado.

```text
SOURCE ERROR != ZERO
```

### Blocker

Condição que impede avanço de um estado do fechamento.

```text
BLOCKER != MY_TASK
```

### Evidência / anexo

Arquivo/documento associado a um item.

```text
ATTACHED != VALIDATED
```

### Validação

Decisão humana ou regra governada sobre evidência conforme o item.

### N/A

Aplicável apenas quando a regra permite.

```text
NOT_APPLICABLE != CANCELLED
```

### Pendência

Item que exige análise/resolução no fluxo.

Pendência não significa automaticamente atraso/SLA.

### Finalizar vs Enviar

```text
PACKAGE_FINALIZED != PACKAGE_SUBMITTED_FOR_REVIEW
```

Finalizar cria/congela uma versão do pacote.

Enviar submete PackageVersion finalizada para análise autenticada dentro da Minha DELPI; e-mail apenas notifica.

### Sala de interação

Colaboração contextual.

Mensagem não executa decisão de negócio.

### Minhas tarefas

Projeção das responsabilidades reais dos owners.

Não é gerenciador genérico de tarefas.

### ACCESS / MANAGE

Em linguagem de usuário:

```text
ACCESS
= usar superfícies operacionais autorizadas

MANAGE
= administrar configuração do Portal
```

Um não implica automaticamente o outro.

---

# 2. Comece por aqui

Section id:

```text
start
```

Guide table TARGET:

| Quero… | Onde ir | Como |
|---|---|---|
| Saber o que precisa de atenção | Início | Veja Eventos e interações, Minhas tarefas e caminhos disponíveis |
| Ver indicadores financeiros | Visão geral | Escolha período/unidade e abra o indicador/drilldown |
| Conversar sobre um contexto | Sala de interação | Abra a sala vinculada à competência/item/pendência/pacote |
| Ver ações que dependem de mim | Minhas tarefas | Use a fila pessoal e abra o contexto owner |
| Configurar o Portal | Administração | Disponível apenas com MANAGE |
| Operar o fechamento mensal | Central de Fechamento | Abra a competência e entre na etapa necessária |
| Entender um campo | ícone de ajuda | Passe/focalize o HelpTooltip |
| Ver meu perfil | avatar | Abra a Página do usuário do Portal |
| Editar foto/cargo/contatos | Meu Perfil da Minha DELPI | Identidade é owned pelo Core |
| Entender um conceito/processo | Ajuda | Use o índice e as seções deste manual |

Somente rows cujo destino existe no runtime podem ser renderizadas.

---

# 3. Início

O conteúdo runtime só entra quando a Home estiver implementada.

Explicar:
- Início é launcher operacional;
- diferença entre Início e Visão geral;
- Hero e highlights reais implementados;
- Eventos e interações;
- Caminhos e funcionalidades;
- busca local do catálogo;
- diferença entre busca local e Buscar da TopBar;
- Últimos acessos;
- Favoritos;
- Central de Fechamento como primeira funcionalidade;
- rotas futuras não aparecem;
- source indisponível não vira zero;
- Administração só aparece quando MANAGE.

Contrato fonte:
- [32-inicio-home.md](./32-inicio-home.md)

Section id:

```text
home
```

---

# 4. Visão geral

Section id:

```text
overview
```

Publicar somente indicadores implementados.

Explicar:
- objetivo analítico;
- período;
- unidade/contexto;
- KPIs financeiros;
- contexto operacional financeiro;
- indicadores estratégicos aprovados;
- significado/fórmula em linguagem de negócio;
- source/owner;
- freshness;
- meta/score somente quando owner fornecer;
- zero vs vazio vs indisponível;
- drilldown;
- filtros e compartilhamento de recorte quando implementados;
- IA não cria fórmula/authority.

Contrato fonte:
- [25-visao-geral-indicadores-financeiros.md](./25-visao-geral-indicadores-financeiros.md)

Não publicar indicador apenas porque consta no roadmap.

---

# 5. Sala de interação

Section id:

```text
interaction-room
```

Explicar:
- colaboração contextual;
- não existe wall/chat genérico;
- contextos suportados em runtime;
- Inbox;
- Todas / Não lidas / Menções;
- responder;
- mencionar;
- reação;
- fixar;
- editar própria mensagem;
- soft-delete;
- anexos;
- Arquivos e links;
- Localizar no chat;
- painel Neste chat;
- participants não são ACL;
- mensagem não aprova/valida/fecha/envia;
- attachment do chat não vira evidência P2 automaticamente;
- realtime degradado;
- voltar ao owner;
- criar task da mensagem não existe na V1.

Contrato fonte:
- [26-sala-de-interacao.md](./26-sala-de-interacao.md)

---

# 6. Minhas tarefas

Section id:

```text
my-tasks
```

Explicar:
- TaskProjection;
- tarefa vem do owner;
- diferença entre task, blocker, warning e mention;
- sources realmente implementadas;
- responsabilidade individual;
- busca;
- filtro source;
- filtro competência;
- `pendingSince` é idade factual;
- due só existe se owner possuir prazo real;
- sem SLA global;
- ação `Abrir`;
- concluir ocorre no owner;
- sem `Nova tarefa`;
- sem editor genérico;
- sem Equipe;
- sem bucket local Concluídas;
- source unavailable != empty;
- coverage COMPLETE/PARTIAL;
- Home usa a mesma projection.

Contrato fonte:
- [27-minhas-tarefas.md](./27-minhas-tarefas.md)

---

# 7. Administração

Section id:

```text
administration
```

Visibility:

```text
effective_permission(controllership-finance.manage)
```

Explicar somente quando runtime administrativo existir:
- MANAGE vs ACCESS;
- Painel;
- Templates;
- Catálogos;
- Histórico;
- DRAFT;
- REVIEW;
- PUBLISH;
- EFFECTIVE_FROM;
- salvar != publicar;
- snapshot;
- publicação prospectiva;
- inativação != exclusão;
- bancos/contas;
- checklist master;
- responsible/validator/recipient;
- referências a Core;
- motivos;
- attachment roles;
- notification targets;
- stale version/conflito;
- auditoria;
- P6 não administra usuário/role/permission.

Contrato fonte:
- [28-administracao.md](./28-administracao.md)

Usuário sem MANAGE:
- seção não entra no TOC;
- guide rows administrativas não viram links;
- manual não sugere ação que ele não pode executar.

---

# 8. Central de Fechamento

Section id:

```text
closing
```

Organizar a seção em subseções.

## Cockpit da Competência — P1

Explicar:
- competência;
- três eixos independentes;
- blockers;
- freshness;
- navegação aos owners;
- Estoque fechado != pacote enviado != fechamento concluído.

Fonte:
- [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md)

## Checklist e Documentos — P2

Explicar:
- snapshot;
- requirement;
- origin;
- evidência;
- ATTACHED != VALIDATED;
- validation scope;
- REQUIRED vs CONDITIONAL;
- N/A;
- rejeição;
- replacement;
- item excepcional;
- correção estrutural;
- histórico.

Fonte:
- [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md)

## Estoque e Conciliação — P3

Explicar:
- preliminary;
- cutoff;
- revalidação;
- P7;
- Entradas/Saídas;
- H02;
- paridade monetária exata;
- divergência;
- READY_TO_CLOSE;
- STOCK_CLOSED;
- `STOCK_CLOSED` é terminal no lifecycle P3 do Portal V1;
- correções pós-sacramentação pertencem ao owner canônico/ERP e não reabrem P3;
- source unavailable;
- V1 sem write ERP.

Regra visível:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
```

Fonte:
- [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md)

## Classificações e Pendências — P4

Explicar:
- sugestão vs decisão humana;
- pendência;
- claim;
- responsável;
- states;
- WAITING_EXTERNAL;
- RESOLVED;
- DISMISSED;
- dismiss exige justificativa;
- sem SLA/overdue formal;
- V1 sem write ERP.

Fonte:
- [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md)

## Pacote, Finalização e Envio — P5

Explicar apenas capacidades runtime liberadas:
- pacote;
- versão;
- finalizar != enviar para análise;
- "Enviar para análise" disponibiliza a versão dentro da Minha DELPI;
- reviewer externo possui login/app access;
- reviewer usa ACCESS + resource scope;
- package não é anexado por e-mail;
- Minha DELPI notifica in-app e pode também enviar e-mail;
- e-mail é aviso/deep link;
- review pending/in progress/changes requested/accepted;
- esclarecimento/correção;
- histórico/versionamento;
- conclusão C2: todos os pacotes aplicáveis submetidos, um aceite por área obrigatória e versão vigente, sem esclarecimentos abertos;
- reatribuição não troca autoria de aceites válidos; versão nova exige novos aceites;
- rejeição de pacote depende de confirmação formal para rejeitar a competência; aceite P5 não pode ser revertido pela interface V1.

Fonte:
- [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md)
- [37-p5-submissao-e-revisao-no-portal.md](./37-p5-submissao-e-revisao-no-portal.md)

---

# 9. Página do usuário

Section id:

```text
user-profile
```

Publicar quando rota existir.

Explicar:
- perfil corporativo;
- dados vindos do Core;
- read-only no Controladoria;
- editar foto/cargo/contatos no Meu Perfil da Minha DELPI;
- outro usuário com app access pode ser consultado conforme regra;
- permissions de outro usuário não são expostas;
- self pode mostrar labels/codes do próprio Portal conforme contract;
- `Não informado` != `temporariamente indisponível`;
- como retornar ao contexto anterior.

Contrato fonte:
- [31-pagina-do-usuario.md](./31-pagina-do-usuario.md)

Sincronização A01 / Gate V2:
- target inexistente/fora do app não é estado vazio;
- fonte indisponível não significa dado “não informado”;
- effective permissions indisponíveis falham fechado;
- Help da página continua runtime-gated e só é publicada quando a rota existir.

Esta sincronização não fecha o gate A07 da própria página Ajuda.

---

# 10. Perguntas frequentes

Section id:

```text
faq
```

FAQ inicial TARGET:

### Qual a diferença entre Início e Visão geral?

Início organiza ações, eventos e caminhos. Visão geral é a superfície analítica com indicadores.

### Por que um valor aparece indisponível em vez de zero?

Porque a fonte necessária não respondeu ou não possui evidência confiável. Ausência/erro de source não é zero.

### Um anexo enviado já está aprovado?

Não.

```text
ATTACHED != VALIDATED
```

### Um blocker sempre aparece em Minhas tarefas?

Não. Só vira TaskProjection quando existe responsabilidade individual acionável atribuída a você.

### Uma mensagem na Sala aprova ou conclui alguma etapa?

Não. Conversa não substitui ação formal do owner.

### Posso criar uma tarefa livre?

Não na V1. Minhas tarefas projeta trabalho dos processos.

### Por que não vejo Administração?

A área exige `controllership-finance.manage`.

### Salvar uma alteração administrativa publica automaticamente?

Não. Draft e publicação são etapas diferentes.

### Alterar um template muda a competência que já está aberta?

Não. A competência preserva o snapshot aplicável à sua abertura.

### O que significa fechamento concluído?

Somente o contract implementado pode determinar. Estoque fechado e pacote enviado são estados distintos; não inferir conclusão por um deles isoladamente.

### Existe tolerância de centavos na conciliação?

Não.

```text
R$ 0,00 = paridade
qualquer valor diferente de zero = divergência
```

### O Portal altera diretamente classificação ou fechamento no Protheus?

Na V1, não para as ações explicitamente documentadas como sem write ERP.

---

# 11. Glossário

Section id:

```text
glossary
```

Termos mínimos:

| Termo | Significado | Onde aparece |
|---|---|---|
| ACCESS | acesso operacional ao Portal | superfícies operacionais |
| MANAGE | administração/configuração | Administração |
| Competência | período mensal do fechamento | Central de Fechamento |
| Snapshot | configuração congelada para um contexto | P2/P6 |
| Preliminary | resultado ainda não final | P3/Visão geral |
| Freshness | momento/versão da fonte | dashboards/cockpit |
| Blocker | condição que impede avanço | P1/P2/P3/P5 |
| Evidência | arquivo/dado que suporta item | P2 |
| Validator | responsabilidade de validação | P2/P6 |
| Replacement | nova evidência após rejeição | P2 |
| Cutoff | marco que encerra movimentos relevantes | P3 |
| Revalidação | nova validação após cutoff/mudança | P3 |
| Divergência | diferença da conciliação | P3 |
| Pendência | item aguardando análise/ação | P4 |
| TaskProjection | projeção pessoal de trabalho owner | Minhas tarefas |
| Sala contextual | conversa vinculada a objeto de trabalho | Sala |
| Finalizar | congelar versão do pacote | P5 |
| Enviar | submeter versão finalizada para revisão autenticada na Minha DELPI | P5 |
| Effective from | data de vigência administrativa | P6 |
| Inativação | fim prospectivo de uso | P6 |

Glossário deve refletir somente terminologia vigente.

---

## Links internos no texto

Seguir o padrão Comercial/Suprimentos:

```text
manual text
→ token/label reconhecido
→ route registry
→ link interno seguro
```

Exemplo conceitual:

```text
"Início"
→ route home

"Visão geral"
→ route overview

"Minhas tarefas"
→ route my-tasks
```

Não parsear URL livre embutida em conteúdo.

Usar registry tipado de destinos.

Somente destinos implementados e autorizados entram no registry runtime.

---

## Modelo lógico de conteúdo

Exemplo:

```ts
type UserManualSection = {
  id: string;
  title: string;
  intro?: string;
  bullets?: readonly string[];
  links?: readonly UserManualLinkRow[];
  faqs?: readonly UserManualFaq[];
  glossary?: readonly UserManualGlossaryEntry[];
  requiresFeature?: FeatureId;
  requiresPermission?: "controllership-finance.manage";
};
```

TARGET:

```text
USER_MANUAL_CONTENT
MANUAL_TOOL_TARGETS
USER_MANUAL_TERM_CATALOG
```

Nomes físicos finais podem seguir o padrão do Portal quando o MFE existir.

---

## Feature gating do manual

Pipeline lógico:

```text
DOCUMENTED TARGET
→ route/capability implemented
→ runtime feature catalog says available
→ permission check
→ manual section/link becomes visible
```

Não usar roadmap como feature flag.

### Regra de seção

Uma seção operacional pode entrar no manual se:

```text
route exists
AND capability implemented
AND viewer authorized
```

### Regra de conceito

Conceito geral pode existir mesmo que uma subfeature ainda não esteja disponível, desde que:
- não instrua uso de botão inexistente;
- não ofereça link para rota futura;
- não prometa capability.

---

## Help contextual

Cada página material deve possuir um entrypoint de Ajuda contextual quando isso melhorar compreensão.

Target:

```text
Page / section
→ "Ajuda" / HelpTooltip / hint
→ /apps/controllership-finance/help#manual-{sectionId}
```

### Mapa

| Página | Help target |
|---|---|
| Início | `#manual-home` |
| Visão geral | `#manual-overview` |
| Sala de interação | `#manual-interaction-room` |
| Minhas tarefas | `#manual-my-tasks` |
| Administração | `#manual-administration` |
| P1–P5 | `#manual-closing` ou subâncora futura |
| Página do usuário | `#manual-user-profile` |

Tooltips de campo continuam locais ao controle e curtos.

---

## Deep link / hash behavior

Ao abrir:

```text
/help#manual-my-tasks
```

o consumidor deve:
1. validar que a seção existe e está visível para o viewer;
2. carregar o manual;
3. focar/rolar para a seção;
4. não bypassar permission;
5. manter heading identificável.

Se hash aponta para seção:
- desconhecida → topo do manual ou not-found local amigável;
- não autorizada → não revelar conteúdo; voltar ao topo/section geral.

Não retornar 403 da página inteira apenas porque uma subseção MANAGE foi solicitada por hash; a rota Help continua ACCESS, mas o conteúdo MANAGE permanece oculto.

---

## Estados

Ajuda é conteúdo local/versionado.

Portanto não depende de source operacional para renderizar conteúdo base.

### LOADING

Somente se houver code-splitting/loading do bundle.

Não simular carregamento de API inexistente.

### SUCCESS

Manual renderizado com seções disponíveis.

### EMPTY

Não é estado esperado do manual publicado.

Se content registry resultar vazio:
- tratar como erro de build/config;
- não mostrar `Nenhuma ajuda disponível` como estado normal.

### ERROR

Falha de bundle/renderização.

Usar error boundary/chrome comum.

### FORBIDDEN

Sem `controllership-finance.access`:
- 403;
- manual não renderiza.

### NOT_FOUND

Rota `/help` existe.

Hash inválido não deve virar 404 da aplicação inteira.

### PARTIAL

Não usar PARTIAL para esconder feature ainda não implementada.

Feature ausente simplesmente não entra no manual.

### UNAVAILABLE

Não é estado normal do conteúdo base, porque o manual é versionado no MFE.

Usar apenas quando uma dependência necessária para montar a experiência segura estiver indisponível, por exemplo:
- effective access necessário para filtrar seção MANAGE não pode ser resolvido;
- registry/router necessário aos tool links falhou de forma material.

Nesses casos:
- não expor seção restrita por fallback;
- não converter indisponibilidade em conteúdo vazio enganoso;
- conteúdo comum pode permanecer quando a autorização necessária já estiver comprovada e a falha for isolável.


---

## Light / dark

```text
SAME DOM
SAME CONTENT
SAME TOC
+ THEME TOKENS
```

Sem versão separada do manual por tema.

---

## Responsividade

Desktop:
- TOC lateral;
- conteúdo principal;
- tabelas/FAQ/glossário.

Mobile:
- TOC adaptado pelo kit;
- conteúdo em uma coluna;
- guide table permanece legível/scroll-safe;
- tool links continuam acessíveis;
- nenhum item depende de hover.

---

## Acessibilidade

Obrigatório:
- heading único de página;
- TOC dentro de `nav` com aria-label;
- botões do TOC operáveis por teclado;
- `section` com id estável;
- foco/scroll contextual previsível;
- links com nomes compreensíveis;
- tabelas com headings semânticos;
- FAQ com `dt/dd`;
- glossary com `dt/dd`;
- HelpTooltip acessível via foco;
- estado/permissão não comunicado só por cor;
- hash navigation não deve deixar foco perdido.

---

## Governança editorial

### Linguagem

UX em PT-BR.

Evitar:
- nomes de classes;
- endpoints;
- detalhes de DB;
- jargon técnico sem tradução;
- referências a código.

Technical identifiers só entram quando realmente ajudam o usuário, por exemplo permission codes no próprio perfil conforme decisão existente.

### Fonte

Cada seção deve apontar na documentação técnica para seu contract fonte.

No runtime, não exibir links ao GitHub/documentação técnica para uso normal.

### Exemplos

Exemplo ilustra regra.

```text
EXAMPLE != BUSINESS RULE
```

Não transformar valor histórico em threshold/regra.

### Terminologia

Se a feature muda nomenclatura:
- atualizar UI;
- manual;
- FAQ;
- glossary;
- tool links;
- tests estruturais
no mesmo gate.

---

## Política de sincronização

Toda mudança user-facing material deve verificar:

```text
PAGE COPY
ROUTE
ACTION
STATE
BUSINESS TERM
FILTER
PERMISSION BEHAVIOR
DEEP LINK
→ HELP IMPACT?
```

Se `YES`:
- Help muda no mesmo PR/slice.

### Mudanças que normalmente exigem Help

- nova página;
- nova ação;
- novo status;
- mudança de regra;
- mudança de filtro;
- nova source visível;
- nova mensagem de indisponibilidade;
- mudança de permission/comportamento;
- novo catálogo administrativo;
- novo deep link;
- mudança de terminologia.

### Mudanças que normalmente não exigem Help

- refactor interno sem efeito visível;
- performance sem mudança comportamental;
- alteração de teste;
- correção de typing sem UX;
- infraestrutura invisível.

---

## Testes estruturais futuros

Seguir padrão Comercial.

Validator/teste deve provar:

```text
USER_MANUAL_CONTENT exists
route /help exists
manifest includes /help
createDashboardUserManual is used
tool links are registered
TOC sections have unique ids
Help content contains only enabled features
Admin section is MANAGE-gated
contextual help targets resolve
glossary catalog is consistent
```

Não copiar assertions do Comercial sobre conteúdo comercial.

---

## RQ / AC

### RQ-HELP-01 — manual usa kit canônico

Aceite:
- `createDashboardUserManual`;
- PageHero/PagePath/SectionCard do kit;
- zero manual chrome local.

### RQ-HELP-02 — Ajuda é rota da topbar

Aceite:
- `/help`;
- item Ajuda na topbar;
- ACCESS necessário;
- F5 funciona.

### RQ-HELP-03 — conteúdo segue runtime

Aceite:
- capability futura não aparece;
- route inexistente não vira link;
- manual não usa roadmap como prova de disponibilidade.

### RQ-HELP-04 — capability gating

Aceite:
- seção Administração somente com MANAGE;
- usuário ACCESS-only não recebe instruções administrativas executáveis;
- nenhuma permission nova.

### RQ-HELP-05 — Help contextual usa deep link

Aceite:
- páginas materiais apontam para seção correta;
- hash válido rola/foca;
- hash inválido não quebra página;
- hash MANAGE não revela conteúdo sem MANAGE.

### RQ-HELP-06 — guide table é mapa operacional

Aceite:
- `Quero / Onde ir / Como`;
- destinos tipados;
- links somente para runtime implementado/autorizado.

### RQ-HELP-07 — conceitos preservam invariantes

Aceite:
- ATTACHED != VALIDATED;
- BLOCKER != MY_TASK;
- Finalizar != Enviar;
- ACCESS != MANAGE;
- source error != zero;
- preliminary != final.

### RQ-HELP-08 — Central de Fechamento acompanha P1–P5

Aceite:
- seções publicadas refletem apenas slices implementados;
- P5 não promete envio enquanto capability estiver bloqueada;
- P3 documenta paridade exata sem tolerância.

### RQ-HELP-09 — FAQ/glossário versionados

Aceite:
- termos usados nas telas;
- sem stale terminology;
- exemplos não viram regra.

### RQ-HELP-10 — sem backend de Help na V1

Aceite:
- nenhum BFF endpoint/table/CMS criado;
- conteúdo versionado no MFE;
- autorização continua na rota/app.

### RQ-HELP-11 — light/dark/mobile/a11y

Aceite:
- mesma estrutura;
- responsive;
- teclado/foco;
- TOC/nav semântico;
- tooltips acessíveis.

### RQ-HELP-12 — feature-help-sync obrigatório

Aceite:
- mudança user-facing material atualiza Help no mesmo gate;
- teste/validator detecta links/sections stale quando aplicável.

---

## Matriz futura de testes

### Positive
- ACCESS abre Ajuda;
- TOC navega para Conceitos;
- TOC navega para seção implementada;
- guide link abre rota real;
- hash abre seção;
- MANAGE vê Administração;
- FAQ renderiza;
- Glossário renderiza;
- Voltar ao Início;
- Help contextual chega à seção esperada.

### Sibling
- habilitar feature A não publica B;
- MANAGE section não altera conteúdo comum;
- remover tool link de rota desativada não remove conceito geral válido;
- atualização de P2 não altera texto P3 indevidamente.

### Negative
- sem ACCESS;
- ACCESS-only tentando hash de Administração;
- link para rota não implementada;
- seção futura publicada;
- manual mencionando botão inexistente;
- stale nomenclature;
- hash inválido;
- URL arbitrária em tool link;
- endpoint/table/CMS de Help criado sem nova decisão;
- duplicação de manual chrome local.

### Experiência
- desktop;
- mobile;
- light;
- dark;
- teclado;
- foco;
- TOC;
- scroll/foco respeitando `prefers-reduced-motion`;
- FAQ;
- glossary;
- contextual deep link;
- 403;
- error boundary.

---

## Scripts / validators planejados

Não criar agora.

```text
validate-help-route
- /help existe
- manifest/router consistentes
- ACCESS guard

validate-help-section-registry
- ids únicos
- source docs conhecidos
- feature/permission gates válidos

validate-help-tool-links
- destino tipado
- rota implementada
- no arbitrary URL

validate-help-capability-gating
- feature disabled => section/link absent
- MANAGE section hidden for ACCESS-only

validate-help-contextual-links
- page → section target existente
- hash roundtrip

validate-help-terminology
- glossary/FAQ termos canônicos
- no deprecated labels

validate-help-sync
- feature user-facing material possui seção/help impact explicitamente avaliado

validate-help-plugin-ui
- createDashboardUserManual used
- no duplicated manual chrome
```

Tecnologia/localização seguem padrão vigente no HEAD futuro.

---

## Inventários técnicos restantes

### HELP01 — route/catalog binding

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Revalidar router, manifest e catálogo real de features quando o MFE existir.

### HELP02 — permission-aware section filtering

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Reusar effective permissions já carregadas pelo Portal; não criar fetch/AuthZ paralelo só para Help.

### HELP03 — hash/focus behavior

```text
TO_VALIDATE_WITH_PLUGIN_UI
```

Confirmar melhor comportamento de scroll/foco com o `Manual.Layout` atual.

Se capability reutilizável estiver faltando:
- evoluir `plugin-ui`;
- não clonar layout.

### HELP04 — structural validator placement

```text
TO_INVENTORY_BEFORE_IMPLEMENTATION
```

Seguir convenções do MFE futuro.

Nenhum desses itens reabre as decisões D-HELP-01..06.

---

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED  = PASS
OWNERS_DEFINED              = PASS
VISUAL_SPEC_DEFINED         = PASS
CONTRACT_DEFINED            = PASS
AUTHZ_DEFINED               = PASS
PLUGIN_UI_REUSE_DEFINED     = PASS
STATES_DEFINED              = PASS
DEEP_LINK_F5_DEFINED        = PASS
RESPONSIVE_DEFINED          = PASS
LIGHT_DARK_DEFINED          = PASS
A11Y_DEFINED                = PASS
HELP_SYNC_DEFINED           = PASS
RQ_AC_DEFINED               = PASS
TEST_MATRIX_DEFINED         = PASS
SCRIPTS_ARTIFACTS_PLANNED   = PASS
IMPLEMENTATION_AUTHORIZED   = NO
```

Inventários:
- HELP01 route/catalog binding;
- HELP02 permission-aware filtering;
- HELP03 hash/focus behavior;
- HELP04 validator placement.

Nenhum deles cria backend/CMS de Help nem reabre D-HELP-01..06.

Resultado:

```text
A07 AJUDA
= READY_FOR_IMPLEMENTATION_BRIEF
!= IMPLEMENTED
```

## Resultado esperado

```text
FEATURE EXISTS
→ USER SEES FEATURE
→ HELP EXPLAINS FEATURE
→ CONTEXTUAL LINK OPENS RIGHT SECTION
→ SAME TERMINOLOGY / SAME RULE
```

Sem manual paralelo, sem documentação de capability futura no runtime e sem Help stale.


## Adendo de governança — decisões PO C2 e D-P5-01 a D-P5-05 (15/10/2026)

**TARGET / DECIDED_BY_PRODUCT_OWNER / DOCUMENTATION_REBASELINE_PENDING**. Registro de decisão, não evidência de runtime nem aprovação de freeze. Este adendo prevalece sobre referências anteriores a C1/C2/C3 como decisão aberta; semânticas derivadas ainda pendentes não devem ser inferidas.

- **C2:** conclusão mensal exige todos os pacotes aplicáveis submetidos, todas as revisões obrigatórias aceitas e nenhum esclarecimento aberto. Submissão ou e-mail de notificação não concluem fechamento.
- **D-P5-01:** podem existir múltiplos reviewers por RecipientPackage; **todos os reviewers obrigatórios** precisam aceitar. Aceite parcial não atende ao quorum.
- **D-P5-02:** esclarecimento sem mudança de conteúdo mantém PackageVersion; qualquer conteúdo modificado exige nova PackageVersion, preservando a anterior e seu histórico.
- **D-P5-03:** aceite não pode ser revertido pela UI V1; correção extraordinária não está automaticamente autorizada.
- **D-P5-04:** ao perder ACCESS efetivo, reviewer perde a capacidade de agir; atribuição e histórico são preservados; substituição exige reatribuição autorizada, auditável e validada pela BFF/Core (fail-closed).
- **D-P5-05:** solicitação de alterações (CHANGES_REQUESTED) e rejeição terminal (REVIEW_REJECTED) são outcomes distintos; não usar um como alias do outro.

Regra alvo:

```text
ALL_APPLICABLE_PACKAGES_SUBMITTED
AND ALL_REQUIRED_REVIEWS = REVIEW_ACCEPTED
AND NO_OPEN_CLARIFICATION
=> MONTHLY_CLOSING_COMPLETED
```

**DECISION_REQUIRED / NO CHANGE TO BEHAVIOR:** definir escopo da terminalidade de REVIEW_REJECTED (submissão vs pacote), regra de substituição/aceite anterior, congelamento ou alteração auditada do conjunto de reviewers obrigatórios, necessidade de novo quorum por versão e tratamento da competência quando houver rejeição terminal. Nenhum endpoint, migration, scaffold ou permission adicional está autorizado.

**Evidência pendente:** rebase do main, .cursor aplicável, ledger RQ/AC, Core effective permissions, test matrix positive/sibling/negative, Help, postcondition. `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`.


## Decisões supervenientes do Product Owner — P5-A a P5-E (15/10/2026)

**TARGET / PO_APPROVED / DOCUMENTATION_ONLY — no runtime changes.** Este registro complementa C2 e prevalece sobre a interpretação anterior de D-P5-01 (unanimidade por identidade): o quórum é por **área/especialidade obrigatória**, não por cada usuário elegível. A multiplicidade de pessoas elegíveis na mesma área não cria múltiplos votos obrigatórios.

| Decisão | Regra aprovada | Relação com decisão anterior |
|---|---|---|
| P5-A | Um aceite por área obrigatória, executável por qualquer usuário elegível daquela área | D-P5-01 reinterpretada: unanimidade de áreas obrigatórias, não de pessoas |
| P5-B | Somente autor de um aceite pode alterá-lo; outra pessoa atua somente com reatribuição formal | Complementa D-P5-03; sem reversão livre na UI V1, preservar trilha imutável |
| P5-C | ACCESS efetivo + grupo/função corporativa + escopo do recurso + regra de negócio | Complementa D-P5-04; Core é owner da identidade/effective permissions; P5 controla workflow e scope |
| P5-D | Rejeição terminal encerra a competência em estado REJECTED, distinto de MONTHLY_CLOSING_COMPLETED; não exige ressubmissão | Concretiza D-P5-05, mantendo CHANGES_REQUESTED distinto de rejeição terminal |
| P5-E | Nova PackageVersion exige novo aceite de todas as áreas obrigatórias, sem herdar aceites da versão anterior | Complementa D-P5-02 e preserva versionamento imutável |

**C2 atualizado semanticamente:** conclusão mensal requer todos os pacotes aplicáveis submetidos, aceites válidos da **versão vigente** para cada área obrigatória e nenhuma clarification aberta. Qualquer rejeição terminal impede MONTHLY_CLOSING_COMPLETED e resulta no desfecho de competência rejeitada, com auditoria. Não inferir que uma permission genérica concede approval irrestrito.

**AuthZ invariant:** JWT identifica; Core resolve `controllership-finance.access` efetivo; BFF valida função/grupo corporativo elegível, área obrigatória, resource scope/ownership e business rule, fail-closed. A origem/contrato preciso do grupo/função Core permanece **TO_INVENTORY (T05)**; não criar permission code para reviewer, área, botão, filial ou unidade. `controllership-finance.manage` não substitui ACCESS.

**Auditoria mínima:** ator Core, ação, instante, competência, recipient package, PackageVersion, área/atribuição usada, decisão e justificativa quando aplicável, mudança de responsável e referência ao evento anterior. Registro original não é apagado ou reatribuído retroativamente; mudança é novo evento auditável.

**DECISION_REQUIRED / ainda não inferir:** (1) efeito de reatribuição formal sobre aceite já registrado; (2) procedimento de alteração do próprio aceite compatível com irreversibilidade da UI V1; (3) mapeamento/configuração de áreas obrigatórias e elegibilidade corporativa; (4) momento e autoridade da rejeição terminal da competência quando mais de uma área participa; (5) tratamento das tarefas pendentes dos demais revisores após rejeição terminal. Separar decisões de produto de inventários físicos (DTO, Core eligibility resolver, storage, adapters).

**Gate:** `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_RULES`; `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `IMPLEMENTATION_AUTHORIZED = NO`. Estes textos registram decisões de produto, não demonstram testes, código, contratos físicos, rebase nem execução de smoke.

**Conteúdo futuro Help (não publicar como runtime antes da feature):** revisão requer um aceite por área obrigatória, executado por usuário elegível, não um aceite por cada pessoa. Nova versão exige todos os aceites novamente. Rejeição terminal encerra a competência como rejeitada, distinta de conclusão; pedir alterações não é rejeição terminal. Alteração/substituição de aceite deve seguir regra auditada ainda pendente.


## Decisões PO P5-F a P5-J — consolidação contratual vigente (16/10/2026)

**TARGET / PO_APPROVED / DOCUMENTED_NOT_IMPLEMENTED.** Este adendo é superveniente aos registros de perguntas abertas P5-F..J e prevalece quando notas históricas anteriores conflitarem. C2, D-P5-02..05 e P5-A..E permanecem válidas nos termos abaixo. A antiga unanimidade de *pessoas* em D-P5-01 foi substituída pela unanimidade das *áreas obrigatórias* em P5-A.

| ID | Resultado aprovado | Invariante |
|---|---|---|
| **P5-F = A** | Substituição de responsável mantém válido o aceite já realizado para a mesma área e PackageVersion; a autoria permanece a do executor original. Substituto assume somente ações futuras. | REASSIGNMENT != INVALIDATE_PRIOR_ACCEPTANCE |
| **P5-G = A** | Aceite P5 não é reversível/alterável pela UI V1. Eventual erro exige processo excepcional separado, formal, auditado e **não autorizado enquanto seu contrato não for aprovado**. | NO_P5_ACCEPTANCE_REVERSAL_IN_V1 |
| **P5-H = A** | P6 configura por tipo de pacote as áreas/especialidades obrigatórias em versão governada; P5 congela a configuração aplicável na submissão. Core fornece identidade, effective permissions e atributos de grupo/função conforme contrato a inventariar. | REVIEW_AREA_SET_SNAPSHOTTED_ON_SUBMISSION |
| **P5-I = B** | Reviewer elegível registra rejeição do pacote em nome da área; uma **autoridade operacional formalmente definida**, distinta da simples permission MANAGE, confirma com justificativa e auditoria a rejeição terminal da competência. | AREA_PACKAGE_REJECTION != TERMINAL_COMPETENCE_REJECTION |
| **P5-J = A** | Após confirmação da rejeição terminal, a competência fica rejeitada e todas as projeções/tarefas de revisão ainda acionáveis deixam de sê-lo; histórico, decisões e autoria permanecem consultáveis conforme AuthZ. | REJECTED_COMPETENCE != MONTHLY_CLOSING_COMPLETED |

### Compatibilidade com regras anteriores

- **C2:** competência concluída somente se TODOS os pacotes aplicáveis foram submetidos, TODAS as áreas obrigatórias aceitaram a PackageVersion vigente e NÃO há esclarecimento aberto. Competência rejeitada nunca satisfaz `MONTHLY_CLOSING_COMPLETED`.
- **P5-A / D-P5-01:** quorum de um aceite por área obrigatória, executado por qualquer usuário elegível; não por indivíduo. Dois elegíveis na mesma área não criam dois aceites necessários.
- **P5-B / D-P5-03 / P5-G:** ninguém sobrescreve aceites; nem o autor pode revertê-los pela UI V1. A referência antiga a “autor pode alterar” é **superseded para aceite P5 na V1**. Reatribuição formal não autoriza mutação de decisões anteriores.
- **P5-C / D-P5-04:** ACCESS efetivo + grupo/função corporativa elegível + escopo do recurso + regra da ação; avaliação server-side fail-closed; reviewer assignment nunca se torna novo permission code.
- **D-P5-02 / P5-E:** esclarecer sem alterar conteúdo preserva versão; qualquer alteração de conteúdo cria nova PackageVersion e **exige novos aceites de todas as áreas obrigatórias**; histórico de versões anteriores preservado.
- **D-P5-05 / P5-D / P5-I:** `CHANGES_REQUESTED` não é `REVIEW_REJECTED`; rejeição da área/pacote não encerra competência automaticamente; só confirmação por autoridade operacional a leva ao estado terminal rejeitado.
- **P5-F / P5-H:** reatribuir elegível não altera aceite já registrado, nem o snapshot de áreas obrigatórias da submissão; edição futura do catálogo P6 não altera snapshots abertos.
- **P5-J:** `TaskProjection != TaskEntity`; P5 continua owner do lifecycle; revisão terminal rejeitada remove acionabilidade, sem hard delete nem apagamento de evidências.

### Trilha de auditoria obrigatória

Preservar identidade Core do ator, data/hora, ação, contexto competência/recipient package, versão, área obrigatória, elegibilidade/scope verificados, motivo/justificativa quando exigidos, estado anterior/posterior, autor original do aceite, referência a reatribuições, confirmação formal da rejeição e correlação da projeção/notificação. Histórico é append-only no nível semântico; **schema físico não definido**.

### Pendências reais — sem aprovação presumida

1. **DECISION_REQUIRED:** quem é a autoridade operacional de confirmação de rejeição terminal; como é designada e substituída, e se a confirmação pode ser negada (e qual estado fica então). Não equiparar automaticamente a `manage`.
2. **DECISION_REQUIRED:** procedimento excepcional de correção de aceite P5 fora da UI V1 (owner, autorização, efeitos na conclusão mensal e revalidação), se for implementado nesta versão; na ausência de decisão, **capability não existe na V1**.
3. **TO_INVENTORY / STOP ON DRIFT:** fonte canônica dos grupos/funções corporativas e sua associação às áreas, contract Core (T05), elegibilidade de múltiplos usuários; não presumir que RBAC do Core tem os atributos necessários.
4. **CONTRACT_PENDING:** mapa versionado tipo de pacote → áreas obrigatórias em P6; regras de publicação/vigência/snapshot, defaults inválidos, configuração ausente e concorrência; não inventar tabelas/migrations.
5. **CONTRACT_PENDING:** outcome de rejeição do pacote versus confirmação terminal da competência, estados técnicos definitivos, falha/conflito no commit, event projection/notifications/Help e matrizes de testes positive+sibling+negative.

**Gates:** `DOCUMENTATION_CLOSURE_COMPLETE = NO`; `PRODUCT_CONTRACT_FREEZE = PENDING_DERIVED_CONTRACT_AND_OWNER`; `IMPLEMENTATION_AUTHORIZED = NO`. Nenhum teste de runtime foi executado; `TEST_NOT_RUN`. Nenhum merge/rebase autorizado por este registro.

**Ajuda planejada P5-F..J:** aceites por área são registrados por usuário elegível; reatribuição não troca autor nem desfaz aceite válido; aceite P5 é irreversível na UI V1; áreas exigidas vêm da configuração P6 congelada na submissão; rejeição do pacote passa por confirmação da autoridade operacional para rejeitar a competência; tarefas deixam de ser acionáveis após rejeição terminal. Só publicar manual quando capability estiver implementada.


## Decisões finais do PO — DEC-01 a DEC-04 (16/10/2026)

**TARGET / PO_APPROVED / NOT_IMPLEMENTED.** Vigência: este contrato substitui referências históricas a `DECISION_REQUIRED` sobre autoridade de rejeição, negativa de confirmação, exceção de reversão na V1 e publicador P6. Não equivale a evidence de testes ou freeze.

| ID | Decisão aprovada | Contrato normativo |
|---|---|---|
| DEC-01 | Responsável formal da Controladoria | A pessoa designada para coordenar o fechamento da competência pode confirmar rejeição terminal **somente** com `controllership-finance.access` efetivo, vínculo operacional, escopo do recurso e business rule verificados server-side. `manage` isolado não concede essa autoridade. A designação/substituição deve ser auditada; owner da identidade/permissão é Core; owner do vínculo operacional é o contexto P5. |
| DEC-02 | Rejeição pendente se não confirmada | Rejeição pela área/pacote cria proposta de rejeição da competência; até decisão formal ela não está `MONTHLY_CLOSING_COMPLETED` nem terminalmente rejeitada. Autoridade registra decisão/motivo; pode devolver análise para esclarecimento ou correção nas transições autorizadas. Não apagar evento original. |
| DEC-03 | Sem correção excepcional de aceite P5 na V1 | Aceite P5 é irreversível pela UI e não existe endpoint de reversão/retificação na V1. Incidentes são registrados e encaminhados a processo **fora do fluxo do Portal**, sem presumir ação técnica, override, database edit ou reversão automática. P2 validação de evidência mantém contrato próprio. |
| DEC-04 | P6 publica configuração com MANAGE | Usuário com `controllership-finance.manage` efetivo **e** escopo administrativo publica nova configuração versionada de áreas obrigatórias por tipo de pacote, com justificativa, auditoria e vigência prospectiva. Competências e submissões existentes mantêm snapshots; MANAGE não implica ACCESS operacional. |

### Consistência transversal

C2 continua exigindo todos os pacotes aplicáveis submetidos, **um aceite válido de cada área obrigatória** sobre a versão atual, e nenhuma clarification aberta. Uma competência terminalmente rejeitada é desfecho diferente de conclusão, dependente de confirmação DEC-01. P5-A..J permanecem vigentes: aceites auditados por ator; reatribuição não troca autoria ou invalida aceite vigente; nova versão reinicia aceites obrigatórios; envio é submissão interna; rejeição terminal desativa TaskProjections acionáveis e preserva histórico. `CHANGES_REQUESTED` não é `REVIEW_REJECTED`.

### AC mínimos (PLANNED / TEST_NOT_RUN)

- DEC-01: reviewer de área não consegue encerrar competência; coordenador com ACCESS + vínculo + scope consegue confirmar; MANAGE sem vínculo/ACCESS falha; ausência de Core/elegibilidade falha fechada.
- DEC-02: rejeição de área sem confirmação mantém estado pendente; negativa motivada permanece auditável e permite devolução somente por transição contratada; nenhuma conclusão automática.
- DEC-03: nenhum endpoint ou ação UI V1 altera aceite P5; eventos originais imutáveis e incidentes externos não falsificam C2.
- DEC-04: MANAGE + escopo publica com motivação e versionamento; ACCESS sem MANAGE não publica; submissão anterior não muda; nova submissão adota versão conforme vigência autorizada.

### Pendências técnicas distintas de escolhas PO

**TO_INVENTORY:** contrato Core T05 de effective permissions e atributos corporativos; source do coordenador/vínculo/eligibilidade; owner/contrato físico de persistência e eventos; formato de estados/DTOs, versionamento P6 e CAS/concorrência; UX, notifications, help e projections. **CONTRACT_PENDING:** mapear transições específicas e outcomes da negativa no ledger e testes; identificar .cursor e padrões HEAD aplicáveis. Não declarar `PASS` sem inspeção de código/producers/consumers/testes e reconciliação da branch com main.

`DECISION_REQUIRED_PRODUCT_P5=NONE_IDENTIFIED_AFTER_DEC01_DEC04` (sujeito a inventário material posterior); `DOCUMENTATION_CLOSURE_COMPLETE=NO`; `IMPLEMENTATION_AUTHORIZED=NO`; `TEST_NOT_RUN`.
