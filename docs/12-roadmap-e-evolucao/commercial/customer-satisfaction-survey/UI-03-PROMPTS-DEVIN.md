# UI-03 — Pedidos de execução para o Devin (pacotes)

> **Estado:** registro vivo dos pedidos de execução do [plano da UI-03](./UI-03-PLANO-IMPLEMENTACAO.md). Um pacote por vez: o próximo só é gerado depois que o anterior for **verificado e aceito** pelo solicitante.
> **Como usar:** o solicitante cola no Devin o **mini prompt** do pacote (fornecido no chat do projeto). O mini prompt manda o Devin ler este arquivo, aplicar o **Protocolo comum (§1)** e executar **somente** o pacote indicado.

## Situação dos pacotes

| Pacote | Fases do plano | Conteúdo | Deploy | Estado |
|---|---|---|---|---|
| **P1** | 0 + 1 | Inventário, tokens claro/escuro, controle de tema, layout da página, demos no catálogo | PluginUI: DEV → **PROD** (componentes genéricos) | **ACEITO COM RESÍDUOS** — commit `7abe0b338b`, deploy PROD e HML em 16/11/2026 (ver §3) |
| **P2** | 2 | Cartão base, abertura, cabeçalho, progresso, logo, botão de tema, quadro da pergunta + resíduos R1/R2 do P1 | PluginUI → PROD | **ACEITO COM RESÍDUOS** — commit `78f11fbd03`, deploy PROD e HML em 16–17/11/2026 (ver §5) |
| **P3** | 3 | Escala de notas (1–5 e 0–10), “Não se aplica”, texto aberto | PluginUI → PROD | **ACEITO COM RESÍDUOS** — commit `f75d2385fe`, deploy PROD e HML em 17/11/2026; R8 obrigatório no P4 (ver §7) |
| **P4** | 4 | Correção R8 + botões, rodapé de ações, aviso, revisão e tela de resultado | PluginUI → PROD | **PRONTO PARA EXECUÇÃO** (§8) |
| P5 | 5 | Formulário guiado completo (com perguntas de exemplo, não as da Pesquisa) | PluginUI → PROD | A gerar |
| P6 | 7 | Página pública nova da Pesquisa no `public-hub` | **Somente HML** | A gerar |
| P7 | 8 | Correções da homologação | Conforme a camada alterada | A gerar |

## 1. Protocolo comum (vale para todo pacote)

### 1.1 Reancoragem obrigatória — antes de qualquer alteração

1. `git rev-parse HEAD`, `git branch --show-current`, `git status --short`, `git worktree list`; confirmar que está em `main`, atualizar com `git pull --ff-only` e registrar o HEAD inicial. Não trocar nem criar branch/worktree (`AGENTS.md`, Regras 1–10).
2. Ler, nesta ordem: `AGENTS.md` (raiz); `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`; `.cursor/rules/development-standards-index.mdc`; `.cursor/rules/evidence-driven-execution.mdc`; `.cursor/rules/test-and-commit.mdc`; `.cursor/rules/plugins-reusable-components.mdc`; `.cursor/rules/plugins-visual-design-system.mdc`; `.cursor/rules/plugins-frontend-build.mdc`.
3. Ler a especificação: [UI-03-FORMULARIO-PUBLICO.md](./UI-03-FORMULARIO-PUBLICO.md) (§3 visual e tokens, §4 regras, §5 kit), [UI-03-PLANO-IMPLEMENTACAO.md](./UI-03-PLANO-IMPLEMENTACAO.md), [referência visual](./UI-03-REFERENCIA-VISUAL.html) e [BUSINESS-DECISIONS Q21–Q23](./BUSINESS-DECISIONS.md#f-experiência-visual).
4. Ler o padrão do kit: `plugins/plugin-ui/docs/contributing.md`, `component-catalog.md`, `module-federation.md`, `architecture.md`; `src/utils/delpiUiClass.ts`; um componente de referência (`src/components/forms/SegmentToggle.tsx` + teste + CSS); `src/catalog/visualComponents.ts`, `src/catalog/componentRegistry.tsx`, `src/catalog/demos/forms.tsx`.
5. Ler a seção do pacote neste arquivo e **declarar** antes de codificar: objetivo, arquivos que vai criar/alterar, invariantes e testes.

### 1.2 Regras de execução

- **Menor diff correto.** Só os arquivos do escopo do pacote. Proibido refatorar código não relacionado, mudar componentes existentes do kit (salvo o que o pacote pedir) ou formatar arquivos inteiros.
- **Kit genérico:** nenhum texto, chave, rota ou regra da Pesquisa de Satisfação dentro do PluginUI; **sem strings em português fixas** nos componentes (`contributing.md`): textos entram por propriedade. Textos de exemplo só nas demos do catálogo.
- **CSS só no PluginUI** (`plugins/plugin-ui/src/styles/`), classes `prefixo` + `.delpi-ui-form-*` via `delpiUiClass`. **Proibido** seletor global (`:root`, `html`, `body`, `*`) no CSS do kit e qualquer CSS de componente em MFE/app.
- **Sem persistência no navegador** em nada do formulário (`localStorage`, `sessionStorage`, IndexedDB, cookie, URL).
- **Acessibilidade e temas** fazem parte do aceite: testar claro e escuro e os contrastes da UI-03 §3.2.
- Se algo da especificação for inviável ou contraditório com o código real: **parar e reportar** (veredito `DECISION_REQUIRED`), sem inventar alternativa.

### 1.3 Verificação

1. Rodar: `npm test --prefix plugins/plugin-ui`; `npm run build --prefix plugins/plugin-ui` (inclui `verify-host-exports`); `python3 scripts/ci/audit_platform_guardrails.py --check --base <HEAD inicial>`; `python3 scripts/ci/audit_mfe_plugin_ui_css.py`; `python3 scripts/ci/audit_plugin_ui_duplication.py --check`; se tocar `public-hub`, `npm run ci --prefix plugins/public-hub`; se tocar docs, `python3 scripts/audit_documentation_structure.py`.
2. **Verificador independente** (`AGENTS.md` §Verificação, parte A de `agent-kit/verifier/project-contract.md`): gravar o `PEDIDO DE VERIFICAÇÃO` em `<git-dir>/delpi-verifier/requests/` (nunca no working tree), com objetivo, IDs do pacote e critérios de aceite, escopo `working tree` ou `base..head`, alegações e modelo do executor; rodar `python ~/.delpi-agent-kit/verify.py --request-file <arquivo>`. Corrigir cada ordem de correção no código de produção (nunca alterar teste/limite para passar); no máximo 3 rodadas. `DECISION_REQUIRED` ou `EXECUTION_DRIFT` **encerram** o pacote e voltam ao solicitante.

### 1.4 Commit, push e deploy

- Commit **só** com os arquivos do pacote, mensagem em português no padrão do repositório, push direto em `main` (fast-forward; se `origin/main` avançou, `fetch` + `rebase` e revalidar).
- **Pacotes P1–P5 (kit genérico no PluginUI):** após verificação aprovada, deploy canônico em `srv-api` (`operador@192.168.1.237`, `~/projetos/delpi-central`): `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build plugin-ui`. Também atualizar HML (`/home/operador/projetos-teste/delpi-central`: `git pull --ff-only` + `./infra/scripts/up-hml-sequential.sh --build plugin-ui`). O solicitante acompanha no catálogo do PluginUI no Portal (`/apps/plugin-ui`). Esses pacotes **não** contêm nada da Pesquisa, por isso seguem a regra geral de deploy.
- **Pacote P6 em diante (página pública da Pesquisa):** **somente HML.** Proibido deploy em PROD do `public-hub` com a página da Pesquisa, conforme a exceção do `AGENTS.md` e o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026). Se um deploy de PROD de outro serviço puder expor a Pesquisa, parar e reportar.
- Após o deploy: conferir que o container subiu, que o remote do PluginUI carrega e que o catálogo abre sem erro no console; conferir um MFE existente que usa o PluginUI (regressão).

