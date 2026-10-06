# 08 — P1 — Cockpit da Competência

## Estado

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PASS / READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY**

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

## Job

> Como está o fechamento desta competência, o que já está pronto e o que ainda impede a conclusão?

O Cockpit é a página principal de uma competência dentro da **Central de Fechamento**.

Ele é uma superfície de **leitura, composição e navegação**.

Não é owner das regras de P2/P3/P4/P5 e não executa validação, sacramentação ou envio.


## Responsabilidade, owners e non-goals

P1 owns **composição e navegação da competência**, não os estados que apresenta.

| Informação | Owner | Papel de P1 |
|---|---|---|
| contexto/competência | contract da Central | identificar recorte |
| documentos/completude | P2 | projetar eixo/blocker |
| estoque/cutoff/paridade/STOCK_CLOSED | P3 / owner canônico | projetar eixo/blocker |
| classificações/pendências | P4 | destacar atenção/navegar |
| pacote/finalização/envio/clarifications | P5 | projetar eixo/blocker |
| effective permissions | Core | autorizar leitura |
| histórico material | owners P2–P5 / composição auditável | apresentar timeline |
| chrome visual | `@delpi/plugin-ui` | composição |

Não pertence a P1:
- alterar lifecycle de P2–P5;
- calcular regra financeira nova;
- validar evidence;
- confirmar cutoff;
- sacramentar estoque;
- resolver classificação;
- finalizar/enviar pacote;
- criar task;
- criar permission;
- persistir estado duplicado apenas para reproduzir owner state.


---

## Objetivo visual

O usuário deve entender, nesta ordem:

```text
1. qual competência está vendo;
2. se existe algum blocker material;
3. como estão os três eixos independentes;
4. quais pendências exigem atenção;
5. o que aconteceu recentemente;
6. para onde navegar para resolver.
```

Não representar o fechamento por um percentual único.

```text
ESTOQUE
!= DOCUMENTOS
!= PACOTE
```

Os três eixos são independentes e devem permanecer visualmente independentes.

---

## Estrutura visual canônica — desktop

```text
┌─────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                                              │
│ Início | Visão geral | Sala | Minhas tarefas | Administração | Ajuda│
├─────────────────────────────────────────────────────────────────────┤
│ Início > Central de Fechamento > Cockpit da Competência             │
├─────────────────────────────────────────────────────────────────────┤
│ CENTRAL DE FECHAMENTO                                               │
│ Fechamento mensal                                                   │
│ Competência: [MM/AAAA]    Contexto: [...]    Atualizado: hh:mm       │
│                                               [Ajuda contextual]     │
├─────────────────────────────────────────────────────────────────────┤
│ BLOCKERS                                                            │
│ ⚠ Documento obrigatório pendente                                   │
│ ⚠ Fonte H02 indisponível                                            │
│ → ações navegam ao owner                                            │
├───────────────────────┬───────────────────────┬─────────────────────┤
│ ESTOQUE               │ DOCUMENTOS            │ PACOTE              │
│ [status]              │ [status derivado]     │ [status]            │
│ detalhe resumido      │ contagens úteis       │ detalhe resumido    │
│ progress/state path   │ requisitos/validação  │ progress/state path │
│ [Abrir Estoque]       │ [Abrir Checklist]     │ [Abrir Pacote]      │
├─────────────────────────────────────────────────────────────────────┤
│ PENDÊNCIAS PRIORITÁRIAS                                             │
│ item • motivo • responsável • pending_since • origem • ação         │
├─────────────────────────────────────────────────────────────────────┤
│ HISTÓRICO DA COMPETÊNCIA                                            │
│ timeline de eventos materiais                                       │
└─────────────────────────────────────────────────────────────────────┘
```

A hierarquia acima é normativa.

---

## Estrutura visual — mobile

Ordem obrigatória:

```text
Topbar responsiva
→ PagePath
→ contexto da competência
→ blockers
→ Estoque
→ Documentos
→ Pacote
→ pendências
→ histórico
→ Help contextual
```

No mobile:
- não esconder blockers atrás de tabs;
- não exigir scroll horizontal para compreender os três eixos;
- cards de eixo empilham verticalmente;
- ações continuam visíveis e focáveis;
- tabelas extensas devem degradar para card/lista quando o componente canônico suportar;
- nenhum estado pode depender apenas de cor.

---

## Cabeçalho e contexto

Exibir:
- competência;
- empresa/unidade como contexto de dado quando aplicável;
- freshness;
- estado geral derivado somente como resumo textual;
- acesso ao Help contextual.

O contexto não cria permission por filial/unidade.

Deep link deve preservar a competência e demais filtros relevantes conforme o router canônico do MFE.

