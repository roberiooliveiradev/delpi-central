# Página 02 — Configuração de Pesquisas e Campanhas

> **Estado:** ESPECIFICAÇÃO DE UI / WIREFRAME PROPOSTO — **NÃO IMPLEMENTADO**. Entrega 1. Ref observada: `main` / `c135a9823e054ce1234f73eee627548043737264` em 11/11/2026; confirmar HEAD/branch/working tree antes de implementar. Owner visual: `plugins/commercial` ou `plugins/public-hub` conforme indicado. Autoridade de regra e dados: `commercial-api`.
>
> **Fontes:** [índice mestre](./REQUIREMENTS-INDEX.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md), [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) e plano Word integral; código existente: \`plugins/commercial/src/features/home/HomePage.tsx\`, \`features/administration/AdministrationHomePage.tsx\`, \`features/analytics/AnalyticsOtdPage.tsx\`.

**Regra visual obrigatória:** reaproveitar exclusivamente componentes de `@delpi/plugin-ui/index` e wrappers/compostos já usados no Portal, sem implementar novo componente visual nativo da página. Layout semântico e ligação de dados React são permitidos; se uma necessidade realmente não estiver coberta, registrar lacuna e passar pelo Abstraction Gate antes de alterar o PluginUI. Não criar CSS/kit de design paralelo.

## 1. Objetivo e navegação

Criar campanhas e selecionar clientes existentes no TOTVS para que o usuário possa **copiar e enviar manualmente** convites; acompanhar pendentes/respondidos para gestão. **Consulta completa de respostas por empresa** fica na [UI-06](./UI-06-RESPOSTAS-POR-EMPRESA.md), página de leitura independente. A página é interna ao MFE, exclusivamente para `commercial.marketing` OU `commercial.manage`. `commercial.access` não deve ver operações de gestão.

**Rotas de UI previstas:** `/apps/commercial/satisfaction-surveys` (lista/configuração) e `/apps/commercial/satisfaction-surveys/{campaignId}` (detalhe como continuação da mesma área). Entrada pela ação **Configuração** do Hero de Resultados, não outro MFE; a gestão pode voltar a Resultados sem perder contexto básico. A UI-06 tem navegação contextual para esta página e vice-versa, sem outra topbar.

## Regra de composição visual — Hero da gestão (11/11/2026)

**Os filtros globais e botões de ação da página de Configuração também ficam no `CommercialPageHero`**, com `density="compact"`, título/descrição e ações superiores. Na listagem: **Nova campanha**, **Ver resultados**, acesso autorizado a **Respostas por empresa** e filtros de ano/situação/busca/limpar. No detalhe: **Ver resultados**, eventual **Editar datas** permitido e filtros globais da lista de participantes. O `CommercialPagePath` continua acima do Hero. Ações de cada linha (`Copiar link`, `Copiar mensagem`, `Consultar respostas por empresa`) continuam na linha correspondente; botões `Cancelar`/`Criar` ficam no diálogo, por serem ações do formulário. Ações indisponíveis por estado/permissão não são renderizadas como controles ativos. **Não criar barra de filtros solta abaixo do Hero nem componente próprio de cabeçalho.** A validação visual final será feita na revisão desta página; decisão de princípio aprovada, implementação ainda pendente.

### Fluxo consolidado — criar, configurar e ampliar uma campanha (11/11/2026)

**CONFIRMADO PELO SOLICITANTE:** a configuração é **por campanha**, iniciada quando o usuário autorizado aciona **Nova campanha**. Após criar e persistir nome/período da campanha, abrir **o detalhe/configuração dessa mesma campanha** para: (a) selecionar e adicionar empresas oficiais TOTVS, inclusive **múltiplas de uma vez**; (b) configurar e salvar **a mensagem padrão da campanha** com `{nome_empresa}` e `{link_pesquisa}`; (c) consultar a **lista acumulada de participantes**; (d) abrir **detalhe de um participante** e copiar o convite resolvido para colar manualmente em e-mail, WhatsApp, Teams ou outro canal. Não impor conclusão única do cadastro: a campanha pode receber novos participantes depois.

- **Campanha aberta:** o usuário de gestão pode **voltar a uma campanha ainda aberta** e adicionar novos clientes ao conjunto existente, com busca por nome/código e multiseleção, individualmente ou em lote; participantes anteriores e seus links permanecem estáveis. A inclusão posterior **não reinicia a campanha**, não altera respostas já registradas e **não estende** a data final. O backend revalida situação/janela e permissão antes de cada escrita.
- **Campanha agendada:** já se prevê configurar o conjunto inicial ao criar a campanha, que pode estar agendada. O que ainda exige contrato/testes é a política de alterações posteriores em agendadas; não inferir autorização irrestrita. **Campanha encerrada:** inclusão de participantes após o término **não foi autorizada**; na proposta, a ação fica indisponível e a API deve rejeitar novas inclusões, preservando histórico.
- **Seleção:** múltiplos registros podem ser marcados numa mesma busca, inclusive após alterar termos/filtros e paginação; mostrar contagem da seleção e confirmação antes de gravar. A `commercial-api` executa inclusão parcial aprovada, devolve incluídas/já existentes/falhas por empresa, valida código+loja/autorizações e não dispara convites.
- **Detalhe/configuração da campanha:** organizar de forma enxuta os controles de **Dados e datas**, **Mensagem padrão** e **Participantes** usando navegação/seções oficiais já previstas, sem novo MFE, sem cadastro paralelo de cliente nem assistente obrigatório. O detalhe do participante permite consultar situação **Pendente/Respondido**, editar contato em diálogo e copiar mensagem/link, não responder em nome do cliente.
- **Dados e ownership:** TOTVS é fonte oficial do cliente; `commercial-api` é autoridade de campanhas, participantes, estado, vínculos, tokens, modelo de mensagem salvo e escritas; UI mostra apenas estado confirmado. Roteiros de testes: adicionar na criação, voltar com campanha aberta, adicionar em lote, validar parcial/duplicados, trocar participante e copiar nome/link corretos, não alterar histórico/respostas e negar escrita quando encerrada ou sem permissão.
- **Status:** fluxo operacional **CONFIRMADO E DOCUMENTADO**; telas, contratos e execução ainda **PENDING**.

## 1.1 Blueprint consolidado da UI-02 — telas para refinamento de cima para baixo (11/11/2026)

> **Status:** consolidação das decisões aprovadas e proposta detalhada de composição visual. **NÃO IMPLEMENTADO**. Os fluxos marcados APROVADO são decisões do usuário; ordenação final de campos, densidade, ações e apresentação de cada tela são referências **A REFINAR VISUALMENTE**, não aprovação integral. Não transformar dados dos wireframes em valores reais.

### Mapa de telas e responsabilidades

| Tela | Função e relação |
|---|---|
| **UI-02A — Campanhas (inicial)** | Lista, pesquisa, filtros, Nova campanha, navegação para Configurar e Resultados |
| **UI-02A.1 — Nova campanha** | Diálogo oficial com nome e datas; após criação confirmada abre configuração |
| **UI-02B — Configuração da campanha** | Trilha, Hero, situação/período, Participantes, Mensagem padrão, Dados |
| **UI-02B.1 — Adicionar participantes** | Pesquisa TOTVS e multiseleção; inclusão parcial por lote e relatório individual |
| **UI-02B.2 — Mensagem padrão** | Editor único com duas chaves dinâmicas, texto persistido por campanha |
| **UI-02C — Detalhe do participante** | Empresa, contato, resposta pendente/respondida, prévia e cópia de convite/link |
| **UI-02C.1 — Editar contato** | Diálogo por empresa; nome/e-mail opcionais apenas do convite |
| **UI-01 — Resultados** | Página analítica independente; entrada global ou por campanha |
| **UI-06/UI-07 — Respostas privadas** | Página de participantes/respondentes e página de resposta individual; não duplicar na UI-02 |

### Regra aprovada de navegação UI-02 → UI-01

**APROVADO, opção A:** no Hero da **listagem UI-02A**, o botão global **Ver resultados** abre **UI-01 na visão geral padrão**, sem recuperar a última campanha visitada. Na linha de uma campanha, **Resultados**, e no seu detalhe **Ver resultados desta campanha**, abrem a **UI-01 com aquela campanha explicitamente selecionada** no filtro, e ano correspondente. O filtro global e os filtros operacionais da UI-02 não migram para os filtros de análise. A volta à Configuração pela UI-01 fica restrita a gestores e utiliza os helpers oficiais de navegação/retorno, preservando o detalhe de origem quando seguro/conhecido, senão a lista. Rotas são propostas e ainda **NÃO IMPLEMENTADAS**.

### UI-02A — Página inicial, de cima para baixo

1. **Trilha:** CommercialPagePath, Comercial / Marketing / Pesquisa de Satisfação / Configuração; sem topbar duplicada.
2. **Hero compacto:** CommercialPageHero, título **Configuração das Pesquisas**, descrição sobre campanhas, participantes e convites. Ações **Ver resultados (global)** e **Nova campanha**; acesso autorizado a Respostas por empresa quando contextualizado.
3. **Filtros no próprio Hero:** **Ano**, **Situação** (Agendada/Aberta/Encerrada), **Pesquisar campanha** e **Limpar filtros**, com aplicação automática. As situações vêm da API, não de botão ativar/desativar.
4. **Corpo:** seção **Campanhas**, total de registros, tabela oficial em desktop com **Campanha/período**, **Situação**, **Participantes cadastrados**, **Respostas** e **Taxa de resposta** se autorizada/disponível; contexto e ações **Abrir/configurar** e **Resultados** por linha. Não usar "convites enviados" nem "entregues".
5. **Base:** ordenação e paginação oficiais (20 por página como referência do Portal), seletor de tamanho quando aplicável; cards no celular; estados vazio, falha, carregamento, acesso negado e ausência de filtro, diferenciados. Personalização de colunas/fonte/tabela-cards somente se apropriada e coberta pelo kit.

### UI-02A.1 — Diálogo Nova campanha

1. **Cabeçalho:** Nova campanha, orientação breve.
2. **Campos:** nome obrigatório; data e hora de **Início**; data e hora de **Término**; indicação **Questionário oficial fixo de 15 perguntas**.
3. **Rodapé:** Cancelar / Criar campanha. Backend valida dados, permissão e período; falha preserva campos e mostra erro. Somente após persistência confirmada o diálogo fecha e abre UI-02B para configurar empresas e mensagem. **Não** colocar busca TOTVS nem editor de mensagem dentro do diálogo; não ativar/encerrar manualmente.

### UI-02B — Detalhe/configuração de campanha

1. **Topo:** CommercialPagePath Configuração / Nome da campanha, retorno à lista; Hero oficial com nome, período e status derivado do backend.
2. **Ações do Hero:** **Ver resultados desta campanha** (UI-01 contextual), **Respostas por empresa** (UI-06, somente gestão) e **Editar datas** somente onde backend permitir. Filtros globais da lista de participantes no Hero, sem toolbar paralela.
3. **Navegação de seções:** **Participantes**, **Mensagem padrão**, **Dados da campanha** via componente oficial de abas/underline navigation; padrão inicial Participantes. Alternar seção sem apagar pesquisas/seleções e sem gravar automaticamente.
4. **Participantes, resumo:** três cards compactos Participantes cadastrados / Respondidas / Pendentes, todos com contagens retornadas pela API. Pendente significa ausência de resposta, não prova de falta de envio.
5. **Participantes, adicionar:** busca de cliente TOTVS por nome, código/loja; múltiplas seleções e ação Adicionar selecionadas. A lista de participantes é **acumulativa**; o gestor pode voltar e adicionar durante a campanha **ABERTA**, sem alterar respostas, links existentes ou prazo. Configuração inicial agendada prevista; detalhes de edições posteriores em agendadas PENDING. Encerrada não recebe inclusão na proposta, validada pelo backend.
6. **Resultado de inclusão:** apresentar **Incluídas**, **Já existentes**, **Com falha** e relatório por empresa (código/loja e motivo seguro). Válidas são incluídas mesmo com outras falhando; duplicadas preservam vínculo/token, erro global não pode ser rotulado sucesso parcial.
7. **Lista acumulada:** pesquisa por nome/código/loja, filtro Pendente/Respondido, tabela/cards oficiais, ordenação e paginação; empresa, código/loja, contato opcional, status e ações. Linha/card abre **UI-02C**. Copiar link pode existir como ação rápida autorizada; copiar mensagem deve abrir prévia do participante, sem editor duplicado. Sem status Enviado/Entregue.
8. **Mensagem padrão:** ver UI-02B.2. Mostrar situação Configurada/A configurar apenas conforme dado real, não como sucesso fictício.
9. **Dados:** nome, janela, estado, versão de questionário fixo; edição de datas sob regras de backend, sem invalidar respostas. Sem criar editor de perguntas ou flag de ativação.

### UI-02B.1 — Inclusão múltipla: interação e estados

- Busca autorizada commercial-api → api-delpi/TOTVS; exibir empresa e **par código+loja preservando zeros iniciais**. Seleção múltipla, contagem, confirmação do lote, manter seleção entre pesquisas/paginação conforme padrão existente.
- Após resposta confirmada, diferenciar **incluídas, já existentes e falhas por empresa**; não repetir gravações bem-sucedidas ou regenerar tokens. Campos/contrato HTTP de lote e transação por item ainda PENDING do backend.
- Estados: carregando, nenhuma empresa localizada, permissão insuficiente, indisponibilidade TOTVS, duplicidade, erro global, validação por item, retentativa segura. Nunca envia convite nem cria cliente no Portal.

### UI-02B.2 — Mensagem padrão da campanha

1. **Cabeçalho:** Mensagem padrão da campanha, texto de ajuda e indicação de alteração pendente/salva conforme backend.
2. **Editor único simples:** assunto para e-mail e corpo textual; o Marketing escreve como deseja. Somente dois campos dinâmicos definidos em código: **{nome_empresa}** e **{link_pesquisa}**. Pode digitar os tokens ou usar **Inserir campo** na posição do cursor. Reconhecimento/destaque no editor ou equivalente compatível com kit, sem editor rico complexo nem cadastro de tokens.
3. **Validação e prévia:** mostrar como nome e link serão substituídos; dados fictícios identificados na configuração ou participante autorizado. Conteúdo final precisa nome e URL corretos; política exata para texto sem algum token (bloqueio ou composição segura) segue PENDING técnico/UX. Escapar conteúdo e proibir HTML/script arbitrário.
4. **Rodapé:** Cancelar/Reverter, Salvar mensagem. Persistir **uma mensagem por campanha**, confirmada pela commercial-api; não salvar links/tokens de participantes dentro do modelo. Futuras cópias usam texto atualizado; convites encaminhados fora do Portal não são rastreados.
5. **Formatos de saída:** e-mail com HTML formatado e alternativa texto; WhatsApp/Teams/outros como texto simples. A cópia HTML rica e compatibilidade com Outlook continuam PENDING de testes. Não há envio automático nem três editores independentes.

### UI-02C — Detalhe do participante

1. **Topo/trilha:** voltar à campanha e à lista no mesmo contexto; nome oficial, código e loja TOTVS; situação Pendente/Respondida oriunda da API.
2. **Contato do convite:** nome e e-mail auxiliares, opcionais; ação **Editar contato**, abrindo UI-02C.1. Não mudar cadastro TOTVS e não identificar pessoa física respondente.
3. **Mensagem:** texto **salvo da campanha**, resolvido exclusivamente para esta empresa; chaves {nome_empresa} e {link_pesquisa} tornam-se nome TOTVS e URL estável retornada pela commercial-api. Se falta configuração, orientar a voltar à seção de mensagem, sem fingir que já foi salva.
4. **Prévia/cópia:** seletor **E-mail / WhatsApp / Teams**, com Copiar mensagem no formato correspondente e Copiar link independente. E-mail: conteúdo rico text/html e alternativa text/plain quando suportado; os demais em texto. Não enviar, não marcar entregue, não abrir app externo automaticamente.
5. **Estados:** só confirmar cópia após clipboard realmente aceitar; quando negado, oferecer seleção/cópia manual. Nenhum token em logs, analytics ou conteúdo de terceiros. Não incorporar resposta privada completa no detalhe operacional; UI-06/UI-07 são áreas distintas.

### UI-02C.1 — Diálogo Editar contato

- Dialog oficial com empresa/código/loja somente leitura; campos opcionais **Nome do contato** e **E-mail do contato**, pré-preenchidos.
- Cancelar não grava; Salvar contato valida e-mail, autorização e vínculo na commercial-api, mantém diálogo em erro e atualiza detalhe após confirmação; nenhuma gravação TOTVS, alteração de token ou envio de convite.

### UI-01, UI-06 e UI-07 — fronteiras das páginas

- **UI-01:** resultados **agregados**, filtros e KPIs próprios, evolução, dimensões, comparações. Entrada global abre geral; ação de campanha abre filtrada. Nenhuma gestão de participantes ou cópia na página de resultados.
- **UI-06:** respostas por empresa, restritas a Marketing/Manage, com os próprios padrões aprovados de filtros, tabela/cards, ordenação e paginação. Não duplicar inteira na aba Participantes.
- **UI-07:** resposta individual **imutável e somente leitura**; não confundir com UI-02C, que é detalhe operacional para convite e contato.

### Componentes, estados, segurança e roteiro de refinamento

**Padrões oficiais a reutilizar:** CommercialPagePath, CommercialPageHero, CommercialActionButton, CommercialSectionCard, CommercialUnderlineNav, CommercialDataTable, CommercialPagination, cards móveis, filtros, CommercialHostDialog, campos e banners do PluginUI. Validar nomes/props atuais antes de implementar. Hero concentra filtros e ações globais; ações de linhas/diálogos ficam com seu conteúdo. Não criar cabeçalho visual ou kit paralelo. Desktop usa tabelas, celular usa cards, acessibilidade com teclado, foco, contraste e zoom.

**Owners:** TOTVS é fonte oficial de cliente; commercial-api detém campanha, participantes, link, texto salvo, autorização, auditoria e persistência; plugin Comercial apresenta/navega/copia. Gestão para commercial.marketing OU commercial.manage (ainda sujeita a implementação/validação); commercial.access isolado recebe somente agregados protegidos, não convites/contatos/respostas individuais. Nenhuma ação do navegador substitui autorização backend.

**PENDÊNCIAS técnicas:** endpoint/persistência do texto por campanha, transporte e retorno de lote, compatibilidade do clipboard HTML, política exata de tokens ausentes, contratos de retorno e seleção em campanhas agendadas. **NÃO IMPLEMENTADO**: páginas, backend e testes. Não declarar recurso pronto pela existência da especificação.

**Ordem futura de refinamento visual:** (1) UI-02A lista — trilha, Hero, filtros, tabela e base; (2) UI-02A.1 criação; (3) UI-02B Hero/abas/resumo; (4) UI-02B.1 seleção e resultado do lote; (5) UI-02B.2 mensagem; (6) UI-02C detalhe e cópia; (7) UI-02C.1 contato; (8) revisão de transições UI-01/UI-06/UI-07. Atualizar esta fonte canônica, sem duplicar documentos.

## 1.2 Refinamento visual de UI-02A — listagem de campanhas (proposta para revisão, 11/11/2026)

> **Status:** especificação visual **PROPOSTA, PENDING aprovação do solicitante**, sem código executado. Componente/props abaixo examinados em `main` HEAD `e2b341d87785345ffcabf784bd6314c3ce0115d7`: `plugins/commercial/src/app/commercialUi.ts` e `plugins/plugin-ui/src/components/layout/PageHero.tsx`; `CommercialPageHero` envolve `createDashboardPageHero` com `density="compact"` por padrão. Tamanhos em px são **alvos de layout** a confrontar com tokens/CSS do PluginUI e captura real; não afirmar que são dimensões já implementadas. Este bloco inicia a rodada de refinamento da página, do topo para baixo.

### 1.2.1 Estrutura e componentes oficiais (do topo para a base)

| Ordem | Componente/owner | Localização e função | Dimensão/spacing alvo PROPOSTO |
|---|---|---|---|
| 1 | `CommercialPagePath` (factory em `commercialUi.ts`, PluginUI) | Trilha acima do Hero: Comercial / Marketing / Pesquisa de Satisfação / Configuração; respeitar roteamento oficial | Distância inferior até Hero: **12px**; altura intrínseca, sem fixar |
| 2 | `CommercialPageHero` (wrapper do `PageHero` real) | Hero único, `density="compact"`, `variant="surface"`; título, descrição, ações e filhos (filtros) | Padding alvo **20–24px desktop**, **16px mobile**; raio e sombra herdados do kit (não customizar) |
| 3 | `CommercialActionButton` | No `actions` do Hero, à direita no desktop: **Ver resultados** (secundária, visão global padrão) e **Nova campanha** (primária) | Alvo mínimo de toque **44px**; gap **8px**; texto completo e sem truncar |
| 4 | `CommercialSelectField`, `CommercialTextField`, `CommercialClearFiltersButton` / `CommercialFilterBarShell` | No `children` do Hero: Ano, Situação, Pesquisa por nome, Limpar filtros; atualização automática | Grade de filtros: desktop **4 colunas lógicas ou 3 campos + limpar alinhado**; gap **12px**. Altura dos campos conforme kit, alvo **40–44px** |
| 5 | `CommercialSectionCard` (ou wrapper oficial validado) | Abaixo do Hero: seção **Campanhas**, título à esquerda e contador de registros à direita | Gap Hero→seção **16–20px**; padding seção **16–20px** |
| 6 | `CommercialDataTable` | Colunas: campanha/período, situação, participantes, respostas, taxa (se API oficial), ações **Abrir** e **Resultados**. Ordenação remota quando paginada | Densidade compacta do kit, alvos de altura de linha **52–64px**, números alinhados à direita; não fixar largura de nome rígida |
| 7 | `CommercialPagination` de `dataTableUi.ts`/comercialUi | Rodapé da listagem, total/posição, páginas e tamanho de página se componente existente suportar | Alvo gap superior **12px** e rodapé **12–16px**, default **20 registros**, tamanho pela fonte de dados |
| 8 | `CommercialDataCardsGrid` e `CommercialDataCardsSortBar` | Alternativa em mobile, preservando nome/período/status, contagens e ações; respeitar controle de visualização existente quando aplicável | Cards com padding alvo **12–16px**, espaço entre cards **12px**, sem rolagem horizontal na página |
| 9 | `CommercialStateBanner`, `EmptyState`, loading kit | Estados de carregar, sem campanhas, sem resultados no filtro, erro/indisponível, sem permissão | Dentro do espaço da seção, com ações pertinentes e sem criar zeros fictícios |

**Nota de comprovação do PluginUI:** `PageHeroProps` realmente suporta `eyebrow`, `title`, `description`, `badge`, `actions`, `children`, `density` e `variant`; o wrapper Comercial define `compact`. Os valores exatos de padding, fontes, bordas e breakpoints **não foram provados pelo TSX** e devem ser obtidos do CSS/tokens reais antes de implementar. **Não criar CSS próprio para imitar o Hero**.

### Decisão visual aprovada — topo e Hero da UI-02A (11/11/2026)

**APROVADO PELO SOLICITANTE:** composição de topo da página de Campanhas. **CommercialPagePath** aparece antes do **CommercialPageHero compacto**. No desktop, **título e descrição alinhados à esquerda**, e **ações do Hero alinhadas à direita**; em larguras menores, as ações quebram para uma linha abaixo do título sem truncamento ou sobreposição. **Filtros continuam no corpo inferior do mesmo Hero**, reorganizados em duas colunas na faixa intermediária/tablet e uma coluna no celular. Não criar segundo cabeçalho, segunda barra de ações ou barra de filtros externa.

- **Componentes confirmados por inspeção:** `CommercialPagePath` (factory do `commercialUi.ts`), `CommercialPageHero` (wrapper de `PageHero` com `density="compact"` por padrão), `CommercialActionButton`, `CommercialSelectField`, `CommercialTextField` e `CommercialClearFiltersButton`. **Posicionamento e responsividade aprovados**; não afirmar que o CSS existente já entrega os tamanhos propostos.
- **Hierarquia das ações:** **Nova campanha** = ação principal; **Ver resultados** = secundária e global, abrindo UI-01 na visão geral padrão. Ambas permanecem dentro de `actions` do Hero, sem mudar o efeito da navegação contextual por campanha.
- **Medidas de referência discutidas:** trilha → Hero **12px**; Hero padding alvo **20–24px desktop**, **16px mobile**; gap entre ações **8px**; alvo tocável dos botões **44px**. Esses números são **alvos de refinamento**, sujeitos a compatibilidade com tokens, CSS e testes do PluginUI antes de virarem contrato de código. Raio, sombra, font-size e margens da página seguem o kit.
- **Faixas de verificação propostas:** desktop útil a partir de 1200px; intermediário 768–1199px; celular abaixo de 768px. Esses pontos **não são breakpoints implementados comprovados**; verificar faixas oficiais e zoom/teclado. A disposição detalhada e medidas **dos filtros** serão refinadas na próxima etapa, embora sua permanência no Hero e 2/1 colunas já tenham aceite.
- **Status:** composição **APROVADA**, valores CSS concretos e implementação **PENDING**.

### Decisão visual aprovada — filtros no corpo do Hero da UI-02A (11/11/2026)

**APROVADO PELO SOLICITANTE:** organizar os filtros globais no `children` do `CommercialPageHero`, sem barra independente. **Ano** e **Situação** ocupam campos mais estreitos; **Pesquisar campanha** ocupa a largura restante; **Limpar filtros** permanece alinhado à direita no desktop e na faixa intermediária e abaixo dos campos no celular. Filtros se aplicam automaticamente; limpar restaura os valores iniciais sem navegar nem afetar dados de campanha.

| Elemento | Desktop largo — meta aprovada para refinamento | Tablet/intermediário | Mobile |
|---|---|---|---|
| `CommercialSelectField` — Ano | **160px** alvo | 1 de 2 colunas iguais | 100% da largura útil |
| `CommercialSelectField` — Situação | **180px** alvo | 1 de 2 colunas iguais | 100% da largura útil |
| `CommercialTextField` — Pesquisar campanha | Flexível, ocupando espaço restante; **min-width 240px** alvo | Ocupa a linha inteira | 100% da largura útil |
| `CommercialClearFiltersButton` — Limpar filtros | À direita na mesma composição de filtros | Alinhado à direita abaixo dos campos | Abaixo dos campos, sem overflow |
| Espaçamento entre filtros | **12px** alvo | **12px** alvo | **12px** alvo |

- **Alinhamento:** labels sobre os campos de filtro; controles usam altura, padding interno, borda, tipografia e foco das primitivas oficiais do PluginUI, sem CSS paralelo. **Faixa de altura 40–44px** citada no blueprint continua alvo de teste, não confirmação de CSS real.
- **Dados e comportamento:** pesquisa por nome, situação `Agendada/Aberta/Encerrada` oriunda do backend e seleção de ano disponível; filtros automáticos com tratamento apropriado de busca e paginação no servidor. Ao alterar filtro, atualizar o conjunto consultado e ajustar página atual quando necessário. Mostrar estado sem resultados, carregamento e falha sem inventar contagens.
- **Responsividade:** desktop em composição horizontal com campos 160/180/flexível; tablet com 2 colunas para selects e linha seguinte de busca; celular em coluna única. Quebra por largura real sem truncar rótulos nem criar rolagem horizontal. Testar com teclado, zoom e faixas/breakpoints do PluginUI.
- **Status:** distribuição, posicionamento e comportamento **APROVADOS**; os tamanhos informados são **alvos visuais aprovados para checagem de compatibilidade**, não CSS implementado, e os breakpoints/contratos do kit ainda exigem inspeção e testes antes de codificar.

### 1.2.2 Layout responsivo PROPOSTO, a testar com kit real

| Área | Desktop largo (>=1200px úteis) | Intermediário (768–1199px úteis) | Mobile (<768px úteis) |
|---|---|---|---|
| Trilha | Uma linha, quebra se necessário | Quebra sem ellipsis de contexto relevante | Voltar + trilha compacta acessível |
| Hero título/descrição | Texto esquerda; ações na direita | Ações podem quebrar para nova linha dentro do Hero | Título e descrição sobre ações; primária visível, ações quebram sem overflow |
| Filtros | Ano e situação menores + pesquisa maior + limpar; alinhamento consistente | Grade de duas colunas; busca ocupa linha inteira se necessário | **Uma coluna**, campos em largura total; Limpar filtros no próprio Hero |
| Campanhas | Tabela oficial de largura útil | Tabela responsiva oficial ou cards quando sem legibilidade | **Cards**, sem mini tabela ilegível nem rolagem horizontal da página |
| Colunas | Campanha/período flexível, status, contagens e ações | Reduzir colunas secundárias somente conforme kit | Cards com nome, período, status, participantes, respostas, ações |
| Paginação | Rodapé oficial e tamanho por página | Controles refluem | Paginação compacta conforme kit, alvos táteis adequados |

Os limiares acima são **faixas de teste propostas**, não equivalem automaticamente aos media queries/tokens atuais; validar nos tamanhos reais do Portal, inclusive zoom 200%, teclado e modo claro/escuro. A largura da página é a **largura útil do shell Comercial**, não `100vw` nem um novo `max-width` arbitrário. Respeitar `cm-page-stack` e tokens/camadas de spacing que realmente existam; medidas explicitadas aqui servem como metas de revisão, não autorização para override CSS.

### Diretriz aprovada — paridade exata com tabelas e gráficos existentes no Comercial (11/11/2026)

**APROVADO PELO SOLICITANTE:** na UI-02 e demais páginas da Pesquisa, **inventariar a tabela/gráfico de referência já em uso no microfrontend Comercial e reproduzir o mesmo conjunto de funcionalidades, composição e comportamento**, somente quando aplicáveis ao caso. **Não criar funcionalidade adicional**, configuração exclusiva, novo componente nem controle visual inventado. A prévia de Campanhas com 5 colunas e controles de fonte/colunas foi **ilustração**, e NÃO aprovação de controles ou estrutura inédita. Não repetir perguntas sobre funcionalidades já padronizadas; revisar apenas conteúdo/semântica e lacunas comprovadas.

**Inventário inicial confirmado no código do HEAD `7f66ff0c824017806744e35fd26ff051364e920d`** (é evidência de componentes e consumidores, **não** comprovação de funcionamento de toda a UI em runtime):

| Área | Evidência verificada | Regra de adoção |
|---|---|---|
| Tabela e lista de clientes | `plugins/commercial/src/features/customers/components/CustomersTable.tsx` usa `CommercialDataListToolbar`, `CommercialDataTable`, `CommercialDataCardsGrid`, `CommercialDataCardsSortBar`, `CommercialTableColumnVisibilityMenu`, `CommercialTableFontSizeControls` e `CommercialExcelExportButton` | É **referência principal de inventário**, não licença para incluir exportação de campanha/participantes ou todas as ações sem autorização e objetivo explícitos |
| Ordenação/paginação de tabela analítica | `plugins/commercial/src/features/analytics/AnalyticsOtdPage.tsx` usa `CommercialDataTable` e `CommercialPagination`, ordenação e parâmetros remotos `sort_by`/`sort_dir` | Reutilizar semântica remota, tamanho/paginação oficial e estados; conferir contratos antes de transportar |
| Kit de tabela | `plugins/commercial/src/app/commercialUi.ts` exporta os wrappers e `app/dataTableUi.ts` exporta `CommercialDataTableSection` e `TABLE_PAGE_SIZE_OPTIONS` | Usar nomes, props, estilos, tokens e ferramentas reais; não criar toolbar própria ou replicar CSS |
| Gráficos temporais em Analytics | `plugins/commercial/src/features/analytics/components/AnalyticsClosingRateSeriesChart.tsx` e `AnalyticsRolSeriesChart.tsx` usam `ChartViewShell`, `MultiTypeSeriesChart`, `usePersistedChartPreferences` e controles de séries/exportação | Na **UI-01** reutilizar ferramentas reais de gráfico conforme tipo de visualização. Não adicionar alternância de gráfico em ranking fixo ou funções sem aderência; cálculos e dados oficiais seguem backend |

**Critérios de paridade para tabela UI-02A, a inventariar por consumidor antes de fechar especificação visual:** toolbar oficial e conteúdo real; alternância tabela/cards se for padrão aplicável; ordenação e colunas efetivamente suportadas; fonte; paginação e tamanhos oficiais; comportamento mobile, vazios, erro e loading. **Exportação Excel NÃO está aprovada especificamente para UI-02A**: ter o botão existente em Clientes não aprova divulgar dados de campanhas/participantes. Colunas concretas dependem de dados oficiais, utilidade operacional e autorizações; não forçar cinco colunas do protótipo. As dimensões/padding/margens devem **herdar do componente original**; medir e registrar CSS/tokens concretos durante refinamento, sem sobrescrever para fazer parecer igual.

**Gráficos:** UI-02A não precisa de gráfico novo. A UI-01 já contém especificações de `ChartViewShell`/séries e gráficos de dimensão apropriados; verificar cada tipo e controle de apresentação em seus consumidores canônicos antes de implementar. Filtros de dados continuam no Hero; ajustes de apresentação permanecem no contêiner original do gráfico. **A regra aprovada é reutilizar, não transplantar indiscriminadamente todos os controles para todo gráfico.**

**PENDING técnico:** inspeção dos estilos CSS e breakpoints exatos do PluginUI, comparação visual em execução e testes de equivalência com Clientes/Analytics; nenhuma implementação foi executada por esta decisão.

### Decisão aprovada — conteúdo da tabela de campanhas UI-02A (12/11/2026)

**APROVADO PELO SOLICITANTE:** a tabela de Campanhas apresenta cinco **informações** (não presumir cinco colunas físicas quando o padrão do kit exige separar ações): **(1) Campanha / Período** (nome principal + início e término em segunda linha), **(2) Situação** (Agendada/Aberta/Encerrada, calculada pela `commercial-api`), **(3) Participantes** (empresas cadastradas na campanha), **(4) Respostas** (empresas que responderam), **(5) Taxa de resposta** (indicador oficial, sem cálculos improvisados no frontend). Ações contextuais padrão do Comercial: **Abrir configuração** → UI-02B e **Resultados** → UI-01 filtrada pela campanha explícita. Não acrescentar nesta etapa responsável, data de criação, mensagens enviadas, última atualização ou outras colunas não solicitadas.

- **Padrão obrigatório:** reutilizar `CommercialDataTable` e seus padrões reais de linha, toolbar, ordenação, paginação e responsividade observados nos consumidores existentes do microfrontend, especialmente `CustomersTable` e Analytics. Não construir toolbar ou controles adicionais, nem assumir que todos os recursos de outras tabelas são aplicáveis por padrão. `ExcelExportButton` não fica automaticamente autorizado.
- **Semântica:** a taxa e as contagens devem vir da autoridade de resultados/participantes; `Pendente` e número de participantes não significam convite entregue/enviado. Para zero participantes, exibir `—` como taxa indisponível, não taxa inventada. Tratamento de privacidade e grupos pequenos permanece responsabilidade do backend quando aplicável.
- **Identificação e interação:** nome da campanha é elemento principal, período na linha secundária; a ação Abrir leva à configuração; Resultados é contextual e não modifica o comportamento do botão global Ver resultados no Hero. A apresentação exata das ações (coluna/menu/ações por card) deve **seguir o padrão comprovado do microfrontend**, não ser inventada aqui.
- **Responsividade, padding, margens e dimensões:** herdados dos wrappers e tokens reais do PluginUI. A disposição mobile, tamanhos de células e ações serão verificados na próxima rodada contra os consumidores existentes; **não fixar números arbitrários**.
- **Status:** informações e ações funcionais **APROVADAS**; contrato de dados, aplicação concreta dos componentes e teste visual **PENDING**. Especificação, não implementação.

### Decisão aprovada — responsividade idêntica à lista de Clientes (12/11/2026)

**APROVADO PELO SOLICITANTE:** na UI-02A, a listagem de Campanhas deve adotar **o mesmo comportamento responsivo da listagem de Clientes do microfrontend Comercial**, com os componentes oficiais já utilizados no consumidor `plugins/commercial/src/features/customers/components/CustomersTable.tsx`. Não criar variante própria de tabela ou cards para a Pesquisa.

- **Desktop:** `CommercialDataTable` com a identidade visual, células, alinhamentos, hierarquia, seleção/ações e densidade que o padrão de Clientes efetivamente suportar, respeitando apenas as cinco informações aprovadas para campanhas e as duas ações contextuais.
- **Celular:** `CommercialDataCardsGrid` e, quando a listagem de Clientes utiliza, `CommercialDataCardsSortBar`, preservando informações e ações com a organização, toque, foco e espaçamentos do padrão existente. Sem novo breakpoint ou CSS específico para simular a tabela.
- **Tablet e transições:** adotar a alternância/reflow existente no consumidor de Clientes, não inventar intervalo fixo de largura. Verificar os breakpoints reais no CSS e os tokens do PluginUI durante a implementação; documentar os valores reais quando inspecionados.
- **Toolbar, paginação e estados:** manter os controles reutilizáveis efetivamente aplicáveis já previstos no Comercial; não acrescentar exportação ou outras capacidades não aprovadas por existir botão em Clientes. Ordenação e paginação devem consultar a fonte oficial de campanhas quando remotas.
- **Dimensões, paddings e margens:** herdar valores reais dos componentes e da composição do microfrontend; os números ilustrativos do blueprint não autorizam overrides. A confirmação exata de medidas, CSS e comportamento em execução continua **PENDING de inventário técnico/testes**.
- **Status:** paridade responsiva com Clientes **APROVADA e DOCUMENTADA**, implementação não executada. Próximo refinamento será **paginação e estados da listagem**, sem solicitar nova aprovação do padrão já existente.

### Refinamento da base da UI-02A — paginação e estados alinhados ao kit (12/11/2026)

**Padrão reaproveitado, sem nova funcionalidade a aprovar:** o código atual `plugins/commercial/src/app/dataTableUi.ts` configura `createDashboardDataTableKit` com `CommercialPagination`, `TablePageSizeSelect`, `TABLE_PAGE_SIZE_OPTIONS` e padrão **20 itens por página**, além dos rótulos reais de paginação e dos estados de loading. `plugins/commercial/src/features/customers/components/CustomersTable.tsx` já usa `CommercialDataListToolbar`, `CommercialDataTable` e `CommercialDataCardsGrid`. Usar a **mesma composição apropriada** à listagem de campanhas, sem duplicar widgets ou inventar rodapé.

- **Localização:** paginação no rodapé da listagem (tabela/cards), não dentro dos filtros do Hero. Seguir `CommercialDataTableSection`/kit quando adequado, com total e intervalo oficiais. `TABLE_PAGE_SIZE_OPTIONS` permanece a fonte dos tamanhos disponíveis; **não codificar opções 10/20/50/100 sem inventário do valor real**.
- **Rótulos reais do kit, comprovados no código:** `Exibindo [início]–[fim] de [total] · Página [atual] de [total]`; ações `Anterior`, `Próxima`, `Ir para` e `Itens por página` conforme o componente. Tratamento previsto de página inválida/fora do intervalo usa mensagens oficiais, não implementação própria.
- **Dados e filtros:** total, página, tamanho, ordenação e filtro devem refletir a consulta autorizada à `commercial-api`, com paginação/ordenação remotas quando a fonte for paginada. Mudança de filtros deve colocar a página em intervalo válido (normalmente primeira página); não paginar apenas registros locais parciais.
- **Estados a distinguir:** (1) primeiro carregamento — componente de loading padrão; (2) atualização dos filtros com dados antigos — indicador oficial de atualização sem mascarar eventual dado desatualizado; (3) nenhuma campanha cadastrada — estado vazio com ação Nova campanha; (4) filtros sem correspondência — estado vazio com Limpar filtros; (5) falha da API — aviso de erro com ação de tentar novamente conforme kit, não zero fictício; (6) autorização insuficiente — acesso negado; (7) dados recebidos com campos não disponíveis — não inventar zeros/taxa. Verificar mensagens e políticas oficiais durante implementação.
- **Responsividade:** mesmo rodapé e rearranjo de controles dos consumidores canônicos da listagem de Clientes; sem alturas, padding, margens, breakpoints ou largura máxima criados especificamente para Campanhas. Registrar valores reais de CSS/tokens na execução quando conferidos. A ação Nova campanha e filtros permanecem no Hero aprovado.
- **Status:** **CONSOLIDAÇÃO de padrão existente** e complemento de especificação da UI-02A; não afirma novo layout implementado e não altera requisitos aprovados. A UI-02A fica suficientemente descrita para iniciar o refinamento de **Nova campanha (UI-02A.1)**.

### 1.2.3 Navegação e comportamentos

- **APROVADO:** **Ver resultados** global no Hero → UI-01 geral padrão. **Resultados** contextual em linha/card → UI-01 filtrada naquela campanha. **Abrir** → UI-02B; **Nova campanha** → diálogo oficial UI-02A.1.
- Ano, situação e busca aplicam automaticamente. **Limpar filtros** redefine apenas os filtros da lista. Paginação e ordenação da tabela devem refletir a consulta da API, nunca somente os 20 itens locais.
- Situação **Agendada/Aberta/Encerrada** deriva do backend, não cor fixa por lógica local. Participantes significa cadastro na campanha, não convite enviado. `commercial.access` isolado não gerencia/consulta participantes privados.
- **PENDING implementação:** confirmar CSS/tokens/props exatos dos componentes, comportamento de filtro e paginação remotos, modo cards do kit, acessibilidade e testes nos três intervalos.

### 1.2.4 Ordem da revisão visual proposta

**Passo 1:** trilha + Hero + título/descrição + posição e hierarquia de ações. **Passo 2:** filtros no Hero. **Passo 3:** cabeçalho e tabela de campanhas. **Passo 4:** paginação/estados/desktop e mobile. Cada aprovação deve atualizar este bloco com os valores confirmados, marcando decisões em vez de tratar todos os alvos como aprovados.

## 2. Wireframe A — lista e criação

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Marketing / Pesquisa de satisfação                                        │
│ [CommercialPageHero compacto]                                             │
│ Configuração das pesquisas                [Ver resultados] [+ Nova]        │
│ [Pesquisar campanha] [Situação ▼] [Ano ▼] [Limpar filtros]                │
├───────────────────────────────────────────────────────────────────────────┤
│ CAMPANHAS                                                                  │
│                                                                           │
│ Nome / período           Situação       Participantes  Respostas   Ação   │
│ Satisfação 2026/2        Aberta         100            72          Abrir  │
│ Satisfação 2026/1        Encerrada       90            70          Abrir  │
│ Satisfação 2025/2        Encerrada       80            74          Abrir  │
│                                               [Página 1 de N]             │
└───────────────────────────────────────────────────────────────────────────┘
                                     │
                         clique [+ Nova campanha]
                                     ▼
                  ┌─ Dialog oficial do PluginUI ─────────┐
                  │ Nome da campanha                     │
                  │ [________________________]           │
                  │ Início [data/hora]   Fim [data/hora]  │
                  │ Questionário oficial fixo (15)       │
                  │ [Cancelar]               [Criar]     │
                  └──────────────────────────────────────┘
```

