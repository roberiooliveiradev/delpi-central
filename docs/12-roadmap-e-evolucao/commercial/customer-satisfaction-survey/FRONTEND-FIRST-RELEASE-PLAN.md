# Frontend — Pesquisa de Satisfação de Clientes (primeira entrega)

> **Status: PLANEJAMENTO FUNCIONAL/TÉCNICO PROPOSTO, NÃO IMPLEMENTADO.** Em 11/11/2026; base consultada: branch `main`, HEAD `1e75d95d000bda6c664c246ee0ba67f27a31a7a3` (revalidar antes de modificar código). Não há telas de pesquisa identificadas no plugin atual.
>
> **Fontes canônicas:** [índice mestre](./REQUIREMENTS-INDEX.md), [decisões](./BUSINESS-DECISIONS.md), [contrato da primeira entrega](./SURVEY-FIRST-RELEASE-CONTRACT.md) e o plano integral nas fontes do projeto. Este documento descreve **a interface para o escopo aprovado**, não altera o ownership ou aprova desenvolvimento de planos de ação.

## 1. Escopo e experiência

**Entregar nesta versão:** o usuário autorizado cria campanha, seleciona empresas TOTVS, copia link/mensagem e distribui **por conta própria**, acompanha respostas e analisa resultados. O cliente abre o formulário pelo link, revisa e envia uma resposta definitiva. O Comercial usa os resultados para suas ações **fora da aplicação**.

**Não entregar:** disparo de e-mail, integração WhatsApp/Teams, envio em lote, lembretes automáticos, confirmação de entrega, CRUD das perguntas, editor de respostas definitivas, telas/tarefas de planos de ação, retorno ou reavaliação, nova permissão além de `commercial.marketing`, novo MCP/novas tools. O CAIO é estendido por entidade/ação em cada etapa do backend, não pelo frontend.

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

### 3.2 Detalhe da campanha — participantes e convites (Gestão)

- Cabeçalho com nome, janela e situação. Seções **Participantes** e **Respostas** dentro da página; sem hierarquia adicional de telas nesta versão.
- Buscar cliente pelo fluxo existente `commercial-api → api-delpi/TOTVS`, selecionar o par completo `customer_code/customer_store` e adicionar à campanha. Não criar cliente no Portal.
- Tabela de participantes: empresa (nome + código/loja), contato/e-mail opcional do convite, **Pendente/Respondido** e ações **Copiar link** / **Copiar mensagem**. Permitido ajustar contato do convite sem editar TOTVS. Não exibir “Enviado”, “Entregue” ou contadores de tentativas, pois o Portal não controla esses eventos.
- **Copiar mensagem** monta texto do convite com link estável retornado pela API; pode usar um texto aprovado no próprio cliente, sem template CRUD de campanha. Não criar botão **Enviar e-mail**. Copiar novamente usa o mesmo link; não gerar token no navegador.
- Ação de remover participante (R09) **não aparece na primeira entrega**, salvo definição e implementação segura posterior.
- As respostas por empresa aparecem apenas para quem tem gestão; clicando numa linha, visualizar notas, NPS e três respostas abertas em painel de leitura. Sem edição ou exclusão.

### 3.3 Formulário externo (Cliente)

1. Tela inicial: identificação clara de que é a Pesquisa de Satisfação da DELPI, período, nota de privacidade/finalidade aprovada e **Iniciar pesquisa**. Não exibir dados de outras empresas nem exigir login no Portal.
2. Um único formulário responsivo, dividido visualmente em **10 dimensões**, **satisfação geral**, **recomendação NPS** e **3 perguntas abertas**. O texto, ordem e escala vêm do contrato oficial versionado; nenhum componente muda a redação. Cada dimensão apresenta nota 1–5 e opção **Não se aplica**; satisfação geral 1–5 e NPS 0–10 são obrigatórios; três abertas são opcionais.
3. **Revisar respostas** antes de submeter, com opção Voltar e corrigir. Indicar claramente que, após a confirmação, a resposta não poderá ser alterada.
4. **Enviar resposta** realiza um único POST e espera confirmação do servidor. Travar ação enquanto a gravação estiver em curso; tratar duplicidade/conflito como **Já respondido** e não reenviar silenciosamente.
5. Tela de sucesso; estados específicos **Ainda não aberta**, **Encerrada**, **Link inválido** e **Resposta já registrada** sem revelar informações sensíveis. Se houver falha temporária de rede, manter dados locais durante a sessão para nova tentativa, sem prometer persistência no backend.

**Acessibilidade:** controles radio com rótulos e agrupamento semântico, navegação por teclado, descrições de escala, foco previsível, mensagens de erro junto ao campo, contraste e layout móvel; não substituir escala por emoji como único indicador.

### 3.4 Resultados e indicadores (Access e Gestão)

- Filtro principal por campanha/intervalo; indicadores canônicos **IGS**, **NPS**, **Taxa de resposta**, **Satisfeitos (%)** e **Críticos (%)**; médias e número de respostas válidas nas 10 dimensões; evolução semestral/anual e comparação com pesquisa anterior.
- Tabela comparativa **Geral / Clientes estratégicos / Demais** como a do plano, somente quando os segmentos tiverem fonte oficial e agregação segura. Não usar números do exemplo do plano como dados reais.
- Filtros previstos: cliente, segmento, vendedor, região, tempo de relacionamento, faturamento e estratégico/demais. **Habilitar apenas filtros implementados com dados oficiais**, respeitando contrato do backend. Se filtro solicitado não estiver disponível, indicar ausência de suporte; não montar listas de opções falsas.
- **Somente resultados agregados** para `commercial.access`: não renderizar nome/nota/comentário individual, lista de convidados nem drill-down que permita reidentificação; o backend deve suprimir grupos pequenos antes da resposta. Uma seleção de cliente individual não pode revelar sua resposta para Access, ainda que a interface tenha filtro previsto no plano.
- Para Gestão, a consulta individual fica na página da campanha, usando endpoints restritos. **Indicador de planos de ação concluídos não estará disponível nesta versão** e não deve ser exibido como `0`.
- Tratar carregamento, ausência de campanhas, nenhuma resposta, amostra insuficiente para agregação e indisponibilidade real como estados distintos. Exibir denominadores/contagens de amostras e rótulos das fórmulas oficiais, sem cálculo de números no navegador.

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

**Fechado agora:** duas páginas internas no MFE Comercial e um formulário por token em `public-hub`, rota candidata `/p/commercial/form/{token}`, experiências e contratos HTTP. **A confirmar apenas na implementação:** teste do roteamento `/p/` e GET/POST públicos, mecanismo oficial de capability Marketing no host, componentes exatos e disponibilidade de filtros oficiais. O padrão de hospedagem pública já existe; não reabrir sua arquitetura sem bloqueio comprovado. Esses pontos não exigem nova rodada geral de descoberta.

**Não criar outros documentos/fluxos sem bloqueio material.** Executar a frente com HEAD, branch, working tree, owners e testes confirmados e menor diff; registrar resultado de execução no índice após prova.