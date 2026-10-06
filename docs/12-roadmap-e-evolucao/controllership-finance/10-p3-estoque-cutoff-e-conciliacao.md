# 10 — P3 — Estoque, Cutoff e Conciliação

## Estado

**TARGET / PAGE_DOCUMENTATION_GATE_V2 PENDING_DECISION_E02 / STOP_CONDITION_ON_T03**

```text
DOCUMENTED != IMPLEMENTED
IMPLEMENTATION_AUTHORIZED = NO

VISUAL_SPEC_DEFINED      = PASS
CONTRACT_DEFINED         = PASS
AUTHZ_DEFINED            = PASS
PLUGIN_UI_REUSE_DEFINED  = PASS
STATES_DEFINED           = PASS
TEST_MATRIX_DEFINED      = PASS

POST_STOCK_CLOSED_RULE   = DECISION_REQUIRED
```

## Job

> Quero saber se o estoque está apto ao fechamento, se as fontes estão atualizadas, se a conciliação fecha exatamente e o que impede o avanço.

P3 é a superfície operacional de cutoff, revalidação, conciliação monetária e leitura do estado canônico de fechamento do estoque.


## Responsabilidade, owners e non-goals

| Capability/dado | Owner |
|---|---|
| state/readiness do Portal até READY_TO_CLOSE | P3 / `controllership-finance-api` |
| regra de paridade exata | P3 business contract |
| P7 / Entradas-Saídas / H02 e regras canônicas TOTVS | `api-delpi` / owner canônico correspondente |
| confirmação de cutoff do Portal | P3, por ator autorizado |
| revalidação/orquestração de leitura | P3/BFF, usando owners canônicos |
| sacramentação ERP | owner/ERP autorizado, fora do Portal V1 |
| `STOCK_CLOSED` canônico | owner a provar em T03 |
| effective permissions | Core |
| chrome visual | `@delpi/plugin-ui` |

Não pertence a P3 V1:
- executar escrita de sacramentação no ERP;
- inventar estado `STOCK_CLOSED` local;
- criar tolerância monetária;
- transformar source offline em zero;
- definir fórmula SQL/TOTVS localmente;
- criar permission por rotina/unidade;
- decidir silenciosamente o que acontece após `STOCK_CLOSED`.


---

## State model

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

Regras visuais:
- o estado atual deve estar sempre explícito em texto;
- `READY_TO_CLOSE` e `STOCK_CLOSED` nunca podem parecer equivalentes;
- cor é sinal auxiliar, não a única forma de comunicar estado;
- a página não pode apresentar `R$ 0,00` isoladamente como sinônimo de fechamento.

---

## Objetivo visual

O usuário deve entender, nesta ordem:

```text
1. qual competência/contexto está sendo conciliado;
2. em qual etapa do state model o estoque está;
3. se o cutoff foi confirmado;
4. se a revalidação pós-cutoff está válida;
5. se P7, Entradas/Saídas e H02 estão disponíveis e fresh;
6. qual é a divergência monetária exata;
7. por que ainda não está READY_TO_CLOSE ou STOCK_CLOSED;
8. onde investigar o detalhe.
```

A página deve transmitir confiança contábil e rastreabilidade, não aparência de dashboard genérico.

---

## Estrutura visual canônica — desktop

