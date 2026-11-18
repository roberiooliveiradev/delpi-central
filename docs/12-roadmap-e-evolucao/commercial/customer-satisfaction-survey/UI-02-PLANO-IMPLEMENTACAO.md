# UI-02 — Plano de implementação do novo visual das páginas internas da Pesquisa

> **Estado:** PLANO APROVADO em 18/11/2026 (D1–D3 aprovadas pelo solicitante). Pedidos de execução: [UI-02-PROMPTS-DEVIN.md](./UI-02-PROMPTS-DEVIN.md). Criado em 18/11/2026 sobre `main` em `f58b66022`; **revalidar HEAD, branch e working tree no início de cada fase.**
> **Referência visual aprovada como base:** maquete *Pesquisa de Satisfação — páginas internas do Portal (proposta)*, seis telas, tema escuro — <https://claude.ai/artifact/7sw5awGxjUydGU7MhzuRUk>.
> **Especificação que este plano implementa:** [UI-02-CONFIGURACAO-PESQUISAS.md](./UI-02-CONFIGURACAO-PESQUISAS.md). Ela será **reescrita como especificação vigente** na fase 0, antes de qualquer código; o histórico de decisões vai para o [BUSINESS-DECISIONS](./BUSINESS-DECISIONS.md).
> **Ambientes:** desenvolvimento em DEV; testes e homologação em HML; **nada da Pesquisa em PROD** sem o gate do [README](./README.md#regra-obrigatória-de-ambientes-e-promoção-decisão-13112026).

## 1. Objetivo e resultado esperado

Refazer o visual das três páginas internas da Pesquisa no Portal Comercial (lista de campanhas, detalhe da campanha com três abas, detalhe do participante) para ficarem iguais à maquete, **nos temas claro e escuro do Portal**, usando somente componentes do PluginUI e os wrappers do Comercial (`commercialUi`, `dataTableUi`).

É uma **refatoração visual e de composição**. Não muda backend, contrato de API, permissões nem regras de negócio. O comportamento atual (criar campanha, incluir clientes, editar contato, salvar mensagem, copiar convite) continua o mesmo.

**Como medir:**

- As seis telas iguais à maquete no escuro, e com a mesma composição no claro.
- Os ajustes 1–16 da §4 cobertos por teste ou por evidência de tela.
- Nenhum CSS de componente novo fora do PluginUI.
- Nenhuma regressão em Clientes, Minha Carteira e nas outras páginas do Comercial.

## 2. Ownership e limites

| Camada | Owner | Pode | Não pode |
|---|---|---|---|
| Componentes genéricos | `plugins/plugin-ui` | Componente novo **somente se aprovado no Abstraction Gate** (§5, fase 1), CSS em `src/styles/`, testes, catálogo | Conhecer a Pesquisa, textos fixos em português, regra de negócio |
| Páginas da Pesquisa | `plugins/commercial` (`features/satisfaction-surveys/`, `content/satisfactionSurveysContent.ts`, `styles/satisfaction.css`) | Composição, textos, ligação de dados, estado da aba no endereço, layout de página | CSS de componente; regra de negócio; mudar chamadas de API |
| Regras e dados | `commercial-api` | Autorização, validação, janela, gravação | — (**não muda neste plano**) |

**Fora do plano:** backend e migrações; formulário público (UI-03, já homologado); páginas de resultados (UI-01, UI-05, UI-06, UI-07), incluindo os botões “Ver resultados” e “Respostas por empresa”; deploy em PROD.

## 3. Decisões (aprovadas pelo solicitante em 18/11/2026)

| ID | Decisão | Recomendação | Impacto se mudar |
|---|---|---|---|
| D1 | **Aba aberta no endereço da página** (pendência #15) | **APROVADO — sim.** A aba fica no endereço como parâmetro `tab` com os valores do tipo atual `CampaignTab` (`participants`, `message`, `data`), no padrão de parâmetros já usado no Comercial (`utils/*DeepLink.ts`, ex.: `view`). Ex.: `…/satisfaction-surveys/{id}?tab=message`. Atualizar ou compartilhar o link reabre a mesma aba; sem valor ou valor inválido, abre Participantes | Se for “não”, a fase 3 só remove o item 15 |
| D2 | Mostrar a quantidade de perguntas na aba Dados (“Questionário oficial — 15 perguntas”) | **APROVADO — sem mudar backend.** O tipo `SatisfactionCampaign` traz só `questionnaire_version` (texto) e não traz a quantidade de perguntas: mostrar só “Questionário oficial” + a versão. Como formatar a versão como data (“versão de dd/mm/aaaa”) depende do valor real em HML, a confirmar no inventário do P1 | Exigir o dado novo muda o backend e sai deste plano |
| D3 | Destaque de `{nome_empresa}` e `{link_pesquisa}` no editor da mensagem (item 10) | **APROVADO — componente genérico novo no PluginUI** (fase 1, pacote P1): campo de texto de uma linha e de várias linhas com trechos destacados, para o Assunto e a Mensagem. O texto continua num campo nativo, para não perder cursor, colar e leitor de tela | Sem o componente, o item 10 fica só na legenda abaixo do campo, e o destaque dentro do texto vira lacuna registrada |

## 4. Catálogo de mudanças (o que muda em cada tela)

O estado atual foi lido no código em 18/11/2026. O estado novo é o da maquete.

| # | Tela | Hoje | Novo | Arquivo principal |
|---|---|---|---|---|
| 1 | Lista — cards | Card sem destaque do nome | Nome da campanha como título do card; linha “Período” | `SatisfactionSurveysPage.tsx` (colunas e configuração de cards) |
| 2 | Lista | Aviso “Escopo parcial” (`copy.partialScope`) | Removido | `SatisfactionSurveysPage.tsx`, conteúdo |
| 3 | Lista | Sem etiqueta | Etiqueta “MARKETING · PESQUISA DE SATISFAÇÃO” acima do título | `CommercialPageHero` `eyebrow` |
| 4 | Lista, campanha, participante | Sem data da última leitura | “Atualizado em dd/mm/aaaa, hh:mm” junto do botão Atualizar, igual a Clientes | Hero `actions` |
| 5 | Lista | Sem ordenação (nem cabeçalho nem cards) | Todos os cabeçalhos ordenáveis; barra “Ordenar por” na visão em cards | `CommercialDataTableSection` (`sortKey`/`onSortChange`) |
| 6 | Campanha | Aviso “Escopo parcial” | Removido | `SatisfactionCampaignDetailPage.tsx` |
| 7 | Campanha — Participantes | Filtros e tabela espalhados | Um único quadro “Participantes” com filtros, barra da tabela, tabela e paginação dentro | `CampaignParticipantsTab.tsx` |
| 8 | Campanha | Números (`cm-satisfaction-metrics`) dentro da aba | Participantes, Respondidas, Pendentes e Taxa de resposta no bloco de título, como em Minha Carteira | Hero `highlights`; remover a grade da aba |
| 9 | Campanha — Participantes | Contato numa linha | Nome em cima e e-mail embaixo; “Sem contato” em tom secundário | Coluna Contato |
| 10 | Campanha — Mensagem | Campos dinâmicos sem destaque | `{nome_empresa}` e `{link_pesquisa}` destacados no texto, com a legenda | `CampaignMessageTab.tsx` + D3 |
| 11 | Campanha — Mensagem | Salvar/Reverter fora do quadro | Rodapé do quadro do editor, alinhado à direita: Reverter alterações, Salvar mensagem | `CampaignMessageTab.tsx` |
| 12 | Campanha — Mensagem | Botão “Copiar prévia” | Removido; a prévia é só para ver | `CampaignMessageTab.tsx`, conteúdo |
| 13 | Campanha — Dados | Versão técnica do questionário | “Questionário oficial — versão de dd/mm/aaaa” (D2) | `CampaignDataTab.tsx` |
| 14 | Campanha — Dados | Aviso técnico sobre datas | “As datas não podem ser alteradas depois que alguma empresa responder.” | `CampaignDataTab.tsx`, conteúdo |
| 15 | Campanha | Aba só em memória (`useState`) | Aba no endereço (D1) | `SatisfactionCampaignDetailPage.tsx`, `pluginRoutes.ts` |
| 16 | Participante | “Esta empresa já respondeu. Respostas individuais não são exibidas nesta etapa.” | “Esta empresa já respondeu à pesquisa.”; bloco de título com etiqueta “PARTICIPANTE DA PESQUISA”, avatar, código/loja e campanha | `SatisfactionRecipientDetailPage.tsx`, conteúdo |

**Fica igual:** diálogo Nova campanha, diálogo Editar contato, quadro recolhível “Adicionar clientes” e seu fluxo de inclusão, avisos flutuantes, botões Copiar mensagem/assunto/link, prévia com Correio eletrônico/Mensageiro, linha e card clicáveis abrindo o participante (sem coluna Ação).

## 5. Fases

Cada fase é um pedido de execução delimitado, com commit próprio, verificação independente (`AGENTS.md`, ciclo delpi-verifier) e relatório. **Não juntar fases num único diff.** Os pedidos de execução ficarão em `UI-02-PROMPTS-DEVIN.md`, no mesmo protocolo da UI-03.

### Fase 0 — Especificação vigente e inventário (coordenação, sem código de produto)

- Reescrever a [UI-02](./UI-02-CONFIGURACAO-PESQUISAS.md) como especificação vigente, no formato da UI-03: princípios, estrutura de cada tela, componentes usados, textos, estados, acessibilidade e critérios de aceite. Hoje ela tem cerca de 106 KB de decisões acumuladas e ainda diz “NÃO IMPLEMENTADO”, mas as páginas já existem em HML.
- Mover o histórico datado para o [BUSINESS-DECISIONS](./BUSINESS-DECISIONS.md).
- Inventário para o primeiro pedido:
  1. Componentes usados hoje por tela.
  2. Como Clientes mostra “Atualizado em”. Hoje é uma composição da página (`cm-customers-page__freshness`). Decidir se a Pesquisa reaproveita a mesma composição ou se vira um componente do kit.
  3. Se `CommercialDataTableSection` ordena todas as colunas e oferece “Ordenar por” na visão em cards.
  4. Formato de parâmetro de aba já usado no roteador (D1).
  5. Se o detalhe da campanha traz quantidade ou versão do questionário (D2).
  6. Nome do serviço do Comercial no `up-hml-sequential.sh`.
- **Saída:** UI-02 vigente aprovada pelo solicitante; D1–D3 fechadas.

### Fase 1 — Lacunas no PluginUI (somente se aprovadas no Abstraction Gate)

- **Candidato principal (D3):** campo de texto com trechos destacados. Ele recebe a lista de marcadores (ex.: `{nome_empresa}`) e os destaca sem trocar o campo nativo. Cursor, seleção, colar, desfazer e leitor de tela continuam funcionando. Não tem textos fixos. Tem temas claro e escuro pelos tokens do kit.
- **Candidato condicional:** indicador “Atualizado em” no bloco de título, só se a fase 0 concluir que copiar a composição de Clientes duplicaria CSS.
- Registro no catálogo `/apps/plugin-ui` (`visualComponents.ts` com `addedAt`, demo nos dois temas).
- **Testes:** destaque acompanha digitação e colagem; inserir marcador na posição do cursor; nada destacado fora da lista; `aria-*` repassados ao campo; contraste nos dois temas.
- **Deploy:** como nos pacotes do kit da UI-03, o componente genérico pode ir para PROD e HML após verificação, porque não contém nada da Pesquisa.

### Fase 2 — Lista de campanhas (itens 1–5)

- Bloco de título: etiqueta, título “Configuração das Pesquisas”, descrição, “Atualizado em”, Atualizar, Nova campanha e filtros Ano, Situação e Pesquisar campanha dentro do bloco.
- Remover o aviso de escopo parcial.
- Quadro “Campanhas” com barra Tabela/Cards, Itens por página, Fonte e Colunas; cabeçalhos ordenáveis; paginação no padrão de Clientes.
- Visão em cards: nome como título, situação, “Período”, três números e barra “Ordenar por”.
- **Testes:** etiqueta e título; ausência do aviso; ordenação por cada coluna; card com nome e “Período”; estado vazio e erro sem mudança de comportamento.

### Fase 3 — Detalhe da campanha: bloco de título, abas e Participantes (itens 4, 6–9, 15)

- Bloco de título com trilha, etiqueta, nome, janela de resposta, situação, “Atualizado em”, Atualizar e os quatro números em `highlights`.
- Remover a grade de números da aba e o aviso de escopo.
- Abas Participantes, Mensagem padrão e Dados da campanha, com a aba no endereço (D1); voltar e avançar no navegador trocam a aba.
- Aba Participantes: quadro recolhível “Adicionar clientes” sem mudança de fluxo; um quadro “Participantes” com filtros Situação e Pesquisar participante, barra da tabela, colunas Empresa (avatar + código/loja), Contato (duas linhas) e Situação, e paginação.
- **Testes:** números no bloco de título iguais aos da API; aba pelo endereço, inclusive valor inválido caindo em Participantes; contato em duas linhas e “Sem contato”; linha abre o participante.

### Fase 4 — Abas Mensagem padrão e Dados da campanha (itens 10–14)

- Mensagem: Assunto e Mensagem com destaque dos marcadores (D3); legenda; botões de inserir; rodapé do quadro com Reverter alterações e Salvar mensagem à direita.
- Prévia: Correio eletrônico/Mensageiro com nome e link de exemplo, sem “Copiar prévia”.
- Dados: grade de leitura com Nome, Janela de resposta, Situação, Questionário, Versão, Criada em e Atualizada em; aviso das datas em linguagem de negócio; Editar dados no cabeçalho do quadro.
- **Testes:** salvar e reverter com o mesmo comportamento de hoje; ausência de “Copiar prévia”; texto da versão; aviso visível; aviso de alterações não salvas, se já existir, preservado.

### Fase 5 — Detalhe do participante (itens 4 e 16)

- Bloco de título com etiqueta, avatar, nome, código/loja, campanha, “Atualizado em”, situação e Atualizar.
- Aviso “Esta empresa já respondeu à pesquisa.” só quando respondida.
- Quadro “Contato do convite” com Editar contato.
- Quadro “Convite personalizado” com Correio eletrônico/Mensageiro, assunto, mensagem, link exclusivo e os três botões de copiar. A cópia manual quando a área de transferência falha continua.
- **Testes:** aviso só para respondida; três cópias; cópia manual no erro; editar contato inalterado.

### Fase 6 — Limpeza, responsividade e tema claro

- Remover de `styles/satisfaction.css` as regras sem uso (ex.: `cm-satisfaction-metrics`) e os textos sem uso do conteúdo.
- Atualizar `satisfactionSurveys.structural.test.mjs`.
- Conferir larguras 360, 768 e 1280 px, igual à lista de Clientes.
- Conferir **claro e escuro** em todas as telas, só com tokens do Portal e do kit: nenhuma cor fixa na página, e a troca de tema muda só cores.
- **Testes:** auditorias de CSS sem item novo; nenhuma cor literal nova em `satisfaction.css`.

### Fase 7 — Homologação em HML

- Deploy do Comercial **somente em HML**, e do PluginUI se a fase 1 ocorrer.
- Roteiro na campanha de HML “HML - Validacao Pesquisa Satisfacao A+B”:
  1. As seis telas nos dois temas.
  2. Criar campanha de teste.
  3. Incluir cliente.
  4. Editar contato.
  5. Salvar e reverter mensagem.
  6. Copiar convite.
  7. Aba pelo endereço, atualizando a página e voltando no navegador.
  8. Teclado, zoom de 200% e celular.
- **Não enviar respostas** pelos links pendentes (WANKE, WEG) sem combinar com o solicitante.
- **Aceite do solicitante** registrado; atualizar o estado da UI-02 e do índice.

## 6. Verificação obrigatória por fase

| Item | Comando / evidência |
|---|---|
| Testes, lint e build do Comercial | `npm test --prefix plugins/commercial`, `npm run lint --prefix plugins/commercial`, `npm run build --prefix plugins/commercial` |
| Testes do kit (fase 1) | `npm test --prefix plugins/plugin-ui` |
| CSS e componentes | `python3 scripts/ci/audit_platform_guardrails.py --check --base <base>`, `python3 scripts/ci/audit_mfe_plugin_ui_css.py`, `python3 scripts/ci/audit_plugin_ui_native_form_controls.py`, `python3 scripts/ci/audit_plugin_ui_duplication.py` (sem item novo) |
| Documentação | `python3 scripts/audit_documentation_structure.py` |
| Verificação independente | ciclo `agent-kit/verifier` descrito em `AGENTS.md` (até 3 rodadas) |
| Relatório | HEAD inicial e final, arquivos alterados, testes executados, capturas nos dois temas, achados, riscos, gaps restantes |

## 7. Riscos

| Risco | Mitigação |
|---|---|
| Mudança visual quebrar fluxo que já funciona (inclusão, contato, mensagem, cópia) | Fases só de composição; testes de comportamento existentes mantidos; roteiro de HML cobre cada fluxo |
| Deploy do Comercial em PROD feito por outra frente levar as páginas novas | As páginas já estão no código e continuam bloqueadas pelo gate da Pesquisa (`COMMERCIAL_SATISFACTION_SURVEY_ENABLED=false`); registrar no relatório, como o R20 da UI-03 |
| Componente novo do kit afetar outros MFEs | Classe e CSS próprios, sem seletor global; demo no catálogo; conferir regressão após deploy |
| Cor fixa quebrar o tema claro | Só tokens; teste estrutural contra cor literal nova; conferência nos dois temas na fase 6 |
| Outro agente reverter o trabalho (incidente R18 da UI-03) | Conferir HEAD e `git log` dos arquivos no início de cada fase; restaurar só o que for desta frente |
| Escopo crescer para resultados | “Ver resultados” e “Respostas por empresa” ficam para o plano dos resultados |
