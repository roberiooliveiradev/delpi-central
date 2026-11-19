# UI-02 — Pedidos de execução para o Devin (pacotes)

> **Estado:** registro vivo dos pedidos de execução do [plano da UI-02](./UI-02-PLANO-IMPLEMENTACAO.md), que refaz o visual das páginas internas da Pesquisa no Portal Comercial. Um pacote por vez: o próximo só é gerado depois que o anterior for **verificado e aceito** pelo solicitante.
> **Como usar:** o solicitante cola no Devin o **mini prompt** do pacote, fornecido no chat do projeto. O mini prompt manda o Devin ler este arquivo, aplicar o **Protocolo comum (§1)** e executar **somente** o pacote indicado.
> **Referência visual:** maquete aprovada em 18/11/2026 — <https://claude.ai/artifact/7sw5awGxjUydGU7MhzuRUk> (seis telas, tema escuro). O catálogo de mudanças está na [§4 do plano](./UI-02-PLANO-IMPLEMENTACAO.md#4-catálogo-de-mudanças-o-que-muda-em-cada-tela).

## Situação dos pacotes

| Pacote | Fases do plano | Conteúdo | Deploy | Estado |
|---|---|---|---|---|
| **P1** | 0 (inventário) + 1 | Inventário técnico + campo de texto com marcadores destacados no PluginUI (D3) | PluginUI: **PROD e HML** (componente genérico) | **ACEITO COM RESÍDUOS** — commit `52eecc38e0`, deploy PROD e HML em 18/11/2026; verificação r3 dispensada pelo solicitante (ver §4) |
| **P2** | 2 | Lista de campanhas (ajustes 1–5) | Comercial: **somente HML** | **ACEITO COM RESÍDUOS** — commit `243c463652`, HML em 19/11/2026 (ver §5.8) |
| **P3a** | 3 (parte do kit) | Números do bloco de título acompanham a quantidade (4 numa linha) no PluginUI | PluginUI: **PROD e HML** (componente genérico) | **A executar** (ver §6) |
| P3b | 3 | Detalhe da campanha: bloco de título, abas no endereço, Participantes (4, 6–9, 15) | Comercial: **somente HML** | A executar depois do aceite do P3a (ver §7) |
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

### 2.8 Ajustes obrigatórios da revisão da declaração (18/11/2026)

A declaração foi aprovada. Os ajustes abaixo fazem parte do pacote.

1. **O controle transparente não pode perder estados.** Ao deixar o fundo do campo nativo transparente, a camada de trás passa a desenhar o fundo dos estados normal, foco, desabilitado e erro, com os mesmos tokens de `native-controls.css`. O seletor deve ser escopado à classe do componente novo, com especificidade suficiente e sem `!important`. O campo desabilitado precisa ficar visualmente igual a um `TextAreaField` desabilitado.
2. **Espelho tipográfico completo.** A camada copia do controle `font-family`, `font-size`, `font-weight`, `line-height`, `letter-spacing`, `text-transform`, `tab-size`, `word-spacing`, `box-sizing`, as bordas internas e as regras de quebra:
   - várias linhas: `white-space: pre-wrap` e `overflow-wrap: break-word`, igual ao `textarea`;
   - uma linha: `white-space: pre`, com rolagem horizontal sincronizada.

   Quando o texto termina em quebra de linha, a camada recebe um espaço final, para a última linha não perder altura.
3. **Sem `ResizeObserver` ou `matchMedia`** (ambiente de teste e navegadores antigos), o componente funciona sem quebrar. O alinhamento por rolagem continua, e o redimensionamento é recalculado em `onScroll`, `onInput` e `resize` da janela.
4. **`placeholder`** continua visível com o campo vazio, sem ficar escondido pela camada.
5. **Modo de alto contraste** (`@media (forced-colors: active)`): o destaque usa contorno (`outline`) em vez de fundo, para não sumir.
6. **Ordem da camada:** o texto real e o cursor ficam sempre por cima. Nenhum clique ou seleção pode cair na camada (`pointer-events: none`), inclusive com zoom de 200%.
7. **Mesma interface de erro dos campos existentes.** Se `TextField`/`TextAreaField` não têm `error`, o `error?` do componente novo segue o padrão já usado no kit para mensagem de erro de campo: `aria-invalid`, `aria-describedby` e a classe de perigo existente. Não inventar estilo novo.
8. **R7 (falta de repasse de `aria-*` em `TextField`/`TextAreaField`) continua fora deste pacote.** Não alterar esses componentes.
9. **No relatório, uma captura com zoom** mostrando o cursor posicionado logo depois de um marcador destacado, em uma linha e em várias linhas, nos dois temas.