Números das linhas **ilustrativos**; não codificar no frontend. Situação vem do backend, derivada da janela. “Participantes” significa cadastrados na campanha, não convites efetivamente enviados; o sistema não comprova contato.

### Decisão visual aprovada — diálogo Nova campanha, UI-02A.1 (12/11/2026)

**APROVADO PELO SOLICITANTE:** a criação é um **diálogo curto**, seguindo os componentes, tokens e comportamento responsivo já existentes no Portal Comercial, sem nova tela ou formulário complexo. O conteúdo editável inicial limita-se a **Nome da campanha**, **Data de início** e **Data de término**, todos obrigatórios; participantes e mensagem serão configurados no detalhe da campanha **após** criação confirmada.

**Ordem visual do topo à base:**
1. **Cabeçalho do diálogo oficial:** título **Nova campanha** à esquerda e fechamento conforme padrão de `CommercialHostDialog`; descrição curta imediatamente abaixo, orientando que mensagem e participantes vêm depois.
2. **Nome da campanha:** campo obrigatório, largura útil completa, rótulo visível, exemplo de nome no placeholder sem substituir o rótulo.
3. **Datas:** **Data de início** e **Data de término**, rótulos e indicadores obrigatórios, **lado a lado em desktop** e **empilhados no celular**, respeitando componente/calendário real e fuso/contrato da API. Não inventar formatação independente do kit.
4. **Informação de questionário:** bloco informativo discreto — **Questionário oficial: 15 perguntas fixas** — sem edição, seleção ou cadastro de perguntas nesta versão.
5. **Rodapé do diálogo:** **Cancelar** (secundária) e **Criar campanha** (primária), alinhados à direita conforme padrão do modal. Não posicionar ações globais da página dentro do corpo do formulário.