---

## Blockers — prioridade visual máxima após contexto

Blockers aparecem **antes dos eixos** quando existirem.

Exemplos:
- REQUIRED/CONDITIONAL aplicável não satisfeito;
- source obrigatório indisponível;
- P3 sem paridade exata pós-cutoff;
- pacote/destinatário pendente;
- esclarecimento aberto quando aplicável.

Cada blocker deve mostrar, quando disponível:
- título;
- motivo;
- source;
- responsável/provider;
- evidência resumida;
- ação de navegação para o owner.

```text
BLOCKER ACTION
= navigate to owner
!= execute owner action in P1
```

Sem blocker real:
- não renderizar um painel alarmista vazio;
- usar empty/positive state discreto se necessário.

---

## Eixos independentes

### 1. Estoque

Estados:

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

Conteúdo visual mínimo:
- label `Estoque`;
- status atual;
- última atualização/freshness;
- resumo de paridade quando disponível;
- situação de cutoff/revalidação;
- CTA `Abrir Estoque e Conciliação`.

Regras:
- zero pré-cutoff continua preliminar;
- H02/source indisponível não aparece como zero;
- divergência monetária só é paridade quando exatamente `R$ 0,00`;
- `READY_TO_CLOSE != STOCK_CLOSED`.

### 2. Documentos

Mostrar contagens úteis por estado, sem percentual único como verdade do fechamento.

Exemplos:
- REQUIRED total/satisfeitos;
- CONDITIONAL aplicáveis;
- pendentes;
- aguardando validação;
- rejeitados/substituição;
- aceitos;
- N/A quando aplicável.

CTA:
- `Abrir Checklist e Documentos`.

Não assumir:
- upload = validação;
- último documento = pacote pronto;
- quantidade alta de concluídos = fechamento concluído.

### 3. Pacote

Estados:

```text
PACKAGE_INCOMPLETE
→ READY_TO_FINALIZE
→ PACKAGE_FINALIZED
→ PACKAGE_SENT
→ WAITING_FOR_CLARIFICATION
→ MONTHLY_CLOSING_COMPLETED
```

Conteúdo visual mínimo:
- status atual;
- resumo por destinatário quando aplicável;
- blockers de readiness;
- versão atual, quando existir;
- CTA `Abrir Pacote e Envio`.

Regras:
- Finalizar != Enviar;
- PACKAGE_SENT é histórico imutável;
- envio de um destinatário não avança sibling;
- clarification aberta impede conclusão quando aplicável.

---

## Pendências prioritárias

Mostrar no Cockpit apenas o subconjunto que ajuda a responder “o que exige atenção agora”.

Campos úteis:
- item;
- motivo;
- contexto;
- responsável;
- source;
- pending_since;
- estado;
- ação/deep link.

Sem SLA formal:
- não usar `atrasada`;
- não usar vermelho por idade como se houvesse prazo;
- `pending_since` é informação factual.

A lista completa continua owner de P4/Minhas tarefas quando aplicável.

---

## Histórico da competência

Mostrar timeline de eventos materiais:
- snapshot/abertura;
- anexos;
- validações/rejeições;
- N/A;
- cutoff;
- revalidação;
- estoque fechado;
- pacote finalizado;
- pacote enviado;
- esclarecimentos;
- conclusão mensal.

O Cockpit consome eventos; não altera histórico.

---

## Reuso obrigatório de `@delpi/plugin-ui`

Import runtime canônico:

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  StatusBadge,
  ProgressTracker,
  MetricStrip,
  AlertQueue,
  WorklistItem,
  Timeline,
  StateBanner,
  StateBox,
  EmptyState,
  LoadingState,
  HelpTooltip,
  ActionButton,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

Mapeamento:

| Necessidade | Componente canônico |
|---|---|
| breadcrumb/context path | `createDashboardPagePath` |
| hero/cabeçalho | `createDashboardPageHero` |
| cards dos eixos | `createDashboardSectionCard` |
| estado atual | `StatusBadge` |
| progressão de Estoque/Pacote | `ProgressTracker` |
| contagens resumidas de Documentos | `MetricStrip` |
| blockers | `AlertQueue` |
| pendências prioritárias | `WorklistItem` |
| histórico | `Timeline` |
| source parcial/indisponível | `StateBanner` / `StateBox` |
| loading/empty | `LoadingState` / `EmptyState` |
| ajuda pontual | `HelpTooltip` |
| CTAs de navegação | `ActionButton` |

### Regra de composição

```text
plugin-ui primitive
+ domain content
+ owner contract
= Cockpit
```

Não criar localmente equivalentes a:
- status badge;
- progress tracker;
- blocker queue;
- worklist item;
- timeline;
- page hero/path;
- state banner/box;
- generic action button.

