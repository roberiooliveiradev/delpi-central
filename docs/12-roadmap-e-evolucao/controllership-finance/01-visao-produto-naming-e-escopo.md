# 01 — Visão do Produto, Naming e Escopo

## Nome oficial

**Portal Controladoria & Finanças**.

"Portal Controladoria/Financeiro" é working label histórico e está superseded.

## Escopo

Produto multi-macroprocesso na Minha DELPI para:
- organizar processos;
- reduzir fragmentação;
- automatizar regras determinísticas;
- centralizar evidências/pendências;
- permitir auditoria;
- oferecer visão operacional/gerencial;
- usar IA de forma assistiva;
- respeitar owners de origem.

## Primeira funcionalidade

**Central de Fechamento**.

Primeiro processo: **PROC-0072 — Gestão do Fechamento Mensal da Controladoria**.

## Arquitetura de informação

Topbar canônica:

```text
Portal Controladoria & Finanças
├── Início
├── Visão geral
├── Sala de interação
├── Minhas tarefas
├── Administração
└── Ajuda
```

O `Início` funciona como hub das funcionalidades:

```text
Início
└── Central de Fechamento
    ├── Cockpit da Competência
    ├── Checklist e Documentos
    ├── Estoque e Conciliação
    ├── Classificações e Pendências
    └── Pacote e Envio
```

A `Visão geral` é a superfície analítica do Portal e deve apresentar indicadores financeiros com owner/source/fórmula comprovados.

Administração é transversal ao Portal e consolida P6.

Novos macroprocessos entram futuramente no Início sem alterar a identidade do produto.

## Fronteiras

A matriz detalhada de produtos, owners e regras de integração está em [21-boundaries-produtos-e-owners.md](./21-boundaries-produtos-e-owners.md).


### Portal Financeiro P0
`plugins/financial` + `financial-api` continuam distintos. Não inferir absorção, migração, desativação, banco comum ou transferência de ownership.

### Roadmap financeiro-controladoria
Permanece discovery/histórico Transforma+. Não substitui este TARGET.

## Permissions do produto

O modelo permanece deliberadamente simples:

```text
controllership-finance.access
controllership-finance.manage
```

Não criar permission por página, botão, CRUD, filial ou unidade.

Filial/unidade pode existir como dimensão de dados, não como permission code dedicado deste Portal.

## Identidade técnica congelada

```text
plugin id       = controllership-finance
plugin folder   = plugins/controllership-finance
basePath        = /apps/controllership-finance
BFF             = controllership-finance-api
BFF baseUrl     = /apps/controllership-finance-api
ACCESS          = controllership-finance.access
MANAGE          = controllership-finance.manage
```

O BFF deve seguir o padrão vigente das APIs/portais atuais da plataforma, revalidado no HEAD antes do scaffold.

## Ainda não definido tecnicamente

- storage;
- schema físico/migrations;
- detalhes de persistência;
- deployment topology;
- bindings concretos de cada source/owner.
