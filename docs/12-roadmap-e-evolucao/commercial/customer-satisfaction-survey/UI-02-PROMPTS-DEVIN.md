# UI-02 — Pedidos de execução para o Devin (pacotes)

> **Estado:** registro vivo dos pedidos de execução do [plano da UI-02](./UI-02-PLANO-IMPLEMENTACAO.md), que refaz o visual das páginas internas da Pesquisa no Portal Comercial. Um pacote por vez: o próximo só é gerado depois que o anterior for **verificado e aceito** pelo solicitante.
> **Como usar:** o solicitante cola no Devin o **mini prompt** do pacote, fornecido no chat do projeto. O mini prompt manda o Devin ler este arquivo, aplicar o **Protocolo comum (§1)** e executar **somente** o pacote indicado.
> **Referência visual:** maquete aprovada em 18/11/2026 — <https://claude.ai/artifact/7sw5awGxjUydGU7MhzuRUk> (seis telas, tema escuro). O catálogo de mudanças está na [§4 do plano](./UI-02-PLANO-IMPLEMENTACAO.md#4-catálogo-de-mudanças-o-que-muda-em-cada-tela).

## Situação dos pacotes

| Pacote | Fases do plano | Conteúdo | Deploy | Estado |
|---|---|---|---|---|
| **P1** | 0 (inventário) + 1 | Inventário técnico + campo de texto com marcadores destacados no PluginUI (D3) | PluginUI: **PROD e HML** (componente genérico) | **A executar** (ver §2) |
| P2 | 2 | Lista de campanhas (ajustes 1–5) | Comercial: **somente HML** | A gerar — depende do aceite do P1 e da UI-02 vigente |
| P3 | 3 | Detalhe da campanha: bloco de título, abas no endereço, Participantes (4, 6–9, 15) | **Somente HML** | A gerar |
| P4 | 4 | Abas Mensagem padrão e Dados (10–14) | **Somente HML** | A gerar |
| P5 | 5 | Detalhe do participante (4, 16) | **Somente HML** | A gerar |
| P6 | 6 | Limpeza, celular e tema claro | **Somente HML** | A gerar |
| P7 | 7 | Correções da homologação | Conforme a camada alterada | A gerar |

## 1. Protocolo comum (vale para todo pacote)

### 1.1 Reancoragem obrigatória — antes de qualquer alteração

1. Rodar `git rev-parse HEAD`, `git branch --show-current`, `git status --short` e `git worktree list`.
   - Confirmar que está em `main`.
   - Atualizar com `git pull --ff-only` e registrar o HEAD inicial.
   - Não trocar nem criar branch ou worktree (`AGENTS.md`, Regras 1–10).
2. Ler, nesta ordem:
   - `AGENTS.md` (raiz), **inclusive a exceção da Pesquisa de Satisfação**;
   - `docs/11-padroes-de-desenvolvimento/instrucoes-oficiais-gpt-arquiteto-delpi-central.md`;
   - `.cursor/rules/development-standards-index.mdc`;
   - `.cursor/rules/evidence-driven-execution.mdc`;
   - `.cursor/rules/test-and-commit.mdc`;
   - `.cursor/rules/plugins-reusable-components.mdc`;
   - `.cursor/rules/plugins-visual-design-system.mdc`;
   - `.cursor/rules/plugins-frontend-build.mdc`.
3. Ler o [plano da UI-02](./UI-02-PLANO-IMPLEMENTACAO.md) inteiro e a maquete. A partir do P2, ler também a [UI-02 vigente](./UI-02-CONFIGURACAO-PESQUISAS.md).
4. Ler o padrão do kit:
   - em `plugins/plugin-ui/docs/`: `contributing.md`, `component-catalog.md`, `module-federation.md` e `architecture.md`;
   - `src/utils/delpiUiClass.ts`;
   - `src/components/forms/TextField.tsx`, `TextAreaField.tsx`, `FormFieldShell.tsx` e `NativeTextAreaControl.tsx`, com testes e CSS;
   - no catálogo: `src/catalog/visualComponents.ts`, `src/catalog/componentRegistry.tsx` e `src/catalog/demos/forms.tsx`.
5. A partir do P2, ler o padrão do Comercial:
   - `plugins/commercial/src/app/commercialUi.ts` e `dataTableUi.ts`;
   - `features/customers/pages/CustomersPage.tsx`, referência de bloco de título, “Atualizado em” e tabela;
   - `features/seller-portfolios/SellerPortfolioDetailPage.tsx`, referência de bloco de título com números (`highlights`);
   - a pasta `features/satisfaction-surveys/` inteira.
6. Ler a seção do pacote neste arquivo e **declarar antes de codificar**: objetivo, arquivos que vai criar ou alterar, invariantes e testes. **Parar e aguardar** a revisão da declaração pelo solicitante.

