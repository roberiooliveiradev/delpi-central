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

```text
Portal Controladoria & Finanças
├── Central de Fechamento
│   ├── Visão Geral
│   ├── Checklist e Documentos
│   ├── Estoque e Conciliação
│   ├── Classificações e Pendências
│   ├── Pacote e Envio
│   └── Configurações
└── futuros macroprocessos
```

## Fronteiras

A matriz detalhada de produtos, owners e regras de integração está em [21-boundaries-produtos-e-owners.md](./21-boundaries-produtos-e-owners.md).


### Portal Financeiro P0
`plugins/financial` + `financial-api` continuam distintos. Não inferir absorção, migração, desativação, banco comum ou transferência de ownership.

### Roadmap financeiro-controladoria
Permanece discovery/histórico Transforma+. Não substitui este TARGET.

## Ainda não definido tecnicamente

- plugin id;
- rota/basePath;
- BFF;
- storage;
- manifest;
- schemas;
- deployment topology.
