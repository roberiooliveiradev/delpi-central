# UI-03 — Pedidos de execução para o Devin (pacotes)

> **Estado:** registro vivo dos pedidos de execução do [plano da UI-03](./UI-03-PLANO-IMPLEMENTACAO.md). Um pacote por vez: o próximo só é gerado depois que o anterior for **verificado e aceito** pelo solicitante.
> **Como usar:** o solicitante cola no Devin o **mini prompt** do pacote (fornecido no chat do projeto). O mini prompt manda o Devin ler este arquivo, aplicar o **Protocolo comum (§1)** e executar **somente** o pacote indicado.

## Situação dos pacotes

| Pacote | Fases do plano | Conteúdo | Deploy | Estado |
|---|---|---|---|---|
| **P1** | 0 + 1 | Inventário, tokens claro/escuro, controle de tema, layout da página, demos no catálogo | PluginUI: DEV → **PROD** (componentes genéricos) | **PRONTO PARA EXECUÇÃO** |
| P2 | 2 | Abertura, cabeçalho, progresso, botão de tema, quadro da pergunta | PluginUI → PROD | A gerar após aceite do P1 |
| P3 | 3 | Escala de notas, “Não se aplica”, texto aberto | PluginUI → PROD | A gerar |
| P4 | 4 | Rodapé de ações, revisão, tela de resultado | PluginUI → PROD | A gerar |
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