---

## 3. Revisão da declaração do P1 e conclusões do inventário (18/11/2026)

**Veredito da declaração:** ACCEPT_WITH_ADJUSTMENTS. O escopo e o desenho estão corretos e seguem o plano: campo nativo, camada `aria-hidden`, `<mark>` sem largura extra, segmentação pura, `inputRef`. Os ajustes estão em §2.8.

**Reancoragem:** HEAD inicial `69e6bc7f0c`. O working tree principal tem alterações de terceiros; elas devem ficar intocadas, e o commit leva só o escopo. O arquivo `119-eva-…` foi conferido byte a byte com o remoto (sha256 idêntico) e não deve entrar no commit.

**Conclusões do inventário para os próximos pacotes:**

| # | Fato confirmado | Consequência |
|---|---|---|
| I2 | “Atualizado em” de Clientes é composição da página (`CustomersPage.tsx:389–391`, cerca de 6 linhas em `customers.css:248`, `formatUpdatedAt` local). Não existe no kit | P2: reaproveitar como composição. Se a mesma regra de CSS for copiada para a Pesquisa, ela passa a existir em dois lugares: decidir no P2 entre um utilitário de página compartilhado do Comercial e uma peça do kit |
| I3 | **Corrigido (OC-3 do verificador, 18/11/2026).** `DataTable` aceita `sortable` por coluna (`plugin-ui/.../DataTable.tsx:70`) e a Section aceita `serverSort`/`onSortChange` (`DataTableSection.tsx:74–77,170`). `CommercialDataCardsSortBar` (`commercialUi.ts:268`) **é usada** em Clientes na visão em cards (`features/customers/components/CustomersTable.tsx:441`) e em Pedidos em aberto (`components/OpenOrdersTable.tsx:588`). As páginas da Pesquisa **não ordenam nada hoje** (zero `sortable`/`onSort`/`SortBar`) | P2: ligar a ordenação por cabeçalho e a barra “Ordenar por” nos cards, copiando o molde de `CustomersTable.tsx`, sem componente novo |
| I4 | `highlights` do `PageHero` usa grade de 3 colunas (`page-hero.css:112`): **4 números ficam 3 + 1** no computador | **Ponto a decidir no P3:** a maquete mostra os 4 números numa linha. É preciso ajustar o kit para a grade acompanhar a quantidade de números, sem mudar páginas com 3 números, como Minha Carteira |
| I5 | Padrão `parse…DeepLink`/`build…Search` + `navigatePluginPath` com `pushState`/`replaceState` | P3: `?tab=` nesse molde; trocar de aba usa `pushState`, para o voltar do navegador funcionar |
| I6 | `questionnaire_version` = `delpi.commercial.satisfaction-survey.canonical-15@2026-11-11` | D2 fechado: mostrar “Questionário oficial — versão de 11/11/2026”, extraindo a data do sufixo `@AAAA-MM-DD`. Sem sufixo válido, mostrar “Questionário oficial” sem data. O identificador técnico não aparece na tela |
| I7 | Serviço `commercial` (MFE). Deploy de outra frente reconstrói o MFE em PROD | Risco igual ao R20 da UI-03, mitigado pelo gate `COMMERCIAL_SATISFACTION_SURVEY_ENABLED=false`. Registrar em cada relatório do P2 ao P6 |
| I8 | `TextField`/`TextAreaField` não repassam `aria-*` nem `ref` (R7). `NativeText*Control` repassam | O componente novo deve repassar. No P4, o `CampaignMessageTab` passa a usar `inputRef` no lugar de `document.getElementById` |

---

## 4. Revisão do relatório do P1 (18/11/2026)

**Veredito:** ACCEPT_WITH_RESIDUAL.

**Conferido no repositório pelo coordenador:**

- O commit `52eecc38e0` é ancestral de `origin/main` e contém exatamente os 9 arquivos do §2.4 (945 inserções).
- `TextField`, `TextAreaField`, `FormFieldShell`, `Native*` e o Comercial não têm alteração.
- As seções §2.8 e §3 deste arquivo estão íntegras no HEAD. A versão local sem elas, na pasta de trabalho do executor, não foi publicada.

