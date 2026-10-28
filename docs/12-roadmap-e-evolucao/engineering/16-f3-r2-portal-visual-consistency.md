# F3.R2 — Portal Engenharia: consistência visual, paridade de tema, avatar e deploy

## Baseline e reancoragem

- Baseline de referência: `cd3eb369c7` (F3.R1).
- Baseline efetiva após rebase: `efcd8a4435` (`origin/main` — delta apenas helpdesk/checklist, sem overlap com `plugins/engineering`).
- Escopo: `plugins/engineering` apenas. `plugin-ui`, Comercial, Portal host e `engineering-api` intocados.

## Comparação Comercial × Engenharia (G0)

| Propriedade | Owner | Comercial | Engenharia (antes) | Decisão |
|---|---|---|---|---|
| padding da página | root do MFE (`.dashboard-*.dashboard-page`) | `padding: var(--cm-page-padding)` = 24px | ausente (full-bleed) | adotar mesma geometria neutra |
| gap entre seções | root do MFE | 24px | `1rem` no stack | 24px via token |
| canvas/fundo | root do MFE | `--app-canvas` + gradiente `primary` 5% | ausente | mesma fórmula |
| tokens do kit | root do MFE | `--delpi-ui-*` mapeados de tokens globais | não mapeados | mesmo mapa neutro |
| dark theme | `:root[data-theme="dark"] .dashboard-*` | color-mix `--surface-2` | ausente | mesmo bloco |
| mobile | `@media (max-width:768px)` | padding 12px | apenas grid | mesmo breakpoint/tokens |
| avatar | Core `/me/person-profile` | via proxy commercial-api | iniciais fixas | leitura direta do owner |

## Causa raiz do padding

O Portal host não aplica padding de página — cada MFE é dono do seu root
`.dashboard-<scope>.dashboard-page`. O Comercial define `padding: 24px`,
`gap` e o canvas nesse root; a Engenharia não tinha nenhuma dessas regras,
logo os filhos ocupavam toda a largura útil.

## Correções aplicadas

### Container/tema (`src/index.css`)

- `.portal-engineering`: tokens `--en-*` espelhando o mapa neutro
  (`--delpi-ui-*` ← tokens globais `:root`/`[data-theme="dark"]`).
- `.portal-engineering.dashboard-page`: `padding: 24px`, `gap: 24px`,
  `min-height: 100%`, background `--app-canvas` + gradiente `primary`.
- Bloco `:root[data-theme="dark"] .portal-engineering` com os mesmos
  color-mix do padrão dos portais.
- `@media (max-width:768px)`: padding 12px + tokens mobile do kit
  (`card-padding-mobile`, `section-header-gap-mobile`, `field-stack-gap-mobile`).
- Sem seletores `.delpi-ui-*` no CSS do MFE (somente variáveis) — audit
  `mfe_plugin_ui_css` segue sem findings de engineering.

### Hero (`HomePage.tsx` + catálogo)

- Bug real: `title={greeting + greetingTail}` — a descrição estava
  concatenada ao título. Corrigido: `title={greeting}`
  (`formatPortalGreeting` → "Boa tarde, Robério") e `description`
  passa a ser a frase contextual, elemento separado do `PageHero`.
- Ação `Atualizar` já estava no slot `actions` do PageHero (padrão Comercial).

### Avatar (`EngineeringPluginShell.tsx` + `api/personProfileApi.ts`)

- Fonte oficial: **Core API** `GET /core-api/me/person-profile`
  (`has_photo`) → `GET /core-api/me/person-profile/photo` (blob) —
  mesmo owner/contrato que o Comercial consome via proxy commercial-api.
- `useAvatarPhoto(subject)`: objectURL revogado e fetch abortado no
  cleanup; escopo pelo `sub` do JWT — troca de usuário não reutiliza
  imagem; falha em qualquer etapa degrada para iniciais.
- `avatarHref="/profile"` (rota do Portal host — dono do Meu Perfil).
- Nenhum token/URL persistido; Bearer humano via `getAccessToken`.

## Testes

- `vitest run`: **50/50** (7 arquivos; +`personProfileApi.test.ts`).
- `tsc --noEmit`: 0 erros. `eslint src`: 0 problemas.
- `vite build`: OK (patch federation React preservado; aviso conhecido lucide-react >500kB).
- Audits: `backend_boundaries` 0, `fastapi_authz` 0, `platform_guardrails` 0,
  `architecture_phase3` OK; `mfe_plugin_ui_css`/`plugin_ui_duplication`
  = findings pré-existentes repo-wide, zero de engineering.

## Validação visual

QA visual autenticado: pendente do gate administrativo (manifest 0.2.0
na Core + grant `engineering.access`). Layout validado por paridade de
contrato (mesma geometria/tokens do padrão dos portais), não por
screenshot — classificar R2-20 conforme evidência disponível.

## Deploy e smoke

- Commit → push `main` (ff-only) → `srv-api`: `git pull --ff-only` +
  `up-prod-sequential.sh --build engineering`.
- Smoke público: remoteEntry/rotas/API (ver relatório EVA).

## Residuais

- Registro do manifest 0.2.0 na Core — `PENDING_OPERATOR_TOKEN`.
- Grant `engineering.access` — `PENDING_GRANT_APPROVAL`.
- Smoke/QA visual autenticado — pendente do gate acima.
- `avatarHref` usa a rota estável `/profile` do Portal; se o host
  expuser contrato próprio de navegação ao perfil, migrar para ele.

## Próxima etapa

Operador com `apps.manage` registra o manifest → grant autorizado →
smoke autenticado + QA visual (claro/escuro/mobile) → fechar Activation Gate.
