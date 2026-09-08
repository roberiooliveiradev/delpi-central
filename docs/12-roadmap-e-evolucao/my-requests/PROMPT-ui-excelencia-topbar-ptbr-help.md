# Prompt de implementação — excelência visual, TopBar, PT-BR e Ajuda em todo o `my-requests`

> **Módulo:** Minhas Solicitações (`plugins/my-requests` + `requests-api`)  
> **Superfície:** **todas** as telas e subfluxos do plugin  
> **Status:** prompt de produto/engenharia — **implementado (E20)**  
> **Referência visual principal:** `plugins/commercial` (Portal Comercial)  
> **UI kit obrigatório:** `@delpi/plugin-ui` via Module Federation  
> **Docs irmãs:** [WIREFRAMES.md](./WIREFRAMES.md) · [MANUAL-USUARIO.md](./MANUAL-USUARIO.md) · [PLAYBOOK.md](./PLAYBOOK.md) · [plugin README](../../../plugins/my-requests/README.md)

### Evidências E20 (S0–S9)

- Código: `MyRequestsTopBar` + `presentationLabels` + `helpTooltips` user-facing; ActionBar/listas/detalhe/painéis/admin consomem labels.
- Testes/build: `cd plugins/my-requests && npm test && npm run typecheck && npm run build` — verde (39 testes).
- Rebuild MFE: `./infra/scripts/up-dev-sequential.sh --fase mfe --build my-requests` — `delpi-my-requests` recriado.
- Smoke visual §30 (claro/escuro/desktop/mobile): validar no Portal federado após rebuild — TopBar collapse, labels PT, Ajuda por tela.

Use este arquivo como **brief único de implementação** para elevar toda a experiência do plugin **Minhas Solicitações**. O trabalho não se limita às telas dos prints: deve revisar o shell, todas as rotas, formulários especializados/genéricos, detalhe e todos os painéis internos.

---

## 1. Objetivo

Transformar o `my-requests` em um módulo visualmente maduro e coerente com o Portal Comercial, sem alterar as fronteiras arquiteturais já definidas.

Entregar, no mesmo esforço:

1. **TopBar canônica** no padrão do `plugins/commercial`, usando `createDashboardTopBar` de `@delpi/plugin-ui`.
2. **Melhoria visual completa** de todas as telas e estados do plugin.
3. **100% da UI visível ao usuário em PT-BR**, sem expor códigos técnicos quando existir apresentação amigável.
4. **Ajuda contextual em todas as telas e seções relevantes**, usando componentes do `plugin-ui` e conteúdo centralizado.
5. **Responsividade real** em desktop, tablet e mobile.
6. **Tema claro/escuro** herdado do Portal, sem CSS isolado.
7. **Zero regressão funcional** em workflow, RBAC, deep links, filtros, uploads, paginação e integrações.
8. **Sincronização obrigatória de Ajuda e documentação** no mesmo PR.

---

## 2. Contexto arquitetural travado — não redecidir

Estas decisões são anteriores a este prompt e **não podem ser quebradas por uma melhoria visual**:

- O MFE `my-requests` chama **somente** `/apps/requests-api`.
- É proibido o browser chamar `/apps/api-delpi` diretamente.
- `requests-api` é o bounded context dono do domínio de solicitações.
- `allowed_actions` é calculado no backend; o MFE é **render-only**.
- O MFE não implementa máquina de estados paralela.
- Validação de negócio continua na API; frontend faz apenas validação de UX.
- O registry de `RequestType` continua dinâmico.
- `/apps/my-requests` é a única rota registrada no manifesto; `/mine`, `/work-queue`, `/new`, `/requests/:id` e `/admin` continuam rotas internas do MFE.
- RBAC continua vindo do contexto já existente do plugin.
- Componentes visuais compartilháveis pertencem ao `plugin-ui`, não ao MFE.
- CSS de componentes do kit dentro do MFE continua proibido.

---

## 3. Regras `.cursor` obrigatórias para esta implementação

Antes de alterar código, carregar somente as regras aplicáveis, especialmente:

- `.cursor/rules/evidence-driven-execution.mdc`
- `.cursor/rules/plugins-reusable-components.mdc`
- `.cursor/rules/plugins-visual-design-system.mdc`
- `.cursor/rules/plugin-mfe-page-excellence.mdc`
- `.cursor/rules/feature-help-sync.mdc`
- `.cursor/rules/clean-code-architecture-guardrails.mdc`
- `.cursor/rules/english-code-identifiers.mdc`
- `.cursor/rules/test-and-commit.mdc`
- `.cursor/rules/mf-federation-patch-safety.mdc` **somente se `plugin-ui` precisar ser alterado**

Princípios que valem para todo o trabalho:

```text
kit-first
→ conteúdo PT-BR centralizado
→ zero CSS de componente do kit no MFE
→ ajuda no mesmo entregável
→ contratos antes de polish
→ nenhuma regra de negócio duplicada no frontend
```

---

## 4. Inventário obrigatório — revisar TODAS as superfícies

A implementação deve começar por um inventário do código real e não somente pelos screenshots.

### 4.1 Shell e roteamento

Revisar:

- `plugins/my-requests/src/App.tsx`
- `plugins/my-requests/src/components/AppShell.tsx`
- `plugins/my-requests/src/hooks/useMyRequestsRouterPath.ts`
- `plugins/my-requests/src/ui/mrUi.tsx`
- `plugins/my-requests/src/ui/mrUiContracts.ts`
- `plugins/my-requests/src/index.css`
- `plugins/my-requests/src/content/helpTooltips.ts`

### 4.2 Telas principais

Revisar integralmente:

| Rota/superfície | Arquivo principal |
|---|---|
| `/mine` | `pages/MinePage.tsx` |
| `/work-queue` | `pages/WorkQueuePage.tsx` |
| `/new` | `pages/NewRequestPage.tsx` |
| criação genérica | `pages/GenericCreateForm.tsx` |
| criação schema-driven | `features/raw-material-creation/SchemaFormPage.tsx` |
| wizard emissão NF | `features/invoice-issuance/ui/InvoiceIssuanceWizard.tsx` |
| `/requests/:id` | `pages/RequestDetailPage.tsx` |
| `/admin` | `pages/AdminTypesPage.tsx` |
| sem acesso | estado de acesso em `App.tsx` |
| tipo specialized sem renderer | fallback em `NewRequestPage.tsx` |

### 4.3 Subsuperfícies do detalhe

Revisar também, como parte da mesma tela:

- `components/ActionBar.tsx`
- `components/TimelinePanel.tsx`
- `components/CommentsPanel.tsx`
- `components/AttachmentsPanel.tsx`
- `components/ArtifactsPanel.tsx`
- `components/ReasonConfirmModal.tsx`
- `features/invoice-issuance/ui/InvoiceIssuancePayloadPanel.tsx`

### 4.4 Conteúdo e apresentação

Revisar:

- `content/requestListFilters.ts`
- `content/requestTypeIcons.ts`
- `content/helpTooltips.ts`
- qualquer mapa de status, ação, evento, tipo, escopo de filial ou artefato visível ao usuário
- helpers de formatação de data/hora, números e valores

### 4.5 Documentação

Revisar e sincronizar:

- `docs/12-roadmap-e-evolucao/my-requests/WIREFRAMES.md`
- `docs/12-roadmap-e-evolucao/my-requests/MANUAL-USUARIO.md`
- `docs/12-roadmap-e-evolucao/my-requests/PLAYBOOK.md` apenas onde o estado visual/etapa mudar
- `plugins/my-requests/README.md`
- este prompt, alterando o status para **implementado** ao concluir

---

## 5. Diagnóstico confirmado no código atual

Não começar a implementação como se a UI estivesse vazia. Há uma base kit-first já existente e ela deve ser **evoluída**, não substituída por um design paralelo.

### 5.1 O que já está correto

- `mrUi.tsx` já centraliza factories do `@delpi/plugin-ui`.
- `MinePage` e `WorkQueuePage` já usam filtros, DataTable, StatusBadge, Empty, Loading e paginação do kit.
- `/new` já usa `NavigationCard` para os tipos.
- detalhe já usa `SectionCard`, `DetailFields`, Timeline, Modal e FileDropzone.
- `helpTooltips.ts` já existe como fonte de conteúdo de Ajuda.
- CSS atual é majoritariamente layout/tokens, sem recriar os componentes do kit.

### 5.2 Problemas visíveis e estruturais a corrigir

#### Shell

O shell atual usa:

```text
PageHeader
+ FormActions
+ quatro botões Minhas/Fila/Nova/Admin
```

Isso deve ser substituído por **TopBar canônica**, no padrão do Portal Comercial.

#### PT-BR incompleto

Hoje ainda podem aparecer diretamente na UI valores técnicos, por exemplo:

```text
raw-material-creation
submitted
created
view
start
cancel
required | optional | none
generic
invoice_pdf
specialized
schema_driven
```

Também existem mensagens técnicas como:

```text
RequestTypes
Tipo specialized
form_schema
my-requests.manage
lookup
Request Engine
WorkflowEngine
type_code
branch_scope
```

Esses termos podem continuar existindo em código, payloads, logs e documentação técnica, mas **não devem aparecer na experiência normal do usuário** quando houver texto de produto equivalente em português.

#### Helps atuais ainda são técnicos demais

`helpTooltips.ts` contém termos úteis para engenharia, mas inadequados para Ajuda de usuário, como:

- `deep link`
- `Request Engine`
- `schema-driven`
- `specialized`
- `lookup`
- `requests-api`
- `type_code`
- `branch_scope`
- descrição de state machine/frontend

A Ajuda do produto deve explicar **o que o usuário faz, o que vê e o que acontece**, não a implementação interna.

#### Detail atual expõe códigos brutos

O detalhe pode exibir:

- `type_code` no campo Tipo;
- status canônico quando `status_alias` não existir;
- actions brutas do backend;
- `event_type` bruto na timeline;
- timestamps ISO crus;
- `kind` bruto de artefato;
- valores crus do payload de emissão.

Tudo isso deve passar por uma camada de apresentação PT-BR.

---

## 6. TopBar — padrão Portal Comercial

### 6.1 Implementação canônica

Adicionar em `mrUi.tsx` uma factory baseada em:

```text
createDashboardTopBar({ prefix: MR_UI_PREFIX })
```

Usar como referência concreta:

- `plugins/commercial/src/app/PluginShell.tsx`
- `plugins/commercial/src/app/commercialUi.ts`

Não copiar CSS do Comercial. Reusar o **mesmo componente de `plugin-ui`** e configurar o `my-requests` com seus próprios itens, permissões e textos.

### 6.2 Itens da TopBar

A TopBar deve representar o módulo inteiro:

| id interno | Label PT-BR | Rota | Visibilidade |
|---|---|---|---|
| `mine` | **Minhas solicitações** | `/mine` | sempre para quem acessa o módulo |
| `work_queue` | **Fila de trabalho** | `/work-queue` | conforme acesso já existente |
| `new` | **Nova solicitação** | `/new` | somente se `canCreateAnyRequest` |
| `admin` | **Administração** | `/admin` | somente `canManage` |

Usar `lucide-react` para ícones, no mesmo padrão de densidade do Comercial.

Sugestão semântica:

- Minhas solicitações → `ClipboardList`
- Fila de trabalho → `ListChecks` ou equivalente já disponível
- Nova solicitação → `PlusCircle`
- Administração → `Settings` ou `SlidersHorizontal`

### 6.3 Estado ativo

O item ativo deve ser calculado a partir da rota interna real.

Regras mínimas:

```text
/mine ou /apps/my-requests       → mine
/work-queue                      → work_queue
/new e todos os forms de criação → new
/admin                           → admin
/requests/:id                    → manter contexto de origem se existir; na ausência, mine
```

Não manter a aba **Nova** ativa simplesmente porque o detalhe veio de uma criação anterior.

### 6.4 Responsividade

A TopBar deve usar o comportamento responsivo/collapsible do próprio componente compartilhado, seguindo o padrão do Comercial. Não criar segunda implementação mobile.

### 6.5 Ajuda na navegação

Cada item deve possuir `title`/help amigável em PT-BR proveniente de `helpTooltips.ts` ou conteúdo equivalente. Não hardcodar texto longo dentro do shell.

---

## 7. Estrutura visual comum das páginas

Depois da TopBar, todas as páginas devem seguir uma hierarquia consistente:

```text
TopBar
↓
PageHero ou PageHeader contextual
  título da tela
  descrição curta
  ajuda contextual
  badge/estado quando fizer sentido
↓
conteúdo operacional
  filtros / resumo / formulário / detalhe
↓
feedback
  loading / empty / erro / confirmação
```

Não criar um hero exagerado em toda página. Usar densidade **compacta** para liberar viewport, como o Comercial.

Se `createDashboardPageHero` for adequado, criar `MyRequestsPageHero` em `mrUi.tsx`. Caso a implementação atual do kit já tenha um `PageHeader` mais adequado para páginas operacionais, manter o componente canônico do kit e apenas reorganizar a composição.

---

## 8. Camada de apresentação PT-BR

Criar uma fonte única de apresentação para valores técnicos conhecidos. O nome do arquivo pode ser, por exemplo:

```text
src/content/requestPresentation.ts
```

ou equivalente coerente com a estrutura existente.

**Não** espalhar `switch` e mapas diferentes por página.

### 8.1 Status

Cobrir no mínimo:

| Valor técnico | UI PT-BR |
|---|---|
| `submitted` | Enviada |
| `pending` | Pendente |
| `in_progress` | Em andamento |
| `needs_information` | Aguardando informações |
| `returned` | Devolvida para ajuste |
| `completed` | Concluída |
| `issued` | Emitida |
| `cancelled` | Cancelada |
| `rejected` | Rejeitada |

Se a API já devolver alias de apresentação confiável, preferi-lo; o frontend deve ter fallback centralizado para códigos conhecidos.

Não alterar o valor enviado para API. Traduzir somente na camada de apresentação.

### 8.2 Ações permitidas

Cobrir no mínimo os actions atualmente existentes nos workflows:

| Código | Label PT-BR |
|---|---|
| `view` | Visualizar |
| `edit` | Editar |
| `start` | Iniciar atendimento |
| `return` | Devolver para ajuste |
| `resubmit` | Reenviar solicitação |
| `complete` | Concluir |
| `issue` | Registrar emissão |
| `cancel` | Cancelar solicitação |
| `reject` | Rejeitar |

A chamada HTTP continua enviando o **código técnico original**.

Além do label, mapear intenção visual quando o `ActionButton` suportar variante semântica apropriada, sem inventar CSS:

- ação principal/avanço → primary;
- editar/visualizar → secondary/ghost/link conforme contexto;
- cancelar/rejeitar → destructive/danger **somente se o kit suportar**;
- se o kit não suportar variante semântica necessária, estender `plugin-ui` de forma compartilhada e documentada, não criar CSS local.

### 8.3 Eventos da timeline

Nunca renderizar `event_type` cru.

Mapear eventos conhecidos, por exemplo:

```text
created           → Solicitação criada
status_changed    → Status atualizado
transitioned      → Etapa atualizada
comment_added     → Comentário adicionado
attachment_added  → Anexo enviado
artifact_added    → Artefato registrado
```

Antes de fechar o mapa, pesquisar os produtores reais em `requests-api` e cobrir **todos os event types vigentes**.

Evento desconhecido não deve quebrar a tela: usar fallback humanizado e neutro, sem vazar `snake_case` quando possível.

### 8.4 Datas e horas

Substituir ISO cru por formatação local:

```text
Intl.DateTimeFormat("pt-BR", ...)
```

Exemplo de saída:

```text
08/09/2026 às 12:20
```

Preservar o timestamp original em `title`/tooltip se isso ajudar auditoria, mas a leitura principal deve ser humana.

### 8.5 Tipos de solicitação

Listas e detalhe devem exibir **nome amigável do RequestType**, não `type_code` quando o catálogo estiver disponível.

Exemplo:

```text
raw-material-creation → Criação de matéria-prima
invoice-issuance      → Emissão de nota fiscal
```

Não criar enum fixo que substitua o registry. Resolver `code → name` a partir do catálogo da API; usar mapa local somente como fallback de apresentação onde necessário.

### 8.6 Escopo de filial

Em `/admin`, não mostrar `required|optional|none` diretamente.

Usar:

```text
required → Filial obrigatória
optional → Filial opcional
none     → Sem filial
```

### 8.7 Artefatos

Não mostrar `(generic)` ou `(invoice_pdf)` cru.

Usar labels centralizados, por exemplo:

```text
generic     → Documento de processamento
invoice_pdf → PDF da nota fiscal
```

### 8.8 Valores de emissão NF

No payload de emissão, traduzir valores de apresentação:

- tipo de NF → usar `INVOICE_TYPE_LABELS` já existente;
- frete → apresentar label apropriado;
- quantidades e preços → `Intl.NumberFormat("pt-BR")`;
- moeda, se aplicável, → `Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" })`;
- nunca exibir estrutura técnica do payload.

### 8.9 Checklist do wizard

A conferência atual não deve renderizar chaves técnicas do objeto retornado por `buildReviewChecklist`.

Cada item deve ter uma frase de produto em PT-BR, por exemplo:

```text
Destinatário selecionado
Itens informados
Tipo de nota fiscal definido
Dados de transporte válidos
Peso e volumes preenchidos
```

Preservar o booleano técnico somente internamente.

---

## 9. Ajuda contextual — obrigatória em todas as telas

### 9.1 Regra

Não considerar a entrega pronta enquanto cada tela e seção operacional não tiver Ajuda coerente.

A fonte canônica continua:

```text
plugins/my-requests/src/content/helpTooltips.ts
```

Pode ser reorganizada, mas não duplicada em componentes.

### 9.2 O que significa “help” neste prompt

Usar componentes reais do `@delpi/plugin-ui`, como:

- `HelpTooltip`
- `FieldLabel` com `hint`
- `SectionHintLabel`
- `createDashboardTitleWithHelp`
- suporte de help do `SectionCard`
- `title` dos itens da TopBar quando apropriado

**Não** considerar `div title="..."` como solução suficiente para todo o sistema de Ajuda.

O atributo `title` nativo pode existir como fallback de acessibilidade, mas as superfícies principais devem usar o padrão de Ajuda do kit.

### 9.3 Conteúdo deve ser para usuário, não para desenvolvedor

Remover da Ajuda normal termos como:

```text
requests-api
api-delpi
Request Engine
WorkflowEngine
state machine
lookup
schema-driven
specialized
type_code
branch_scope
deep link
```

Exemplo inadequado:

```text
Status e botões vêm de allowed_actions do WorkflowEngine.
```

Exemplo desejado:

```text
As ações exibidas dependem da etapa atual da solicitação e do seu perfil de acesso.
```

### 9.4 Cobertura mínima

| Superfície | Ajuda esperada |
|---|---|
| TopBar | finalidade de cada área |
| Minhas solicitações | o que aparece e como localizar uma solicitação |
| Busca | o que pode ser pesquisado |
| Tipo | significado do filtro |
| Status | significado do filtro |
| Filial | escopo da unidade |
| Fila de trabalho | quem aparece e por quê |
| Nova solicitação | como escolher o tipo |
| Cards de tipo | o que acontece ao abrir |
| Filial no formulário | quando é necessária |
| Wizard NF | objetivo geral + ajuda por etapa/campos relevantes |
| Schema form | instruções do formulário/tipo |
| Detalhe | o que representa a ficha |
| Ações | por que ações variam por usuário/status |
| Dados da emissão | resumo do conteúdo |
| Timeline | finalidade do histórico |
| Comentários | quem visualiza / para que usar |
| Anexos | arquivos enviados pelo solicitante |
| Artefatos | diferença para anexos |
| Administração | o que significa cada coluna |
| Modal devolver/cancelar | efeito da ação e necessidade do motivo |

---

## 10. Tela `/mine` — Minhas solicitações

### Objetivo visual

Virar uma lista operacional limpa e informativa, não um card vazio envolvendo filtros e uma tabela.

### Fazer

- TopBar com **Minhas solicitações** ativa.
- Header/hero compacto com:
  - título `Minhas solicitações`;
  - descrição curta: `Acompanhe as solicitações que você abriu.`;
  - help contextual.
- Manter FiltersKit do `plugin-ui`.
- Tornar filtros visualmente compactos e alinhados.
- Exibir `Tipo` pelo nome do RequestType.
- Exibir `Status` em PT-BR com variante semântica do badge.
- Exibir filial com label amigável quando existir metadado canônico; sem inventar nome se só houver código.
- Número continua deep link para detalhe.
- Empty state deve orientar o usuário:
  - sem dados: explicar que ainda não há solicitações e oferecer CTA **Nova solicitação** se autorizado;
  - com filtros: informar que nenhum resultado corresponde aos filtros e oferecer limpar filtros.
- Paginação só deve aparecer se houver dados; manter compacta.
- Se houver apenas uma página, avaliar conforme contrato do componente se a paginação pode ser omitida sem perda de UX.
- Não inventar KPI que a API não fornece.

---

## 11. Tela `/work-queue` — Fila de trabalho

Esta tela deve receber atenção especial: é bancada operacional.

### Fazer

- TopBar com **Fila de trabalho** ativa.
- Header/hero compacto:
  - `Fila de trabalho`;
  - descrição: `Solicitações disponíveis para atendimento no seu escopo.`;
  - help explicando que disponibilidade depende do perfil e da etapa.
- Reusar a mesma linguagem visual da lista `Minhas`, mas permitir maior ênfase operacional.
- Status em PT-BR e semanticamente colorido pelo kit.
- Tipo pelo nome amigável.
- Se o payload atual fornecer informações adicionais úteis (solicitante, data, prioridade, responsável), usar **somente campos reais já existentes**.
- Não inventar campos, SLA ou prioridade.
- Se o contrato atual for insuficiente para tornar a fila operacional, registrar gap de contrato e evoluir P0 antes do polish que depender dele.
- Empty state: `Não há solicitações aguardando atendimento no seu escopo.`
- Filtros e paginação seguindo o mesmo padrão de `/mine`.
- URL/filtros: preservar comportamento atual e, se o código já suportar query shareable, não regredir. Se não suportar e a regra `plugin-mfe-page-excellence` exigir nesta mudança, implementar de forma canônica e testada.