### 1.2 Regras de execução

- **Menor diff correto.** Só os arquivos do escopo do pacote. Proibido refatorar código não relacionado, mudar componente existente do kit (salvo o que o pacote pedir) ou formatar arquivos inteiros.
- **Comportamento preservado.** Esta frente é visual e de composição. Proibido mudar backend, chamadas de API, contratos, permissões ou regras de negócio. Fluxos que já funcionam continuam iguais: criar campanha, incluir clientes, editar contato, salvar e reverter mensagem, copiar convite e cópia manual.
- **Kit genérico:** nada da Pesquisa dentro do PluginUI. Isso inclui textos, marcadores como `{nome_empresa}`, rotas e regras. **Sem strings em português fixas** nos componentes (`contributing.md`); textos entram por propriedade.
- **CSS de componente só no PluginUI** (`plugins/plugin-ui/src/styles/`), com classes de prefixo duplo via `delpiUiClass`. No Comercial, só layout de página em `styles/satisfaction.css`.
  - **Proibido:** seletor global, `!important` e cor literal nova.
  - **Temas claro e escuro** só por tokens; trocar de tema muda só cores, nunca posição ou espaçamento.
- **Acessibilidade** faz parte do aceite: rótulos, foco visível, teclado, `aria-*` repassados ao campo nativo, contraste nos dois temas.
- Se algo do plano ou da maquete for inviável ou contraditório com o código real: **parar e reportar** com veredito `DECISION_REQUIRED`, sem inventar alternativa.
- **Não enviar respostas** pelos links públicos dos participantes de HML.

### 1.3 Verificação

1. Rodar os comandos de acordo com o que o pacote tocou:

   | Quando | Comando |
   |---|---|
   | Se tocar o PluginUI | `npm test --prefix plugins/plugin-ui` |
   | Se tocar o PluginUI | `npm run build --prefix plugins/plugin-ui` (inclui `verify-host-exports`) |
   | Se tocar o Comercial | `npm test --prefix plugins/commercial` |
   | Se tocar o Comercial | `npm run lint --prefix plugins/commercial` |
   | Se tocar o Comercial | `npm run build --prefix plugins/commercial` |
   | Sempre | `python3 scripts/ci/audit_platform_guardrails.py --check --base <HEAD inicial>` |
   | Sempre | `python3 scripts/ci/audit_mfe_plugin_ui_css.py` |
   | Sempre | `python3 scripts/ci/audit_plugin_ui_native_form_controls.py` |
   | Sempre | `python3 scripts/ci/audit_plugin_ui_duplication.py --check` |
   | Se tocar docs | `python3 scripts/audit_documentation_structure.py` |

2. **Verificador independente**, conforme `AGENTS.md` §Verificação e a parte A de `agent-kit/verifier/project-contract.md`:
   - Gravar o `PEDIDO DE VERIFICAÇÃO` em `<git-dir>/delpi-verifier/requests/`, nunca no working tree. Ele leva objetivo, IDs do pacote e critérios de aceite, escopo (`working tree` ou `base..head`), alegações e o modelo do executor.
   - Rodar `python ~/.delpi-agent-kit/verify.py --request-file <arquivo>`.
   - Corrigir cada ordem de correção no código de produção. Nunca alterar teste ou limite para passar.
   - No máximo 3 rodadas.
   - `DECISION_REQUIRED` ou `EXECUTION_DRIFT` **encerram** o pacote e voltam ao solicitante.

### 1.4 Commit, push e deploy

- Commit **só** com os arquivos do pacote, mensagem em português no padrão do repositório, push direto em `main` (fast-forward). Se `origin/main` avançou, fazer `fetch` + `rebase` e revalidar o escopo.
- **Pacote que altera somente o PluginUI (P1):** após a verificação aprovada, fazer o deploy canônico em `srv-api` (`operador@192.168.1.237`, `~/projetos/delpi-central`):
  - PROD: `git pull --ff-only` + `./infra/scripts/up-prod-sequential.sh --build plugin-ui`.
  - HML: em `/home/operador/projetos-teste/delpi-central`, `git pull --ff-only` + `./infra/scripts/up-hml-sequential.sh --build plugin-ui`.

  Esse pacote **não** contém nada da Pesquisa, por isso segue a regra geral de deploy. O solicitante acompanha no catálogo do PluginUI em `/apps/plugin-ui`.
