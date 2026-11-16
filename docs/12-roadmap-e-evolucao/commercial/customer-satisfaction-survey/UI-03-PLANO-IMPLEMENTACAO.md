# UI-03 — Plano de implementação do kit de formulário (PluginUI) e da página pública da Pesquisa

> **Estado:** PLANO APROVÁVEL — nenhuma fase iniciada. Criado em 16/11/2026 sobre `main` em `9e604df78`; **revalidar HEAD, branch e working tree no início de cada fase.**
> **Especificação que este plano implementa:** [UI-03-FORMULARIO-PUBLICO.md](./UI-03-FORMULARIO-PUBLICO.md) (visual, temas, componentes, regras) e [referência visual](./UI-03-REFERENCIA-VISUAL.html). Decisões: [Q21–Q23](./BUSINESS-DECISIONS.md#f-experiência-visual).
> **Ambientes:** desenvolvimento em DEV; testes e homologação em HML; **nada em PROD** sem o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026).

## 1. Objetivo e resultado esperado

1. Um **kit de formulário reutilizável no PluginUI** (`@delpi/plugin-ui`), com todos os componentes e subcomponentes da UI-03, nos **temas claro e escuro**, e um componente que monta o **formulário guiado completo** a partir de uma definição de etapas e perguntas.
2. Uma **página pública nova e dedicada** à Pesquisa de Satisfação no `public-hub`, que importa o kit — sem reaproveitar as telas públicas existentes (nem o formulário de Customer Experience, nem a `FormPage.tsx` atual da pesquisa).

**Como medir:** as seis telas iguais à referência nos dois temas; regras da UI-03 §4 cobertas por testes; zero CSS de componente fora do PluginUI; nenhuma regressão nas outras páginas públicas e MFEs.

## 2. Ownership e limites

| Camada | Owner | Pode | Não pode |
|---|---|---|---|
| Kit de formulário | `plugins/plugin-ui` | Componentes, CSS em `src/styles/`, tokens `--delpi-ui-form-*`, testes, catálogo | Conhecer a pesquisa, a `commercial-api` ou regras de negócio |
| Página da Pesquisa | `plugins/public-hub` | Rota, carregamento por token, adaptação perguntas→definição, envio, mapeamento de resultados, opção de shell | CSS de componente; regra de negócio; persistência de respostas no navegador |
| Regras e dados | `commercial-api` | Validação final, janela, token, unicidade, gravação | — (**não muda neste plano**) |

**Fora do plano:** backend, migrações, permissões, Portal Comercial interno (UI-02), formulário de Customer Experience, construtor de formulários.

## 3. Decisões abertas antes da fase 6

| ID | Decisão | Recomendação | Impacto se mudar |
|---|---|---|---|
| D1 | **Endereço da página nova** | **Manter `/p/commercial/form/{token}`** e apontá-lo para a página nova, removendo a implementação antiga | Um endereço diferente exige alterar o gerador do link na `commercial-api` (`manage_satisfaction_surveys.py`, linha ~717) e invalida os links já gerados em HML |
| D2 | Texto de privacidade da abertura | Aguardar o responsável LGPD; até lá, a abertura mostra só “Não pedimos seus dados pessoais” | Nenhum para o código |
| D3 | Logo `/p/logoMinhaDelpi.svg` respondendo 403 em HML | **Causa encontrada (Devin, P1/fase 0, 16/11/2026):** no clone de HML o arquivo está com modo `660` (o `COPY` do Dockerfile preserva o modo, e o nginx não consegue ler); `demo-cover.svg` igual; no clone de PROD o modo é `670`, com o mesmo risco num próximo rebuild. **Correção a programar:** normalizar o modo dos arquivos em `plugins/public-hub/public/` (ex.: `chmod 644`/`git checkout`) e rebuild do `public-hub`; avaliar `chmod` no Dockerfile como endurecimento | Bloqueia o aceite visual |

## 4. Mapa de componentes do kit (PluginUI)

Pasta proposta: `plugins/plugin-ui/src/components/forms/questionnaire/` · CSS: `plugins/plugin-ui/src/styles/questionnaire.css` (importado em `src/styles.css`) · classes `prefixo` + `.delpi-ui-form-*` via `delpiUiClass`. Nomes são propostos; ajustar ao padrão do kit sem mudar a responsabilidade.