---

## 12. Tela `/new` — escolha do tipo

### Fazer

- TopBar com **Nova solicitação** ativa.
- Header/hero compacto:
  - `Nova solicitação`;
  - `Escolha o assunto para iniciar sua solicitação.`
- Manter grid de `MyRequestsNavigationCard`.
- Cards devem usar nome do tipo e ícone Lucide; não mostrar código técnico.
- Se `RequestType` já expuser descrição apropriada, usá-la; se não, não inventar descrição de negócio.
- Cards devem ter focus/teclado/mobile via componente do kit.
- Loading, erro e empty usando componentes do kit.
- O fallback para `presentation_mode=specialized` sem renderer deve ser reescrito para PT-BR, por exemplo:
  - título: `Formulário indisponível`;
  - mensagem: `Este tipo de solicitação ainda não possui um formulário disponível neste portal.`
- Não mostrar `specialized`, `schema_driven`, `code` ou detalhes de configuração para usuário comum.

---

## 13. Criação genérica

### Fazer

- Título do RequestType.
- Descrição curta de criação, se houver metadado real.
- Filial dentro do formulário conforme regra atual.
- Labels amigáveis para filiais.
- Botões:
  - `Voltar`;
  - `Criar solicitação` em vez de apenas `Criar`.
- Ajuda na filial e no propósito da tela.
- Erros do backend devem passar por tratamento amigável já existente; não exibir stack/path técnico.

---

## 14. Formulário schema-driven / matéria-prima

### Fazer

- Manter renderer dinâmico por schema.
- Não criar campos hardcoded para MP fora do schema.
- Header contextual amigável.
- Todos os labels, hints e options exibidos devem estar em PT-BR conforme o schema vigente.
- Se o schema vier com conteúdo técnico/inglês, corrigir na fonte dona do RequestType, não com patch de string específico na página.
- Estado `sem form_schema` deve virar mensagem de produto:
  - `O formulário deste tipo ainda não está configurado.`
- Ajuda de formulário deve explicar preenchimento e unidade, não a tecnologia schema-driven.
- Preservar `branch_scope` apenas como regra interna; usuário vê `Filial obrigatória/opcional` quando necessário.

---

## 15. Wizard de emissão de NF

O wizard atual funciona, mas ainda parece uma implementação técnica. Ele deve virar um fluxo guiado e visualmente claro.

### 15.1 Estrutura

Manter os 6 passos:

1. Destinatário
2. Tipo de nota fiscal
3. Itens
4. Transporte
5. Informações adicionais
6. Conferência

### 15.2 Navegação do wizard

Antes de manter `FormActions + vários ActionButton` como stepper, consultar o catálogo do `plugin-ui`.

Se existir componente compartilhado adequado para stepper/progressão, usá-lo.

Se não existir e o padrão tiver potencial de reuso, implementar no `plugin-ui` e reutilizar. Não criar chrome de stepper com CSS próprio no MFE.

### 15.3 Etapa destinatário

- ajuda clara para Cliente/Fornecedor;
- busca com loading/empty/error visual;
- resultado selecionado em card/resumo do kit se houver componente adequado;
- não usar lista crua se o catálogo já tiver componente de resultados/record card.

### 15.4 Etapa itens

- melhorar leitura dos itens adicionados;
- quantidade e preço com labels claros;
- números em formato PT-BR;
- usar tabela/lista/card do kit quando semanticamente apropriado;
- preservar regra de negócio atual.

### 15.5 Transporte

- `CIF` e `FOB` podem permanecer como siglas, com help explicando a escolha em linguagem de negócio;
- transportadora selecionada deve ter estado visual claro.

### 15.6 Adicionais

- `Peso (kg)` e `Volumes` com ajuda e validação visual;
- observação com `FieldLabel` + hint.

### 15.7 Conferência

- substituir chaves técnicas do checklist por labels PT-BR;
- apresentar checks visualmente com componentes/tokens do kit;
- CTA final `Enviar solicitação`;
- deixar claro o que falta para permitir envio.

---

## 16. Tela `/requests/:id` — detalhe completo

Esta tela deve ser tratada como ficha operacional completa.

### 16.1 Header

Exibir:

- número da solicitação como título;
- nome amigável do tipo;
- status em badge;
- contexto de filial se aplicável;
- help do detalhe.

Não usar somente `REQ-...` isolado sem contexto.

### 16.2 Resumo da solicitação

`DetailFields` deve exibir:

- Tipo — nome amigável;
- Status — PT-BR;
- Filial — amigável;
- Solicitante — nome;
- outros campos somente se já existirem no contrato real e tiverem valor operacional.

### 16.3 Ações

`ActionBar` deve:

- continuar recebendo `allowed_actions` da API;
- renderizar label PT-BR via mapa central;
- enviar o código original ao callback/API;
- usar ordem coerente e variantes semânticas do kit;
- não mostrar `view/start/cancel/...` crus;
- ter help explicando que ações dependem da etapa e do perfil.

A ação `view`, se o usuário já está no detalhe, não deve virar um botão inútil sem função. Confirmar a semântica atual e decidir com evidência: esconder somente se for de fato redundante e sem efeito, sem alterar autorização do backend.

### 16.4 Modal de motivo

Manter `ReasonConfirmModal`, melhorando somente composição/copy se necessário.

Adicionar help curto sobre consequência da devolução/cancelamento. Não exibir código técnico.

---

## 17. Painel Dados da emissão

### Fazer

- tipo de NF em label amigável;
- frete amigável;
- quantidade de itens;
- produtos em lista/tabela mais legível;
- preço e quantidade formatados em PT-BR;
- considerar `DataTable`, `DataRecordCard` ou componente adequado já existente no kit;
- não mostrar payload bruto.