### 1.5 Relatório final (EXECUTION REPORT)

HEAD inicial e final · commits · arquivos criados/alterados · o que foi entregue × critérios de aceite (um por linha, com evidência) · testes e auditorias executados com resultado · veredito do verificador **sem edição** e tabela de rodadas · deploy executado (ambiente, comando, resultado) · onde ver no catálogo · riscos, desvios e pendências.

---

## 2. Pacote P1 — Fundação do kit: inventário, tokens, tema e layout

**Fases do plano:** 0 e 1. **Pré-requisito:** nenhum.

### 2.1 Objetivo

Criar a base do kit de formulário no PluginUI: os **tokens dos temas claro e escuro**, o **controle de tema por visita** e o **layout da página** (faixa da marca + coluna), visíveis no catálogo do PluginUI. Nenhum componente de pergunta ainda.

### 2.2 Fase 0 dentro do pacote (sem código)

- Confirmar como o remote do PluginUI é publicado em DEV/HML/PROD e quais MFEs o consomem (risco de regressão) — registrar no relatório.
- Investigar por que `GET /p/logoMinhaDelpi.svg` respondeu **403** em HML em 16/11/2026 (`plugins/public-hub/nginx.conf`, gateway, permissões no container) — **somente diagnóstico**, sem corrigir neste pacote; registrar causa provável e correção sugerida.
- Confirmar que os nomes propostos não colidem com exports existentes.

### 2.3 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/forms/questionnaire/` (nova pasta) | `QuestionnaireThemeScope.tsx`, `useSessionColorScheme.ts`, `FormPageLayout.tsx`, `index.ts` e testes `*.test.tsx`/`*.test.ts` |
| `plugins/plugin-ui/src/styles/questionnaire.css` (novo) | Tokens e estilos da raiz e do layout |
| `plugins/plugin-ui/src/styles.css` | **Uma** linha de `@import` do novo CSS |
| `plugins/plugin-ui/src/components/forms/index.ts` e `src/index.ts` | Exportar os novos itens |
| `plugins/plugin-ui/src/catalog/visualComponents.ts`, `src/catalog/componentRegistry.tsx` e `src/catalog/demos/forms.tsx` (ou novo `demos/questionnaire.tsx` registrado) | Inventário com `addedAt: "<data>"` e demo |
| `plugins/plugin-ui/docs/component-catalog.md` | Documentar os exports |

Qualquer outro arquivo: fora do escopo.

### 2.4 Entregáveis

**a) Tokens (`questionnaire.css`)** — na raiz `.delpi-ui-form-root`, todos os tokens `--delpi-ui-form-*` da [UI-03 §3.2](./UI-03-FORMULARIO-PUBLICO.md#32-tokens--claro-e-escuro-inventário-de-16112026) com valores do **claro**; em `.delpi-ui-form-root[data-color-scheme="dark"]` os valores do **escuro**; `color-scheme: light | dark` correspondente. Os papéis que usam tokens já existentes (`--delpi-ui-surface`, `-text`, `-muted`, `-accent`, `-on-accent`, `-border`, `-control-border`, `-danger`, `-success`, `-focus-ring`) também são definidos **dentro da raiz** com os valores da tabela, para não depender do host. Fonte: `--delpi-ui-form-font`.

**b) `useSessionColorScheme()`** — retorna `{ scheme: "light" | "dark", toggle(), userChosen: boolean }`.
- Valor inicial pelo `window.matchMedia("(prefers-color-scheme: dark)")` (ambiente sem `matchMedia` → `light`).
- Acompanha mudanças do aparelho **até** o primeiro `toggle()`; depois mantém a escolha da visita.
- **Não lê nem grava** nada em armazenamento; não altera `<html>`/`document`.

**c) `QuestionnaireThemeScope`** — `({ colorScheme?: "auto" | "light" | "dark", children, className? })`; renderiza o elemento raiz `.delpi-ui-form-root` com `data-color-scheme` resolvido (`auto` usa o hook). Expor o estado e o `toggle` por contexto (ex.: `useQuestionnaireColorScheme()`) para o futuro botão de tema (P2).

