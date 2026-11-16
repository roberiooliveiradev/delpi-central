# Página 03 — Formulário Público da Pesquisa (UI-03)

> **Estado:** ESPECIFICAÇÃO VIGENTE — padrão visual **APROVADO PELO SOLICITANTE EM 16/11/2026** (“é exatamente assim que eu quero o formulário para respostas”). Entrega 1.
> **Implementação:** existe uma versão funcional anterior em `plugins/public-hub/src/apps/commercial/` (commit `7d275ed2`, homologação desde 14/11/2026) com o **visual antigo**. Esta especificação exige **REWORK visual** dessa versão; regras funcionais e contratos de rede permanecem os mesmos.
> **Arquitetura de componentes (Q22, 16/11/2026):** todo o formulário é construído com componentes do **PluginUI** (`@delpi/plugin-ui`) — os que faltam são **criados no PluginUI** — e importado pelo `public-hub`. O kit é genérico, para ser reaproveitado em outros formulários. Ver §5.
> **Referência visual normativa:** [`UI-03-REFERENCIA-VISUAL.html`](./UI-03-REFERENCIA-VISUAL.html) (abrir no navegador; arquivo estático, sem lógica). Em caso de divergência, **este Markdown prevalece**.
> **Histórico:** a redação anterior deste documento (decisões de 11/11/2026) está no histórico do Git; as decisões substituídas e mantidas estão registradas em [BUSINESS-DECISIONS — Q21](./BUSINESS-DECISIONS.md#q21--padrão-visual-do-formulário-público-16112026). Não reabrir os pontos abaixo sem nova decisão do solicitante.

## 1. Resumo

| Item | Definição |
|---|---|
| Quem usa | Contato da empresa cliente convidada, **fora** do Portal, sem login. Canal principal: **celular**, a partir de link recebido por WhatsApp, Teams ou e-mail |
| Problema que resolve | Coletar uma resposta definitiva por empresa e campanha, com as 15 perguntas literais do plano Word, com baixo esforço e sem erro de preenchimento |
| Rota | `/p/commercial/form/{token}` no `plugins/public-hub` (página `commercial.form`) |
| Autoridade | `commercial-api` — valida token, janela, obrigatoriedade e unicidade; o frontend é só interface |
| Rede | `GET /public/satisfaction-surveys/{token}` e `POST /public/satisfaction-surveys/{token}/response` — **sem alteração de contrato** |
| Estilo | Formulário *clean* no padrão Microsoft Forms / Google Forms: fundo claro, faixa da marca no topo, uma pergunta por cartão branco, escalas numéricas simples |

## 2. Fluxo

```text
Abertura ──Começar──▶ Etapa 1/3 ──Avançar──▶ Etapa 2/3 ──Avançar──▶ Etapa 3/3 ──Revisar respostas──▶ Revisão
                      (perg. 1–5)            (perg. 6–10)           (perg. 11–15)                      │
                         ▲  Voltar              ▲  Voltar              ▲                                 │ Editar (por seção)
                         └──────────────────────┴──────────────────────┴─────────────────────────────────┘
Revisão ──Enviar respostas (único POST)──▶ Agradecimento
Estados alternativos (vindos da API): ainda não aberta · encerrada · resposta já registrada · link inválido · indisponível
```

- **Etapa 1:** perguntas 1–5 (Qualidade, Prazo de entrega, Atendimento, Agilidade, Comunicação).
- **Etapa 2:** perguntas 6–10 (Suporte técnico, Suporte comercial, Flexibilidade, Confiabilidade, Parceria).
- **Etapa 3:** pergunta 11 (Satisfação geral, 1–5), 12 (Recomendação, 0–10) e 13–15 (abertas, opcionais).
- Transições entre etapas, revisão e edição são **estado local**; nenhuma chamada de rede até **Enviar respostas**.

## 3. Padrão visual aprovado (16/11/2026)

### 3.1 Princípios

1. **Tema claro fixo.** O formulário não oferece alternância claro/escuro e não segue o tema do sistema operacional.
2. **Uma pergunta por cartão**, com o tema em letra pequena acima e a pergunta numerada com o **texto literal** do catálogo canônico.
3. **Escala numérica limpa:** só os números nos botões; o significado fica nas pontas (“1 · Muito insatisfeito” / “5 · Muito satisfeito”) e, depois da escolha, numa linha de confirmação (“Sua nota: 4 · Satisfeito”).
4. **“Não se aplica” discreto:** opção em formato de pílula com indicador redondo, abaixo da escala (celular) ou à direita após um divisor (computador). Nunca uma linha inteira com o mesmo peso das notas.
5. **Título público fixo:** “Pesquisa de Satisfação de Clientes”. O **nome interno da campanha não aparece** para o cliente.
6. **Ações sempre à mão no celular:** rodapé fixo com Voltar / Avançar.
7. Sem gradientes, sem ilustrações, sem emojis, sem estrelas.
8. **Tudo vem do PluginUI.** Nenhum componente visual é desenhado dentro do `public-hub`; a página só monta o formulário com o kit e aplica os tokens do tema claro (§5).

### 3.2 Tokens

Os valores abaixo são o **tema claro de referência do kit de formulário do PluginUI**: ficam como tokens do kit (`--delpi-ui-*` existentes ou novos `--delpi-ui-form-*`), com o CSS dos componentes em `plugins/plugin-ui/src/styles/`. O `public-hub` **só mapeia** esses tokens na raiz da página (a partir de `brand-tokens.css` quando houver equivalente) — nunca escreve CSS de componente.

| Token | Valor | Uso |
|---|---|---|
| Marca / primária | `#0c6fb0` (`--pub-accent` claro) | Faixa do topo, botão primário, nota selecionada, barra de progresso |
| Marca escura | `#0a5a8f` | Texto “Sua nota…”, texto de “Não se aplica” selecionado, hover do primário |
| Fundo da página | `#f3f4f6` | Abaixo da faixa |
| Cartão | `#ffffff`, borda `1px #e1e4e8`, raio `12px`, sombra `0 1px 2px rgba(16,24,40,.06)` | Todos os blocos |
| Texto principal | `#1f2328` | Perguntas, valores |
| Texto secundário | `#57606a` (contraste ≥ 4,5:1 sobre branco) | Rótulos, legendas, ajuda |
| Borda de controle | `#c4ccd5` | Botões de nota, “Não se aplica”, campos de texto |
| Fundo suave | `#eaf3fb` | Bloco da empresa na abertura; “Não se aplica” selecionado |
| Erro | `#b42318` | Asterisco de obrigatória, mensagens e borda do cartão pendente |
| Sucesso | `#1a7f37` | Círculo do agradecimento |
| Aviso | fundo `#fff8e6`, borda `#f0d58c`, texto `#5c4400` | Aviso de imutabilidade na revisão |
| Foco | contorno `3px #8fc3ea`, afastamento `2px` | Todo elemento interativo (`:focus-visible`) |
| Fonte | `'Segoe UI', Inter, system-ui, -apple-system, sans-serif` | Toda a página |

### 3.3 Estrutura da página

| Região | Celular (< 600 px) | Computador (≥ 600 px) |
|---|---|---|
| Faixa da marca | Altura 112 px (etapas/revisão) ou 168 px (abertura/agradecimento), cor primária, largura total | Altura 220 px |
| Coluna de conteúdo | Margem lateral 16 px; sobrepõe a faixa em 80 px (112 px na abertura) | Largura 760 px, centralizada; sobrepõe a faixa em 160 px |
| Espaço entre cartões | 12 px | 16 px |
| Padding do cartão | 20 px | 28 px vertical / 32 px horizontal |
| Rodapé de ações | **Fixo** na base (`position: sticky`), fundo branco, borda superior e sombra leve; botão primário ocupa a largura restante | No fim da coluna, alinhado à direita; mensagem de pendência à esquerda |

**Cabeçalho das etapas (cartão superior):** logo Minha Delpi (34 px de altura no celular, 44 px no computador) · título “Pesquisa de Satisfação de Clientes” (20 px / 28 px, negrito) · “Respondendo por **{empresa}**” · divisor · linha “Etapa N de 3 · {nome da etapa}” com “X de 12” à direita · barra de progresso (6 px, raio 3 px). No computador, “Responda até {data}” aparece à direita do logo.

**Logo:** o shell público atual desenha logo e botão de tema próprios. Para esta página, **o shell não deve desenhar logo nem botão de tema**; o logo entra dentro do cartão do cabeçalho (ver §5).

### 3.4 Componentes do formulário

**Cartão de pergunta**
- Rótulo do tema: 12 px, maiúsculas, `letter-spacing .06em`, cor secundária (ex.: QUALIDADE).
- Pergunta: “{n}. {texto literal}” em 16 px (17 px no computador), peso 600, altura de linha 1,4; asterisco vermelho nas obrigatórias; “(opcional)” em cor secundária, peso normal, nas abertas.
- Semântica: `fieldset` com `legend`; cada opção com nome acessível completo (ex.: “4 — Satisfeito”).
- Pendente após tentativa de avançar: borda do cartão em vermelho + mensagem “Selecione uma nota ou “Não se aplica”.” (13 px, 600). Nas perguntas 11 e 12: “Selecione uma nota.”

**Escala 1–5 (perguntas 1–11)**
- Celular: grade de 5 colunas iguais, espaço 8 px, altura 48 px. Computador: botões de 64 × 52 px, espaço 10 px.
- Botão normal: fundo branco, borda `#c4ccd5`, raio 8 px, número 17–18 px peso 600. Selecionado: fundo e borda primária, número branco. `aria-pressed` (ou `radio` nativo estilizado) refletindo a seleção.
- Legenda das pontas abaixo da escala, 12–13 px, cor secundária: “1 · Muito insatisfeito” à esquerda e “5 · Muito satisfeito” à direita.
- Após escolha: “Sua nota: {n} · {significado}” (13–14 px, 600, marca escura). Significados: 1 Muito insatisfeito · 2 Insatisfeito · 3 Neutro · 4 Satisfeito · 5 Muito satisfeito.

**Não se aplica (perguntas 1–10 apenas)**
- Pílula de 44 px de altura (52 px no computador), raio total, padding 16 px, borda `#c4ccd5`, com indicador redondo de 18 px à esquerda.
- Selecionado: borda primária, fundo `#eaf3fb`, texto marca escura em 600, indicador preenchido (anel de 6 px na cor primária).
- Exclusivo com as notas do mesmo grupo: escolher nota desmarca N/A e vice-versa.
- Posição: abaixo da linha de confirmação no celular; à direita da escala, após divisor vertical de 1 px, no computador.

**Escala de recomendação 0–10 (pergunta 12)**
- Legenda **acima** da escala: “0 · Nada provável” à esquerda e “10 · Extremamente provável” à direita.
- Celular: grade de 6 colunas — 0 a 5 na primeira linha e 6 a 10 na segunda —, botões de 46 px de altura, espaço 8 px. Computador: uma linha com os 11 botões.
- Mesmo estilo de normal/selecionado da escala 1–5, **sem cores por faixa** (nada de vermelho/amarelo/verde), para não induzir a nota. `0` é resposta válida.
- Após escolha: “Sua nota: {n}”.

**Perguntas abertas (13–15)**
- Rótulo “Sua resposta” (13 px, secundário) ligado ao campo; `textarea` com altura mínima de 96 px, padding 12 px, borda `#c4ccd5`, raio 8 px, 15 px, redimensionável na vertical; texto de exemplo “Escreva sua resposta”.
- Sem contador de caracteres nesta entrega; o limite de tamanho continua o do backend e, se excedido, a mensagem de erro aparece no próprio cartão.

**Barra de progresso:** trilho `#e6eaef`, preenchimento primário, `role="progressbar"` com valor atual; texto “X de 12” (cabeçalho) e “12 de 12 avaliações obrigatórias concluídas” (revisão).

**Botões**
- Primário: altura 48 px, raio 8 px, fundo primário, texto branco 16 px peso 600; no celular ocupa a largura disponível no rodapé.
- Secundário: mesma altura, fundo branco, borda `#d0d7de`, texto principal.
- “Editar” da revisão: 36 px de altura, borda `#d0d7de`, texto primário com ícone de lápis; nome acessível “Editar etapa N”.
- Enquanto envia: primário desabilitado com texto “Enviando…”; nunca reenviar automaticamente.

### 3.5 Telas

| Tela | Conteúdo, de cima para baixo |
|---|---|
| **Abertura** | Faixa 168 px · cartão: logo (44 px) · rótulo “PESQUISA DE SATISFAÇÃO” · título “Pesquisa de Satisfação de Clientes” (26 px) · bloco suave “Respondendo em nome da empresa / **{empresa}**” · frase de propósito · lista com ícones de traço: “15 perguntas em 3 etapas, com revisão antes de enviar”, “Responda até **{data de término}**”, “Não pedimos seus dados pessoais” · botão **Começar** (largura total) · texto de privacidade (12 px) |
| **Etapas 1–3** | Cabeçalho com progresso · 5 cartões de pergunta · rodapé fixo: mensagem de pendência (se houver) e **Voltar** (etapas 2 e 3) / **Avançar** (etapas 1 e 2) ou **Revisar respostas** (etapa 3) |
| **Revisão** | Faixa 112 px · cartão: logo · “Revise suas respostas” · orientação · barra 100% · três cartões de seção (“Avaliação dos serviços — parte 1”, “— parte 2”, “Visão geral e comentários”), cada um com **Editar** e linhas “tema → valor” (“4 · Satisfeito”, “Não se aplica”, “9”; aberta vazia em itálico “Não respondida”; aberta preenchida em bloco abaixo do rótulo) · aviso amarelo “Depois de enviar, as respostas não poderão ser alteradas.” · rodapé **Voltar** / **Enviar respostas** |
| **Agradecimento** | Faixa 168 px · cartão centralizado: logo · círculo verde 72 px com ✓ · “Obrigado por participar!” · “Sua avaliação foi registrada. Ela ajuda a Delpi a melhorar produtos, serviços e o relacionamento com sua empresa.” · “Você já pode fechar esta página.” Sem resumo de notas, sem botões |
| **Estados alternativos** | Mesmo layout do agradecimento (faixa + cartão centralizado + logo), sem círculo verde; título e mensagem atuais de `SurveyStateView` mantidos; período exibido como “Período da pesquisa: dd/mm/aaaa a dd/mm/aaaa” quando aplicável; “Tentar novamente” só em indisponibilidade temporária. **Não exibir o nome interno da campanha** |

### 3.6 Textos (microcopy vigente)

| Lugar | Texto |
|---|---|
| Título público | Pesquisa de Satisfação de Clientes |
| Empresa (abertura) | Respondendo em nome da empresa · **{nome}** |
| Empresa (etapas) | Respondendo por **{nome}** |
| Propósito | Sua avaliação ajuda a Delpi a melhorar produtos, serviços e o relacionamento com sua empresa. |
| Prazo | Responda até **{dd/mm/aaaa}** (data de término no fuso America/Sao_Paulo, **sem hora**) |
| Botões | Começar · Avançar · Voltar · Revisar respostas · Editar · Enviar respostas · Enviando… · Tentar novamente |
| Pendência no rodapé | Falta 1 avaliação nesta etapa. / Faltam {n} avaliações nesta etapa. |
| Revisão | Revise suas respostas · Confira antes de enviar. Use “Editar” para corrigir uma etapa sem perder as demais respostas. |
| Aberta vazia na revisão | Não respondida |
| Privacidade | **PENDENTE:** texto a ser fornecido/validado pelo responsável LGPD. Até lá, não publicar declaração jurídica inventada; a frase “Não pedimos seus dados pessoais” é fato do produto e pode ser exibida |

**Empresa ausente:** se a API devolver `companyName` nulo, omitir o bloco/linha da empresa (não exibir “—” nem código/loja).

### 3.7 Responsividade e acessibilidade

- Ponto de quebra único em 600 px. Testar em 360, 375, 390, 768 e 1280 px de largura; **nenhuma palavra pode quebrar no meio** e não pode haver rolagem horizontal.
- Alvos de toque ≥ 44 × 44 px (exceto “Editar”, 36 px, com área clicável ampliada por padding).
- Teclado: Tab percorre as opções na ordem; Espaço/Enter seleciona; Enter **nunca** envia o formulário; foco vai para a primeira pendência ao tentar avançar.
- Leitor de tela: grupos com `legend`, opções com nome completo (“4 — Satisfeito”), progresso anunciado, mensagens de erro ligadas ao grupo (`aria-describedby`), estados terminais com `role="status"`/`"alert"`.
- Zoom de 200% sem perda de conteúdo.

## 4. Regras funcionais vigentes (inalteradas desde 11/11/2026)

1. **Obrigatoriedade:** cada dimensão (1–10) exige nota 1–5 **ou** “Não se aplica”; perguntas 11 e 12 exigem nota; 13–15 opcionais. Nenhuma opção vem pré-selecionada.
2. **Progresso:** `100 × avaliações obrigatórias respondidas ÷ 12`; comentários não contam; recalcular a cada mudança; 100% não significa enviado.
3. **Avanço por etapa:** Avançar/Revisar só com a etapa completa; senão marcar pendências, mostrar a contagem no rodapé e levar o foco à primeira.
4. **Revisão obrigatória** com **Editar** por seção, que leva direto à etapa e volta com **Voltar à revisão**, preservando todas as respostas.
5. **Envio único:** só “Enviar respostas” faz o POST; botão desabilitado enquanto envia, mas a unicidade é garantida pela API; conflito mostra “Resposta já registrada”, nunca falso sucesso.
6. **Agradecimento** somente após confirmação da API.
7. **Sem rascunho persistente:** respostas só na memória da página (nada em `localStorage`, `sessionStorage`, IndexedDB, cookie ou URL); aviso nativo de saída (`beforeunload`) enquanto houver respostas não enviadas, desligado após o envio ou em estado terminal.
8. **Privacidade:** nunca pedir nome, e-mail ou CPF do respondente; não exibir código/loja, token, dados internos, nome interno da campanha; sem rastreamento de terceiros.

## 5. Implementação — kit de formulário no PluginUI (Q22)

**Decisão (16/11/2026):** usar ou criar **todos** os componentes no PluginUI e importá-los no microfrontend; de preferência, o **formulário inteiro** (fluxo em etapas) é um componente do PluginUI, alimentado por uma definição de perguntas, para ser reaproveitado em **outros formulários e fluxos**.

### 5.1 Por que é viável (evidência no código, 16/11/2026)

| Fato | Evidência |
|---|---|
| O `public-hub` já consome o PluginUI em tempo de execução via Module Federation | `plugins/public-hub/vite.config.ts` (`pluginUiRemote()`); `customer-experience/FormPage.tsx` e `production-control` importam de `@delpi/plugin-ui/index` |
| A regra do repositório já manda o visual de componente para o kit | `.cursor/rules/plugins-reusable-components.mdc`: CSS de componente só em `plugins/plugin-ui/src/styles/**` (dual-class `prefixo` + `.delpi-ui-*`); o app mapeia tokens e faz layout de página; override novo falha em `MFE_PLUGIN_UI_OVERRIDE` |
| Já existem peças reaproveitáveis | `ActionButton`, `TextAreaField`/`FormFieldShell`, `StateBox`/`InfoStatePanel`, `JourneyProgressBar` (avaliar), `SegmentToggle` |
| Há um segundo formulário público candidato a reaproveitar o kit | `public-hub/src/apps/customer-experience/FormPage.tsx` (tipos: nota em estrelas, texto curto/longo, sim/não, escolha única/múltipla) — **não migrar nesta entrega** |
| Nomes propostos não colidem com exports atuais | Busca em `plugins/plugin-ui/src` por `QuestionCard`, `RatingScale`, `GuidedForm`… sem ocorrência (busca é descoberta, não prova absoluta) |

### 5.2 Camada 1 — componentes de apresentação (PluginUI)

Local sugerido: `plugins/plugin-ui/src/components/forms/questionnaire/` + CSS em `plugins/plugin-ui/src/styles/`. Nomes são **propostos**; o implementador pode ajustar ao padrão do kit, registrando no `component-catalog.md`/`export-catalog.md`.

| Componente | Responsabilidade | Contrato mínimo (props) |
|---|---|---|
| `FormPageLayout` | Faixa da marca + coluna central + espaçamento entre cartões (§3.3) | `band: "compact" \| "tall"`, `children` |
| `FormHeaderCard` | Logo, título, linha de contexto, metadado à direita, etapa e progresso | `logo`, `title`, `subtitle`, `meta?`, `stepLabel?`, `progress?: { done, total }` |
| `QuestionCard` | Cartão `fieldset` com rótulo do tema, pergunta numerada, obrigatória/opcional e erro | `number?`, `eyebrow?`, `prompt`, `required`, `optionalLabel?`, `error?`, `children` |
| `RatingScale` | Escala numérica genérica (serve 1–5 e 0–10) com legenda das pontas, confirmação da escolha e “Não se aplica” opcional | `min`, `max`, `value`, `onChange`, `valueLabels?` (ex.: 1→“Muito insatisfeito”), `endLabels`, `endLabelsPosition: "below" \| "above"`, `narrowColumns?` (ex.: 6 para 0–10), `selectionCaption?`, `notApplicable?: { label, selected, onSelect }`, `ariaLabel`, `invalid?` |
| (texto aberto) | Reusar `TextAreaField` do kit dentro de `QuestionCard`; se o visual não bater, ajustar **no kit** | — |
| `FormStepFooter` | Rodapé de ações: fixo em tela estreita, mensagem de pendência, Voltar/Avançar (via `ActionButton`) | `message?`, `back?: { label, onClick }`, `next: { label, onClick, busy? }` |
| `FormReviewSection` | Seção da revisão com título, botão Editar e linhas rótulo → valor | `title`, `onEdit`, `editLabel`, `rows: { label, value, muted?, block? }[]` |
| `FormResultPanel` | Tela final ou de estado (sucesso, informação, erro) centralizada | `tone`, `title`, `message`, `hint?`, `action?` |

### 5.3 Camada 2 — formulário guiado completo (PluginUI)

`GuidedQuestionnaire` (nome proposto): componente que monta **todo o fluxo** abertura → etapas → revisão → envio → resultado a partir de uma **definição declarativa**, usando só a camada 1.

| Entrada | Conteúdo |
|---|---|
| `intro` | título, empresa/contexto, frase, lista de itens, rótulo do botão de início, texto de rodapé |
| `steps[]` | `{ id, title, questions[] }`; cada questão: `{ key, kind: "scale" \| "text", number, eyebrow, prompt, required, scale?: { min, max, valueLabels, endLabels, endLabelsPosition, narrowColumns, notApplicable } }` |
| `texts` | microcopy (padrões em português de §3.6, sobrescrevíveis) |
| `onSubmit(answers)` | função do app; devolve o resultado (enviado, já registrado, erro…) para o kit exibir a tela certa |
| `renderResult?` | permite ao app escolher título/mensagem por resultado |

**Comportamento genérico do kit:** estado das respostas só em memória; validação de obrigatórias por etapa com foco na primeira pendência; progresso = obrigatórias respondidas ÷ total de obrigatórias; revisão com Editar por etapa e “Voltar à revisão”; Enter nunca envia; um envio por vez; aviso `beforeunload` enquanto houver respostas não enviadas; sem `localStorage`/`sessionStorage`/cookie/URL.

**Fica fora do kit (domínio):** as 15 perguntas e a divisão 5/5/5 (`surveyForm.ts`), as chamadas à `commercial-api` (`api.ts`), a tradução dos resultados da API em telas, regras de negócio e a validação final — que continua na `commercial-api`.

### 5.4 Camada 3 — página da Pesquisa no `public-hub`

| Arquivo | O que fica |
|---|---|
| `src/apps/commercial/FormPage.tsx` | Adaptador fino: converte o questionário da API na definição do `GuidedQuestionnaire`, passa `onSubmit` → `submitPublicSurvey`, mapeia resultados |
| `src/apps/commercial/SurveyStateView.tsx` | Usa `FormPageLayout` + `FormResultPanel`; remove o nome da campanha |
| `src/apps/commercial/form.css` | **Removido** ou reduzido a mapeamento de tokens `--delpi-ui-*` / layout de página; nenhum seletor de componente |
| `src/apps/commercial/pages.tsx` + `src/shell/` | Página sem botão de tema e sem logo do shell, com **tema claro forçado**. Menor solução: opção opcional na definição da página (ex.: `theme: "light"` e/ou `chrome` sem decoração), padrão inalterado para as demais apps |
| `surveyForm.ts`, `api.ts` | Mantidos (regra de etapas e rede) |

### 5.5 Ordem de execução sugerida e cuidados

1. **PluginUI:** camada 1 com testes e registro no catálogo; depois camada 2 com testes de comportamento (validação, foco, progresso, revisão, envio único, `beforeunload`, teclado).
2. **Publicação do remote do PluginUI em HML** e verificação de que o `public-hub` carrega os novos exports.
3. **public-hub:** adaptador da pesquisa + opção de tema/chrome no shell; remoção do CSS próprio.
4. **Verificar regressão** das demais páginas públicas e dos MFEs que usam o PluginUI (o kit é compartilhado).

- **Logo:** `/p/logoMinhaDelpi.svg`; em HML (16/11/2026) respondeu **403** — investigar `public-hub/nginx.conf`/gateway antes do aceite.
- **Exposição em produção:** o remote do PluginUI é compartilhado por todo o Portal. Componentes novos e inertes no PluginUI não expõem a pesquisa, mas **qualquer deploy do PluginUI em PROD** deve seguir a regra de ambientes da Pesquisa ([README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026)) e ser avaliado pelo owner; a página pública da pesquisa continua só em DEV/HML.
- **Reaproveitamento futuro (não nesta entrega):** migrar o formulário de Customer Experience para o kit (exige `ChoiceList` para escolha única/múltipla e decisão sobre estrelas × escala numérica) e eventual construtor de formulários por usuários — ambos precisam de decisão própria.

**Fora do escopo desta entrega:** contador de caracteres, rascunho salvo, tema escuro, personalização das perguntas, envio de convites, imagem na faixa, `ChoiceList`, migração do Customer Experience.

## 6. Estado observado em HML (16/11/2026) — gaps a corrigir

Observado no link de uma empresa pendente (sem envio de resposta).

| # | Gap | Origem |
|---|---|---|
| G1 | Logo do shell quebrado: `GET /p/logoMinhaDelpi.svg` → **403** | Observado (requisição no navegador) |
| G2 | No celular, rótulos das notas quebram no meio da palavra (“Insatisfeit/o”) | Observado em 375 px |
| G3 | “Não se aplica” ocupa linha inteira com o mesmo peso das notas | Observado |
| G4 | Perguntas sem nome do tema e sem separação; etapa vira um bloco contínuo | Observado |
| G5 | Recomendação 0–10 quebra 6+5 sem legenda 0/10 | Observado em 375 px |
| G6 | Abertura com informações soltas e prazo com hora (“01/11/2026 00:00 a 31/12/2026 23:59”) | Observado |
| G7 | Botão de tema sobrepõe o topo do conteúdo no celular | Observado |
| G8 | Nome interno da campanha exibido ao cliente (ex.: “HML - Validacao…”) | Observado |
| G9 | Link de convite usa o endereço interno de HML (`https://192.168.1.237:18443`), inacessível fora da rede | Observado; configuração `PUBLIC_BASE_URL` de HML. **Não é ajuste de tela**; requisito do gate de produção (endereço público acessível externamente) |

## 7. Critérios de aceite

1. Visual igual à [referência](./UI-03-REFERENCIA-VISUAL.html) nas seis telas, em celular (375 px) e computador (1280 px), em tema claro, sem botão de tema.
2. Gaps G1–G8 resolvidos; G9 registrado no plano de produção.
3. 15 perguntas com texto e ordem literais do catálogo; nenhuma seleção inicial.
4. Regras de §4 verificadas por testes automatizados e em HML, sem POST antes de “Enviar respostas”.
5. Acessibilidade de §3.7 verificada (teclado, leitor de tela, zoom 200%, alvos de toque).
6. Demais páginas públicas do `public-hub` e MFEs consumidores do PluginUI sem regressão visual (shell, tema e kit).
7. Formulário montado **só** com componentes exportados pelo PluginUI; nenhum CSS de componente no `public-hub` (auditorias `scripts/ci/audit_platform_guardrails.py --check --base` e `scripts/ci/audit_mfe_plugin_ui_css.py` sem item novo); componentes registrados no catálogo do kit com testes próprios.
8. Homologação visual pelo solicitante em HML; **nenhuma publicação em produção** sem o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026).