**Comportamentos:** botão Criar indisponível enquanto os três campos obrigatórios não forem válidos; término posterior ao início, com validação final na `commercial-api`. Exibir carregamento/erro usando feedback oficial sem duplicar criação; manter dados preenchidos quando houver falha. **Somente após confirmação persistida** fechar o diálogo e navegar à **UI-02B, configuração da campanha criada** (Participantes / Mensagem padrão / Dados), onde se adicionam clientes TOTVS e se salva mensagem por campanha. Cancelar descarta a criação sem gerar campanha local falsa.

**Dimensões, padding, margens, fonte e responsividade:** herdar dos tokens e da implantação real do `CommercialHostDialog` e controles oficiais; duas colunas de datas somente quando comportadas, uma em mobile. **PENDING inventário de CSS/props exatos e teste visual** antes de fixar medidas numéricas; não inventar overrides.

**Status:** composição e três campos **APROVADOS**; contratos técnicos, implementação e validação em dispositivos **PENDING**. Não incluir envio automático, editor de questionário, inclusão de empresas ou mensagem padrão dentro do diálogo.

### Decisão visual aprovada — topo e navegação da UI-02B (12/11/2026)

**APROVADO PELO SOLICITANTE:** na página de detalhe/configuração de campanha, exibir **CommercialPagePath** acima de um único **CommercialPageHero** do Portal; o Hero apresenta **nome da campanha** como título principal, **período início–término** como informação secundária e **situação derivada pela commercial-api** em badge oficial. Ações contextuais de gestão no Hero: **Ver resultados** (UI-01 já filtrada pela campanha) e **Respostas por empresa** (UI-06 restrita a gestão). O retorno da trilha leva à lista de campanhas. Não criar segundo cabeçalho nem menu de navegação paralelo.

