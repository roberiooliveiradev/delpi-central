# CRM Minha DELPI — Visão Funcional, Escopo Mestre e Catálogo de Capacidades

> **Produto:** Minha DELPI — Portal Comercial  
> **ID técnico atual:** `commercial`  
> **Frontend:** `plugins/commercial`  
> **Backend de domínio:** `commercial-api`  
> **Integração operacional:** `api-delpi` → TOTVS/Protheus e demais fontes corporativas  
> **Governança:** Core API + Keycloak + RBAC da Minha DELPI  
> **Status deste documento:** visão funcional alvo e catálogo mestre de requisitos  
> **Data-base da análise:** 21 de agosto de 2026  
> **Atualização:** gaps de rituais (Agendor) + funil Kanban omnicanal de conversas (benchmark ChatGuru, adaptado a Teams/Outlook/redes)

---

## 1. Finalidade deste documento

Este documento define a visão funcional completa do **CRM Minha DELPI**, que será desenvolvido como evolução nativa do **Portal Comercial**.

O objetivo é transformar o Portal Comercial atual em uma plataforma integrada de relacionamento, marketing, prospecção, vendas, colaboração e gestão comercial, cobrindo toda a jornada B2B industrial:

```text
Mercado e empresas-alvo
  ↓
Visitante / contato identificado
  ↓
Lead / prospect
  ↓
Qualificação
  ↓
Oportunidade
  ↓
Apresentação / desenvolvimento / amostra
  ↓
Proposta
  ↓
Negociação
  ↓
Pedido no ERP
  ↓
Confirmação / produção / faturamento / entrega
  ↓
Relacionamento, expansão, recorrência e reativação
```

O CRM não será apenas um cadastro de oportunidades. Ele deverá preservar o histórico corporativo completo do relacionamento com cada empresa, permitindo saber:

- como o contato entrou;
- quais campanhas, páginas, mensagens e reuniões antecederam a oportunidade;
- quem participou de cada interação;
- quanto tempo foi gasto até a conversão;
- quais produtos e soluções despertaram interesse;
- quais propostas, pedidos, faturamentos e entregas decorreram da negociação;
- por que uma oportunidade foi ganha, perdida, adiada ou desqualificada;
- quais são o próximo passo, o risco e a responsabilidade atual;
- como continuar o atendimento quando o responsável estiver ausente;
- quais oportunidades de expansão, recorrência ou recuperação existem na conta.

---

## 2. Método de análise

A definição foi construída a partir de quatro grupos de fontes:

1. **Código atual do repositório Minha DELPI**
   - `commercial-api/commercial_app/**`;
   - `commercial-api/migrations/**`;
   - `plugins/commercial/src/**`;
   - `plugins/commercial/commercial.manifest.json`;
   - regras de arquitetura em `.cursor/rules/**`.

2. **Documentação atual do Portal Comercial**
   - `docs/12-roadmap-e-evolucao/commercial/**`;
   - inventário de ativos, rotas, modelo de dados, gestão à vista, tarefas, escopo, perfis, atas e roadmap.

3. **Documentação geral da Minha DELPI**
   - visão geral e arquitetura;
   - autenticação e autorização;
   - Core API, RBAC, JWT, eventos, notificações e Socket.IO;
   - Portal, plugins, manifestos, Gateway, bancos e ambientes.

4. **Necessidades levantadas em reuniões e análise de mercado**
   - histórico desde a prospecção;
   - campanhas, segmentação, rastreamento e qualificação;
   - múltiplos processos comerciais;
   - produtividade, agenda, mensagens, inteligência e integração ao ERP;
   - continuidade do relacionamento durante férias, afastamentos e trocas de carteira;
   - leitura controlada de comunicações corporativas, inclusive Microsoft Teams e Outlook.

