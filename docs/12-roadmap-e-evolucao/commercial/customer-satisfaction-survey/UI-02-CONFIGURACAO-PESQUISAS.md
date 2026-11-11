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
- **Persistência:** aprovado **editar antes de copiar**, mas **não** está aprovado guardar versões de texto por campanha/participante, criar CRUD de templates ou logar conteúdo. Política de reutilização do texto ao preparar convite para outra empresa continua **PENDING**; manter requisito de nome e link específicos independentemente dessa decisão.
- **Validação e testes:** verificar dois clientes com nomes diferentes e códigos/lojas distintos, mudanças de seleção, prevenção de link/nome cruzados, caracteres especiais/HTML malicioso, falta de nome oficial, equivalência entre as três prévias, clipboard negado, compatibilidade Outlook/WhatsApp/Teams, fluxo por teclado e **ausência completa de disparo**.
- **Estado:** decisão funcional/UX **APROVADA e documentada**; implementação, representação de placeholders, compatibilidade HTML e aprovação do texto institucional por Marketing **PENDING**.

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