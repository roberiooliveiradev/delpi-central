# Workspace Controls — pacote público reutilizável do Plugin UI

**Estado:** Implementação de código versionada no GitHub; testes/build/Verify/consumo em runtime ainda exigem execução no ambiente do repositório.  
**Owner:** `@delpi/plugin-ui`. **Scope:** apresentação genérica para ferramentas e páginas; não contém métodos industriais, roteamento, API, autorização, estado de estudo ou persistência.

## Como importar

```tsx
import {
  NavigationCard, navigationCardBemClasses,
  CollapsibleToolRail, SegmentToggle, NumberStepperControl,
  ActionButton, IconButton, ModernSelectControl, NativeTextControl,
  DataTable, SectionCard, SimpleKpiCard, StateBox, StatusBadge,
  StackedColumnChart,
} from "@delpi/plugin-ui/workspace-controls";
```

O CSS **fechado do conjunto** é `@delpi/plugin-ui/workspace-controls.css`. Um MFE sem Shadow DOM importa essa folha **uma vez** no stylesheet do consumer:

```css
@import "@delpi/plugin-ui/workspace-controls.css";
```

Em um Custom Element com Shadow DOM, **processar e injetar o CSS dentro do shadow root** pelo pipeline validado de `?inline`/styles, não apenas no documento pai. A resolução `?inline` é responsabilidade do bundler do consumidor, e deve ser comprovada por screenshot e computed styles.

O pacote possui subpath público em `package.json` e um expose próprio `./workspace-controls` no remote do Plugin UI. Não depender de imports relativos de `components/**` na aplicação.

## O que ele organiza

| Camada | Componentes |
|---|---|
| Origem / opções principais | `NavigationCard` com `density="featured"` e `selected` opcional |
| Ferramentas e métodos | `CollapsibleToolRail` com itens, ícones, grupos, labels e status genéricos |
| Ações e entradas | `ActionButton`, `IconButton`, `NativeTextControl`, `ModernSelectControl`, `NumberStepperControl`, `SegmentToggle` |
| Corpo e feedback | `SectionCard`, `DataTable`, `SimpleKpiCard`, `StateBox`, `StatusBadge`, `StackedColumnChart` |
| Ajuda contextual | `HelpTooltip`, `HintAction`, `FieldLabel`, `SectionHintLabel`, `TitleWithHelp`, `TabHintCell`, `KeyTip` — genéricos, sem texto de domínio (ver família `help` na doc do pacote principal) |

### Exemplo de sidebar genérica

```tsx
const groups = [
  {
    id: "operations",
    label: "Ferramentas",
    items: [
      { id: "inspect", label: "Inspecionar", icon: <Search size={18} /> },
      { id: "compare", label: "Comparar", icon: <GitCompare size={18} /> },
    ],
  },
  {
    id: "future",
    label: "Próximas ferramentas",
    collapsible: true,
    defaultOpen: false,
    items: [{ id: "future-a", label: "Futura", icon: <Clock3 size={18} />, disabled: true, statusText: "Planejado" }],
  },
];

<CollapsibleToolRail
  groups={groups}
  expanded={expanded}
  activeId={activeId}
  onExpandedChange={setExpanded}
  onSelect={setActiveId}
  ariaLabel="Ferramentas de análise"
/>;
```

A variável `expanded` pertence ao consumer. O componente não sabe o que é método de balanceamento, não interpreta status como permissão e não persiste dados.

### Exemplo de dois cards destacados

```tsx
const classNames = navigationCardBemClasses("my-workspace");

<NavigationCard
  classNames={classNames}
  density="featured"
  title="Origem oficial"
  description="Consultar dados autorizados"
  icon={<PackageSearch size={28} />}
  selected={source === "official"}
  onClick={() => setSource("official")}
/>;
```

`selected` é aditivo e opcional; consumidores que usam `NavigationCard` como link/ação comum não recebem `aria-pressed` automaticamente.

## Requisitos técnicos e riscos

- `CollapsibleToolRail` controlado, sem estado de autorização ou navegação; gruppos recolhíveis têm estado local de apresentação.
- Labels acessíveis permanecem nos itens com ícones, incluindo atributo `title` para foco/hover básico; `ToolRailItem.description` (opcional) compõe esse `title` após `label` e `statusText`. Grupos com itens desabilitados não executam ações.
- O item ativo do rail usa `color-mix(accent 55%, text)` — mantém a identidade azul com contraste AA nos temas claro e escuro; o gatilho da família help usa `--delpi-ui-text-muted` opaco pelo mesmo motivo.
- Componente não implementa drawer mobile ou trap de foco; o modo compacto cabe no viewport, mas um consumer que exija drawer deve usar um drawer genérico aprovado, com foco e escape testados. Não declarar drawer funcional.
- `NumberStepperControl` e `SegmentToggle` são exports do kit geral, não inventados para este conjunto.
- Na importação MF, verificar export presente em remote e versão de CSS acoplada ao código; não alegar compatibilidade apenas porque o Typescript compila.
- Conferir temas claro/escuro, 1440/1024/390/320, focus, keyboard e computedStyle no Shadow DOM e fora dele.
- Release de código exige testes unitários, import contract, build do Plugin UI, Verify independente e integração progressiva. Sem resultado desses gates, estado permanece `IMPLEMENTED_IN_GITHUB / TEST_NOT_RUN`.

## Plano de consumo

1. **Plugin UI:** validar código, build e testes do conjunto.
2. **DELPI Line Balance Studio:** importar subpath, mapear M1–M6 no Studio (não no kit) e construir os dois cards grandes com dados do estudo.
3. **Portal Engenharia:** consumir **o Studio pronto**, não montar a sidebar novamente no MFE; preservar AuthZ, rotas e origem de dados.
4. Validar visual com a demo aprovada de GitHub Pages em paralelo a HML antes de produção.

Ver também o [inventário de UX V4](../../delpi-line-balance-studio/docs/plugin-ui-v4-component-inventory.md).