- **Pacotes que alteram o Comercial (P2 em diante):** **somente HML** (`up-hml-sequential.sh --build <serviço do Comercial confirmado no inventário do P1>`).
  - Proibido deploy em PROD do Comercial com estas alterações, conforme a exceção do `AGENTS.md` e o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026).
  - Se um deploy de PROD de outra frente puder levar estas alterações, registrar no relatório (as páginas continuam bloqueadas pelo gate `COMMERCIAL_SATISFACTION_SURVEY_ENABLED=false`). Se não for possível garantir isso, parar e reportar.
- Após o deploy, conferir:
  - que o container subiu;
  - que o remote carrega;
  - que a página ou o catálogo abre sem erro no console;
  - que um MFE existente que usa o PluginUI não regrediu.

### 1.5 Relatório final (EXECUTION REPORT)

O relatório traz, nesta ordem:

- HEAD inicial e final, e os commits.
- Arquivos criados e alterados.
- O que foi entregue × critérios de aceite, um por linha, com evidência.
- Testes e auditorias executados, com resultado.
- Veredito do verificador **sem edição** e a tabela de rodadas.
- Deploy executado: ambiente, comando e resultado.
- Onde ver o resultado, com capturas nos temas claro e escuro.
- Riscos, desvios e pendências.

---

## 2. Pacote P1 — Inventário técnico e campo de texto com marcadores destacados (PluginUI)

**Fases do plano:** 0 (somente o inventário técnico) e 1. **Pré-requisito:** nenhum. **Decisão de origem:** D3, aprovada em 18/11/2026.

### 2.1 Objetivo

1. Levantar os fatos técnicos de que os próximos pacotes dependem. A reescrita da UI-02 como especificação vigente é da coordenação e **não** faz parte deste pacote.
2. Criar no PluginUI um **campo de texto com marcadores destacados**, genérico, em versões de uma linha e de várias linhas, visível no catálogo nos temas claro e escuro.

   No Comercial ele vai ser usado depois (P4) no Assunto e na Mensagem do convite, para destacar `{nome_empresa}` e `{link_pesquisa}`. **Neste pacote o Comercial não é alterado.**

### 2.2 Inventário (sem código; registrar no relatório, item por item, com arquivo e linha)

| # | Pergunta | Para que serve |
|---|---|---|
| I1 | Quais componentes do kit e do `commercialUi` cada tela da Pesquisa usa hoje (`SatisfactionSurveysPage`, `SatisfactionCampaignDetailPage` e suas três abas, `SatisfactionRecipientDetailPage`) | Base dos P2–P5 |
| I2 | Como Clientes mostra “Atualizado em” (`cm-customers-page__freshness`): é só composição com CSS da página? Reaproveitar na Pesquisa exigiria copiar CSS? Existe algo equivalente no kit? | Decidir se o P2 compõe igual ou se precisa de peça no kit |
| I3 | `CommercialDataTableSection`: todas as colunas podem ser ordenáveis? A visão em cards oferece “Ordenar por”? Como Clientes faz? | Ajuste 5 |
| I4 | `CommercialPageHero`: `highlights` aceita os quatro números da campanha e o estado de carregamento? Como ficam em 360 px? | Ajuste 8 |
| I5 | Padrão de parâmetro na URL do Comercial (`utils/*DeepLink.ts`, `app/pluginNavigation.ts`, `app/pluginRoutes.ts`): como ler e gravar `?tab=` sem quebrar a trilha, o retorno e o “voltar” do navegador | D1, ajuste 15 |
| I6 | Valor real de `questionnaire_version` nas campanhas de HML (somente leitura, pela tela ou por uma chamada GET da API autenticada já usada pela página): é data, número ou texto? | D2, ajuste 13 |
| I7 | Nome do serviço do Comercial nos scripts `up-hml-sequential.sh`/`up-prod-sequential.sh` e se o MFE do Comercial em PROD é reconstruído por deploys de outras frentes | Deploy dos P2 em diante e risco de exposição |
| I8 | Se `TextField`/`TextAreaField` repassam `aria-*` ao campo nativo (resíduo R7 da UI-03) | Acessibilidade do componente novo |

### 2.3 Componente — requisitos

Nome proposto: `TokenHighlightField`, com fábrica `createDashboardTokenHighlightField({ prefix })` no mesmo padrão de `createDashboardTextField`/`createDashboardTextAreaField`. Ajustar o nome ao padrão do kit sem mudar a responsabilidade, e declarar antes de codificar.

- **Propriedades mínimas:**

  | Grupo | Propriedades |
  |---|---|
  | Campo | `id`, `label`, `hint?`, `error?`, `value`, `onChange(value)` |
  | Marcadores | `tokens: readonly string[]`, ex.: `["{nome_empresa}", "{link_pesquisa}"]` |
  | Formato | `multiline?: boolean`, `rows?` |
  | Estado | `disabled?`, `fullWidth?` |
  | Repasse | `aria-*` e `inputRef` ou equivalente, para o host inserir um marcador na posição do cursor (como faz hoje o `insertTokenAtSelection` da Pesquisa) |