**Ajustes da §2.8 no código:**

| # | Ajuste | Situação | Evidência no código |
|---|---|---|---|
| 1 | Estados do campo | OK | A camada desenha o fundo normal, desabilitado (88% e `.55`) e somente leitura (92%) com as mesmas fórmulas de `native-controls.css:79,84`. Foco e erro não mudam o fundo do controle nativo: só borda e sombra, que continuam com o controle. Seletores escopados, sem `!important` |
| 2 | Espelho tipográfico | OK | Métricas copiadas do estilo computado do controle (fonte, espaçamentos, `tab-size`, quebra, `box-sizing`, paddings, bordas). Linha única com `pre`, várias linhas com `pre-wrap`. Espaço final após quebra de linha |
| 3 | Sem `ResizeObserver` | OK | Sincroniza em `useLayoutEffect`, `onScroll`, `onPointerUp` (cobre arrastar a alça do `textarea`) e `resize` da janela |
| 4 | Placeholder | OK | O controle é transparente e continua por cima |
| 5 | Alto contraste | OK | `forced-colors` usa `outline: MarkText` |
| 6 | Ordem das camadas | OK | Camada com `pointer-events: none` e `user-select: none`; controle com `position: relative` por cima |
| 7 | Erro | OK | `aria-invalid`, `aria-describedby` e `role="alert"`. O kit não tem classe única de erro de campo (cada componente tem a sua, ex.: `audio-recorder__error`). A classe própria só usa `--delpi-ui-danger` |
| 8 | R7 | OK | Fora do escopo; não alterado |
| 9 | Captura do cursor | Parcial | O navegador sem tela não desenha o cursor. A posição foi comprovada por `selectionEnd` medido e por capturas de seleção |

O tema escuro segue o padrão do kit (`:root[data-theme="dark"] .delpi-ui-…`, 23 arquivos) e só troca cores.

**Resíduos:**

| ID | Resíduo | Tratamento |
|---|---|---|
| R1 | `__stack` redeclara as métricas de `native-controls.css` (13 px, 8/12 px, raio 10 px) como valor de primeiro desenho. Se `native-controls.css` mudar, o primeiro desenho diverge até a sincronização por JS | Baixo. Corrigir se um pacote futuro tocar o componente |
| R2 | Verificação r3 dispensada pelo solicitante (AC-15, só documental) | Registrado. Os ACs de código passaram na r2 |
| R3 | Cursor não capturado em imagem (limitação do navegador sem tela) | Conferir visualmente no uso real, no P4 (Mensagem padrão em HML) |
| R4 | O catálogo `plugin-ui` não está registrado nos apps de HML (problema anterior a este pacote) | Acompanhar o componente no catálogo de PROD (`/apps/plugin-ui`) |
| R5 | A pasta de trabalho do executor tem versões locais de `UI-02-PROMPTS-DEVIN.md` e `README.md` diferentes do HEAD | Nunca publicar. Cada pacote confere `git diff --cached --stat` antes do commit |
| R6 | **Ocorrido:** o commit `40caeb143` (outra frente, TOTVS G2-B2) publicou a versão local antiga do `README.md` desta pasta e desfez a linha do plano da UI-02 | Linha restaurada pela coordenação em 18/11/2026. Outras frentes afetadas por esse commit não foram tocadas e devem ser avisadas ao solicitante |
| R7 | **Ocorrido de novo:** o commit `fc46a3fba` (outra frente, Controladoria CF-004-R4) publicou a versão local antiga deste arquivo e apagou a §4 (revisão do P1) | §4 restaurada pela coordenação em 18/11/2026. **A pasta de trabalho do executor precisa ser alinhada ao HEAD** nos arquivos desta pasta, com autorização do solicitante |

---

## 5. Pacote P2 — Lista de campanhas (ajustes 1–5)

**Fase do plano:** 2. **Pré-requisitos:** P1 aceito; [UI-02 vigente](./UI-02-CONFIGURACAO-PESQUISAS.md) de 18/11/2026. **Especificação desta tela:** UI-02 §3.1, §5, §6 (só as chaves da lista) e §7. **Maquete:** telas 1 (tabela) e 2 (cards).

### 5.1 Objetivo

Refazer a composição da página `SatisfactionSurveysPage` para ficar igual às telas 1 e 2 da maquete, nos temas claro e escuro.