5. **Benchmark de CRM B2B (Agendor)** — [rituais de vendas](https://www.agendor.com.br/blog/rituais-de-vendas/) e [soluções](https://www.agendor.com.br/solucoes)
   - rituais diários do vendedor (preparação do dia seguinte, lista, script, histórico pré-contato, atualização pós-abordagem);
   - rituais de gestão (sumário semanal, forecast, 1-on-1, alinhamento marketing–vendas);
   - mapa de vendas / saúde do funil, fluxo inteligente de atividades, sumário semanal/mensal;
   - múltiplos funis com handoff, congelamento de negócios, mapa de visitas e rotas.

6. **Benchmark de funil Kanban de conversas (ChatGuru)** — [funil estilo Trello no WhatsApp](https://chatguru.com.br/blog/como-fazer-funil-de-vendas-no-whatsapp-no-estilo-do-trello/)
   - quadro Kanban em que cada **cartão é uma conversa** (não só a oportunidade);
   - múltiplos funis (atendimento, vendas, produção/pós-venda) com etapas como colunas;
   - entrada automática por gatilho/diálogo/chatbot e movimentação por automação;
   - adição em lote de conversas, tags, anotações de equipe e visibilidade só dos cartões atribuídos;
   - **adaptação DELPI:** o mesmo padrão vale para Microsoft Teams, Outlook/e-mail, WhatsApp corporativo, web chat e redes sociais autorizadas, com ingestão normalizada no CRM — não amarrar o funil a um único canal.

### 2.1 Legenda de maturidade

| Símbolo | Situação | Significado |
|---|---|---|
| **E** | Existente | Confirmado no código, rotas, migrations ou interface atual |
| **P** | Parcial | Existe uma base funcional, mas o requisito-alvo é mais amplo |
| **B** | Backlog documentado | Já está especificado ou registrado no roadmap, mas não foi entregue por completo |
| **N** | Novo requisito | Deve ser incluído no CRM-alvo e ainda não possui entrega confirmada |
| **D** | Dependência externa | Exige política, contrato, consentimento, API ou dado de outro sistema |

> A legenda diferencia de forma explícita o que já existe do que ainda será desenvolvido. Uma linha marcada como **B**, **N** ou **D** não deve ser apresentada como funcionalidade disponível hoje.

---

## 3. Descrição do produto

O **CRM Minha DELPI** será o sistema corporativo de gestão do relacionamento comercial da DELPI, integrado à experiência da Minha DELPI e especializado no contexto B2B industrial.

Ele deverá reunir, em uma única experiência:

- gestão de empresas, grupos econômicos, unidades e contatos;
- prospecção e qualificação de novos negócios;
- marketing baseado em contas e segmentos;
- campanhas, formulários, automações e rastreamento da jornada;
- múltiplos funis comerciais;
- oportunidades, propostas, negociação e aprovações;
- tarefas, cadências, visitas, reuniões e agenda;
- histórico omnicanal de e-mail, Teams, mensageria, chamadas e interações internas;
- informações do ERP, pedidos, produção, faturamento e entrega;
- carteira de clientes, territórios e distribuição de leads;
- previsão de vendas, metas e cenários;
- indicadores, atribuição, CAC, conversão e produtividade;
- colaboração em tempo real e notificações;
- copiloto de inteligência artificial com rastreabilidade e confirmação humana;
- APIs, webhooks e conectores corporativos;
- governança, LGPD, auditoria e controle de acesso.

### 3.1 Resultado esperado

O produto deve permitir que qualquer usuário autorizado compreenda uma conta sem depender da memória individual de outro colaborador.

Ao abrir uma empresa, o usuário deve visualizar uma linha do tempo coerente contendo, conforme sua permissão:

```text
Campanhas e origem
→ visitas ao site e conversões
→ contatos e interesses
→ e-mails e mensagens
→ conversas e reuniões
→ tarefas e follow-ups
→ oportunidades e propostas
→ pedidos e produção
→ faturamento e notas fiscais
→ ocorrências de entrega
→ próximos passos e oportunidades futuras
```

---

## 4. Princípios obrigatórios do CRM

### 4.1 Sistema corporativo, não agenda pessoal

O histórico comercial pertence à DELPI e deve permanecer acessível às pessoas autorizadas, mesmo quando houver férias, afastamento, desligamento, mudança de função ou transferência de carteira.

### 4.2 ERP e CRM possuem papéis diferentes

O CRM controla pré-venda, relacionamento, atividades, oportunidades e inteligência comercial. O ERP permanece mestre das transações operacionais e fiscais.

### 4.3 Uma única experiência comercial

Novas capacidades devem ser incorporadas ao Portal Comercial, evitando criar telas concorrentes, listas paralelas ou cadastros duplicados sem necessidade arquitetural.

### 4.4 Regra de negócio no backend de domínio

O MFE não deve calcular escopo, membership, autorização, atribuição ou regras críticas. Essas regras pertencem à `commercial-api`.

### 4.5 Acesso ao ERP somente pela fronteira correta

O fluxo obrigatório é:

```text
plugins/commercial
  ↓
commercial-api
  ↓
api-delpi
  ↓
TOTVS / Protheus
```

O MFE não deve chamar a `api-delpi` diretamente.

### 4.6 Autenticação e autorização separadas

```text
Keycloak → autentica
Core API → resolve permissões e apps
commercial-api → aplica autorização e escopo de negócio
Portal Comercial → renderiza a experiência autorizada
```

### 4.7 Privacidade por projeto

Integrações com e-mail, Teams, mensagens, chamadas, gravações e transcrições devem seguir minimização de dados, finalidade comercial, consentimento, retenção, auditoria e menor privilégio.

### 4.8 Automação com supervisão

A automação deve reduzir trabalho manual, mas decisões sensíveis — preço, desconto, prazo, compromisso comercial, envio externo e alteração crítica — devem exigir confirmação humana ou política formal de aprovação.

### 4.9 Evento após persistência

Eventos, notificações e sincronizações devem ser publicados somente após commit bem-sucedido, usando outbox e processamento idempotente quando houver efeito externo.

### 4.10 Conteúdo explicável

Indicadores, scores, recomendações e respostas de IA devem indicar origem, data de atualização e fatores que sustentam o resultado.

---

## 5. Fronteiras e sistemas mestres

| Dado ou responsabilidade | Sistema mestre | Uso no CRM |
|---|---|---|
| Login, sessão e identidade | Keycloak | Autenticação SSO e JWT |
| Apps, rotas e permissões da plataforma | Core API | Governança, RBAC, menu e notificações |
| Carteiras, memberships, tarefas e colaboração comercial | `commercial-api` | Persistência e regra de negócio nativa |
| Prospects, leads e oportunidades nativas | `commercial-api` | Fonte oficial do novo CRM |
| Campanhas, automações e eventos de jornada | `commercial-api` e serviços especializados do domínio | Fonte oficial de marketing e atribuição |
| Cadastro fiscal de cliente | TOTVS/Protheus | Leitura pela `api-delpi`; extensão local sem sobrescrever o mestre |
| Produtos, famílias, preços e tabelas | TOTVS/Protheus | Leitura e validação; cache controlado quando necessário |
| Pedidos, itens, estoque e produção | TOTVS/Protheus | Leitura viva via `api-delpi` |
| Notas fiscais, faturamento e financeiro | TOTVS/Protheus | Leitura autorizada; dados sensíveis protegidos |
| Contatos comerciais complementares | `commercial-api` | CRUD local; contato canônico do ERP continua somente leitura |
| E-mails e calendário corporativos | Microsoft 365 | Sincronização seletiva e referência no histórico |
| Conversas e reuniões corporativas | Microsoft Teams | Sincronização seletiva, autorizada e auditável |
| Mensageria externa | Conector oficial do canal | Conversas vinculadas e eventos normalizados |
| Arquivos comerciais | Storage persistente do domínio ou repositório corporativo | Metadados, autorização, versionamento e download |
| Indicadores corporativos | `commercial-api` + `api-delpi` + demais APIs | Composição sem duplicar regra nas telas |

### 5.1 Regra para dados externos

O CRM não deve copiar indiscriminadamente toda a base de sistemas externos. Deve persistir somente:

- referências estáveis;
- snapshots necessários para auditoria;
- eventos normalizados da jornada;
- dados que precisam ser pesquisados ou correlacionados no domínio;
- conteúdo autorizado para formar o histórico comercial;
- checkpoints, hashes e metadados de sincronização.

---

## 6. Arquitetura funcional alvo

```text
Usuário
  ↓
Gateway Nginx
  ↓
Portal Minha DELPI
  ↓
MFE commercial
  ↓
commercial-api
  ├─ PostgreSQL schema commercial
  ├─ Storage de anexos
  ├─ Realtime / WebSocket
  ├─ Outbox e jobs
  ├─ Conectores Microsoft 365
  ├─ Conector de mensageria
  ├─ Serviço de campanhas e tracking
  ├─ Serviço de IA corporativa
  └─ Gateway api-delpi
        ↓
      TOTVS / Protheus e demais fontes operacionais

Core API
  ├─ usuários e RBAC
  ├─ apps e manifesto
  ├─ notificações do Portal
  └─ auditoria da plataforma
```

---

## 7. Inventário do que existe atualmente

| Capacidade atual | Situação | Observação |
|---|---:|---|
| Home comercial com eventos, busca, favoritos e atalhos | **E** | Base para o novo cockpit diário |
| Visão geral com ROL, conversão, OTD, carteira e séries | **E** | Deve receber indicadores adicionais do CRM |
| Carteiras multiusuário e membership | **E** | Fonte atual de escopo comercial |
| Administração de carteiras e membros | **E** | Inclui carteiras órfãs e transferência de clientes |
| Grupos operacionais | **E** | Diferentes de papéis RBAC |
| Lista de clientes da carteira | **E** | Com enriquecimento e indicadores do ERP |
| Conta 360 | **P** | Possui resumo, pedidos, histórico, oportunidades, contatos e atividades; falta timeline omnicanal completa |
| Contatos locais da conta | **E** | Cadastro TOTVS permanece somente leitura |
| Pedidos em aberto | **E** | Filtros, tabela, cards, board e escopo comercial |
| Alocação FIFO e indicação “Pode faturar” | **E** | Alimenta operação e notificações |
| Detalhe de pedido e item | **E** | Com informações operacionais e links de contexto |
| Detalhe de ordem de produção | **E** | Estrutura, progresso e apontamentos disponíveis |
| Faturamento e notas fiscais da conta | **E** | Leitura autorizada via BFF |
| Propostas e PDF | **E** | Documento comercial atual; não substitui pipeline nativo |
| Oportunidades oriundas do ERP | **P** | Leitura e indicadores existem; falta gestão nativa completa do ciclo |
| OTD e análise de prazo | **E** | Deve se conectar à oportunidade e ao pós-venda |
| Tarefas e worklist | **E** | Criar, editar, concluir, adiar, excluir, reatribuir e filtrar |
| Responsáveis múltiplos e grupos em tarefas | **E** | Com visibilidade por equipe |
| Observações e anexos em tarefas | **E** | Storage persistente e prévia na interface |
| Tarefas concluídas | **E** | Histórico separado da fila aberta |
| Notificações de tarefa e prazo | **E** | Outbox + notificações do Portal + realtime |
| Presença e atualização em tempo real | **E** | WebSocket e eventos de domínio |
| Sala de interação | **E** | Inbox, thread, menções, reações, pins, anexos e criação de tarefa |
| Menções a entidades e preview | **E** | Cliente, pedido e outras entidades do catálogo |
| Auditoria comercial mínima | **E** | Append-only para operações sensíveis já cobertas |
| Perfis comerciais e foto | **E** | Extensão local do diretório corporativo |
| SLA configurável | **P** | Migration e contrato parcial; falta adoção ampla por processos |
| Importação, deduplicação e qualidade de base | **P** | Há enriquecimento e especificação de issues; falta governança completa |
| Prospects e leads nativos | **B** | Modelo e rotas planejados; não confirmados como entrega atual |
| Visitas nativas | **B** | Modelo planejado; integração de agenda e veículo pendente |
| Pipeline nativo e múltiplos funis | **B** | Modelo e rotas planejados; CRUD completo ainda não confirmado |
| Forecast completo | **B** | Especificação futura; declaração simplificada foi removida |
| Confirmação de pedido | **B** | Processo e SLA documentados; não entregue integralmente |
| Amostras e desenvolvimento | **B** | Modelo futuro documentado |
| Exceções de entrega | **B** | Modelo futuro documentado |
| Integração Outlook e Teams | **B** | Registrada como T11; ainda não implementada |
| Inbox compartilhada de e-mail | **B** | Backlog de carteiras E7 |
| Mapa de territórios, rotação e redistribuição assistida | **B** | Backlog E7 |
| Marketing, campanhas e automação | **N** | Novo domínio do CRM-alvo |
| Mensageria omnicanal oficial | **N** | Hoje há apenas dados de contato/deep links, sem inbox corporativa completa |
| Funil Kanban de conversas (multi-canal) | **N** | Quadro estilo Trello com cartão = conversa; benchmark ChatGuru adaptado a Teams/Outlook/redes |
| Copiloto de IA comercial | **N** | Novo domínio, com supervisão humana |

---

## 8. Perfis de usuário e necessidades

| Perfil | Necessidades principais |
|---|---|
| **Vendedor de prospecção / hunter** | Empresas-alvo, cadências, qualificação, primeiro contato, pipeline de aquisição, agenda e conversão |
| **Gestor de conta / farmer** | Conta 360, recorrência, expansão, cross-sell, risco, plano da conta, histórico e relacionamento contínuo |
| **Pré-vendas / SDR** | Filas de leads, scoring, roteamento, cadências, contatos, critérios de qualificação e passagem de bastão |
| **Vendedor técnico** | Produtos, requisitos técnicos, amostras, documentos, reunião, engenharia, proposta e histórico da solução |
| **Orçamentista** | Solicitações, dados técnicos, SLA, versões de proposta, aprovações, preço e retorno ao vendedor |
| **Marketing** | Segmentos, base, formulários, campanhas, automações, jornada, scoring, atribuição e consentimento |
| **Gestor comercial** | Pipeline, forecast, produtividade, conversão, aging, cobertura, carteira, metas, coaching e aprovações |
| **Diretoria** | Indicadores executivos, previsibilidade, risco, receita, rentabilidade, CAC, evolução e exceções |
| **Faturamento** | Pedidos aptos, pendências, notificações, documentos, confirmação e histórico de ação |
| **Engenharia / Qualidade / Produção** | Demandas técnicas, amostras, etapas, SLA, menções e contexto da oportunidade sem acesso indevido a dados comerciais sensíveis |
| **Logística / Atendimento** | Exceções de entrega, comunicação ao cliente, plano de ação e rastreabilidade |
| **Sales Operations** | Configuração, qualidade de dados, integrações, funis, catálogos, automações e auditoria |
| **Administrador** | Usuários, perfis, permissões, conectores, retenção, regras e monitoramento operacional |
| **Auditor / Compliance** | Histórico imutável, consentimentos, acessos, exportações, decisões e trilha de alterações |

---

## 9. Jornadas obrigatórias

### 9.1 Aquisição de novo cliente

```text
Empresa-alvo
→ lead capturado ou importado
→ higienização e deduplicação
→ scoring de perfil e intenção
→ atribuição ao responsável
→ cadência de contato
→ qualificação
→ oportunidade
→ apresentação / amostra
→ proposta
→ negociação
→ aprovação
→ ganho
→ criação ou associação do cliente no ERP
→ pedido
→ relacionamento de conta
```

### 9.2 Expansão de cliente existente

```text
Conta ativa
→ análise de histórico e cobertura de produtos
→ sinal de oportunidade ou campanha segmentada
→ contato com decisor
→ oportunidade de expansão
→ proposta
→ pedido
→ medição de incremento e recorrência
```

### 9.3 Reativação

```text
Conta sem compra no período definido
→ segmento de reativação
→ campanha ou cadência
→ resposta / interesse
→ oportunidade de recuperação
→ nova venda
→ indicador de cliente recuperado
```

### 9.4 Desenvolvimento técnico e amostra

```text
Necessidade do cliente
→ oportunidade técnica
→ requisitos e arquivos
→ desenvolvimento de amostra
→ etapas por área
→ testes / validação
→ aprovação do cliente
→ proposta / pedido
```

### 9.5 Pedido e entrega

```text
Oportunidade ganha
→ pré-pedido / pedido no ERP
→ confirmação de recebimento
→ análise das áreas
→ data firme
→ produção
→ faturamento
→ embarque
→ entrega
→ exceção, quando houver
→ fechamento e lições aprendidas
```

### 9.6 Continuidade durante ausência

```text
Responsável ausente
→ substituto abre Conta 360
→ consulta timeline, conversas e tarefas
→ identifica compromisso e próximo passo
→ continua atendimento
→ registra decisão
→ responsável original recebe resumo no retorno
```

### 9.7 Campanha até receita

```text
Público segmentado
→ campanha
→ entrega / abertura / clique / visita
→ conversão
→ lead qualificado
→ oportunidade
→ proposta
→ pedido
→ faturamento
→ receita atribuída
```

---

## 10. Catálogo detalhado de funcionalidades

### 10.1 Shell, início e navegação comercial

**Objetivo:** transformar o início do Portal Comercial em cockpit de ação, sem duplicar o painel analítico.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-PLT-001 | **E** | Manter início com saudação, eventos, indicadores pessoais, busca, favoritos e rotas recentes. |
| CRM-PLT-002 | **E** | Manter navegação nativa e autorizada pelo manifesto e pela Core API. |
| CRM-PLT-003 | **P** | Consolidar alertas de tarefas, leads, oportunidades, campanhas, mensagens, aprovações e exceções em uma fila priorizada. |
| CRM-PLT-004 | **N** | Oferecer cards personalizados por persona, sem depender de nome de cargo no código. |
| CRM-PLT-005 | **N** | Permitir configuração de widgets pessoais dentro de uma lista aprovada pela administração. |
| CRM-PLT-006 | **N** | Exibir “próxima melhor ação” com explicação dos fatores e link para o registro. |
| CRM-PLT-007 | **N** | Permitir busca global por empresa, contato, lead, oportunidade, proposta, pedido, produto, tarefa, reunião e mensagem. |
| CRM-PLT-008 | **N** | Suportar atalhos de teclado e command palette para criar ou navegar rapidamente. |
| CRM-PLT-009 | **N** | Exibir estado de sincronização das integrações relevantes sem poluir a experiência comum. |
| CRM-PLT-010 | **N** | Preservar deep links e contexto de filtros ao alternar entre lista, conta e detalhe. |

### 10.2 Conta 360 e gestão de empresas

**Objetivo:** fornecer uma visão corporativa completa de cada empresa e de seu relacionamento com a DELPI.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-ACC-001 | **P** | Evoluir a Conta 360 atual para uma visão única de dados comerciais, operacionais e relacionais. |
| CRM-ACC-002 | **E** | Exibir cadastro mestre do ERP como somente leitura, com indicação da origem e atualização. |
| CRM-ACC-003 | **N** | Manter extensão local com nome comercial, descrição, site, segmento, subsegmento, potencial, classificação, tags e observações. |
| CRM-ACC-004 | **N** | Representar grupo econômico, matriz, filiais, unidades e subgrupos comerciais. |
| CRM-ACC-005 | **N** | Permitir classificação de conta: prospect, ativa, inativa, estratégica, risco, recuperação e encerrada. |
| CRM-ACC-006 | **N** | Calcular saúde da conta com fatores explicáveis: compra, frequência, atraso, interação, oportunidade, satisfação e pendências. |
| CRM-ACC-007 | **B** | Implementar plano de conta versionado com objetivos, riscos, estratégia, ações e responsáveis. |
| CRM-ACC-008 | **N** | Exibir cobertura de produtos: comprados, não comprados, abandonados, potenciais e oportunidades de cross-sell. |
| CRM-ACC-009 | **N** | Exibir mapa de stakeholders e comitê de compra. |
| CRM-ACC-010 | **E** | Manter pedidos, faturamento, notas fiscais, oportunidades, contatos e atividades como abas contextualizadas. |
| CRM-ACC-011 | **N** | Acrescentar abas de campanhas, mensagens, reuniões, documentos, amostras, ocorrências e plano de conta. |
| CRM-ACC-012 | **N** | Permitir favoritos, pin de informações importantes e resumo executivo da conta. |
| CRM-ACC-013 | **N** | Registrar transferência de responsável, motivo, data e passagem de bastão. |
| CRM-ACC-014 | **N** | Preservar histórico de responsáveis sem reescrever autoria de interações passadas. |
| CRM-ACC-015 | **N** | Exibir contas relacionadas e potenciais conflitos de cadastro ou duplicidade. |

### 10.3 Contatos e comitê de compra

**Objetivo:** administrar pessoas de contato, seus papéis e sua influência no processo de compra.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-CON-001 | **E** | Manter o CRUD de contatos locais associado a código e loja do cliente. |
| CRM-CON-002 | **E** | Exibir separadamente o contato canônico do ERP, sem sobrescrevê-lo. |
| CRM-CON-003 | **N** | Registrar cargo, departamento, papel no processo, nível de influência e poder de decisão. |
| CRM-CON-004 | **N** | Identificar decisor, influenciador, usuário, comprador, financeiro, técnico, patrocinador e bloqueador. |
| CRM-CON-005 | **N** | Permitir múltiplos e-mails, telefones, canais preferidos, idioma e horário de contato. |
| CRM-CON-006 | **N** | Registrar consentimentos, bases legais, opt-ins, opt-outs e restrições por canal. |
| CRM-CON-007 | **N** | Controlar contato principal por finalidade, não apenas um principal global. |
| CRM-CON-008 | **N** | Detectar contatos duplicados por e-mail, telefone e identidade externa. |
| CRM-CON-009 | **N** | Registrar mudança de empresa, cargo ou desligamento sem apagar o histórico anterior. |
| CRM-CON-010 | **N** | Relacionar contatos a leads, oportunidades, reuniões, campanhas e conversas. |
| CRM-CON-011 | **N** | Exibir nível de engajamento e última interação por contato. |
| CRM-CON-012 | **N** | Permitir importação e atualização em massa com validação prévia. |

### 10.4 Importação, qualidade, deduplicação e identidade

**Objetivo:** impedir que o CRM se torne uma nova base desatualizada ou duplicada.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-DQ-001 | **N** | Importar empresas, contatos e leads por planilha com mapeamento de colunas. |
| CRM-DQ-002 | **N** | Executar prévia, validação e simulação antes de confirmar a importação. |
| CRM-DQ-003 | **N** | Identificar duplicidades por CNPJ/CPF, código ERP, domínio, e-mail, telefone e similaridade de nome. |
| CRM-DQ-004 | **N** | Permitir mesclagem controlada com registro de origem e valores escolhidos. |
| CRM-DQ-005 | **N** | Manter `external_id`, origem, data de sincronização e chave canônica por fonte. |
| CRM-DQ-006 | **B** | Registrar issues de qualidade com severidade, entidade, mensagem e responsável pela resolução. |
| CRM-DQ-007 | **N** | Detectar e-mails inválidos, bounces, domínios inexistentes, telefones incompletos e empresas encerradas. |
| CRM-DQ-008 | **N** | Criar fila de revisão humana para combinações incertas. |
| CRM-DQ-009 | **N** | Aplicar regras de normalização de nomes, documentos, telefones e endereços. |
| CRM-DQ-010 | **N** | Permitir enriquecimento por fontes aprovadas sem substituir silenciosamente dados mestres. |
| CRM-DQ-011 | **N** | Exibir indicador de completude e confiança do cadastro. |
| CRM-DQ-012 | **N** | Auditar importações, merges, exclusões lógicas e alterações em massa. |

### 10.5 Prospects e leads

**Objetivo:** gerir empresas e pessoas antes de se tornarem clientes do ERP.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-LEAD-001 | **B** | Implementar cadastro nativo de prospect com identidade estável anterior ao cliente ERP. |
| CRM-LEAD-002 | **B** | Suportar status: novo, em contato, qualificado, nutrição, convertido, desqualificado e perdido. |
| CRM-LEAD-003 | **N** | Diferenciar lead individual, empresa prospect e conta-alvo. |
| CRM-LEAD-004 | **N** | Registrar origem, campanha, canal, formulário, indicação, evento ou importação. |
| CRM-LEAD-005 | **N** | Registrar segmento, território, potencial, produtos de interesse e aderência ao perfil ideal. |
| CRM-LEAD-006 | **N** | Exigir próximo passo e data para leads em atendimento. |
| CRM-LEAD-007 | **N** | Permitir qualificação por critérios configuráveis de perfil, necessidade, prazo, autoridade e potencial. |
| CRM-LEAD-008 | **N** | Registrar motivo de desqualificação ou perda por catálogo. |
| CRM-LEAD-009 | **B** | Converter prospect em cliente ou vinculá-lo a cliente existente sem perder histórico. |
| CRM-LEAD-010 | **N** | Converter lead qualificado em oportunidade com cópia controlada de contexto, contatos e origem. |
| CRM-LEAD-011 | **N** | Permitir fila de leads sem responsável e regras de distribuição. |
| CRM-LEAD-012 | **N** | Manter histórico de owner, atribuição, aceite, devolução e reatribuição. |
| CRM-LEAD-013 | **N** | Exibir aging desde entrada, última atividade e tempo até primeiro contato. |
| CRM-LEAD-014 | **N** | Impedir conversões duplicadas para o mesmo documento ou conta canônica. |

### 10.6 Segmentação e públicos

**Objetivo:** criar públicos dinâmicos para marketing, prospecção, reativação e gestão de carteira.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SEG-001 | **N** | Criar segmentos por atributos de empresa, contato, lead, produto, venda, campanha e comportamento. |
| CRM-SEG-002 | **N** | Suportar operadores E/OU, grupos aninhados e condições de inclusão/exclusão. |
| CRM-SEG-003 | **N** | Criar segmentos estáticos e dinâmicos com atualização agendada. |
| CRM-SEG-004 | **N** | Permitir segmentos por ausência de compra em 30, 60, 90 dias ou período configurável. |
| CRM-SEG-005 | **N** | Permitir segmentos de cross-sell: compra família A e não compra família B. |
| CRM-SEG-006 | **N** | Permitir segmentos por unidade, vendedor, carteira, território, grupo econômico e subgrupo. |
| CRM-SEG-007 | **N** | Permitir segmentos por visita ao site, abertura, clique, formulário e pontuação. |
| CRM-SEG-008 | **N** | Exibir tamanho estimado, critérios e amostra antes de usar o público. |
| CRM-SEG-009 | **N** | Aplicar consentimento, suppression list e frequência máxima antes de ativar uma campanha. |
| CRM-SEG-010 | **N** | Versionar critérios e registrar qual versão foi usada em cada campanha. |

### 10.7 Captura, formulários e páginas de conversão

**Objetivo:** transformar interações digitais em leads identificados e rastreáveis.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-CAP-001 | **N** | Criar formulários configuráveis com campos padrão e personalizados. |
| CRM-CAP-002 | **N** | Criar páginas de conversão responsivas com identidade visual DELPI. |
| CRM-CAP-003 | **N** | Suportar formulários incorporáveis no site e em páginas externas aprovadas. |
| CRM-CAP-004 | **N** | Capturar UTM, página, referenciador, campanha e consentimento. |
| CRM-CAP-005 | **N** | Permitir ações pós-conversão: mensagem, redirecionamento, arquivo ou aviso à equipe. |
| CRM-CAP-006 | **N** | Criar ou atualizar lead e contato de forma idempotente. |
| CRM-CAP-007 | **N** | Disparar automação, scoring, atribuição e tarefa após conversão. |
| CRM-CAP-008 | **N** | Implementar proteção antispam, rate limit, validação e captcha quando necessário. |
| CRM-CAP-009 | **N** | Versionar formulários e preservar a versão usada em cada submissão. |
| CRM-CAP-010 | **N** | Permitir formulários de orçamento, atualização cadastral, download, evento, amostra e contato técnico. |

### 10.8 Campanhas e e-mail marketing

**Objetivo:** planejar, executar e medir comunicações comerciais e de relacionamento.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-CAM-001 | **N** | Criar campanhas com objetivo, público, responsável, orçamento, período e tags. |
| CRM-CAM-002 | **N** | Criar e versionar templates de e-mail responsivos. |
| CRM-CAM-003 | **N** | Oferecer editor visual e modo HTML controlado. |
| CRM-CAM-004 | **N** | Personalizar assunto e conteúdo com campos de empresa, contato, vendedor e produtos. |
| CRM-CAM-005 | **N** | Programar envio, fuso horário, janela comercial e limitação de frequência. |
| CRM-CAM-006 | **N** | Executar envio de teste e aprovação antes do disparo. |
| CRM-CAM-007 | **N** | Controlar entrega, bounce, abertura, clique, resposta, descadastro e denúncia. |
| CRM-CAM-008 | **N** | Manter suppression lists globais e por finalidade. |
| CRM-CAM-009 | **N** | Suportar testes A/B de assunto, remetente, conteúdo e horário. |
| CRM-CAM-010 | **N** | Relacionar campanha, contato, oportunidade, pedido e receita atribuída. |
| CRM-CAM-011 | **N** | Criar campanhas de lançamento, reativação, cross-sell, eventos, conteúdo técnico e atualização cadastral. |
| CRM-CAM-012 | **N** | Exibir métricas por campanha, segmento, carteira, vendedor e produto. |
| CRM-CAM-013 | **D** | Configurar domínio, reputação, autenticação de envio e provedor conforme política de TI. |
| CRM-CAM-014 | **N** | Permitir pausar, cancelar e bloquear campanha quando houver anomalia. |

### 10.9 Automação de marketing e nutrição

**Objetivo:** reagir a eventos da jornada e manter relacionamento sem depender de ações manuais repetitivas.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-AUT-001 | **N** | Criar fluxos visuais com gatilhos, condições, esperas e ações. |
| CRM-AUT-002 | **N** | Usar como gatilho: formulário, campanha, visita, score, mudança de lead, compra, inatividade ou evento externo. |
| CRM-AUT-003 | **N** | Enviar e-mail, criar tarefa, alterar tag, mudar estágio, atribuir owner ou notificar equipe. |
| CRM-AUT-004 | **N** | Permitir ramificações por perfil, comportamento, consentimento e carteira. |
| CRM-AUT-005 | **N** | Evitar loops, reentrada indevida e duplicidade de ações. |
| CRM-AUT-006 | **N** | Registrar execução passo a passo e motivo de cada decisão. |
| CRM-AUT-007 | **N** | Permitir pausa, versão, publicação e rollback de fluxo. |
| CRM-AUT-008 | **N** | Respeitar horários, feriados, SLAs e frequência por canal. |
| CRM-AUT-009 | **N** | Permitir saída automática quando houver venda, opt-out, desqualificação ou conflito. |
| CRM-AUT-010 | **N** | Exibir taxa de entrada, progressão, conversão, abandono e impacto em receita. |

### 10.10 Tracking, scoring e atribuição

**Objetivo:** identificar intenção, priorizar atendimento e ligar esforço comercial ao resultado.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SCO-001 | **N** | Registrar eventos de página, conteúdo, formulário, campanha, e-mail e canal autorizado. |
| CRM-SCO-002 | **N** | Associar eventos anônimos a um contato após identificação, conforme consentimento. |
| CRM-SCO-003 | **N** | Criar score de perfil e score de comportamento separadamente. |
| CRM-SCO-004 | **N** | Permitir regras positivas, negativas, decaimento temporal e limites. |
| CRM-SCO-005 | **N** | Exibir fatores que compõem o score e data da última atualização. |
| CRM-SCO-006 | **N** | Gerar qualificação, tarefa ou atribuição ao atingir limiar configurado. |
| CRM-SCO-007 | **N** | Medir primeiro toque, último toque e atribuição multitoque. |
| CRM-SCO-008 | **N** | Relacionar campanha a oportunidade, pedido, faturamento e receita. |
| CRM-SCO-009 | **N** | Diferenciar aquisição, influência, reativação, expansão e retenção. |
| CRM-SCO-010 | **N** | Permitir reprocessar modelos sem alterar silenciosamente resultados históricos. |
| CRM-SCO-011 | **N** | Registrar origem declarada pelo vendedor e origem calculada pelo sistema. |
| CRM-SCO-012 | **N** | Disponibilizar trilha auditável para métricas de conversão e CAC. |


### 10.11 Múltiplos funis e etapas

**Objetivo:** suportar processos comerciais diferentes sem forçar todos os vendedores a uma única sequência.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-PIP-001 | **B** | Implementar definições de pipeline e etapas configuráveis. |
| CRM-PIP-002 | **N** | Suportar funis distintos para aquisição, gestão de conta, reativação, projeto técnico, amostra e renovação. |
| CRM-PIP-003 | **N** | Permitir pipeline por unidade, segmento, linha de produto, carteira ou processo. |
| CRM-PIP-004 | **N** | Definir ordem, probabilidade, SLA, campos obrigatórios e critérios de saída por etapa. |
| CRM-PIP-005 | **N** | Definir transições permitidas, inclusive retorno controlado à etapa anterior. |
| CRM-PIP-006 | **N** | Exigir motivo e comentário em saltos, retrocessos, pausa e cancelamento. |
| CRM-PIP-007 | **N** | Calcular tempo total e tempo em cada etapa. |
| CRM-PIP-008 | **N** | Alertar aging, ausência de atividade, SLA vencido e etapa incompatível. |
| CRM-PIP-009 | **N** | Versionar o pipeline sem alterar o histórico de oportunidades antigas. |
| CRM-PIP-010 | **N** | Permitir templates de pipeline e clonagem administrada. |
| CRM-PIP-011 | **N** | Impedir exclusão física de etapa usada; usar inativação e migração assistida. |
| CRM-PIP-012 | **N** | Exibir funil por quantidade, valor, margem, probabilidade, produto e responsável. |
| CRM-PIP-013 | **N** | Oferecer visão **mapa de vendas** (saúde do funil): negócios destacados por aging, valor e risco, além de kanban e lista. |
| CRM-PIP-014 | **N** | Permitir handoff controlado entre funis (pré-venda → venda → pós-venda / reativação), com cópia ou vínculo e histórico preservado. |
| CRM-PIP-015 | **N** | Exibir coluna ou fila lateral de negócios elegíveis a entrar no funil atual (ex.: ganhos do funil anterior pendentes de pós-venda). |
| CRM-PIP-016 | **N** | Distinguir **funil de oportunidade** (receita) de **funil de conversa/atendimento** (cartão = thread omnicanal), permitindo handoff entre os dois sem duplicar histórico. |
| CRM-PIP-017 | **N** | Permitir templates de etapas de atendimento no estilo Kanban (ex.: novos chats, em atendimento, proposta enviada, follow-up, ganho, perdido/postergado), configuráveis por processo. |

### 10.12 Oportunidades e negociações

**Objetivo:** controlar cada possibilidade de receita desde sua abertura até ganho, perda ou cancelamento.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-OPP-001 | **P** | Manter leitura das oportunidades oriundas do ERP e criar oportunidades nativas no CRM. |
| CRM-OPP-002 | **B** | Implementar CRUD, detalhe, histórico e transição de etapa. |
| CRM-OPP-003 | **N** | Registrar conta/prospect, contatos, owner, equipe, origem, campanha e pipeline. |
| CRM-OPP-004 | **N** | Registrar título, necessidade, escopo, valor, quantidade, moeda, probabilidade e fechamento previsto. |
| CRM-OPP-005 | **N** | Associar produtos, famílias, aplicações, concorrentes e solução proposta. |
| CRM-OPP-006 | **N** | Registrar próximo passo obrigatório, data e responsável. |
| CRM-OPP-007 | **N** | Permitir colaboradores internos com papéis e visibilidades diferentes. |
| CRM-OPP-008 | **N** | Exibir timeline própria com mensagens, reuniões, tarefas, arquivos, decisões e mudanças. |
| CRM-OPP-009 | **N** | Registrar riscos, objeções, dependências, critérios de decisão e concorrência. |
| CRM-OPP-010 | **N** | Permitir pausar com motivo, data de revisão e automação de retomada. |
| CRM-OPP-019 | **N** | Permitir **congelar** negócio (fora do funil ativo, sem contar no forecast operacional) com motivo, data de descongelamento e filtro para ocultar/exibir congelados. |
| CRM-OPP-011 | **N** | Fechar como ganha somente com dados mínimos e vínculo ao pedido ou justificativa de exceção. |
| CRM-OPP-012 | **N** | Fechar como perdida com catálogo de motivo, concorrente, valor e observação. |
| CRM-OPP-013 | **N** | Permitir reabrir somente com permissão e auditoria. |
| CRM-OPP-014 | **N** | Detectar oportunidades duplicadas ou sobrepostas na mesma conta. |
| CRM-OPP-015 | **N** | Calcular saúde da oportunidade com fatores explicáveis. |
| CRM-OPP-016 | **N** | Suportar oportunidade compartilhada entre carteiras quando houver regra formal. |
| CRM-OPP-017 | **N** | Exibir board, lista, calendário, timeline e visão por produto. |
| CRM-OPP-018 | **N** | Oferecer histórico de alterações de valor, prazo, probabilidade e owner. |

### 10.13 Produtos, propostas, preço e aprovações

**Objetivo:** ligar a necessidade comercial ao produto, documento, preço e decisão correspondente.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-PRO-001 | **E** | Manter consulta de propostas/documentos e geração de PDF. |
| CRM-PRO-002 | **N** | Criar solicitação de orçamento vinculada à oportunidade, conta e contatos. |
| CRM-PRO-003 | **N** | Registrar requisitos técnicos, quantidades, aplicação, prazo e anexos. |
| CRM-PRO-004 | **N** | Controlar versão de proposta, vigência, responsável, status e motivo de revisão. |
| CRM-PRO-005 | **N** | Relacionar itens da oportunidade aos produtos e tabelas do ERP. |
| CRM-PRO-006 | **D** | Consultar preços, frete, impostos, prazo, estoque e condições no ERP pela API apropriada. |
| CRM-PRO-007 | **N** | Registrar desconto solicitado, margem estimada e justificativa. |
| CRM-PRO-008 | **B** | Criar aprovação genérica para desconto, margem, exceção e condição comercial. |
| CRM-PRO-009 | **N** | Configurar alçada por valor, margem, unidade, produto e tipo de condição. |
| CRM-PRO-010 | **N** | Notificar aprovadores e medir tempo de decisão. |
| CRM-PRO-011 | **N** | Impedir envio de versão não aprovada quando a política exigir aprovação. |
| CRM-PRO-012 | **N** | Registrar envio, visualização, aceite, recusa, expiração e retorno do cliente. |
| CRM-PRO-013 | **N** | Suportar assinatura eletrônica por integração aprovada. |
| CRM-PRO-014 | **N** | Comparar versões e destacar mudanças de preço, prazo, item e condição. |
| CRM-PRO-015 | **N** | Transformar proposta aceita em pré-pedido ou solicitação de pedido ao ERP. |
| CRM-PRO-016 | **N** | Medir tempo de orçamento, propostas por colaborador, aging e hit rate. |

### 10.14 Tarefas, Meu Dia e produtividade

**Objetivo:** garantir que cada compromisso comercial tenha owner, prazo e conclusão rastreável.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-TSK-001 | **E** | Manter criação, edição, conclusão, exclusão lógica, adiamento e reatribuição. |
| CRM-TSK-002 | **E** | Manter tipos follow-up, ligação, e-mail, visita e to-do. |
| CRM-TSK-003 | **E** | Manter responsáveis individuais ou grupos, clientes associados e anexos. |
| CRM-TSK-004 | **E** | Manter filas atrasadas, hoje, futuras e concluídas. |
| CRM-TSK-005 | **N** | Associar tarefa a lead, contato, oportunidade, proposta, pedido, amostra, ocorrência ou mensagem. |
| CRM-TSK-006 | **B** | Implementar checklist e subtarefas com dependências. |
| CRM-TSK-007 | **B** | Implementar recorrência diária, semanal, mensal e regra personalizada. |
| CRM-TSK-008 | **N** | Permitir lembretes múltiplos por canal e antecedência. |
| CRM-TSK-009 | **N** | Permitir prioridade, esforço estimado, categoria, localização e janela de execução. |
| CRM-TSK-010 | **N** | Exibir capacidade e sobrecarga por responsável sem expor conteúdo indevido. |
| CRM-TSK-011 | **N** | Criar tarefas automaticamente por automações, SLA, mensagem, reunião, risco ou evento do ERP. |
| CRM-TSK-012 | **N** | Registrar resultado da tarefa, observação final e motivo de não conclusão. |
| CRM-TSK-013 | **N** | Impedir conclusão silenciosa quando a tarefa exige resultado ou evidência. |
| CRM-TSK-014 | **N** | Exibir produtividade por tipo, prazo, origem, conta e resultado, sem estimular apenas volume. |
| CRM-TSK-015 | **N** | Permitir visualização lista, calendário e agenda semanal. |
| CRM-TSK-016 | **N** | Criar resumo diário com atrasos, compromissos e prioridades. |
| CRM-TSK-017 | **N** | Oferecer ritual **fim de expediente**: revisar compromissos do dia seguinte, gaps sem próximo passo e itens atrasados em até 10 minutos. |
| CRM-TSK-018 | **N** | Oferecer lista diária com check visual de conclusão e progresso do dia (foco e satisfação de fechamento). |
| CRM-TSK-019 | **N** | Após concluir atividade, sugerir **fluxo inteligente** de próximo passo (ligação, e-mail, reunião, proposta) conforme etapa, tipo e playbook, com confirmação humana. |
| CRM-TSK-020 | **N** | Exigir resultado/outcome da abordagem antes de liberar a conclusão quando a política do processo exigir atualização do CRM. |
| CRM-TSK-021 | **N** | Disponibilizar **script/roteiro de vendas** contextual (qualificação, objeções, perguntas) ao lado da tarefa/ligação, sem bloquear o diálogo. |
| CRM-TSK-022 | **N** | Permitir nota rápida por áudio em tarefa/visita (mobile), com transcrição opcional e vínculo ao registro. |

### 10.15 Sequências e cadências comerciais

**Objetivo:** padronizar abordagens repetitivas de prospecção, nutrição e reativação.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SEQ-001 | **B** | Implementar cadastro, edição e ativação de sequências. |
| CRM-SEQ-002 | **N** | Definir passos de e-mail, tarefa, ligação, mensagem, espera e decisão. |
| CRM-SEQ-003 | **N** | Inscrever leads, contatos, oportunidades ou segmentos. |
| CRM-SEQ-004 | **N** | Personalizar conteúdo por empresa, contato, owner e interesse. |
| CRM-SEQ-005 | **N** | Pausar automaticamente ao receber resposta, reunião, conversão ou opt-out. |
| CRM-SEQ-006 | **N** | Respeitar horário comercial, feriado, fuso e limite de frequência. |
| CRM-SEQ-007 | **N** | Permitir cadências diferentes para hunter, farmer, reativação e pós-proposta. |
| CRM-SEQ-008 | **N** | Exibir progresso, respostas, reuniões, conversões e abandono por etapa. |
| CRM-SEQ-009 | **N** | Registrar versão da sequência usada em cada inscrição. |
| CRM-SEQ-010 | **N** | Impedir inscrição duplicada ou conflitante por regra configurável. |
| CRM-SEQ-011 | **N** | Oferecer fila de execução humana para passos não automatizados. |
| CRM-SEQ-012 | **N** | Permitir aprovação de templates e bloqueio de conteúdo não autorizado. |

### 10.16 Agenda, reuniões, visitas e deslocamento

**Objetivo:** integrar compromisso comercial, calendário, reunião e visita ao histórico da conta.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-CAL-001 | **B** | Implementar entidade nativa de visita vinculada a conta, lead ou oportunidade. |
| CRM-CAL-002 | **B** | Integrar calendário corporativo por conector Microsoft 365. |
| CRM-CAL-003 | **N** | Consultar disponibilidade livre/ocupado dos participantes autorizados. |
| CRM-CAL-004 | **N** | Criar evento com assunto, descrição, local, participantes, fuso e lembretes. |
| CRM-CAL-005 | **N** | Criar reunião online e guardar o vínculo no registro comercial. |
| CRM-CAL-006 | **N** | Sincronizar atualização, aceite, recusa, cancelamento e nova proposta de horário. |
| CRM-CAL-007 | **N** | Permitir agenda individual, da equipe e por conta, conforme permissão. |
| CRM-CAL-008 | **N** | Registrar objetivo, pauta, preparação, ata, decisões, participantes e próximos passos. |
| CRM-CAL-009 | **N** | Converter próximos passos da reunião em tarefas com confirmação. |
| CRM-CAL-010 | **B** | Integrar solicitação de veículo para visita quando o módulo corporativo estiver disponível. |
| CRM-CAL-011 | **N** | Registrar endereço, rota, check-in opcional e duração real da visita. |
| CRM-CAL-015 | **N** | Oferecer **mapa de clientes/visitas** com otimização assistida de rota do dia (sem tracking contínuo). |
| CRM-CAL-012 | **N** | Evitar captura de localização contínua; usar somente finalidade e consentimento aprovados. |
| CRM-CAL-016 | **N** | Antes de cada contato/reunião, oferecer **briefing pré-contato** (histórico, última interação, pendências, produtos e riscos) em um clique. |
| CRM-CAL-013 | **N** | Exibir reuniões sem registro comercial e sugerir associação, sem vincular automaticamente em caso incerto. |
| CRM-CAL-014 | **N** | Preservar privacidade de eventos particulares e sensíveis. |

### 10.17 Carteiras, territórios e distribuição

**Objetivo:** organizar cobertura comercial, ownership e carga de trabalho.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-PRT-001 | **E** | Manter carteiras multiusuário, owner, membros, clientes e auditoria de transferência. |
| CRM-PRT-002 | **E** | Manter escopo próprio, equipe e consolidado resolvido no backend. |
| CRM-PRT-003 | **B** | Criar mapa de territórios com clientes, prospects e regiões. |
| CRM-PRT-004 | **N** | Definir território por região, segmento, potencial, produto, unidade ou regra combinada. |
| CRM-PRT-005 | **B** | Implementar rotação de leads por round-robin e capacidade. |
| CRM-PRT-006 | **N** | Permitir filas, prioridade, SLA de aceite e redistribuição automática. |
| CRM-PRT-007 | **B** | Sugerir redistribuição assistida com base em carga, região, potencial e risco. |
| CRM-PRT-008 | **N** | Exigir aprovação humana para alteração em massa de ownership. |
| CRM-PRT-009 | **N** | Detectar contas sem cobertura, duplicadas em carteiras ou sem responsável ativo. |
| CRM-PRT-010 | **N** | Criar regras de substituição temporária para férias e afastamentos. |
| CRM-PRT-011 | **N** | Entregar ao substituto somente o escopo e período necessários. |
| CRM-PRT-012 | **N** | Gerar relatório de cobertura, carga, atenção, valor aberto e potencial. |

### 10.18 Timeline omnicanal

**Objetivo:** formar o histórico corporativo único da relação com o cliente.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-TML-001 | **P** | Evoluir atividades e histórico atuais para timeline unificada. |
| CRM-TML-002 | **N** | Normalizar e-mails, mensagens, reuniões, ligações, tarefas, campanhas e eventos do ERP. |
| CRM-TML-003 | **N** | Exibir autor, canal, data, direção, participantes, assunto, resumo e vínculos. |
| CRM-TML-004 | **N** | Permitir filtrar por tipo, período, pessoa, oportunidade, produto e origem. |
| CRM-TML-005 | **N** | Permitir busca textual conforme política e autorização. |
| CRM-TML-006 | **N** | Exibir edições, exclusões, sincronizações e origem sem apagar a trilha. |
| CRM-TML-007 | **N** | Evitar duplicidade de eventos importados por diferentes participantes. |
| CRM-TML-008 | **N** | Permitir associação manual e sugestão automática a conta, contato e oportunidade. |
| CRM-TML-009 | **N** | Identificar eventos privados ou restritos e ocultar conteúdo quando necessário. |
| CRM-TML-010 | **N** | Permitir fixar eventos relevantes no resumo da conta. |
| CRM-TML-011 | **N** | Criar resumo por período sem substituir o conteúdo original. |
| CRM-TML-012 | **N** | Registrar fonte, `external_id`, hash, checkpoint e status de sincronização. |

### 10.19 Colaboração interna e sala de interação

**Objetivo:** manter discussão operacional vinculada ao registro, substituindo mensagens soltas sem contexto.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-COL-001 | **E** | Manter salas por entidade, processo, grupo e mural global. |
| CRM-COL-002 | **E** | Manter inbox, mensagens, threads, menções, reações, pins e anexos. |
| CRM-COL-003 | **E** | Manter criação de tarefa a partir de mensagem e referência de origem. |
| CRM-COL-004 | **E** | Manter eventos em tempo real e cursor de leitura. |
| CRM-COL-005 | **N** | Permitir associar sala a lead, oportunidade, proposta, pedido, amostra e exceção. |
| CRM-COL-006 | **N** | Criar templates de passagem de bastão e decisão. |
| CRM-COL-007 | **N** | Permitir marcar decisão, pendência, risco, compromisso e informação do cliente. |
| CRM-COL-008 | **N** | Criar reunião ou tarefa a partir de mensagem com prévia e confirmação. |
| CRM-COL-009 | **N** | Gerar resumo da thread com fontes e links para mensagens. |
| CRM-COL-010 | **N** | Aplicar visibilidade específica quando a sala envolver dados sensíveis. |
| CRM-COL-011 | **N** | Permitir watchers, mute, preferências e digest sem transformar membership em ACL implícita. |
| CRM-COL-012 | **N** | Manter retenção e moderação conforme tipo de sala. |

### 10.20 Integração com Microsoft Teams

**Objetivo:** incorporar ao histórico comercial somente as conversas corporativas autorizadas e relacionadas ao processo comercial.

> A integração não deve significar leitura irrestrita e silenciosa de todas as conversas. O acesso deve ser aprovado pela administração, seguir menor privilégio e restringir a ingestão à finalidade comercial definida.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-TMS-001 | **B** | Implementar conector Microsoft Graph como integração própria da `commercial-api`. |
| CRM-TMS-002 | **N** | Suportar modo delegado por usuário e modo de aplicação somente quando aprovado pela administração. |
| CRM-TMS-003 | **N** | Permitir allowlist de equipes, canais, chats, usuários ou reuniões elegíveis para sincronização. |
| CRM-TMS-004 | **N** | Ler mensagens de canal, respostas, chats individuais, chats de grupo e chats de reunião conforme escopo concedido. |
| CRM-TMS-005 | **N** | Capturar autor, participantes, data, conteúdo, menções, reações, links e referências de anexos. |
| CRM-TMS-006 | **N** | Receber notificações de criação, alteração e exclusão para sincronização de baixa latência. |
| CRM-TMS-007 | **N** | Executar carga inicial e recuperação incremental com checkpoint, idempotência e deduplicação. |
| CRM-TMS-008 | **N** | Propagar edição e exclusão da origem para o espelho do CRM, preservando trilha de auditoria. |
| CRM-TMS-009 | **N** | Mapear identidades do tenant ao `sub` do Keycloak e aos contatos externos quando possível. |
| CRM-TMS-010 | **N** | Permitir associação manual de conversa ou mensagem a conta, contato, oportunidade, pedido, tarefa ou amostra. |
| CRM-TMS-011 | **N** | Sugerir associação por participantes, domínio, número de pedido, código de cliente e contexto, exigindo confirmação em baixa confiança. |
| CRM-TMS-012 | **N** | Importar metadados de reunião e chat relacionado. |
| CRM-TMS-013 | **D** | Importar transcrição de reunião apenas quando a transcrição existir e o acesso estiver habilitado por política. |
| CRM-TMS-014 | **N** | Guardar transcrição em formato pesquisável, com timestamp e atribuição de fala quando autorizada. |
| CRM-TMS-015 | **N** | Gerar resumo, decisões e ações da reunião com revisão humana. |
| CRM-TMS-016 | **N** | Não armazenar gravação por padrão; manter link protegido ou política específica quando necessário. |
| CRM-TMS-017 | **N** | Excluir chats particulares, pessoais, jurídicos, médicos, sindicais ou não comerciais por política e classificação. |
| CRM-TMS-018 | **N** | Respeitar retenção, legal hold, exclusão, acesso do usuário e política do tenant. |
| CRM-TMS-019 | **N** | Registrar consentimento administrativo, permissões concedidas, data, finalidade e responsável. |
| CRM-TMS-020 | **N** | Auditar toda consulta, importação, associação, exportação e visualização sensível. |
| CRM-TMS-021 | **N** | Implementar renovação de subscriptions, lifecycle notifications, retry e dead-letter. |
| CRM-TMS-022 | **N** | Monitorar limites, throttling, mensagens perdidas, duplicidades e atraso de sincronização. |
| CRM-TMS-023 | **N** | Permitir “enviar para o CRM” a partir de uma experiência aprovada, reduzindo necessidade de captura ampla. |
| CRM-TMS-024 | **N** | Exibir origem e link de retorno para a conversa quando o usuário ainda possuir acesso na fonte. |


#### 10.20.1 Modos de acesso a validar

| Modo | Uso aceitável | Regra de governança |
|---|---|---|
| Delegado | Conteúdo ao qual o usuário autenticado já possui acesso | Consentimento do usuário, menor privilégio e associação comercial explícita |
| Consentimento específico do recurso | App autorizado somente em equipe, chat ou reunião definida | Preferível quando o caso permitir restringir a superfície |
| Aplicação em nível de tenant | Jobs sem usuário, exportação ou subscriptions amplas | Somente com aprovação administrativa, política formal, allowlist e auditoria reforçada |
| Transcrição de reunião | Reuniões cuja transcrição foi gerada e liberada | Exige configuração do tenant, permissão correspondente e política de retenção |

Permissões técnicas candidatas devem ser validadas na implementação conforme o modo escolhido. Entre os escopos que podem ser necessários estão `Chat.Read`, `Chat.Read.All`, `ChannelMessage.Read.All`, `User.Read.All` e `OnlineMeetingTranscript.Read.All`. O CRM deve solicitar somente o conjunto mínimo compatível com o cenário aprovado.

As APIs de exportação e transcrição acessam dados corporativos sensíveis. Portanto:

- o conector deve ser tratado como integração protegida;
- a administração deve aprovar permissões de aplicação;
- a política deve definir usuários, equipes, canais e reuniões elegíveis;
- subscriptions e exportações amplas não devem ser usadas para criar uma cópia paralela do tenant;
- quando possível, deve-se preferir captura por recurso ou ação explícita “enviar para o CRM”.

### 10.21 Outlook, e-mail e caixa compartilhada

**Objetivo:** transformar e-mails comerciais em histórico corporativo, mantendo privacidade e controle.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-EML-001 | **B** | Implementar conector de e-mail e calendário Microsoft 365. |
| CRM-EML-002 | **N** | Suportar sincronização delegada da caixa do usuário e caixas compartilhadas autorizadas. |
| CRM-EML-003 | **N** | Importar mensagens enviadas e recebidas, assunto, remetentes, destinatários, datas, thread e anexos permitidos. |
| CRM-EML-004 | **N** | Deduplicar por `internetMessageId`, `conversationId` e demais chaves estáveis. |
| CRM-EML-005 | **N** | Associar e-mail automaticamente por domínio, endereço, contatos, assunto e identificadores comerciais. |
| CRM-EML-006 | **N** | Permitir corrigir associação e bloquear sugestão incorreta. |
| CRM-EML-007 | **N** | Registrar resposta, tempo de resposta, ausência de retorno e última interação. |
| CRM-EML-008 | **N** | Criar e enviar e-mail individual pelo CRM, usando identidade autorizada do usuário. |
| CRM-EML-009 | **N** | Oferecer templates aprovados, variáveis e assinatura corporativa. |
| CRM-EML-010 | **N** | Permitir agendamento de envio e cancelamento antes do processamento. |
| CRM-EML-011 | **N** | Permitir criar tarefa, oportunidade ou contato a partir de e-mail. |
| CRM-EML-012 | **N** | Criar inbox compartilhada por carteira ou processo com distribuição, SLA e owner. |
| CRM-EML-013 | **N** | Separar e-mail transacional, campanha em massa e conversa individual. |
| CRM-EML-014 | **N** | Respeitar opt-out, lista de bloqueio, finalidade e política de retenção. |
| CRM-EML-015 | **N** | Não sincronizar pastas particulares ou excluídas pela política. |
| CRM-EML-016 | **N** | Usar subscriptions e lifecycle notifications, evitando polling excessivo. |
| CRM-EML-017 | **N** | Criptografar payloads sensíveis e proteger segredos/certificados do conector. |
| CRM-EML-018 | **N** | Manter trilha de quem visualizou, vinculou, exportou ou removeu conteúdo. |

#### 10.21.1 Modos de acesso a validar

- `Mail.Read` ou equivalente mínimo para mensagens autorizadas;
- `Calendars.Read` ou equivalente mínimo para disponibilidade e eventos;
- `Contacts.Read` somente quando a sincronização de contatos pessoais for realmente necessária;
- permissões de escrita apenas para envio, criação ou atualização explicitamente aprovados;
- modo delegado para ações do próprio usuário;
- modo de aplicação para caixas compartilhadas ou processamento sem usuário somente com consentimento administrativo.

A caixa compartilhada deve ter finalidade, owner, política de retenção e escopo próprios. Permissão de acesso ao CRM não concede automaticamente acesso a toda caixa de correio do tenant.

### 10.22 Mensageria externa e atendimento digital

**Objetivo:** centralizar conversas autorizadas com clientes em uma inbox corporativa.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-MSG-001 | **N** | Integrar canal de mensageria por API/conector oficial, sem automação baseada em dispositivo pessoal. |
| CRM-MSG-002 | **N** | Manter inbox compartilhada com filas, owner, transferência e status de atendimento. |
| CRM-MSG-003 | **N** | Vincular conversa a empresa, contato, lead, oportunidade e pedido. |
| CRM-MSG-004 | **N** | Registrar mensagens enviadas, recebidas, entregues, lidas, falhas e timestamps. |
| CRM-MSG-005 | **N** | Suportar texto, imagem, documento, localização, contato e áudio quando permitido pelo canal. |
| CRM-MSG-006 | **N** | Transcrever mensagens de áudio com indicação de confiança e acesso ao original. |
| CRM-MSG-007 | **N** | Não prometer transcrição de chamada do canal; tratar chamadas em módulo de voz separado. |
| CRM-MSG-008 | **N** | Permitir templates aprovados e variáveis controladas. |
| CRM-MSG-009 | **N** | Controlar opt-in, opt-out, janela de atendimento, finalidade e custo por tipo de mensagem. |
| CRM-MSG-010 | **N** | Criar campanhas somente para públicos elegíveis e com frequência controlada. |
| CRM-MSG-011 | **N** | Distribuir atendimentos por carteira, fila, disponibilidade, prioridade ou round-robin. |
| CRM-MSG-012 | **N** | Permitir handoff entre bot, IA e atendente humano com preservação de contexto. |
| CRM-MSG-013 | **N** | Medir primeira resposta, resolução, reabertura, abandono e conversão. |
| CRM-MSG-014 | **N** | Criar tarefa, lead ou oportunidade a partir de conversa. |
| CRM-MSG-015 | **N** | Permitir respostas rápidas e base de conhecimento aprovada. |
| CRM-MSG-016 | **N** | Auditar envio em massa, exportação e visualização de conteúdo sensível. |
| CRM-MSG-017 | **N** | Expor conversas no **quadro Kanban de funil** (ver § 10.40), com badge de canal e abertura do thread a partir do cartão. |
| CRM-MSG-018 | **N** | Permitir mudar etapa do funil de dentro da conversa e arrastar o cartão no quadro, com a mesma validação de backend. |
| CRM-MSG-019 | **N** | Inserir ou mover conversa no funil por gatilho (primeira mensagem, palavra-chave, bot, formulário, tag ou regra de jornada). |
| CRM-MSG-020 | **N** | Adicionar conversas em lote ao funil com filtros (canal, status, owner, tag, período, fila). |
| CRM-MSG-021 | **N** | Aceitar como canal de origem, além de WhatsApp: Teams, Outlook/e-mail, web chat e redes sociais corporativas homologadas (LinkedIn, Instagram, Facebook Messenger e futuras), via conector oficial. |

### 10.23 Ligações, telefonia e voz

**Objetivo:** registrar chamadas comerciais e transformar conversas em ações rastreáveis.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-VOI-001 | **N** | Integrar telefonia corporativa ou provedor aprovado. |
| CRM-VOI-002 | **N** | Registrar origem/destino, participantes, horário, duração, direção e resultado. |
| CRM-VOI-003 | **N** | Permitir click-to-call quando a infraestrutura suportar. |
| CRM-VOI-004 | **N** | Solicitar classificação e resultado após a chamada. |
| CRM-VOI-005 | **D** | Gravar chamada somente quando permitido por contrato, política e legislação. |
| CRM-VOI-006 | **D** | Transcrever chamada somente com consentimento e aviso exigidos. |
| CRM-VOI-007 | **N** | Gerar resumo, objeções, compromissos e tarefas com confirmação humana. |
| CRM-VOI-008 | **N** | Vincular chamada a conta, contato, lead, oportunidade e tarefa. |
| CRM-VOI-009 | **N** | Restringir reprodução e download por permissão sensível. |
| CRM-VOI-010 | **N** | Aplicar retenção distinta a metadados, transcrição e gravação. |
| CRM-VOI-011 | **N** | Medir tentativas, contatos efetivos, duração e resultado sem usar volume como único indicador. |
| CRM-VOI-012 | **N** | Permitir exclusão ou anonimização conforme política e base legal. |

### 10.24 Documentos, anexos e assinatura

**Objetivo:** reunir documentos comerciais com segurança, versão e contexto.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-DOC-001 | **E** | Manter anexos persistentes em tarefas e mensagens. |
| CRM-DOC-002 | **N** | Estender anexos a conta, lead, oportunidade, proposta, visita, amostra e ocorrência. |
| CRM-DOC-003 | **N** | Controlar versão, categoria, descrição, autor, origem e data de validade. |
| CRM-DOC-004 | **N** | Implementar antivírus, validação de MIME, limite, hash e quarentena. |
| CRM-DOC-005 | **N** | Permitir preview de formatos seguros e download autorizado. |
| CRM-DOC-006 | **N** | Aplicar classificação: público interno, comercial, confidencial e sensível. |
| CRM-DOC-007 | **N** | Integrar repositório corporativo quando o documento já possuir fonte oficial. |
| CRM-DOC-008 | **N** | Evitar duplicar arquivos externos; armazenar referência e snapshot somente quando necessário. |
| CRM-DOC-009 | **N** | Permitir geração de documentos a partir de templates aprovados. |
| CRM-DOC-010 | **N** | Integrar assinatura eletrônica e registrar evidência, status e versão assinada. |
| CRM-DOC-011 | **N** | Auditar visualização, download, envio, substituição e exclusão. |
| CRM-DOC-012 | **N** | Aplicar retenção e descarte por categoria documental. |

### 10.25 Integração com ERP e dados operacionais

**Objetivo:** unir pré-venda e relacionamento ao processo transacional sem transformar o CRM em ERP paralelo.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-ERP-001 | **E** | Manter a `api-delpi` como fronteira de SQL e contratos TOTVS. |
| CRM-ERP-002 | **E** | Manter a `commercial-api` como BFF e dona de escopo antes de consultar o ERP. |
| CRM-ERP-003 | **E** | Consultar clientes, pedidos, itens, estoque, OPs, faturamento, NF e oportunidades existentes. |
| CRM-ERP-004 | **N** | Associar oportunidade nativa a proposta, pré-pedido, pedido e nota do ERP. |
| CRM-ERP-005 | **N** | Enviar somente comandos formalmente contratados, idempotentes e auditáveis. |
| CRM-ERP-006 | **N** | Validar cliente, produto, tabela, preço, desconto, condição, prazo e impostos antes de criar pré-pedido. |
| CRM-ERP-007 | **N** | Exibir status e erro de integração com opção segura de reprocessamento. |
| CRM-ERP-008 | **N** | Não persistir cópia integral de tabelas do ERP no schema comercial. |
| CRM-ERP-009 | **N** | Usar snapshots somente em documentos e decisões que exijam evidência histórica. |
| CRM-ERP-010 | **N** | Sincronizar eventos relevantes por polling incremental, webhook ou fila, conforme capacidade da origem. |
| CRM-ERP-011 | **N** | Registrar correlação ponta a ponta entre CRM e ERP. |
| CRM-ERP-012 | **N** | Tratar indisponibilidade do ERP com cache identificado, fallback seguro e bloqueio de comandos críticos. |
| CRM-ERP-013 | **N** | Exibir `freshness` e origem em dados compostos. |
| CRM-ERP-014 | **N** | Não permitir que o usuário altere no CRM um dado cujo mestre é o ERP. |

### 10.26 Confirmação de pedido e passagem para operação

**Objetivo:** rastrear o intervalo entre entrada do pedido, análise das áreas e confirmação ao cliente.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-ORD-001 | **B** | Implementar caso de confirmação de pedido com histórico de etapas. |
| CRM-ORD-002 | **N** | Registrar dois marcos: recebimento do pedido e confirmação da data firme. |
| CRM-ORD-003 | **N** | Definir responsáveis de Vendas e áreas operacionais. |
| CRM-ORD-004 | **N** | Aplicar SLA por etapa, tipo de pedido, unidade e prioridade. |
| CRM-ORD-005 | **N** | Registrar dúvidas, pendências, respostas e documentos por área. |
| CRM-ORD-006 | **N** | Notificar atraso, bloqueio, escalonamento e conclusão. |
| CRM-ORD-007 | **N** | Gerar mensagem sistêmica na sala de interação do pedido. |
| CRM-ORD-008 | **N** | Medir tempo total e tempo por área até confirmação ao cliente. |
| CRM-ORD-009 | **N** | Registrar data prometida, data firme, alteração e justificativa. |
| CRM-ORD-010 | **N** | Manter comunicação ao cliente vinculada ao caso. |
| CRM-ORD-011 | **N** | Exibir divergência entre pedido, promessa, produção, faturamento e entrega. |
| CRM-ORD-012 | **N** | Encerrar somente após confirmação registrada ou exceção formal. |

### 10.27 Produção, faturamento, embarque e entrega

**Objetivo:** dar visibilidade comercial ao andamento pós-venda sem assumir a operação de produção.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-DEL-001 | **E** | Manter detalhe de pedido, linha, OP, estrutura, progresso e apontamentos. |
| CRM-DEL-002 | **E** | Manter indicação de estoque alocado, atraso e pronto para faturar. |
| CRM-DEL-003 | **N** | Criar linha do tempo colocação → confirmação → produção → faturamento → embarque → entrega. |
| CRM-DEL-004 | **N** | Diferenciar claramente data de faturamento, embarque, previsão e entrega ao cliente. |
| CRM-DEL-005 | **B** | Implementar exceção de entrega com tipo, severidade, owner e plano de ação. |
| CRM-DEL-006 | **N** | Registrar ruptura, atraso, divergência, avaria, redespacho, devolução e reclamação. |
| CRM-DEL-007 | **N** | Vincular comunicações, tarefas e decisão à exceção. |
| CRM-DEL-008 | **N** | Escalonar conforme SLA, valor, cliente estratégico e impacto. |
| CRM-DEL-009 | **N** | Registrar previsão revisada, comunicação ao cliente e aceite. |
| CRM-DEL-010 | **N** | Medir reincidência por cliente, produto, unidade, etapa e causa. |
| CRM-DEL-011 | **N** | Exibir faturado e não embarcado quando o contrato de dados existir. |
| CRM-DEL-012 | **D** | Integrar tracking de transporte somente quando houver fonte confiável e contrato definido. |
| CRM-DEL-013 | **N** | Não inferir chegada ao cliente somente pela data de faturamento. |
| CRM-DEL-014 | **N** | Encerrar ocorrência com causa, ação corretiva e evidência. |

### 10.28 Amostras e desenvolvimento técnico

**Objetivo:** controlar amostras e projetos de desenvolvimento ligados ao potencial comercial.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SAM-001 | **B** | Implementar entidade de amostra e histórico de etapas. |
| CRM-SAM-002 | **N** | Vincular amostra a conta, contatos, oportunidade, produto e aplicação. |
| CRM-SAM-003 | **N** | Registrar objetivo, especificação, quantidade, prazo, custo e responsável. |
| CRM-SAM-004 | **N** | Configurar etapas por área e critérios de passagem. |
| CRM-SAM-005 | **N** | Registrar envio, recebimento, teste, retorno e aprovação do cliente. |
| CRM-SAM-006 | **N** | Controlar anexos técnicos, desenhos, laudos, fotos e versões. |
| CRM-SAM-007 | **N** | Aplicar SLA e alertas de atraso. |
| CRM-SAM-008 | **N** | Registrar motivo de reprovação, retrabalho ou cancelamento. |
| CRM-SAM-009 | **N** | Converter aprovação em proposta ou oportunidade atualizada. |
| CRM-SAM-010 | **N** | Medir prazo médio, taxa de aprovação, conversão em venda e valor gerado. |
| CRM-SAM-011 | **N** | Restringir documentos técnicos sensíveis por classificação. |
| CRM-SAM-012 | **N** | Criar sala de interação própria para desenvolvimento complexo. |


### 10.29 Forecast, metas e previsibilidade

**Objetivo:** transformar o pipeline em uma previsão versionada, revisável e mensurável.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-FOR-001 | **B** | Implementar ciclos de forecast com início, fim, corte e status. |
| CRM-FOR-002 | **N** | Criar submissão por vendedor, carteira, unidade, equipe e consolidado. |
| CRM-FOR-003 | **N** | Classificar itens como pipeline, upside, best case, commit e fechado. |
| CRM-FOR-004 | **N** | Gerar baseline a partir das oportunidades elegíveis. |
| CRM-FOR-005 | **N** | Permitir ajuste manual com justificativa e histórico. |
| CRM-FOR-006 | **N** | Separar valor calculado, valor declarado e ajuste do gestor. |
| CRM-FOR-007 | **N** | Implementar submissão, aprovação, rejeição e devolução. |
| CRM-FOR-008 | **N** | Criar snapshots imutáveis por corte. |
| CRM-FOR-009 | **N** | Comparar previsão a pedido, faturamento, meta e resultado realizado. |
| CRM-FOR-010 | **N** | Medir acurácia, viés, erro absoluto e variação por período. |
| CRM-FOR-011 | **N** | Simular cenários pessimista, provável e otimista. |
| CRM-FOR-012 | **N** | Exibir cobertura de pipeline versus meta e gap por carteira. |
| CRM-FOR-013 | **N** | Não criar segunda fonte de meta; consumir a meta corporativa oficial. |
| CRM-FOR-014 | **N** | Registrar premissas, riscos e dependências da previsão. |
| CRM-FOR-015 | **N** | Bloquear alteração retroativa de ciclo encerrado sem fluxo excepcional. |

### 10.30 Indicadores, relatórios e gestão à vista

**Objetivo:** oferecer visão operacional, tática e executiva com definições rastreáveis.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-BI-001 | **E** | Manter ROL, gap versus meta, conversão, OTD, carteira aberta, horizonte e séries. |
| CRM-BI-002 | **E** | Manter filtros por período, unidade, segmento e carteira. |
| CRM-BI-003 | **N** | Adicionar pipeline por etapa, valor ponderado, aging e tempo de ciclo. |
| CRM-BI-004 | **N** | Adicionar leads por origem, qualificação, tempo de primeiro contato e conversão. |
| CRM-BI-005 | **N** | Adicionar oportunidades ganhas/perdidas, motivos, concorrentes e produtos. |
| CRM-BI-006 | **N** | Adicionar produtividade por atividade, sem usar quantidade isolada como avaliação. |
| CRM-BI-007 | **N** | Adicionar campanhas, entregabilidade, engajamento, conversão e receita influenciada. |
| CRM-BI-008 | **N** | Adicionar clientes ativos, novos, recuperados, inativos, em risco e expandidos. |
| CRM-BI-009 | **N** | Adicionar ticket médio, recorrência, frequência, mix e cobertura de produto. |
| CRM-BI-010 | **N** | Adicionar tempo de proposta, etapa, confirmação, amostra e exceção de entrega. |
| CRM-BI-011 | **N** | Adicionar forecast, acurácia e cobertura versus meta. |
| CRM-BI-012 | **N** | Adicionar SLA de resposta por canal, equipe e processo. |
| CRM-BI-013 | **N** | Disponibilizar drill até registros que compõem cada indicador. |
| CRM-BI-014 | **N** | Exibir fórmula, fonte, atualização, timezone, filtros e limitações. |
| CRM-BI-015 | **N** | Permitir salvar visões e compartilhar somente com usuários autorizados. |
| CRM-BI-016 | **N** | Exportar dados permitidos com auditoria e marcação de contexto. |
| CRM-BI-017 | **N** | Comparar MTD, YTD, período anterior e ano anterior onde fizer sentido. |
| CRM-BI-018 | **N** | Impedir soma conceitualmente inválida de métricas sem ficha de indicador aprovada. |
| CRM-BI-019 | **N** | Gerar **sumário semanal e mensal de vendas** (atividades planejadas vs. executadas, pipeline, forecast e próximos passos) para ritual de gestão. |
| CRM-BI-020 | **N** | Medir aderência a rituais e disciplina de CRM (atualização pós-contato, próximo passo preenchido, briefing aberto antes de reunião) sem ranqueamento tóxico. |
| CRM-BI-021 | **N** | Incluir visão **mapa de vendas** nos dashboards de gestão à vista (aging × valor × etapa). |

### 10.31 CAC, atribuição e retorno de marketing

**Objetivo:** medir esforço e investimento da aquisição até a receita.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-CAC-001 | **N** | Registrar custos de campanha, mídia, evento, ferramenta e ação atribuível. |
| CRM-CAC-002 | **N** | Definir período, regra e população do CAC. |
| CRM-CAC-003 | **N** | Calcular CAC por segmento, origem, campanha, produto, unidade e carteira. |
| CRM-CAC-004 | **N** | Diferenciar aquisição de novo cliente, reativação e expansão. |
| CRM-CAC-005 | **N** | Medir custo por lead, qualificado, oportunidade, proposta e cliente ganho. |
| CRM-CAC-006 | **N** | Relacionar receita e margem realizadas, respeitando disponibilidade da fonte financeira. |
| CRM-CAC-007 | **N** | Calcular tempo até primeira venda e payback quando houver dados suficientes. |
| CRM-CAC-008 | **N** | Identificar jornadas sem origem conhecida e qualidade da atribuição. |
| CRM-CAC-009 | **N** | Exibir custo declarado, custo importado e custo estimado separadamente. |
| CRM-CAC-010 | **N** | Não atribuir automaticamente toda receita à última campanha. |
| CRM-CAC-011 | **N** | Permitir modelos de atribuição versionados e comparação entre modelos. |
| CRM-CAC-012 | **N** | Auditar alterações de custo, regra, vínculo e reprocessamento. |

### 10.32 Copiloto de inteligência artificial

**Objetivo:** reduzir trabalho operacional e melhorar decisão, sem retirar responsabilidade humana.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-AI-001 | **N** | Gerar resumo de conta, oportunidade, reunião, conversa e período. |
| CRM-AI-002 | **N** | Exibir fontes e links usados em cada resumo ou recomendação. |
| CRM-AI-003 | **N** | Sugerir próxima melhor ação com fatores explicáveis. |
| CRM-AI-004 | **N** | Preparar briefing antes de reunião com histórico, pedidos, riscos e oportunidades. |
| CRM-AI-005 | **N** | Extrair compromissos, datas, pessoas, objeções e produtos de textos autorizados. |
| CRM-AI-006 | **N** | Sugerir tarefas a partir de e-mail, Teams, mensageria, chamada e reunião. |
| CRM-AI-007 | **N** | Redigir e-mail, mensagem, pauta, ata e follow-up em tom corporativo configurável. |
| CRM-AI-008 | **N** | Exigir revisão antes de qualquer envio externo por padrão. |
| CRM-AI-009 | **N** | Permitir comandos em linguagem natural para consultar e preparar alterações. |
| CRM-AI-010 | **N** | Exigir confirmação estruturada antes de criar, mover, fechar ou excluir registros. |
| CRM-AI-011 | **N** | Sugerir score de lead, saúde da oportunidade e risco de conta, com explicação. |
| CRM-AI-012 | **N** | Detectar ausência de próximo passo, campos incoerentes e oportunidades paradas. |
| CRM-AI-013 | **N** | Sugerir cross-sell, reativação e contas semelhantes com base em dados permitidos. |
| CRM-AI-014 | **N** | Apoiar deduplicação e qualidade de cadastro sem executar merge autônomo. |
| CRM-AI-015 | **N** | Apoiar previsão e cenários sem substituir submissão e aprovação humanas. |
| CRM-AI-016 | **N** | Responder perguntas operacionais usando base de conhecimento aprovada. |
| CRM-AI-017 | **N** | Transferir atendimento para humano quando houver preço, compromisso, exceção, risco ou baixa confiança. |
| CRM-AI-018 | **N** | Registrar modelo, versão, prompt de sistema, fontes, usuário e resultado relevante. |
| CRM-AI-019 | **N** | Aplicar mascaramento, filtro de dados sensíveis e políticas por domínio. |
| CRM-AI-020 | **N** | Permitir feedback útil/não útil, correção e monitoramento de qualidade. |
| CRM-AI-021 | **N** | Não treinar modelo externo com dados corporativos sem contrato e aprovação formal. |
| CRM-AI-022 | **N** | Desabilitar automaticamente automações quando houver anomalia ou risco operacional. |

### 10.33 Notificações, alertas e tempo real

**Objetivo:** informar a pessoa certa, no canal adequado, sem criar ruído ou broadcast indevido.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-NOT-001 | **E** | Manter WebSocket para presença, worklist, carteiras e salas. |
| CRM-NOT-002 | **E** | Manter outbox para notificações do Portal e integrações. |
| CRM-NOT-003 | **E** | Manter notificações de atribuição, conclusão, prazo e pronto para faturar. |
| CRM-NOT-004 | **N** | Adicionar alertas de lead, oportunidade, mensagem, aprovação, campanha, SLA, forecast e exceção. |
| CRM-NOT-005 | **N** | Definir destinatário por envolvimento, owner, grupo, permissão ou regra explícita. |
| CRM-NOT-006 | **N** | Nunca usar `commercial.access` como broadcast genérico para eventos pessoais. |
| CRM-NOT-007 | **N** | Permitir preferências por categoria, canal, horário, digest e importância. |
| CRM-NOT-008 | **N** | Agrupar eventos repetitivos e aplicar deduplicação. |
| CRM-NOT-009 | **N** | Fornecer deep link estável ao registro e estado relevante. |
| CRM-NOT-010 | **N** | Permitir marcar lida, dispensar, adiar e agir a partir da notificação. |
| CRM-NOT-011 | **N** | Implementar escalonamento conforme SLA e ausência de ação. |
| CRM-NOT-012 | **N** | Medir entrega, leitura, ação, falha e latência. |
| CRM-NOT-013 | **N** | Evitar duplicar toast realtime e sino do Portal para o mesmo evento. |
| CRM-NOT-014 | **N** | Respeitar privacidade do conteúdo na prévia da notificação. |

### 10.34 Busca, visões, filtros e exportação

**Objetivo:** tornar a base pesquisável e operável em escala.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SRH-001 | **P** | Evoluir busca de catálogo e buscas locais para busca global autorizada. |
| CRM-SRH-002 | **N** | Indexar entidades e textos permitidos com atualização incremental. |
| CRM-SRH-003 | **N** | Aplicar autorização antes de retornar resultado ou trecho. |
| CRM-SRH-004 | **N** | Suportar busca por código, nome, documento, e-mail, telefone, pedido, produto e texto. |
| CRM-SRH-005 | **N** | Permitir filtros avançados e composição E/OU. |
| CRM-SRH-006 | **N** | Permitir salvar visão pessoal e visão compartilhada administrada. |
| CRM-SRH-007 | **N** | Permitir configurar colunas, ordenação, agrupamento e densidade. |
| CRM-SRH-008 | **N** | Suportar ações em massa com prévia, limite, confirmação e auditoria. |
| CRM-SRH-009 | **N** | Exportar CSV/XLSX/PDF somente conforme permissão e volume seguro. |
| CRM-SRH-010 | **N** | Executar exportações grandes de forma assíncrona, com expiração do arquivo. |
| CRM-SRH-011 | **N** | Registrar filtros e contexto usados na exportação. |
| CRM-SRH-012 | **N** | Aplicar mascaramento e watermark em dados sensíveis quando necessário. |
| CRM-SRH-013 | **N** | Não oferecer “listar tudo” sem paginação ou limite. |
| CRM-SRH-014 | **N** | Manter URLs compartilháveis sem expor dados no query string. |

### 10.35 Administração e configuração

**Objetivo:** permitir evolução do produto sem hardcode de processos e catálogos.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-ADM-001 | **E** | Manter administração de carteiras, membros, grupos e perfis. |
| CRM-ADM-002 | **B** | Implementar administração de pipelines, etapas, motivos, SLAs, segmentos e famílias. |
| CRM-ADM-003 | **N** | Administrar campos personalizados por entidade com tipo, validação e visibilidade. |
| CRM-ADM-004 | **N** | Administrar tags, fontes, campanhas, canais, concorrentes e classificações. |
| CRM-ADM-005 | **N** | Administrar templates de e-mail, mensagem, proposta, sequência, automação e **scripts/roteiros de vendas**. |
| CRM-ADM-015 | **N** | Administrar playbooks e rituais (fim de dia, sumário semanal, 1-on-1, role-play) com checklist e versão publicada. |
| CRM-ADM-006 | **N** | Administrar regras de roteamento, score, saúde, deduplicação e retenção. |
| CRM-ADM-007 | **N** | Administrar conectores, consentimentos, scopes, subscriptions e checkpoints. |
| CRM-ADM-008 | **N** | Exibir saúde das integrações, filas, jobs, outbox e dead-letter. |
| CRM-ADM-009 | **N** | Permitir ativar, pausar e testar configuração antes de publicar. |
| CRM-ADM-010 | **N** | Versionar configurações críticas e permitir rollback seguro. |
| CRM-ADM-011 | **N** | Separar ambiente, segredo e configuração de negócio. |
| CRM-ADM-012 | **N** | Exigir justificativa e auditoria para alterações de alto impacto. |
| CRM-ADM-013 | **N** | Fornecer simulação de público, automação, roteamento e permissão. |
| CRM-ADM-014 | **N** | Não permitir exclusão física de catálogo referenciado; usar inativação. |

### 10.36 Segurança, RBAC, LGPD e auditoria

**Objetivo:** proteger dados comerciais e comunicações corporativas de ponta a ponta.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-SEC-001 | **E** | Validar JWT, issuer, audience, expiração e claims obrigatórias. |
| CRM-SEC-002 | **E** | Aplicar RBAC da Core API e revalidar autorização na `commercial-api`. |
| CRM-SEC-003 | **E** | Resolver escopo de carteira somente no backend. |
| CRM-SEC-004 | **N** | Implementar políticas por capacidade, escopo, sensibilidade e relação com o registro. |
| CRM-SEC-005 | **N** | Aplicar menor privilégio a conectores Microsoft 365 e demais canais. |
| CRM-SEC-006 | **N** | Registrar base legal, consentimento, finalidade e retenção de dados pessoais. |
| CRM-SEC-007 | **N** | Implementar opt-out, anonimização, correção, exportação e descarte conforme processo aprovado. |
| CRM-SEC-008 | **N** | Classificar dados e conteúdo por sensibilidade. |
| CRM-SEC-009 | **N** | Criptografar tráfego, secrets e conteúdo sensível em repouso quando aplicável. |
| CRM-SEC-010 | **N** | Auditar leitura sensível, exportação, download, integração e decisão. |
| CRM-SEC-011 | **E** | Preservar autoria, timestamp e append-only audit para operações críticas. |
| CRM-SEC-012 | **N** | Implementar segregação de função para aprovação e administração. |
| CRM-SEC-013 | **N** | Implementar revisão periódica de acesso e conectores. |
| CRM-SEC-014 | **N** | Detectar acesso anômalo, exportação incomum e falha repetida de autorização. |
| CRM-SEC-015 | **N** | Proibir token, senha, stack trace e SQL em respostas de erro. |
| CRM-SEC-016 | **N** | Aplicar retenção específica para e-mail, Teams, mensagens, gravações e transcrições. |
| CRM-SEC-017 | **N** | Permitir legal hold somente por processo formal e acesso restrito. |
| CRM-SEC-018 | **N** | Documentar matriz de responsabilidade de controlador, operador e fornecedor. |

### 10.37 APIs, webhooks e plataforma de integração

**Objetivo:** permitir integração segura, idempotente e observável com sistemas corporativos.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-API-001 | **E** | Manter envelope `{ success, message, data, meta }`. |
| CRM-API-002 | **E** | Manter paths e `operationId` em inglês e mensagens de usuário em português. |
| CRM-API-003 | **E** | Manter paginação obrigatória, datas ISO 8601 e erros de domínio. |
| CRM-API-004 | **E** | Manter `Idempotency-Key` e controle de versão em escritas sensíveis. |
| CRM-API-005 | **N** | Publicar OpenAPI completo por módulo e versão. |
| CRM-API-006 | **N** | Criar webhooks assinados para eventos aprovados. |
| CRM-API-007 | **N** | Permitir subscriptions por evento, entidade, escopo e callback. |
| CRM-API-008 | **N** | Assinar payload, aplicar retry exponencial e dead-letter. |
| CRM-API-009 | **N** | Registrar delivery, resposta, duração, falha e reprocessamento. |
| CRM-API-010 | **N** | Implementar rate limit por cliente, usuário, integração e endpoint. |
| CRM-API-011 | **N** | Manter correlation ID entre Portal, commercial-api, api-delpi e ERP. |
| CRM-API-012 | **N** | Expor endpoints de health, readiness e status de conectores. |
| CRM-API-013 | **N** | Suportar importação assíncrona, exportação e jobs com acompanhamento. |
| CRM-API-014 | **N** | Não compartilhar módulos internos de regra entre bounded contexts. |
| CRM-API-015 | **N** | Versionar contratos e publicar política de depreciação. |
| CRM-API-016 | **N** | Manter registros de integração e checkpoints fora de controllers e do MFE. |

### 10.38 Experiência móvel, responsividade e acessibilidade

**Objetivo:** permitir operação segura em desktop, notebook, tablet e celular.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-MOB-001 | **P** | Manter responsividade existente e ampliar para novos módulos. |
| CRM-MOB-002 | **N** | Priorizar Meu Dia, conta, mensagens, agenda, oportunidades e visita no celular. |
| CRM-MOB-003 | **N** | Garantir alvos de toque adequados, navegação por teclado e foco visível. |
| CRM-MOB-004 | **N** | Garantir contraste, labels, mensagens de erro e leitura por tecnologia assistiva. |
| CRM-MOB-005 | **N** | Oferecer tabelas adaptadas, cards ou colunas configuráveis em telas pequenas. |
| CRM-MOB-006 | **N** | Permitir captura de foto e anexo somente com consentimento do usuário. |
| CRM-MOB-007 | **N** | Não armazenar tokens ou dados sensíveis de forma insegura no dispositivo. |
| CRM-MOB-008 | **N** | Tratar conexão instável com retry seguro e indicação de estado. |
| CRM-MOB-009 | **N** | Não executar escrita duplicada após reconexão. |
| CRM-MOB-010 | **N** | Avaliar PWA somente após requisitos de segurança, cache e logout. |
| CRM-MOB-011 | **N** | Suportar modo claro e escuro pelos tokens da Minha DELPI. |
| CRM-MOB-012 | **N** | Usar `@delpi/plugin-ui` antes de criar componentes próprios. |

### 10.39 Rituais comerciais, disciplina e coaching

**Objetivo:** transformar hábitos de alta performance (benchmark [Agendor — rituais de vendas](https://www.agendor.com.br/blog/rituais-de-vendas/)) em capacidades do produto, sem virar “relógio de ponto” nem app de bem-estar.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-RIT-001 | **N** | Ritual **preparar o dia seguinte**: ao fim do expediente, lista do amanhã com compromissos, oportunidades sem próximo passo e lembretes. |
| CRM-RIT-002 | **N** | Ritual **lista do dia** com checks, priorização e fechamento do dia (itens feitos vs. remanescentes). |
| CRM-RIT-003 | **N** | Ritual **segmentar antes de prospectar**: fila de ligações/cadência agrupada por perfil, setor, origem, ticket ou necessidade. |
| CRM-RIT-004 | **N** | Ritual **script por perto**: abrir roteiro de qualificação/objeção na mesma tela da atividade. |
| CRM-RIT-005 | **N** | Ritual **histórico antes do contato**: briefing obrigatório ou recomendado conforme política da equipe. |
| CRM-RIT-006 | **N** | Ritual **atualizar CRM após abordagem**: outcome, próximo passo e campos mínimos antes de concluir a atividade. |
| CRM-RIT-007 | **N** | Ritual opcional **propósito × meta**: vincular meta comercial a objetivo pessoal declarado pelo vendedor (motivação), sem exposição pública forçada. |
| CRM-RIT-008 | **N** | Ritual de gestão **reunião semanal**: agenda gerada a partir do sumário (resultados, forecast, riscos e gaps). |
| CRM-RIT-009 | **N** | Ritual de gestão **1-on-1**: pauta, feedback mútuo, acordos e tarefas de coaching com histórico. |
| CRM-RIT-010 | **N** | Ritual de gestão **role-play**: cenários, script, gravação opcional autorizada e feedback estruturado. |
| CRM-RIT-011 | **N** | Ritual **SLA marketing–vendas**: reunião/artefato recorrente com handoff, critérios de MQL/SQL e métricas de qualidade. |
| CRM-RIT-012 | **N** | Configurar quais rituais são recomendados vs. obrigatórios por equipe, sem hardcode de cargo. |
| CRM-RIT-013 | **N** | Fora de escopo de produto: técnica Pomodoro, pausas de bem-estar e qualquer controle de “tempo de tela” — o CRM não deve cronometrar foco pessoal. |

### 10.40 Funil Kanban omnicanal de conversas

**Objetivo:** oferecer quadro estilo Trello/Kanban em que cada cartão é uma **conversa** (thread) normalizada no CRM, independentemente do canal de origem — inspirado no [funil ChatGuru](https://chatguru.com.br/blog/como-fazer-funil-de-vendas-no-whatsapp-no-estilo-do-trello/), generalizado para Teams, Outlook, WhatsApp, web chat e redes sociais homologadas.

> O funil de **oportunidade** (§ 10.11) continua sendo a visão de receita. O funil de **conversa** governa atendimento e qualificação do contato no canal. Conversão (lead/oportunidade) e handoff entre funis devem preservar histórico e vínculos.

| ID | Status | Requisito funcional |
|---|---:|---|
| CRM-FNL-001 | **N** | Criar múltiplos funis de conversa (ex.: atendimento, prospecção, pós-venda/produção) com nome, dono, escopo e status. |
| CRM-FNL-002 | **N** | Definir etapas como colunas ordenáveis (arrastar para reordenar), com cor, SLA e tipo semântico (entrada, trabalho, ganho, perdido, postergado). |
| CRM-FNL-003 | **N** | Representar cada cartão como conversa omnicanal vinculável a contato, lead, conta, oportunidade e pedido. |
| CRM-FNL-004 | **N** | Exibir no cartão: nome/identidade, canal (badge), identificador do canal (telefone, e-mail, Teams, handle social), tags, data de entrada, owner, bot ligado/desligado, etapa, preview da última mensagem e aging. |
| CRM-FNL-005 | **N** | Mover cartão por drag-and-drop no quadro ou pela troca de etapa dentro da tela da conversa, com validação, concorrência e auditoria no backend. |
| CRM-FNL-006 | **N** | Inserir conversa automaticamente no funil/etapa por gatilho: primeira mensagem, saudação/palavra-chave, evento de chatbot, formulário, tag, score ou regra de jornada. |
| CRM-FNL-007 | **N** | Mover conversa entre etapas por automação (bot, cadência, SLA, resposta do cliente, transferência humana) sem perder contexto do thread. |
| CRM-FNL-008 | **N** | Adicionar conversas existentes ao funil em lote, com filtros por canal, fila, owner, tag, status e período, e prévia antes de confirmar. |
| CRM-FNL-009 | **N** | Permitir anotações internas no cartão/conversa visíveis à equipe autorizada (não enviadas ao cliente). |
| CRM-FNL-010 | **N** | Aplicar tags de campanha, qualificação e status no cartão, reutilizáveis em filtros, automações e segmentos. |
| CRM-FNL-011 | **N** | Restringir visibilidade: usuário sem permissão de “ver todos” enxerga apenas cartões atribuídos a si (ou à sua fila/carteira). |
| CRM-FNL-012 | **N** | Medir tempo em cada etapa/status, conversão entre colunas, abandono, volume por canal e taxa de handoff para oportunidade. |
| CRM-FNL-013 | **N** | Converter cartão qualificado em lead e/ou oportunidade nativa, com cópia controlada de contexto, canal de origem e histórico. |
| CRM-FNL-014 | **N** | Unificar no mesmo quadro conversas de WhatsApp, Teams, Outlook/e-mail, web chat e redes sociais autorizadas, sem funil separado por canal. |
| CRM-FNL-015 | **N** | Modelar conector de canal como adaptador: ingestão, identidade externa, envio e webhooks — o domínio do funil não conhece detalhes do provedor. |
| CRM-FNL-016 | **N** | Exigir conector oficial / API homologada; proibir histórico corporativo baseado em dispositivo pessoal ou automação não governada. |
| CRM-FNL-017 | **N** | Respeitar consentimento, opt-out, janela do canal, classificação sensível e retenção por política ao exibir cartão e conteúdo. |
| CRM-FNL-018 | **N** | Atualizar o quadro em tempo real (Socket.IO / outbox) quando cartões entrarem, mudarem de etapa ou forem reatribuídos. |

---

## 11. Matriz consolidada de gaps

| Domínio | Hoje | Alvo | Maior gap | Prioridade sugerida |
|---|---|---|---|---:|
| Home comercial | Launcher e eventos | Cockpit completo por contexto | Priorização entre canais e processos | P1 |
| Conta 360 | Dados ERP + contatos + atividades | Timeline omnicanal e plano de conta | Histórico ainda fragmentado | P1 |
| Contatos | CRUD local e contato ERP | Comitê de compra, consentimento e identidade | Papéis e qualidade de contato | P1 |
| Prospects/leads | Modelo planejado | Gestão completa pré-cliente | Não há lifecycle nativo confirmado | P1 |
| Pipeline | OV de ERP e visão analítica | CRUD nativo, mapa de vendas e handoff entre funis | Falta governança de etapas, saúde visual e congelamento | P1 |
| Oportunidades | Consulta parcial | Negociação completa, health e congelamento | Falta owner, next step e workflow nativos | P1 |
| Tarefas | Forte base entregue | Checklist, recorrência, fluxo inteligente e rituais diários | Disciplina pós-abordagem e próximo passo | P2 |
| Calendário | Sem conector | Agenda, reuniões, free/busy, visitas e mapa de rotas | Integração Microsoft 365 + rotas | P2 |
| Sala de interação | Entregue | Integrada a todas as entidades e decisões | Visibilidade sensível e templates | P2 |
| Teams | Backlog | Conversas e transcrições seletivas | Consentimento, ingestão e associação | P2 |
| Outlook/e-mail | Backlog | Histórico, envio e inbox compartilhada | Conector e governança | P2 |
| Mensageria | Sem inbox oficial | Atendimento, campanhas, handoff e **funil Kanban omnicanal** | Conector + quadro de conversas multi-canal | P2 |
| Funil de conversas | Ausente | Kanban estilo Trello com cartão = thread (Teams/Outlook/WhatsApp/redes) | Entrada por gatilho, lote e handoff para oportunidade | P2 |
| Voz | Ausente | Metadados, gravação e transcrição controladas | Telefonia e consentimento | P4 |
| Segmentação | Ausente | Públicos dinâmicos B2B | Motor de consulta e consentimento | P2 |
| Campanhas | Ausente | E-mail, conteúdo e mensuração | Entregabilidade e serviço de envio | P3 |
| Formulários | Ausente | Captura rastreável | Builder, segurança e tracking | P3 |
| Automação | Ausente | Fluxos de marketing e vendas | Orquestrador versionado | P3 |
| Scoring | Ausente | Perfil, comportamento e intenção | Motor explicável | P3 |
| Atribuição/CAC | Ausente | Jornada até receita | Custos, modelos e qualidade de vínculo | P4 |
| Propostas | Consulta/PDF | Versionamento, aprovação e aceite | Workflow comercial | P2 |
| Forecast | Backlog | Ciclos, submissões e snapshots | Modelo definitivo e aprovação | P2 |
| Carteiras | Entregue | Território, rotação e cobertura | Mapa e distribuição | P3 |
| Confirmação de pedido | Backlog | SLA ponta a ponta | Workflow entre áreas | P2 |
| Produção/entrega | Boa leitura operacional | Exceção e comunicação estruturada | Dados de transporte e ownership | P3 |
| Amostras | Backlog | Processo técnico ligado à receita | Etapas e integração entre áreas | P3 |
| BI | Forte base | CRM + marketing + forecast + CAC + sumário semanal | Fichas de KPI, mapa de vendas e rituais de gestão | P2 |
| Rituais / coaching | Ausente | Rituais do vendedor e do gestor no produto | Disciplina de uso sem vigilância indevida | P2 |
| IA | Ausente | Copiloto explicável e supervisionado | Plataforma, governança e avaliação | P4 |
| Qualidade de dados | Parcial | Importação, dedupe e data stewardship | Identidade canônica | P1 |
| Auditoria/LGPD | Base existente | Governança de conteúdo omnicanal | Retenção e acessos sensíveis | P1 transversal |
| APIs/webhooks | Base de API e outbox | Plataforma de integração completa | Subscriptions externas e observabilidade | P1 transversal |

---

## 12. Arquitetura da informação alvo

A evolução deve manter a Home como ponto de ação e evitar uma barra principal com dezenas de itens.

### 12.1 Navegação principal proposta

```text
Início
Meu Dia
CRM
Contas
Conversas
Visão geral
Administração†
```

† somente para usuários autorizados.

### 12.2 Subáreas

| Área | Conteúdo |
|---|---|
| **Início** | Eventos, prioridades, favoritos, busca, recentes e atalhos contextuais |
| **Meu Dia** | Tarefas, agenda, mensagens pendentes, leads novos, follow-ups, rituais diários e aprovações |
| **CRM** | Leads, prospects, pipeline, mapa de vendas, oportunidades, propostas, forecast, cadências e campanhas |
| **Contas** | Carteiras, lista de clientes, Conta 360, planos, contatos e territórios |
| **Conversas** | Inbox omnicanal, funil Kanban de conversas, sala interna, e-mail compartilhado, Teams, mensageria, redes homologadas e chamadas autorizadas |
| **Visão geral** | Gestão à vista, funil, mapa de vendas, forecast, marketing, produtividade, SLA, OTD, receita e sumários |
| **Administração** | Carteiras, membros, grupos, pipelines, scripts, rituais, catálogos, automações, integrações e auditoria |

### 12.3 Regras de experiência

- no máximo duas ações primárias por seção;
- qualquer alerta deve levar ao registro que o originou;
- filtros devem sobreviver à navegação quando fizer sentido;
- listas precisam de paginação e estados de loading/erro por seção;
- ações em massa precisam de prévia e confirmação;
- a Conta 360 deve ser a referência de contexto, não uma cópia de todos os módulos;
- o produto deve usar componentes de `@delpi/plugin-ui` e tokens da plataforma;
- novas rotas devem ser internas ao app sempre que não precisarem aparecer no menu global;
- a autorização final deve continuar no backend.

---

## 13. Modelo de dados funcional mínimo

### 13.1 Entidades atuais que devem ser preservadas e evoluídas

| Entidade atual | Evolução esperada |
|---|---|
| `seller_portfolios` | Cobertura, território, substituição e regras de distribuição |
| `seller_portfolio_members` | Papéis de membership e vigência temporal |
| `seller_customers` | Histórico de vínculo, origem e motivo de transferência |
| `commercial_groups` | Grupos operacionais por finalidade |
| `commercial_group_members` | Vigência e fonte do membership |
| `commercial_user_profiles` | Preferências, contatos e disponibilidade comercial |
| `account_contacts` | Comitê de compra, consentimentos e identidades externas |
| `customer_avatars` | Manter como metadado visual, sem virar cadastro paralelo |
| `tasks` | Recorrência, checklist, lembretes e associações genéricas |
| `task_assignees` | Vigência, aceite e conclusão por responsável |
| `task_assignee_groups` | Expansão controlada e snapshot de destinatários |
| `task_customers` | Generalizar associação sem perder compatibilidade |
| `activities` | Evoluir para eventos normalizados da timeline |
| `attachments` | Mais owner types, classificação, versão e origem |
| `interaction_rooms` | Novas entidades e visibilidade sensível |
| `interaction_room_members` | Preferências, cursor e watchers |
| `interaction_messages` | Decisão, risco, ação e integração externa |
| `interaction_mentions` | Novos tipos de entidade e identidade externa |
| `interaction_reactions` | Manter como interação leve |
| `interaction_pins` | Pins por contexto e categoria |
| `integration_outbox` | Eventos internos e externos com retry/dead-letter |
| `integration_checkpoints` | Cursor, delta, subscription e reconciliação |
| `audit_log` | Cobertura de leitura/exportação sensível |
| `sla_policies` | Aplicação a mais processos e versões |

### 13.2 Novas entidades — núcleo comercial

| Grupo | Entidades mínimas |
|---|---|
| Prospect e lead | `prospects`, `prospect_contacts`, `lead_sources`, `lead_assignments`, `lead_status_history` |
| Pipeline | `pipeline_definitions`, `pipeline_versions`, `pipeline_stages`, `pipeline_stage_rules` |
| Oportunidade | `opportunities`, `opportunity_contacts`, `opportunity_team`, `opportunity_products`, `opportunity_stage_history`, `opportunity_value_history`, `opportunity_risks` |
| Proposta | `quote_requests`, `proposal_versions`, `proposal_items`, `proposal_approvals`, `proposal_deliveries` |
| Conta | `account_profiles`, `account_relationships`, `account_plans`, `account_plan_actions`, `account_health_snapshots` |
| Visita | `visits`, `visit_attendees`, `visit_outcomes`, `vehicle_requests` |
| Forecast | `forecast_cycles`, `forecast_submissions`, `forecast_items`, `forecast_adjustments`, `forecast_approvals`, `forecast_snapshots` |
| Rituais e coaching | `sales_scripts`, `sales_rituals`, `ritual_completions`, `coaching_one_on_ones`, `deal_freezes` |

> A migration simplificada de declaração de forecast removida não deve ser reativada. O forecast completo precisa de modelo próprio e nova sequência de migrations.

### 13.3 Novas entidades — marketing e jornada

| Grupo | Entidades mínimas |
|---|---|
| Segmentação | `segments`, `segment_versions`, `segment_memberships` |
| Campanha | `campaigns`, `campaign_assets`, `campaign_audiences`, `campaign_costs`, `campaign_deliveries` |
| Formulários | `forms`, `form_versions`, `form_submissions`, `landing_pages` |
| Automação | `automation_flows`, `automation_versions`, `automation_enrollments`, `automation_step_runs` |
| Tracking | `journey_events`, `anonymous_identities`, `identity_links`, `tracking_consents` |
| Scoring | `scoring_models`, `scoring_rules`, `score_snapshots`, `score_explanations` |
| Atribuição | `attribution_models`, `attribution_touches`, `attribution_results` |
| Consentimento | `consents`, `consent_events`, `suppression_entries`, `communication_preferences` |
| Cadências | `sequences`, `sequence_versions`, `sequence_steps`, `sequence_enrollments`, `sequence_executions` |

### 13.4 Novas entidades — omnicanal

| Grupo | Entidades mínimas |
|---|---|
| Conectores | `integration_connections`, `integration_permissions`, `integration_subscriptions`, `integration_jobs` |
| Identidade externa | `external_identities`, `external_entity_links` |
| E-mail | `email_threads`, `email_messages`, `email_participants`, `shared_inboxes` |
| Teams | `teams_conversations`, `teams_messages`, `teams_meetings`, `meeting_transcripts` |
| Mensageria | `channel_inboxes`, `channel_conversations`, `channel_messages`, `channel_templates` |
| Voz | `call_records`, `call_participants`, `call_transcripts`, `call_recording_refs` |
| Timeline | `timeline_events`, `timeline_links`, `timeline_visibility` |

### 13.5 Novas entidades — processos industriais

| Grupo | Entidades mínimas |
|---|---|
| Amostras | `samples`, `sample_stage_history`, `sample_documents`, `sample_results` |
| Confirmação | `order_confirmation_cases`, `order_confirmation_stage_history`, `order_confirmation_responses` |
| Entrega | `delivery_exceptions`, `delivery_exception_actions`, `delivery_updates` |
| Aprovação | `approval_requests`, `approval_steps`, `approval_decisions` |
| Qualidade de dados | `data_quality_issues`, `merge_candidates`, `merge_decisions` |

### 13.6 Regras do modelo

- UUID para entidades próprias;
- chaves externas explícitas e únicas por fonte;
- timestamps em UTC;
- soft delete para registros de negócio;
- versionamento otimista em escritas concorrentes;
- histórico append-only para transições e decisões;
- `created_by`, `updated_by` e `source` quando aplicável;
- nenhuma FK direta ao banco interno do Keycloak;
- nenhum clone integral de dados do ERP;
- conteúdo externo com `external_id`, hash e estado de sincronização;
- índices para owner, status, data, account key, opportunity, source e external id;
- particionamento ou arquivamento para eventos de jornada e mensagens em alto volume;
- retenção configurável por classe de conteúdo.

---

## 14. Modelo de autorização recomendado

### 14.1 Princípio

O catálogo atual é deliberadamente condensado:

- `commercial.access`;
- `commercial.manage`;
- `commercial.billing.notify`.

O CRM completo não deve criar uma permissão por botão ou tela. Novos códigos só se justificam quando existir uma fronteira real de sensibilidade, administração, aprovação, exportação ou integração.

### 14.2 Códigos atuais a preservar

| Código | Uso |
|---|---|
| `commercial.access` | Uso operacional comum do Portal Comercial e das capacidades autorizadas pelo escopo |
| `commercial.manage` | Administração estrutural, visão ampla de carteiras e ações de gestão |
| `commercial.billing.notify` | Destinatário específico de notificações de faturamento |

### 14.3 Candidatos de capacidade sensível

> Estes códigos são proposta de desenho. Cada inclusão no manifesto deve ser justificada no PR, documentada e concedida antes do deploy.

| Código candidato | Justificativa |
|---|---|
| `commercial.marketing.manage` | Criar segmentos, campanhas, formulários e automações |
| `commercial.campaigns.send` | Aprovar ou executar disparos externos em massa |
| `commercial.pipeline.manage` | Administrar pipelines, etapas e regras, sem liberar toda a administração |
| `commercial.forecast.submit` | Submeter forecast próprio ou da carteira |
| `commercial.forecast.approve` | Ajustar, devolver e aprovar forecast de equipe |
| `commercial.integrations.manage` | Configurar conectores, subscriptions, scopes e credenciais |
| `commercial.audit.view` | Consultar trilha de auditoria comercial |
| `commercial.sensitive-financial.view` | Visualizar margem, rentabilidade ou informação financeira sensível |
| `commercial.sensitive-communications.view` | Acessar gravações, transcrições ou conteúdo restrito quando necessário |
| `commercial.data-export` | Executar exportações amplas ou sensíveis |
| `commercial.ai.manage` | Configurar modelos, prompts, políticas e automações de IA |

### 14.4 Papéis sugeridos

| Papel | Capacidades agrupadas |
|---|---|
| Comercial — Operacional | `commercial.access` + membership de carteira |
| Comercial — Gestão | `commercial.access` + `commercial.manage` + capacidades de forecast aprovadas |
| Pré-vendas | `commercial.access` + acesso às filas e cadências atribuídas |
| Marketing | `commercial.access` + `commercial.marketing.manage`; envio em massa separado |
| Orçamentista | `commercial.access` + escopo de propostas e aprovações necessárias |
| Faturamento | `commercial.access` + `commercial.billing.notify` |
| Sales Operations | gestão de pipeline, qualidade, integrações e auditoria conforme função |
| Auditor | acesso de leitura e auditoria, sem alteração operacional |
| Administração técnica | integração e configuração, sem acesso automático a conteúdo comercial sensível |

### 14.5 Escopos adicionais

Além da permissão, a API deve considerar:

- membership de carteira;
- owner e equipe da oportunidade;
- participante da conversa;
- unidade e território;
- envolvimento em tarefa ou aprovação;
- classificação do conteúdo;
- vigência de substituição temporária;
- finalidade do conector;
- relação do usuário com o registro.

---

## 15. Catálogo de eventos do domínio

Os eventos devem ser coletados pelo use case, persistidos na outbox quando necessário e publicados somente após commit.

### 15.1 Leads e contas

```text
commercial.lead.created
commercial.lead.assigned
commercial.lead.accepted
commercial.lead.qualified
commercial.lead.disqualified
commercial.lead.converted
commercial.account.created
commercial.account.updated
commercial.account.owner_changed
commercial.account.health_changed
commercial.account.risk_detected
commercial.account.reactivated
```

### 15.2 Pipeline e oportunidades

```text
commercial.opportunity.created
commercial.opportunity.stage_changed
commercial.opportunity.value_changed
commercial.opportunity.owner_changed
commercial.opportunity.risk_changed
commercial.opportunity.stalled
commercial.opportunity.won
commercial.opportunity.lost
commercial.opportunity.reopened
commercial.proposal.requested
commercial.proposal.version_created
commercial.proposal.sent
commercial.proposal.viewed
commercial.proposal.approved
commercial.proposal.rejected
commercial.proposal.expired
```

### 15.3 Tarefas, agenda e colaboração

```text
commercial.task.created
commercial.task.assigned
commercial.task.group_assigned
commercial.task.reassigned
commercial.task.due_soon
commercial.task.overdue
commercial.task.completed
commercial.task.cancelled
commercial.meeting.created
commercial.meeting.updated
commercial.meeting.completed
commercial.visit.created
commercial.visit.completed
commercial.room.message_created
commercial.room.mention_created
commercial.room.decision_marked
```

### 15.4 Marketing e jornada

```text
commercial.form.submitted
commercial.contact.identified
commercial.journey.page_viewed
commercial.campaign.started
commercial.campaign.paused
commercial.campaign.completed
commercial.message.delivered
commercial.message.opened
commercial.message.clicked
commercial.message.replied
commercial.message.bounced
commercial.contact.opted_out
commercial.score.changed
commercial.segment.membership_changed
commercial.automation.enrolled
commercial.automation.step_executed
commercial.automation.completed
```

### 15.5 Integrações e canais

```text
commercial.integration.connected
commercial.integration.permission_changed
commercial.integration.subscription_expiring
commercial.integration.sync_started
commercial.integration.sync_completed
commercial.integration.sync_failed
commercial.external_message.created
commercial.external_message.updated
commercial.external_message.deleted
commercial.meeting.transcript_available
commercial.channel.conversation_assigned
commercial.channel.handoff_requested
```

### 15.6 ERP e processos industriais

```text
commercial.erp.customer_linked
commercial.erp.preorder_requested
commercial.erp.order_linked
commercial.order.confirmation_started
commercial.order.stage_changed
commercial.order.confirmed
commercial.order.ready_to_invoice
commercial.order.invoiced
commercial.order.shipped
commercial.delivery.exception_created
commercial.delivery.exception_escalated
commercial.delivery.exception_resolved
commercial.sample.created
commercial.sample.stage_changed
commercial.sample.approved
commercial.sample.rejected
```

### 15.7 Forecast, aprovação e IA

```text
commercial.forecast.cycle_opened
commercial.forecast.submitted
commercial.forecast.adjusted
commercial.forecast.approved
commercial.forecast.rejected
commercial.approval.requested
commercial.approval.approved
commercial.approval.rejected
commercial.ai.suggestion_created
commercial.ai.suggestion_accepted
commercial.ai.suggestion_rejected
commercial.ai.external_action_confirmed
```

### 15.8 Requisitos dos eventos

Todo evento deve possuir, quando aplicável:

```json
{
  "event_id": "uuid",
  "event_type": "commercial.opportunity.stage_changed",
  "occurred_at": "ISO-8601 UTC",
  "actor_user_id": "keycloak-sub-or-system",
  "entity_type": "opportunity",
  "entity_id": "uuid",
  "account_key": {
    "customer_code": "...",
    "customer_store": "..."
  },
  "correlation_id": "uuid",
  "causation_id": "uuid-or-null",
  "schema_version": 1,
  "payload": {}
}
```

Regras:

- payload mínimo e sem segredo;
- schema versionado;
- idempotência por `event_id`;
- correlation ID ponta a ponta;
- evento não substitui consulta autorizada ao registro;
- dados pessoais devem ser minimizados;
- consumidores devem tolerar reentrega;
- falha de consumidor não desfaz a transação original.

---

## 16. Requisitos não funcionais

### 16.1 Segurança

- JWT validado em toda rota protegida;
- menor privilégio e consentimento administrativo para integrações;
- secrets fora do repositório e das variáveis frontend;
- TLS em produção;
- criptografia de conteúdo sensível em repouso quando aplicável;
- proteção contra CSRF nos fluxos que exigirem cookie;
- rate limit e proteção contra abuso;
- validação de arquivo e conteúdo;
- logs sem token, senha ou conteúdo pessoal desnecessário;
- revisão de dependências e imagens;
- segregação entre ambiente de desenvolvimento e produção.

### 16.2 Privacidade e retenção

- inventário de dados pessoais por módulo;
- finalidade e base legal documentadas;
- consentimentos versionados;
- retenção por tipo de conteúdo;
- descarte e anonimização verificáveis;
- opt-out imediato para campanhas futuras;
- política específica para mensagens, e-mails, gravações e transcrições;
- restrição a conteúdo privado ou não comercial;
- trilha de exportação e acesso sensível;
- resposta a solicitações do titular por processo corporativo.

### 16.3 Desempenho

Metas iniciais propostas, sujeitas a teste de carga e validação de infraestrutura:

| Cenário | Meta inicial |
|---|---:|
| Abertura de página com dados locais | p95 até 2 s |
| Lista composta com dependência do ERP | p95 até 5 s, com loading parcial |
| Busca global | p95 até 2 s para resultados iniciais |
| Evento realtime | p95 até 3 s após commit |
| Notificação do Portal | p95 até 60 s para eventos assíncronos comuns |
| Importação/campanha/exportação grande | assíncrona, com progresso e sem bloquear request web |

Regras:

- paginação obrigatória;
- batch para enriquecimentos;
- cache somente com `freshness` explícita;
- evitar N+1;
- timeout e circuit breaker em integrações;
- índices e planos de consulta monitorados;
- particionamento/arquivamento de eventos de alto volume;
- limites de payload e arquivo.

### 16.4 Disponibilidade e resiliência

- health, readiness e liveness;
- retry exponencial com jitter;
- circuit breaker para fontes externas;
- outbox e dead-letter;
- renovação automática de subscriptions;
- reconciliação periódica após perda de webhook;
- reprocessamento idempotente;
- backup e restauração testados;
- recuperação de storage de anexos;
- degradação parcial quando ERP ou canal estiver indisponível;
- comandos críticos bloqueados quando não houver confirmação da origem.

### 16.5 Observabilidade

- logs estruturados;
- correlation ID em todos os serviços;
- métricas de API, banco, fila, job, webhook e conector;
- tracing distribuído para fluxos críticos;
- dashboards de sincronização;
- alertas de atraso, throttling, dead-letter e falha de renovação;
- monitoramento de qualidade de IA;
- métricas de custo de canal e modelo;
- auditoria funcional separada de log técnico.

### 16.6 Qualidade e testes

- testes unitários de regras;
- testes de contrato entre MFE e `commercial-api`;
- testes de contrato entre `commercial-api` e `api-delpi`;
- testes de integração de banco e migrations;
- testes de autorização por papel e escopo;
- testes de idempotência e concorrência;
- testes de webhook, retry e recuperação;
- testes de retenção e exclusão;
- testes de acessibilidade;
- testes visuais das rotas principais;
- testes de carga nos caminhos críticos;
- datasets sintéticos ou anonimizados em ambientes não produtivos.

### 16.7 Acessibilidade e UX

- compatibilidade com teclado;
- foco visível;
- labels e mensagens de erro associadas;
- contraste adequado;
- semântica de tabelas e formulários;
- redução de movimento quando solicitada;
- layout responsivo;
- botões com tamanho de toque adequado;
- conteúdo em português e identificadores técnicos em inglês;
- ajuda contextual centralizada, não espalhada em literais JSX.

---

## 17. Roadmap funcional sugerido

O roadmap abaixo organiza dependências. Ele não substitui playbooks técnicos por etapa.

### Fase 0 — Governança e fundação transversal

**Objetivo:** preparar o domínio para crescer sem criar dívida estrutural.

Entregas:

- confirmar bounded context e donos de dados;
- consolidar OpenAPI atual;
- definir eventos e outbox;
- catálogo de erros;
- correlação ponta a ponta;
- política de retenção e classificação;
- matriz de permissões e escopos;
- data quality e identidade externa;
- observabilidade de jobs e integrações;
- índices, paginação e critérios de performance;
- estratégia de busca e timeline.

Critério de saída:

> Nenhum módulo novo inicia com regra no MFE, chamada direta à `api-delpi`, dado mestre duplicado ou integração sem idempotência/auditoria.

### Fase 1 — Núcleo CRM

**Objetivo:** entregar a jornada nativa de prospect até oportunidade.

Entregas:

- prospects e leads;
- contatos e comitê de compra;
- importação, dedupe e qualidade;
- múltiplos pipelines;
- oportunidades e histórico de etapas;
- produtos e interesses;
- motivos de qualificação, ganho e perda;
- Conta 360 com timeline unificada inicial;
- busca global inicial;
- indicadores de lead, pipeline, aging e conversão.

### Fase 2 — Produtividade, proposta e previsão

**Objetivo:** estruturar execução e previsibilidade.

Entregas:

- tarefas com checklist, recorrência e lembretes;
- sequências/cadências;
- solicitação e versionamento de proposta;
- aprovações comerciais;
- forecast por ciclo, submissão, aprovação e snapshot;
- plano de conta;
- alertas de oportunidade parada e ausência de próximo passo;
- indicadores de produtividade e acurácia.

### Fase 3 — Microsoft 365 e colaboração integrada

**Objetivo:** incorporar calendário, e-mail e conversas corporativas autorizadas.

Entregas:

- registro de aplicativo e consentimentos;
- conector Outlook;
- calendário, free/busy, criação e sincronização de eventos;
- e-mail individual e inbox compartilhada;
- conector Teams por allowlist/finalidade;
- mensagens, threads e reuniões vinculadas;
- transcrições permitidas;
- subscriptions, lifecycle, checkpoint, reconciliação e auditoria;
- políticas de retenção e acesso sensível.

### Fase 4 — Marketing e jornada digital

**Objetivo:** fechar o ciclo aquisição → venda.

Entregas:

- segmentos;
- formulários e páginas de conversão;
- campanhas e templates;
- tracking e consentimento;
- automações de nutrição;
- scoring;
- atribuição inicial;
- dashboards de campanha e conversão;
- conexão com pipeline e receita.

### Fase 5 — Mensageria e atendimento omnicanal

**Objetivo:** centralizar relacionamento externo em canais aprovados.

Entregas:

- conector oficial de mensageria;
- inbox, filas e distribuição;
- templates e opt-in;
- campanhas autorizadas;
- áudio e transcrição de mensagem;
- handoff humano;
- base de conhecimento;
- SLA e indicadores;
- telefonia corporativa, se aprovada.

### Fase 6 — Processos industriais conectados

**Objetivo:** conectar o ciclo comercial ao cumprimento do pedido.

Entregas:

- confirmação de pedido;
- passagem entre áreas;
- amostras e desenvolvimento;
- exceções de entrega;
- aprovações genéricas;
- linha do tempo pós-venda;
- indicadores de SLA, reincidência e conversão técnica.

### Fase 7 — Inteligência avançada

**Objetivo:** aplicar IA e otimização após haver dados confiáveis e governança.

Entregas:

- resumos com fontes;
- preparação de reunião;
- extração de ações;
- next best action;
- sugestão de cross-sell e reativação;
- saúde de conta e oportunidade;
- apoio ao forecast;
- sugestão de redistribuição;
- atendimento assistido;
- avaliação contínua, feedback e guardrails.

### Fase 8 — Otimização e expansão

Entregas possíveis:

- mapa de territórios;
- rotação avançada;
- otimização de carteira;
- atribuição multitoque completa;
- CAC e payback;
- assinatura eletrônica;
- experiência móvel ampliada;
- APIs para parceiros internos;
- novos canais autorizados.

---

## 18. Definição de pronto por funcionalidade

Uma funcionalidade do CRM só pode ser considerada pronta quando atender, quando aplicável, a todos os itens abaixo:

### 18.1 Produto e UX

- requisito e persona definidos;
- tela usa kit oficial ou justifica exceção;
- loading, vazio, erro, sucesso e acesso negado implementados;
- desktop e mobile verificados;
- acessibilidade básica validada;
- textos em português centralizados;
- deep links e navegação preservados;
- ajuda contextual atualizada.

### 18.2 Backend e dados

- regra no use case/serviço correto;
- repository e Unit of Work usados;
- migration reversível ou procedimento de rollback definido;
- idempotência aplicada quando necessária;
- concorrência e versão tratadas;
- auditoria registrada;
- paginação, filtros e índices definidos;
- erro de domínio padronizado;
- data source e system of record documentados.

### 18.3 Segurança

- autenticação testada;
- autorização e escopo testados;
- conteúdo sensível classificado;
- menor privilégio aplicado;
- exportação e download protegidos;
- logs sem segredo;
- retenção e consentimento definidos;
- riscos de LGPD avaliados.

### 18.4 Integrações

- contrato e versão documentados;
- timeout, retry e circuit breaker definidos;
- webhook/subscription renovável;
- checkpoint e reconciliação implementados;
- idempotência externa testada;
- dead-letter e reprocessamento disponíveis;
- health operacional visível;
- falha parcial tratada.

### 18.5 Eventos e notificações

- evento publicado após commit;
- schema versionado;
- consumidores idempotentes;
- destinatário correto;
- sem broadcast indevido;
- deep link válido;
- preferência do usuário respeitada;
- duplicidade entre canais evitada.

### 18.6 Qualidade

- testes unitários;
- testes de integração;
- testes de autorização;
- testes de contrato;
- teste de migração;
- teste de erro e timeout;
- typecheck/lint/build;
- documentação atualizada;
- evidência de homologação.

---

## 19. Critérios de aceite do produto completo

O CRM-alvo deve ser capaz de demonstrar, com dados de homologação, os seguintes cenários:

1. importar uma base, detectar duplicidades e criar leads sem duplicar clientes do ERP;
2. capturar um lead por formulário, registrar origem e atribuí-lo;
3. qualificar o lead e convertê-lo em oportunidade;
4. executar pipeline diferente para aquisição e gestão de conta;
5. registrar contatos e comitê de compra;
6. criar tarefas, cadência, reunião e follow-up;
7. consultar histórico corporativo durante ausência do responsável;
8. vincular e-mail e conversa autorizada à oportunidade;
9. importar mensagem e transcrição de reunião do Teams sob política aprovada;
9a. operar funil Kanban de conversas com cartões de Teams, Outlook, WhatsApp e rede homologada no mesmo quadro, mover por gatilho/lote e converter em lead/oportunidade;
10. criar proposta, obter aprovação e registrar aceite;
11. associar a oportunidade ganha ao pedido do ERP;
12. acompanhar confirmação, produção, faturamento e entrega;
13. registrar uma exceção e comunicação ao cliente;
14. reativar uma conta por segmento/campanha;
15. rastrear campanha → lead → oportunidade → pedido → faturamento;
16. submeter e aprovar forecast;
17. explicar cada indicador e score;
18. gerar resumo e próximas ações por IA com fontes;
19. impedir envio externo autônomo sem política/confirmação;
20. provar autorização, auditoria, retenção e reprocessamento de integração.

---

## 20. Decisões que precisam ser formalizadas antes da implementação

| Tema | Decisão necessária |
|---|---|
| Nome e posicionamento | Confirmar se “CRM Minha DELPI” será nome de produto ou nome funcional dentro do Portal Comercial |
| Marketing | Confirmar se ficará no mesmo MFE ou em submódulo/remote compartilhando o bounded context |
| Serviço de envio | Escolher infraestrutura de e-mail transacional e marketing |
| Tracking web | Definir sites, domínios, consentimento e política de cookies |
| Microsoft 365 | Definir delegated x application permissions, allowlist e aprovação administrativa |
| Teams | Definir quais equipes, canais, chats e reuniões são comercialmente elegíveis |
| Transcrições | Definir ativação, speaker attribution, retenção e acesso |
| E-mail | Definir caixas pessoais, compartilhadas e pastas excluídas |
| Mensageria | Escolher conector oficial, números, filas e políticas de opt-in |
| Funil de conversas | Definir funis iniciais (atendimento/prospecção/pós-venda), canais no quadro unificado e regras de handoff para oportunidade |
| Redes sociais | Homologar quais redes (LinkedIn, Instagram, Messenger etc.) entram no modelo omnicanal e com qual conector |
| Telefonia | Definir provedor, consentimento, gravação e retenção |
| IA | Escolher modelos, hospedagem, contrato, dados permitidos e avaliação |
| Busca | Escolher motor e estratégia de indexação/segurança |
| Arquivos | Definir storage oficial, antivírus, retenção e integração documental |
| Assinatura | Definir fornecedor e validade jurídica |
| Forecast | Aprovar categorias, ciclos, alçadas e fonte das metas |
| CAC | Aprovar componentes de custo e modelo de atribuição |
| Rentabilidade | Aprovar fonte, fórmula e quem pode visualizar |
| Entrega | Confirmar fontes de embarque, transporte e chegada ao cliente |
| Dados históricos | Definir o que será migrado, desde quando e com qual qualidade |
| Permissões | Aprovar códigos adicionais sem fragmentar o catálogo |
| Retenção | Aprovar tabela por tipo de registro e conteúdo |

---

## 21. Riscos principais e mitigação

| Risco | Impacto | Mitigação |
|---|---|---|
| Tentar entregar todos os módulos simultaneamente | Alto | Roadmap por dependência, contratos e critérios de saída |
| Duplicar ERP no CRM | Alto | Matriz de sistema mestre e leitura via API |
| Regra crítica no MFE | Alto | Bounded context e testes de arquitetura |
| Captura ampla de Teams/e-mail | Muito alto | Menor privilégio, allowlist, consentimento e finalidade |
| Base importada com duplicidades | Alto | Preview, dedupe e stewardship antes da carga |
| Automação enviando conteúdo indevido | Alto | Aprovação, limites, simulação e kill switch |
| IA gerando compromisso incorreto | Muito alto | Fonte, confirmação humana e proibição de envio autônomo |
| Indicadores inconsistentes | Alto | Ficha de indicador, drill, versão e fonte |
| Webhooks perdidos | Médio/alto | Checkpoint, lifecycle, reconciliação e idempotência |
| Custo de canal ou IA sem controle | Médio/alto | Métricas, orçamento, quotas e alertas |
| Crescimento de mensagens/eventos | Alto | Particionamento, retenção, indexação e arquivamento |
| Permissões excessivas | Muito alto | Capability + scope + revisão periódica |
| Dependência de um fornecedor | Médio | Ports/adapters, contratos e exportação de dados |
| Falta de adoção pelos vendedores | Alto | UX orientada a ação, integração automática e implantação gradual |
| CRM virar ferramenta de cobrança de volume | Alto | Indicadores de qualidade e resultado, não apenas atividade |

---

## 22. Rastreabilidade entre ativos atuais e CRM-alvo

| Ativo atual | Reaproveitamento no CRM |
|---|---|
| `CommercialRealtimeProvider` | Realtime de tarefas, pipeline, mensagens, aprovações e integrações |
| `PortfolioScopeContext` | Identidade visual do escopo; regra continua na API |
| `ResolveCommercialCustomerScopeService` | Fonte de verdade para escopo de conta e carteira |
| Worklist e `tasks` | Base de produtividade, cadências e automações |
| `activities` | Base para evolução da timeline |
| `account_contacts` | Base para comitê de compra e consentimento |
| `attachments` | Base documental multientidade |
| `interaction_rooms` | Colaboração contextual e integração interna |
| `integration_outbox` | Publicação de notificações e efeitos externos |
| `integration_checkpoints` | Sincronização de Microsoft 365 e canais |
| WebSocket comercial | Atualização de worklist, salas, pipeline e conectores |
| Conta 360 | Superfície central de relacionamento |
| Open orders BFF | Contexto pós-venda dentro da conta e oportunidade |
| Analytics APIs | Base de gestão à vista e novos KPIs |
| Propostas/PDF | Base documental da negociação |
| OTD | Contexto de cumprimento e risco |
| Customer enrichment | Base de dados operacionais sem clone do ERP |
| Core notifications | Canal corporativo de alertas persistentes |
| RBAC Core | Governança de acesso e capacidades |
| Manifesto `commercial` | Registro de novas rotas e permissões justificadas |
| `@delpi/plugin-ui` | Padrão visual e componentes reutilizáveis |

---

## 23. Itens explicitamente fora do comportamento permitido

O CRM não deve:

- substituir o ERP em estoque, fiscal, faturamento ou contabilidade;
- ler diretamente tabelas internas do Keycloak;
- permitir chamada do MFE à `api-delpi`;
- calcular membership ou autorização no navegador;
- copiar toda conversa de Teams ou toda caixa de e-mail sem finalidade e política;
- guardar gravações por padrão;
- enviar campanhas sem consentimento e suppression;
- realizar merge automático de empresas em caso incerto;
- deixar IA enviar preço, prazo, desconto ou compromisso sem confirmação;
- usar dados de produção para inferir entrega ao cliente sem fonte válida;
- criar “listar tudo” sem paginação;
- expor conteúdo sensível em notificações;
- criar uma permissão por tela ou botão;
- publicar evento antes do commit;
- armazenar anexos em diretório temporário;
- excluir fisicamente histórico relevante de negócio;
- usar mensagem textual como único identificador de erro;
- misturar regra do Portal Comercial com plugin legado;
- apresentar backlog como funcionalidade entregue;
- cronometrar foco pessoal (Pomodoro) ou transformar o CRM em app de bem-estar;
- expor metas pessoais motivacionais (“propósito”) a terceiros sem consentimento do titular.

---

## 24. Fontes consultadas

### 24.1 Código e documentação do Portal Comercial

- `commercial-api/docs/README.md`;
- `commercial-api/commercial_app/**`;
- `commercial-api/migrations/V001__*.sql` até `V021__*.sql`;
- `plugins/commercial/README.md`;
- `plugins/commercial/commercial.manifest.json`;
- `plugins/commercial/src/App.tsx`;
- `plugins/commercial/src/api/**`;
- `plugins/commercial/src/app/**`;
- `plugins/commercial/src/features/**`;
- `docs/12-roadmap-e-evolucao/commercial/README.md`;
- `docs/12-roadmap-e-evolucao/commercial/INVENTARIO-ATIVOS.md`;
- `docs/12-roadmap-e-evolucao/commercial/ATA-MAPA-NECESSIDADES.md`;
- `docs/12-roadmap-e-evolucao/commercial/ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md`;
- `docs/12-roadmap-e-evolucao/commercial/DATA-MODEL.md`;
- `docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md`;
- `docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md`;
- `docs/12-roadmap-e-evolucao/commercial/SCOPE-OWNERSHIP.md`;
- `docs/12-roadmap-e-evolucao/commercial/UX-E-TASKS-EVOLUTION.md`;
- `docs/12-roadmap-e-evolucao/commercial/DESIGN-IA-COMERCIAL.md`;
- `docs/12-roadmap-e-evolucao/commercial/GESTAO-A-VISTA.md`;
- regras aplicáveis em `.cursor/rules/**`.

### 24.2 Documentação geral da Minha DELPI

- `glossario.md`;
- `mapa-da-plataforma.md`;
- `minha-delpi-visao-geral.md`;
- `estrutura-de-repositorio.md`;
- `arquitetura-geral.md`;
- `clean-architecture.md`;
- `fluxo-de-requisicao.md`;
- `event-driven-e-socket.md`;
- `variaveis-de-ambiente.md`;
- `gateway-nginx.md`;
- `bancos-de-dados.md`;
- `ambientes-dev-prod.md`;
- `docker-compose.md`;
- `permission-resolver.md`;
- `rbac.md`;
- `keycloak-sso.md`;
- `jwt.md`;
- `erros-api.md`;
- `modelos-de-banco.md`;
- `unit-of-work.md`;
- `visao-geral-core-api.md`;
- `repositories.md`;
- `notificacoes.md`;
- `controllers-e-rotas.md`;
- `use-cases.md`;
- `migrations.md`;
- documentação do Plugin System e do Portal frontend.

### 24.3 Reuniões e necessidades funcionais

- transcrição `26081909090805592_transcribe_transcript (1).txt`;
- atas e documentos de alinhamento do Portal Comercial;
- demandas de indicadores, confirmação de pedidos, produtividade, OTD, amostras e entregas.

### 24.4 Documentação técnica externa consultada para viabilidade Microsoft 365

- Microsoft Graph — notificações de alterações em mensagens de chats e canais;
- Microsoft Teams Export APIs — mensagens, chats, canais e permissões protegidas;
- Microsoft Graph — acesso a transcrições de reuniões e notificações de disponibilidade;
- Microsoft Graph — notificações de Outlook para mensagens, eventos e contatos;
- Microsoft Graph — disponibilidade livre/ocupado e criação de eventos.

### 24.5 Benchmark de mercado — Agendor CRM

Fontes usadas para preencher gaps de rituais, produtividade e saúde do funil (ago/2026):

- [8 rituais de vendas (+ 5 de gestão)](https://www.agendor.com.br/blog/rituais-de-vendas/);
- [Soluções Agendor](https://www.agendor.com.br/solucoes) — funis, follow-up, mapa de vendas, sumário, WhatsApp, visitas;
- [Funil de vendas / mapa de vendas](https://www.agendor.com.br/beneficios/funil-de-vendas);
- [Gestão de CRM](https://www.agendor.com.br/blog/gestao-crm/) — tarefas por etapa, lembretes, sumário semanal como ritual;
- Central de ajuda Agendor — fluxo inteligente de atividades e sumário semanal.

**Adaptação DELPI:** manter disciplina e rituais no produto; rejeitar vigilância de pausas/Pomodoro; alinhar handoff e forecast aos rituais de gestão sem ranqueamento tóxico.

### 24.6 Benchmark de mercado — funil Kanban de conversas (ChatGuru)

Fonte usada para preencher gaps de quadro de atendimento/vendas por conversa (ago/2026):

- [Como fazer funil de vendas no WhatsApp no estilo do Trello — ChatGuru](https://chatguru.com.br/blog/como-fazer-funil-de-vendas-no-whatsapp-no-estilo-do-trello/)

**Capacidades absorvidas no catálogo (§ 10.40 / CRM-FNL-* e CRM-MSG-017..021):**

- quadro Kanban com etapas como colunas e cartão = chat/conversa;
- múltiplos funis (atendimento, vendas, produção);
- gatilho/diálogo/chatbot para inserir ou mover cartão;
- adição em lote, tags, anotações de equipe e escopo “só meus cartões”;
- tempo/status por etapa e visão operacional do pipeline de atendimento.

**Adaptação DELPI (obrigatória):** o artigo é centrado em WhatsApp; no CRM Minha DELPI o mesmo modelo alimenta-se de **Teams, Outlook/e-mail, WhatsApp corporativo, web chat e redes sociais homologadas**, com conversa normalizada, conector oficial e handoff para lead/oportunidade — sem amarrar o domínio do funil a um único provedor.

---

## 25. Conclusão

O CRM Minha DELPI deverá evoluir o Portal Comercial de um hub operacional e analítico para uma plataforma completa de relacionamento B2B industrial.

A base atual já resolve partes importantes — carteira, Conta 360, pedidos, produção, faturamento, propostas, tarefas, colaboração, realtime e indicadores. O próximo salto não deve descartar essa base. Deve acrescentar, de forma incremental e governada:

```text
prospects e leads
+
marketing e jornada
+
pipeline nativo e mapa de vendas
+
oportunidades e propostas
+
agenda, cadências e rituais de execução
+
histórico omnicanal
+
funil Kanban de conversas (multi-canal)
+
Microsoft 365 e mensageria
+
forecast, sumários e coaching de gestão
+
inteligência artificial supervisionada
```

O resultado esperado é uma única fonte corporativa de contexto comercial, integrada ao ERP e à Minha DELPI, capaz de sustentar prospecção, relacionamento, continuidade, previsibilidade, colaboração e melhoria contínua sem depender de memória individual ou controles paralelos.