```text
┌──────────────────────────────────────────────────────────────────────┐
│ TOPBAR                                                               │
├──────────────────────────────────────────────────────────────────────┤
│ Início > Central de Fechamento > Estoque e Conciliação               │
├──────────────────────────────────────────────────────────────────────┤
│ ESTOQUE E CONCILIAÇÃO                                                │
│ Competência [MM/AAAA] • contexto • freshness geral • Help            │
│ Estado: [PRELIMINARY / ... / STOCK_CLOSED]                           │
├──────────────────────────────────────────────────────────────────────┤
│ FLUXO DO ESTOQUE                                                     │
│ Preliminary → Cutoff → Revalidação → Ready to Close → Stock Closed   │
├──────────────────────────────────────────────────────────────────────┤
│ CUTOFF / REVALIDAÇÃO                                                 │
│ cutoff: status + ator + timestamp                                    │
│ revalidação: status + timestamp + ação quando permitida              │
├──────────────────┬──────────────────┬──────────────────┬─────────────┤
│ ENTRADAS/SAÍDAS  │ P7               │ H02              │ DIVERGÊNCIA │
│ R$ ...           │ R$ ...           │ R$ ...           │ R$ 0,00     │
│ source/freshness │ source/freshness │ source/freshness │ PARIDADE?   │
├──────────────────────────────────────────────────────────────────────┤
│ READINESS / BLOCKERS                                                 │
│ ✓/⚠ cutoff  • ✓/⚠ revalidação • ✓/⚠ sources • ✓/⚠ paridade          │
├──────────────────────────────────────────────────────────────────────┤
│ DRILLDOWN DA CONCILIAÇÃO                                             │
│ total → grupo → item/evidência                                       │
├──────────────────────────────────────────────────────────────────────┤
│ PROVENIÊNCIA E FRESHNESS                                             │
│ source • fetched/calculated_at • finality • rule/version             │
├──────────────────────────────────────────────────────────────────────┤
│ HISTÓRICO                                                            │
│ cutoff • revalidações • mudanças de input • estado canônico          │
└──────────────────────────────────────────────────────────────────────┘
```

A hierarquia acima é normativa.

---

## Estrutura visual — mobile

Ordem obrigatória:

```text
Topbar responsiva
→ PagePath
→ competência/contexto
→ Status atual
→ ProgressTracker
→ cutoff
→ revalidação
→ divergência
→ Entradas/Saídas
→ P7
→ H02
→ readiness/blockers
→ drilldown
→ proveniência/freshness
→ histórico
```

No mobile:
- a divergência aparece antes dos três valores de apoio;
- o rótulo `PRELIMINARY`/`FINAL` permanece visível;
- nenhuma informação crítica depende de hover;
- tabelas de drilldown devem usar comportamento responsivo canônico;
- CTAs de cutoff/revalidação permanecem acessíveis por teclado e touch;
- não comprimir os quatro valores em cards ilegíveis lado a lado.

---

## Cabeçalho e contexto

Exibir:
- competência;
- empresa/unidade como contexto de dado quando aplicável;
- estado atual do state model;
- freshness geral derivada sem mascarar sources individuais;
- acesso ao Help contextual.

Deep link deve preservar competência/contexto e drilldown quando aplicável.

---

## Fluxo visual de estado

Usar progressão explícita:

```text
PRELIMINARY
→ WAITING_FOR_CUTOFF
→ REVALIDATION_REQUIRED
→ READY_TO_CLOSE
→ STOCK_CLOSED
```

### PRELIMINARY
- dados podem ser exibidos;
- `R$ 0,00` é apenas resultado preliminar;
- não usar linguagem de conclusão.

### WAITING_FOR_CUTOFF
- destacar que falta confirmação humana;
- sinais de estabilidade podem ser mostrados como informação, nunca como cutoff implícito.

### REVALIDATION_REQUIRED
- mostrar claramente qual input/source mudou ou por que a revalidação expirou;
- readiness fica bloqueada.

### READY_TO_CLOSE
- significa requisitos de cutoff/revalidação/sources/paridade satisfeitos;
- não significa `STOCK_CLOSED`.

### STOCK_CLOSED
- somente a partir do estado canônico do owner/ERP quando T03 estiver comprovado;
- sem fallback manual silencioso.

---

## Cutoff

O sistema mostra sinais de prontidão.

Um humano autorizado confirma o cutoff.

Não inferir cutoff automaticamente apenas porque relatórios parecem estáveis.

Visual mínimo:
- status do cutoff;
- ator, quando confirmado;
- timestamp;
- contexto/competência;
- ação `Confirmar cutoff` somente quando permitida;
- explicação de que confirmação dispara/requer revalidação.

Confirmação deve usar fluxo explícito/confirmado, não botão destrutivo instantâneo.

---

## Revalidação

Após cutoff confirmado, disparar automaticamente o núcleo:
- P7;
- Entradas/Saídas;
- H02;
- conciliação tripla.

