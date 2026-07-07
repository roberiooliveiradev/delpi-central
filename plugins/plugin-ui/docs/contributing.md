# Como contribuir — `@delpi/plugin-ui`

## Antes de adicionar um componente

1. O componente será usado em **pelo menos dois plugins**, ou substitui **cópias já duplicadas** no monorepo?
2. Não acopla domínio (sem strings PT fixas, sem chamadas HTTP, sem rotas)?
3. Estilos usam prefixo `delpi-ui-*` e tokens CSS documentados?
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
7. Migrar um segundo consumidor ou remover duplicata local
8. Atualizar migration-catalog.md

### Plugin com `Dockerfile` que importa biblioteca irmã

1. Registrar markers em `plugins/shared-libraries.manifest.json` (se biblioteca nova).
2. Adicionar `COPY <biblioteca>/` no Dockerfile — ver `plugins/docker/shared-libraries.Dockerfile.fragment`.
3. Garantir `context: ../plugins` no `infra/docker-compose*.yml`.
4. Rodar `python3 scripts/ci/check_plugin_docker_shared_libraries.py --check`.
```

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

## Integrar em um plugin consumidor

### 1. Alias Vite

```ts
import path from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@delpi/plugin-ui": path.resolve(__dirname, "../plugin-ui/src/index.ts"),
    },
    dedupe: ["react", "react-dom"],
  },
});
```

### 2. CSS

```ts
// src/main.tsx (ajuste o caminho relativo)
import "../../plugin-ui/src/styles.css";
```

### 3. Tokens no dashboard

```css
.dashboard-meu-plugin {
  --delpi-ui-accent: var(--prefix-accent);
  --delpi-ui-surface: var(--prefix-surface);
  --delpi-ui-text: var(--prefix-text);
  --delpi-ui-border: var(--prefix-border);
  --delpi-ui-muted: var(--prefix-muted);
}
```

### 4. Textos de ajuda

Criar `src/content/helpTooltips.ts` no plugin (padrão `assistant-content` / dashboards).

### 5. Remover duplicata local

Apagar `components/HelpTooltip.tsx` (ou equivalente) e atualizar imports para `@delpi/plugin-ui`.

## Checklist antes do merge

- [ ] Export documentado em `component-catalog.md`
- [ ] Estilos `delpi-ui-*` sem vazar para `body` / `:root` global
- [ ] `npm test` verde em `plugin-ui`
- [ ] `npm run build` verde em pelo menos um consumidor alterado
- [ ] `migration-catalog.md` atualizado
- [ ] Sem strings PT com pontuação no código do pacote

## Migrar cópia existente de HelpTooltip

Ver lista completa em [migration-catalog.md](./migration-catalog.md).

Passos típicos:

1. Adicionar alias + import CSS no plugin
2. Substituir `import { HelpTooltip } from "./HelpTooltip"` → `@delpi/plugin-ui`
3. Trocar classes `kz-help-tooltip` / `lmps-help-tooltip` por tokens `--delpi-ui-*` (remover CSS duplicado do plugin)
4. `FieldLabel`: passar `className` que o plugin já usa (`td-field__label`, `kz-field__label`, …)
5. Build + smoke visual claro/escuro no portal federado