| Nível | Componente | Subcomponentes | Usa do kit |
|---|---|---|---|
| Base | `QuestionnaireThemeScope` + hook `useSessionColorScheme` | — | — |
| Layout | `FormPageLayout` | faixa da marca, coluna | — |
| Cabeçalho | `FormHeaderCard` | `FormProgress`, `FormThemeToggle` | ícones Lucide do kit |
| Pergunta | `QuestionCard` | rótulo do tema, enunciado, marca de obrigatória/opcional, mensagem de erro | — |
| Resposta | `RatingScale` | `RatingScaleOption`, `RatingScaleEndLabels`, `RatingSelectionCaption` | — |
| Resposta | `NotApplicableOption` | indicador redondo | — |
| Resposta | (texto aberto) | — | `TextAreaField`/`FormFieldShell` — se não atender ao visual, **ajustar no kit** e registrar |
| Ações | `FormStepFooter` | mensagem de pendência | `ActionButton` |
| Revisão | `FormReviewSection` | `FormReviewRow` | `ActionButton` (Editar) |
| Final | `FormResultPanel` | ícone de estado | — |
| Abertura | `FormIntroCard` | lista de itens com ícone | `ActionButton` |
| Fluxo | `GuidedQuestionnaire` | máquina de estados, validação, foco, progresso, aviso de saída | todos acima |

**Temas no kit (ajuste em relação à UI-03 §3.2):** para o kit ser reutilizável fora da Pesquisa, os **valores claro e escuro dos tokens `--delpi-ui-form-*` ficam no próprio CSS do kit**, no elemento raiz do formulário (`.delpi-ui-form-root` e `.delpi-ui-form-root[data-color-scheme="dark"]`), com `color-scheme` correspondente. O app hospedeiro pode **sobrescrever** tokens, mas não precisa declará-los. A escolha de tema é do kit: `colorScheme="auto"` segue `prefers-color-scheme`, e o botão troca **só em memória** (sem `localStorage`), conforme UI-03 §3.1.

## 5. Fases

Cada fase é um pedido de execução delimitado, com commit próprio, verificação independente (`AGENTS.md`, ciclo delpi-verifier) e relatório. **Não juntar fases num único diff.**

### Fase 0 — Preparação (sem código de produto)

- Confirmar HEAD/branch/`git status`/`git worktree list`.
- Ler: UI-03, este plano, `.cursor/rules/plugins-reusable-components.mdc`, `plugins-visual-design-system.mdc`, `plugins-frontend-build.mdc`, `plugins/plugin-ui/docs/component-catalog.md`, `export-catalog.md`, `module-federation.md`.
- Inventariar como o PluginUI publica o remote em DEV/HML e quais MFEs o carregam (risco de regressão).
- Investigar D3 (logo 403) e registrar causa.
- **Saída:** nota de inventário nesta pasta só se houver achado que mude o plano.

### Fase 1 — Fundação do kit: tokens, tema e layout

- `questionnaire.css` com tokens `--delpi-ui-form-*` claro/escuro (valores da UI-03 §3.2) e os tokens `--delpi-ui-*` existentes como base.
- `QuestionnaireThemeScope`, `useSessionColorScheme` (automático pelo aparelho, troca em memória, acompanha mudança do aparelho até o primeiro clique, sem gravar nada).
- `FormPageLayout` (faixa 112/168/220 px, coluna 16 px / 760 px, ponto de quebra 600 px).
- **Testes:** tema inicial pelo `matchMedia`; troca não grava em `localStorage`/`sessionStorage`; reabrir volta ao automático; mudança do aparelho antes e depois do clique.
- **Aceite:** demo do layout vazio nos dois temas.

### Fase 2 — Componentes de cabeçalho e pergunta

- `FormHeaderCard`, `FormProgress`, `FormThemeToggle`, `FormIntroCard`, `QuestionCard`.
- **Testes:** semântica `fieldset/legend`; asterisco e “(opcional)”; erro ligado por `aria-describedby`; progressbar com valor; botão de tema com nome acessível; logo sobre selo no escuro.

### Fase 3 — Componentes de resposta

- `RatingScale` (+ subcomponentes) genérica: `min/max`, rótulos por valor, legenda nas pontas acima/abaixo, colunas em tela estreita (6 para 0–10), linha “Sua nota…”, estado inválido.
- `NotApplicableOption` exclusiva com as notas do grupo.
- Texto aberto com `TextAreaField` (ajuste no kit se preciso).
- **Testes:** seleção, troca, exclusividade N/A, teclado (Tab/Espaço/Enter, Enter nunca envia), nomes acessíveis “4 — Satisfeito”, `0` válido, nenhuma seleção inicial, alvos ≥ 44 px, sem quebra de palavra em 360 px.

### Fase 4 — Ações, revisão e resultado

- `FormStepFooter` (fixo em tela estreita), `FormReviewSection` + `FormReviewRow`, `FormResultPanel`.
- **Testes:** rodapé fixo no celular e estático no computador; Editar com nome “Editar etapa N”; valores vazios em itálico “Não respondida”; painel de resultado com `role="status"`/`"alert"` conforme tom.

### Fase 5 — `GuidedQuestionnaire` (fluxo completo)