**Logo abaixo do Hero:** usar o padrão oficial **CommercialUnderlineNav** para três seções: **Participantes** (selecionada ao entrar), **Mensagem padrão** e **Dados**. Alternar seções na mesma área de configuração, sem mudar a campanha, duplicar páginas, perder contexto sem necessidade ou gravar mudanças implicitamente. Abaixo da navegação aparece somente o conteúdo da seção ativa. `Editar datas`, quando admitido pelo contrato do backend, permanece ação contextual autorizada; não presumir uma edição livre para todos os estados.

#### Matriz visual e responsiva — contrato de composição

| Região | Componente de referência | Desktop largo | Tablet / largura intermediária | Celular |
|---|---|---|---|---|
| Trilha acima do Hero | `CommercialPagePath` | Trilha com retorno e identificação da campanha | Quebra/compactação seguindo kit | Retorno acessível, sem overflow |
| Hero e título | `CommercialPageHero` (`density="compact"`) | Título e período à esquerda; situação no badge do próprio Hero | Refluxo nativo do componente | Título pode quebrar em linhas, mantendo identificação |
| Ações | `CommercialActionButton` no slot `actions` | Alinhadas à direita da linha do título | Quebram para linha inferior quando faltar espaço | Ordem lógica e alvos de toque herdados do kit, sem truncar |
| Navegação abaixo do Hero | `CommercialUnderlineNav` | Seções em faixa horizontal, Participantes inicialmente ativa | Refluxo ou navegação do kit | Mesmo padrão responsivo de navegação já usado no Comercial, sem abas inventadas |
| Conteúdo da seção | Cards, tabelas e campos oficiais conforme função | Ocupa largura útil do shell | Adapta ao container | Empilha conforme componente real, sem rolagem horizontal de página |

