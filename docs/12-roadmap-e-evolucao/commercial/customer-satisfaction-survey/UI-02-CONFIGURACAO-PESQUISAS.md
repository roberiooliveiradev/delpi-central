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