**d) `FormPageLayout`** — `({ band: "compact" | "tall", children, className? })`; ocupa a altura da janela com o fundo `--delpi-ui-form-page-bg`; faixa `--delpi-ui-form-band-bg` com 112 px (`compact`) / 168 px (`tall`) em tela estreita e 220 px a partir de 600 px; coluna com margem lateral 16 px (estreita) e largura máxima 760 px centralizada (≥ 600 px); sobreposição da coluna sobre a faixa de 80 px (`compact`) / 112 px (`tall`) e 160 px a partir de 600 px; espaço entre filhos 12 px / 16 px.

**e) Demo no catálogo** — layout com dois cartões de exemplo (texto neutro, sem a Pesquisa), botão de demo para alternar tema, e visualização lado a lado ou alternada de claro e escuro.

### 2.5 Invariantes

- **Namespace (ajuste na revisão da declaração, 16/11/2026):** o kit já tem `.delpi-ui-form-actions*` e `--delpi-ui-form-actions-*` (barra de ações de formulários, ~37 usos). **Nunca** criar classe ou token com o nome `form-actions*`; novos nomes do kit usam `.delpi-ui-form-root`, `.delpi-ui-form-page*` etc., sem tocar nos existentes.

- Nenhuma alteração visual em componente existente do PluginUI ou em qualquer MFE.
- Nenhum seletor global; nenhum `!important`; nenhum valor de cor fora dos tokens.
- Sem texto em português fixo nos componentes; sem referência à Pesquisa.
- Sem persistência no navegador.

### 2.6 Testes mínimos

1. Tema inicial `dark` quando `matchMedia` indica escuro e `light` quando claro; `light` sem `matchMedia`.
2. `toggle()` alterna e **não** chama `localStorage`/`sessionStorage` (espionar).
3. Mudança do aparelho antes do `toggle()` é seguida; depois do `toggle()`, ignorada.
4. Novo montar do componente (simula reabrir a página) volta ao tema do aparelho.
5. `QuestionnaireThemeScope` aplica `data-color-scheme` e as classes dual (`prefixo` + `delpi-ui-form-root`).
6. `FormPageLayout` aplica as variantes `compact`/`tall`.
7. `componentRegistry.test.ts` continua cobrindo todos os exports visuais.
8. Teste de contrato do CSS (no padrão dos `*CssContract.test.ts` existentes): `questionnaire.css` define todos os tokens da UI-03 §3.2 no bloco claro **e** no bloco `[data-color-scheme="dark"]`, e não contém `:root`, `html`, `body`, `*` nem `!important`.

### 2.7 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| A1 | Tokens claro/escuro presentes com os valores da UI-03 §3.2 | Trecho do CSS e lista dos tokens no relatório |
| A2 | Tema segue o aparelho, troca só na visita, não persiste | Testes 1–4 verdes |
| A3 | Layout conforme medidas em 375 px e 1280 px, nos dois temas | Demo no catálogo + capturas no relatório |
| A4 | Zero CSS de componente fora do PluginUI; sem seletor global | Auditorias de §1.3 sem item novo |
| A5 | Build do remote e `verify-host-exports` ok; catálogo abre em PROD em `/apps/plugin-ui` sem erro | Saída do build + verificação pós-deploy |
| A6 | Nenhuma regressão em MFE existente | Conferência de pelo menos um MFE após deploy |
| A7 | Diagnóstico do logo 403 registrado | Seção no relatório |
| A8 | Verificador independente aprovado | Veredito sem edição |

---

## 3. Revisão do P1 (16/11/2026)

**Veredito do coordenador:** `ACCEPT_WITH_RESIDUAL`. Conferido no código (`7abe0b338b`): hook sem persistência e sem tocar `document`, escopo de tema com contexto, layout com as medidas, 23 tokens nos dois temas iguais à UI-03 §3.2, `--delpi-ui-focus-ring` no mesmo formato (sombra) já usado pelo kit, nenhum nome `form-actions*`, nenhum termo da Pesquisa. Verificador independente: `ACCEPT_WITH_RESIDUAL`, sem ordens de correção. Deploy PROD e HML confirmados pelo executor.

| Resíduo | Descrição | Destino |
|---|---|---|
| R1 | Entre 600 e ~792 px a coluna perde a margem lateral (`max-width: 760px` com `margin: auto`, sem respiro) | **Corrigir no P2** |
| R2 | Com `colorScheme` fixo (`light`/`dark`), o contexto ainda expõe `toggle()`, que não muda nada visualmente | **Corrigir no P2** (expor `canToggle`) |
| R3 | `up-hml-sequential.sh` aborta por drift do compose HML (`helpdesk`/`helpdesk-api` fora das fases) — deploy feito com o compose direto | Owner de infraestrutura; fora da Pesquisa |
| R4 | Permissões nos clones do servidor: scripts `664` (sem execução) e `public-hub/public/*.svg` `660`/`670` (causa do logo 403, D3) | Pacote de infraestrutura a programar antes do P6 |
| R5 | `tsc --noEmit` com 2 erros pré-existentes em testes não tocados | Fora do escopo |

## 4. Pacote P2 — Cartão base, abertura, cabeçalho, progresso, tema e pergunta

**Fase do plano:** 2. **Pré-requisito:** P1 aceito.

### 4.1 Objetivo

Criar no kit os componentes de **estrutura de conteúdo** do formulário — cartão base, logo, botão de tema, barra de progresso, cartão de abertura, cartão de cabeçalho e cartão de pergunta —, nos dois temas, e corrigir os resíduos R1 e R2 do P1. Ainda **sem** escalas de nota, campos de resposta, rodapé ou revisão.