- Comportamento, API, filtros, criação de campanha e navegação ficam iguais.
- Detalhe da campanha e participante ficam para o P3 em diante.

### 5.2 Entregáveis

1. **Bloco de título** (UI-02 §3.1 item 2):
   - etiqueta `eyebrow` “MARKETING · PESQUISA DE SATISFAÇÃO”, título e descrição atuais;
   - em `actions`, “Atualizado em dd/mm/aaaa, hh:mm” (com “· Atualizando…” durante a recarga, `aria-live="polite"`), Atualizar e Nova campanha;
   - os filtros continuam no corpo do bloco.

   **“Atualizado em”** (conclusão do I2): é a hora da última carga com sucesso da lista.
   - Compor com o que já existe, sem CSS novo de texto. Primeiro tentar uma tipografia ou componente de texto secundário que o kit ou o `commercialUi` já tenha.
   - Se só for possível copiando a regra de `customers.css:248`, **parar e declarar** antes de copiar. A alternativa seria mover a regra para um utilitário compartilhado de página do Comercial, e isso toca Clientes.
2. **Sem o aviso “Escopo parcial”** na lista.
   - Remover o `CommercialStateBanner` da lista.
   - **Não remover** a chave `list.partialScope` ainda, porque o detalhe da campanha a usa. Ela sai no P3.
3. **Ordenação na tabela:** todas as colunas com `sortable` (ajuste 5).

   | Coluna | Critério |
   |---|---|
   | Campanha / período | Nome, com `localeCompare` em `pt-BR` |
   | Situação | Ordem do ciclo: Agendada → Aberta → Encerrada |
   | Participantes, Respostas | Valor numérico |
   | Taxa de resposta | Valor numérico, com vazio sempre no fim |

   - Sem ordenação escolhida, a ordem é a que a API devolve (a de hoje).
   - A ordenação se aplica sobre o resultado dos filtros, com a paginação atual.
4. **Visão em cards:**
   - barra **“Ordenar por”** com `CommercialDataCardsSortBar` + `CommercialSelectField` + direção, copiando o molde de `features/customers/components/CustomersTable.tsx:441`, com os mesmos critérios e o mesmo estado da tabela (trocar de visão mantém a ordenação);
   - no card: nome como título, selo de situação no topo, campo **“Período”** (hoje o rótulo repete “Campanha / período”, ajuste 1) e os três números.
5. **Textos** em `content/satisfactionSurveysContent.ts` (UI-02 §6): `list.eyebrow`, `updatedAt(data)` (ou nome equivalente, sem texto fixo no componente), `list.cardPeriod`, `list.sortBy` e os rótulos de direção, se o molde de Clientes usar. As dicas novas vão em `CM_HELP.satisfactionSurveys` (`helpTooltips.ts`), no padrão das existentes.
6. **Taxa de resposta** sem mudança de formato (UI-02 §3.1).

### 5.3 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/commercial/src/features/satisfaction-surveys/SatisfactionSurveysPage.tsx` | Composição |
| `plugins/commercial/src/features/satisfaction-surveys/satisfactionFilters.ts` ou um arquivo novo `satisfactionSort.ts` na mesma pasta | Ordenação pura e testável |
| `plugins/commercial/src/features/satisfaction-surveys/satisfactionDates.ts` | Formatação de “Atualizado em”, se não houver utilitário compartilhado do Comercial para reaproveitar |
| `plugins/commercial/src/content/satisfactionSurveysContent.ts`, `plugins/commercial/src/content/helpTooltips.ts` | Textos e dicas |
| `plugins/commercial/src/features/satisfaction-surveys/satisfactionSurveys.test.ts`, `satisfactionSurveys.structural.test.mjs` | Testes |
| `plugins/commercial/src/styles/satisfaction.css` | Só se faltar layout de página; sem cor literal |

Qualquer outro arquivo, inclusive no PluginUI e em Clientes, está fora do escopo e exige parar e declarar.

### 5.4 Invariantes

- Mesmas chamadas de API, filtros, preferências de tabela (`viewLayoutPreferencesKey`, `columnPreferencesKey`, `fontSizePreferencesKey` sem mudar de nome), diálogo Nova campanha e navegação para a campanha.
- Nenhuma alteração em outras páginas do Comercial nem no PluginUI.
- Sem cor literal nova; troca de tema muda só cores.
- Sem “Ver resultados” nem “Respostas por empresa” (Q24).