Se faltar capability visual realmente reutilizável, registrar `PLUGIN_UI_GAP_FOUND` antes de criar chrome local.

---

## Wireframe semântico dos eixos

Cada eixo deve seguir a mesma gramática visual:

```text
SectionCard
├── title
├── StatusBadge
├── supporting summary
├── optional ProgressTracker / MetricStrip
├── freshness/source hint
└── ActionButton → owner page
```

A mesma estrutura visual não significa mesma regra de negócio.

---

## Contratos TARGET — MFE → BFF → owners

O browser consome somente `controllership-finance-api`.

```text
plugins/controllership-finance
→ controllership-finance-api
   → Core effective permissions
   → P2 / P3 / P4 / P5 contracts
```

P1 é read model/composição. A FASE A não congela um endpoint agregado específico por preferência.

Operações semânticas necessárias:

| Operação | Semântica |
|---|---|
| resolveClosingContext | competência/contexto autorizado |
| composeStockAxis | estado/freshness/blockers vindos de P3 |
| composeDocumentsAxis | completude/validation blockers vindos de P2 |
| composePackageAxis | package/finalization/send/clarification state vindo de P5 |
| listPriorityPendencies | subset navegável de P4/owners |
| listClosingHistory | eventos materiais dos owners |
| composeBlockers | normalização sem transferir regra/ownership |

Se uma futura BFF oferecer um único read endpoint ou múltiplos endpoints, isso é decisão física de implementação; a semântica acima permanece.

Regras:
- BFF pode normalizar shapes/provenance;
- BFF não recalcula state machine de owner;
- source indisponível permanece indisponível;
- blocker só existe quando owner/contract o sustenta;
- nenhuma operação de write pertence a P1.

### AuthZ

```text
authenticated
AND effective_permission(controllership-finance.access)
AND context/resource_scope
AND business_rule_allows_read
```

- `MANAGE` não substitui `ACCESS`;
- unidade/filial é contexto, não permission code;
- UI não autoriza;
- falha do Core/effective permissions → fail-closed;
- navegação ao owner será reautorizada na página destino.

## Estados de experiência

### LOADING
- skeleton/loading canônico;
- manter layout previsível;
- não exibir zero/default como dado real.

### SUCCESS
- contexto e eixos carregados com coverage suficiente;
- estados e blockers refletem os owners;
- zero real só aparece quando source respondeu validamente.

### EMPTY
Somente quando a ausência é válida e todas as sources necessárias responderam.

### PARTIAL
Mostrar o que é confiável + banner claro indicando o que não foi carregado.

### UNAVAILABLE / UNAVAILABLE_SOURCE
Identificar a source indisponível e impacto no eixo.

`UNAVAILABLE` é o estado de experiência do módulo/eixo; `UNAVAILABLE_SOURCE` qualifica a dependência afetada.

Se a source for necessária para afirmar readiness, o eixo não pode aparecer como pronto.

### ERROR
Mensagem clara + retry quando tecnicamente possível.

### FORBIDDEN
Sem exposição de dados do cockpit.

### NOT_FOUND
Competência/contexto inexistente ou inválido.

---

## Light / dark, responsividade e acessibilidade

Contrato de tema:

```text
SAME DOM
+ SAME SECTION ORDER
+ SAME STATES
+ SAME ACTIONS
+ THEME TOKENS
= LIGHT / DARK PARITY
```

- TopBar pertence ao shell;
- P1 é deep page da Central e usa `PagePath`;
- desktop mantém blockers antes dos eixos;
- mobile empilha eixos sem esconder blockers;
- nenhum status depende só de cor;
- CTAs/links e timeline são operáveis por teclado;
- foco permanece visível;
- refresh/navegação não deve perder contexto de competência;
- CSS de componentes compartilhados permanece no `plugin-ui`.

## Navegação

P1 pode navegar para:
- P2 Checklist e Documentos;
- P3 Estoque e Conciliação;
- P4 Classificações e Pendências;
- P5 Pacote e Envio;
- Help contextual.

P1 não executa:
- validação de evidência;
- N/A;
- sacramentação;
- classificação final;
- finalização;
- envio.

---

## Critérios visuais de aceite

### VA-P1-01 — Hierarquia
Contexto → blockers → eixos → pendências → histórico é preservado em desktop e mobile.

### VA-P1-02 — Eixos independentes
Estoque, Documentos e Pacote são cards independentes e não colapsam em um “percentual geral”.

### VA-P1-03 — Blockers
Blockers materiais aparecem antes dos eixos e navegam ao owner.

