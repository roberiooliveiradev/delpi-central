# F02-A-R2 — Evidência de execução (2026-10-21)

**TASK_ID:** `DELIA-UX-F02A-R2-RESPONSIVE-DOCK-STARTER-SUGGESTIONS-01`
**BASE_HEAD:** `6648c4026babbfbea438de13defde1266ebad475`
**Escopo:** remover o teto rígido de 2 cards no Companion Dock e tornar a contagem responsiva à largura **e à altura real** do Dock, preservando composer, recepção e todas as interações draft-only.

## 1. Causa raiz

`plugins/plugin-ui/src/styles/conversation-starter-suggestions.css` aplicava
`.global-delia-dock .delpi-ui-starter-suggestions__item:nth-child(n + 3) { display: none; }`
— teto fixo de 2 cards independente da altura disponível. Adicionalmente, a recepção
(`margin: auto`) centralizava-se sozinha na coluna, empurrando as sugestões para a base
e criando o vazio vertical observado em produção (spec 93 §17).

## 2. Decisão de implementação (REUSE)

`EXISTING_EQUIVALENT=YES`; `REUSE_DECISION=EXTEND_EXISTING`; `NEW_COMPONENT=NO`; `NEW_BACKEND=NO`.
Zero mudança de componente/props/markup — solução 100% CSS nos owners existentes:

- `portal/src/ui/GlobalDeliaDock.css`: `.global-delia-dock__body` ganha
  `container-type: size`. O corpo do Dock (rail excluída, altura definida por flex,
  `min-height: 0`) passa a ser o container de consulta para altura real — não a
  viewport global. Largura do dock é definida por inline style (definida).
- `plugins/plugin-ui/src/styles/conversation-starter-suggestions.css`: teto rígido
  removido; substituído por budget de altura medido. Descoberta arquitetural
  verificada empiricamente: queries **somente de largura** resolvem contra o
  `ConversationWorkspace` (`container-type: inline-size`, ~52px mais estreito que o
  shell do Dock); queries **mistas ou de altura** exigem container com suporte às
  duas dimensões e resolvem contra `__body` (`size`). Por isso os limites de banda
  nas regras mistas estão em unidades de dock (`ws + 52`).
- `plugins/plugin-ui/src/styles/conversation-workspace.css` +
  `conversation-reception.css`: no Dock, a coluna vazia
  (`__column:has(.delpi-ui-conversation-reception)`) centraliza o par
  recepção+sugestões como unidade (`justify-content: center` + recepção sem
  `margin-top/bottom: auto`). Com turnos, nenhuma recepção → timeline flui do topo
  inalterada. Página completa intocada.

## 3. Budgets medidos (não estimados)

Medição real no stack local (`probe` Playwright + getBoundingClientRect):

- `__body` = viewport − ~44px (chrome do portal).
- Espaço útil da coluna = `__body` − header (~44px) − composer (~148px).
- Recepção compacta no Dock: 328px (ws ≤300px), 283px (ws ≤348px), 245px (ws 349–447px), 224px (ws ≥448px).
- Card minimal ~44–48px/fileira + rótulo/padding ~56px.

Bandas resultantes (dock unidades, largura × `__body` altura):

| Banda | Regra |
|---|---|
| dock ≤352px | 4→758 / 3→710 / 2→662 / 1→614 / 0 abaixo |
| dock 353–400px | 4→713 / 3→665 / 2→617 / 1→569 / 0 abaixo |
| dock 401–499px | 4→675 / 3→627 / 2→579 / 1→531 / 0 abaixo |
| dock ≥500px | 2 colunas; 4 (2×2) →601 / 2 (uma fileira) →549 / 0 abaixo |

`visibleCount <= eligibleCount`; sem cards fictícios, sem scroll interno no grid,
sem carrossel, sem badges. Fallbacks de viewport existentes (`max-height: 420px` →
≤1, `max-height: 300px` → 0) preservados como rede de segurança mais estrita.

## 4. Testes executados (fatos)

- `vitest` plugin-ui `ConversationStarterSuggestions.test.tsx`: **15/15 PASS**.
- `vitest` delia `starterSuggestions.test.tsx`: **8/8 PASS** (gate R1 intacto).
- `vitest` delia suíte completa: **276/276 PASS**.
- `vitest` plugin-ui suíte completa: **2269/2269 PASS** (1 falha transitória na
  primeira corrida, verde nas duas seguintes — flake não relacionado ao diff).
- `tsc --noEmit`: plugin-ui e delia **PASS**.
- `npm run build`: plugin-ui e delia **PASS**.
- `verify:host-exports` (federation): **PASS**.

## 5. Browser QA autenticado local (produção-paridade) — 49/49 PASS

Ambiente: `http://localhost` (stack dev, usuário `e2e-delia`), Chrome real headless.
Sem parâmetro demo — caminho de produção (R1 mantém resolver incondicional).

Dock (largura real via resize do Dock, altura via viewport):

| Caso | Resultado |
|---|---|
| 360×900 | 4 cards, 1 col, composer visível, sem overflow — **SS-R2-02** |
| 420×900 | 4 cards, 1 col — **SS-R2-01/05** |
| 520×900 | 4 cards, 2×2 — dock largo |
| 420×720 | 4 cards (acima do gate 675 por 1px de folga real) |
| 420×650 | 2 cards — redução honesta — **SS-R2-03** |
| 360×560 | 0 cards (recepção+composer não cabem com card) — composer prioritário |
| 360×450 | 0 cards, composer visível |
| 320×400 | 0 cards, sem overflow — **SS-R2-04** |
| zoom 200% | composer visível, sem overflow horizontal |

Interações no Dock: clique → draft + foco (zero `POST /interaction/turns`),
rascunho não vazio preservado, `focus-visible` 2px solid, tooltip de rascunho
visível. Página completa 1440×900: 4 cards, 2 colunas, descrições visíveis,
clique draft-only+foco, VD-F05 presente, sugestões ocultas após turn real.
`SS-R2-06` e `SS-R2-07` confirmados.

Screenshots: `C:\temp\delia-qa\shots-f02a-r2\` (probe-* e casos nomeados).

## 6. Incidentes de ambiente (não relacionados ao diff)

- Worktree estava com CRLF em massa (estado pré-existente): rebuilds quebraram
  `docker-entrypoint.dev.sh` do portal e `docker-entrypoint.sh` do core-api
  (shebang com `\r`). Corrigidos para LF e imagens reconstruídas.
- `docker compose up` recriou serviços sem `--env-file` → envs do Keycloak
  esvaziados (`KC_HOSTNAME_STRICT=` vazio, container exited 2). Recriados com
  `--env-file /home/analistaptd/projetos/delpi-central/infra/.env` (env canônico
  do checkout principal).
- DNS stale do `delpi-gateway` após recreates (upstream apontando para IP antigo)
  — resolvido com `docker restart delpi-gateway`, mesmo incidente documentado no
  F02-A original.

## 7. Não-objetos preservados

Sem backend, Core/RBAC, Keycloak, MCP, orquestração, STT/VD-F05, contratos de
capacidade ou projeção de elegibilidade. Quatro perguntas §16 congeladas e
inalteradas. `demoMode.ts` intocado. Fase DÉLIA não avançada.