#### Dimensões, spacing, margens, tipografia e regras de evidência

- **Regra de padronização reiterada pelo solicitante:** para **cada região e componente** da UI-02B e próximas páginas, documentar explicitamente **owner, componente PluginUI ou wrapper Comercial, props e variantes, localização/hierarquia, largura/altura, padding interno, margens externas, gap, alinhamentos, fonte, peso, raio/sombra, estados, foco/teclado e comportamento por largura de tela**. Quando um valor vier de token CSS ou media query existente, citar **arquivo e símbolo/selector com valor real**; se ainda não inspecionado, indicar **TO_INVENTORY**, nunca inventar medida ou chamar proposta de existente.
- **Herança visual:** `CommercialPageHero`, `CommercialPagePath`, `CommercialActionButton` e `CommercialUnderlineNav` devem utilizar tokens/estilos/componentes oficiais do microfrontend. Não criar paddings, margins, font-size, breakpoints, bordas, alturas mínimas ou sombras específicos da Pesquisa apenas para reproduzir a prévia. O wrapper `CommercialPageHero` já adota `density="compact"` por padrão em `plugins/commercial/src/app/commercialUi.ts`; seus valores CSS efetivos e os da navegação **TO_INVENTORY** antes de implementação.
- **Contexto e responsabilidades:** frontend organiza visual e navegação; `commercial-api` é autoridade para nome/período/situação/contagens e autorização de gestão. Nenhuma preferência visual autoriza informação restrita. Exigir `commercial.marketing` OU `commercial.manage` com validação final no backend. UI-01 mantém resultados agregados segundo autorização e UI-06 não pode ser acessada por `commercial.access` isolado.
- **Status:** composição e seção inicial **APROVADAS**; inventário numérico de CSS/spacing e implementação **PENDING/TO_INVENTORY**. Próximo refinamento: seção **Participantes**, do topo ao rodapé, reutilizando padrões do Comercial.

### Decisão visual aprovada — indicadores de Participantes empilhados no celular (12/11/2026)

**APROVADO PELO SOLICITANTE:** na seção **Participantes** da UI-02B, apresentar as três métricas **Participantes cadastrados**, **Respondidas** e **Pendentes** em **três cartões empilhados verticalmente no celular**, nesta ordem, mantendo componentes, estilos e medidas oficiais do PluginUI/Comercial. A mudança é exclusivamente de **composição responsiva**, não modifica cálculos, contrato dos dados ou permissões.

- **Desktop:** três cartões compactos na mesma linha quando houver largura útil e legibilidade, com a estrutura oficial de cartão/indicador do Comercial.
- **Tablet/intermediário:** utilizar o comportamento responsivo do componente real; conservar três na linha quando couber, mas permitir reorganização conforme tokens e breakpoints já existentes, sem fixar regra nova arbitrária.
- **Celular:** uma coluna, três cartões em sequência (Participantes cadastrados → Respondidas → Pendentes), cada cartão usando a largura útil do contêiner e o padding/margens/gap/tipografia/raio oficiais. Não criar grid, componente ou CSS próprio que replique o PluginUI. Evitar rolagem horizontal e truncamento de rótulos ou valores.
- **Componentes a confirmar no código de implementação:** wrapper de cartões/indicadores apropriado (por exemplo, `CommercialMetricCard` se suas propriedades e semântica forem adequadas) e layout/grid já empregado pelo Comercial. **TO_INVENTORY:** CSS real, tokens exatos de largura, gap, padding, margin, altura, fonte, raio, media queries e comportamento com zoom; documentar arquivo e seletor antes de codificar. Não atribuir valores em pixels sem evidência.
- **Dados e segurança:** métricas com valores oficiais da `commercial-api`; pendentes = participantes sem resposta, não convidados não enviados. Tratamento de loading, falha, ausência de dados e autorização segue componentes oficiais; valores do protótipo são fictícios.
- **Aceite visual posterior:** conferir desktop, tablet, celular e zoom, mantendo ordem, alinhamento, foco acessível e paridade com o kit. **Status:** decisão responsiva **APROVADA E DOCUMENTADA**; medidas efetivas/implementação/testes **PENDING**.

### Decisão vigente — UI-02B.1 card expansível de adição de clientes (13/11/2026)

**DECISÃO MAIS RECENTE DO SOLICITANTE — SUBSTITUI A OPÇÃO ANTERIOR DE DIÁLOGO:** o botão **Adicionar novo** (ou **Adicionar clientes**, conforme rótulo aprovado na seção) na UI-02B, seção **Participantes**, **expande um card completo dentro da própria página**, acima da listagem de empresas já participantes. **NÃO usar modal, drawer ou navegação para outra tela** nessa operação. O fluxo é similar ao de **adicionar clientes às carteiras**: busca TOTVS por nome ou código, resultado com avatar oficial, seleção acumulada de vários clientes, revisão visível da lista selecionada e ação final explícita para **Adicionar à pesquisa**. Ao terminar, o card pode voltar ao estado colapsado, preservando participantes confirmados na lista abaixo.

**Referências canônicas comprovadas no código** (inventariadas em `main`; manter validação em HEAD da implementação):

- `plugins/commercial/src/features/seller-portfolios/SellerPortfolioDetail.tsx`: adiciona clientes em **seção embutida**, com `CustomerSearchPicker`, `excludeKeys={linkedKeys}`, `renderOptionLeading` e `renderSelectedChip` com `CustomerAvatar size="sm"`, e botão de confirmação. Esse padrão embutido é a referência principal, não o `CommercialHostDialog`. O `maxSelected={20}` é uma escolha local de Carteiras, **não** um limite confirmado para a Pesquisa.
- `plugins/commercial/src/features/customers/components/CustomerSearchPicker.tsx`: `value/onChange` guardam seleção acumulada; `excludeKeys` e seleção atual são retirados dos resultados por `customerKey(code,store)`; há seleção múltipla, ação `Selecionar todos filtrados`, chips selecionados, remoção, busca e estados de carregamento/erro/vazio. A pesquisa usa atualmente `useActiveCustomerSearch({pageSize:12})`; verificar limites/cobertura do contrato para Pesquisa antes de implementar.
- `plugins/commercial/src/features/customers/components/CustomerAvatar.tsx`: avatar real de cliente com `createInitialsAvatar("cm")` do PluginUI, opção de foto e iniciais como fallback; usar nos resultados/chips sem inventar componente visual paralelo.
- **Card expansível:** procurar primeiro o padrão de `CommercialSectionCard` e o controle de expansão/colapso efetivamente existente no Comercial/PluginUI; **TO_INVENTORY** do consumidor de expansão e de suas props antes de fixar wrapper; não criar componente novo nem afirmar que `CommercialSectionCard` por si já implementa colapso.