Também deve existir reprocessamento/revalidação manual para usuário autorizado.

Visual mínimo:
- estado da última revalidação;
- início/fim ou calculated_at conforme contract;
- sources avaliadas;
- versão/regra;
- ação `Revalidar` quando permitida;
- motivo visível quando `REVALIDATION_REQUIRED`.

Input alterado pós-revalidação invalida prontidão aplicável e deve ser visível como evento/alerta.

---

## Bloco monetário principal

O bloco principal contém quatro métricas:

```text
ENTRADAS_SAIDAS
P7
H02
DIVERGENCIA
```

Regra canônica:

```text
DIVERGENCIA = ENTRADAS_SAIDAS - P7 - H02
PARIDADE_OK <=> DIVERGENCIA = R$ 0,00
TOLERANCIA_MONETARIA = NONE
```

### Hierarquia visual

`DIVERGENCIA` é a métrica de maior destaque sem esconder os três componentes da fórmula.

Cada métrica deve exibir:
- valor monetário formatado;
- source;
- freshness;
- preliminary/final quando aplicável;
- unavailable/partial explicitamente.

### Paridade exata

```text
R$ 0,00  → paridade monetária somente se contexto final aplicável estiver válido
R$ 0,01  → divergência
R$ -0,01 → divergência
R$ 0,25  → divergência
qualquer valor != R$ 0,00 → divergência
```

Não usar:
- epsilon;
- tolerância visual;
- arredondamento para liberar readiness;
- texto como `praticamente conciliado`;
- ícone de sucesso em zero preliminar.

### Zero pré-cutoff

Quando divergência = `R$ 0,00` antes do cutoff/revalidação final:

```text
valor = R$ 0,00
estado = PRELIMINARY
paridade final = NÃO CONFIRMADA
```

O visual deve impedir interpretação de sucesso final.

---

## Readiness / blockers

`READY_TO_CLOSE` requer simultaneamente:
- cutoff confirmado;
- revalidação aplicável válida;
- sources necessários disponíveis;
- divergência exatamente `R$ 0,00`.

O painel de readiness deve mostrar cada condição separadamente.

Exemplo semântico:

```text
Cutoff                 ✓ confirmado
Revalidação            ✓ válida
Entradas/Saídas        ✓ disponível
P7                     ✓ disponível
H02                    ⚠ indisponível
Paridade               — não calculável
Resultado              BLOCKED
```

Uma source indisponível não pode ser convertida em zero nem permitir status verde global.

---

## Sources e freshness

Resultados estruturados devem carregar:
- source;
- fetched/calculated_at;
- competência;
- unidade/contexto;
- preliminary/final;
- rule/version.

Cada source deve ter estado próprio.

Estados mínimos de apresentação:
- disponível/fresh;
- stale quando contrato definir stale;
- indisponível;
- partial/incompleto;
- erro.

Não inventar threshold de stale; freshness policy pertence ao owner/contract.

---

## Drilldown da conciliação

Níveis previstos:

```text
total
→ grupo
→ item/evidência
```

O drilldown deve explicar de onde vem a divergência, não apenas repetir o total.

Regras:
- preservar filtros/contexto ao navegar;
- permitir ordenar/buscar apenas se o contract suportar;
- valor monetário sempre com sinal e unidade;
- item sem source/evidência não recebe valor default;
- exportação só se capability/necessidade forem aprovadas.

---

## Sacramentação

V1 não executa escrita no ERP.

A authority permanece no owner autorizado.

E03 confirmará executor/permissões reais.

A página pode mostrar readiness e estado canônico; não deve criar botão local de `Sacramentar` enquanto owner/capability não estiverem comprovados.

---

## STOCK_CLOSED

Target: ler estado canônico do owner/ERP, se existir.

T03 é inventário obrigatório e permanece stop condition.

Sem fallback manual silencioso.

Se T03 provar ausência/incompatibilidade, registrar `EXECUTION_DRIFT`.

---

## Histórico

