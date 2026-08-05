# Tokens do portal UI kit

Fonte de verdade: [`portal/src/index.css`](../index.css) (`:root` e `:root[data-theme="dark"]`).

| Token | Uso no kit |
|-------|------------|
| `--primary` | Botão primary, tabs ativas, anel de foco |
| `--secundary` | Texto principal (light) |
| `--text` / `--text-muted` | Tipografia |
| `--surface` / `--surface-2` / `--surface-3` | Fundos de chrome, controles, hover |
| `--border` / `--border-2` | Bordas |
| `--control-bg` / `--control-text` / `--control-border` / `--control-placeholder` | Inputs / selects / textareas |
| `--danger` / `--success` / `--warning` | Tons de Badge / Alert / invalid |
| `--alert-*-border` / `--alert-*-bg` | Alert success/danger |
| `--shadow` | Elevação (dropdowns) |
| `--focus-ring` | Anel de foco genérico |

## Controles (`.portal-ui-control`)

- Altura: `md` = 36px, `sm` = 32px
- Raio: 8px
- Foco: `border-color: var(--primary)` + `box-shadow: 0 0 0 3px color-mix(in srgb, var(--primary) 12%, transparent)`
- Inválido: `[aria-invalid="true"]` → borda `--danger`

## Proibido

Cores hardcoded (`#fff`, `rgba(0,0,0,0.6)`) nos CSS do kit — exceção: texto sobre `--primary` / `--danger` em botões filled (`#ffffff` para contraste).