**Ordem no card expandido:** (1) título **Adicionar clientes** e controle oficial de recolher; (2) texto curto de instrução; (3) campo de busca **Nome ou código do cliente**; (4) resultados do TOTVS com avatar, nome e **código + loja**; (5) seleção acumulada, visível em lista/chips com avatar e ação de remover, mesmo após nova pesquisa; (6) contagem de selecionados; (7) ações **Cancelar** (recolhe sem gravar; descarte da seleção ainda pendente conforme confirmação de UX, se necessária) e **Adicionar à pesquisa** (confirma lote). A lista de participantes **confirmados** permanece abaixo do card e é atualizada somente após confirmação da API.

**Sem duplicidade nos dois sentidos:** os resultados **disponíveis** excluem o conjunto oficial de **já participantes da campanha** e os itens **selecionados ainda não confirmados**. Ao desmarcar item pendente, ele volta a ser pesquisável; ao incluir com sucesso, migra para o conjunto oficial de participantes e deixa de ser elegível nas próximas aberturas. A identificação é pelo par exato de strings `customer_code` + `customer_store`, **preservando zeros à esquerda**. Um cliente já participante não pode ficar selecionável apenas por abrir outro card ou trocar a busca. O backend revalida todos os vínculos no momento da inclusão, prevenindo corrida/duplicidade.

**Inclusão e retorno:** a `commercial-api` valida permissão (`commercial.marketing` OU `commercial.manage`), status/janela de campanha, clientes TOTVS e unicidade. Manter decisão anterior de **sucesso parcial em lote**: incluídas, já existentes e falhas individualizadas; não reenviar convites nem reemitir links de participantes antigos. Em falha, apresentar feedback oficial e não simular sucesso; seleção pendente deve ser recuperável para revisão segura.

**Layout, dimensões e responsividade:** o card ocupa a largura útil da seção Participantes dentro do shell aprovado; **colapsado** exibe apenas affordance oficial para abrir; **expandido** contém busca, resultados, selecionados e ações. Desktop: organização conforme seção de Carteiras e componentes originais. Tablet: reflow do kit. Celular: busca/lists/chips e botões ajustam-se à largura disponível, sem overflow horizontal e com alvos acessíveis. **TO_INVENTORY obrigatório:** componentes concretos de expansão, seletores CSS, largura/altura, espaçamento entre card e lista, padding, margens, gap, tipo/tamanho de fonte, raio, breakpoints e foco/teclado. Registrar arquivos, valores e tokens **reais**, sem fixar pixels arbitrários ou CSS exclusivo para Pesquisa.

**Distinção de escopo:** este veto a modal vale **somente para a inclusão de clientes na UI-02B**; não altera as decisões separadas sobre **Nova campanha (UI-02A.1)** e **Editar contato (UI-02C.1)**.

**Status:** substituição da decisão de modal **CONFIRMADA**; componente exato de expansão e detalhes CSS **TO_INVENTORY**, contrato de inclusão e implementação **PENDING**. A especificação não significa que a funcionalidade já esteja implementada.

### Refinamento de retorno de inclusão — sem painel de contadores (13/11/2026)

**ORIENTAÇÃO EXPRESSA DO SOLICITANTE, substitui propostas visuais anteriores:** **não** exibir indicadores adicionais permanentes de **Incluídas / Já existentes / Com falha** no card de adicionar clientes. A inclusão bem-sucedida fica visível na **lista de participantes** imediatamente abaixo, atualizada com dados confirmados pela `commercial-api`. Clientes já vinculados à campanha **não devem aparecer na pesquisa de disponíveis**, assim como os já selecionados na operação atual; o `CustomerSearchPicker` comprovadamente admite `excludeKeys`. Não confundir a especificação de um **retorno de lote por item no backend** com obrigação de mostrar três cards de contagem no frontend.

**Fluxo visual simplificado:** card expansível → busca nome/código TOTVS → avatares de empresas elegíveis não vinculadas → seleção acumulada → botão Adicionar à pesquisa → atualização oficial da lista de participantes. Sem relatório de sucesso ou modal adicional na operação normal; feedback discreto do kit quando necessário. Em erro, mostrar mensagem **somente se houve falha confirmada** e vinculada a uma causa confiável. Exemplos de **hipóteses, não erros comprovados do contrato**: concorrência (outra pessoa inclui o mesmo cliente antes da gravação), término da campanha entre consulta e confirmação, perda de autorização, falha de rede ou mudança de elegibilidade TOTVS. A frase `Cadastro indisponível para inclusão` do protótipo anterior foi **fictícia e genérica**; não padronizar nem assumir que o TOTVS emite isso.

**Backend ainda precisa tratar corretamente:** unicidade por `customer_code+customer_store`, escrita concorrente, retorno parcial por empresa, idempotência, autorização e auditoria. Se a API não puder confirmar o resultado da operação (erro de comunicação), a UI deve consultar o estado oficial antes de repetir a gravação; não afirmar inclusão nem repetição segura sem evidência. Se um item específico falhar, mostrar mensagem contextual e identidade dessa empresa, **sem painel fixo de três contadores**. Condições/códigos de erro efetivos **PENDING** do contrato da `commercial-api`.

**Padronização visual:** mesmo card expansível e mesmos componentes de busca/avatar/seleção do Comercial; usar o componente oficial de feedback apenas em exceções, preservando tokens, dimensões, margens, padding, gap e breakpoints reais (**TO_INVENTORY**) em desktop/tablet/celular. Nenhuma nova visualização, badge ou gráfico de resultado de lote.

**Decisão visual mais recente APROVADA (13/11/2026) — SUBSTITUI feedback no card:** erros e avisos da inclusão devem usar **o toast/aviso flutuante já existente no canto superior direito do Portal Comercial**, **não** uma mensagem dentro do card expansível, painel de indicadores, relatório de erros separado ou modal. Evidência do código em `plugins/commercial/src/app/CommercialFloatingNoticeProvider.tsx`: `CommercialFloatingNoticeProvider`, `useCommercialFloatingNotice`, `notifyError`, `notifyWarning`, `notifySuccess`, baseados no `createFloatingNoticeStack`/`useFloatingNotices` do PluginUI. Consumidor real: `plugins/commercial/src/features/seller-portfolios/SellerPortfolioDetailPage.tsx` invoca `notifyError`, `notifyWarning` e `notifySuccess` na inclusão de clientes em carteiras. A posição percebida no canto superior direito foi informada pelo solicitante; posição, largura, margens, animação e duração específicas **TO_INVENTORY** no CSS e configuração real do stack antes de qualquer alteração.

- **Sucesso normal:** atualizar os participantes confirmados na lista abaixo; opcional feedback padrão de sucesso do fluxo existente, **sem** cards de Incluídas/Já existentes/Com falha.
- **Erro real individual ou parcial:** usar `notifyError` ou `notifyWarning` conforme severidade do fluxo oficial; quando houver identidade/motivo confiáveis e seguros, incluir nome ou código/loja e razão na mensagem; não inventar `cadastro indisponível` ou outros motivos do TOTVS sem contrato real. Quantidades extensas de erros exigem avaliar legibilidade/limites do toast existente; não criar lista de falhas nova sem decisão.
- **Falha de comunicação/estado incerto:** aviso de que a inclusão não pôde ser confirmada, reconciliar participantes oficiais antes de novo envio. Preservar seleção pendente quando seguro, retirando empresas comprovadamente incluídas; não duplicar vínculos nem tokens.
- **Dados e responsividade:** o toast segue tokens e breakpoints do Provider/PluginUI em desktop, tablet e celular, **sem overrides visuais específicos**. O card permanece apenas para buscar, selecionar e confirmar. O backend mantém retorno técnico por empresa e validação de unicidade/autorização, mesmo sem exibir relatório separado.

**Status:** filtragem de já participantes, ausência dos três indicadores e **notificação pelo toast oficial do Portal APROVADAS**; valores CSS, contrato de falhas e implementação da Pesquisa **PENDING**. Não implementado.

## 3. Wireframe B — detalhe de campanha

```text
┌───────────────────────────────────────────────────────────────────────────┐
│ Marketing / Configuração / Satisfação 2026/2                             │
│ Satisfação 2026/2 · [Aberta]      [Editar datas]*  [Ver resultados]       │
│ Janela: DD/MM/AAAA a DD/MM/AAAA                                          │
├───────────────────────────────────────────────────────────────────────────┤
│ [Participantes]   [Respostas]                                             │
├───────────────────────────────────────────────────────────────────────────┤
│ PARTICIPANTES         cadastrados: 100  respondidos: 72   pendentes: 28  │
│ [Buscar cliente TOTVS (código, nome)]        [Adicionar à campanha]      │
│ [Buscar na lista] [Pendente / Respondido ▼]                              │
│                                                                           │
│ Cliente (código+loja)       Contato/e-mail     Respondeu    Ações         │
│ Empresa A — 001/01         contato opcional   Pendente    [Copiar link]  │
│ Empresa B — 002/01         contato opcional   Respondido  [Copiar link]  │
│                                                      [Copiar mensagem]  │
├───────────────────────────────────────────────────────────────────────────┤
│ [Consultar respostas por empresa] → UI-06 (com campanha selecionada)      │
│ Consulta detalhada não se duplica aqui                                     │
└───────────────────────────────────────────────────────────────────────────┘

*Editar datas apenas segundo regras do backend, sem invalidar respostas.
```

## 4. Mapa real de componentes

| Região/ação | Componente existente | Arquivo/padrão |
|---|---|---|
| Hero, breadcrumbs e voltar | `CommercialPageHero`, `CommercialPagePath`, `CommercialActionButton` | `commercialUi.ts` |
| Seção de campanhas e participantes | `SectionCard`/`CommercialSectionCard` | PluginUI/Portal Comercial |
| Seções do detalhe | `CommercialUnderlineNav` | Wrapper PluginUI no Comercial |
| Tabela de campanhas, participantes e respostas | `CommercialDataTable`, `CommercialPagination` | `commercialUi.ts`, exemplo `AnalyticsOtdPage.tsx` |
| Busca de cliente/campanha | `CommercialTextField`, `CommercialFilterBarShell` | `commercialUi.ts` |
| Data e filtros | `CommercialDateField`, `CommercialSelectField`, `CommercialMultiSelectField` | `commercialUi.ts` |
| Nome/contato/e-mail ajustável | `CommercialTextField`, `CommercialDetailFieldGrid` | `commercialUi.ts` |
| Criar/editar campanha | `CommercialHostDialog`, `CommercialActionButton` | Modal host-contained do PluginUI |
| Leitura da resposta | [UI-06](./UI-06-RESPOSTAS-POR-EMPRESA.md) → [UI-07](./UI-07-DETALHES-RESPOSTA.md) | Página independente, sem drawer nem editor |
| Status | `CommercialStatusBadge` | Wrapper PluginUI; não usar status `enviado` |
| Cópia link/mensagem | `CommercialActionButton` + API nativa de clipboard como comportamento | Visual 100% kit; sem botão HTML estilizado custom |
| Feedback | `CommercialStateBanner`, `CommercialLoadingCard`, `EmptyState` | Portal Comercial |

