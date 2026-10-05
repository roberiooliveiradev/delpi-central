# 08 — P1 — Cockpit da Competência

## Estado

**TARGET / VISUAL_SPEC_DEFINED / READY_FOR_IMPLEMENTATION_INVENTORY**

## Job

> Como está o fechamento desta competência, o que já está pronto e o que ainda impede a conclusão?

O Cockpit é a página principal de uma competência dentro da **Central de Fechamento**.

Ele é uma superfície de **leitura, composição e navegação**.

Não é owner das regras de P2/P3/P4/P5 e não executa validação, sacramentação ou envio.

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

## Estados de experiência

### LOADING
- skeleton/loading canônico;
- manter layout previsível;
- não exibir zero/default como dado real.

### EMPTY
Somente quando a ausência é válida e todas as sources necessárias responderam.

### PARTIAL
Mostrar o que é confiável + banner claro indicando o que não foi carregado.

### UNAVAILABLE_SOURCE
Identificar a source indisponível e impacto no eixo.

### ERROR
Mensagem clara + retry quando tecnicamente possível.

### FORBIDDEN
Sem exposição de dados do cockpit.

### NOT_FOUND
Competência/contexto inexistente ou inválido.

---

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

## Resultado esperado

O Cockpit deve funcionar como **painel de decisão e navegação**, não como uma nova camada de workflow.

```text
SEE
→ UNDERSTAND
→ IDENTIFY BLOCKER
→ NAVIGATE TO OWNER
```

Esse é o contrato visual de P1.