### 4.2 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/forms/questionnaire/` | Novos: `FormCard.tsx`, `FormLogo.tsx`, `FormThemeToggle.tsx`, `FormProgress.tsx`, `FormIntroCard.tsx`, `FormHeaderCard.tsx`, `QuestionCard.tsx` + testes; ajustar `QuestionnaireThemeScope.tsx` (R2), `index.ts` |
| `plugins/plugin-ui/src/styles/questionnaire.css` | Estilos dos novos componentes; correção R1 |
| `plugins/plugin-ui/src/styles/questionnaireCssContract.test.ts` | Estender o contrato às novas classes |
| `plugins/plugin-ui/src/components/forms/index.ts` | Exports |
| `plugins/plugin-ui/src/catalog/visualComponents.ts`, `src/catalog/demos/questionnaire.tsx`, `src/app/catalog.css` | Inventário (`addedAt`) e demos |
| `plugins/plugin-ui/docs/component-catalog.md` | Documentação |

### 4.3 Entregáveis

Medidas, cores e textos de referência: [UI-03 §3.3–§3.5](./UI-03-FORMULARIO-PUBLICO.md#33-estrutura-da-página) e a [referência visual](./UI-03-REFERENCIA-VISUAL.html). **Nenhum texto fixo**: todo rótulo, título e nome acessível entra por propriedade.

**a) `FormCard`** — cartão base reutilizado pelos demais (e pelos pacotes seguintes): fundo `--delpi-ui-surface`, borda `1px --delpi-ui-border` (**obrigatória** no escuro), raio 12 px, sombra `--delpi-ui-form-card-shadow`, padding 20 px (estreito) / 28 px × 32 px (≥ 600 px), coluna com espaço 12 px. Props: `as?` (`"div" | "section" | "fieldset"`), `tone?: "default" | "invalid"` (borda `--delpi-ui-danger`), `className`, `children`.

**b) `FormLogo`** — `({ src, alt, size: "sm" | "md" | "lg" })` → altura 34 / 40 / 44 px, largura automática; envolve a imagem num selo com fundo `--delpi-ui-form-logo-bg` (transparente no claro; branco com padding 6 × 10 px e raio 8 px no escuro).

**c) `FormThemeToggle`** — usa `useQuestionnaireColorScheme()`; botão redondo 44 × 44 px, borda `--delpi-ui-form-border-soft`, fundo da superfície, ícone `--delpi-ui-muted`; ícone **lua** no claro e **sol** no escuro (`lucide-react`, como os demais componentes do kit); `aria-label` **obrigatório por prop**; `aria-pressed` refletindo o escuro. **Não renderiza** quando o escopo não permite troca (R2).

**d) `FormProgress`** — `({ done, total, label, ariaLabel })`: trilho `--delpi-ui-form-track` 6 px, raio 3 px, preenchimento `--delpi-ui-accent`; `role="progressbar"` com `aria-valuemin=0`, `aria-valuemax=100`, `aria-valuenow` = `round(100 × done ÷ total)` (0 se `total` = 0); `label` (texto pronto, ex.: “3 de 12”) exibido pelo componente que o usa.

**e) `FormIntroCard`** — tela de abertura: `logo`, `headerAction?` (botão de tema, à direita do logo), `eyebrow?` (12 px, maiúsculas, `--delpi-ui-muted`), `title` (26 px, 700), `context?: { label, value }` (bloco `--delpi-ui-form-tint`, raio 10 px, padding 14 × 16 px; omitido se ausente), `description?` (16 px), `items?: { icon, content }[]` (lista com ícone 18 px em `--delpi-ui-accent`, espaço 12 px), `action: ReactNode` (o botão primário entra pronto — o `ActionButton` do kit ou o futuro botão do P4), `footnote?` (12 px, `--delpi-ui-muted`).

**f) `FormHeaderCard`** — cabeçalho das etapas e da revisão: linha do `logo` com `meta?` (≥ 600 px, ex.: prazo) e `headerAction?` à direita; `title` (20 px / 28 px, 700); `subtitle?` (14–15 px, `--delpi-ui-muted`, aceita `ReactNode` para destaque em negrito); divisor `--delpi-ui-form-track`; `step?: { label, progressLabel }` (linha com rótulo da etapa à esquerda e texto do progresso à direita) e `progress?: { done, total, ariaLabel }` usando `FormProgress`.

**g) `QuestionCard`** — `fieldset` + `legend` sobre `FormCard`: `eyebrow?` (rótulo do tema, 12 px, maiúsculas, `letter-spacing .06em`, `--delpi-ui-muted`), `number?`, `prompt` (16 px / 17 px ≥ 600 px, 600, altura de linha 1,4), `required` (asterisco em `--delpi-ui-danger` com `aria-hidden` + texto acessível por prop `requiredLabel`), `optionalLabel?` (peso normal, `--delpi-ui-muted`), `error?` (13 px, 600, `--delpi-ui-danger`, ligado por `aria-describedby` com id gerado; liga `tone="invalid"`), `children` (a resposta, nos próximos pacotes).

**h) R1** — a partir de 600 px a coluna mantém respiro lateral até caber 760 px (ex.: `width: min(760px, 100% - 32px)` centralizada).

**i) R2** — o contexto passa a expor `canToggle: boolean` (`true` só em `colorScheme="auto"`); com esquema fixo, `toggle()` não faz nada e `FormThemeToggle` não aparece.

**j) Demos no catálogo** — abertura completa, cabeçalho com progresso em 3 de 12 e cartões de pergunta nos estados normal, opcional e com erro, nos dois temas lado a lado (textos de exemplo neutros, sem a Pesquisa).

### 4.4 Invariantes

Mesmos do P1 (§2.5), mais: os componentes não importam nada da Pesquisa nem do `public-hub`; `FormCard` não substitui nem altera `SectionCard` ou outros cartões existentes; ícones só do `lucide-react` já usado pelo kit.

### 4.5 Testes mínimos

