# Manutenção — cobertura de helps

Padrão: **hover no texto do rótulo** via `DM_HELP` em [`helpTooltips.ts`](../../plugins/maintenance/src/content/helpTooltips.ts). Proibido `HelpTooltip` sem `wrap` (ícone ?).

## Inventário

| Superfície | Chave DM_HELP | Status |
|------------|---------------|--------|
| Shell / TopBar | `shell.*` | P0 |
| Home | `home.*` | P0 |
| Filiais | `filiais.*` | P0 |
| Mini-aplicadores lista | `miniAplicadores.*` | P0 |
| Relatório preventivo | `relatorio.*` | P0 |
| Configuração | `configuracao.*` | P0 |
| Programas máquina | `programas.*` | P0 |
| Manutenção geral | `manutencaoGeral.*` | P0 |
| Revisão programada | `revisao.*` | P0 |
| Detalhe preventivo | `preventivaDetalhe.*` | P1 |

## Gate

```bash
node plugins/maintenance/src/content/helpCoverage.structural.test.mjs
```

## Isenções

- Botões só-ícone com `aria-label` de ação (Editar, Excluir) — não exigem help de negócio.
- PlaceholderPage (roadmap) — texto estático sem help operacional.