Mostrar eventos materiais:
- cutoff confirmado;
- revalidação iniciada/concluída;
- source indisponível/recuperada quando auditável;
- mudança de input que invalida prontidão;
- READY_TO_CLOSE atingido/perdido;
- estado canônico STOCK_CLOSED recebido.

O histórico não deve inventar evento se o producer não o fornece.

---

## Contratos TARGET — MFE → BFF → owners

```text
plugins/controllership-finance
→ controllership-finance-api
   → Core effective permissions
   → api-delpi / owners canônicos de P7, Entradas-Saídas e H02
   → owner canônico de STOCK_CLOSED quando T03 provar
```

O browser não chama `api-delpi`/ERP/Core diretamente.

Operações semânticas:

| Operação | Semântica |
|---|---|
| getStockClosingState | contexto + state model + cutoff + revalidation + canonical close state |
| confirmCutoff | confirmação humana auditada, sem ERP write |
| revalidateStockInputs | rerun das sources aplicáveis |
| getReconciliation | valores + source/freshness + divergência exata |
| getReconciliationDrilldown | total → grupo → item/evidência |
| getStockClosingHistory | eventos auditáveis conhecidos |

A BFF pode orquestrar leituras e aplicar a regra TARGET de readiness, mas:
- SQL/TOTVS continua no `api-delpi`;
- `STOCK_CLOSED` não é fabricado pelo Portal;
- `confirmCutoff` não equivale a sacramentação;
- `READY_TO_CLOSE` não equivale a `STOCK_CLOSED`.

### AuthZ

```text
authenticated
AND effective_permission(controllership-finance.access)
AND resource_scope / context_access
AND business_rule
```

Para `confirmCutoff`/`revalidateStockInputs`, o backend também verifica se o ator é autorizado pela regra operacional correspondente.

Regras:
- `MANAGE` não implica `ACCESS`;
- unidade é contexto/dado;
- UI não autoriza;
- effective permissions indisponíveis → fail-closed;
- owner/ERP continua authority da sacramentação.

## Reuso obrigatório de `@delpi/plugin-ui`

Import runtime canônico:

```ts
import {
  createDashboardPagePath,
  createDashboardPageHero,
  createDashboardSectionCard,
  MetricKpiCard,
  StatusBadge,
  ProgressTracker,
  AlertQueue,
  DetailFieldGrid,
  DataTableSection,
  Timeline,
  StateBanner,
  StateBox,
  ModalShell,
  ConfirmModalPanel,
  FloatingNoticeStack,
  ActionButton,
  HelpTooltip,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Styles:

```ts
await import("@delpi/plugin-ui/styles");
```

### Mapeamento

| Necessidade | Componente canônico |
|---|---|
| breadcrumb / hero | `createDashboardPagePath` / `createDashboardPageHero` |
| seções | `createDashboardSectionCard` |
| valores monetários | `MetricKpiCard` |
| state/source status | `StatusBadge` |
| state model | `ProgressTracker` |
| readiness/blockers | `AlertQueue` |
| proveniência/freshness | `DetailFieldGrid` |
| drilldown | `DataTableSection` |
| histórico | `Timeline` |
| partial/unavailable | `StateBanner` / `StateBox` |
| confirmação cutoff | `ModalShell` / `ConfirmModalPanel` |
| feedback de revalidação | `FloatingNoticeStack` |
| ações | `ActionButton` |
| ajuda | `HelpTooltip` |
| loading/empty | `LoadingState` / `EmptyState` |

### DO NOT RECREATE

Não criar localmente:
- KPI card monetário;
- state progress tracker;
- status badge;
- blocker/readiness queue;
- detail/provenance grid;
- data table de drilldown;
- timeline;
- modal/confirm shell;
- generic loading/empty/state panels.

Se faltar capability visual reutilizável, registrar `PLUGIN_UI_GAP_FOUND` antes de criar chrome local.

---

## Estados de experiência

### LOADING
- manter estrutura previsível;
- não preencher métricas com `R$ 0,00` enquanto carrega.

### SUCCESS
- sources necessárias responderam para o recorte;
- valores/freshness/state são coerentes;
- zero só é paridade quando as demais condições aplicáveis também estiverem válidas.

### EMPTY
`EMPTY` só é válido quando a ausência de dado for semanticamente correta; conciliação sem source obrigatória é indisponibilidade, não empty.

### PARTIAL
Mostrar sources válidas e bloquear conclusão, indicando exatamente o que falta.

### UNAVAILABLE / UNAVAILABLE_SOURCE
Exibir source afetada e impacto na paridade/readiness.

`UNAVAILABLE` é o estado da experiência/módulo; `UNAVAILABLE_SOURCE` qualifica a source afetada.

Source obrigatória indisponível bloqueia readiness.

### VALIDATION_ERROR
Input/ação inválida preserva o contexto; cutoff/revalidation não recebe optimistic success.

### ERROR
Erro contextual; retry/revalidar somente quando tecnicamente permitido.

### FORBIDDEN
Sem exposição dos valores financeiros.

### NOT_FOUND
Competência/contexto inexistente ou não acessível.

---

## Light / dark, responsividade e acessibilidade

```text
SAME DOM
+ SAME STATE MODEL
+ SAME MONETARY VALUES
+ SAME BLOCKERS
+ THEME TOKENS
= LIGHT / DARK PARITY
```

- TopBar pertence ao shell;
- P3 é deep page e usa `PagePath`;
- desktop mantém conciliação/readiness em hierarquia explícita;
- mobile prioriza estado e divergência sem cards comprimidos;
- `R$ 0,00`/divergência nunca dependem só de cor;
- cutoff, revalidation e drilldown são keyboard-operable;
- focus permanece visível;
- CSS de primitives do kit permanece no `plugin-ui`.

## Edge cases visuais obrigatórios

- H02 indisponível;
- P7 indisponível;
- Entradas/Saídas indisponível;
- cutoff confirmado com source falhando;
- divergência `R$ 0,00` pre-cutoff;
- divergência residual `R$ 0,01` pós-cutoff;
- divergência residual `R$ -0,01` pós-cutoff;
- input alterado pós-revalidação;
- estado owner atrasado;
- unidade/contexto não aplicável.

---

## Critérios visuais de aceite

### VA-P3-01 — State model
O estado PRELIMINARY → STOCK_CLOSED é textual, acessível e visualmente inequívoco.

### VA-P3-02 — Divergência em destaque
A divergência é a métrica monetária principal, mas não oculta Entradas/Saídas, P7 e H02.

### VA-P3-03 — Zero preliminar
`R$ 0,00` antes do cutoff/revalidação aplicável não recebe apresentação de sucesso final.

### VA-P3-04 — Centavo residual
`R$ 0,01` e `R$ -0,01` permanecem visualmente divergentes e bloqueiam readiness.

### VA-P3-05 — Source indisponível
Source obrigatória indisponível aparece como indisponível; nunca como `R$ 0,00`.

### VA-P3-06 — Readiness separada
Cutoff, revalidação, sources e paridade aparecem como condições separadas.

### VA-P3-07 — READY vs CLOSED
`READY_TO_CLOSE` nunca usa linguagem ou chrome que o confunda com `STOCK_CLOSED`.

### VA-P3-08 — Cutoff humano
Confirmação de cutoff exige ação humana explícita e confirmação acessível.

### VA-P3-09 — Revalidation drift
Mudança de input após revalidação volta a página para estado que exige revalidação, sem preservar visual de prontidão.

### VA-P3-10 — Proveniência
Valores exibidos permitem inspecionar source, timestamp/freshness, finality e rule/version.

### VA-P3-11 — Drilldown
Usuário consegue navegar de total → grupo → item/evidência preservando contexto.

### VA-P3-12 — Mobile
No mobile, divergência e estado permanecem prioritários e legíveis sem scroll horizontal de cards.

### VA-P3-13 — Kit-first
Nenhum componente local duplica os exports públicos listados acima.

### VA-P3-14 — Acessibilidade
Status não depende de cor; ações, drilldown e confirmação são operáveis por teclado com foco visível.

### VA-P3-15 — Help
Help contextual explica cutoff, revalidação, paridade exata, zero preliminar, sources/freshness, READY_TO_CLOSE e STOCK_CLOSED.

---

## Scripts e artefatos auxiliares PLANNED

Não criar durante a FASE A.

```text
validate-p3-monetary-parity
- exact cents
- no epsilon
- AC-P3-PARITY-01..07

