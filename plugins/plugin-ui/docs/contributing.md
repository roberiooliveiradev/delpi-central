# Como contribuir — `@delpi/plugin-ui`

## Antes de adicionar um componente

1. O componente será usado em **pelo menos dois plugins**, ou substitui **cópias já duplicadas** no monorepo?
2. Não acopla domínio (sem strings PT fixas, sem chamadas HTTP, sem rotas)?
3. Estilos usam prefixo `delpi-ui-*` e tokens CSS documentados (consumidor **não** espelha esse CSS)?
4. Funciona em tema claro/escuro via vars do portal?

Se alguma resposta for não, o componente pertence ao plugin específico — não ao pacote compartilhado.

## Fluxo para componente novo

```text
1. Escolher família em src/components/{familia}/
2. Implementar Component.tsx + testes *.test.tsx
3. Exportar em src/components/{familia}/index.ts
4. Reexportar em src/index.ts
5. Documentar em docs/component-catalog.md
6. Adicionar estilos em src/styles.css (ou src/styles/{familia}.css importado)
7. Adicionar demo no catálogo visual (`src/catalog/demos/{familia}.tsx` + registry)
8. Migrar um segundo consumidor ou remover duplicata local
9. Atualizar migration-catalog.md

### Plugin com `Dockerfile` (consumidor MFE)

1. Seguir [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md) — **sem** `COPY plugin-ui`.
2. Compose: `<<: *plugin-ui-federated`.
3. Rodar `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check`.
4. Rodar `python3 scripts/ci/audit_plugin_ui_duplication.py --check` (duplicatas bloqueantes).
```

## Catálogo visual (app do portal)

O mesmo pacote expõe `./App` — app federado de listagem/prévia:

- Código: `src/app/` (shell) + `src/catalog/` (registry + demos)
- Inventário obrigatório: `src/catalog/visualComponents.ts` (um export visual = uma entrada)
- Cobertura: `npm test` → `componentRegistry.test.ts` falha se faltar componente
- Manifesto: [`plugin-ui.manifest.json`](../plugin-ui.manifest.json) — permissão `plugin-ui.view`
- Dev local: `npm run dev` (porta 5010) monta o catálogo em `#root`
- Registro: `TOKEN=… ./scripts/register-manifest.sh`

**Novo export público visual:**

1. Documentar em `component-catalog.md`
2. Incluir em `visualComponents.ts` com metadados de ciclo de vida (obrigatório)
3. Preferir demo interativa em `src/catalog/demos/{familia}.tsx` (senão o registry gera stub automático)

Helpers BEM, factories `create*`, tipos e constantes **não** entram no catálogo visual.

### Metadados no inventário (`visualComponents.ts`)

Datas declarativas (ISO `YYYY-MM-DD`) — **não** derivar de `git log` em runtime.

| Evento | Ação |
|--------|------|
| Novo export visual | `addedAt` = hoje; omitir `updatedAt` |
| Mudança relevante de API/visual | `updatedAt` = hoje; `changeNote` opcional (1 linha) |
| Só typo / docs / teste | **não** alterar `updatedAt` |

O app deriva badges **Novo** (≤ 30 dias desde `addedAt`) e **Atualizado** (não novo, `updatedAt` ≠ `addedAt`, ≤ 14 dias). Chips **Recentes** / **Atualizados** na sidebar filtramos por esse lifecycle.

## Convenções de código

| Tópico | Regra |
|--------|--------|
| Nome de arquivo | PascalCase: `HelpTooltip.tsx` |
| Export | Named exports; tipos `*Props` no mesmo arquivo |
| Ícones | `lucide-react` (peer dependency) |
| Textos ao usuário | **Proibido** no pacote — props `content`, `label`, `hint` |
| Acessibilidade | `aria-label`, `role="tooltip"`, foco no gatilho |
| Botões aninhados | Proibido — usar padrão irmão (`TabHintCell`) ou `wrap` em não-botão |

## Testes

