# Portal UI kit

Biblioteca de componentes do **shell do portal** (Admin, home, auth).

- Prefixo CSS: `.portal-ui-*` (não vaza para MFEs).
- Tokens: variáveis de [`../index.css`](../index.css) — ver [`tokens.md`](./tokens.md).
- **Não** importar `@delpi/plugin-ui` aqui (Federation / dual-class dos plugins).

## Uso

```ts
import { Button, FormField, Input, PageChrome } from "../ui-kit";
```

## Catálogo v1

| Componente | Quando usar |
|------------|-------------|
| `Button` | Ações primárias/secundárias/perigo/ghost/link. `danger-soft` para exclusão em linha de tabela ou card; `danger` para confirmação explícita; `pressed` para filtro/ordenação ativos |
| `Badge` | Contagens, status, “Obrigatório” visual |
| `Alert` | Feedback inline (erro API, aviso estrutural) |
| `Spinner` | Loading de página/seção |
| `Tabs` | Abas de editor Admin |
| `SegmentedControl` | Alternância binária (Form \| JSON) |
| `Breadcrumb` | Navegação hierárquica |
| `PageChrome` | Header sticky + body + footer de páginas Admin |
| `FormField` / `FormGrid` | Label + erro + layout de formulário |
| `Input` / `Textarea` / `Select` / `MultiSelect` | Controles de formulário |
| `AnchoredPanel` | Painel flutuante preso a um gatilho (base de `Select` / `MultiSelect`) |
| `Checkbox` / `RadioGroup` / `Radio` / `Switch` / `SearchInput` | Booleanos e busca (`Radio` avulso só para linha de tabela) |
| `DenseTable` | Tabelas editáveis densas (permissões/rotas) |

## Botão de alternância (`pressed`)

Filtros e ordenação usam `<Button pressed>` em vez de `variant="primary"`: o estado
ligado vira um tint da cor primária com `aria-pressed`, sem competir com a ação
primária da tela.

```tsx
<Button size="sm" pressed={filtro === "online"} onClick={() => setFiltro("online")}>
  Online
</Button>
```

## Fora do kit

Subsistemas com identidade visual própria continuam com markup e CSS locais:
`Sidebar` / `PortalMobileNavBar` (navegação do shell), `tour/*` (gamificação),
hero da home e o CTA de login, `AppLauncherCard` e demais cards clicáveis.
`RelationshipPicker`, `AppGroupedPermissionPicker`, `AppLauncher` e `IconPicker`
seguem sendo componentes de domínio, mas seus **controles** já usam o kit.

## Select

Segue o `SelectControl` do `@delpi/plugin-ui` (`.delpi-ui-select`): gatilho `<button>`
com `role="combobox"`, painel próprio com `role="listbox"`, chevron que gira ao abrir,
busca automática a partir de 8 opções e navegação por teclado (setas, Home/End, Enter,
Esc, Tab). Não é `<select>` nativo — por isso a lista respeita o tema em qualquer SO.

```tsx
<Select value={tipo} onChange={setTipo} options={opcoes} />
```

`onChange` recebe **o valor** (`string`), não o evento — mesma assinatura do
`NativeSelectControl` do plugin-ui. O painel é renderizado no `body` via
`AnchoredPanel`, então funciona dentro de `DenseTable` e modais com `overflow: auto`.

## Alinhamento e convivência com CSS legado

- `Button` (`sm` 32 px / `md` 36 px / `lg` 40 px) tem a **mesma altura** de `Input`,
  `Select` e `SearchInput`, então botão e campo lado a lado ficam alinhados.
- Ícone dentro de `children` funciona porque `.portal-ui-btn__label` é `inline-flex`
  (o `svg { display: block }` global quebraria a linha). Ainda assim, prefira a prop
  `icon`; sem `children` o botão vira quadrado (`--icon-only`).
- Abaixo de 720px o `PageChrome` deixa de ser sticky e as ações do topo viram uma faixa
  rolável na horizontal: um cabeçalho fixo com título, botões e abas ocupava metade da
  tela num iPhone SE. Painéis que esticam no desktop devem voltar a `flex: 0 0 auto` no
  celular, senão o conteúdo fica espremido em vez de rolar.
- `PageChrome` preenche a altura da área de conteúdo: `.content > .portal-ui-page` cresce
  no flex do shell. Painéis que devem ocupar o resto da página (pickers, editor JSON) usam
  `flex: 1 1 auto` — evite `height: 48vh` e afins, que ignoram a altura real disponível.
- Nessa cadeia use `flex-shrink: 0` (`flex: 1 0 auto`) no elemento da página e no corpo:
  encolhendo, o corpo fica menor que o conteúdo, o formulário transborda e o rodapé
  sticky aparece flutuando no meio da página.
- `Tabs` aceita `icon` e `dataTour` por item: é o mesmo componente usado no cabeçalho do
  editor de manifesto e na navegação principal do Admin, que precisa de ícones e de
  âncoras do tour guiado.
- CSS antigo que estilizava `container button` / `container input` foi escopado com
  `:where(:not(.portal-ui-btn))` / `:where(:not(.portal-ui-control))`. **Ao criar regra
  nova por tipo de elemento, faça o mesmo** — caso contrário ela vence o kit por
  especificidade.
- O `:where()` é obrigatório: `button:not(.portal-ui-btn)` vale uma classe e passaria a
  vencer regras de página como `.collapse-btn`, quebrando sidebar, launcher e cards.
  `:where()` zera essa contribuição e preserva a cascata original.
- Regras de descendente como `.meu-header span { display: block }` venciam
  `.portal-ui-btn__label`. As partes internas do botão usam dupla classe
  (`.portal-ui-btn .portal-ui-btn__label`) para resistir a isso; ainda assim,
  prefira seletor de filho direto (`> div > span`) no CSS de página.

## Migração

1. Preferir `ui-kit` em páginas novas.
2. `components/FormField` reexporta o kit.
3. Classes legadas `.btn-primary` / `.btn-secondary` em `Modal.css` ficam deprecated — usar `Button`.