1. `QuestionCard`: `fieldset/legend`; asterisco com `aria-hidden` e texto acessível; `optionalLabel`; erro ligado por `aria-describedby` e cartão com tom inválido.
2. `FormProgress`: `aria-valuenow` correto (0, parcial, 100; `total` 0 → 0).
3. `FormThemeToggle`: alterna o tema do escopo; ícone e `aria-pressed` mudam; não renderiza com esquema fixo.
4. `QuestionnaireThemeScope`: `canToggle` true só em `auto`; `toggle()` sem efeito no fixo.
5. `FormLogo`: tamanhos e selo (classe/token) presentes.
6. `FormIntroCard`/`FormHeaderCard`: omitem blocos opcionais ausentes; renderizam `headerAction`/`meta`.
7. Contrato do CSS estendido: novas classes só com `var(--delpi-ui-*)` para cor; sem seletor global nem `!important`.
8. `componentRegistry.test.ts` verde.

### 4.6 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| B1 | Os sete componentes exportados, documentados e no catálogo com `addedAt` | Diff + catálogo |
| B2 | Visual conforme UI-03 §3.3–§3.5 em 375 e 1280 px, nos dois temas | Capturas das demos no relatório |
| B3 | R1 corrigido (respiro lateral entre 600 e 792 px) | Captura em ~700 px |
| B4 | R2 corrigido (`canToggle`, botão oculto no fixo) | Testes 3–4 |
| B5 | Acessibilidade: semântica, nomes por prop, foco visível, alvos ≥ 44 px no botão de tema | Testes + revisão |
| B6 | Zero texto fixo e zero referência à Pesquisa nos componentes | `grep` no relatório |
| B7 | Auditorias de §1.3 sem item novo; build e `verify-host-exports` ok | Saídas |
| B8 | Deploy PROD e HML com catálogo 200 e MFE de referência sem regressão | Verificação pós-deploy |
| B9 | Verificador independente aprovado | Veredito sem edição |

### 4.7 Ajustes da revisão da declaração (16/11/2026)

1. **`legend` sem `display: contents`** (perde o nome acessível do grupo em alguns navegadores): o `legend` é o primeiro filho do `fieldset`, visível, sem flutuação e sem padding, e contém o rótulo do tema (bloco pequeno) + número + enunciado + marca de obrigatória/opcional. O nome do grupo fica “Qualidade 1. Como você avalia…”.
2. **Texto só para leitor de tela:** seguir o padrão do kit (classe com escopo do componente, como `.delpi-ui-underline-nav__label--sr-only`), ex.: `.delpi-ui-form-question__sr-only` em `questionnaire.css`; nada global.
3. **`FormProgress.label`:** quando usado no `FormHeaderCard`, o texto do progresso aparece **uma vez**, na linha da etapa; o componente não repete o rótulo.
4. **Alterações concorrentes:** o working tree tem mudanças de outra tarefa em `src/index.ts` e `src/styles.css` do plugin-ui. O P2 **não** altera esses arquivos; o commit inclui só os arquivos do §4.2 (conferir com `git diff --cached --stat` antes do commit).

**Deploy em HML:** enquanto o resíduo R3 existir, é aceito o mesmo procedimento do P1 (compose direto com os parâmetros do script), registrado no relatório.

---

## 5. Revisão do P2 (17/11/2026)

**Veredito do coordenador:** `ACCEPT_WITH_RESIDUAL`. Conferido no código (`78f11fbd03`, ancestral de `main`): os sete componentes sem texto fixo e sem referência à Pesquisa; `legend` visível como primeiro filho com tema + número + enunciado; asterisco oculto ao leitor de tela com texto acessível por propriedade; erro ligado por `aria-describedby`; botão de tema some com esquema fixo (`canToggle`); progresso com `aria-valuenow` limitado a 0–100; R1 com `min(760px, 100% - 32px)`; commit só com os arquivos do pacote. Verificador: `ACCEPT_WITH_RESIDUAL` na 3ª rodada, depois de duas ordens de correção resolvidas em código. Deploy PROD e HML confirmados; o script de HML voltou a funcionar (R3 resolvido por correção de outra frente, `b5f42ed1ee`).

| Resíduo | Descrição | Destino |
|---|---|---|
| R3 | Script de deploy HML | **Resolvido** (upstream) |
| R4 | Permissões nos clones do servidor (inclui logo 403, D3) e ajustes locais de modo de arquivo feitos durante o deploy | Pacote de infraestrutura antes do P6 |
| R5 | 2 erros de `tsc` pré-existentes | Fora do escopo |
| R6 | Dentro do `fieldset`, o espaço entre vários filhos da área de resposta (escala, legenda, “Sua nota…”, N/A, erro) não está garantido — o próprio CSS registra que o espaçamento do cartão só separa título ↔ conteúdo | **Tratar no P3** (pilha própria da área de resposta) |

## 6. Pacote P3 — Respostas: escala de notas, “Não se aplica” e texto aberto

**Fase do plano:** 3. **Pré-requisito:** P2 aceito.

### 6.1 Objetivo

Criar os controles de resposta do kit — escala numérica genérica (serve 1–5 e 0–10), opção “Não se aplica” exclusiva com as notas e campo de texto aberto —, nos dois temas, prontos para entrar no `QuestionCard`, e tratar o resíduo R6.

### 6.2 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/forms/questionnaire/` | Novos: `RatingScale.tsx` (+ subcomponentes internos ou exportados: opção, legenda das pontas, linha da nota escolhida), `NotApplicableOption.tsx`, `QuestionTextAnswer.tsx`, `QuestionAnswerStack.tsx` (R6) + testes; `index.ts` |
| `plugins/plugin-ui/src/styles/questionnaire.css` e `questionnaireCssContract.test.ts` | Estilos e contrato |
| `plugins/plugin-ui/src/components/forms/index.ts` | Exports |
| `plugins/plugin-ui/src/catalog/visualComponents.ts`, `src/catalog/demos/questionnaire.tsx`, `src/app/catalog.css` | Inventário e demos |
| `plugins/plugin-ui/docs/component-catalog.md` | Documentação |

**Não alterar** `TextAreaField`, `FormFieldShell`, `src/index.ts`, `src/styles.css` nem componentes existentes. Se o campo de texto do kit não atingir o visual só com tokens, **parar e reportar** (`DECISION_REQUIRED`).

### 6.3 Decisão de interação (registrada na UI-03 §3.7)