---

## 18. Linha do tempo

### Fazer

- títulos de evento em PT-BR;
- data/hora formatada em PT-BR;
- ator com apresentação humana;
- se houver metadata real útil do evento, apresentar resumo sem despejar JSON;
- usar `MyRequestsTimeline`/factory do kit;
- empty state amigável;
- help explicando que é o histórico da solicitação.

---

## 19. Comentários

### Fazer

- revisar catálogo do `plugin-ui` antes de manter `<ul>` simples;
- se houver thread/composer compartilhado adequado e desacoplado do domínio Comercial, reutilizá-lo via factory;
- caso não haja, manter composição simples, mas visualmente coerente e sem recriar componente do kit;
- mostrar autor e data/hora quando o contrato real fornecer;
- textarea com hint de uso;
- CTA `Enviar comentário` se isso melhorar clareza;
- estados enviando/erro/empty;
- help em PT-BR.

Não inventar menções, reações ou realtime neste escopo.

---

## 20. Anexos

### Fazer

- manter `MyRequestsFileDropzone`;
- consultar `createDashboardAttachmentFileList` / previews do `plugin-ui` antes de manter `<ul>` cru;
- se aplicável, criar aliases em `mrUi.tsx` e usar o componente compartilhado;
- mostrar nome do arquivo e ações em PT-BR;
- loading/progresso somente se houver suporte real;
- help explicando formatos e finalidade;
- manter limites/MIME reais do contrato.

---

## 21. Artefatos

### Fazer

- diferenciar visualmente de Anexos;
- explicar que são documentos produzidos durante o atendimento;
- `kind` em PT-BR;
- upload somente conforme autorização já existente;
- reusar componentes de arquivo do kit;
- não expor `generic` / `invoice_pdf`.

---

## 22. Tela `/admin`

Hoje a tela ainda parece técnica. Deve virar uma tela administrativa de produto.

### Fazer

- TopBar com **Administração** ativa.
- Header:
  - `Administração de solicitações`;
  - descrição curta: `Consulte os tipos de solicitação disponíveis no módulo.`
- Section title `Tipos de solicitação`, não `RequestTypes`.
- Colunas:
  - Código — pode permanecer porque é identificador administrativo;
  - Nome;
  - Situação;
  - Uso de filial.
- `active` → `Ativo/Inativo`.
- `branch_scope` traduzido.
- mensagem de acesso negado sem expor `my-requests.manage` como texto principal:
  - `Você não possui acesso à administração deste módulo.`
- se a permissão técnica precisar aparecer, colocar somente em detalhe de suporte/help, não como mensagem principal.
- Ajuda por coluna quando necessário.

Não adicionar CRUD neste prompt se o contrato atual é somente leitura.

---

## 23. Estado sem acesso / erros globais

O estado atual em `App.tsx` usa um `<p>` simples. Substituir por componente de estado do kit.

### Fazer

- `MyRequestsStateBanner`, Empty/Guidance ou componente equivalente do catálogo;
- mensagem PT-BR amigável;
- não expor stack, endpoint ou permission code;
- preservar o gate real de autorização.

---

## 24. `mrUi.tsx` — ampliar o binding compartilhado

O MFE não deve importar factories de forma aleatória em cada página. Continuar centralizando aliases/factories em `src/ui/mrUi.tsx`.

Avaliar adicionar, conforme uso real:

```text
MyRequestsTopBar
MyRequestsPageHero
MyRequestsTitleWithHelp
MyRequestsAttachmentFileList
MyRequestsDataRecordCard
MyRequestsMetricStrip
MyRequestsSoftEmptyState / EmptyGuidance
```

Só adicionar componentes efetivamente usados.

Para cada factory:

- usar `MR_UI_PREFIX`;
- usar `MR_PORTAL_SCOPE` quando aplicável;
- fornecer labels PT-BR configuráveis;
- emitir dual-class corretamente;
- não criar CSS de componente em `index.css`.

---

## 25. CSS — apenas layout e tokens

`plugins/my-requests/src/index.css` continua limitado a:

- tokens do plugin;
- mapeamento `--delpi-ui-*`;
- layout de página;
- grids/stacks entre seções;
- responsividade do layout;
- CSS de elementos realmente específicos de domínio que não existam no kit.

### Proibido

- `.delpi-ui-*` no CSS do MFE;
- BEM espelho de TopBar, SectionCard, DataTable, FileDropzone etc.;
- copiar CSS do `plugins/commercial`;
- hardcode de superfícies/cores para corrigir dark mode;
- `body`, `:root` global ou `*` global fora do escopo permitido;
- criar `.my-requests-topbar`, `.my-requests-card`, `.my-requests-table` para substituir componentes que já existem no kit.

### Responsividade mínima

Validar pelo menos:

```text
≥ 1440px desktop amplo
~ 1024px tablet/desktop compacto
≤ 768px mobile
~ 390px mobile estreito
```

Sem scroll horizontal acidental no shell.

---

## 26. Tema claro e escuro

Validar no Portal federado, não apenas no Vite standalone.

Conferir:

- TopBar;
- filtros;
- tabelas;
- badges;
- modais;
- dropzones;
- cards;
- textos muted;
- estados vazios/erro/loading;
- foco/hover/disabled.

Corrigir problema visual de componente compartilhado **no `plugin-ui`**, não no CSS local.

Se `plugin-ui` for alterado:

1. atualizar componente + CSS canônico + catálogo/teste;
2. rebuild do remote `plugin-ui` antes do `my-requests`;
3. seguir `mf-federation-patch-safety.mdc`.

---

## 27. Acessibilidade

Manter ou melhorar:

- landmarks (`nav`, headings, sections);
- `aria-label` em TopBar e controles;
- foco visível;
- navegação por teclado;
- alvo mínimo de toque;
- tooltips acessíveis;
- modais com foco/fechamento correto provido pelo kit;
- não depender apenas de cor para status;
- ícones decorativos com `aria-hidden`.

---

## 28. Não fazer

- Não redesenhar apenas os prints fornecidos.
- Não deixar Wizard, SchemaForm, Admin, painel de comentários, anexos ou artefatos fora do escopo.
- Não criar componente visual primitivo se já existir no `plugin-ui`.
- Não copiar `PluginShell.tsx` do Comercial literalmente; copiar **o padrão**, reutilizando as factories compartilhadas.
- Não copiar CSS do Comercial.
- Não chamar `api-delpi` no MFE.
- Não mover regra de workflow para React.
- Não traduzir payload antes de enviá-lo à API.
- Não trocar códigos persistidos por labels PT-BR.
- Não hardcodar os tipos de solicitação para substituir o registry.
- Não inventar métricas, SLA, prioridade, responsável ou datas ausentes do contrato.
- Não adicionar CRUD de RequestType só para “melhorar Admin”.
- Não manter texto técnico em help de usuário.
- Não entregar visual novo com Manual/Wireframe desatualizados.

---

## 29. Testes obrigatórios

### 29.1 Estruturais / kit-first

Garantir regressão para:

- TopBar vem de `@delpi/plugin-ui`;
- nenhum primitivo TopBar local;
- zero CSS `.delpi-ui-*` no MFE;
- zero BEM espelho de componentes do kit;
- `preparePluginUiRemote()` continua correto;
- MFE continua sem `/apps/api-delpi`.

### 29.2 Roteamento / TopBar

Testar:

- item ativo por rota;
- Nova ocultada sem permissão de create;
- Administração ocultada sem manage;
- rotas de detalhe não quebram o shell;
- deep link `/new?type=...` continua abrindo o formulário correto.

### 29.3 PT-BR

Criar testes para mapas de apresentação:

- status;
- actions;
- timeline events;
- branch scope;
- artifact kind;
- datas;
- tipos quando resolvidos pelo catálogo.

Casos negativos:

- valor desconhecido não quebra UI;
- fallback não envia label traduzido à API;
- `ActionBar` chama `onAction` com o código original.

### 29.4 Ajuda

Adicionar teste estrutural/conteúdo que garanta help mínimo nas superfícies principais.

No mínimo validar chaves para:

```text
shell
mine
workQueue
new
invoiceWizard
rawMaterialForm
detail
timeline
comments
attachments
artifacts
admin
```

E atualizar os testes se a estrutura da Ajuda for reorganizada.

### 29.5 Funcionalidade existente

Preservar testes atuais de:

- filtros/debounce;
- paginação;
- deep link;
- branch scope;
- schema form;
- wizard NF;
- action bar;
- reason modal;
- uploads;
- permissões.

### 29.6 Build

Executar no mínimo:

```bash
cd plugins/my-requests
npm test
npm run build
```

Se houver script de typecheck/lint no `package.json`, executar também.

Se `plugin-ui` mudar:

```text
build/test plugin-ui
→ rebuild remote
→ build/test my-requests
```

---

## 30. Validação visual obrigatória

Após testes programáticos, fazer smoke visual no **Portal real/federado**.

Matriz mínima:

| Tela | Claro | Escuro | Desktop | Mobile |
|---|---:|---:|---:|---:|
| Minhas | ✓ | ✓ | ✓ | ✓ |
| Fila | ✓ | ✓ | ✓ | ✓ |
| Nova / cards | ✓ | ✓ | ✓ | ✓ |
| Wizard NF | ✓ | ✓ | ✓ | ✓ |
| Schema MP | ✓ | ✓ | ✓ | ✓ |
| Detalhe | ✓ | ✓ | ✓ | ✓ |
| Modal motivo | ✓ | ✓ | ✓ | ✓ |
| Comentários | ✓ | ✓ | ✓ | ✓ |
| Anexos | ✓ | ✓ | ✓ | ✓ |
| Artefatos | ✓ | ✓ | ✓ | ✓ |
| Admin | ✓ | ✓ | ✓ | ✓ |
| Sem acesso | ✓ | ✓ | ✓ | ✓ |

Validar também:

- refresh/F5 em rotas internas;
- back/forward;
- foco teclado;
- TopBar collapse/mobile;
- upload/dropzone;
- empty/loading/error;
- filtros e paginação.

---

## 31. Atualização obrigatória de documentação

No mesmo PR:

### `WIREFRAMES.md`

Atualizar o chrome comum para:

```text
TopBar
→ Header/Hero contextual
→ conteúdo
```

E atualizar **todos** os WF-01 a WF-07 afetados.

Remover wireframes que ainda mostrem `PageHeader + FormActions nav` como chrome global.

### `MANUAL-USUARIO.md`

Reescrever como documento de usuário:

- explicar TopBar;
- nomes finais PT-BR;
- telas e fluxos;
- filtros;
- ações;
- timeline;
- anexos/artefatos;
- admin;
- sem termos internos de arquitetura na parte de uso.

Detalhes técnicos podem ficar em seção separada de notas de suporte, se realmente necessários.

### `plugins/my-requests/README.md`

Atualizar:

- arquitetura visual kit-first;
- TopBar canônica;
- fonte de Ajuda;
- componentes/factories novos em `mrUi.tsx`;
- comandos de validação.

### Este arquivo

Ao concluir:

```text
Status: implementado
```

Adicionar breve seção de evidências com testes/build/smoke executados.

---

## 32. Definition of Done

A entrega só pode ser considerada concluída quando:

- [ ] TopBar do `plugin-ui` substituiu o nav atual em **todo o plugin**.
- [ ] TopBar segue o padrão visual do Portal Comercial sem copiar CSS local.
- [ ] Todas as rotas/subfluxos foram revisados, não somente `/mine` e detalhe.
- [ ] Nenhum status/action/evento conhecido aparece cru em inglês na UI.
- [ ] Tipos aparecem pelo nome amigável onde possível.
- [ ] Datas/horas estão formatadas em PT-BR.
- [ ] Branch scope e artifact kind estão traduzidos na apresentação.
- [ ] Checklist do wizard não mostra chaves técnicas.
- [ ] Ajuda contextual existe em todas as telas/seções listadas.
- [ ] Ajuda não expõe arquitetura interna ao usuário.
- [ ] `mrUi.tsx` continua sendo o binding central do kit.
- [ ] `index.css` contém apenas tokens/layout/domínio permitido.
- [ ] Claro/escuro validados.
- [ ] Desktop/tablet/mobile validados.
- [ ] Deep links, filtros, workflow, RBAC e uploads continuam funcionando.
- [ ] `npm test` verde.
- [ ] `npm run build` verde.
- [ ] `WIREFRAMES.md`, `MANUAL-USUARIO.md` e README sincronizados.
- [ ] Smoke visual no Portal federado concluído.

---

## 33. Sequência sugerida de execução

### E20.S0 — Inventário e baseline

- listar todas as telas/componentes deste prompt;
- registrar screenshots baseline em claro/escuro quando útil;
- rodar testes/build antes de alterar;
- confirmar exports existentes no catálogo `plugin-ui`.

### E20.S1 — Shell + TopBar

- criar binding `MyRequestsTopBar` em `mrUi.tsx`;
- refatorar shell;
- active nav + permissões;
- responsividade;
- testes de navegação.

### E20.S2 — Apresentação PT-BR transversal

- mapas centrais status/action/event/type/branch/artifact;
- formatter de data/hora/número;
- testes unitários.

### E20.S3 — Minhas + Fila

- header/hero compacto;
- filtros/lista/empty;
- tipo/status amigáveis;
- help completo;
- mobile.

### E20.S4 — Nova + forms

- cards;
- genérico;
- SchemaForm;
- erros/empty;
- help.

### E20.S5 — Wizard NF

- stepper/progressão via kit;
- buscas/resultados;
- itens;
- conferência PT-BR;
- ajuda por etapa.

### E20.S6 — Detalhe

- header/resumo;
- ActionBar localizado;
- payload NF;
- timeline;
- modal motivo.

### E20.S7 — Comunicação e arquivos

- comentários;
- anexos;
- artefatos;
- reutilização de componentes de arquivo do kit.

### E20.S8 — Administração + estados globais

- admin PT-BR;
- sem acesso;
- fallbacks.

### E20.S9 — Docs + validação final

- helpTooltips final;
- Manual;
- Wireframes;
- README;
- testes/build;
- smoke visual claro/escuro/mobile;
- atualizar status deste prompt.

Cada subetapa deve ser testável e não deixar a UI em estado intermediário quebrado.

---

## 34. Prompt colável para o Cursor/agente

```text
Implemente a modernização visual COMPLETA do plugin Minhas Solicitações
conforme:

docs/12-roadmap-e-evolucao/my-requests/PROMPT-ui-excelencia-topbar-ptbr-help.md

IMPORTANTE: revise TODO o código e TODAS as telas do plugin, não somente
os screenshots fornecidos.

Objetivos obrigatórios:
1. substituir o nav PageHeader + FormActions por TopBar no padrão do
   plugins/commercial, usando createDashboardTopBar de @delpi/plugin-ui;
2. manter mrUi.tsx como binding central das factories do kit;
3. melhorar o visual de /mine, /work-queue, /new, GenericCreateForm,
   SchemaFormPage, InvoiceIssuanceWizard, /requests/:id, todos os painéis
   do detalhe, /admin e estados globais;
4. deixar 100% da UI visível em PT-BR: status, allowed_actions, eventos,
   datas, branch_scope, artifact kind, tipos e checklist do wizard não
   podem aparecer como códigos técnicos quando houver apresentação humana;
5. implementar Ajuda contextual em TODAS as telas/seções usando
   @delpi/plugin-ui; conteúdo em content/helpTooltips.ts, em linguagem de
   usuário e sem requests-api/WorkflowEngine/schema-driven/type_code etc.;
6. zero CSS de componente do kit no MFE; index.css somente tokens/layout;
7. responsivo desktop/tablet/mobile e compatível com tema claro/escuro;
8. não mudar regras de negócio, workflow, RBAC nem contratos sem evidência;
9. MFE continua chamando somente /apps/requests-api;
10. sincronizar WIREFRAMES.md, MANUAL-USUARIO.md, README e o status do
    próprio prompt no mesmo PR.

Antes de implementar, leia as regras .cursor aplicáveis e inspecione o
catálogo atual de plugins/plugin-ui. Se um componente compartilhado já
existir, reutilize. Se faltar um primitivo realmente transversal, crie-o no
plugin-ui com teste/docs e rebuild do remote; não copie CSS do Comercial.

Use plugins/commercial/src/app/PluginShell.tsx e commercialUi.ts apenas como
referência de composição da TopBar e maturidade visual — não copie regra de
domínio nem CSS.

Preserve allowed_actions como render-only: traduza somente o label exibido
e envie o código original à requests-api.

Faça a execução em etapas E20.S0–E20.S9 definidas no documento, com testes
por etapa. No final rode npm test + npm run build do my-requests e smoke
visual no Portal federado em claro/escuro e mobile.
```