**Não reutilizar** componentes de `commercial.tasks` como mecanismo para a pesquisa nesta entrega. Na entrega 2 serão avaliados somente se respeitarem isolamento e ownership; o plano de ação continua obrigatório no produto completo.

## 5. Estados, validações e regras de interação

### Criar campanha
- Nome, início e fim; formulário oficial com perguntas **fixas e não editáveis**.
- Erro de datas, conflito e falha de rede aparecem no diálogo sem gerar campanha local falsa; fechar/navegar somente após sucesso de persistência.
- `Agendada`, `Aberta`, `Encerrada` são estados derivados no backend; não deixar o usuário mudar uma flag manual de “ativa”.
- Edição de datas deve respeitar imutabilidade das respostas e validações do backend.

### Decisão aprovada — seleção múltipla e inclusão em lote (11/11/2026)

**APROVADO PELO SOLICITANTE:** na configuração de participantes da UI-02, o usuário de gestão poderá **pesquisar e selecionar várias empresas oficiais do TOTVS** (cada uma identificada pelo par `customer_code` + `customer_store`) e **confirmar a inclusão em uma única operação**. Não limitar a interface a uma empresa por vez e não interpretar o lote como envio de convites.

- **Fluxo da interface:** busca autorizada na fonte oficial via `commercial-api → api-delpi/TOTVS`, seleção múltipla visível com quantidade de empresas selecionadas, revisão da seleção e ação explícita **“Adicionar à campanha”**. Preservar a seleção ao pesquisar/navegar pelos resultados conforme os padrões oficiais do Portal; não cadastrar empresas paralelas.
- **Autoridade e escrita:** a `commercial-api` valida o lote inteiro no momento da gravação (campanha, permissão `commercial.marketing` OU `commercial.manage`, identidade código/loja, existência/elegibilidade consultável no TOTVS, unicidade e demais invariantes). O frontend **não** substitui validação nem gera token de convite. Utilizar o contrato REST oficial de participantes, com suporte real a lote **PENDING de especificação técnica/implementação**; não presumir que o POST atual já aceita coleção.
- **Duplicidades e retorno — decisão posterior aprovada:** **inclusão parcial**: incluir as empresas válidas, manter as que já eram participantes sem qualquer alteração de token, e devolver falhas específicas por empresa, com totais e motivo para cada falha. A semântica funcional é **APROVADA**; formato REST, limites do lote, tratamento transacional por item e contrato de erro são **PENDING do backend**. Não mostrar sucesso antes da confirmação real de cada inclusão; proteger contra repetição concorrente.
- **Nenhum disparo:** inclusão em lote **não envia e-mail/WhatsApp/Teams**, não gera status “Enviado”/“Entregue”, não dispara lembretes e não equivale a contato comprovado. Após inclusão, os links continuam disponíveis somente para **cópia manual** e distribuição externa pelo usuário autorizado.
- **Acessibilidade e testes:** teclado, multiseleção, filtros/paginação preservando selecionados, zeros iniciais em código/loja, duplicidades, lote parcialmente inválido, erro de rede, autorização negativa para `commercial.access`, feedback pós-gravação e nenhuma distribuição automática.
- **Status:** decisão de negócio/UX **APROVADA E DOCUMENTADA**; suporte de endpoint em lote, política de erro e implementação **PENDING**.

### Decisão aprovada — inclusão parcial com resultado por empresa (11/11/2026)

**APROVADO PELO SOLICITANTE — OPÇÃO A:** quando um lote tiver empresas válidas, empresas já incluídas e empresas inválidas, **incluir as válidas sem bloquear o lote inteiro**; **preservar sem alterações** as já participantes; e apresentar **relatório das falhas por empresa** com identificação código/loja, motivo e orientação de correção quando segura. Não exigir repetição de toda a seleção devido a uma falha isolada.

- A `commercial-api` revalida autorização, campanha, identidade e elegibilidade para **cada item**. O resultado do lote diferencia, no mínimo, `incluída`, `já existente` e `falhou`; os nomes exatos e o formato do contrato HTTP são **PENDING técnico**, não existentes comprovados. Fornecer contagens e itens classificados, sem listar sucesso de gravação que não foi confirmada. Cada inclusão bem-sucedida é durável; uma falha em outro item não desfaz essas inclusões.
- Empresas já existentes conservam exatamente o mesmo vínculo e link/token. Impedir duplicidade no banco e manter comportamento idempotente inclusive sob cliques repetidos/concorrência. Itens repetidos dentro do mesmo lote não viram convites duplicados.
- Falhas precisam identificar a empresa selecionada, sem expor dados privados, tokens, detalhes internos ou dados de outras campanhas. A seleção que falhou pode permanecer disponível para correção/nova tentativa; não reenviar automaticamente todos os itens já processados.
- Se uma **falha global** inviabilizar a operação (por exemplo, falta de autorização ou indisponibilidade completa da API), **não** interpretar o caso como sucesso parcial confirmado; mostrar estado adequado e conferir o resultado com a autoridade antes de permitir tentativa insegura. Definir política detalhada no contrato do caso de uso.
- **Sem envio de convites** por consequência da inclusão; copiar links/mensagens continua manual. Autorizar writes somente a `commercial.marketing` ou `commercial.manage`, com validação final e auditoria no backend; `commercial.access` isolado não pode incluir participantes.
- **Aceite:** lote misto, todos válidos, todos duplicados, todos inválidos, duplicados no próprio lote, falha global, concorrência, retentativa, contagens corretas, auditoria, ausência de disparos e testes de permissão.
- **Status:** decisão funcional **APROVADA e documentada**; endpoint, atomicidade por item, infraestrutura, autorização em execução e testes **NÃO IMPLEMENTADOS/TO_INVENTORY**.

### Selecionar participante
- Busca usa `commercial-api` (BFF já existente) e a fonte TOTVS; seleção conserva `customer_code+customer_store`, inclusive códigos com zeros iniciais.
- Ao incluir duplicado, carregar participante já existente e **preservar o mesmo token**; nunca gerar link no browser.
- O e-mail/contato copiado do ERP é informação auxiliar ajustável só neste convite; não editar cadastro TOTVS nem exigir e-mail para copiar link.

### Decisão aprovada — diálogo de edição de contato por participante (11/11/2026)

**APROVADO PELO SOLICITANTE — OPÇÃO B:** na lista de participantes da campanha, a ação **“Editar contato”** abre **diálogo oficial do Portal/PluginUI** específico da empresa escolhida. A tabela permanece em leitura, exibindo o contato disponível; não criar edição de células em linha. No diálogo, apresentar empresa e código/loja em leitura, além de campos editáveis **nome do contato** e **e-mail do contato**, restritos **ao convite desta empresa nesta campanha**.

- Pré-preencher os campos com os dados de contato já registrados para o convite (inicialmente derivados da fonte oficial quando disponíveis); ambos continuam **opcionais**. Não exigir e-mail para gerar/copiar link. Salvar campos após validação do formato quando informados e confirmação de persistência da `commercial-api`; erro de validação ou rede mantém o diálogo e valores preenchidos, sem afirmar sucesso.
- **Autoridade e fronteira:** `PATCH /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}` é a proposta de contrato existente no planejamento, **ainda não implementada**. O backend revalida permissão `commercial.marketing` OU `commercial.manage`, campanha, participante e campos autorizados, aplica auditoria e confirma estado persistido; `commercial.access` isolado não edita. Nenhum write direto da UI ao TOTVS/`api-delpi`; não modificar cadastro mestre, nome da empresa, código/loja, token ou resposta definitiva.
- **Interação:** botões **Cancelar** e **Salvar contato** no diálogo; Cancelar não persiste mudanças. Após sucesso, fechar diálogo e atualizar apenas o participante correspondente com dados confirmados pelo servidor. Reutilizar `CommercialHostDialog`, campos e feedback existentes; não criar novo modal ou editor visual.
- **Privacidade e processo:** contato/e-mail são auxiliares da distribuição **manual** de convites, não identidade do respondente; não enviar convite nem registrar situação “Enviado/Entregue” por editar contato. Não expor contato a usuários sem autorização.
- **Testes:** pré-preenchimento, valores vazios, e-mail inválido, cancelar, sucesso/erro de PATCH, concorrência, permissões, auditoria, teclado/foco e preservação do mesmo link exclusivo.
- **Status:** decisão de experiência **APROVADA E DOCUMENTADA**; endpoint, autorizações reais e testes **PENDING**.

### Decisão aprovada — editor único e mensagem personalizada por empresa (11/11/2026)

**APROVADO PELO SOLICITANTE:** oferecer **um editor único de convite personalizável**, com prévia e **cópia por canal**: e-mail como **HTML formatado** (mais alternativa de texto simples), WhatsApp como **texto** e Teams como **texto**. Nenhum canal é enviado automaticamente pelo Portal. Cada convite deve mencionar **automaticamente o nome real da empresa participante** — vindo do cadastro oficial TOTVS via consulta autorizada e/ou nome-snapshot validado pela `commercial-api` — em lugar da expressão genérica “sua empresa”. O vínculo inequívoco é `customer_code` + `customer_store`; não tentar identificar empresa pelo texto do nome.