As notas e o “Não se aplica” formam **um único grupo de opções exclusivas com `input type="radio"` nativo** (mesmo `name`), visualmente substituído pelos botões da especificação. Consequências:

- teclado padrão de grupo de opções: **Tab** entra e sai do grupo; **setas** movem e escolhem; **Espaço** escolhe; **Enter nunca envia** formulário;
- a exclusividade nota × N/A é garantida pelo próprio grupo;
- o nome acessível de cada opção vem por propriedade (ex.: “4 — Satisfeito”, “Não se aplica”);
- **nenhuma opção marcada** no início (`value` nulo).

### 6.4 Entregáveis

Medidas e estados: [UI-03 §3.4](./UI-03-FORMULARIO-PUBLICO.md#34-componentes-do-formulário) e a [referência visual](./UI-03-REFERENCIA-VISUAL.html). Nenhum texto fixo.

**a) `RatingScale`** — props: `name`, `min`, `max`, `value: number | "na" | null`, `onChange(value)`, `optionLabel(n) → string` (nome acessível de cada nota), `endLabels: { min, max }` (textos das pontas), `endLabelsPosition: "below" | "above"`, `narrowColumns?` (colunas em tela estreita; padrão = quantidade de notas; 0–10 usa 6), `selectionCaption?(n) → ReactNode` (linha após escolher, ex.: “Sua nota: 4 · Satisfeito”), `notApplicable?: { label: string }` (renderiza `NotApplicableOption` no mesmo grupo), `invalid?`, `describedBy?` (id do erro do cartão), `disabled?`.
- Estreito (< 600 px): grade de colunas iguais, espaço 8 px, altura 48 px (46 px quando `max - min ≥ 10`); ≥ 600 px: botões 64 × 52 px, espaço 10 px, numa linha (0–10 numa linha só).
- Normal: superfície, borda `--delpi-ui-control-border`, raio 8 px, número 17–18 px peso 600. Selecionado: fundo e borda `--delpi-ui-accent`, número `--delpi-ui-on-accent`. Foco visível com `--delpi-ui-focus-ring`. Inválido: borda `--delpi-ui-danger` nos botões **ou** só no cartão — escolher um e justificar.
- Legenda das pontas: 12–13 px, `--delpi-ui-muted`, extremos à esquerda e à direita, acima ou abaixo conforme a prop.
- Linha da nota escolhida: 13–14 px, 600, `--delpi-ui-form-accent-text`.
- Sem palavras quebradas e sem rolagem horizontal em 360 px; alvos ≥ 44 px.

**b) `NotApplicableOption`** — pílula 44 px de altura (52 px ≥ 600 px), raio total, padding 16 px, borda de controle, indicador redondo 18 px (anel de 6 px em `--delpi-ui-accent` quando escolhida); escolhida: borda primária, fundo `--delpi-ui-form-tint`, texto `--delpi-ui-form-accent-text` peso 600. Posição: abaixo da linha da nota no estreito; à direita da escala após divisor vertical de 1 px a partir de 600 px. Faz parte do grupo do `RatingScale` (não é controle independente).

**c) `QuestionTextAnswer`** — campo de texto aberto sobre o `TextAreaField` existente: rótulo visível (por prop), texto de exemplo (por prop), altura mínima 96 px, padding 12 px, fundo `--delpi-ui-form-input-bg`, borda de controle, raio 8 px, 15 px, redimensionável na vertical, `maxLength?`, `describedBy?`. Aparência obtida **só por tokens/classes no escopo `.delpi-ui-form-root`**.

**d) `QuestionAnswerStack` (R6)** — pilha da área de resposta dentro do `QuestionCard` com espaço 12 px (estreito) / 14 px (≥ 600 px) entre escala, legenda, linha da nota, N/A e campo, garantindo o mesmo ritmo da referência. Ajustar o `QuestionCard` só se indispensável para o erro ficar logo após a pilha.

**e) Demos no catálogo** — dentro de `QuestionCard`, nos dois temas: escala 1–5 sem escolha, com nota escolhida, com N/A escolhido e com erro; escala 0–10 com legenda acima (sem N/A); campo aberto vazio e preenchido. Textos de exemplo neutros (sem a Pesquisa).

### 6.5 Invariantes

Os do P1/P2, mais: nenhuma lógica de obrigatoriedade, progresso ou envio (isso é do P5); nenhuma cor por faixa na escala 0–10; `0` é valor válido.

### 6.6 Testes mínimos

1. Grupo nativo: todos os `radio` com o mesmo `name`; nenhum marcado no início; escolher nota chama `onChange(n)`; escolher N/A chama `onChange("na")` e desmarca a nota (e vice-versa).
2. Teclado: setas movem/escolhem dentro do grupo; Enter não dispara `submit` de um `<form>` ao redor.
3. Nomes acessíveis vindos de `optionLabel` e de `notApplicable.label`.
4. `0` escolhível e exibido; escala 0–10 com 11 opções e legenda acima.
5. `selectionCaption` só aparece com nota escolhida (não com N/A).
6. `describedBy` repassado ao grupo; estado inválido aplicado.
7. `QuestionTextAnswer`: rótulo, `onChange`, `maxLength`, `describedBy`.
8. Contrato do CSS estendido às novas classes.
9. `componentRegistry.test.ts` verde.

### 6.7 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| C1 | Componentes exportados, documentados e no catálogo com `addedAt` | Diff + catálogo |
| C2 | Visual conforme UI-03 §3.4 em 360, 375, ~700 e 1280 px, nos dois temas, sem palavra quebrada nem rolagem horizontal | Capturas |
| C3 | Grupo nativo com exclusividade nota × N/A e teclado padrão | Testes 1–2 |
| C4 | Contrastes: borda de controle ≥ 3:1 e texto sobre a primária conforme UI-03 §3.2 | Medição no relatório |
| C5 | R6 resolvido: ritmo de espaçamento igual à referência dentro do cartão | Captura comparada |
| C6 | `TextAreaField` intacto; aparência do campo só por tokens no escopo | Diff |
| C7 | Zero texto fixo e zero referência à Pesquisa | `grep` |
| C8 | Auditorias, build e `verify-host-exports` ok; deploy PROD e HML com catálogo 200 e MFE de referência sem regressão | Saídas |
| C9 | Verificador independente aprovado | Veredito sem edição |

