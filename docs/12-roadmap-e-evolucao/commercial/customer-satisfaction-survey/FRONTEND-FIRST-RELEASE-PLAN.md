# Frontend — Pesquisa de Satisfação de Clientes (primeira entrega)

> **Status: PLANEJAMENTO FUNCIONAL/TÉCNICO PROPOSTO, NÃO IMPLEMENTADO.** Em 11/11/2026; base consultada: branch `main`, HEAD `1e75d95d000bda6c664c246ee0ba67f27a31a7a3` (revalidar antes de modificar código). Não há telas de pesquisa identificadas no plugin atual.
>
> **Planejamento por etapas:** esta especificação é exclusiva da **entrega 1**. A **entrega 2 está assumida como obrigatória** e incluirá gestão de classificação, planos de ação, retornos e reavaliações, com suas interfaces a detalhar ao iniciar essa frente. Não eliminar requisitos do Word por não aparecerem nas páginas deste ciclo.
>\n> **Fontes canônicas:** [índice mestre](./REQUIREMENTS-INDEX.md), [decisões](./BUSINESS-DECISIONS.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md) e o plano integral nas fontes do projeto. Este documento descreve **a interface para o escopo aprovado**, não altera o ownership ou aprova desenvolvimento de planos de ação.

> **Revisão UX da UI-01 em 11/11/2026:** o wireframe detalhado foi atualizado para **Hero com todas as ações/filtros globais → Resumo executivo → Evolução histórica (gráfico e tabela no mesmo bloco) → Dez dimensões → Comparativos → Respostas restritas**. Cinco KPIs com contexto e tendências comparáveis, barras com máximo fixo 5, sem cores de alerta por limiar não aprovado; a página mantém componentes oficiais PluginUI e `CommercialUi`. Consulte [UI-01](./UI-01-RESULTADOS-PESQUISA.md) como fonte **mais específica** para o desenho da página. Estado: proposta registrada, implementação pendente.

## Especificações completas por página — wireframes e PluginUI

O [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) permanece como **visão geral**; cada superfície possui um documento específico, com wireframe, inventário de componentes reais, regras de segurança, contratos, estados e critérios de aceite. **Não criar componentes visuais nativos nas páginas**: reutilizar PluginUI e componentes já utilizados no Comercial, submetendo qualquer lacuna ao Abstraction Gate.

| Superfície | Documento |
|---|---|
| Página principal — Resultados | [UI-01](./UI-01-RESULTADOS-PESQUISA.md) |
| Página de Configuração e detalhe de campanha | [UI-02](./UI-02-CONFIGURACAO-PESQUISAS.md) |
| Página pública de respostas | [UI-03](./UI-03-FORMULARIO-PUBLICO.md) |
| Integração no Início: card Marketing | [UI-04](./UI-04-INICIO-CARD-MARKETING.md) |
| Integração na Visão Geral: seção Pesquisa de Satisfação do Cliente | [UI-05](./UI-05-VISAO-GERAL-SECAO-PESQUISA.md) |

**Prioridade visual de revisão:** UI-01 → UI-02 → UI-03; UI-04/UI-05 são pontos de encaixe no portal existente. Os wireframes são propostas visuais **não aprovadas individualmente**, nem prova de implementação.

### Diretriz transversal aprovada — reutilização dos padrões implementados (11/11/2026)

**Decisão do solicitante, válida para todas as páginas aplicáveis da Pesquisa de Satisfação:** inventariar e reutilizar os padrões **já implementados** no Portal Comercial para Heroes, filtros automáticos, botão Limpar filtros, tabelas, cabeçalhos ordenáveis, paginação, cartões móveis, seleção de visualização, ajustes de fonte, personalização de colunas, estados e navegação. **Não reapresentar esses padrões como novas dúvidas visuais por página.** Validar se cada página realmente precisa do recurso; páginas públicas e telas sem tabela não recebem controles sem sentido. Exceções operacionais, riscos de dados e lacunas técnicas seguem exigindo análise.