- **Experiência:** ao acionar **“Preparar convite”/“Copiar mensagem”** para um participante, exibir empresa e campanha, assunto de e-mail editável, **corpo de mensagem editável** e três prévias/cópias (E-mail, WhatsApp, Teams). Há **uma fonte textual compartilhada**, não três editores independentes. **“Copiar link”** isolado continua acessível. Empregar componentes oficiais do Portal/PluginUI, sem editor visual paralelo.
- **Campos dinâmicos obrigatórios:** usar placeholders internos **`{nome_empresa}`** e **`{link_pesquisa}`** (nomes de exibição propostos; representação técnica a definir) com resolução **para o participante atual** antes de cada prévia e cópia. A interface deve mostrar o nome efetivo no resultado e não permitir troca manual do nome oficial ou do link exclusivo dentro do editor. Se um usuário alterar/remover tokens no texto livre, o fluxo deve garantir por composição segura que **nome e URL corretos sempre estejam presentes no convite final**, sem duplicação. Se o nome oficial estiver ausente ou inconsistente, **não inventar nome nem copiar convite associado a outra empresa**: bloquear a cópia personalizada e orientar correção/consulta ao dado oficial.
- **Link e segurança:** o URL exclusivo estável é fornecido pela `commercial-api` somente após validação de permissão `commercial.marketing` ou `commercial.manage` e vínculo campanha/participante; nunca criar link no frontend. Evitar cache compartilhado entre participantes, token em logs/analytics, exposição de URLs de outras empresas e conteúdo inseguro no HTML. Sanitizar/escapar texto do Marketing, nome oficial e URL.
- **Saída E-mail:** montar HTML simples de comunicação visual aprovada (parágrafos, identidade e link/CTA) e `text/plain`; copiar **conteúdo formatado**, não markup bruto, via clipboard suportado pelo navegador, com fallback de texto e cópia manual quando necessário. Suporte real à colagem rica depende do editor de e-mail; testar com os clientes DELPI. Assunto é editável para cópia manual, mas não há envio.
- **WhatsApp e Teams:** a mesma mensagem resolvida é convertida para texto simples com quebras de linha e URL visível; não assumir interpretação de HTML ou Markdown. A ação é copiar/colar externamente; nenhuma abertura/envio automático.
- **Decisão posterior do solicitante (11/11/2026):** substituir a proposta de editor apenas temporário por **área padrão de configuração do texto do convite**. O usuário autorizado define o texto e o utiliza para preparar/copy convites a várias empresas. O modelo configurado deve ser recuperável para uso posterior; **escopo aprovado: uma mensagem padrão salva POR CAMPANHA, reutilizada para seus participantes**. Não presumir uma versão por participante nem guardar o token exclusivo no modelo. Armazenamento, endpoints e autoria/auditoria são **PENDING de desenho mínimo do owner `commercial-api`**, sem criar CRUD genérico de templates.
- **Validação e testes:** verificar dois clientes com nomes diferentes e códigos/lojas distintos, mudanças de seleção, prevenção de link/nome cruzados, caracteres especiais/HTML malicioso, falta de nome oficial, equivalência entre as três prévias, clipboard negado, compatibilidade Outlook/WhatsApp/Teams, fluxo por teclado e **ausência completa de disparo**.
- **Estado:** decisão funcional/UX **APROVADA e documentada**; implementação, representação de placeholders, compatibilidade HTML e aprovação do texto institucional por Marketing **PENDING**.

### Decisão complementar — configuração simples e inserção de campos dinâmicos (11/11/2026)

**APROVADO PELO SOLICITANTE:** disponibilizar na UI-02 **área de configuração de mensagem padrão**, funcional e deliberadamente simples. O usuário escreve e ajusta o texto, pode **digitar manualmente as chaves** ou usar um pequeno botão/lista de **“Inserir campo”** para colocar a chave na **posição atual do cursor**, mantendo a seleção/foco quando possível. O sistema **reconhece e destaca visualmente** as ocorrências das chaves no editor (ou fornece marcação equivalente compatível com os componentes oficiais, sem criar editor rico do zero). Não criar ferramenta para o usuário cadastrar/renomear campos dinâmicos.

- **Exatamente dois campos dinâmicos disponíveis nesta entrega**, definidos em código: **`{nome_empresa}`** (nome oficial do participante TOTVS) e **`{link_pesquisa}`** (link estável e exclusivo obtido da `commercial-api`). Não implementar campos extras sem requisito futuro. Inserir campo deve respeitar cursor/seleção; validar ocorrências e avisar se houver chave desconhecida ou sintaxe incorreta, sem interpretar conteúdo do usuário como código.
- **Prévia por participante:** resolver as chaves exclusivamente no momento da prévia/cópia, com contexto da campanha e empresa selecionadas e validação de autorização no backend. Exibir valores reais na prévia; não guardar valores sensíveis resolvidos dentro do modelo configurado. Impedir misturar nome/link de empresas diferentes. Ao trocar participante, renderizar novamente a mesma mensagem e atualizar ambos os dados.
- **Obrigatoriedade da composição:** o convite final precisa conter corretamente o nome oficial e o link exclusivo. Se o texto configurado não tiver uma das chaves, orientar a inserção ou compor a informação obrigatória com segurança, sem duplicação; critério exato de bloqueio versus composição automática **PENDING técnico/UX**. Não alterar manualmente os valores resolvidos de nome e URL.
- **Formatos mantidos:** mesma fonte textual alimenta **cópia HTML formatada para e-mail** (com `text/plain` alternativo), **texto para WhatsApp** e **texto para Teams**; prévias específicas, mas **sem três editores** e sem envio automático. Evitar WYSIWYG avançado, editor HTML livre, novos componentes visuais ou ferramenta de gestão de tokens. Assunto de e-mail pode seguir o editor simples já previsto.
- **Responsabilidades:** frontend controla campo, destaque/validação de sintaxe e inserção na posição do cursor; backend é autoridade da configuração persistida (quando definido escopo), permissão, link e vínculo com cliente. Tratar conteúdo como dado: escape/sanitização do HTML final, sem scripts/HTML arbitrário e sem registrar tokens em logs.
- **Testes:** inserção no meio do texto e substituição de seleção, digitação manual e destaque das duas chaves, chaves inválidas, texto simples/multilinha, nomes com caracteres especiais, troca de participantes, cópia HTML/texto, teclado e colagem em Outlook/WhatsApp/Teams.
- **Status:** fluxo/editor, dois campos dinâmicos e escopo por campanha **APROVADOS**; contrato de persistência, suporte técnico do componente e testes **PENDING**. Não implementado.

### Decisão aprovada — configuração por campanha e cópia no detalhe do participante (11/11/2026)

**APROVADO PELO SOLICITANTE:** o gestor configura e salva **uma mensagem padrão da pesquisa/campanha**, não um modelo geral comum a todas as campanhas. Volta à **lista pesquisável de empresas participantes**, abre o **detalhe da empresa selecionada**, visualiza a mensagem com nome e link próprios e **copia** no formato adequado para colar manualmente no e-mail, WhatsApp, Teams ou outro meio.

- **Percurso:** detalhar campanha → **Configurar mensagem** (texto e dois campos dinâmicos em código) → salvar na autoridade `commercial-api` → voltar à lista de participantes → buscar empresa por nome ou código/loja → abrir detalhe do participante → escolher prévia/cópia de e-mail HTML (com texto simples alternativo) ou WhatsApp/Teams texto → copiar. A ação separada **Copiar link** permanece.
- **Responsabilidades visuais:** o editor de configuração fica **na campanha**; no detalhe do participante fica **prévia e cópia**, não outro editor completo. O corpo configurado é reutilizado para os participantes daquela campanha; modificar a configuração altera apenas futuras cópias, não contatos já encaminhados fora do Portal.
- **Resolução segura:** `{nome_empresa}` = nome oficial TOTVS do participante; `{link_pesquisa}` = URL estável exclusiva fornecida pela `commercial-api`. Os valores são resolvidos novamente para o participante selecionado; nunca salvar URL/token real no modelo nem misturar dados de empresas diferentes. Acesso e escrita de gestão exigem `commercial.marketing` OU `commercial.manage` no backend.
- **Persistência:** texto configurado permanece disponível ao retornar à campanha. O contrato e armazenamento mínimo sob ownership da `commercial-api`, validações, auditoria e testes continuam **PENDING**; não afirmar que há endpoint/tabela pronto nem criar CRUD genérico de templates.
- **Processo:** nenhuma cópia dispara mensagem; o usuário cola e encaminha externamente. Nenhum status “Enviado/Entregue” é inferido. Testar busca, detalhe, retorno à configuração, alteração do texto, cópia multi-canal, duas empresas e dois links, permissões, falhas de clipboard e zero disparos.
- **Status:** fluxo e escopo **APROVADOS**, implementação **PENDING**.

### Copiar convite
- **Copiar link** solicita ao backend o mesmo URL estável e copia; **Copiar mensagem** abre **editor único personalizado**, com **nome oficial da empresa e link específico inseridos automaticamente** e prévias/cópias E-mail HTML, WhatsApp texto e Teams texto. Não disparar nada.
- Toast/estado de sucesso só após confirmação da cópia; falha de clipboard oferece seleção/cópia manual. Não incluir `Enviar e-mail`, `Reenviar`, `WhatsApp direto`, `Entregue`, `Enviado`, disparo em lote ou contador de tentativas.
- Recópia não indica que houve contato com o cliente; mostrar **Pendente/Respondido** com base na submissão.

### Consultar respostas
- Resposta individual é somente leitura; notas, NPS, 10 dimensões e até três comentários, data e vínculo empresa. Nada de `Editar`, `Excluir` ou “Responder em nome do cliente”.
- Nenhuma página ou componente público recebe dados de outros participantes.

## 6. APIs, permissões e fluxo

| Interação | REST planejado | Requer |
|---|---|---|
| Listar/criar/abrir/editar campanha | `GET/POST /satisfaction-surveys/campaigns`, `GET/PATCH /satisfaction-surveys/campaigns/{id}` | Gestão |
| Busca cliente | `GET /customers/search` existente; via BFF | Autorização da operação e validação no backend |
| Listar/adicionar participantes | `GET/POST /satisfaction-surveys/campaigns/{id}/recipients` | Gestão |
| Ajustar contato | `PATCH /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}` | Gestão |
| Copiar mesmo link | `GET /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}/link` | Gestão; resposta sensível |
| Listar/detalhar respostas | `GET /satisfaction-surveys/campaigns/{id}/responses`, `GET /satisfaction-surveys/responses/{id}` | Gestão |
| Enviar e-mail | **INEXISTENTE nesta experiência** | Usuário usa seu canal fora do Portal |

`commercial.marketing` será registrado durante implementação, junto com RBAC do frontend/host, backend e CAIO. **Não** inventar `commercial.survey.write` ou outros códigos.

## 7. Responsividade, testes e critérios de aceite

- Desktop: tabela com paginação e colunas essenciais; tablet/mobile: filtros reorganizados com kit e tabela rolável/adaptativa do PluginUI; ações acessíveis pelo teclado e rótulos claros.
- Estado vazio inicial oferece `Nova campanha`, sem dados fictícios; acesso negado tem mensagem específica; falha de consulta não se apresenta como `0 participantes`.
- O link não aparece em logs, navegação indevida ou analytics; Clipboard é ação explícita.
- Testar via UI e backend: criação, datas, duplicidade, edição controlada, pares TOTVS, link estável, cópia sem envio, pendência, restrição de acesso, leitura imutável e responsividade.
- Testar `read`/`execute` no CAIO com os mesmos casos de uso e limites de autorização; teste REST/CAIO na **mesma etapa**. Conferir HEAD, arquivos, mudanças, residual search, outcome e gaps em execution report.

**Entrega 2:** classificação e plano de ação **não aparecem agora**, mas estão previstos e obrigatórios segundo o [Word/índice](./REQUIREMENTS-INDEX.md). Não antecipar telas de ações nesta página enquanto a pesquisa não estiver entregue.