### 6.8 Ajustes da revisão da declaração (17/11/2026)

1. **Estado inválido:** aceita a borda `--delpi-ui-danger` nos botões + `aria-invalid` nos `input`, somada ao `tone="invalid"` do cartão.
2. **Campo de texto:** aceito o envoltório com `role="group"` + `aria-describedby`, sem alterar o `TextAreaField`. Novo resíduo **R7**: o `TextAreaField` não repassa `aria-*` ao `<textarea>`; como as perguntas abertas são opcionais, o impacto é baixo; mudança no componente compartilhado fica para decisão própria.
3. **`addedAt`:** usar a data real da inclusão (`2026-11-17`), não a do P1.
4. **Publicação com `main` divergente:** a cópia local do executor tinha um commit de outro trabalho ainda não publicado (`ee7a961633`, correção de engineering). **Proibido publicar esse commit junto com o P3** (`AGENTS.md`, Regra 9: não misturar tarefas). Caminho autorizado pelo solicitante para este pacote: criar um **worktree temporário** a partir de `origin/main`, aplicar nele só o commit do P3, publicar a partir dele e removê-lo em seguida, sem alterar o worktree principal nem o commit do outro trabalho; registrar no relatório.

---

## 7. Revisão do P3 (17/11/2026)

**Veredito do coordenador:** `ACCEPT_WITH_RESIDUAL`, com correção obrigatória no início do P4. Conferido: commit `f75d2385fe` em `main`, 16 arquivos só em `plugins/plugin-ui`; o commit de outro trabalho (`ee7a961633` e sucessores) **não** foi publicado; publicação feita pelo worktree temporário autorizado e removido. Grupo `radio` nativo com o mesmo `name`, N/A no grupo, `0` válido, Enter sem envio, `aria-invalid`, sem texto fixo. Contrastes medidos dentro do alvo (borda de controle 3,04:1 claro / 4,29:1 escuro). Verificador: `ACCEPT_WITH_RESIDUAL` na 1ª rodada.

| Resíduo | Descrição | Destino |
|---|---|---|
| **R8** | **Posição da legenda das pontas:** com `endLabelsPosition="below"`, o bloco “1 · … / 5 · …” é renderizado **depois** de toda a linha de opções — no celular fica abaixo da linha da nota e do “Não se aplica”; no computador, abaixo da linha inteira (inclusive do N/A). Na referência, a legenda fica **logo abaixo dos números**, antes da linha “Sua nota…” e do N/A (celular) e dentro da coluna das notas, à esquerda do divisor (computador) | **Corrigir no P4 (§8.3a)** |
| R9 | Setas/Home/End implementados à mão (determinístico), sem teste dedicado para Home/End | Testes no P4 |
| R4 | Permissões nos clones do servidor (inclui logo 403, D3) | Pacote de infraestrutura antes do P6 |
| R5 | 2 erros de `tsc` pré-existentes | Fora do escopo |
| R7 | `TextAreaField` sem repasse de `aria-*` | Decisão própria futura |

## 8. Pacote P4 — Correção R8, botões, rodapé de ações, aviso, revisão e resultado

**Fase do plano:** 4. **Pré-requisito:** P3 aceito.

### 8.1 Objetivo

Corrigir a posição da legenda da escala (R8) e criar os componentes de **ação e fechamento** do formulário — botões do formulário, rodapé de ações, aviso, seção de revisão e tela de resultado —, nos dois temas. Ainda **sem** o fluxo completo (P5).

### 8.2 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/forms/questionnaire/` | Ajustar `RatingScale.tsx` (R8) e testes (R9); novos: `FormButton.tsx`, `FormStepFooter.tsx`, `FormNotice.tsx`, `FormReviewSection.tsx` (+ `FormReviewRow`), `FormResultPanel.tsx` + testes; `index.ts` |
| `plugins/plugin-ui/src/styles/questionnaire.css` e `questionnaireCssContract.test.ts` | Estilos e contrato |
| `plugins/plugin-ui/src/components/forms/index.ts` | Exports |
| `plugins/plugin-ui/src/catalog/visualComponents.ts`, `demos/questionnaire.tsx`, `src/app/catalog.css` | Inventário (`addedAt` = data real) e demos |
| `plugins/plugin-ui/docs/component-catalog.md` | Documentação |

**Não alterar** `ActionButton`, `src/index.ts`, `src/styles.css` nem outros componentes existentes.

### 8.3 Entregáveis

Referência: [UI-03 §3.3–§3.6](./UI-03-FORMULARIO-PUBLICO.md#33-estrutura-da-página) e a [referência visual](./UI-03-REFERENCIA-VISUAL.html). Nenhum texto fixo.

**a) R8 — legenda das pontas** — ordem final da escala:
- **Estreito:** números → legenda das pontas (se `below`) → “Sua nota…” → “Não se aplica”. Com `above`: legenda → números → “Sua nota…”.
- **≥ 600 px:** coluna da esquerda com números + legenda (abaixo ou acima); divisor vertical de 1 px; “Não se aplica” à direita, alinhado à linha dos números; “Sua nota…” abaixo de tudo, em largura total.
- Manter o grupo `radio` e a ordem de foco: números e depois N/A.
- Testes que verificam a ordem no DOM nos dois casos (`below`/`above`) + **R9**: testes de Home/End (incluindo N/A como último).

**b) `FormButton`** — botões do formulário sobre o `ActionButton` existente (sem alterá-lo), com classe de escopo: `variant: "primary" | "secondary"`, `busy?` + `busyLabel` (desabilitado e mantendo o foco, via `softDisabled`), `fullWidth?`. Medidas: altura 48 px, raio 8 px, 16 px peso 600, padding 0 24 px (primário) / 0 20 px (secundário). Primário: fundo `--delpi-ui-accent`, texto `--delpi-ui-on-accent`; secundário: superfície, borda `--delpi-ui-form-border-soft`, texto `--delpi-ui-text`. Foco com `--delpi-ui-focus-ring`. **Se o CSS do `ActionButton` impedir o visual sem `!important` ou sem alterá-lo, parar e reportar (`DECISION_REQUIRED`).**