### 5.5 Testes mínimos

1. A ordenação pura ordena cada coluna nos dois sentidos, com a regra de Situação, `pt-BR` no nome e vazio no fim na taxa. Sem chave, a ordem fica intacta.
2. A página renderiza a etiqueta e o título.
3. O aviso de escopo parcial não aparece na lista.
4. “Atualizado em” aparece depois da carga e “Atualizando…” durante a recarga.
5. Todas as colunas são ordenáveis; trocar de tabela para cards mantém a ordenação.
6. O card tem o nome como título e o rótulo “Período”.
7. Os testes existentes da Pesquisa continuam verdes sem afrouxar asserções.
8. O teste estrutural confirma que não há cor literal nova em `satisfaction.css`.

### 5.6 Critérios de aceite

| # | Critério | Evidência esperada |
|---|---|---|
| A1 | Telas 1 e 2 da maquete reproduzidas em 1280 px, 768 px e 360 px, nos temas claro e escuro | Capturas em HML no relatório |
| A2 | Ajustes 1–5 do plano entregues | Testes 2–6 + capturas |
| A3 | Comportamento preservado: filtros, criação de campanha, abertura da campanha, preferências | Testes existentes verdes + roteiro manual em HML (sem criar dados além de uma campanha de teste, se precisar) |
| A4 | Escopo respeitado e commit só dos arquivos do §5.3 (`git diff --cached --stat` no relatório) | Diff |
| A5 | Auditorias de §1.3 sem item novo; lint, testes e build do Comercial verdes | Saídas |
| A6 | Deploy **somente HML** do serviço `commercial`; risco de PROD do I7 registrado | Comando e resultado |
| A7 | Verificador independente aprovado | Veredito sem edição |

### 5.7 Revisão da declaração do P2 (18/11/2026)

**Veredito:** ACCEPT_WITH_ADJUSTMENTS.

**Decisão aceita:** sair de `CommercialDataTableSection` para a composição que Clientes e Pedidos em aberto já usam (`usePersistedViewLayout`, `CommercialDataListToolbar`, `CommercialDataTable`/`CommercialDataCardsGrid`, `CommercialDataCardsSortBar`, `CommercialPagination`).

- Motivo comprovado: a Section guarda a visão (tabela ou cards) e a ordenação em estado interno e não tem espaço para a barra “Ordenar por”.
- Mudar a Section no PluginUI ficaria fora do escopo e afetaria outras páginas.
- A Section usa o mesmo `useTableColumnVisibility` (`DataTableSection.tsx:9,489`), então as preferências salvas podem ser preservadas.

**Ajustes obrigatórios:**

1. **Preferências salvas.** Chamar `usePersistedViewLayout`, `useTableColumnVisibility` e `useTableFontSize` com **as mesmas chaves, as mesmas chaves de coluna e os mesmos padrões** que a Section usa hoje.
   - Teste: uma preferência gravada no formato atual (ex.: coluna “Respostas” oculta, visão em cards, fonte alterada) é lida corretamente pela página nova.
   - Se os formatos não forem iguais, parar e declarar.
2. **Comportamentos que a Section dava e agora são da página.** Testar cada um:
   - clique e Enter na linha abrem a campanha;
   - carregando, vazio e vazio por filtro com os mesmos textos;
   - paginação padrão 20 com `TABLE_PAGE_SIZE_OPTIONS`;
   - **voltar à página 1** ao mudar filtro, ordenação ou itens por página;
   - “Página X de Y · N registro(s)”;
   - colunas ocultas também somem nos cards, se a Section fazia isso hoje.
3. **“Atualizado em”:** usar `delpi-ui-section-hint-label` é aceito, porque já existe precedente em `OpenOrdersTable.tsx:553`. Se `CommercialSectionHintLabel` renderizar exatamente esse texto sem ícone de ajuda, preferir o componente. Nenhuma regra nova de CSS.
4. **Teste estrutural obsoleto.** Trocar a asserção que proíbe `response_rate` é uma mudança pedida pela especificação, não um afrouxamento de teste: a UI-02 vigente §3.1 exige a coluna Taxa de resposta, e a Q24 adia só “Ver resultados” e “Respostas por empresa”.
   - No pedido de verificação e no relatório, declarar como **“asserção alinhada à especificação vigente”**, com a citação.
   - A nova asserção deve **vetar** “Ver resultados”, “Respostas por empresa” e rotas da UI-01/UI-06 nesta página.
