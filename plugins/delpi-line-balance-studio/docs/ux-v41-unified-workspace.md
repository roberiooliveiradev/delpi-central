# UX V4.1 — Bancada unificada do Line Balance Studio

**Status:** IMPLEMENTED / TEST_RUN  
**Tarefa:** `EVA-LBS-V41-UNIFIED-WORKSPACE-UX-REFACTOR-01`  
**Rota HML:** `/apps/engineering/processes/line-balancing`

## 1. Problema identificado na V4

As capturas do Product Owner sobre a V4 em HML mostraram fragmentação visual:

- A bancada ficava centralizada em largura máxima estreita (`width: min(calc(100% - 36px), 1280px)`), com vazios laterais grandes em telas amplas.
- O Portal Engenharia renderizava **fora** do Studio dois `SectionCard` concorrentes — `Operações oficiais do roteiro` e `Análise oficial M1 — capacidade e takt` — mais uma linha de `FormActions` com exportações e limpeza.
- A tabela de operações oficiais do host duplicava a tabela de operações do estudo OBSERVED dentro do Studio.
- A identificação do produto aparecia tanto no cabeçalho do Studio quanto nos cartões externos.
- O conjunto parecia duas aplicações empilhadas, não uma bancada.

## 2. Decisão de produto V4.1

**Uma única bancada de trabalho.** Toda a experiência de estudo — contexto, ações, KPIs, método ativo, detalhes oficiais e análise M1 — vive dentro do elemento `delpi-line-balance-studio`. O host deixa de renderizar qualquer cartão de conteúdo ao redor do Studio e passa a operar somente pelo contrato público (propriedades e eventos).

Decisões substituídas em relação à V4:

| V4 | V4.1 |
| --- | --- |
| Largura útil limitada a 1280px | Largura fluida na área útil do Portal |
| Análise M1 e tabela oficial em cartões do host | Apresentados dentro do workspace do Studio |
| Exportações/limpeza em barra externa do host | `Mais ações` dentro da barra contextual do Studio |
| Metadados do roteiro em segunda tabela | Disclosure `Detalhes oficiais` na seção Operações |

## 3. Layout antes → depois

**Antes (V4):**

```text
Portal Engenharia
└── SectionCard: Operações oficiais do roteiro   ← fora do Studio
└── SectionCard: Análise oficial M1               ← fora do Studio
└── FormActions: CSV / Excel / PDF / Limpar       ← fora do Studio
└── delpi-line-balance-studio (max 1280px, centrado)
    ├── rail de métodos
    └── bancada
```

**Depois (V4.1):**

```text
Portal Engenharia
└── Área útil do MFE (largura fluida)
    └── delpi-line-balance-studio
        ├── Rail de métodos (retrátil)
        └── Bancada
            ├── Contexto do estudo (compacto) + badges de provenance
            ├── Barra de ações: Cenário | Novo cenário | Condições | Mais ações ▾ | badge de salvamento
            ├── KPIs compactos do método
            └── Bancada do método ativo
                ├── M1: diagnóstico local + Análise oficial M1 (OBSERVED)
                └── M5: Yamazumi + Operações (+ Detalhes oficiais sob demanda)
```

## 4. Wireframes