validate-p3-state-machine
- PRELIMINARY → WAITING_FOR_CUTOFF → REVALIDATION_REQUIRED → READY_TO_CLOSE
- READY_TO_CLOSE != STOCK_CLOSED

validate-p3-source-readiness
- unavailable != zero
- pre-cutoff zero != final
- input change invalidates readiness

validate-p3-owner-boundary
- no ERP write
- STOCK_CLOSED only from canonical owner
- T03 stop enforced

validate-p3-authz
- ACCESS/context/business rule
- MANAGE does not bypass
- fail-closed

validate-p3-deep-links
- competence/context/drilldown
- F5
- no open redirect

validate-p3-help
- exact parity/cutoff/revalidation/READY-vs-CLOSED synchronized

validate-p3-plugin-ui
- MetricKpiCard/ProgressTracker/AlertQueue/DataTableSection/Timeline reused
- no local clone
```

Tecnologia/localização seguem o HEAD da futura implementação.

## Pendências de implementação preservadas

- **E02 correção pós-sacramentação — DOCUMENTATION BLOCKER / DECISION_REQUIRED**;
- E03 executor/permissões — inventory do owner da sacramentação, sem write Portal V1;
- T01 bindings — TO_INVENTORY;
- T03 estado canônico — STOP_CONDITION / TO_INVENTORY.

E02 é diferente dos demais: pode alterar lifecycle, revalidação, auditoria e impacto em P5. A evidência AS-IS/TÉO atual comprova sacramentação e pós-envio, mas não define reabertura/retificação/correção após `STOCK_CLOSED`.

Antes do PASS de A10, é necessário decidir/provar:
- se `STOCK_CLOSED` é terminal para o Portal V1;
- se existe reabertura controlada;
- ou se existe correção/versionamento canônico no owner sem reabrir o fechamento histórico;
- quem autoriza;
- quais inputs são revalidados;
- efeito sobre package finalizado/enviado;
- audit trail obrigatório.

Não inferir a resposta.

---

## Gate documental V2

```text
OBJECTIVE_BOUNDARY_DEFINED   = PASS
OWNERS_DEFINED               = PASS
VISUAL_SPEC_DEFINED          = PASS
CONTRACT_DEFINED             = PASS
AUTHZ_DEFINED                = PASS
PLUGIN_UI_REUSE_DEFINED      = PASS
STATES_DEFINED               = PASS
DEEP_LINK_F5_DEFINED         = PASS
RESPONSIVE_DEFINED           = PASS
LIGHT_DARK_DEFINED           = PASS
A11Y_DEFINED                 = PASS
HELP_SYNC_DEFINED            = PASS
RQ_AC_DEFINED                = PASS
TEST_MATRIX_DEFINED          = PASS
SCRIPTS_ARTIFACTS_PLANNED    = PASS
MONETARY_PARITY_DEFINED      = PASS
POST_STOCK_CLOSED_RULE       = DECISION_REQUIRED
IMPLEMENTATION_AUTHORIZED    = NO
```

Resultado:

```text
A10 P3 ESTOQUE E CONCILIAÇÃO
= PENDING_DECISION_E02
!= READY_FOR_IMPLEMENTATION_BRIEF
!= IMPLEMENTED
```

T03 permanece stop condition técnico mesmo depois de E02 ser fechado.

## Resultado esperado

P3 deve funcionar como **mesa de conciliação e readiness**, em que o usuário consegue provar por que o estoque está ou não apto ao fechamento.

```text
VERIFY SOURCES
→ CONFIRM CUTOFF
→ REVALIDATE
→ RECONCILE EXACTLY
→ UNDERSTAND BLOCKER
→ OBSERVE CANONICAL CLOSE STATE
```

Esse é o contrato visual de P3.