5. **Linha de base das falhas.** Listar no relatório, **pelo nome**, as 13 falhas `.mjs` antes e depois.
   - Depois do pacote: `satisfactionSurveys.structural.test.mjs` verde e **nenhuma falha nova**.
   - Se o “help coverage gate” mudar de conteúdo por causa das dicas novas, as dicas novas não podem aparecer na lista de falhas.
6. **Estado da ordenação** só em memória (sem `localStorage`), igual entre tabela e cards. Sem ordenação escolhida, a ordem é a do `filterCampaigns`.
7. **Commit:** mostrar `git diff --cached --stat` antes do commit e incluir no relatório. A pasta de documentação da Pesquisa não entra neste commit.

### 5.8 Revisão do relatório do P2 (19/11/2026)

**Veredito:** ACCEPT_WITH_RESIDUAL.

**Conferido pelo coordenador:**

- O commit `243c463652` é ancestral de `origin/main` e tem exatamente os 7 arquivos do §5.3.
- As chaves de preferência são as mesmas de antes (`SatisfactionSurveysPage.tsx:78–80`).
- A ordenação pura segue as regras (`satisfactionSort.ts`): situação pelo ciclo, nome em `pt-BR`, taxa vazia sempre no fim, sem chave mantém a ordem.
- Verificador `devin/swe-2-high`: r1 REWORK (cobertura de testes) e r2 **ACCEPT**, sem ordens de correção.
- As 12 falhas `.mjs` restantes são anteriores ao pacote e estão listadas pelo nome. O teste estrutural da Pesquisa voltou a ficar verde.

**Resíduos:**

| ID | Resíduo | Tratamento |
|---|---|---|
| R8 | A barra “Ordenar por” dos cards tem a opção extra “Período”. Na tabela, o período está junto da coluna Campanha / período | Aceito como desvio mínimo. Revisar na homologação final |
| R9 | **Mais um caso:** o commit `4be7b6948` (TOTVS G2-B2 r2) publicou a versão antiga deste arquivo e desfez a §5.7. Ela foi restaurada em `f803c27d3` | Mesmo problema do R6 e do R7. **Todo pacote, de qualquer frente, precisa conferir `git diff --cached --stat` antes do commit** |
| R10 | 12 falhas `.mjs` anteriores ao pacote no Comercial (lista no relatório do P2) | Fora desta frente. Avisar os responsáveis |
| R11 | O solicitante ainda não conferiu a lista em HML | Conferir junto com o P3b |
| R12 | **Adendo do executor (19/11/2026), com capturas em 1280, 768 e 360 px nos dois temas:** a paridade com as telas 1 e 2 está confirmada. Em 360 px, o título longo é cortado e sobram cerca de 24 px de rolagem lateral, porque “Atualizado em” e as ações da barra da tabela não quebram linha. **O mesmo acontece em Clientes** (`stackSW=326` nas duas): o problema vem do `PageHero`/`DataListToolbar` do PluginUI e do cabeçalho do Portal, e não foi introduzido pelo P2 | A UI-02 §7 exige 360 px sem cortes. **Tratar num pacote do PluginUI na fase 6 (P6-K)**, que corrige todas as páginas de uma vez, com conferência de Clientes antes e depois. O cabeçalho do Portal (shell) fica fora desta frente |

---

## 6. Pacote P3a — Números do bloco de título acompanham a quantidade (PluginUI)

**Fase do plano:** 3, parte do kit. **Origem:** inventário I4.

Hoje `.delpi-ui-page-hero__highlights` usa uma grade fixa de 3 colunas (`page-hero.css:112`), que vira 1 coluna abaixo de 900 px. Com os quatro números da campanha, eles ficam **3 + 1**, e a maquete mostra 4 numa linha.

### 6.1 Objetivo

Fazer a grade de números do `PageHero` **acompanhar a quantidade** quando houver **4** números, **sem mudar nada** nas páginas que usam 1, 2 ou 3 números. Elas são pelo menos 10 arquivos em `plugins/commercial` e `plugins/controllership-finance`.

### 6.2 Requisitos

| Itens | Computador (> 900 px) | 601–900 px | ≤ 600 px |
|---|---|---|---|
| 4 | **4 colunas** | **2 colunas** | 1 coluna |
| 1, 2, 3 ou 5+ | **igual a hoje** (3 colunas) | **igual a hoje** (1 coluna) | **igual a hoje** |

