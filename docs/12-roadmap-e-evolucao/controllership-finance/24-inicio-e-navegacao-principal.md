# 24 — Início e Navegação Principal

## Estado

**TARGET / DOCUMENTED**

Este documento define a arquitetura de informação da topbar do **Portal Controladoria & Finanças**.

## Topbar canônica

A navegação principal do Portal contém exatamente:

```text
Início
Visão geral
Sala de interação
Minhas tarefas
Administração
Ajuda
```

Não adicionar nova entrada de topbar sem decisão explícita de produto.

## Rotas lógicas

Seguindo o padrão atual dos Portais Comercial e Suprimentos:

| Item | Rota TARGET | Permission |
|---|---|---|
| Início | `/apps/controllership-finance` | `controllership-finance.access` |
| Visão geral | `/apps/controllership-finance/overview` | `controllership-finance.access` |
| Sala de interação | `/apps/controllership-finance/interaction-rooms` | `controllership-finance.access` |
| Minhas tarefas | `/apps/controllership-finance/my-tasks` | `controllership-finance.access` |
| Administração | `/apps/controllership-finance/administration` | `controllership-finance.manage` |
| Ajuda | `/apps/controllership-finance/help` | `controllership-finance.access` |

Identifiers técnicos são em inglês; labels de UX permanecem PT-BR.


## Reuso obrigatório de `@delpi/plugin-ui`

Esta página não deve recriar chrome de navegação, cards de launcher ou estados genéricos.

Import canônico em MFE federado:

```ts
import {
  createDashboardTopBar,
  createDashboardSectionRouteCard,
  createDashboardNavigationCard,
  createDashboardRecentAccessStrip,
  createDashboardPageHero,
  EmptyState,
  LoadingState,
} from "@delpi/plugin-ui/index";
```

Estilos/runtime do kit:

```ts
await import("@delpi/plugin-ui/styles");
```

Uso esperado:

| Necessidade | Reuso canônico |
|---|---|
| topbar principal | `createDashboardTopBar` |
| launcher de funcionalidades com subrotas | `createDashboardSectionRouteCard` |
| card simples de entrada em uma funcionalidade | `createDashboardNavigationCard` |
| acessos recentes, quando habilitados | `createDashboardRecentAccessStrip` |
| hero/cabeçalho da página | `createDashboardPageHero` |
| loading/empty genéricos | `LoadingState` / `EmptyState` |

`SectionRouteCard` e `NavigationCard` recebem conteúdo de domínio do Portal; o kit controla chrome, foco e acessibilidade.

**DO NOT RECREATE:** TopBar, underline/nav chrome, launcher-card chrome, recent-access chrome, loading/empty genéricos.

## Modelo de permissions

O Portal usa somente:

```text
controllership-finance.access
controllership-finance.manage
```

Não criar permission por página, botão, endpoint, CRUD, filial, unidade, indicador ou funcionalidade interna.

`ACCESS` autoriza o uso normal do Portal.

`MANAGE` autoriza administração/configuração. Não deve ser usado para fragmentar a navegação operacional.

## Unit scope / filial

Para este Portal:

```text
BRANCH_PERMISSION_CODES = NO
UNIT_SCOPE_PERMISSION_MODEL = NOT_APPLICABLE
```

Filial/unidade pode existir como dimensão de dados, filtro ou contexto do processo quando a fonte exigir, mas não como permission code dedicado do Portal.

AuthZ continua server-side e fail-closed.

## Papel do Início

`Início` é a home/root do produto e funciona como hub de funcionalidades.

Estrutura inicial:

```text
Início
└── Central de Fechamento
    ├── Cockpit da Competência
    ├── Checklist e Documentos
    ├── Estoque e Conciliação
    ├── Classificações e Pendências
    └── Pacote e Envio
```

Novos macroprocessos/funcionalidades entram futuramente no Início sem renomear o Portal.

## Central de Fechamento

A Central de Fechamento é a primeira funcionalidade do Portal, não uma entrada adicional da topbar.

Ela agrupa P1–P5:

| Página interna | Documento |
|---|---|
| Cockpit da Competência | [08-p1-cockpit-da-competencia.md](./08-p1-cockpit-da-competencia.md) |
| Checklist e Documentos | [09-p2-checklist-e-documentos.md](./09-p2-checklist-e-documentos.md) |
| Estoque e Conciliação | [10-p3-estoque-cutoff-e-conciliacao.md](./10-p3-estoque-cutoff-e-conciliacao.md) |
| Classificações e Pendências | [11-p4-classificacoes-e-pendencias.md](./11-p4-classificacoes-e-pendencias.md) |
| Pacote e Envio | [12-p5-pacote-finalizacao-e-envio.md](./12-p5-pacote-finalizacao-e-envio.md) |

Administração permanece transversal ao Portal e é documentada em [28-administracao.md](./28-administracao.md).

## Composição lógica do Início

```text
ProductHeader
→ FunctionalityLauncher
→ CentralClosingCard
→ RecentContext
→ ContextualHelp
```

Os nomes acima são lógicos, não contrato de componente React.

## CentralClosingCard

Deve apresentar somente informação suficiente para orientar a entrada na funcionalidade, por exemplo: competência corrente quando existir, estado resumido confiável, blockers materiais quando disponíveis e ação de entrada na Central.

Não duplicar o Cockpit inteiro no Início.

Se a fonte necessária estiver indisponível, mostrar estado honesto; ausência/erro não vira zero nem sucesso.

## Estados de experiência

Cobrir `LOADING`, `EMPTY`, `PARTIAL`, `UNAVAILABLE_SOURCE`, `ERROR`, `FORBIDDEN` e `NOT_FOUND`.

## Padrões de UX

- topbar estável entre páginas;
- item ativo identificável sem depender apenas de cor;
- navegação por teclado e foco visível;
- mobile responsivo e claro/escuro;
- deep link/F5;
- Help contextual;
- nenhum botão/ocultação de UI substitui AuthZ backend.

## Não objetivos

O Início não substitui a Visão geral, não vira dashboard analítico completo, não cria workflow próprio e não executa validação, sacramentação ou envio.

## Critério de aceite documental

```text
TOPBAR = [Início, Visão geral, Sala de interação, Minhas tarefas, Administração, Ajuda]
```

e:

```text
P1–P5 ∈ Central de Fechamento
P1–P5 ∉ topbar principal
```
