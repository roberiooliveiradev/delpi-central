# 77 — DÉLIA: Conversation Workspace e Conversation Header compartilhados

**Status:** `IMPLEMENTED` — componentes existem em `plugins/plugin-ui` e são consumidos por `plugins/delia`. Nenhum backend, contrato de interação ou autorização foi alterado.
**Escopo:** shell conversacional reutilizável (workspace + header leve), integração na DÉLIA, comportamento full-page/dock, acessibilidade, light/dark e evidências.
**Reanchor:** HEAD de referência `2b0b1f54dc330992fda6068eae1ce21d11109cb0`; execução sempre verifica HEAD, status, WIP concorrente e a cadeia canônica de reanchor (Project Instructions → 16 → 50 → 17 → 49 → 51 → 52 → 21 → 20 → 25 → specs temáticas → ledger).
**Referências:** [69 — experiência conversacional](./69-conversation-experience-ux-wireframes-and-activity-plan.md), [70 — atividade](./70-tool-activity-and-source-transparency-ux-specification.md), [73 — identidade chat-first](./73-chat-first-visual-identity-and-message-anatomy-specification.md), [74 — composer](./74-message-composer-visual-specification.md), [76 — avatares](./76-unified-avatar-delia-motion-and-user-profile-visual-specification.md).

## 1. Problema resolvido

O shell da DÉLIA dependia de CSS local para estrutura essencial (altura total do host, coluna de leitura centrada, footer ancorado). O objetivo é mover a anatomia genérica para `plugin-ui` sem carregar estado de produto:

```text
ConversationWorkspace (plugin-ui — layout apenas)
 ├── header   (slot — ConversationHeader ou equivalente)
 ├── banner   (slot opcional, p.ex. demo-mode)
 ├── body     (viewport rolável + coluna de leitura)
 └── footer   (slot ancorado — composer, erro, helper)
```

## 2. Reuse gate — inventário executado

| Candidato | EVIDENT_EQUIVALENT | Decisão | Motivo |
|---|---|---|---|
| `RoomConversationChatColumn` / `room-thread` (portal rooms) | PARTIAL | NEW | mesma anatomia (stage + msgs rolável + dock ancorado), mas acoplado a rooms, file-drop e contrato de tópicos; reutilizar implicaria importar semântica de outro bounded context |
| `PageHeader` (plugin-ui) | PARTIAL | NEW | chrome administrativo (breadcrumb, ações de página); linguagem errada para chrome conversacional leve |
| `PageHero` | NO | — | bloco de destaque editorial, não header de superfície |
| `ResizableColumns` / `Section` | NO | — | primitivos de layout de página, não shell de conversa |
| `ConversationWorkspace` | — | NEW | composição nova sobre tokens existentes; sem duplicar primitivos |
| `ConversationHeader` | — | NEW | chrome leve; não estende `PageHeader` porque o contrato visual é diferente (sem breadcrumb, título compacto, ações opcionais) |

## 3. Responsabilidades

`ConversationWorkspace` é **layout, não runtime**. Possui apenas: altura oferecida pelo host (nunca `100vh` próprio), `min-height: 0`, viewport rolável único no body, coluna de leitura centrada (`--delpi-ui-conversation-column`), footer ancorado por flex (sem `position: fixed`), densidade `comfortable|compact`, slots e `ariaLabel` configurável. **Não** possui: estado de conversa, turns, API, loading, auth, contratos, seleção de capability, semântica de atividade, identidade ou confirmação.

`ConversationHeader` é **chrome, não autoridade**. Possui: título (hierarquia configurável via `titleAs`, evita H1 duplicado), subtítulo/contexto opcional, leading (identidade/ícone) e actions opcionais, modo compacto, truncamento responsivo. **Não** possui: navegação, auth, estado de sessão, histórico, status online fictício, nome de provider/modelo, IDs internos de sessão.

## 4. API implementada

```ts
type ConversationWorkspaceProps = {
  header?: ReactNode;
  banner?: ReactNode;
  children: ReactNode;           // body rolável
  footer?: ReactNode;
  bodyRef?: Ref<HTMLDivElement>; // viewport p/ autoscroll do consumidor
  className?: string;
  columnClassName?: string;
  ariaLabel?: string;
  density?: "comfortable" | "compact";
};

type ConversationHeaderProps = {
  title: ReactNode;
  subtitle?: ReactNode;
  leading?: ReactNode;
  actions?: ReactNode;
  titleAs?: "h1" | "h2" | "h3" | "div";
  compact?: boolean;
  className?: string;
};
```