- Marcar a quantidade no elemento: atributo `data-highlight-count` ou modificador de classe no padrão `delpiUiClass` (declarar qual) e aplicar a regra só para 4.
- **Proibido** mudar a regra base de 3 colunas ou o `1fr` ≤ 900 px dos outros casos.
- `density="compact"` e as cores dos temas claro e escuro continuam iguais.
- O catálogo `/apps/plugin-ui` ganha a variação com 4 números na demo do `PageHero`.

### 6.3 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/plugin-ui/src/components/layout/PageHero.tsx` + teste | Marcar a quantidade |
| `plugins/plugin-ui/src/styles/page-hero.css` | Regras só para 4 |
| Demo do `PageHero` no catálogo (`src/catalog/demos/…`) | Variação com 4 |
| `plugins/plugin-ui/docs/component-catalog.md` | Uma linha sobre o comportamento |

### 6.4 Testes mínimos

1. Com 4 itens, o elemento recebe a marcação; com 1, 2, 3 e 5 itens, não recebe, e as classes ficam idênticas às de hoje.
2. Teste de contrato do CSS: a regra base (`repeat(3, …)` e `1fr` ≤ 900 px) continua igual. As regras novas só valem com a marcação de 4. Nenhum seletor global, nenhum `!important`.
3. Testes existentes do `PageHero` verdes sem mudança.

### 6.5 Critérios de aceite

| # | Critério | Evidência |
|---|---|---|
| A1 | 4 números numa linha no computador, 2 por linha entre 601 e 900 px, 1 por linha no celular, nos dois temas | Demo do catálogo + capturas |
| A2 | Nenhuma mudança visual nas páginas com 3 números: Minha Carteira, Clientes, Pedidos em aberto, Controladoria | Capturas antes e depois de pelo menos 2 delas + testes |
| A3 | Auditorias de §1.3 sem item novo; testes e build do PluginUI verdes | Saídas |
| A4 | Deploy `plugin-ui` em PROD e HML (§1.4); remote carrega; um MFE sem regressão | Resultado |
| A5 | Verificador independente aprovado | Veredito sem edição |

---

## 7. Pacote P3b — Detalhe da campanha: bloco de título, abas no endereço e Participantes (ajustes 4, 6–9 e 15)

**Fase do plano:** 3. **Pré-requisito:** P3a aceito e em HML. **Especificação desta tela:** UI-02 §3.2 (topo comum e aba Participantes), §5, §6 e §7. **Maquete:** tela 3.

### 7.1 Objetivo

Refazer a composição de `SatisfactionCampaignDetailPage` e `CampaignParticipantsTab` para ficarem iguais à tela 3 da maquete, nos dois temas.

- Inclusão de clientes, situação, navegação para o participante e chamadas de API ficam iguais.
- As abas Mensagem padrão e Dados ficam para o P4: neste pacote só passam a abrir pelo endereço.

### 7.2 Entregáveis

1. **Bloco de título** (UI-02 §3.2):
   - trilha;
   - etiqueta “MARKETING · PESQUISA DE SATISFAÇÃO”;
   - nome da campanha como título;
   - “Janela de resposta: {início} → {término}”;
   - em `actions`: “Atualizado em” (mesma composição e formatação do P2, `formatSurveyUpdatedAt` e `updatedAt`), selo de situação e Atualizar;
   - `highlights` com PARTICIPANTES, RESPONDIDAS, PENDENTES e TAXA DE RESPOSTA, vindos dos números que a página já recebe da API, com “—” enquanto carrega.
2. **Remover** a grade `cm-satisfaction-metrics` da aba (e as regras sem uso em `satisfaction.css`) e o aviso de escopo parcial do detalhe. A chave `list.partialScope` **sai do conteúdo** agora, se nada mais a usar.
3. **Aba no endereço (D1):**
   - função pura `parseCampaignTab(search)` / `buildCampaignTabSearch(tab)` no molde `parse…DeepLink`/`build…Search` (I5), aceitando `participants`, `message` e `data`;
   - sem valor ou com valor inválido, abre `participants`;
   - trocar de aba usa `navigatePluginPath` com **push**, para o “voltar” do navegador funcionar;
   - abrir uma URL com `?tab=` abre a aba certa;
   - voltar e avançar no navegador atualizam a aba;
   - a trilha e os links para o participante preservam o caminho da campanha.