```bash
cd plugins/plugin-ui
npm test
```

Mínimo para componente novo:

- Render sem crash
- Comportamento crítico (ex.: `wrap` vs trigger, `FieldLabel` com `htmlFor`)
- Demo no catálogo visual quando o export for público

## Integrar em um plugin consumidor

**Padrão atual (jul/2026):** Module Federation — ver [novo-plugin-mfe-checklist.md](../../docs/05-plugin-system/novo-plugin-mfe-checklist.md).

### 1. Vite + bootstrap

```ts
// vite.config.ts
remotes: pluginUiRemote(),
shared: { ...FEDERATION_SHARED_REACT },
```

```ts
// bootstrap.tsx — preparePluginUiRemote + import() dinâmico de App (ver module-federation.md)
import { preparePluginUiRemote } from "../../vite/federationShareScope";
await preparePluginUiRemote();
const { default: App } = await import("./App");
```

```ts
import { HelpTooltip } from "@delpi/plugin-ui/index";
```

### 2. Tokens no dashboard (sem CSS de chrome)

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--prefix-accent);
  --delpi-ui-surface: var(--prefix-surface);
  --delpi-ui-text: var(--prefix-text);
  --delpi-ui-border: var(--prefix-border);
  --delpi-ui-muted: var(--prefix-muted);
  --delpi-ui-card-padding: var(--prefix-card-padding);
  --delpi-ui-section-gap: var(--prefix-section-gap);
  --delpi-ui-grid-gap: var(--prefix-grid-gap);
}
```

**Proibido — em hipótese alguma** no `index.css` do MFE: qualquer CSS de componente deste pacote (KPI, card, filter bar, tabela, loading, section card, state box — inclusive BEM local dual-class). O remote entrega `.delpi-ui-*`. No MFE só tokens + layout de página + UI **fora** do kit.

Bug visual no componente → alterar `src/styles/*.css` (ou o TSX) **aqui**, não no consumidor. Rebuild: fase `remote` antes do MFE.

Ver [architecture.md](./architecture.md) § CSS e tema · regra Cursor `plugins-reusable-components.mdc` (zero CSS do kit no MFE).
### 3. Textos de ajuda

Criar `src/content/helpTooltips.ts` no plugin (padrão `assistant-content` / dashboards).

### 4. Remover duplicata local

Apagar `components/HelpTooltip.tsx` (ou equivalente) **e** CSS espelho (`*-help-tooltip*`, `*-kpi-card { padding… }`, etc.). Atualizar imports para `@delpi/plugin-ui` + `*BemClasses` / factory com dual-class.
## Checklist antes do merge

- [ ] Export documentado em `component-catalog.md`
- [ ] Entrada em `src/catalog/visualComponents.ts` (+ demo preferencial)
- [ ] Demo no catálogo visual (`src/catalog/`) ou stub aceito temporariamente
- [ ] Estilos `delpi-ui-*` sem vazar para `body` / `:root` global
- [ ] Consumidores **não** ganharam CSS espelho do chrome (só tokens + layout de página)
- [ ] `npm test` verde em `plugin-ui`
- [ ] `npm run build` verde em pelo menos um consumidor alterado
- [ ] `migration-catalog.md` atualizado
- [ ] Sem strings PT com pontuação no código do pacote

## Migrar cópia existente de HelpTooltip

Ver lista completa em [migration-catalog.md](./migration-catalog.md).

Passos típicos:

1. MF + `preparePluginUiRemote()` (não alias Vite de `plugin-ui` em prod)
2. Substituir `import { HelpTooltip } from "./HelpTooltip"` → `@delpi/plugin-ui`
3. Remover CSS duplicado do plugin (`*-help-tooltip*`, chrome de KPI/card se o kit cobre)
4. `FieldLabel`: passar `className` que o plugin já usa (`td-field__label`, `kz-field__label`, …)
5. Build + smoke visual claro/escuro no portal federado
6. Rebuild remote `plugin-ui` antes do MFE se alterou CSS do kit