- Definição declarativa: `intro`, `steps[]` (`questions[]` com `kind: "scale" | "text"`), `texts` (**obrigatório** — o kit não tem textos fixos em português, conforme `plugins/plugin-ui/docs/contributing.md`; a página da Pesquisa passa os textos da UI-03 §3.6), `onSubmit(answers) → resultado`, `renderResult?`, `colorScheme`, `showThemeToggle`.
- Fluxo: abertura → etapas → revisão → enviando → resultado; Editar por etapa e “Voltar à revisão”.
- Regras genéricas: obrigatórias por etapa com foco na primeira pendência e contagem no rodapé; progresso = obrigatórias respondidas ÷ total; um envio por vez; `beforeunload` enquanto houver respostas não enviadas; nada salvo no navegador; troca de tema preserva respostas.
- **Testes:** fluxo completo com definição de exemplo **não ligada à Pesquisa**; bloqueio de avanço; edição a partir da revisão; envio duplo impedido; erro de envio mantém respostas; resultado só após `onSubmit` resolver.

### Fase 6 — Catálogo, demo e publicação do remote em DEV/HML

- Exports em `src/components/forms/index.ts` / `src/index.ts`; registro em `component-catalog.md` e `export-catalog.md`; demo com as seis telas nos dois temas.
- Build e publicação do remote do PluginUI. **Decisão do solicitante (16/11/2026):** os pacotes do kit genérico (P1–P5) seguem o deploy canônico em **PROD** após verificação, para acompanhamento pelo catálogo do PluginUI em `/apps/plugin-ui`; eles não contêm nada da Pesquisa. A página pública da Pesquisa continua **somente HML**. Pedidos de execução: [UI-03-PROMPTS-DEVIN.md](./UI-03-PROMPTS-DEVIN.md).
- **Verificar regressão** em MFEs e páginas públicas que usam o PluginUI.

### Fase 7 — Página pública nova da Pesquisa (public-hub)

- **Módulo novo e dedicado**, ex.: `plugins/public-hub/src/apps/commercial/satisfaction-survey/` com `SatisfactionSurveyPage.tsx` (adaptador), `surveyDefinition.ts` (perguntas da API → definição do kit, divisão 5/5/5), `surveyResults.ts` (resultados da API → telas) e testes. Reaproveitar `api.ts` (contrato de rede) sem mudança.
- Registrar a página conforme **D1** (recomendado: mesma rota `commercial.form`), **remover** `FormPage.tsx`, `SurveyStateView.tsx` e `form.css` antigos e seus testes obsoletos.
- Shell: opção de `chrome` **sem decoração** (sem logo, sem botão de tema e sem fundo do palco) em `types.ts`/`PublicShell.tsx`, padrão inalterado para as outras apps.
- Título do documento “Pesquisa de Satisfação de Clientes”; nome interno da campanha nunca exibido; empresa omitida se `companyName` nulo.
- **Testes:** carregamento por token; seis estados alternativos; envio único com `submitPublicSurvey`; sem gravação no navegador; demais apps públicas sem mudança.

### Fase 8 — Homologação em HML

- Deploy do PluginUI e do `public-hub` **somente em HML**.
- Roteiro: celular 360/375/390 px e computador 1280 px; claro e escuro (aparelho e botão; reabrir volta ao automático); todos os estados; teclado e leitor de tela; zoom 200%; link de empresa pendente, já respondida, campanha encerrada/agendada, token inválido.
- Gaps G1–G8 da UI-03 §6 resolvidos; G9 (endereço público do link) registrado para o gate de produção.
- **Aceite do solicitante** registrado; atualizar o estado da UI-03 e do índice.

## 6. Verificação obrigatória por fase

| Item | Comando / evidência |
|---|---|
| Testes do kit | `npm test --prefix plugins/plugin-ui` |
| Lint, testes e build da página | `npm run ci --prefix plugins/public-hub` |
| Nenhum CSS de componente fora do kit | `python3 scripts/ci/audit_platform_guardrails.py --check --base <base>` e `python3 scripts/ci/audit_mfe_plugin_ui_css.py` (sem item novo) |
| Documentação | `python3 scripts/audit_documentation_structure.py` |
| Verificação independente | ciclo `agent-kit/verifier` descrito em `AGENTS.md` (pedido em `<git-dir>/delpi-verifier/requests/`, até 3 rodadas) |
| Relatório | HEAD inicial e final, arquivos alterados, testes executados, achados, riscos, gaps restantes |

## 7. Riscos

| Risco | Mitigação |
|---|---|
| Mudança no PluginUI afetar outros MFEs | Componentes novos isolados em pasta e CSS próprios (`.delpi-ui-form-*`); nenhum seletor global; verificação de regressão na fase 6 |
| Deploy do PluginUI em PROD expor algo da Pesquisa | O kit não conhece a Pesquisa (sem textos, chaves ou rotas dela); a página pública só existe em DEV/HML; conferência de regressão em MFE após cada deploy |
| `TextAreaField` não atender ao visual | Ajuste no kit com teste, nunca CSS na página |
| Tokens do escuro sem contraste | Contrastes da UI-03 §3.2 como critério de teste |
| Escopo crescer para outros formulários | Customer Experience e construtor de formulários ficam fora; exigem decisão própria |
