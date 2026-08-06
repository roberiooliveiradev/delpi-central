# Design / IA — Portal Comercial (Wave G)

> **Status:** Wave G (UI + CRM inicial) · ago/2026  
> **Produto:** Portal Comercial · `id` `commercial` · `/apps/commercial`  
> **UI kit:** `@delpi/plugin-ui` · prefixo MFE `cm-` · root `.dashboard-commercial`  
> **Wireframes:** [WIREFRAMES.md](./WIREFRAMES.md) · **Perfis:** [PERFIS-E-PERMISSOES.md](./PERFIS-E-PERMISSOES.md)

## Princípios de informação (Overview → Focus → Detail → Action)

| Camada | Superfície | Objetivo |
|--------|------------|----------|
| **Overview** | Início (`/`) | Status, alertas, atalhos — sem regra pesada |
| **Focus / Action** | Meu dia (`/my-day`) | Worklist priorizada; concluir / criar tarefa |
| **Detail** | Pedidos, carteira, conta | Operação e Account 360 |
| **Admin** | Carteiras (`/seller-portfolios`) | Configuração (permission manage) |

Analytics pesado (ROL/OTD/BI) permanece em deep link para `dashboard-commercial` / propostas — não embutido no portal operacional.

## Navegação por objeto (Wave G)

```text
Início → Meu dia → Pedidos em aberto → Minha carteira → Conta → Carteiras (admin)
```

Sem categorias vagas. Escopo (carteira/vendedor) visível no chrome via `ScopeChipBar`.

## Alinhamento `.cursor`

| Regra | Aplicação |
|-------|-----------|
| `plugins-reusable-components` | Componentes novos no kit; MFE só compõe; zero CSS de `.delpi-ui-*` no MFE |
| `plugins-visual-design-system` | Tokens `--cm-*` → `--delpi-ui-*`; dark via `data-theme`; escopo `.dashboard-commercial` |
| `mfe-modal-host-contained` | Dialogs de tarefa/transferência contidos no host |
| `infra-sequential-container-startup` | Rebuild: `plugin-ui` → `commercial` → `commercial-api` |
| `test-and-commit` | Testes API + build MFE antes de fechar a wave |

## Componentes kit (Wave G)

| Componente | Uso |
|------------|-----|
| `AlertQueue` | Home “Precisa de atenção” |
| `ScopeChipBar` | Chrome escopo carteira/vendedor |
| `WorklistItem` | Linha do Meu dia |
| `Timeline` (existente) | Timeline de activities na conta |
| `EmptyState` + children CTA | Onboarding WF-11 |

## UX

- Uma ação primária por seção; ≤ 2 cliques do Início até a ação.
- Loading/erro por seção (`allSettled`); empty states com próximo passo.
- Mobile ≤768: cards / botões ≥44px (WF-12).
- Semântica de status via `StatusBadge` / tones do kit — sem cores hardcoded.

## Fora desta wave

F2c (PVA), prospects/pipeline/forecast (Wave H), F3–F4 runtime module, rentabilidade.