### Desktop (≥1024px)

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Balanceamento de Linha — DELPI · Engenharia de Processos                 │
├───────────┬──────────────────────────────────────────────────────────────┤
│ MÉTODOS   │ Produto 90264302  [Roteiro oficial · OBSERVED] [DRAFT_LOCAL] │
│           │ Filial 01 · Estágio 10 · Roteiro 01                          │
│ ▸ M1      │                                                              │
│ ● M5      │ [Cenário ▾] [+ Novo cenário] [Condições] [Mais ações ▾] ✓    │
│           │ ── Trocar origem | CSV | Excel | PDF | Limpar estudo ──      │
│ Próximos  │                                                              │
│ métodos ▸ │ [Takt] [Tempo produtivo] [Maior carga] [Sem posto]           │
│           │                                                              │
│           │ ┌─ YAMAZUMI ──────────────────────────── [+ Adicionar posto]┐│
│           │ │ Gráfico carga por posto × takt                          ││
│           │ └─────────────────────────────────────────────────────────┘│
│           │ ┌─ OPERAÇÕES ─── [Detalhes oficiais] [+ Adicionar operação]┐│
│           │ │ Operação | Origem | Tempo | Posto | Ações               ││
│           │ └─────────────────────────────────────────────────────────┘│
└───────────┴──────────────────────────────────────────────────────────────┘
```

### Mobile (≤900px)

```text
┌──────┬─────────────────────────────┐
│ ⌃    │ Produto 90264302 [OBSERVED] │
│ M1   │ Filial 01 · Estágio 10      │
│ M5 ● │ [Cenário▾][+][Condições][⋯] │
│ …    │ [Takt][Produtivo]           │
│      │ [Maior carga][Sem posto]    │
│      │ ┌─ YAMAZUMI ──────────────┐ │
│      │ │ gráfico rola se preciso │ │
│      │ └───────────────────────┘ │
│      │ ┌─ OPERAÇÕES ───────────┐ │
│      │ │ tabela scroll interno │ │
│      │ └───────────────────────┘ │
└──────┴─────────────────────────────┘
```

Abaixo de 900px a rail fica sempre no modo compacto de ícones, mesmo que a preferência seja expandida — decisão da V4 mantida, pois rail expandida + bancada excede a viewport.

## 5. Regras por região

### Sidebar de métodos (inalterada na V4.1)

- `CollapsibleToolRail` do Plugin UI, preferência persistida em `delpi-lbs:ui`.
- Grupo principal: métodos executáveis (M1, M5). `Próximos métodos`: M2–M4, M6 desabilitados com `Planejado`.
- ≤900px: sempre compacta (ícones + tooltip), independente da preferência.

### Cabeçalho compacto do estudo

- Produto oficial: `Produto {code}` + `Filial {branch} · {stage} · Roteiro {route}` + badges `Roteiro oficial · OBSERVED` e `Estudo local · DRAFT_LOCAL`.
- Estudo manual: nome do estudo + `Rascunho manual · DRAFT_LOCAL`.
- Nome editável via `CommitInput` (renomeia o rascunho local, nunca o roteiro).
- Nenhum outro cabeçalho repete a identificação do produto.

### Barra de ações contextual

- Primárias: seletor de cenário (quando >1), `+ Novo cenário`, `Condições de produção`.
- `Mais ações ▾` (disclosure `aria-expanded`/`aria-controls`): `Trocar origem`, `Exportar CSV`, `Exportar Excel`, `Exportar PDF`, `Limpar estudo`.
- Badge de salvamento (`draftSave`) ao lado das ações, resolvido pelo host.
- `Trocar origem` e `Limpar estudo` exigem confirmação (`role="alertdialog"` / fluxo do host).

### KPIs compactos

- Faixa de `SimpleKpiCard` imediatamente abaixo das ações: Takt de referência, Tempo produtivo, Maior carga, Sem posto.
- `—` quando não calculável; nunca zero no lugar de `UNKNOWN`.
- Reorganiza em grade no mobile.

### Bancada Yamazumi (M5)

- `SectionCard Yamazumi` + `StackedColumnChart` com takt de referência, cargas parciais marcadas e drag-and-drop com alternativa por teclado.
- `SectionCard Operações` + `DataTable` com Origem (`Oficial` / `Ajuste local` / `Local`), tempo editável, posto e ações.
- **Estado vazio:** sem postos → `Nenhum posto configurado.` + orientação + CTA `+ Adicionar posto`; sem operações → `Adicione uma operação para começar.` Nenhum gráfico fictício.
- Quando há 0 postos, o CTA do estado vazio é o único `+ Adicionar posto` visível (a ação do cartão é suprimida para não duplicar o affordance).

### Detalhes oficiais do roteiro

- Botão `Detalhes oficiais` (disclosure) nas ações do cartão Operações, visível somente quando o host fornece `officialOperations`.
- Revela tabela compacta com `Operação | Descrição | CT | Recurso | Tempo padrão (min/peça) | Setup (h/lote)` — consulta, não edição. Tempo oficial ausente exibe `UNKNOWN`.
- Substitui a antiga tabela `Operações oficiais do roteiro` que o host renderizava abaixo do Studio — sem segunda tabela concorrente.

### Análise oficial M1

- No painel do método M1, abaixo do diagnóstico local (`CALCULATED local`), aparece o bloco `Análise oficial M1` **somente em estudo OBSERVED**.
- `Executar análise oficial` emite `studio-analysis-run`; o host executa o BFF/domínio e devolve `analysisState`.
- Fases: `idle` (CTA habilitado), `running` (botão `Calculando…` desabilitado), `result` (KPIs `CALCULATED`: takt min/peça, conteúdo de trabalho, mínimo teórico de postos, gargalo candidato), `error` (mensagem do host em `StateBox`).
- `issues` do host desabilitam a execução e são listadas como impedimentos.
- `stageCovered: false` → aviso de que a resposta não cobre o estágio; `operationsMissingTime > 0` → aviso `UNKNOWN, nunca zero`.
- Em estudo manual o bloco não aparece — exibe aviso de que não há contrato de cálculo oficial.

## 6. Estado compartilhado e provenance

- Um único `study` alimenta contexto, ações, KPIs e bancada de qualquer método; trocar M1↔M5 não perde operações, postos, cenários ou condições.
- Trocar de estudo (novo `study` no setter) reseta `analysisState`, `officialOperations`, `draftSave`, disclosures e confirmações — resultados oficiais não vazam entre contextos.
- Provenance preservada: `OBSERVED` (roteiro), `DRAFT_LOCAL` (rascunho), `CALCULATED` (resultado oficial), `CALCULATED local`/diagnóstico (local), `SIMULATION` (cenários), `UNKNOWN` (tempos ausentes).

## 7. Contrato público com o host (V4.1)

Extensão **aditiva** sobre o contrato V4. Detalhes em `contracts.md`.

| Superfície | Direção | Uso |
| --- | --- | --- |
| `routingState` | host → Studio | fases da busca oficial (idle/searching/awaiting-stage/error) |
| `analysisState` | host → Studio | fases e resultado da análise oficial M1 |
| `officialOperations` | host → Studio | metadados do roteiro para `Detalhes oficiais` |
| `draftSave` | host → Studio | badge de persistência do rascunho |
| `studio-analysis-run` | Studio → host | usuário pediu a análise oficial M1 |
| `studio-export` | Studio → host | `{ format: "csv" \| "xlsx" \| "pdf" }` |
| `studio-clear-study` | Studio → host | pedido de limpeza (confirmação e persistência no host) |
| `study-change`, `studio-routing-search`, `studio-routing-context`, `studio-manual-study`, `studio-origin-reset`, `studio-method-change` | Studio → host | inalterados |

O cálculo oficial M1 continua no BFF/domínio do Portal Engenharia — o Studio nunca executa, estima ou arredonda o resultado; só apresenta o payload tipado.

## 8. Componentes Plugin UI reutilizados

`CollapsibleToolRail`, `NavigationCard`, `SectionCard`, `ActionButton`, `IconButton`, `ModernSelectControl`, `DataTable`, `SimpleKpiCard`, `StatusBadge`, `StateBox`, `StackedColumnChart`, `CommitInput`. Nenhum componente novo foi promovido ao kit nesta etapa — `Mais ações` é uma composição local de `ActionButton` + disclosure (Abstraction Gate: um único consumidor ainda não justifica componente genérico).

## 9. Estados vazios

| Condição | Apresentação |
| --- | --- |
| Sem operações | `Adicione uma operação para começar.` (tabela) + CTA `+ Adicionar operação` |
| Operações sem postos | `Nenhum posto configurado.` + `Crie um posto e atribua operações para visualizar as cargas.` + CTA `+ Adicionar posto` |
| Sem condições válidas | KPIs `—` + orientação para condições de produção no painel M1 |
| Sem `officialOperations` | botão `Detalhes oficiais` ausente |
| `analysisState.phase = idle` | bloco M1 com CTA, sem KPIs |

## 10. Acessibilidade

- Disclosures com `aria-expanded` + `aria-controls` (`Mais ações`, `Detalhes oficiais`, `Condições`).
- Confirmações com `role="alertdialog"` e opção de cancelar (`Manter estudo`).
- `aria-live="polite"` nas faixas de KPI e no resultado M1.
- Tabela com scroll interno — a página nunca ganha overflow horizontal.
- Rail compacta em ≤900px mantém foco visível e tooltips.

## 11. Critérios de aceite

| RQ | Critério | Evidência |
| --- | --- | --- |
| UX41-01 | Bancada usa a largura útil do Portal, sem limite de 1280px | CSS `.layout` sem cap + screenshot 1440px |
| UX41-02 | Nenhum cartão de conteúdo do host ao redor do Studio | diff `LineBalancingPage.tsx` + teste estrutural |
| UX41-03 | Barra de ações única com primárias + `Mais ações` | preview-smoke (5 itens no grupo) |
| UX41-04 | `Detalhes oficiais` apresenta CT/recurso/tempo/setup sob demanda | preview-smoke + e2e |
| UX41-05 | Análise M1 dentro do método M1, executada pelo host | preview-smoke (`studio-analysis-run`) + e2e |
| UX41-06 | Estado vazio do Yamazumi orienta a próxima ação | preview-smoke (`Nenhum posto configurado`) |
| UX41-07 | Exportações e limpeza emitidas por evento, refletindo o estudo | teste de contrato + e2e |
| UX41-08 | Troca de método preserva estudo; troca de estudo limpa estado oficial | unit + e2e |
| UX41-09 | Sem overflow em 1440/1024/390/320, light/dark | preview-smoke + capturas HML |
| UX41-10 | Resultado M1 exibe `CALCULATED`; ausência de tempo exibe `UNKNOWN` | preview-smoke + e2e |

## 12. Evidências de teste

- `node --test tests/` no pacote do Studio (contrato público).
- `tests/preview-smoke.mjs` (Chromium): fluxo oficial completo — busca, `Detalhes oficiais`, `Mais ações`, `studio-analysis-run` com resultado, vazio de postos, 1440/1024/390/320, dark.
- Suite Vitest do MFE Engenharia (estrutural da página + adapter).
- E2E autenticado HML `processes-yamazumi.spec.ts` em desktop/tablet/mobile.

## 13. Limitações e pendências

- `Mais ações` é um disclosure, não um menu popover com roving tabindex — promoção ao Plugin UI depende de segundo consumidor.
- `analysisState` cobre somente M1; M2–M4 e M6 permanecem `Planejado` sem contrato.
- O PDF/Excel gerados pelo host não mudaram de formato — apenas o ponto de disparo migrou para dentro do Studio.
- `Detalhes oficiais` exibe os campos que o adapter do host fornece; campos ausentes aparecem `—`/`UNKNOWN`.

**Não reescreve o histórico:** a V4 continua documentada em `ux-v4-study-entry-and-method-sidebar.md`; esta especificação registra apenas a evolução V4.1 e as decisões substituídas (seção 2).