- **Texto em campo nativo** (`input`/`textarea`). Cursor, seleção, colar, desfazer, corretor, teclado e leitor de tela funcionam como num campo comum.
  - O destaque é uma camada visual atrás do texto, alinhada caractere a caractere: mesma fonte, espaçamento, quebra de linha e rolagem.
  - Proibido `contenteditable`.
- **Destaque:** cada ocorrência exata de um item de `tokens` aparece como etiqueta, com fundo e borda por tokens do kit nos dois temas.
  - Texto fora da lista não é destacado.
  - Marcador parcial ou com erro de digitação (ex.: `{nome_empresaa}`) não é destacado.
  - O destaque não muda a largura do texto; nada de `padding` horizontal que desalinhe o cursor.
- **Aparência igual** à de `TextField`/`TextAreaField` (`FormFieldShell`): rótulo, dica, erro, foco, desabilitado. Ele deve parecer o mesmo campo, só com os destaques.
- **Rolagem:** em várias linhas, a camada acompanha a rolagem do `textarea`. Redimensionar a janela mantém o alinhamento.
- **Sem textos fixos em português** e sem nada da Pesquisa. A demo do catálogo usa marcadores e textos de exemplo neutros, como `{cliente}` e `{data}`.

### 2.4 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/forms/TokenHighlightField.tsx` (novo) + teste | Componente e fábrica |
| `plugins/plugin-ui/src/styles/` (arquivo novo de estilo do componente, ou o arquivo de campos existente se for o padrão) + `src/styles.css` (uma linha de `@import`, se arquivo novo) | Estilos e tokens claro/escuro |
| `plugins/plugin-ui/src/components/forms/index.ts` e `src/index.ts` | Exportar |
| `plugins/plugin-ui/src/catalog/visualComponents.ts` (`addedAt: "2026-11-18"`), `componentRegistry.tsx`, `demos/forms.tsx` | Inventário e demo |
| `plugins/plugin-ui/docs/component-catalog.md` e `export-catalog.md` | Documentar |

Qualquer outro arquivo, inclusive no Comercial, está fora do escopo.

### 2.5 Invariantes

- Nenhuma alteração visual ou de comportamento em `TextField`, `TextAreaField`, `FormFieldShell` ou em qualquer componente existente. Se o componente novo precisar de algo deles, **parar e reportar**.
- Nenhum seletor global; nenhum `!important`; nenhuma cor fora dos tokens.
- Trocar de tema muda só cores (mesma regra do P6.2 da UI-03).
- Sem texto em português fixo e sem nada da Pesquisa no kit.

### 2.6 Testes mínimos

1. Renderiza o campo nativo correto: `input` sem `multiline`, `textarea` com `multiline`. O rótulo fica ligado pelo `id`.
2. Digitar e colar chamam `onChange` com o valor exato; o destaque acompanha o novo valor.
3. Somente ocorrências exatas da lista são destacadas, incluindo várias ocorrências e marcador no início e no fim do texto. Marcador parcial e fora da lista não são destacados.
4. A camada de destaque fica oculta para leitor de tela (`aria-hidden="true"`); o campo nativo mantém o nome acessível. `aria-*` e `inputRef` são repassados.
5. `disabled` e `error` se comportam como em `TextAreaField`.
6. Valor vazio e `tokens` vazio não quebram.
7. Teste de contrato do CSS: tokens definidos nos dois temas; nenhum seletor global e nenhum `!important`; o bloco do tema escuro não muda geometria.
8. `componentRegistry.test.ts` continua cobrindo todos os exports visuais.

### 2.7 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| A1 | Inventário I1–I8 respondido com arquivo e linha | Seção no relatório |
| A2 | Destaque alinhado ao texto em uma e em várias linhas, com rolagem, nos dois temas, em 375 px e 1280 px | Demo no catálogo + capturas no relatório |
| A3 | Campo se comporta como nativo: cursor, seleção, colar, desfazer, teclado | Testes 1–3 + verificação manual descrita |
| A4 | Acessibilidade: camada oculta ao leitor de tela, nome acessível, `aria-*` repassados | Teste 4 |
| A5 | Componentes existentes sem mudança; zero CSS fora do PluginUI; sem seletor global | Diff + auditorias de §1.3 sem item novo |
| A6 | Build do remote e `verify-host-exports` ok; catálogo abre em PROD e HML em `/apps/plugin-ui` sem erro | Saída do build + verificação pós-deploy |
| A7 | Nenhuma regressão em MFE existente | Conferência de pelo menos um MFE após o deploy |
| A8 | Verificador independente aprovado | Veredito sem edição |