### VA-P1-04 — Estados
Status usa texto/ícone/semântica acessível; cor não é único sinal.

### VA-P1-05 — Source failure
Source indisponível nunca aparece como zero ou sucesso.

### VA-P1-06 — Mobile
Os três eixos empilham verticalmente e blockers continuam visíveis antes deles.

### VA-P1-07 — Kit-first
Nenhum componente local duplica export público do `@delpi/plugin-ui`.

### VA-P1-08 — Keyboard/focus
Todos os CTAs e navegação são operáveis por teclado com foco visível.

### VA-P1-09 — Deep link/F5
A competência/contexto permanece após refresh sem bypass de AuthZ.

### VA-P1-10 — Help
Help contextual explica eixos, freshness, blockers, preliminary/final e diferença entre estoque fechado, pacote enviado e fechamento concluído.

---

## Critérios funcionais-chave preservados

- STOCK_CLOSED + REQUIRED pendente → pacote incompleto;
- último doc aceito → sem auto-send;
- pre-cut zero → não final;
- paridade monetária exige divergência exatamente R$ 0,00;
- qualquer valor monetário não zero continua divergência e bloqueia READY_TO_CLOSE;
- H02 indisponível → não zero;
- PACKAGE_SENT + clarification → não complete;
- source parcial → PARTIAL;
- FORBIDDEN → sem exposição.

---

## RQ / AC / testes

Rastreabilidade canônica:
- `RQ-P1-01` — competência/contexto e F5;
- `RQ-P1-02` — eixos independentes;
- `RQ-P1-03` — blockers com source/ação;
- `RQ-P1-04` — source indisponível não vira zero/sucesso;
- `RQ-P1-05` — P1 é composição/read-only;
- `RQ-P1-06` — histórico navegável;
- `RQ-P1-07` — Help contextual.

Authority executável: [23-ledger-rq-ac-testes.md](./23-ledger-rq-ac-testes.md).

Matriz futura mínima:

### Positive
- abrir competência válida;
- navegar entre P2/P3/P4/P5 preservando contexto;
- exibir três eixos independentes;
- mostrar blocker com motivo/source/ação;
- reconstruir contexto após F5;
- exibir histórico material.

### Sibling
- mudança em Estoque não falsifica Documentos/Pacote;
- mudança em Documentos não falsifica Estoque/Pacote;
- source parcial de um eixo preserva siblings confiáveis.

### Negative
- sem ACCESS;
- resource/contexto fora do scope;
- source indisponível tratado como zero;
- zero pré-cutoff tratado como final;
- P1 tentando validar evidência;
- P1 tentando sacramentar;
- P1 tentando finalizar/enviar;
- PACKAGE_SENT tratado como conclusão quando existe clarification.

### Experiência
- loading;
- empty;
- partial;
- unavailable source;
- error;
- 403;
- 404;
- desktop/mobile;
- light/dark;
- keyboard/focus;
- deep link/F5;
- Help.

## Scripts e artefatos auxiliares PLANNED

Não criar durante a FASE A.

```text
validate-p1-axis-contracts
- cada eixo tem owner conhecido
- owner state não é duplicado/recalculado

validate-p1-blockers
- blocker possui reason/source/owner/deep link
- unavailable não vira success

validate-p1-deep-links
- competence/context roundtrip
- F5
- owner routes conhecidas
- no open redirect

validate-p1-authz
- ACCESS required
- MANAGE-only denied
- context scope revalidado
- fail-closed

validate-p1-help
- invariantes e links P2–P5 sincronizados

validate-p1-plugin-ui
- primitives canônicas usadas
- nenhum clone local
```

Tecnologia/localização serão escolhidas conforme padrão vigente no HEAD da futura implementação.

## Inventários técnicos remanescentes

- `T01` — bindings/source/freshness dos eixos;
- `T05` — Core effective permissions e resource ownership;
- contratos físicos de agregação do BFF;
- route/query param names.

Esses itens são `TO_INVENTORY_BEFORE_IMPLEMENTATION` e não reabrem as regras funcionais de P1 salvo evidência incompatível.

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
- T01 bindings/source/freshness;
- T05 effective permissions/resource scope;
- contratos físicos de composição do BFF;
- route/query param names.

Resultado:

```text
A08 P1 COCKPIT DA COMPETÊNCIA
= READY_FOR_IMPLEMENTATION_BRIEF_WITH_INVENTORY
!= IMPLEMENTED
```

## Resultado esperado

O Cockpit deve funcionar como **painel de decisão e navegação**, não como uma nova camada de workflow.

```text
SEE
→ UNDERSTAND
→ IDENTIFY BLOCKER
→ NAVIGATE TO OWNER
```

Esse é o contrato visual de P1.