4. **Aba Participantes:**
   - “Adicionar clientes” recolhível sem mudança de fluxo;
   - **um único quadro “Participantes”**, com os filtros Situação e Pesquisar participante **dentro**, de preferência por `toolbarFilters` e `embedded` da Section, se ficar igual à maquete (declarar a escolha);
   - barra da tabela;
   - **três colunas**:
     - Empresa: avatar + nome + “Código/loja …” com zeros preservados;
     - Contato: nome em cima e e-mail embaixo; “Sem contato” em tom secundário;
     - Situação.
   - todas `sortable` (Empresa pelo nome em `pt-BR`; Contato pelo nome, com vazio no fim; Situação Pendente → Respondida);
   - linha e card abrem o participante;
   - paginação.
5. **Textos** (UI-02 §6): `detail.metricParticipants` = “Participantes”, `detail.metricResponseRate` = “Taxa de resposta” e a etiqueta, reaproveitando `list.eyebrow` ou uma chave comum. Dicas novas em `CM_HELP.satisfactionSurveys`.

### 7.3 Escopo de arquivos permitido

| Arquivo | Ação |
|---|---|
| `plugins/commercial/src/features/satisfaction-surveys/SatisfactionCampaignDetailPage.tsx`, `CampaignParticipantsTab.tsx` | Composição |
| Arquivo novo `campaignTabDeepLink.ts` na pasta da Pesquisa (ou em `plugins/commercial/src/utils/`, seguindo o molde I5; declarar) | Aba no endereço |
| `satisfactionSort.ts` (participantes), `satisfactionDates.ts` | Funções puras |
| `plugins/commercial/src/content/satisfactionSurveysContent.ts`, `helpTooltips.ts` | Textos e dicas |
| `plugins/commercial/src/styles/satisfaction.css` | **Só remover** regras sem uso |
| `satisfactionSurveys.test.ts`, `satisfactionSurveys.structural.test.mjs` | Testes |

`app/pluginRoutes.ts` só pode mudar se a rota atual não aceitar `?tab=`. Nesse caso, parar e declarar.

### 7.4 Invariantes

- Mesmas chamadas de API, inclusão em lote e avisos flutuantes. Campanha encerrada continua sem inclusão.
- Preferências da tabela de participantes com as mesmas chaves.
- Sem coluna Ação nem botões na linha.
- Sem “Ver resultados” e sem “Respostas por empresa”.
- Sem cor literal nova; trocar de tema muda só cores.
- PluginUI sem mudança neste pacote (a mudança dele é o P3a).
- A pasta de documentação da Pesquisa fora do commit (`git diff --cached --stat` no relatório).

### 7.5 Testes mínimos

1. `parseCampaignTab` e `buildCampaignTabSearch`: os três valores, vazio, inválido, e preservação de outros parâmetros, se houver.
2. Abrir com `?tab=message` mostra a aba Mensagem; trocar de aba grava no endereço com push.
3. Os quatro números aparecem no bloco de título com os valores da API; “—” durante a carga; a grade antiga não existe mais.
4. Sem o aviso de escopo parcial no detalhe; a chave foi removida, se não tiver mais uso.
5. Um único quadro “Participantes” com os filtros dentro.
6. Contato em duas linhas e “Sem contato”.
7. Ordenação de cada coluna dos participantes.
8. Linha abre o participante; inclusão de clientes com o mesmo comportamento.
9. Lista de falhas `.mjs` antes e depois pelo nome, sem falha nova.

### 7.6 Critérios de aceite

| # | Critério | Evidência |
|---|---|---|
| A1 | Tela 3 da maquete reproduzida em 1280, 768 e 360 px, nos dois temas | Capturas em HML |
| A2 | Ajustes 4, 6–9 e 15 entregues | Testes + capturas |
| A3 | Atualizar a página e o “voltar” do navegador mantêm a aba | Roteiro em HML |
| A4 | Comportamento preservado na inclusão, na situação e na navegação | Testes existentes verdes + roteiro em HML **sem enviar respostas** |
| A5 | Escopo e commit só dos arquivos do §7.3 | `git diff --cached --stat` |
| A6 | Deploy **somente HML** (`commercial`); risco de PROD do I7 registrado | Resultado |
| A7 | Verificador independente aprovado | Veredito sem edição |