`bodyRef` é o contrato mínimo de scroll: a DÉLIA usa o nó real do viewport para o cálculo near-bottom existente; o plugin-ui não esconde mecânica de scroll que o consumidor precisa observar.

## 5. Arquivos

Criados em `plugins/plugin-ui`:

- `src/components/conversation/ConversationWorkspace.tsx`
- `src/components/conversation/ConversationHeader.tsx`
- `src/components/conversation/index.ts`
- `src/components/conversation/ConversationWorkspace.test.tsx`
- `src/components/conversation/ConversationHeader.test.tsx`
- `src/styles/conversation-workspace.css` (importado por `src/styles.css`)

Registro público: exports em `src/index.ts`, entradas no catálogo (`visualComponents.ts`, família `collaboration`), demos em `catalog/demos/collaboration.tsx`, símbolos `ConversationWorkspace`/`ConversationHeader` adicionados à allowlist `scripts/verify-host-exports.mjs`.

Integração DÉLIA (`plugins/delia/src/App.tsx`): workspace compartilhado recebe `ConversationHeader` ("DÉLIA" / "Inteligência operacional DELPI"), banner de demo, reception/timeline no body e erro + `DeliaComposer` no footer. CSS local de scaffolding genérico foi removido; permanecem estilos de produto (reception, timeline, mensagens, confirmação, branding).

## 6. Comportamento responsivo e estados

- **Empty:** header + reception centrada + composer estável.
- **Active:** timeline ocupa o topo da coluna de leitura; sem centralização vertical de turns; `ActivityViewer` de pending dentro do body após a timeline.
- **Dock/narrow (container queries):** mesma estrutura; subtítulo pode ocultar; coluna = 100% - padding seguro; sem overflow horizontal.
- **Loading/erro:** erro permanece no footer acima do composer; pending no body; composer nunca some.
- **Zoom 200% / mobile 320–480px:** flex + tokens, sem larguras fixas além da coluna com `clamp`/token.
- **Motion:** apenas transições sutis de presença; `prefers-reduced-motion` respeitado no CSS do workspace.

## 7. Acessibilidade

- `ariaLabel` configurável no workspace (sem landmark duplicado); `titleAs` evita múltiplos `<h1>` com o Portal; body é rolável por teclado naturalmente; sem focus trap nem foco forçado.
- `ActivityViewer` mantém `role=status` existente; nenhuma mudança de semântica.

## 8. Segurança e privacidade

Nenhuma mudança em `getAccessToken`, permissões, contrato de interação, payload ou identidade. Sem `localStorage`/`sessionStorage`, sem parse de JWT, sem novo endpoint.

## 9. Anti-patterns (FORBIDDEN)

- Colocar estado de conversa/API/auth dentro de `ConversationWorkspace`.
- Usar `ConversationWorkspace` como card com bordas/padding pesados.
- `position: fixed` para o composer; `100vh` como altura do shell.
- `ConversationHeader` com breadcrumb, model picker, fake online status ou ações não contratadas.
- Duplicar `PageHeader` administrativo dentro do workspace.

## 10. Evidência de implementação

- Testes plugin-ui conversation: 10/10 (slots, ref de viewport, densidade, heading levels, regiões opcionais).
- Suite DÉLIA: 149/149 (reception, timeline, composer ancorado, erro, pending, autoscroll, identidade — sem mudança de contrato).
- Builds: `plugin-ui` e `delia` PASS; `verify-federation` PASS; `verify-host-exports` PASS com os dois símbolos novos.
- Typecheck: DÉLIA clean; plugin-ui mantém apenas erros pré-existentes de `visualComponents.ts` (entradas legadas sem `addedAt`, fora deste diff).
- Residuals pré-existentes no suite plugin-ui: `componentRegistry`, `MentionComposer`, `ModalShell` (3), `SignatureCapturePanel`, `SignaturePad` — não relacionados.
- Visual QA em browser: `TEST_NOT_RUN` nesta execução (ambiente sem preview); jsdom não substitui evidência visual — reagendar QA de página completa/dock/light/dark/narrow/zoom/reduced-motion.