**Referências concretas verificadas em código:** `plugins/commercial/src/app/commercialUi.ts` (`CommercialPageHero`, `CommercialClearFiltersButton`, `CommercialDataTable`, `CommercialDataCardsGrid`, `CommercialDataCardsSortBar`, `CommercialTableColumnVisibilityMenu`, `CommercialTableFontSizeControls`, `CommercialExcelExportButton`); `app/dataTableUi.ts` (`CommercialPagination`, `CommercialDataTableSection`, default de 20 registros); `features/customers/components/CustomersTable.tsx` (tabela/cards, cabeçalhos ordenáveis, seletor de ordenação, personalização, exportação e fonte); `features/proposals/ProposalsPage.tsx` (paginação e busca com espera de 350 ms); `app/commercialNavigationReturn.ts` (retorno seguro). O kit `DataTableSection` declara que ordenação com paginação remota deve ocorrer na fonte de dados, não apenas na página carregada.

**Aprovação específica UI-06:** cinco opções aprovadas em conjunto — personalização de colunas, fonte, **exportação Excel restrita**, alternância tabela/cards no desktop e seleção de tamanho de página. Detalhes, restrições e gates: [UI-06](./UI-06-RESPOSTAS-POR-EMPRESA.md#decisão-em-lote--recursos-de-tabela-e-lista-já-existentes-no-portal-11112026). A exportação é uma nova capacidade **desejada para UI-06**, não um endpoint já implementado; nenhuma exportação de dados identificáveis pode ser habilitada para `commercial.access` isolado. Não estender automaticamente a outras páginas sem conferir escopo, finalidade e autorização. Implementação e testes permanecem pendentes.

## 1. Escopo e experiência

**Entregar nesta versão:** o usuário autorizado cria campanha, seleciona empresas TOTVS, copia link/mensagem e distribui **por conta própria**, acompanha respostas e analisa resultados. O cliente abre o formulário pelo link, revisa e envia uma resposta definitiva. O Comercial usa os resultados para suas ações **fora da aplicação**.

**Não entregar na primeira versão:** disparo integrado de e-mail/WhatsApp/Teams, envio em lote, lembretes automáticos, confirmação de entrega, CRUD das perguntas, editor de respostas definitivas, telas/tarefas de planos de ação, retorno ou reavaliação, nova permissão além de `commercial.marketing`, novo MCP/novas tools. **Planos de ação, retorno e reavaliação serão desenvolvidos na entrega 2**, não descartados. O CAIO é estendido por entidade/ação em cada etapa do backend, não pelo frontend.

**Reutilizar o Portal Comercial:** `plugins/commercial` já possui `App.tsx`, roteamento próprio (`app/pluginRoutes.ts` e `app/pluginNavigation.ts`), catálogo de navegação (`content/shellNav.ts`, `content/pluginRouteCatalog.ts`), shell (`app/PluginShell.tsx`), HTTP `api/httpClient.ts`, componentes `CommercialPageHero`, `CommercialMetricCard`, `CommercialDataTable`, filtros, seletores, estados de carregamento e mensagens em `app/commercialUi.ts`/`@delpi/plugin-ui`. Reaproveitar contratos e componentes existentes antes de novas abstrações. **Não criar microfrontend separado para a gestão interna.**

## 2. Rotas de interface propostas

Paths internos são **propostos**, não encontrados implementados. A nomenclatura deve seguir o roteador `pluginRoutes.ts` e o catálogo do shell no momento de implementação.

| Visão | Rota de UI proposta | Usuário | Responsabilidade principal |
|---|---|---|---|
| Pesquisa — entrada | `/apps/commercial/satisfaction-surveys` | `commercial.marketing` OU `commercial.manage` | Listar campanhas; ação Nova campanha; abrir resultados |
| Campanha — detalhe | `/apps/commercial/satisfaction-surveys/:campaignId` | Gestão | Dados/datas, participantes, links copiáveis e situação das respostas; navegação por seções na **mesma página**, sem obrigar subrotas |
| Respostas da campanha | Seção **Respostas** dentro do detalhe | Gestão | Lista por empresa, notas e comentários autorizados; detalhe por painel/expansão se suficiente |
| Indicadores | `/apps/commercial/satisfaction-results` | `commercial.access` ou Gestão | IGS, NPS, taxa, dimensões, evolução, filtros e tabela estratégica/demais; **somente agregado** para Access |
| Formulário do cliente | `/p/commercial/form/{token}` no `plugins/public-hub` (path proposto dentro do padrão público real) | Cliente com link válido, sem login interno | Apresentar 15 perguntas, revisão, confirmação e sucesso |

**Decisão de composição proposta:** **as duas páginas internas pertencem ao MFE `plugins/commercial`**; a página pública pertence ao `plugins/public-hub`. Duas entradas internas são suficientes: **Pesquisa de Satisfação** para os gestores e **Resultados da Pesquisa** para quem pode ver agregados. Não adicionar quatro itens fixos à topbar; preferir entrada apropriada no hub/área comercial com acesso por capability. Se o hub atual permitir um item com seções, preservar a navegação mais enxuta.

**Formulário externo — PADRÃO EXISTENTE IDENTIFICADO:** implementar a página pública em `plugins/public-hub`, **não** dentro do shell autenticado `plugins/commercial`, e **não** criar um novo MFE/site. O `public-hub` já atende `/p/{app}/{page}/{token}` sem login (fonte: `plugins/public-hub/README.md`), inclui roteador/registro (`src/shell/routing.ts`, `registry.ts`), UI comum (`PublicShell.tsx`) e formulário público de referência em `src/apps/customer-experience/{pages.tsx,FormPage.tsx,api.ts}`. **Path proposto:** `/p/commercial/form/{token}`; registrar uma página no `publicRegistry` com `appId=commercial` e `pageId=form`, reutilizando o contrato visual público e mantendo lógica/contrato próprios da pesquisa. Chamadas apenas à `commercial-api` (`GET /public/satisfaction-surveys/{token}` e `POST /public/satisfaction-surveys/{token}/response`), sem bearer do usuário interno. É necessário verificar a exceção HTTP no middleware da API Comercial; o gateway já serve `/p/` ao public-hub conforme documentação atual. O token não deve vazar para logs, telemetria, terceiros ou referer.

## 3. Telas e comportamento

### 3.1 Lista de campanhas (Gestão)

- Tabela: nome, período, situação derivada (`Agendada`, `Aberta`, `Encerrada`), **participantes cadastrados**, respostas, taxa de resposta; ordenação recente. Data/hora exibidas no fuso adotado pelo Portal.
- Ação **Nova campanha** abre formulário enxuto: nome, início, fim e confirmação. Datas editáveis conforme backend. Não criar edição do questionário.
- Ao abrir uma campanha: detalhe da campanha (não modal com todas as ações). Loading, vazio, erro/retry, acesso negado; manter filtros básicos de campanha se existirem.
- O frontend **não calcula** situação, validade do convite ou taxa: usa o valor/contrato retornado pela API, sem criar relógio de autoridade.

**Fluxo confirmado de configuração (11/11/2026):** ação **Nova campanha** persiste nome/datas e abre a configuração/detalhe daquela campanha; ali o usuário seleciona clientes TOTVS (um ou muitos), configura/salva mensagem padrão por campanha e vê a lista acumulada. Pode retornar à **campanha ainda aberta** para adicionar mais clientes, com inclusão parcial por lote, sem modificar participantes/links anteriores ou respostas definitivas. Ao abrir o detalhe de cada empresa da lista, copia mensagem resolvida com nome/link exclusivos, sem envio pelo Portal. A situação e autorização de cada inclusão são validadas pela `commercial-api`; inclusão pós-encerramento não autorizada, alterações posteriores em campanhas agendadas sujeitas a contrato e verificação. Isso não é um assistente obrigatório nem uma criação única e imutável de participantes.

### 3.2 Detalhe da campanha — participantes e convites (Gestão)

- Cabeçalho com nome, janela e situação. Seções **Participantes** e **Respostas** dentro da página; sem hierarquia adicional de telas nesta versão.
- **Seleção múltipla e inclusão em lote aprovadas (11/11/2026):** buscar empresas pelo fluxo existente `commercial-api → api-delpi/TOTVS`, selecionar **vários pares completos** `customer_code/customer_store`, revisar a seleção e adicionar à campanha em uma operação com validação final no backend. Não criar cliente no Portal. Não confundir inclusão em lote com envio de convites; nenhum disparo automático. **Inclusão parcial APROVADA em 11/11/2026:** gravar empresas válidas, preservar as já incluídas e exibir falhas por empresa, com motivo seguro e totais. Contrato REST, formato do resultado e suporte HTTP são **PENDING** de implementação.
- Tabela de participantes: empresa (nome + código/loja), contato/e-mail opcional do convite, **Pendente/Respondido** e ações **Editar contato**, **Copiar link** / **Copiar mensagem**. **Edição de contato em diálogo próprio por participante aprovada (11/11/2026)**: nome e e-mail opcionais, pré-preenchidos e gravados somente no contexto do convite mediante validação/autorização da `commercial-api`, sem editar TOTVS nem vínculo/token. A tabela fica em leitura; cancelar não salva; sucesso depende de resposta confirmada do backend. Não exibir “Enviado”, “Entregue” ou contadores de tentativas, pois o Portal não controla esses eventos.
- **Editor único de mensagem personalizável, aprovado em 11/11/2026:** corpo editável e assunto para e-mail, prévias/cópias por canal (**HTML formatado + texto simples para e-mail; texto para WhatsApp e Teams**). Inserir obrigatoriamente **nome da empresa selecionada** a partir da referência oficial TOTVS/`commercial-api` e **link exclusivo da empresa** por resolução segura de campos dinâmicos; nunca copiar nome/link de outro participante. **Decisão posterior (11/11/2026): configuração persistente da mensagem padrão POR CAMPANHA; salvar no detalhe da pesquisa, voltar à listagem pesquisável de participantes e abrir o detalhe da empresa para prévia/cópia com nome/link resolvidos**; sem criar CRUD genérico de templates. **O editor terá apenas dois campos dinâmicos definidos em código, `{nome_empresa}` e `{link_pesquisa}`, reconhecidos/destacados no texto, digitáveis ou inseridos por controle na posição do cursor; sem cadastro de campos nem editor rico complexo.** Não criar botão **Enviar e-mail**: a ação é exclusivamente de **copiar para colar externamente**. Testar HTML/clipboard nos aplicativos reais; copiar novamente usa o mesmo link, sem gerar token no navegador.
- Ação de remover participante (R09) **não aparece na primeira entrega**, salvo definição e implementação segura posterior.
- As respostas por empresa aparecem apenas para quem tem gestão; clicando em **Ver resposta**, navegar à **UI-07 — página independente**, sem modal/drawer, exibindo notas individuais e os três comentários em leitura. Sem edição ou exclusão.
- **Rotas fechadas em spec (auditoria 11/11/2026, não implementadas):** UI-06 `/apps/commercial/satisfaction-survey-responses`; UI-07 `/apps/commercial/satisfaction-survey-responses/:responseId` + `returnTo`/`returnLabel`. Ver [UI-07 §1.1](./UI-07-DETALHES-RESPOSTA.md#11-contrato-de-rota-e-navegação-g02--closed_spec-não-implementado). `RatingDots` = `CLOSED_SPEC` no PluginUI; página UI-07 e R13 = pendentes.

### 3.3 Formulário externo (Cliente)

1. Tela inicial: identificação clara de que é a Pesquisa de Satisfação da DELPI, período, nota de privacidade/finalidade aprovada e **Iniciar pesquisa**. Não exibir dados de outras empresas nem exigir login no Portal.
2. Um formulário responsivo em **três etapas principais sequenciais** (decisão posterior de 11/11/2026), com indicador percentual no topo que atualiza a cada resposta; distribuição **aprovada**: dimensões 01–05 na etapa 1, dimensões 06–10 na etapa 2, e satisfação geral, recomendação e três comentários opcionais na etapa 3. **Cálculo aprovado:** percentual = avaliações obrigatórias respondidas / 12 × 100, com atualização por resposta; os três comentários opcionais não contam e 100% não representa envio. Preservar **10 dimensões**, **satisfação geral**, **recomendação NPS** e **3 perguntas abertas**. O texto, ordem e escala vêm do contrato oficial versionado; nenhum componente muda a redação. Cada dimensão apresenta nota 1–5 e opção **Não se aplica**; satisfação geral 1–5 e NPS 0–10 são obrigatórios; três abertas são opcionais.
3. **Concluir as avaliações obrigatórias da etapa atual antes de avançar (decisão aprovada)**: cinco escolhas nas etapas 1 e 2 (incluindo “Não se aplica”), e as duas notas obrigatórias na etapa 3; os três comentários não bloqueiam. Indicar campos pendentes e manter as escolhas ao voltar. **Na revisão final, apresentar três blocos e um botão “Editar” em cada seção (decisão aprovada)**, para retornar diretamente à etapa correspondente e depois à revisão, preservando respostas, sem percorrer as outras etapas novamente. Indicar claramente que, após a confirmação, a resposta não poderá ser alterada.
4. **Enviar resposta** realiza um único POST e espera confirmação do servidor. Travar ação enquanto a gravação estiver em curso; tratar duplicidade/conflito como **Já respondido** e não reenviar silenciosamente.
5. **Tela simples de agradecimento aprovada (11/11/2026):** somente depois da confirmação da `commercial-api`, exibir “Obrigado por participar!” e mensagem breve, **sem resumo das notas/comentários, sem segunda resposta e sem links internos**. Estados específicos **Ainda não aberta**, **Encerrada**, **Link inválido** e **Resposta já registrada** permanecem distintos do sucesso e não revelam informações sensíveis. Se houver falha temporária de rede, manter dados locais durante a sessão para nova tentativa, sem prometer persistência no backend. **Saída antes do envio (aprovado em 11/11/2026):** advertir sobre possível perda do preenchimento ao abandonar/recarregar o formulário, usando comportamento nativo do navegador quando aplicável e confirmação nas navegações internas suportadas; **sem rascunho persistente** em navegador ou API. Não garantir que o alerta será exibido em todas as situações, especialmente no celular; navegação entre etapas e revisão não deve dispará-lo.

**Acessibilidade:** controles radio com rótulos e agrupamento semântico, navegação por teclado, descrições de escala, foco previsível, mensagens de erro junto ao campo, contraste e layout móvel; não substituir escala por emoji como único indicador. **Decisão visual aprovada (11/11/2026):** escalas 1–5 com botões/alternativas **numéricas** e legenda sempre visível (1 Muito insatisfeito; 2 Insatisfeito; 3 Neutro; 4 Satisfeito; 5 Muito satisfeito); “Não se aplica” exclusivo nas dez dimensões, ausente na satisfação geral. Não usar estrelas nem emojis. A recomendação continua com escala própria 0–10.

### 3.4 Análise detalhada dos resultados (Access e Gestão)

- Filtro principal por campanha/intervalo; indicadores canônicos **IGS**, **NPS**, **Taxa de resposta**, **Satisfeitos (%)** e **Críticos (%)**; médias e número de respostas válidas nas 10 dimensões; evolução semestral/anual e comparação com pesquisa anterior.
- Tabela comparativa **Geral / Clientes estratégicos / Demais** como a do plano, somente quando os segmentos tiverem fonte oficial e agregação segura. Não usar números do exemplo do plano como dados reais.
- Filtros previstos: cliente, segmento, vendedor, região, tempo de relacionamento, faturamento e estratégico/demais. **Habilitar apenas filtros implementados com dados oficiais**, respeitando contrato do backend. Se filtro solicitado não estiver disponível, indicar ausência de suporte; não montar listas de opções falsas.
- **Somente resultados agregados** para `commercial.access`: não renderizar nome/nota/comentário individual, lista de convidados nem drill-down que permita reidentificação; o backend deve suprimir grupos pequenos antes da resposta. Uma seleção de cliente individual não pode revelar sua resposta para Access, ainda que a interface tenha filtro previsto no plano.
- Para Gestão, a consulta individual fica na página da campanha, usando endpoints restritos. **Indicador de planos de ação concluídos não estará disponível nesta versão** e não deve ser exibido como `0`.
- Tratar carregamento, ausência de campanhas, nenhuma resposta, amostra insuficiente para agregação e indisponibilidade real como estados distintos. Exibir denominadores/contagens de amostras e rótulos das fórmulas oficiais, sem cálculo de números no navegador.

### 3.5 Seção "Pesquisa de Satisfação do Cliente" na Visão Geral (decisão 11/11/2026)

**Decisão funcional:** manter **uma única seção chamada "Pesquisa de Satisfação do Cliente"** na página **Visão Geral** que já existe no MFE Comercial. A seção mostra o conjunto de indicadores gerais da primeira entrega, e não apenas um card de IGS. Não criar nova página para esse resumo, nem novas entradas de menu ou seções separadas por indicador.

**Composição enxuta da seção:** mostrar a última campanha encerrada e seu período; IGS (1–5), NPS (-100 a +100), taxa de resposta (respondentes/participantes), porcentagem de satisfeitos (notas 4–5), porcentagem de críticos (notas 1–2), médias das dez dimensões e evolução em relação à campanha anterior, quando houver. Usar os componentes existentes da Visão Geral (`SectionCard`, `CommercialMetricCard`/`CommercialDashboardKpiCard` e visualização compacta); não duplicar o painel detalhado.

**Acesso:** todos os usuários autorizados do Comercial com `commercial.access` e os perfis gestores com `commercial.marketing` ou `commercial.manage`, conforme contrato backend. Apenas dados consolidados: não carregar nem mostrar empresas identificadas, notas e comentários individuais ou tokens. A autoridade para agregar e suprimir grupos pequenos é a `commercial-api`; o frontend não recalcula esses valores nem substitui a autorização.

**Consulta:** reutilizar `GET /satisfaction-surveys/results` com seleção da última campanha encerrada e uma projeção de resumo, sem nova rota por indicador. O resumo é geral, independente dos filtros de pedidos, carteira e faturamento da Visão Geral.

**Navegação:** ação discreta **"Ver análise completa"** para a página de resultados da pesquisa, onde ficam filtros, segmentações e comparações detalhadas; respostas por empresa continuam exclusivas de Marketing/Manage em sua área restrita.

**Estados:** sem pesquisa encerrada, sem respostas, amostra insuficiente, carregamento ou erro devem aparecer corretamente, sem inventar zero nem expor valores que permitam reidentificação. O indicador de **planos de ação concluídos** do Word será acrescentado na **entrega 2**, quando houver dados oficiais de ações; não mostrar zero na entrega 1.

**Verificação por etapa:** garantir a apresentação dos indicadores gerais, a fidelidade aos cálculos da API, a restrição da informação, a navegação e a responsividade. **Planejado, não implementado.**

## 4. Mapa de contrato frontend → backend

| Interação | Fonte REST proposta | Autorização |
|---|---|---|
| Lista/criação/edição de campanha | `GET/POST /satisfaction-surveys/campaigns`, `GET/PATCH /satisfaction-surveys/campaigns/{id}` | Gestão |
| Consulta de cliente | Cliente oficial já disponível por `/customers/search` na commercial-api | Gestão no novo fluxo; servidor revalida |
| Selecionar/listar participantes | `GET/POST /satisfaction-surveys/campaigns/{id}/recipients` | Gestão |
| Ajustar e-mail/contato | `PATCH /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}` | Gestão |
| Copiar link | `GET /satisfaction-surveys/campaigns/{id}/recipients/{recipientId}/link` | Gestão |
| Respostas identificadas | `GET /satisfaction-surveys/campaigns/{id}/responses`, `GET /satisfaction-surveys/responses/{id}` | Gestão |
| Formulário público | `GET /public/satisfaction-surveys/{token}`, `POST .../{token}/response` | Link válido, sem JWT interno |
| Resumo e comparação | `GET /satisfaction-surveys/results` | Access ou Gestão; privacidade da agregação no backend |
| Seção da Visão Geral | Mesmo serviço agregado de resultados, seleção da última campanha encerrada e resumo dos indicadores gerais | `commercial.access`, sem respostas individuais |

**Clientes HTTP:** usar `plugins/commercial/src/api/httpClient.ts` e respostas/erros oficiais para gestão e indicadores, criando `satisfactionSurveysApi.ts` quando necessário. Para a página pública, usar `plugins/public-hub/src/apps/commercial/api.ts`, seguindo o `fetch` sem bearer do módulo público existente. **Não chamar `api-delpi` diretamente**. O código público pertence ao shell público compartilhado, sem assumir o CRUD de formulários de Customer Experience.

## 5. Permissões e navegação

- **Gestão** `commercial.marketing` OU `commercial.manage`: criar campanhas, selecionar participantes, copiar convites e ver respostas detalhadas.
- **Indicadores agregados** `commercial.access` ou Gestão: consultar resultados com supressão segura de grupos.
- **Cliente externo**: formulário somente com token de convite. Sem login.
- A apresentação/ocultação de ações na UI **não autoriza** nada; a API valida todas as operações. O app atual resolve capacidades de carteiras no `PortfolioScopeContext`; a implementação deve **não** inferir `marketing` a partir de `manage` nem misturar carteira e pesquisa. O contrato de capacidades deverá ser encaixado na fonte real de RBAC do host/backend, sem elevar escopo.
- Atualizar `commercial.manifest.json` e os catálogos de rotas/menus **durante implementação** de Marketing, preservando `commercial.access` e `commercial.manage`. Não criar `commercial.surveys.*` ou outros códigos.

## 6. Incrementos e critérios de aceite

| Incremento | Interface entregável | Validação junto ao backend/CAIO |
|---|---|---|
| FE-1 | Lista/criação/detalhe de campanhas; seleção de clientes, tabela e link copiável | Unicidade de destinatário, janela, capacidades; `read`/`execute` no CAIO com mesmos casos de uso |
| FE-2 | Formulário externo responsivo, revisão, envio único, sucesso/estados de erro | Token público, escalas, NPS, concorrência e imutabilidade; **não** expor submissão externa pelo CAIO |
| FE-3 | Painel de resultados, filtros oficiais, comparação e respostas individuais restritas | IGS/NPS calculados na API, proteção de agregados, `analyze` e `read` no CAIO com paridade |

**Testes por incremento:** roteamento e navegação; permissões nas interfaces e no backend; contrato HTTP e erros; cópia sem regenerar link; ausência de botões de envio e planos de ação; formulário por teclado/móvel; escala/validação/revisão; duplicidade e erro de rede; não exposição de detalhes a `access`; filtros e supressão no backend; nenhuma chamada direta do Portal a `api-delpi`; testes CAIO/paridade e relatório de execução por prompt.

## 7. Limites do planejamento

**Fechado agora:** duas páginas internas no MFE Comercial, uma única seção **Pesquisa de Satisfação do Cliente** na Visão Geral existente e um formulário por token em `public-hub`, rota candidata `/p/commercial/form/{token}`, experiências e contratos HTTP. **A confirmar apenas na implementação:** teste do roteamento `/p/` e GET/POST públicos, mecanismo oficial de capability Marketing no host, componentes exatos e disponibilidade de filtros oficiais. O padrão de hospedagem pública já existe; não reabrir sua arquitetura sem bloqueio comprovado. Esses pontos não exigem nova rodada geral de descoberta.

**Não criar outros documentos/fluxos sem bloqueio material.** Executar a frente com HEAD, branch, working tree, owners e testes confirmados e menor diff; registrar resultado de execução no índice após prova.