**c) `FormStepFooter`** — `message?: ReactNode` (pendência, 13–14 px, 600, `--delpi-ui-danger`, com `role="status"`), `back?: { label, onClick }`, `next: { label, onClick, busy?, busyLabel? }`.
- **< 600 px:** fixo na base (`position: sticky; bottom: 0`), ocupando a largura da coluna até as bordas (margem negativa de 16 px), fundo da superfície, borda superior `--delpi-ui-border`, sombra leve para cima, padding 12 × 16 × 16 px; mensagem em cima; Voltar (secundário) à esquerda e o primário ocupando o restante.
- **≥ 600 px:** no fim da coluna, sem fixar; mensagem à esquerda, botões à direita; primário com largura mínima 160 px.

**d) `FormNotice`** — aviso em bloco: `tone: "warning" | "info"`, `children`; warning com `--delpi-ui-form-warning-bg/-border/-text`, raio 12 px, padding 14 × 16 px, 14 px, altura de linha 1,5; `role="note"`.

**e) `FormReviewSection` + `FormReviewRow`** — seção da revisão sobre `FormCard`: `title` (16 px, 700), `edit: { label, ariaLabel, onClick }` (botão 36 px de altura com ícone de lápis do `lucide-react`, borda `--delpi-ui-form-border-soft`, texto `--delpi-ui-accent`, área clicável ≥ 44 px), `rows: { label, value, muted?, block? }[]`. Linha: borda superior `--delpi-ui-form-track`, padding 10 px 0, 14 px; rótulo à esquerda e valor à direita em peso 600; `muted` = itálico em `--delpi-ui-muted`; `block` = rótulo em cima e valor embaixo (comentários longos, com quebra de linha preservada). Usar lista semântica (`dl`/`dt`/`dd`).

**f) `FormResultPanel`** — tela final ou de estado, centralizada sobre `FormCard`: `tone: "success" | "info" | "warning" | "error"`, `logo?`, `title` (26 px, 700), `message` (16 px), `hint?` (14 px, `--delpi-ui-muted`), `action?: ReactNode`. `success`: círculo 72 px em `--delpi-ui-success` com ícone de confirmação em `--delpi-ui-on-accent` (garantir contraste nos dois temas e medir); demais tons: sem círculo verde (ícone discreto opcional). `role="status"` em sucesso/informação e `role="alert"` em erro.

**g) Demos no catálogo** — nos dois temas: escala com R8 corrigido (1–5 com N/A; 0–10 com legenda acima); rodapé com e sem Voltar, com mensagem e enviando; aviso; seção de revisão com valores, N/A, vazio em itálico e comentário em bloco; resultado de sucesso e de erro com ação. Textos neutros.

### 8.4 Invariantes

Os anteriores, mais: nenhuma lógica de fluxo (navegação entre etapas, validação, envio) — os componentes só recebem dados e funções; `ActionButton` intocado.

### 8.5 Testes mínimos

1. R8: ordem no DOM para `below` e `above`; N/A depois da legenda no estreito. R9: Home/End.
2. `FormButton`: variantes, `busy` mostra `busyLabel`, mantém foco e não dispara `onClick`.
3. `FormStepFooter`: sem `back` não renderiza Voltar; mensagem com `role="status"`; botão primário recebe `busy`.
4. `FormReviewSection`: `dl/dt/dd`; Editar com nome acessível; `muted` e `block`.
5. `FormResultPanel`: papel `status`/`alert` por tom; círculo só em `success`.
6. `FormNotice`: tom e `role="note"`.
7. Contrato do CSS estendido; `componentRegistry.test.ts` verde.

### 8.6 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| D1 | R8 corrigido: legenda imediatamente abaixo (ou acima) dos números, em 360 px e 1280 px, nos dois temas | Capturas comparadas com a referência |
| D2 | Componentes exportados, documentados e no catálogo | Diff + catálogo |
| D3 | Visual conforme UI-03 §3.3–§3.5 em 360, 375, ~700 e 1280 px, nos dois temas; rodapé fixo só abaixo de 600 px | Capturas |
| D4 | Contraste do ícone de sucesso e dos botões medido nos dois temas | Tabela no relatório |
| D5 | `ActionButton` intocado; nenhum `!important` | Diff + contrato |
| D6 | Zero texto fixo e zero referência à Pesquisa | `grep` |
| D7 | Auditorias, build e `verify-host-exports` ok; deploy PROD e HML com catálogo 200 e MFE de referência sem regressão | Saídas |
| D8 | Verificador independente aprovado | Veredito sem edição |

**Publicação:** se o `main` local voltar a ter commit de outro trabalho não publicado, usar o mesmo caminho autorizado no §6.8 item 4 (worktree temporário a partir de `origin/main`, só o commit do pacote).

### 8.7 Ajustes da revisão da declaração (17/11/2026)

1. **R8:** aceita a estrutura proposta (`__main` com números + legenda; “Sua nota”, divisor e N/A como irmãos; reposicionamento por `order` só a partir de 600 px; ordem de foco inalterada).
2. **`FormButton` sem depender da ordem dos `@import`:** a sobrescrita do `ActionButton` não pode depender de `questionnaire.css` vir depois de `action-controls.css` em `styles.css` (frágil: qualquer reordenação quebra o visual). Escopar os seletores na raiz do kit, ex.: `.delpi-ui-form-root .delpi-ui-form-button`, ganhando especificidade sem `!important` e sem tocar no `ActionButton`; incluir no teste de contrato.
3. **Rodapé fixo:** registrar no relatório que o `position: sticky` só funciona se nenhum ancestral tiver `overflow` diferente de `visible` — conferir na demo e anotar como verificação obrigatória da página pública (P6).
