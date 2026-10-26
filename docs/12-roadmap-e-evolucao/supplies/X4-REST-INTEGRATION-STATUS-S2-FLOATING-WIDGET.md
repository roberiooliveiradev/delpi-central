# X4.REST-STATUS.S2 — Widget flutuante do diagnóstico REST de fornecedores

**Data:** 2026-10-26 · **Task:** `X4.REST-STATUS.S2` · **Owner:**
`plugins/supplies` (MFE apenas) · **Base:** S1 (`d86d49ac20` / `f53d9cf34b`).

## 1. Problema

O card S1 era flutuante apenas em viewport ≥1024px e oferecia apenas
expandir/recolher — sem estado fechado e sem acionador de reabertura. Nas
capturas do PO, o painel ocupava espaço fixo e não havia como removê-lo sem
perder o acesso ao diagnóstico.

## 2. Solução — máquina de estados única

```text
closed  →(reabrir)→  collapsed  →(expandir)→  expanded
                      collapsed  →(fechar)→    closed
                      expanded   →(recolher)→  collapsed
                      expanded   →(fechar)→    closed
```

Estado inicial: `collapsed`. O último resultado e a última view ficam em
cache de módulo (`lastStatus`/`lastView`), compartilhado entre a lista e a
ficha — navegar entre páginas não refaz a verificação REST nem reabre o
painel fechado. Nenhuma persistência global nova foi criada.

- **collapsed:** barra compacta — dot de status + título + resumo (badge) +
  `⌃` expandir + `×` fechar.
- **expanded:** detalhes completos (configuração, conectividade,
  autenticação, consulta, gates POST/PUT, guard, gravação não testada,
  ambiente, timestamp) + «Verificar novamente». O painel cresce para cima
  (ancorado em `bottom`), sem deslocar o conteúdo da página.
- **closed:** o widget some; um FAB discreto (ícone `Activity`,
  lucide-react — kit já federado) com tooltip «Abrir diagnóstico da
  integração Protheus» restaura para `collapsed`.

Alternar de view **nunca** dispara chamada REST — a única chamada continua
sendo «Verificar integração», manual e idempotente. Nenhum POST/PUT.

## 3. Posicionamento

- `position: fixed` no canto inferior direito em **todas** as viewports,
  com `env(safe-area-inset-bottom)`.
- `z-index: 30` — abaixo de modais/overlays oficiais do kit (1200) e do
  controle flutuante de IA.
- Largura `min(380px, 100vw − 2×padding)`; no expanded, `max-height:
  min(55dvh, 480px)` com rolagem apenas do conteúdo interno.

## 4. Acessibilidade

- Botões reais para expandir (`⌃`, `aria-expanded` + `aria-controls`),
  recolher (`⌄`) e fechar (`×`), todos com `aria-label`/`title`.
- `Escape` recolhe somente quando expandido.
- Ao fechar, o foco é devolvido ao FAB de reabertura (nunca fica em
  elemento oculto).
- `aria-live="polite"` reservado ao resumo/timestamp do diagnóstico.
- `prefers-reduced-motion`: transições desabilitadas; nenhuma animação.

## 5. Escopo

Apenas `plugins/supplies`: componente, CSS isolado
(`.dashboard-supplies-portal`), `content.ts`, Help/Manual, teste
estrutural. **Zero** alteração em `api-delpi`, `supplies-api`, contratos,
RBAC, flags ou parâmetros.

## 6. Testes

Suíte estrutural ampliada para 13 testes — novos casos: máquina de
estados, posicionamento fixed/z-index/safe-area, close/reopen sem refetch,
cache compartilhado lista↔ficha, FAB com tooltip e ícone do kit, Escape,
foco devolvido, `prefers-reduced-motion`. Regressão MFE: **476/476**.

## 7. Evidências e deploy

- `tsc -b` limpo; `npm run build` ok; eslint 0 erros; `git diff --check`
  limpo.
- Deploy canônico: `up-prod-sequential.sh --build supplies`.
- Smoke autenticado: `INCONCLUSIVE` (sem sessão autenticada disponível).

## 8. Residuais

- Estado do widget é por sessão/aba (cache de módulo) — F5 volta a
  `collapsed`, por design.
- Resultado do diagnóstico não persiste entre recarregamentos — a
  verificação é sempre explícita.
