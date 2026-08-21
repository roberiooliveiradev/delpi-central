# CRM Minha DELPI — Visão de Produto e Especificação Funcional Mestra

> **Produto:** Minha DELPI  
> **Módulo:** Portal Comercial / CRM Minha DELPI  
> **Frontend:** `plugins/commercial`  
> **Backend de domínio e BFF:** `commercial-api`  
> **Versão deste documento:** 1.1  
> **Data de referência:** 21 de agosto de 2026  
> **Status:** visão funcional alvo e catálogo mestre de capacidades  
> **Atualização 1.1:** gaps de rituais, mapa de vendas, fluxo inteligente e coaching (benchmark Agendor)  
> **Base analisada:** documentação oficial da Minha DELPI, código e documentação do `commercial-api`, código e documentação do `plugins/commercial`, manifesto vigente do plugin comercial, requisitos levantados com as áreas de negócio e benchmark de CRM B2B (Agendor).

---

## 1. Resumo executivo

O **CRM Minha DELPI** será a plataforma corporativa de marketing, prospecção, vendas, relacionamento, colaboração e inteligência comercial da DELPI, entregue dentro do **Portal Comercial da Minha DELPI**.

A solução deverá acompanhar a jornada completa de uma empresa e de seus contatos, desde a identificação de um prospect até a aquisição, expansão, recompra, atendimento comercial e reativação. O sistema unificará dados próprios do CRM, dados operacionais do ERP, interações de e-mail, mensagens e reuniões, atividades dos vendedores, campanhas, documentos, propostas, pedidos, indicadores e recomendações assistidas por inteligência artificial.

O produto não será apenas um cadastro de oportunidades. Ele deverá funcionar como uma plataforma integrada de execução comercial, capaz de responder, com evidência e histórico, perguntas como:

- quem é a empresa e quem participa da decisão de compra;
- como o relacionamento começou e qual foi a origem da oportunidade;
- quais conteúdos, campanhas, páginas, reuniões e mensagens influenciaram a decisão;
- quais produtos já foram comprados e quais ainda podem ser oferecidos;
- qual vendedor, equipe ou carteira é responsável pela conta;
- qual é o próximo passo comercial, quem deve executá-lo e até quando;
- em qual etapa está cada negociação e há quanto tempo ela permanece ali;
- quais riscos impedem o fechamento, a entrega ou a recompra;
- o que foi discutido por e-mail, Teams, WhatsApp, telefone, reunião ou visita;
- quais compromissos foram assumidos com o cliente;
- quais propostas foram emitidas, aprovadas, recusadas ou substituídas;
- quais pedidos estão abertos, postergados, prontos para faturar ou em risco;
- quanto tempo, esforço e investimento foram necessários para conquistar e desenvolver a conta;
- quais oportunidades têm maior probabilidade de conversão;
- quais clientes estão esfriando, inativos ou com potencial de expansão;
- como estão o pipeline, a previsão de vendas, as metas e a produtividade da equipe.

O CRM será construído sobre a base já existente do Portal Comercial, preservando e evoluindo as funcionalidades atuais de **Conta 360, carteiras, contatos, tarefas, pedidos em aberto, propostas, analytics, administração de equipes, anexos, auditoria e sala de interação em tempo real**.

---

## 2. Definição do produto

### 2.1 O que o CRM Minha DELPI será

O CRM Minha DELPI será:

1. o sistema de relacionamento comercial e pré-venda da DELPI;
2. a fonte oficial de leads, prospects, oportunidades nativas, pipelines, atividades, cadências, campanhas, consentimentos, interações normalizadas e planos de conta;
3. a camada de visão unificada do cliente dentro da Minha DELPI;
4. o orquestrador das integrações comerciais com ERP, Microsoft 365, canais de mensagens, telefonia, site, formulários, serviços de envio, provedores de assinatura e outros sistemas autorizados;
5. uma ferramenta de execução diária para vendedores, orçamentistas, gestores, marketing, faturamento e áreas colaboradoras;
6. uma plataforma de inteligência comercial, com métricas rastreáveis e assistência por IA;
7. um produto modular, auditável, seguro, orientado a eventos e integrado à arquitetura oficial da Minha DELPI.

### 2.2 O que o CRM Minha DELPI não será

O CRM não deverá:

- substituir o ERP como fonte oficial de estoque, preço oficial, pedido, nota fiscal, faturamento, contas a receber ou demais transações fiscais e financeiras;
- substituir a Core API como fonte de verdade de autenticação, autorização, apps, manifestos e permissões da plataforma;
- acessar diretamente o banco interno do Keycloak;
- duplicar regras operacionais do ERP no frontend;
- permitir que o microfrontend chame diretamente a API DELPI ou provedores externos;
- armazenar secrets, refresh tokens ou credenciais de integrações no navegador;
- copiar indiscriminadamente todas as conversas, caixas de e-mail ou reuniões do tenant;
- usar inteligência artificial como fonte de verdade ou executar ações externas sensíveis sem política e confirmação humana;
- criar indicadores sem metodologia, fonte, unidade, data de atualização e regra de cálculo documentadas;
- misturar dados de governança da plataforma com dados de domínio comercial no banco da Core API.

---

## 3. Objetivos estratégicos

### 3.1 Objetivos de negócio

- Centralizar o histórico comercial corporativo, reduzindo dependência da memória individual dos vendedores.
- Estruturar a prospecção e a gestão de carteira com processos mensuráveis.
- Integrar marketing e vendas em uma única jornada de dados.
- Aumentar velocidade de resposta e disciplina de follow-up.
- Melhorar conversão, previsibilidade, recompra, reativação e venda cruzada.
- Permitir continuidade do atendimento em férias, afastamentos ou mudanças de responsável.
- Tornar visível o esforço comercial investido em cada conta e oportunidade.
- Medir origem, influência, ciclo, conversão, custo e retorno das iniciativas comerciais.
- Conectar relacionamento comercial aos dados reais de pedidos, faturamento e entrega.
- Disponibilizar gestão à vista e apoio à decisão sem inventar métricas.

### 3.2 Objetivos de produto

- Entregar uma experiência única dentro do Portal Comercial.
- Manter uma linha do tempo completa e permissionada por conta, contato, lead e oportunidade.
- Oferecer uma área “Meu Dia” que priorize ações, mensagens, tarefas, reuniões, rituais diários e riscos.
- Suportar múltiplos funis, processos e equipes sem hardcode por cargo.
- Embutir disciplina de execução (scripts, briefing, atualização pós-contato, fluxo inteligente) sem vigilância de bem-estar.
- Permitir automações configuráveis e versionadas.
- Integrar canais externos por conectores desacoplados.
- Oferecer APIs e webhooks estáveis para expansão do ecossistema.
- Ser utilizável em desktop e dispositivos móveis.
- Ser auditável, observável, resiliente e compatível com LGPD.

---

## 4. Princípios obrigatórios da Minha DELPI

### 4.1 Separação de responsabilidades

| Componente | Responsabilidade no CRM |
|---|---|
| **Keycloak** | Autenticação SSO e emissão de JWT da Minha DELPI. |
| **Core API** | Usuário local, RBAC, apps, rotas, manifesto, favoritos, notificações de plataforma e autorização do acesso ao plugin. |
| **Portal** | Shell visual, menu dinâmico, contexto autenticado e carregamento do microfrontend. |
| **`plugins/commercial`** | Experiência visual do CRM; não concentra regra de negócio nem acessa provedores diretamente. |
| **`commercial-api`** | Dono do domínio comercial, escopo de clientes, BFF do plugin, casos de uso, integrações e políticas de dados do CRM. |
| **API DELPI** | Contratos de acesso a dados operacionais e integrações corporativas, inclusive ERP. Não é dona das entidades nativas do CRM. |
| **ERP** | Fonte oficial de cadastro transacional, produtos, estoque, preços oficiais, pedidos, notas, faturamento e financeiro. |
| **PostgreSQL de domínios/plugins** | Persistência das entidades do CRM e estados operacionais que não pertencem à Core API. |
| **Gateway Nginx** | Entrada HTTP única, roteamento, headers e políticas de borda. |
| **Barramento de eventos/outbox** | Propagação confiável de eventos após commit. |
| **Socket.IO / canal de tempo real** | Atualização reativa do Portal para eventos autorizados. |
| **AI Gateway da plataforma** | Execução governada dos modelos de IA; o CRM monta contexto e aplica políticas. |

### 4.2 Regras arquiteturais

1. O Portal Comercial deverá chamar somente o `commercial-api` para funcionalidades do CRM.
2. O `commercial-api` deverá aplicar autorização e escopo antes de consultar ou devolver dados.
3. Dados do ERP deverão ser consumidos por contratos HTTP oficiais, nunca por regra duplicada no MFE.
4. Controllers deverão permanecer finos; regras ficarão em casos de uso e serviços de domínio.
5. Repositórios deverão encapsular persistência e serem expostos por Unit of Work.
6. Eventos deverão ser publicados somente após commit confirmado.
7. Toda escrita sensível deverá suportar idempotência e concorrência otimista quando aplicável.
8. Listagens deverão ser paginadas; não haverá “listar tudo” sem limites.
9. Migrations aplicadas serão imutáveis; alterações de schema exigirão nova migration.
10. Novas rotas e permissões do plugin exigirão versionamento e registro de novo manifesto.
11. Mensagens de interface serão em pt-BR; identificadores técnicos e contratos serão em inglês.
12. Integrações externas serão implementadas por portas/adapters, com retry, rate limit, circuit breaker, observabilidade e dead-letter quando necessário.
13. O frontend nunca será a única barreira de segurança.

---

## 5. Situação atual do Portal Comercial

### 5.1 Capacidades já existentes e que deverão ser preservadas

| Área | Capacidade atual | Situação no CRM alvo |
|---|---|---|
| Acesso | Plugin comercial registrado e carregado pela Minha DELPI | Preservar e versionar. |
| Autorização | `commercial.access`, `commercial.manage` e `commercial.billing.notify` | Preservar; adicionar permissões específicas apenas quando houver efeito sensível justificado. |
| Home | Atalhos e visão inicial conforme perfil | Evoluir para “Meu Dia” e home por contexto. |
| Visão geral | Indicadores comerciais e comparativos | Integrar pipeline, campanhas, forecast e produtividade. |
| Conta 360 | Clientes, resumo executivo, oportunidades do ERP, pedidos, faturamento, atividades e contatos | Tornar a tela central do relacionamento completo. |
| Carteiras | Carteiras, membros, cobertura, carga, transferência e auditoria | Evoluir para territórios, regras de distribuição e planos de conta. |
| Contatos | CRUD de contatos locais por conta | Evoluir identidade, papéis, consentimentos, deduplicação e relacionamento. |
| Tarefas | Criação, atribuição, grupos, conclusão, anexos e vínculo com clientes | Evoluir recorrência, checklist, reunião, SLA, dependências e cadências. |
| Pedidos em aberto | Lista, filtros, kanban, detalhes, produção e disponibilidade | Integrar ao processo de relacionamento e confirmação com cliente. |
| Propostas | Consulta de propostas e documentos gerados no ecossistema operacional | Evoluir para ciclo nativo de cotação, versões, aprovação e assinatura. |
| Analytics | Oportunidades do ERP, OTD, equipe, séries e taxas | Incorporar métricas do CRM e atribuição de marketing. |
| Sala de interação | Inbox, threads, menções, não lidas, presença, busca e criação de tarefa a partir de mensagem | Preservar como colaboração interna e conectá-la aos demais objetos do CRM. |
| Anexos | Upload e vínculo a entidades | Evoluir versionamento, classificação, antivírus, preview e retenção. |
| Auditoria | Registros de ações administrativas e operacionais | Ampliar para todas as entidades e acessos sensíveis. |
| Notificações | Integração com o sino da Minha DELPI e jobs de tarefas/faturamento | Evoluir preferências, escalonamentos, digest e canais. |
| Administração | Gestão de equipe, grupos, perfis e carteiras | Evoluir para configuração funcional completa do CRM. |
| Realtime | Eventos, presença e atualização em tempo real | Expandir com outbox e eventos de domínio do CRM. |

### 5.2 Capacidades parcialmente implementadas

| Área | Base disponível | Gap atual |
|---|---|---|
| Oportunidades | Leitura e análise de oportunidades originadas no ERP | Não existe entidade nativa de negócio/oportunidade do CRM com pipeline próprio. |
| Propostas | Documentos e histórico operacional | Não existe editor nativo, versionamento comercial, aprovação, aceite e conversão controlada. |
| Tarefas | Motor local funcional | Faltam recorrência, checklist, dependências, tipo reunião, cadências e regras de SLA mais completas. |
| Contatos | Cadastro local por conta | Faltam papéis na compra, múltiplos canais, consentimentos, merge e identidade multissistema. |
| WhatsApp | Helpers e abertura de links | Não há ingestão, sincronização, histórico corporativo, entrega, áudio, campanha ou caixa compartilhada. |
| Colaboração | Sala interna robusta | A sala não substitui histórico externo de e-mail, Teams, WhatsApp, telefone e reunião. |
| Agenda | Exportação `.ics`/integração pontual | Não há sincronização bidirecional e governada com calendários corporativos. |
| Conta 360 | Visão operacional consolidada | Faltam jornada de marketing, comunicação omnicanal, mapa de influência, plano de conta, saúde e previsão. |
| Indicadores | Base de KPIs comerciais | Faltam CAC, atribuição, ciclo nativo do CRM, geração de pipeline, forecast e eficiência por canal. |

### 5.3 Backlogs formalmente reconhecidos no projeto atual

- Integração real com Microsoft Graph para Outlook, Teams e reuniões.
- Evolução de tarefas recorrentes, checklists e modelo de reunião.
- Fluxo de confirmação de pedidos.
- IA comercial em produção, integrada ao AI Gateway e com confirmação humana.
- Oportunidades, pipeline e forecast nativos no `commercial-api`.
- Segmentação estruturada de clientes.
- SLAs, etapas e follow-up dedicado para ofertas.
- Rastreio de causas de atraso e marcos de entrega.
- Visões gerenciais e de gestão à vista adicionais.

### 5.4 Gaps adicionais necessários para um CRM completo

1. cadastro de leads e prospects antes de existirem no ERP;
2. conversão de lead em empresa, contato e oportunidade sem perder histórico;
3. captação por formulários, landing pages, chat e integrações;
4. higienização, importação, deduplicação e enriquecimento de dados;
5. segmentação dinâmica, scoring e qualificação;
6. campanhas, e-mail marketing e jornadas automatizadas;
7. rastreamento de site, origem, UTM e comportamento digital;
8. múltiplos pipelines e regras de etapa;
9. cadências de prospecção e follow-up;
10. sincronização corporativa de e-mail, calendário, Teams, mensagens e transcrições;
11. caixa omnicanal com WhatsApp, web chat e canais futuros;
12. telefonia, gravação e transcrição condicionadas a consentimento e suporte do provedor;
13. previsão de vendas, metas, quotas e cobertura de pipeline;
14. atribuição, CAC, ROI e receita influenciada;
15. plano de conta, saúde, risco, renovação, expansão e reativação;
16. campos personalizados, layouts, regras de validação e catálogos administráveis;
17. mecanismo visual de automação com versionamento, teste e auditoria;
18. consentimento, preferências e supressão por canal;
19. APIs públicas do domínio, webhooks e central de integrações;
20. busca global permissionada;
21. experiência móvel para visitas e ações rápidas;
22. recursos de produtividade e assistência por IA;
23. observabilidade e operação dos conectores;
24. políticas de retenção, anonimização e atendimento a direitos do titular;
25. modelo explícito para vendas industriais, amostras, viabilidade técnica e homologação;
26. rituais de execução do vendedor (fim de dia, lista, script, briefing pré-contato, atualização pós-abordagem);
27. rituais de gestão (sumário semanal/mensal, forecast em reunião, 1-on-1, role-play, SLA marketing–vendas);
28. mapa de vendas (saúde visual do funil), fluxo inteligente pós-atividade e handoff entre funis;
29. congelamento de negócios e mapa/rota de visitas sem tracking contínuo;
30. scripts/roteiros de vendas e playbooks versionados na mesma experiência da atividade.

---

## 6. Jornada funcional completa

```text
Mercado / empresa-alvo
        ↓
Visitante identificado ou anônimo
        ↓
Lead / contato capturado
        ↓
Enriquecimento, consentimento, segmentação e scoring
        ↓
Qualificação de marketing
        ↓
Distribuição para equipe comercial
        ↓
Prospecção e cadência multicanal
        ↓
Empresa prospect + contatos + mapa de decisão
        ↓
Oportunidade em pipeline
        ↓
Descoberta, viabilidade, amostra, proposta e negociação
        ↓
Ganho / perdido / adiado / desqualificado
        ↓
Cadastro e transação no ERP quando aplicável
        ↓
Pedido, produção, faturamento e entrega
        ↓
Relacionamento, suporte comercial e plano de conta
        ↓
Recompra, expansão, venda cruzada, renovação ou reativação
```

Cada transição deverá registrar data, ator, origem, motivo, evidências e eventos necessários para auditoria e analytics.

---

## 7. Personas e escopos

### 7.1 Personas funcionais

| Persona | Necessidades principais |
|---|---|
| Vendedor de carteira | Conta 360, follow-up, pedidos, oportunidades, mensagens, reuniões, reativação e expansão. |
| Hunter/prospecção | Leads, listas, cadências, scoring, reuniões, conversão e pipeline de novos clientes. |
| Farmer/gestor de conta | Plano de conta, saúde, relacionamento, cross-sell, recompra e risco. |
| Orçamentista | Oportunidades, requisitos, proposta, versão, preço, aprovação e documentos. |
| Marketing | Segmentos, campanhas, formulários, automações, scoring, atribuição e conversão. |
| Gestor comercial | Equipe, pipeline, forecast, metas, performance, riscos, coaching e auditoria. |
| Faturamento | Pedidos prontos, pendências, confirmação e comunicação associada. |
| Engenharia/apoio técnico | Viabilidade, requisitos, amostras, documentos e decisões técnicas. |
| Diretoria | Indicadores executivos, previsão, carteira, receita, conversão, CAC e expansão. |
| Administrador funcional | Pipelines, etapas, campos, templates, regras, integrações e políticas. |
| Auditor/compliance | Trilha completa, acessos sensíveis, consentimentos, exportações e retenção. |

### 7.2 Modelo de acesso

O acesso será composto por:

```text
Permissões da Minha DELPI
+ escopo de carteira/equipe/filial
+ participação no registro
+ sensibilidade do dado
+ consentimento/autorização do conector externo
+ política específica da ação
```

Regras:

- `commercial.access` continuará sendo a porta de entrada do produto.
- `commercial.manage` continuará concedendo administração e visão ampliada conforme política.
- `commercial.billing.notify` continuará restrita ao efeito de faturamento.
- A maior parte das funcionalidades diárias deverá reutilizar `commercial.access` e escopo de registros, evitando fragmentação sem justificativa.
- Novas permissões específicas serão admitidas para ações externas ou de alto risco, por exemplo envio massivo, administração de integrações, leitura de conteúdo corporativo em escopo ampliado, exclusão/anomização e aprovação financeira sensível.
- O backend deverá revalidar toda ação.
- Conteúdo sincronizado de Microsoft 365 ou de outros canais não poderá ser exibido a um usuário apenas porque ele vê a conta; o sistema deverá respeitar também a política de acesso ao conteúdo e o modo de consentimento usado na captura.

---

## 8. Catálogo mestre de funcionalidades

### Legenda de situação

| Situação | Significado |
|---|---|
| **Existe** | Há base funcional entregue no código atual e ela deverá ser preservada. |
| **Parcial** | Há parte da capacidade, mas faltam componentes essenciais. |
| **Backlog formal** | A própria documentação comercial atual já reconhece a necessidade. |
| **Novo** | Capacidade necessária para completar o CRM alvo. |


### 8.1 Acesso, identidade e perfil comercial

**Situação atual:** Existe, com evolução necessária.

**Objetivo:** permitir acesso único, seguro e contextual ao CRM, sem duplicar autenticação ou autorização da plataforma.

#### Funcionalidades obrigatórias

- **CRM-IAM-001 — SSO:** utilizar a sessão Keycloak da Minha DELPI sem segundo login.
- **CRM-IAM-002 — Contexto do usuário:** carregar identidade, permissões efetivas, grupos, escopos, carteiras e preferências.
- **CRM-IAM-003 — Perfil comercial:** manter cargo funcional, telefone, assinatura, filial, idioma, fuso, agenda e canais conectados.
- **CRM-IAM-004 — Mapeamento de identidades externas:** associar o usuário da Minha DELPI a identidades autorizadas de Microsoft 365, telefonia e mensageria.
- **CRM-IAM-005 — Escopo de dados:** aplicar `own`, `portfolio`, `team`, `branch` e `all` sem permitir ampliação por parâmetros enviados pelo cliente.
- **CRM-IAM-006 — Participação em registro:** permitir acesso adicional quando o usuário for responsável, participante, aprovador, observador ou mencionado.
- **CRM-IAM-007 — Separação de funções:** impedir que uma mesma pessoa aprove operações sensíveis que ela própria criou quando a política exigir dupla validação.
- **CRM-IAM-008 — Acesso temporário:** permitir delegação com prazo, motivo e auditoria para férias, afastamentos ou cobertura.
- **CRM-IAM-009 — Preferências:** armazenar home, filtros, notificações, assinatura, horários, canais e opções de acessibilidade.
- **CRM-IAM-010 — Sessão segura:** tratar expiração, refresh, logout global e desconexão de canais em tempo real.
- **CRM-IAM-011 — Auditoria de conteúdo sensível:** registrar visualização, exportação e download de mensagens, transcrições, dados financeiros e documentos classificados.
- **CRM-IAM-012 — Revogação imediata:** refletir alterações de RBAC e escopo em `/me`, menus, rotas, buscas, caches e conexões em tempo real.

#### Regras críticas

- Cargo ou persona não será usado como permission code.
- O MFE poderá ocultar ações por UX, mas a decisão final será sempre do backend.
- A conta Microsoft conectada não ampliará automaticamente o escopo comercial do usuário.
- Tokens de conectores ficarão cifrados no backend ou em cofre de secrets.

---

### 8.2 Home personalizada e “Meu Dia”

**Situação atual:** Parcial; já existem Home, tarefas, atalhos e indicadores.

**Objetivo:** concentrar tudo que exige atenção imediata do usuário.

#### Funcionalidades obrigatórias

- **CRM-HOME-001 — Agenda diária:** tarefas, reuniões, visitas, retornos e prazos em ordem cronológica.
- **CRM-HOME-002 — Prioridades:** itens atrasados, SLA em risco, leads quentes, oportunidades sem próxima ação e pedidos críticos.
- **CRM-HOME-003 — Inbox unificada:** novas mensagens, e-mails vinculados, menções, respostas e solicitações pendentes.
- **CRM-HOME-004 — Pipeline pessoal:** resumo de negócios por etapa, valor, probabilidade e data prevista.
- **CRM-HOME-005 — Carteira em atenção:** clientes sem contato, queda de compra, atraso, risco, oportunidade de cross-sell e necessidade de reativação.
- **CRM-HOME-006 — Campanhas e leads:** leads recém-atribuídos, respostas, conversões e pendências de qualificação.
- **CRM-HOME-007 — Pedidos e faturamento:** itens disponíveis, postergados, prontos para faturar e com exceções.
- **CRM-HOME-008 — Próxima melhor ação:** recomendações explicáveis, sempre acompanhadas da evidência utilizada.
- **CRM-HOME-009 — Atalhos por contexto:** vendedor, gestor, marketing, orçamentista e faturamento sem hardcode de autorização.
- **CRM-HOME-010 — Widgets configuráveis:** reordenar, ocultar e salvar preferências dentro dos limites do perfil.
- **CRM-HOME-011 — Digest:** resumo diário ou semanal por canal escolhido.
- **CRM-HOME-012 — Continuidade:** seção “recentemente acessados” e rascunhos em andamento.
- **CRM-HOME-013 — Ritual fim de dia:** revisar amanhã, gaps sem próximo passo e atrasos em fluxo guiado curto.
- **CRM-HOME-014 — Lista do dia:** checks visuais, progresso e fechamento do dia.
- **CRM-HOME-015 — Sumário de vendas:** atalho para o sumário semanal/mensal do usuário ou da equipe autorizada.

#### Regras críticas

- A home não deverá somar indicadores incompatíveis.
- Todo card deverá declarar fonte, atualização e escopo.
- Recomendações não poderão executar automaticamente envio, fechamento ou alteração financeira.
- Rituais não poderão cronometrar foco pessoal nem expor metas motivacionais privadas a terceiros.

---

### 8.3 Empresas, prospects e Conta 360

**Situação atual:** Existe para clientes do ERP; deve evoluir para prospects e relacionamento completo.

**Objetivo:** oferecer uma ficha única para qualquer empresa, antes e depois de ela existir no ERP.

#### Funcionalidades obrigatórias

- **CRM-ACC-001 — Empresa prospect:** criar empresa ainda sem código de cliente no ERP.
- **CRM-ACC-002 — Empresa cliente:** vincular códigos, lojas, filiais e referências externas sem perder histórico anterior.
- **CRM-ACC-003 — Identidade canônica:** usar ID interno estável e referências externas versionadas.
- **CRM-ACC-004 — Dados cadastrais:** nome, razão social, nome fantasia, domínio, CNPJ/identificador, endereços, telefones, segmento, porte e região.
- **CRM-ACC-005 — Hierarquia empresarial:** matriz, filiais, grupo econômico e relacionamentos entre empresas.
- **CRM-ACC-006 — Responsabilidade comercial:** carteira, equipe, proprietário principal, cobertura e substitutos.
- **CRM-ACC-007 — Classificação:** prospect, cliente, ex-cliente, parceiro, concorrente e outras categorias administráveis.
- **CRM-ACC-008 — Ciclo de vida:** novo, em prospecção, ativo, em risco, inativo, reativado e encerrado, com regras documentadas.
- **CRM-ACC-009 — Segmentos e tags:** associação manual e dinâmica.
- **CRM-ACC-010 — Linha do tempo:** campanhas, páginas, formulários, tarefas, reuniões, mensagens, ligações, propostas, negócios, pedidos, notas e eventos relevantes.
- **CRM-ACC-011 — Resumo executivo:** situação atual, valor aberto, faturamento, pipeline, riscos, próximos passos e última interação.
- **CRM-ACC-012 — Histórico de compras:** produtos, famílias, frequência, ticket e evolução oriundos do ERP.
- **CRM-ACC-013 — Espaço de oportunidade:** produtos já comprados versus portfólio aplicável ainda não comprado.
- **CRM-ACC-014 — Pedidos em aberto:** manter a capacidade atual, com status, produção, disponibilidade, entrega e exceções.
- **CRM-ACC-015 — Faturamento e notas:** manter visão operacional e acesso controlado aos documentos.
- **CRM-ACC-016 — Pipeline da conta:** oportunidades abertas, ganhas, perdidas, adiadas e desqualificadas.
- **CRM-ACC-017 — Relacionamento:** contatos-chave, mapa de influência, força do relacionamento e cobertura.
- **CRM-ACC-018 — Plano de conta:** objetivos, iniciativas, riscos, concorrentes, oportunidades de expansão e plano de ação.
- **CRM-ACC-019 — Saúde da conta:** score explicável baseado em relacionamento, compras, pendências, satisfação e risco.
- **CRM-ACC-020 — Pré-reunião:** briefing automático com histórico, pedidos, oportunidades, contatos, pendências e perguntas sugeridas.
- **CRM-ACC-021 — Documentos:** contratos, apresentações, desenhos, especificações, anexos e links classificados.
- **CRM-ACC-022 — Notas internas:** comentários permissionados, com menções e histórico de edição.
- **CRM-ACC-023 — Merge:** unificar empresas duplicadas mantendo referências, auditoria e rollback administrativo.
- **CRM-ACC-024 — Restrição de dado:** mascarar ou omitir valores sensíveis conforme política.
- **CRM-ACC-025 — Exportação:** exportar visão autorizada em formatos estruturados e relatório executivo.

#### Regras críticas

- Prospect poderá existir sem cadastro no ERP.
- A conversão em cliente não criará uma segunda empresa; apenas adicionará referência externa e estado transacional.
- Dados financeiros e fiscais continuarão tendo o ERP como fonte oficial.
- Classificações comerciais derivadas deverão ter metodologia e data de cálculo.

---

### 8.4 Contatos e mapa de relacionamento

**Situação atual:** Parcial; já existe CRUD de contatos locais.

**Objetivo:** representar pessoas, papéis, preferências e influência ao longo do ciclo comercial.

#### Funcionalidades obrigatórias

- **CRM-CON-001 — Cadastro completo:** nome, cargo, área, empresa, e-mails, telefones, idioma, fuso e endereço.
- **CRM-CON-002 — Múltiplas empresas:** permitir vínculo histórico ou simultâneo com mais de uma organização.
- **CRM-CON-003 — Papéis na compra:** decisor, comprador, usuário, influenciador técnico, financeiro, qualidade, patrocinador e bloqueador.
- **CRM-CON-004 — Papel por oportunidade:** um contato poderá exercer papéis diferentes em negócios distintos.
- **CRM-CON-005 — Preferências de comunicação:** canal, horário, idioma e restrições.
- **CRM-CON-006 — Consentimento:** base legal, origem, data, prova, finalidade, canal e revogação.
- **CRM-CON-007 — Supressão:** impedir comunicações incompatíveis com opt-out, bounce, reclamação ou política.
- **CRM-CON-008 — Identidade externa:** mapear e-mail, telefone, ID de mensageria, ID Microsoft e outras referências.
- **CRM-CON-009 — Deduplicação:** detectar possíveis duplicados por e-mail, telefone, domínio e similaridade.
- **CRM-CON-010 — Merge:** mesclar contatos preservando consentimentos, atividades e referências.
- **CRM-CON-011 — Relacionamento interno:** responsável DELPI, última interação, próxima ação e nível de relacionamento.
- **CRM-CON-012 — Organograma:** visualizar estrutura de decisão e relações entre contatos.
- **CRM-CON-013 — Mudança de empresa:** preservar histórico e criar novo vínculo sem apagar o anterior.
- **CRM-CON-014 — Inatividade:** identificar contatos inválidos, desligados ou sem interação.
- **CRM-CON-015 — Captura assistida:** criar contato a partir de e-mail, mensagem, cartão digital, formulário ou reunião com confirmação humana.
- **CRM-CON-016 — Dados mínimos:** permitir captura rápida e enriquecimento progressivo.
- **CRM-CON-017 — Portabilidade e exclusão:** atender solicitações conforme política legal, sem destruir trilhas obrigatórias.

---

### 8.5 Qualidade, importação e enriquecimento de dados

**Situação atual:** Novo.

**Objetivo:** garantir base confiável e permitir migração controlada de listas históricas.

#### Funcionalidades obrigatórias

- **CRM-DQ-001 — Importação CSV/XLSX:** upload, preview, mapeamento de colunas e validação antes de gravar.
- **CRM-DQ-002 — Dry run:** mostrar quantos registros serão criados, atualizados, ignorados ou rejeitados.
- **CRM-DQ-003 — Idempotência:** repetir um arquivo sem gerar duplicidades.
- **CRM-DQ-004 — Relatório de erros:** devolver linha, coluna, motivo e sugestão de correção.
- **CRM-DQ-005 — Reversão administrativa:** desfazer lote quando tecnicamente seguro.
- **CRM-DQ-006 — Deduplicação em lote:** agrupar candidatos e exigir revisão quando houver ambiguidade.
- **CRM-DQ-007 — Normalização:** e-mail, telefone, CNPJ, domínio, endereço, nomes e códigos.
- **CRM-DQ-008 — Enriquecimento:** consultar fontes autorizadas e registrar origem/freshness.
- **CRM-DQ-009 — Completude:** dashboard de campos ausentes, inválidos ou desatualizados.
- **CRM-DQ-010 — Conflito de fontes:** política de precedência e aprovação para substituir dados.
- **CRM-DQ-011 — Atualização em massa:** alterar proprietário, segmento, tag, status ou campo permitido com preview.
- **CRM-DQ-012 — Regras de validação:** configuração por entidade, etapa e contexto.
- **CRM-DQ-013 — Governança de exportação:** autorização, finalidade, limite e marca d'água/log quando aplicável.
- **CRM-DQ-014 — Histórico:** registrar valor anterior, valor novo, fonte, lote e ator.
- **CRM-DQ-015 — Base de supressão:** importar e manter bloqueios de comunicação.

---

### 8.6 Leads e prospecção

**Situação atual:** Novo; não existe entidade nativa de lead no domínio atual.

**Objetivo:** controlar pessoas e empresas que ainda precisam ser qualificadas.

#### Funcionalidades obrigatórias

- **CRM-LEAD-001 — Cadastro de lead:** pessoa, empresa, origem, interesse, proprietário, status e consentimento.
- **CRM-LEAD-002 — Lead sem empresa conhecida:** permitir captura inicial mínima.
- **CRM-LEAD-003 — Lead de empresa conhecida:** relacionar a conta sem criar contato definitivo até qualificação.
- **CRM-LEAD-004 — Origens:** formulário, importação, indicação, evento, campanha, site, chat, ligação, mensagem, lista e criação manual.
- **CRM-LEAD-005 — UTM e atribuição inicial:** registrar source, medium, campaign, content e term.
- **CRM-LEAD-006 — Caixa de novos leads:** triagem com filtros, SLA, score e duplicidade.
- **CRM-LEAD-007 — Qualificação:** critérios de perfil, necessidade, autoridade, orçamento, prazo e aderência técnica configuráveis.
- **CRM-LEAD-008 — Estados:** novo, em contato, qualificado, desqualificado, convertido, reciclado e descartado.
- **CRM-LEAD-009 — Motivos:** lista administrável para desqualificação, reciclagem e descarte.
- **CRM-LEAD-010 — Distribuição:** regras por região, segmento, produto, carga, disponibilidade, carteira e round-robin.
- **CRM-LEAD-011 — Aceite do vendedor:** confirmar recebimento ou devolver com motivo dentro de prazo.
- **CRM-LEAD-012 — SLA de primeira resposta:** medir criação até primeira interação válida.
- **CRM-LEAD-013 — Conversão:** gerar/reutilizar empresa, contato e oportunidade em transação única.
- **CRM-LEAD-014 — Preservação de histórico:** campanha, score, consentimento, atividades e mensagens acompanham a conversão.
- **CRM-LEAD-015 — Reciclagem:** retornar lead para nutrição ou fila futura sem perder dados.
- **CRM-LEAD-016 — Listas de prospecção:** montar listas salvas, priorizadas e permissionadas.
- **CRM-LEAD-017 — Enriquecimento assistido:** sugerir empresa, domínio, cargo e contatos relacionados.
- **CRM-LEAD-018 — Duplicidade:** alertar se pessoa/empresa já existe como contato, lead ou cliente.
- **CRM-LEAD-019 — Conversão em massa:** apenas para processos aprovados e auditados.
- **CRM-LEAD-020 — Métricas:** volume, velocidade, origem, qualificação, conversão, rejeição e aging.

---

### 8.7 Scoring, qualificação e priorização

**Situação atual:** Novo.

**Objetivo:** priorizar leads e contas com base em aderência e comportamento, de forma explicável.

#### Funcionalidades obrigatórias

- **CRM-SCORE-001 — Score de perfil:** setor, porte, região, cargo, aplicação, potencial e aderência.
- **CRM-SCORE-002 — Score de engajamento:** visitas, conteúdos, formulários, respostas, reuniões e recência.
- **CRM-SCORE-003 — Score negativo:** opt-out, dados inválidos, inatividade, baixa aderência e rejeições.
- **CRM-SCORE-004 — Decaimento temporal:** reduzir peso de ações antigas.
- **CRM-SCORE-005 — Regras configuráveis:** pontos, limites, público e vigência.
- **CRM-SCORE-006 — Histórico do score:** explicar cada alteração e sua origem.
- **CRM-SCORE-007 — Faixas:** frio, morno, quente ou classificação equivalente administrável.
- **CRM-SCORE-008 — Gatilhos:** notificar, distribuir, criar tarefa, entrar em automação ou qualificar.
- **CRM-SCORE-009 — Override manual:** permitir ajuste com justificativa e expiração opcional.
- **CRM-SCORE-010 — Modelo preditivo:** admitir IA após haver base suficiente, mantendo explicabilidade e validação.
- **CRM-SCORE-011 — Avaliação:** acompanhar precisão, conversão por faixa e degradação do modelo.
- **CRM-SCORE-012 — Anti-abuso:** limitar eventos repetitivos e excluir tráfego interno/bots.

---

### 8.8 Segmentação e listas

**Situação atual:** Backlog formal para segmentação estruturada.

**Objetivo:** criar públicos reutilizáveis para marketing, vendas, carteira e analytics.

#### Funcionalidades obrigatórias

- **CRM-SEG-001 — Segmento estático:** membros escolhidos ou importados.
- **CRM-SEG-002 — Segmento dinâmico:** regras avaliadas continuamente.
- **CRM-SEG-003 — Construtor de filtros:** atributos, comportamento, compras, campanhas, pipeline, score e consentimento.
- **CRM-SEG-004 — Operadores:** AND, OR, grupos, inclusão, exclusão, datas relativas e agregações.
- **CRM-SEG-005 — Preview:** tamanho, amostra e motivo de inclusão.
- **CRM-SEG-006 — Snapshot:** congelar audiência no momento de um envio quando necessário.
- **CRM-SEG-007 — Exclusões:** listas de supressão, clientes bloqueados, contatos inválidos e frequência.
- **CRM-SEG-008 — Versionamento:** registrar alterações de regra e impacto.
- **CRM-SEG-009 — Compartilhamento:** privado, equipe ou corporativo.
- **CRM-SEG-010 — Uso:** campanhas, cadências, relatórios, distribuição e automações.
- **CRM-SEG-011 — Segmentos industriais:** produto, família, aplicação, histórico, potencial, inatividade e período sem compra.
- **CRM-SEG-012 — Desempenho:** medir conversão e receita por segmento.

---

### 8.9 Campanhas de marketing

**Situação atual:** Novo.

**Objetivo:** planejar, executar e medir ações de aquisição, relacionamento e reativação.

#### Funcionalidades obrigatórias

- **CRM-CAMP-001 — Cadastro:** nome, objetivo, período, responsável, orçamento, canal, audiência e status.
- **CRM-CAMP-002 — Tipos:** aquisição, lançamento, conteúdo, evento, reativação, cross-sell, relacionamento e pesquisa.
- **CRM-CAMP-003 — Audiência:** segmento dinâmico ou snapshot, com supressões.
- **CRM-CAMP-004 — Canais:** e-mail, WhatsApp autorizado, web, evento, mídia paga, ligação, visita e canais futuros.
- **CRM-CAMP-005 — Jornada multicanal:** combinar canais em sequência governada.
- **CRM-CAMP-006 — Conteúdo:** templates, assets, páginas, formulários, links e variantes.
- **CRM-CAMP-007 — Agenda:** rascunho, revisão, aprovação, programação, execução, pausa e encerramento.
- **CRM-CAMP-008 — Controle de orçamento:** planejado, comprometido e realizado por fonte integrada.
- **CRM-CAMP-009 — Membros:** status por lead/contato, respostas, conversões e receita influenciada.
- **CRM-CAMP-010 — Frequência:** limite por contato, canal e período.
- **CRM-CAMP-011 — Teste A/B:** assunto, conteúdo, audiência, horário e destino.
- **CRM-CAMP-012 — Aprovação:** revisão de conteúdo e público antes de envios massivos.
- **CRM-CAMP-013 — UTM:** geração e padronização de parâmetros.
- **CRM-CAMP-014 — Métricas:** entrega, abertura quando aplicável, clique, resposta, conversão, pipeline, receita, custo e ROI.
- **CRM-CAMP-015 — Atribuição:** first touch, last touch e modelos configuráveis.
- **CRM-CAMP-016 — Histórico imutável:** preservar o conteúdo efetivamente enviado e a audiência usada.
- **CRM-CAMP-017 — Clonagem:** reutilizar campanha sem copiar estados de execução.
- **CRM-CAMP-018 — Compliance:** validar consentimento, opt-out, base legal e restrições de canal.

---

### 8.10 E-mail marketing e comunicação individual

**Situação atual:** Novo para envio e tracking; integração Outlook é backlog formal.

**Objetivo:** suportar campanhas e comunicação individual sem confundir caixa corporativa com envio massivo.

#### Funcionalidades obrigatórias

- **CRM-EMAIL-001 — Editor de template:** blocos responsivos, identidade visual, preview e conteúdo reutilizável.
- **CRM-EMAIL-002 — Personalização:** campos permitidos, fallback e validação de variável.
- **CRM-EMAIL-003 — Teste de envio:** destinatário de teste, preview desktop/mobile e verificação de links.
- **CRM-EMAIL-004 — Programação:** data, hora, fuso e janela de silêncio.
- **CRM-EMAIL-005 — Domínio:** configuração e validação de SPF, DKIM e DMARC no provedor de envio.
- **CRM-EMAIL-006 — Entregabilidade:** delivered, bounce, blocked, complaint e suppression.
- **CRM-EMAIL-007 — Descadastro:** link e central de preferências obrigatórios em comunicação de marketing.
- **CRM-EMAIL-008 — Tracking governado:** abertura e clique apenas conforme política, transparência e legislação.
- **CRM-EMAIL-009 — Resposta:** relacionar respostas à campanha, contato, conta e responsável.
- **CRM-EMAIL-010 — Comunicação individual:** redigir e enviar e-mail a partir da conta, contato ou oportunidade usando identidade corporativa conectada.
- **CRM-EMAIL-011 — Templates comerciais:** abordagem, follow-up, proposta, confirmação, cobrança de retorno e reativação.
- **CRM-EMAIL-012 — Thread:** agrupar mensagens por conversa e preservar referências externas.
- **CRM-EMAIL-013 — Associação automática:** sugerir conta/oportunidade pelo domínio e participantes; exigir confirmação em casos ambíguos.
- **CRM-EMAIL-014 — Anexos:** registrar metadados, verificar malware e aplicar limite/classificação.
- **CRM-EMAIL-015 — Rascunho assistido:** IA poderá sugerir texto, mas o usuário deverá revisar antes do envio.
- **CRM-EMAIL-016 — Separação de tráfego:** provedor/canal de marketing e caixa individual terão políticas, reputação e métricas distintas.
- **CRM-EMAIL-017 — Auditoria:** registrar envio, destinatários, template, versão e ator.
- **CRM-EMAIL-018 — Restrições:** impedir envio para contato sem base legal, suprimido ou fora do escopo permitido.

---

### 8.11 Landing pages, formulários, pop-ups e chat web

**Situação atual:** Novo.

**Objetivo:** capturar demanda digital e alimentar automaticamente o CRM.

#### Funcionalidades obrigatórias

- **CRM-WEB-001 — Construtor de landing page:** componentes responsivos e identidade visual aprovada.
- **CRM-WEB-002 — Formulários:** campos padrão e personalizados, validação, máscara e lógica condicional.
- **CRM-WEB-003 — Progressive profiling:** pedir informações adicionais ao longo da jornada sem repetir campos conhecidos.
- **CRM-WEB-004 — Campos ocultos:** origem, UTM, página, campanha e referrer.
- **CRM-WEB-005 — Consentimento:** checkbox, texto, finalidade, versão e prova.
- **CRM-WEB-006 — Anti-spam:** CAPTCHA, honeypot, rate limit e reputação.
- **CRM-WEB-007 — Double opt-in:** opção configurável por finalidade/canal.
- **CRM-WEB-008 — Upload:** anexos seguros para solicitações autorizadas.
- **CRM-WEB-009 — Embed:** formulário incorporável em sites autorizados.
- **CRM-WEB-010 — Conversão:** criar/atualizar lead, contato, campanha e evento de origem.
- **CRM-WEB-011 — Roteamento:** distribuir conforme regra e SLA.
- **CRM-WEB-012 — Página de agradecimento:** redirecionamento, conteúdo e próximo passo.
- **CRM-WEB-013 — Pop-ups/banners:** gatilho por página, tempo, comportamento e frequência.
- **CRM-WEB-014 — Chat web:** captura, qualificação, respostas básicas, transferência humana e criação de lead/caso.
- **CRM-WEB-015 — Agenda:** permitir agendar reunião em horários disponíveis quando autorizado.
- **CRM-WEB-016 — Métricas:** visitas, conversões, abandono, origem e qualidade.
- **CRM-WEB-017 — Publicação:** rascunho, revisão, domínio, versionamento e rollback.
- **CRM-WEB-018 — Acessibilidade e performance:** páginas leves, teclado, contraste e semântica.

---

### 8.12 Rastreamento de site e comportamento digital

**Situação atual:** Novo.

**Objetivo:** registrar sinais de interesse sem violar consentimento e privacidade.

#### Funcionalidades obrigatórias

- **CRM-TRACK-001 — Script de tracking:** instalação em domínios autorizados e versionamento.
- **CRM-TRACK-002 — Sessão anônima:** registrar eventos mínimos até identificação, conforme consentimento.
- **CRM-TRACK-003 — Identificação:** associar sessão após formulário, link autenticado ou ação consentida.
- **CRM-TRACK-004 — Eventos:** page view, clique, download, busca, vídeo, formulário e eventos customizados aprovados.
- **CRM-TRACK-005 — Catálogo de páginas:** produto, família, conteúdo, campanha e etapa da jornada.
- **CRM-TRACK-006 — Recência e frequência:** indicadores de engajamento.
- **CRM-TRACK-007 — Merge de identidade:** unificar eventos anônimos e conhecidos de forma auditável.
- **CRM-TRACK-008 — Exclusão de tráfego interno:** IPs, usuários e ambientes de teste.
- **CRM-TRACK-009 — Retenção:** agregação ou anonimização após o prazo definido.
- **CRM-TRACK-010 — Gatilhos:** scoring, segmento, automação, alerta e recomendação.
- **CRM-TRACK-011 — Integração de analytics:** importar métricas agregadas de tráfego e campanha quando necessário.
- **CRM-TRACK-012 — Transparência:** respeitar banner de cookies e preferências.
- **CRM-TRACK-013 — Segurança:** bloquear payloads arbitrários e dados sensíveis em parâmetros.
- **CRM-TRACK-014 — Diagnóstico:** painel de saúde do script e eventos rejeitados.

---

### 8.13 Automação de marketing e jornadas

**Situação atual:** Novo.

**Objetivo:** nutrir, qualificar e encaminhar leads com processos controlados.

#### Funcionalidades obrigatórias

- **CRM-JOURNEY-001 — Construtor visual:** gatilhos, condições, ações, esperas e ramificações.
- **CRM-JOURNEY-002 — Gatilhos:** formulário, segmento, score, campanha, página, data, compra, inatividade, resposta e evento de integração.
- **CRM-JOURNEY-003 — Condições:** perfil, consentimento, comportamento, pipeline, produto, carteira e histórico.
- **CRM-JOURNEY-004 — Ações:** enviar comunicação, criar tarefa, atribuir, taguear, alterar status, notificar, criar oportunidade e chamar webhook aprovado.
- **CRM-JOURNEY-005 — Esperas:** duração, data, janela de negócio e evento futuro.
- **CRM-JOURNEY-006 — Saída:** conversão, opt-out, mudança de segmento, limite de tentativas ou condição de parada.
- **CRM-JOURNEY-007 — Versões:** rascunho, validação, publicação, pausa e histórico imutável.
- **CRM-JOURNEY-008 — Simulação:** testar com registros fictícios e visualizar caminho.
- **CRM-JOURNEY-009 — Inscrição:** manual, automática, única, recorrente ou restrita por período.
- **CRM-JOURNEY-010 — Proteção contra loop:** limite de ações, reentrada e recursão.
- **CRM-JOURNEY-011 — Retry:** política para falhas transitórias sem duplicar ações.
- **CRM-JOURNEY-012 — Aprovação humana:** etapa obrigatória antes de ação sensível.
- **CRM-JOURNEY-013 — Métricas:** inscritos, ativos, concluídos, convertidos, erros e tempo por etapa.
- **CRM-JOURNEY-014 — Auditoria:** registrar versão, caminho, decisões e ações executadas.
- **CRM-JOURNEY-015 — Frequência:** respeitar limite global e por canal.
- **CRM-JOURNEY-016 — Prioridade:** resolver conflito quando várias automações tentarem atuar no mesmo registro.

---

### 8.14 Distribuição, filas e SLAs

**Situação atual:** Parcial em carteiras e grupos; novo para leads e oportunidades.

**Objetivo:** garantir que demanda comercial tenha responsável, prazo e escalonamento.

#### Funcionalidades obrigatórias

- **CRM-ROUTE-001 — Regras de distribuição:** região, segmento, produto, filial, origem, carteira, score e capacidade.
- **CRM-ROUTE-002 — Round-robin:** balancear com pesos, ausências e limites.
- **CRM-ROUTE-003 — Fila manual:** permitir triagem por equipe autorizada.
- **CRM-ROUTE-004 — Aceite:** responsável confirma ou devolve com motivo.
- **CRM-ROUTE-005 — SLA de primeira ação:** tempo entre entrada e contato válido.
- **CRM-ROUTE-006 — SLA por etapa:** prazo máximo configurado por pipeline e processo.
- **CRM-ROUTE-007 — Aging:** exibir tempo total e tempo na etapa atual.
- **CRM-ROUTE-008 — Escalonamento:** notificar responsável, gestor e fila alternativa.
- **CRM-ROUTE-009 — Reatribuição automática:** afastamento, ausência, fila parada ou mudança de carteira.
- **CRM-ROUTE-010 — Calendário de negócio:** feriados, expediente, filial e fuso.
- **CRM-ROUTE-011 — Motivo de quebra:** registrar justificativa e impacto.
- **CRM-ROUTE-012 — Dashboard:** filas, tempos, violações, taxa de aceite e capacidade.
- **CRM-ROUTE-013 — Auditoria:** toda mudança de dono terá origem, ator e motivo.

---

### 8.15 Pipelines, etapas e oportunidades nativas

**Situação atual:** Backlog formal; as oportunidades atuais são principalmente analíticas e oriundas do ERP.

**Objetivo:** controlar negócios desde a descoberta até o fechamento, independentemente da existência de uma transação no ERP.

#### Funcionalidades obrigatórias

- **CRM-PIPE-001 — Múltiplos pipelines:** novos clientes, carteira, reativação, projetos, amostras, propostas e processos configuráveis.
- **CRM-PIPE-002 — Etapas:** nome, ordem, probabilidade, SLA, obrigatoriedades, cor e tipo semântico.
- **CRM-PIPE-003 — Regras de transição:** impedir avanço sem dados, atividade ou aprovação exigida.
- **CRM-PIPE-004 — Kanban:** mover por drag-and-drop com validação backend e concorrência.
- **CRM-PIPE-005 — Visão lista:** filtros, ordenação, colunas, agrupamento e exportação.
- **CRM-PIPE-006 — Oportunidade:** nome, conta, contatos, responsável, pipeline, etapa, origem, valor, moeda, probabilidade e data prevista.
- **CRM-PIPE-007 — Próxima ação:** toda oportunidade aberta deverá possuir próximo passo ou justificativa.
- **CRM-PIPE-008 — Produtos:** itens, família, quantidade, preço estimado, frequência, volume e aplicação.
- **CRM-PIPE-009 — Equipe do negócio:** proprietário, co-responsáveis, especialistas, aprovadores e observadores.
- **CRM-PIPE-010 — Contatos e papéis:** decisores, influenciadores, comprador e demais participantes.
- **CRM-PIPE-011 — Concorrentes:** empresa, solução, força, fraqueza e motivo de comparação.
- **CRM-PIPE-012 — Critérios de qualificação:** checklist configurável e score da oportunidade.
- **CRM-PIPE-013 — Histórico de etapa:** data de entrada/saída, duração, ator e motivo.
- **CRM-PIPE-014 — Estados finais:** ganho, perdido, desqualificado, adiado e cancelado.
- **CRM-PIPE-015 — Motivos de perda:** catálogo obrigatório, observação e concorrente quando aplicável.
- **CRM-PIPE-016 — Motivos de adiamento:** data de retorno e automação de reabertura.
- **CRM-PIPE-017 — Split/participação:** participação de vendedores/equipes para atribuição e meta.
- **CRM-PIPE-018 — Probabilidade:** manual, padrão por etapa ou preditiva, sempre identificando a fonte.
- **CRM-PIPE-019 — Valor:** recorrente, total, anualizado, ponderado e em moeda base.
- **CRM-PIPE-020 — Timeline:** todas as atividades, mensagens, documentos, mudanças e decisões.
- **CRM-PIPE-021 — Duplicidade:** detectar oportunidades semelhantes na mesma conta.
- **CRM-PIPE-022 — Clonagem:** reutilizar estrutura sem copiar histórico indevido.
- **CRM-PIPE-023 — Conversão em pedido:** enviar comando/contrato ao sistema transacional, sem gravar pedido diretamente no CRM.
- **CRM-PIPE-024 — Relação com ERP:** vincular oportunidade nativa a oferta, proposta, pedido e faturamento externos.
- **CRM-PIPE-025 — Encerramento governado:** exigir campos, motivos e evidências definidos pelo pipeline.
- **CRM-PIPE-026 — Reabertura:** somente com permissão, motivo e auditoria.
- **CRM-PIPE-027 — Aging e risco:** alertar negócios parados, sem interação ou próximos da data prevista.
- **CRM-PIPE-028 — Visibilidade:** respeitar carteira, equipe, participação, filial e sensibilidade.
- **CRM-PIPE-029 — Forecast category:** pipeline, best case, commit, closed e categorias configuráveis.
- **CRM-PIPE-030 — Métricas:** conversão, velocidade, ciclo, valor, win rate, perda e cobertura.
- **CRM-PIPE-031 — Mapa de vendas:** visão de saúde do funil destacando aging, valor e risco além de kanban/lista.
- **CRM-PIPE-032 — Congelamento:** ocultar do funil ativo e do forecast operacional, com motivo, data de retorno e filtro congelados.
- **CRM-PIPE-033 — Handoff entre funis:** pré-venda → venda → pós-venda/reativação com vínculo, fila lateral de elegíveis e histórico preservado.
- **CRM-PIPE-034 — Ordenação operacional:** maior valor, data prevista, ranking, aging e prioridade configurável.


### 8.16 Produtos, aplicações e contexto industrial

**Situação atual:** Parcial; há leitura de produtos, pedidos, produção e oportunidades operacionais.

**Objetivo:** representar corretamente negociações industriais sem duplicar o catálogo oficial do ERP.

#### Funcionalidades obrigatórias

- **CRM-IND-001 — Catálogo referenciado:** consultar produtos, famílias, grupos, unidades e status no ERP por contrato.
- **CRM-IND-002 — Item ainda não cadastrado:** permitir descrição preliminar em oportunidade técnica, identificada como não oficial.
- **CRM-IND-003 — Aplicação do cliente:** registrar equipamento, linha, projeto, programa ou uso final.
- **CRM-IND-004 — Código do cliente:** associar part number, revisão e descrição do cliente.
- **CRM-IND-005 — Volume estimado:** quantidade por período, ramp-up, início e fim previstos.
- **CRM-IND-006 — Requisitos técnicos:** especificação, desenho, material, norma, teste, embalagem e condição especial.
- **CRM-IND-007 — Viabilidade:** estado, responsáveis, pareceres, riscos, pendências e data de validade.
- **CRM-IND-008 — Amostras e protótipos:** solicitação, quantidade, prazo, envio, retorno e aprovação.
- **CRM-IND-009 — Homologação:** etapas, documentos, testes, aprovação e restrições.
- **CRM-IND-010 — Engenharia de aplicação:** tarefas, decisões e handoff para áreas técnicas sem mover a regra para o frontend.
- **CRM-IND-011 — Concorrência técnica:** solução concorrente, diferenciais e requisitos decisivos.
- **CRM-IND-012 — Custos e margem:** consumir dados aprovados da fonte responsável, com acesso sensível e sem cálculo paralelo não homologado.
- **CRM-IND-013 — Alteração de revisão:** versionar impacto em proposta, amostra e oportunidade.
- **CRM-IND-014 — Checklist por tipo de projeto:** campos e documentos obrigatórios por família/processo.
- **CRM-IND-015 — Marco de produção:** SOP, EOP, lançamento, piloto e demais datas configuráveis.
- **CRM-IND-016 — Handoff ganho:** pacote estruturado para cadastro, contrato, pedido e operação.

---

### 8.17 Propostas, cotações, aprovações e aceite

**Situação atual:** Parcial; já há consulta de propostas e PDFs do ecossistema operacional.

**Objetivo:** controlar o ciclo comercial da proposta sem romper a integração existente.

#### Funcionalidades obrigatórias

- **CRM-QUOTE-001 — Rascunho:** criar proposta vinculada à oportunidade, conta e contatos.
- **CRM-QUOTE-002 — Itens:** produto, descrição, quantidade, preço, moeda, impostos indicativos, prazo e condições.
- **CRM-QUOTE-003 — Dados oficiais:** preços e condições oficiais serão consultados/confirmados na fonte autorizada.
- **CRM-QUOTE-004 — Versões:** cada revisão terá número, data, autor, motivo e snapshot imutável.
- **CRM-QUOTE-005 — Comparação:** destacar diferenças entre versões.
- **CRM-QUOTE-006 — Templates:** modelos por unidade, segmento, idioma e tipo de proposta.
- **CRM-QUOTE-007 — Documentos:** gerar PDF e outros formatos com identidade visual controlada.
- **CRM-QUOTE-008 — Validade:** data de expiração e alerta de renovação.
- **CRM-QUOTE-009 — Aprovação:** fluxo por desconto, valor, margem, condição, exceção e alçada.
- **CRM-QUOTE-010 — Separação de funções:** criador não aprova a própria exceção quando a política exigir.
- **CRM-QUOTE-011 — Comentários de aprovação:** registrar decisão, motivo e condicionantes.
- **CRM-QUOTE-012 — Envio:** e-mail ou canal autorizado, preservando versão e destinatários.
- **CRM-QUOTE-013 — Visualização/aceite:** registrar entrega, abertura quando permitido, aceite, recusa e solicitação de alteração.
- **CRM-QUOTE-014 — Assinatura eletrônica:** integrar provedor autorizado e armazenar referências/evidências.
- **CRM-QUOTE-015 — Estado:** rascunho, em aprovação, aprovada, enviada, visualizada, aceita, recusada, expirada e substituída.
- **CRM-QUOTE-016 — Conversão:** vincular proposta aceita a pedido/contrato sem duplicar a transação.
- **CRM-QUOTE-017 — Proposta externa existente:** continuar exibindo documentos e histórico do fluxo atual.
- **CRM-QUOTE-018 — Auditoria:** acesso, download, envio, aprovação, aceite e alteração.
- **CRM-QUOTE-019 — Métricas:** tempo de elaboração, aprovação, aceite, desconto, conversão e perdas.
- **CRM-QUOTE-020 — Segurança:** marca d'água, expiração de link e revogação conforme classificação.

---

### 8.18 Tarefas, atividades e follow-ups

**Situação atual:** Existe como base; evolução de recorrência/checklist é backlog formal.

**Objetivo:** transformar compromissos em execução rastreável e impedir oportunidades sem próxima ação.

#### Funcionalidades obrigatórias

- **CRM-TASK-001 — Tipos:** ligação, e-mail, mensagem, reunião, visita, análise, proposta, amostra, aprovação e personalizado.
- **CRM-TASK-002 — Dados:** título, descrição, prazo, prioridade, status, responsável, criador e entidade relacionada.
- **CRM-TASK-003 — Múltiplos responsáveis:** usuários e grupos, com regra clara de conclusão individual ou coletiva.
- **CRM-TASK-004 — Checklist:** itens, ordem, obrigatoriedade e progresso.
- **CRM-TASK-005 — Recorrência:** diária, semanal, mensal, regra customizada, término e exceções.
- **CRM-TASK-006 — Dependências:** bloquear ou alertar quando outra tarefa não estiver concluída.
- **CRM-TASK-007 — Lembretes:** múltiplos horários, canais e escalonamento.
- **CRM-TASK-008 — SLA:** prazo calculado por calendário de negócio.
- **CRM-TASK-009 — Conclusão:** resultado, data, usuário, observação e próxima ação.
- **CRM-TASK-010 — Reabertura:** motivo e auditoria.
- **CRM-TASK-011 — Cancelamento:** motivo obrigatório e impacto em automações.
- **CRM-TASK-012 — Vínculos:** conta, contato, lead, oportunidade, proposta, pedido, campanha, reunião, caso e mensagem.
- **CRM-TASK-013 — Criação contextual:** a partir de mensagem, e-mail, transcrição, etapa, automação ou recomendação.
- **CRM-TASK-014 — Delegação:** transferir mantendo histórico.
- **CRM-TASK-015 — Bulk actions:** reagendar, reatribuir e priorizar com preview.
- **CRM-TASK-016 — Views:** hoje, atrasadas, próximas, concluídas, delegadas, equipe e por entidade.
- **CRM-TASK-017 — Produtividade:** conclusão, atraso, tempo, resultado e relação com conversão.
- **CRM-TASK-018 — Offline/mobile:** registrar visita ou conclusão com sincronização posterior controlada.
- **CRM-TASK-019 — Anexos e comentários:** preservar a base atual e aplicar segurança.
- **CRM-TASK-020 — Notificações:** não notificar o ator da própria ação e respeitar preferências.
- **CRM-TASK-021 — Fluxo inteligente:** ao concluir, sugerir próximo passo conforme etapa, tipo, playbook e política, com confirmação humana.
- **CRM-TASK-022 — Outcome obrigatório:** resultado da abordagem, próximo passo e campos mínimos antes de concluir, quando o processo exigir.
- **CRM-TASK-023 — Script embutido:** roteiro de vendas/qualificação na mesma tela da atividade.
- **CRM-TASK-024 — Nota por áudio:** captura mobile com transcrição opcional e vínculo ao registro.
- **CRM-TASK-025 — Fila segmentada:** agrupar ligações/tarefas do dia por segmento (perfil, setor, origem, ticket).

---

### 8.19 Agenda, reuniões e visitas

**Situação atual:** Parcial; sincronização Microsoft 365 é backlog formal.

**Objetivo:** gerenciar compromissos internos e com clientes, conectando preparação, execução e follow-up.

#### Funcionalidades obrigatórias

- **CRM-MEET-001 — Reunião:** assunto, início, fim, fuso, modalidade, local/link, organizador e participantes.
- **CRM-MEET-002 — Visita:** endereço, objetivo, check-in opcional, notas, fotos autorizadas e resultado.
- **CRM-MEET-003 — Participantes:** usuários, contatos, convidados externos e status de resposta.
- **CRM-MEET-004 — Disponibilidade:** consultar agendas autorizadas antes de sugerir horário.
- **CRM-MEET-005 — Sincronização bidirecional:** criar, atualizar, cancelar e refletir alterações externas.
- **CRM-MEET-006 — Política de conflito:** identificar qual sistema prevalece por campo e registrar resolução.
- **CRM-MEET-007 — Lembretes:** participantes internos, responsável e alertas de preparação.
- **CRM-MEET-008 — Briefing:** gerar resumo da conta, oportunidade, contatos e pendências antes do encontro.
- **CRM-MEET-009 — Pauta:** itens, responsáveis e documentos.
- **CRM-MEET-010 — Ata:** decisões, compromissos, riscos e próximos passos.
- **CRM-MEET-011 — Transcrição:** importar quando disponível e autorizada, sem presumir que toda reunião possua transcrição.
- **CRM-MEET-012 — Resumo assistido:** IA poderá propor resumo e tarefas com aprovação humana.
- **CRM-MEET-013 — No-show/remarcação:** registrar motivo e automação de retorno.
- **CRM-MEET-014 — Associação:** conta, contatos, lead, oportunidade, campanha e pedido.
- **CRM-MEET-015 — Recorrência:** reuniões periódicas com exceções.
- **CRM-MEET-016 — Métricas:** reuniões realizadas, no-show, tempo até reunião, resultado e conversão.
- **CRM-MEET-017 — Handoff:** encaminhar decisões a tarefas, aprovações ou áreas responsáveis.
- **CRM-MEET-018 — Privacidade:** conteúdo e participantes obedecerão às políticas de origem e retenção.
- **CRM-MEET-019 — Mapa de visitas:** clientes/contatos no mapa e otimização assistida de rota do dia.
- **CRM-MEET-020 — Briefing pré-contato:** abrir histórico, últimas interações, pendências e riscos antes de ligação ou visita.
- **CRM-MEET-021 — Sem tracking contínuo:** localização somente com finalidade e consentimento; nunca geofencing permanente.

---

### 8.20 Cadências e sequências de prospecção

**Situação atual:** Novo.

**Objetivo:** padronizar abordagens multicanal sem transformar o processo em spam.

#### Funcionalidades obrigatórias

- **CRM-SEQ-001 — Construtor:** etapas de tarefa, e-mail, mensagem, ligação, espera e decisão.
- **CRM-SEQ-002 — Templates:** conteúdo por etapa com variáveis seguras.
- **CRM-SEQ-003 — Inscrição:** lead, contato ou lista, individual ou em lote autorizado.
- **CRM-SEQ-004 — Horário:** dias úteis, fuso, janela de contato e frequência.
- **CRM-SEQ-005 — Personalização:** revisão antes do primeiro envio e campos por registro.
- **CRM-SEQ-006 — Pausa automática:** resposta, reunião agendada, opt-out, conversão ou erro.
- **CRM-SEQ-007 — Saída manual:** motivo e histórico.
- **CRM-SEQ-008 — Reentrada:** regra de cooldown e limite.
- **CRM-SEQ-009 — Distribuição de tarefas:** responsável e fila por etapa.
- **CRM-SEQ-010 — Entregabilidade:** respeitar supressão, limites e reputação.
- **CRM-SEQ-011 — Experimentos:** comparar sequência, timing e mensagem.
- **CRM-SEQ-012 — Métricas:** contatos, respostas, reuniões, conversões e tempo.
- **CRM-SEQ-013 — Governança:** aprovação para cadências corporativas e versão publicada.
- **CRM-SEQ-014 — IA assistiva:** sugerir personalização com evidências, nunca enviar sem política.
- **CRM-SEQ-015 — Contenção:** evitar que o mesmo contato esteja em cadências conflitantes.

---

### 8.21 Linha do tempo omnicanal

**Situação atual:** Parcial; atividades e sala interna existem, mas canais externos não estão consolidados.

**Objetivo:** oferecer histórico cronológico único e permissionado do relacionamento.

#### Funcionalidades obrigatórias

- **CRM-TL-001 — Eventos normalizados:** e-mail, Teams, WhatsApp, telefone, reunião, visita, campanha, web, tarefa, documento, proposta, pedido e nota.
- **CRM-TL-002 — Fonte explícita:** cada item mostrará canal, origem, autor, data e referência externa.
- **CRM-TL-003 — Filtros:** canal, tipo, pessoa, período, entidade e direção.
- **CRM-TL-004 — Associação múltipla:** um evento poderá pertencer a conta, contato, oportunidade e campanha.
- **CRM-TL-005 — Conteúdo resumido:** preview seguro, com abertura controlada do conteúdo completo.
- **CRM-TL-006 — Deep link:** abrir o item na fonte quando permitido.
- **CRM-TL-007 — Editados/excluídos:** refletir estado sem apagar a trilha de sincronização.
- **CRM-TL-008 — Deduplicação:** não registrar duas vezes o mesmo evento recebido por polling e webhook.
- **CRM-TL-009 — Evento manual:** nota, ligação, visita ou comunicação não integrada.
- **CRM-TL-010 — Fixar/importante:** marcar decisões e compromissos.
- **CRM-TL-011 — Busca:** indexar conteúdo permitido e filtrar por acesso.
- **CRM-TL-012 — Retenção:** respeitar a política mais restritiva entre CRM e sistema de origem.
- **CRM-TL-013 — Auditoria:** registrar acesso a conteúdo sensível.
- **CRM-TL-014 — IA:** resumir intervalo ou assunto com referências aos itens-fonte.
- **CRM-TL-015 — Exportação:** somente com permissão e política de conteúdo.
- **CRM-TL-016 — Freshness:** exibir data da última sincronização e eventual atraso.

---

### 8.22 Integração com Microsoft Teams

**Situação atual:** Backlog formal; não implementada no código atual.

**Objetivo:** permitir que conversas e reuniões comerciais acessíveis e autorizadas sejam relacionadas ao CRM sem criar vigilância indiscriminada.

#### Escopos funcionais

A integração deverá suportar, conforme modo de autorização e disponibilidade técnica:

- chats individuais;
- chats em grupo;
- chats de reunião;
- mensagens de canais;
- respostas em threads;
- menções, reações e anexos;
- reuniões e participantes;
- transcrições e gravações quando disponíveis e permitidas;
- links profundos para o Teams;
- notificações de criação, edição e exclusão.

#### Funcionalidades obrigatórias

- **CRM-TEAMS-001 — Conexão de identidade:** mapear usuário Minha DELPI a usuário Microsoft autorizado.
- **CRM-TEAMS-002 — Modos de acesso:** suportar delegado por usuário, consentimento específico de recurso e aplicação administrativa somente quando aprovado.
- **CRM-TEAMS-003 — Princípio do menor privilégio:** usar o menor escopo que atenda ao caso.
- **CRM-TEAMS-004 — Seleção explícita:** usuário poderá localizar e vincular chat, canal, thread ou reunião a uma entidade do CRM.
- **CRM-TEAMS-005 — Sem captura global por padrão:** não copiar automaticamente todas as conversas do tenant ou do usuário.
- **CRM-TEAMS-006 — Associação:** conta, contatos, lead, oportunidade, campanha, caso ou pedido.
- **CRM-TEAMS-007 — Sincronização incremental:** obter novas mensagens e alterações sem reler todo o histórico.
- **CRM-TEAMS-008 — Change notifications:** receber eventos em tempo próximo do real e fazer reconciliação periódica.
- **CRM-TEAMS-009 — Paginação e cursor:** controlar backfill e retomada segura.
- **CRM-TEAMS-010 — Mensagens:** autor, participantes, data, corpo sanitizado, anexos, menções, reações, reply e link externo.
- **CRM-TEAMS-011 — Edição/exclusão:** atualizar estado no CRM e registrar evento de sincronização.
- **CRM-TEAMS-012 — Identidade de convidados:** mapear participantes externos por e-mail/tenant quando possível, sem criar contato definitivo automaticamente.
- **CRM-TEAMS-013 — Sugestão de vínculo:** propor conta e contato por domínio/participantes, exigindo confirmação quando ambíguo.
- **CRM-TEAMS-014 — Criação de atividade:** transformar mensagem selecionada em tarefa, nota, oportunidade ou compromisso.
- **CRM-TEAMS-015 — Compartilhamento no Teams:** publicar cartão/link de registro CRM em chat/canal autorizado, com dados mínimos.
- **CRM-TEAMS-016 — Reuniões:** associar agenda, participantes, chat e oportunidade.
- **CRM-TEAMS-017 — Transcrições:** importar artefato somente quando a reunião gerar transcrição, a configuração administrativa permitir e o app tiver autorização.
- **CRM-TEAMS-018 — Atribuição de fala:** exibir oradores apenas quando disponibilizados e permitidos pelo tenant.
- **CRM-TEAMS-019 — Resumo de reunião:** IA gera rascunho de ata, decisões, riscos e tarefas com referências e revisão humana.
- **CRM-TEAMS-020 — Gravações:** preferir referência segura à origem; cópia local somente mediante política explícita.
- **CRM-TEAMS-021 — Restrição de exibição:** conteúdo não será liberado apenas pela permissão de ver a conta; a política do conector também será aplicada.
- **CRM-TEAMS-022 — Conteúdo sensível:** respeitar classificação, retenção, legal hold e outras políticas corporativas disponíveis.
- **CRM-TEAMS-023 — Auditoria:** registrar conexão, consentimento, vínculo, sincronização, visualização, exportação e revogação.
- **CRM-TEAMS-024 — Revogação:** desconectar conta, cancelar subscriptions e impedir novas sincronizações.
- **CRM-TEAMS-025 — Administração:** painel de tenant, app registration, permissões, subscriptions, expiração, erros e último sync.
- **CRM-TEAMS-026 — Resiliência:** retry com backoff, rate limit, idempotência, dead-letter e replay.
- **CRM-TEAMS-027 — Retenção:** armazenar somente metadados, previews ou conteúdo integral conforme política; não perpetuar conteúdo apagado indevidamente.
- **CRM-TEAMS-028 — Pesquisa:** pesquisar apenas no corpus sincronizado e autorizado; busca federada deverá respeitar o contexto do usuário.
- **CRM-TEAMS-029 — Métricas operacionais:** conexões, subscriptions, latência, falhas, mensagens vinculadas e reuniões processadas.
- **CRM-TEAMS-030 — Sem promessa indevida:** funcionalidades dependentes de APIs, políticas do tenant ou artefatos não disponíveis deverão indicar limitação na interface.

#### Política recomendada de autorização

1. **Padrão:** acesso delegado do próprio usuário para caixa, chats e calendário pessoais autorizados.
2. **Escopo específico:** consentimento por equipe, canal, chat ou reunião quando o recurso suportar esse modelo.
3. **Aplicação administrativa:** somente para caixas, equipes ou cenários corporativos previamente aprovados, nunca como default.
4. **Tenant-wide:** exige decisão formal de segurança, jurídico, privacidade e administração Microsoft 365.

#### Restrições técnicas conhecidas que deverão ser tratadas no desenho

- APIs de chats e canais usam permissões e modelos de consentimento diferentes.
- Algumas subscriptions e artefatos não cobrem todos os tipos de reunião.
- Acesso a transcrições pode estar desabilitado no tenant mesmo com permissão concedida ao app.
- Transcrição depende de ter sido gerada; não é sinônimo de gravação nem de toda chamada realizada.
- Subscriptions expiram e precisam ser renovadas.
- Conteúdo recebido em HTML deverá ser sanitizado antes de renderização.

---

### 8.23 Integração com Outlook e calendário corporativo

**Situação atual:** Backlog formal.

**Objetivo:** incorporar e-mail e agenda ao histórico comercial com consentimento e rastreabilidade.

#### Funcionalidades obrigatórias

- **CRM-OUT-001 — Conectar caixa:** fluxo de autorização separado da autenticação Minha DELPI.
- **CRM-OUT-002 — Pastas autorizadas:** inbox, enviados, pasta compartilhada ou escopo aprovado.
- **CRM-OUT-003 — Sincronização seletiva:** mensagens vinculadas por participantes, domínio, categoria, tag ou ação explícita.
- **CRM-OUT-004 — Associação manual:** vincular e-mail/thread a conta, contato, oportunidade, pedido ou caso.
- **CRM-OUT-005 — Associação sugerida:** domínio e participantes, com confirmação quando ambígua.
- **CRM-OUT-006 — Threading:** preservar conversation ID, in-reply-to, participantes e referências.
- **CRM-OUT-007 — Envio:** criar rascunho ou enviar mensagem individual por identidade conectada conforme política.
- **CRM-OUT-008 — Anexos:** metadados, antivírus, classificação e armazenamento/referência controlados.
- **CRM-OUT-009 — Change notifications:** receber alterações e usar reconciliação/delta quando disponível.
- **CRM-OUT-010 — Shared mailboxes:** suportar caixas compartilhadas com autorização adequada.
- **CRM-OUT-011 — Calendário:** listar disponibilidade, criar, atualizar, cancelar e receber respostas.
- **CRM-OUT-012 — Reunião online:** gerar ou associar link corporativo conforme capacidade autorizada.
- **CRM-OUT-013 — Categorias:** opção de marcar itens sincronizados no Outlook sem obrigar alteração.
- **CRM-OUT-014 — Exclusão/edição:** refletir estado da origem conforme retenção.
- **CRM-OUT-015 — Limites:** paginação, throttling e janela de backfill configurável.
- **CRM-OUT-016 — Segurança:** escopos mínimos; segredos e tokens no backend.
- **CRM-OUT-017 — Auditoria:** conexão, leitura, vínculo, envio, download e revogação.
- **CRM-OUT-018 — Desconexão:** revogar tokens, subscriptions e sincronização futura.
- **CRM-OUT-019 — Caixa compartilhada comercial:** filas, ownership, SLA e resposta sem perder a autoria.
- **CRM-OUT-020 — Métricas:** mensagens vinculadas, respostas, tempo de resposta e falhas de sync.

---

### 8.24 WhatsApp e caixa omnicanal

**Situação atual:** Parcial apenas como abertura de link; não há ingestão real.

**Objetivo:** centralizar conversas corporativas em canal oficial e permitir continuidade do atendimento.

#### Funcionalidades obrigatórias

- **CRM-WA-001 — Conector oficial:** integrar provedores homologados e números corporativos.
- **CRM-WA-002 — Caixa compartilhada:** filas, times, responsáveis, transferências e SLA.
- **CRM-WA-003 — Inbound/outbound:** mensagens de texto, imagens, documentos, localização, contatos e tipos suportados.
- **CRM-WA-004 — Estados:** enviado, entregue, lido, falhou e motivo.
- **CRM-WA-005 — Identidade:** associar telefone a contato/lead, com fluxo de confirmação para duplicidade.
- **CRM-WA-006 — Timeline:** relacionar conversa a conta, oportunidade, campanha, pedido e caso.
- **CRM-WA-007 — Templates:** biblioteca, aprovação no provedor, variáveis e idioma.
- **CRM-WA-008 — Janela de atendimento:** respeitar regras vigentes do canal/provedor.
- **CRM-WA-009 — Opt-in/opt-out:** registrar prova, finalidade e revogação.
- **CRM-WA-010 — Campanhas:** audiência, aprovação, limite, custo, entrega, resposta e conversão.
- **CRM-WA-011 — Áudio:** reproduzir e transcrever mensagem de áudio quando permitido.
- **CRM-WA-012 — Chamadas:** não prometer captura de chamadas se o canal/provedor não expuser esse artefato.
- **CRM-WA-013 — Chatbot:** qualificação, FAQ, coleta de dados, status e transferência humana.
- **CRM-WA-014 — Handoff:** preservar contexto, mensagens e responsável.
- **CRM-WA-015 — Respostas rápidas:** snippets, templates e conteúdo recomendado.
- **CRM-WA-016 — Anexos:** malware scan, preview, retenção e classificação.
- **CRM-WA-017 — Custos:** registrar custo estimado/real por conversa ou campanha quando o provedor disponibilizar.
- **CRM-WA-018 — Números pessoais:** não depender de celulares pessoais como histórico corporativo oficial.
- **CRM-WA-019 — Supervisão:** fila, volume, tempo de resposta, abandono, resolução e satisfação.
- **CRM-WA-020 — Webhooks:** assinatura, idempotência, ordem, retry e replay.
- **CRM-WA-021 — IA assistiva:** sugestão de resposta, resumo e extração com confirmação.
- **CRM-WA-022 — Bloqueio:** impedir comunicação após opt-out ou restrição.
- **CRM-WA-023 — Auditoria:** leitura, envio, transferência, exportação e alteração de vínculo.
- **CRM-WA-024 — Expansão omnicanal:** modelo de conversa deverá aceitar web chat, SMS e canais futuros sem reescrever o domínio.

---

### 8.25 Telefonia, chamadas e transcrição

**Situação atual:** Novo.

**Objetivo:** registrar interações por voz e seus resultados, respeitando consentimento e capacidade do provedor.

#### Funcionalidades obrigatórias

- **CRM-CALL-001 — Click-to-call:** iniciar chamada por provedor homologado.
- **CRM-CALL-002 — Registro manual:** número, contato, horário, duração, direção, resultado e notas.
- **CRM-CALL-003 — Log automático:** importar início, fim, duração, usuário, fila e status.
- **CRM-CALL-004 — Gravação:** somente quando legalmente permitida, avisada e suportada.
- **CRM-CALL-005 — Transcrição:** importar/gerar com política, idioma e indicação de qualidade.
- **CRM-CALL-006 — Disposição:** conectado, sem resposta, ocupado, inválido, reunião marcada e outros motivos.
- **CRM-CALL-007 — Associação:** conta, contato, lead, oportunidade, campanha e tarefa.
- **CRM-CALL-008 — Próxima ação:** criar tarefa, reunião ou atualização após a chamada.
- **CRM-CALL-009 — Resumo assistido:** IA com referências e confirmação.
- **CRM-CALL-010 — Palavras-chave e temas:** análise agregada, sem uso inadequado para vigilância individual.
- **CRM-CALL-011 — Métricas:** tentativas, conexão, duração, resultado e conversão.
- **CRM-CALL-012 — Retenção:** política específica para áudio e transcrição.
- **CRM-CALL-013 — Acesso:** gravações e transcrições terão controle mais restrito que metadados.
- **CRM-CALL-014 — Provedor desacoplado:** porta/adaptador para troca de solução.
- **CRM-CALL-015 — Limitação explícita:** chamada de mensageria, chamada PSTN e reunião online serão tratadas como artefatos distintos.

---

### 8.26 Sala de interação e colaboração interna

**Situação atual:** Existe e deverá ser preservada.

**Objetivo:** manter colaboração interna em tempo real sem confundi-la com canais de cliente.

#### Funcionalidades obrigatórias

- **CRM-COLLAB-001 — Inbox e salas:** manter lista, não lidas e acesso global conforme política atual.
- **CRM-COLLAB-002 — Threads:** preservar respostas encadeadas.
- **CRM-COLLAB-003 — Menções:** usuários, grupos e entidades do CRM.
- **CRM-COLLAB-004 — Presença:** status e participantes conectados.
- **CRM-COLLAB-005 — Busca:** texto, autor, período e entidade.
- **CRM-COLLAB-006 — Criar tarefa:** manter capacidade de converter mensagem em atividade.
- **CRM-COLLAB-007 — Links de entidade:** conta, oportunidade, pedido, proposta, campanha, lead e caso.
- **CRM-COLLAB-008 — Decisões:** marcar mensagem como decisão, compromisso, risco ou dúvida.
- **CRM-COLLAB-009 — Pins:** fixar contexto e documentos.
- **CRM-COLLAB-010 — Anexos:** aplicar a política comum de arquivos.
- **CRM-COLLAB-011 — Resumo:** gerar resumo de thread com referências.
- **CRM-COLLAB-012 — Realtime confiável:** evento pós-commit, reconexão e recuperação de lacunas.
- **CRM-COLLAB-013 — Notificações:** menção, resposta e atribuição com preferências.
- **CRM-COLLAB-014 — Histórico:** edições e exclusões auditadas.
- **CRM-COLLAB-015 — Separação de canais:** mensagens internas não serão exibidas ao cliente nem exportadas junto a comunicação externa sem regra explícita.

---

### 8.27 Pedidos em aberto, produção e exceções

**Situação atual:** Existe e é uma das bases mais maduras do Portal Comercial.

**Objetivo:** conectar a execução pós-venda ao relacionamento sem tornar o CRM o sistema transacional.

#### Funcionalidades obrigatórias

- **CRM-ORDER-001 — Lista consolidada:** preservar filtros, escopo e visão por carteira/equipe.
- **CRM-ORDER-002 — Detalhe:** itens, quantidade, valor, datas, produção, disponibilidade e bloqueios.
- **CRM-ORDER-003 — Kanban:** disponibilidade, postergado, pronto para faturar e demais estados homologados.
- **CRM-ORDER-004 — Horizonte:** atraso, períodos futuros e sem data.
- **CRM-ORDER-005 — Alocação:** exibir lógica oficial fornecida pelo backend, nunca recalculada no MFE.
- **CRM-ORDER-006 — Operações de produção:** consultar OPs, marcos e rastreio quando disponíveis por contrato.
- **CRM-ORDER-007 — Exceções:** atraso, quantidade, alteração de data, falta, bloqueio e risco.
- **CRM-ORDER-008 — Comunicação:** associar e-mail, Teams, WhatsApp, ligação e tarefa ao pedido.
- **CRM-ORDER-009 — Notificação de faturamento:** preservar destinatários por carteira e permission code específico.
- **CRM-ORDER-010 — Ação contextual:** criar tarefa, sala, caso ou reunião a partir de uma exceção.
- **CRM-ORDER-011 — Freshness:** exibir data/hora da consulta e origem.
- **CRM-ORDER-012 — Timeline:** mudanças relevantes e comunicações vinculadas.
- **CRM-ORDER-013 — Sem edição indevida:** qualquer comando transacional deverá passar por API oficial, validação e autorização.
- **CRM-ORDER-014 — OTD:** manter metodologia documentada e ligar causas a fatos, não a inferências inventadas.
- **CRM-ORDER-015 — Métricas:** valor aberto, itens, aging, atraso, disponibilidade, exceções e tempo de resolução.

---

### 8.28 Confirmação de pedidos com o cliente

**Situação atual:** Backlog formal.

**Objetivo:** registrar de forma auditável o alinhamento de datas, quantidades e condições com o cliente.

#### Funcionalidades obrigatórias

- **CRM-CONF-001 — Solicitação de confirmação:** selecionar pedido/itens e enviar por canal autorizado.
- **CRM-CONF-002 — Snapshot:** preservar dados apresentados ao cliente no momento do envio.
- **CRM-CONF-003 — Resposta:** confirmado, divergente, solicitação de alteração, sem resposta e cancelado.
- **CRM-CONF-004 — Detalhe por item:** quantidade, data, entrega parcial e observação.
- **CRM-CONF-005 — Evidência:** mensagem, e-mail, portal seguro, anexo ou registro manual com autoria.
- **CRM-CONF-006 — Prazo:** data limite e lembretes.
- **CRM-CONF-007 — Escalonamento:** vendedor, gestor, PCP, faturamento ou área configurada.
- **CRM-CONF-008 — Divergência:** criar tarefa/caso e impedir estado “confirmado” sem resolução.
- **CRM-CONF-009 — Portal/link seguro:** permitir resposta externa por link expirável, quando aprovado.
- **CRM-CONF-010 — Integração:** encaminhar decisão à fonte transacional por comando oficial quando necessário.
- **CRM-CONF-011 — Auditoria:** quem enviou, quem respondeu, quando, qual versão e qual canal.
- **CRM-CONF-012 — Métricas:** taxa de resposta, divergências, tempo de confirmação e impacto em entrega.
- **CRM-CONF-013 — Reconfirmação:** nova versão sem apagar a anterior.
- **CRM-CONF-014 — Consentimento e segurança:** não expor dados de outros pedidos ou clientes no link externo.

---

### 8.29 Carteiras, territórios e cobertura

**Situação atual:** Existe para carteiras, membros, cobertura, carga e transferência.

**Objetivo:** organizar responsabilidade comercial, balancear trabalho e permitir continuidade.

#### Funcionalidades obrigatórias

- **CRM-PORT-001 — Carteira:** preservar CRUD, membros, owner e carteiras órfãs quando permitido.
- **CRM-PORT-002 — Clientes:** manter inclusão, remoção e substituição controladas.
- **CRM-PORT-003 — Transferência:** manter motivo, origem, destino, lote e auditoria.
- **CRM-PORT-004 — Cobertura:** clientes sem responsável, duplicados, compartilhados e com lacunas.
- **CRM-PORT-005 — Carga:** quantidade, potencial, valor aberto, tarefas, leads e oportunidades.
- **CRM-PORT-006 — Regras de território:** região, segmento, linha, filial, potencial e cliente nomeado.
- **CRM-PORT-007 — Cobertura compartilhada:** responsabilidades primária e secundária.
- **CRM-PORT-008 — Substituição temporária:** início, fim, motivo e escopo.
- **CRM-PORT-009 — Histórico:** preservar quem atendia a conta em cada período.
- **CRM-PORT-010 — Rebalanceamento assistido:** sugerir redistribuição sem executar automaticamente.
- **CRM-PORT-011 — Capacidade:** disponibilidade do vendedor e limite de entradas.
- **CRM-PORT-012 — Equipes:** agrupamento operacional separado de RBAC.
- **CRM-PORT-013 — Visões:** minha carteira, equipe, filial e consolidado conforme autorização.
- **CRM-PORT-014 — KPIs:** cobertura, carga, inatividade, pipeline, faturamento e risco por carteira.
- **CRM-PORT-015 — Sem dual-read indevido:** uma única fonte de escopo será aplicada pelo `commercial-api`.

---

### 8.30 Plano de conta, saúde, expansão e reativação

**Situação atual:** Novo, com alguns dados que já existem na Conta 360.

**Objetivo:** transformar relacionamento pós-venda em processo ativo de crescimento e retenção.

#### Funcionalidades obrigatórias

- **CRM-CS-001 — Plano de conta:** objetivos, iniciativas, responsáveis, prazos e resultados.
- **CRM-CS-002 — Mapa de stakeholders:** influência, apoio, relacionamento e lacunas de contato.
- **CRM-CS-003 — SWOT/risco:** forças, oportunidades, fraquezas, ameaças e mitigação.
- **CRM-CS-004 — Produtos atuais:** consumo, tendência e participação quando houver fonte homologada.
- **CRM-CS-005 — White space:** famílias/produtos aplicáveis ainda não comprados.
- **CRM-CS-006 — Saúde:** score composto por sinais documentados e explicáveis.
- **CRM-CS-007 — Risco:** queda de compra, atraso, reclamação, ausência de contato, perda de sponsor e pendência crítica.
- **CRM-CS-008 — Inatividade:** regras por segmento, periodicidade e histórico.
- **CRM-CS-009 — Reativação:** lista, campanha, cadência, oportunidade e resultado.
- **CRM-CS-010 — Expansão:** cross-sell, upsell, nova planta, novo projeto e renovação.
- **CRM-CS-011 — Marcos:** onboarding, homologação, contrato, revisão e renovação.
- **CRM-CS-012 — Contratos:** referência, vigência, condições, alertas e documentos; fonte oficial definida por contrato.
- **CRM-CS-013 — Plano mútuo:** ações DELPI/cliente, datas e evidências quando aplicável.
- **CRM-CS-014 — Pesquisa:** NPS, CSAT ou pesquisa customizada, com contexto e histórico.
- **CRM-CS-015 — Handoff:** transição de hunter para farmer preservando responsabilidades e histórico.
- **CRM-CS-016 — Métricas:** retenção, reativação, expansão, frequência, risco e saúde.
- **CRM-CS-017 — Alertas:** evento de risco cria tarefa ou fluxo, sem classificar cliente sem metodologia aprovada.


### 8.31 Casos, solicitações e suporte comercial

**Situação atual:** Novo; poderá integrar módulos especializados sem substituí-los.

**Objetivo:** controlar solicitações comerciais que exigem acompanhamento, SLA e resolução.

#### Funcionalidades obrigatórias

- **CRM-CASE-001 — Caso:** assunto, descrição, tipo, prioridade, status, responsável e origem.
- **CRM-CASE-002 — Tipos:** dúvida, documentação, preço, entrega, divergência, cadastro, amostra, reclamação comercial e personalizado.
- **CRM-CASE-003 — Vínculos:** conta, contato, oportunidade, pedido, nota, produto e comunicação.
- **CRM-CASE-004 — Fila:** equipe, owner, transferência e escalonamento.
- **CRM-CASE-005 — SLA:** primeira resposta, atualização e resolução por tipo/cliente.
- **CRM-CASE-006 — Comunicação:** thread omnicanal associada ao caso.
- **CRM-CASE-007 — Tarefas:** plano de resolução e dependências.
- **CRM-CASE-008 — Handoff:** encaminhar a qualidade, engenharia, PCP, financeiro ou módulo especialista por contrato, sem copiar regra de domínio.
- **CRM-CASE-009 — Status:** novo, em análise, aguardando cliente, aguardando área, resolvido, fechado e reaberto.
- **CRM-CASE-010 — Resolução:** categoria, causa, ação, evidência e data.
- **CRM-CASE-011 — Reabertura:** motivo, prazo e auditoria.
- **CRM-CASE-012 — Satisfação:** pesquisa opcional ao final.
- **CRM-CASE-013 — Base de conhecimento:** sugerir artigos e respostas aprovadas.
- **CRM-CASE-014 — Métricas:** volume, SLA, backlog, causa, reabertura e satisfação.
- **CRM-CASE-015 — Limite de escopo:** casos técnicos especializados continuarão pertencendo aos respectivos módulos; o CRM manterá referência e status resumido.

---

### 8.32 Forecast, metas e quotas

**Situação atual:** Backlog formal para forecast nativo; metas e indicadores já possuem bases em outros componentes.

**Objetivo:** oferecer previsão comercial rastreável sem substituir a fonte oficial de metas corporativas.

#### Funcionalidades obrigatórias

- **CRM-FCT-001 — Categorias:** pipeline, upside, best case, commit, closed e outras homologadas.
- **CRM-FCT-002 — Forecast por oportunidade:** valor, data, probabilidade e categoria.
- **CRM-FCT-003 — Forecast do vendedor:** submissão periódica e comentário.
- **CRM-FCT-004 — Roll-up:** vendedor, carteira, equipe, filial, unidade e empresa.
- **CRM-FCT-005 — Snapshot:** congelar cada ciclo para comparar evolução.
- **CRM-FCT-006 — Ajuste gerencial:** override separado do valor do vendedor, com justificativa.
- **CRM-FCT-007 — Cenários:** conservador, provável e otimista.
- **CRM-FCT-008 — Conversão monetária:** moeda original e moeda base com taxa/fonte.
- **CRM-FCT-009 — Quotas:** valor, período, responsável, equipe, produto e fonte.
- **CRM-FCT-010 — Integração de metas:** consumir metas homologadas, sem criar uma segunda fonte conflitante.
- **CRM-FCT-011 — Cobertura de pipeline:** pipeline elegível dividido pela meta, com metodologia visível.
- **CRM-FCT-012 — Acurácia:** comparar forecast com realizado após fechamento.
- **CRM-FCT-013 — Tendência:** histórico de mudança de valor, data e categoria.
- **CRM-FCT-014 — Risco:** sinalizar concentração, aging, ausência de próxima ação e data irrealista.
- **CRM-FCT-015 — Lock:** fechar período e exigir permissão para reabertura.
- **CRM-FCT-016 — Métricas:** gap para meta, commit, forecast, realizado, acurácia e cobertura.

---

### 8.33 Analytics comercial, marketing e atribuição

**Situação atual:** Existe para parte dos indicadores operacionais; novo para CRM e marketing.

**Objetivo:** transformar eventos rastreáveis em indicadores confiáveis para operação e gestão.

#### Regras universais de KPI

Todo indicador deverá declarar:

- nome e objetivo;
- fórmula;
- numerador e denominador;
- unidade;
- natureza bruta/líquida quando aplicável;
- fonte de dados;
- escopo;
- filtros aceitos;
- timezone e período;
- regra para dados incompletos;
- data/hora de atualização;
- status da metodologia;
- responsável pela homologação.

#### Funcionalidades obrigatórias

- **CRM-AN-001 — Dashboard executivo:** receita, pipeline, forecast, meta, conversão, ciclo, carteira, risco e campanhas.
- **CRM-AN-002 — Dashboard do vendedor:** carteira, atividades, oportunidades, tarefas, mensagens e objetivos.
- **CRM-AN-003 — Dashboard do gestor:** equipe, capacidade, produtividade, cobertura, coaching e violações de SLA.
- **CRM-AN-004 — Funil:** entradas, saídas, conversão e tempo por etapa.
- **CRM-AN-005 — Velocidade:** valor, quantidade, win rate e ciclo em composição documentada.
- **CRM-AN-006 — Win/loss:** motivos, concorrentes, produto, segmento e tendência.
- **CRM-AN-007 — Aging:** leads, tarefas, oportunidades, propostas e casos.
- **CRM-AN-008 — Atividades:** volume, conclusão, resultado e correlação com avanço.
- **CRM-AN-009 — Lead response:** tempo até primeira ação e contato válido.
- **CRM-AN-010 — Marketing:** alcance, entrega, engajamento, conversão, pipeline e receita influenciada.
- **CRM-AN-011 — Atribuição:** first touch, last touch, linear e modelos aprovados.
- **CRM-AN-012 — CAC:** custos elegíveis divididos por clientes adquiridos, com janela e critérios explícitos.
- **CRM-AN-013 — ROI:** receita/margem elegível e custo conforme fonte homologada.
- **CRM-AN-014 — Cohorts:** aquisição, conversão, recompra e reativação por período.
- **CRM-AN-015 — Carteira:** ativo, inativo, recuperado, frequência e potencial apenas com fichas aprovadas.
- **CRM-AN-016 — Cross-sell:** adoção de famílias/produtos e white space.
- **CRM-AN-017 — Forecast:** submissão, acurácia, variação e gap.
- **CRM-AN-018 — Canais:** e-mail, Teams, WhatsApp, telefone, web, evento e visita.
- **CRM-AN-019 — Comunicação:** tempo de resposta, volume, fila e resultado.
- **CRM-AN-020 — Pedidos:** preservar valor aberto, horizonte, disponibilidade, OTD e exceções homologadas.
- **CRM-AN-021 — Customer success:** saúde, risco, retenção, expansão e reativação.
- **CRM-AN-022 — Drill-down:** indicador até registros-fonte autorizados.
- **CRM-AN-023 — Comparações:** período anterior, ano anterior, meta e benchmark interno aprovado.
- **CRM-AN-024 — Filtros globais:** período, filial, equipe, carteira, vendedor, segmento, produto e origem.
- **CRM-AN-025 — Exportação:** dados e relatório com escopo e auditoria.
- **CRM-AN-026 — Agendamento:** envio periódico de relatórios autorizados.
- **CRM-AN-027 — Alertas:** regra baseada em KPI com cooldown e responsável.
- **CRM-AN-028 — Catálogo de métricas:** glossário contextual e versão da metodologia.
- **CRM-AN-029 — Freshness:** indicar atraso e indisponibilidade, nunca apresentar dado velho como atual.
- **CRM-AN-030 — Anti-invenção:** métricas ainda não homologadas não poderão ser exibidas como definitivas.
- **CRM-AN-031 — Sumário semanal/mensal:** atividades planejadas vs. executadas, pipeline, forecast e próximos passos para ritual de gestão.
- **CRM-AN-032 — Aderência a rituais:** atualização pós-contato, próximo passo preenchido, briefing pré-reunião — sem ranqueamento tóxico.
- **CRM-AN-033 — Mapa de vendas analítico:** aging × valor × etapa na gestão à vista.

---

### 8.34 Inteligência artificial comercial

**Situação atual:** Design documentado; execução produtiva ainda é backlog.

**Objetivo:** reduzir trabalho mecânico e melhorar decisões sem retirar controle humano.

#### Casos de uso obrigatórios

- **CRM-AI-001 — Resumo de conta:** fatos recentes, pedidos, pipeline, mensagens, riscos e próximos passos.
- **CRM-AI-002 — Resumo de oportunidade:** situação, stakeholders, objeções, atividades, riscos e pendências.
- **CRM-AI-003 — Resumo de conversa:** e-mail, Teams, WhatsApp, sala interna ou ligação, conforme acesso.
- **CRM-AI-004 — Resumo de reunião:** decisões, compromissos, riscos, perguntas e tarefas sugeridas.
- **CRM-AI-005 — Briefing pré-reunião:** contexto e perguntas recomendadas.
- **CRM-AI-006 — Próxima melhor ação:** sugestão explicada e ligada a fatos.
- **CRM-AI-007 — Rascunho de mensagem:** e-mail, WhatsApp e resposta interna no tom configurado.
- **CRM-AI-008 — Extração:** contatos, datas, compromissos, produtos, valores e riscos a partir de conteúdo.
- **CRM-AI-009 — Criação assistida:** preparar tarefa, contato, lead, oportunidade, nota ou caso para confirmação.
- **CRM-AI-010 — Consulta em linguagem natural:** responder perguntas sobre dados autorizados com fonte e filtros.
- **CRM-AI-011 — Análise de pipeline:** riscos, negócios estagnados e inconsistências.
- **CRM-AI-012 — Forecast assistido:** estimativa adicional, separada da previsão oficial e explicável.
- **CRM-AI-013 — Qualidade de dados:** sugerir duplicidades, campos ausentes e inconsistências.
- **CRM-AI-014 — Recomendações de conteúdo/produto:** baseadas em catálogo e histórico homologados.
- **CRM-AI-015 — Coaching:** identificar padrões e sugerir perguntas, sem produzir avaliação opaca de pessoas.
- **CRM-AI-016 — Chatbot externo:** responder com base aprovada, capturar lead e transferir para humano.
- **CRM-AI-017 — Voz:** aceitar ditado/comando e devolver ação em rascunho.
- **CRM-AI-018 — Tradução e revisão:** apoiar comunicação multilíngue com indicação de conteúdo gerado.

#### Guardrails obrigatórios

- **CRM-AI-G01 — Fonte:** IA nunca será fonte de verdade.
- **CRM-AI-G02 — Confirmação:** escrita, envio, fechamento, aprovação, exclusão e alteração de valor exigirão confirmação/política.
- **CRM-AI-G03 — Escopo:** o contexto obedecerá ao mesmo RBAC e escopo do usuário.
- **CRM-AI-G04 — Citações:** respostas factuais deverão apontar para registros usados.
- **CRM-AI-G05 — Minimização:** enviar ao modelo somente o contexto necessário.
- **CRM-AI-G06 — Redação:** remover ou mascarar secrets e PII quando aplicável.
- **CRM-AI-G07 — Conteúdo externo não confiável:** e-mails e mensagens não poderão instruir o agente a contornar políticas.
- **CRM-AI-G08 — Sem treinamento indevido:** dados corporativos não serão usados para treinar modelos externos sem autorização formal.
- **CRM-AI-G09 — Auditoria:** registrar usuário, ação, hash do prompt, IDs de contexto, modelo, versão, resultado e confirmação.
- **CRM-AI-G10 — Avaliação:** medir qualidade, alucinação, segurança, utilidade e custo.
- **CRM-AI-G11 — Feedback:** permitir correção e sinalização pelo usuário.
- **CRM-AI-G12 — Fallback:** falha do modelo não bloqueará funções essenciais do CRM.
- **CRM-AI-G13 — Gateway:** toda execução passará pelo AI Gateway definido pela plataforma.
- **CRM-AI-G14 — Transparência:** interface identificará conteúdo sugerido/gerado.

---

### 8.35 Motor de workflows e automações comerciais

**Situação atual:** Novo como plataforma genérica; há jobs e eventos pontuais.

**Objetivo:** permitir processos configuráveis, auditáveis e seguros para vendas e relacionamento.

#### Funcionalidades obrigatórias

- **CRM-WF-001 — Gatilhos:** evento de entidade, horário, SLA, webhook, score, etapa e condição de dados.
- **CRM-WF-002 — Condições:** campos, relações, agregações e escopo.
- **CRM-WF-003 — Ações internas:** criar tarefa, alterar proprietário, mover etapa, adicionar tag, notificar e criar caso.
- **CRM-WF-004 — Ações externas:** enviar mensagem, chamar webhook ou criar evento, sempre sob política.
- **CRM-WF-005 — Aprovação:** etapa humana com aprovador, prazo e escalonamento.
- **CRM-WF-006 — Espera:** tempo, data, evento ou janela de negócio.
- **CRM-WF-007 — Ramificação:** condições, switch e fallback.
- **CRM-WF-008 — Versão:** rascunho, teste, publicação, pausa e rollback.
- **CRM-WF-009 — Simulação:** executar sem efeitos e mostrar decisões.
- **CRM-WF-010 — Idempotência:** chave por evento/instância/ação.
- **CRM-WF-011 — Retry:** backoff, limite e classificação de erro.
- **CRM-WF-012 — Dead-letter:** fila de falhas com replay autorizado.
- **CRM-WF-013 — Compensação:** ação de reversão quando possível.
- **CRM-WF-014 — Loop guard:** profundidade, frequência e limite.
- **CRM-WF-015 — Observabilidade:** instâncias, etapas, duração, erro e ação atual.
- **CRM-WF-016 — Auditoria:** versão, gatilho, dados avaliados, caminho e efeitos.
- **CRM-WF-017 — Permissão:** criador do fluxo não poderá obter acesso a dados por meio da automação.
- **CRM-WF-018 — Templates:** fluxos aprovados para lead, oportunidade, pedido, reativação, SLA e aprovação.

---

### 8.36 Notificações, alertas e preferências

**Situação atual:** Existe como base na Minha DELPI e no domínio comercial.

**Objetivo:** avisar a pessoa certa, no canal certo, sem excesso e com deep link acionável.

#### Funcionalidades obrigatórias

- **CRM-NOT-001 — Sino Minha DELPI:** canal padrão para eventos do CRM.
- **CRM-NOT-002 — Categorias:** tarefas, leads, oportunidades, propostas, pedidos, mensagens, campanhas, aprovações e integrações.
- **CRM-NOT-003 — Destinatários:** envolvidos, responsáveis, grupos, carteira ou permission code específico justificado.
- **CRM-NOT-004 — Exclusão do ator:** evitar notificar quem acabou de executar a ação.
- **CRM-NOT-005 — Deep link:** abrir o registro e contexto exato.
- **CRM-NOT-006 — Preferências:** tipo, severidade, canal, digest e silêncio.
- **CRM-NOT-007 — Canais:** in-app, e-mail, Teams, push e outros autorizados.
- **CRM-NOT-008 — Digest:** agrupar eventos de baixa urgência.
- **CRM-NOT-009 — Escalonamento:** atraso, SLA e ausência de resposta.
- **CRM-NOT-010 — Deduplicação:** agrupar repetições e atualizar estado.
- **CRM-NOT-011 — Rate limit:** impedir tempestade de alertas.
- **CRM-NOT-012 — Leitura:** marcar individual/todas, histórico e expiração.
- **CRM-NOT-013 — Severidade:** info, atenção, risco e crítica com critérios.
- **CRM-NOT-014 — Auditoria:** emissão, entrega, leitura e ação.
- **CRM-NOT-015 — Respeito ao acesso:** notificação não poderá vazar dado de registro que o destinatário não pode abrir.
- **CRM-NOT-016 — Saúde de integração:** alertar administradores sobre subscriptions vencendo, tokens revogados e filas paradas.

---

### 8.37 Arquivos, documentos, templates e conhecimento

**Situação atual:** Parcial; anexos e documentos de propostas já existem.

**Objetivo:** organizar conteúdo comercial e técnico com segurança e reutilização.

#### Funcionalidades obrigatórias

- **CRM-DOC-001 — Upload:** tamanho, tipo, checksum e vínculo.
- **CRM-DOC-002 — Armazenamento:** object storage ou serviço autorizado; metadados no domínio.
- **CRM-DOC-003 — Antivírus:** escanear antes de disponibilizar.
- **CRM-DOC-004 — Preview:** formatos suportados sem download obrigatório.
- **CRM-DOC-005 — Versão:** revisão, autor, motivo e validade.
- **CRM-DOC-006 — Classificação:** público interno, comercial, confidencial, restrito e categorias definidas.
- **CRM-DOC-007 — Permissão:** herança controlada da entidade e exceções explícitas.
- **CRM-DOC-008 — Link seguro:** expiração, revogação, limite e auditoria.
- **CRM-DOC-009 — Templates:** e-mail, proposta, ata, plano, checklist e playbook.
- **CRM-DOC-010 — Biblioteca comercial:** catálogo pesquisável por produto, segmento e etapa.
- **CRM-DOC-011 — Conhecimento:** FAQs, objeções, apresentações, requisitos e conteúdo técnico aprovado.
- **CRM-DOC-012 — Recomendação:** sugerir conteúdo conforme contexto, sem burlar acesso.
- **CRM-DOC-013 — Uso:** registrar compartilhamento e associação, respeitando privacidade.
- **CRM-DOC-014 — Assinatura:** integração com provedor e evidência.
- **CRM-DOC-015 — Retenção:** política por tipo e origem.
- **CRM-DOC-016 — Exclusão:** soft delete, quarentena ou remoção conforme política.
- **CRM-DOC-017 — OCR/indexação:** somente para formatos/políticas aprovados; conteúdo sensível terá índice restrito.
- **CRM-DOC-018 — DLP:** impedir ou alertar compartilhamento incompatível com classificação.

---

### 8.38 Busca global, filtros, views e produtividade

**Situação atual:** Parcial; há buscas por domínio e filtros nas telas atuais.

**Objetivo:** localizar rapidamente qualquer informação autorizada e reduzir navegação repetitiva.

#### Funcionalidades obrigatórias

- **CRM-SEARCH-001 — Busca global:** empresas, contatos, leads, oportunidades, pedidos, propostas, tarefas, casos, mensagens e documentos.
- **CRM-SEARCH-002 — Permission-aware:** indexação e consulta respeitarão acesso e sensibilidade.
- **CRM-SEARCH-003 — Fuzzy:** tolerância a acento, abreviação e pequenas diferenças.
- **CRM-SEARCH-004 — Facetas:** entidade, período, owner, status, carteira, canal e produto.
- **CRM-SEARCH-005 — Destaque:** mostrar trecho e motivo de correspondência.
- **CRM-SEARCH-006 — Busca por identificadores:** CNPJ, código/loja, pedido, nota, telefone, e-mail e part number.
- **CRM-SEARCH-007 — Views salvas:** filtros, colunas, ordenação, agrupamento e compartilhamento.
- **CRM-SEARCH-008 — Favoritos:** preservar integração com favoritos da Minha DELPI e favoritos internos quando fizer sentido.
- **CRM-SEARCH-009 — Recentes:** últimos registros e pesquisas.
- **CRM-SEARCH-010 — Ações em lote:** somente para operações autorizadas e com preview.
- **CRM-SEARCH-011 — Command palette:** navegação e ações rápidas por teclado.
- **CRM-SEARCH-012 — Exportação:** respeitar view, escopo, limite e auditoria.
- **CRM-SEARCH-013 — Reindexação:** operação segura, observável e sem indisponibilidade crítica.
- **CRM-SEARCH-014 — Conteúdo externo:** não indexar corpo integral sem política e acesso compatíveis.

---

### 8.39 Administração funcional e customização

**Situação atual:** Parcial; já há administração de equipe, grupos e carteiras.

**Objetivo:** permitir evolução do processo sem alterações de código para toda regra simples.

#### Funcionalidades obrigatórias

- **CRM-ADM-001 — Pipelines:** criar, ordenar, ativar, arquivar e versionar.
- **CRM-ADM-002 — Etapas:** probabilidade, SLA, campos e transições.
- **CRM-ADM-003 — Motivos:** perda, desqualificação, adiamento, cancelamento e resolução.
- **CRM-ADM-004 — Campos personalizados:** texto, número, moeda, data, seleção, multiseleção, usuário, relação e booleano.
- **CRM-ADM-005 — Layouts:** seções e campos por entidade, pipeline e tipo.
- **CRM-ADM-006 — Campos obrigatórios:** por criação, etapa e encerramento.
- **CRM-ADM-007 — Validações:** regras declarativas seguras e mensagens em pt-BR.
- **CRM-ADM-008 — Catálogos:** segmentos, famílias, fontes, canais, tipos e tags.
- **CRM-ADM-009 — Calendários de negócio:** expediente, feriados, filial e fuso.
- **CRM-ADM-010 — Templates:** mensagens, documentos, tarefas, checklists e workflows.
- **CRM-ADM-011 — Regras de distribuição:** lead, carteira, fila e capacidade.
- **CRM-ADM-012 — Conectores:** configuração, escopos, status, subscriptions e credenciais por referência segura.
- **CRM-ADM-013 — Feature flags:** liberação por ambiente/grupo sem substituir RBAC.
- **CRM-ADM-014 — Auditoria de configuração:** before/after, autor, motivo e data.
- **CRM-ADM-015 — Preview de impacto:** quantidade de registros, automações e usuários afetados.
- **CRM-ADM-016 — Arquivamento:** impedir remoção destrutiva de configuração em uso.
- **CRM-ADM-017 — Import/export de configuração:** pacote versionado e validado entre ambientes.
- **CRM-ADM-018 — Ajuda contextual:** descrição, exemplo e efeito de cada parâmetro.

---

### 8.40 APIs, webhooks e central de integrações

**Situação atual:** Parcial; há BFF e integrações específicas, mas não uma central completa.

**Objetivo:** integrar o CRM ao ecossistema de forma estável, observável e desacoplada.

#### Funcionalidades obrigatórias

- **CRM-INT-001 — APIs versionadas:** contratos por domínio, OpenAPI e depreciação controlada.
- **CRM-INT-002 — Autenticação:** JWT da plataforma para usuários e credenciais técnicas dedicadas para jobs quando aprovadas.
- **CRM-INT-003 — Autorização:** escopo de dados e ação em todos os endpoints.
- **CRM-INT-004 — Idempotency-Key:** obrigatório em criação/efeito externo sensível.
- **CRM-INT-005 — Concorrência:** `version`/`If-Match` em updates críticos.
- **CRM-INT-006 — Paginação:** cursor ou page/page_size documentados.
- **CRM-INT-007 — Filtros:** explícitos, indexados e sem ampliação de escopo.
- **CRM-INT-008 — Erros:** códigos estáveis, recuperabilidade e correlation ID.
- **CRM-INT-009 — Rate limit:** por cliente, rota e integração.
- **CRM-INT-010 — Webhooks de saída:** eventos selecionáveis, assinatura, retry e dead-letter.
- **CRM-INT-011 — Webhooks de entrada:** validação de assinatura, timestamp, replay protection e idempotência.
- **CRM-INT-012 — Subscriptions:** criação, renovação, expiração e revogação.
- **CRM-INT-013 — Sync cursor:** estado por conector, recurso e usuário/tenant.
- **CRM-INT-014 — Backfill:** janela controlada e retomável.
- **CRM-INT-015 — Reconciliação:** job periódico para corrigir perda de webhook.
- **CRM-INT-016 — Mapeamento:** IDs externos, campos e transformações versionadas.
- **CRM-INT-017 — Monitor de saúde:** conectado, degradado, expirando, bloqueado e falho.
- **CRM-INT-018 — Fila de erro:** detalhe, tentativa, próxima execução e replay.
- **CRM-INT-019 — Secrets:** cofre e rotação; nunca retornar valor ao frontend.
- **CRM-INT-020 — Sandbox:** ambiente/test mode para conectores que suportem.
- **CRM-INT-021 — Contrato ERP:** manter leitura de produtos, clientes, pedidos, notas, faturamento e demais dados pela API DELPI.
- **CRM-INT-022 — Comandos ao ERP:** operações transacionais terão APIs específicas, validação, idempotência e confirmação.
- **CRM-INT-023 — Eventos de domínio:** outbox pós-commit e consumidores idempotentes.
- **CRM-INT-024 — Catálogo:** documentação de dono, dados, SLA, limites e contato técnico de cada integração.

---

### 8.41 Privacidade, LGPD, segurança e auditoria

**Situação atual:** Parcial; autenticação, RBAC e auditoria já fornecem base.

**Objetivo:** garantir uso legítimo, seguro e rastreável dos dados comerciais e de comunicação.

#### Funcionalidades obrigatórias

- **CRM-GOV-001 — Inventário de dados:** entidade, campo, finalidade, origem, classificação e retenção.
- **CRM-GOV-002 — Base legal:** registrar quando aplicável por contato, finalidade e canal.
- **CRM-GOV-003 — Consentimento:** prova, versão, timestamp, origem e revogação.
- **CRM-GOV-004 — Preferências:** granularidade por canal e finalidade.
- **CRM-GOV-005 — Direitos do titular:** localizar, exportar, corrigir, anonimizar ou excluir conforme política e obrigação legal.
- **CRM-GOV-006 — Legal hold:** bloquear descarte quando houver obrigação formal.
- **CRM-GOV-007 — Minimização:** coletar apenas dados necessários.
- **CRM-GOV-008 — Retenção:** política por entidade, canal, conteúdo e sistema de origem.
- **CRM-GOV-009 — Criptografia:** TLS em trânsito e criptografia em repouso para dados sensíveis/tokens.
- **CRM-GOV-010 — Field-level protection:** mascarar campos e restringir conteúdo.
- **CRM-GOV-011 — Segregação:** isolamento por ambiente, tenant lógico quando aplicável e privilégio.
- **CRM-GOV-012 — Auditoria de escrita:** ator, ação, entidade, ID, before/after, data, IP/contexto e correlation ID.
- **CRM-GOV-013 — Auditoria de leitura:** mensagens, transcrições, gravações, exportações e dados classificados.
- **CRM-GOV-014 — Logs seguros:** não registrar token, senha, secret ou corpo sensível desnecessário.
- **CRM-GOV-015 — Download/export:** limite, justificativa, trilha e proteção.
- **CRM-GOV-016 — Malware/DLP:** anexos e compartilhamentos.
- **CRM-GOV-017 — CSRF/XSS/SSRF/injection:** proteções aplicadas nos adapters, APIs e renderização.
- **CRM-GOV-018 — Sanitização:** HTML externo tratado como não confiável.
- **CRM-GOV-019 — Webhook security:** assinatura, replay e validação.
- **CRM-GOV-020 — Break-glass:** acesso emergencial limitado, justificado, expirável e alertado.
- **CRM-GOV-021 — Revisão de acesso:** relatórios periódicos de permissões, conexões e tokens.
- **CRM-GOV-022 — Incidente:** capacidade de revogar conectores, pausar automações e preservar evidência.
- **CRM-GOV-023 — IA segura:** política de dados, provedores, retenção e uso para treinamento.
- **CRM-GOV-024 — Conteúdo Microsoft 365:** respeitar consentimento, políticas administrativas, retenção e escopo de recurso.
- **CRM-GOV-025 — Auditoria imutável:** proteção contra alteração por usuários funcionais.

---

### 8.42 Experiência móvel, acessibilidade e usabilidade

**Situação atual:** Parcial; MFE web responsivo deve evoluir.

**Objetivo:** permitir uso eficaz em escritório, visita e deslocamento.

#### Funcionalidades obrigatórias

- **CRM-UX-001 — Responsividade:** desktop, tablet e celular.
- **CRM-UX-002 — PWA:** instalação opcional, push e cache seguro quando aprovado.
- **CRM-UX-003 — Ações rápidas:** ligar, enviar mensagem, registrar visita, criar tarefa, nota e oportunidade.
- **CRM-UX-004 — Offline controlado:** rascunhos/notas e fila de sincronização para cenários definidos.
- **CRM-UX-005 — Conflito de sync:** informar e permitir resolução.
- **CRM-UX-006 — Voz:** ditado de nota e comando assistido.
- **CRM-UX-007 — Câmera:** anexar foto/documento com consentimento e classificação.
- **CRM-UX-008 — Localização:** opcional, justificada e nunca usada silenciosamente.
- **CRM-UX-009 — Acessibilidade:** alvo WCAG 2.2 AA, teclado, foco, contraste, labels e leitor de tela.
- **CRM-UX-010 — Performance percebida:** skeleton, carregamento progressivo e feedback.
- **CRM-UX-011 — Estados claros:** vazio, carregando, parcial, erro, offline e sem permissão.
- **CRM-UX-012 — Ajuda contextual:** glossário, metodologia, tutorial e exemplos.
- **CRM-UX-013 — Consistência:** componentes compartilhados do `plugin-ui`, sem CSS espelho desnecessário.
- **CRM-UX-014 — pt-BR:** linguagem de negócio clara; datas, moedas e timezone corretos.
- **CRM-UX-015 — Atalhos:** teclado e command palette para usuários intensivos.
- **CRM-UX-016 — Sem aba/painel desnecessário:** priorizar leitura e ação, evitando chrome que atrapalhe o conteúdo.

---

### 8.43 Observabilidade, operação e confiabilidade

**Situação atual:** Parcial; deverá ser ampliada para o novo domínio e conectores.

**Objetivo:** operar o CRM com diagnóstico rápido e falhas controladas.

#### Funcionalidades obrigatórias

- **CRM-OPS-001 — Health/readiness:** aplicação, banco, filas e dependências críticas.
- **CRM-OPS-002 — Logs estruturados:** correlation ID, operação, entidade e duração sem dados sensíveis.
- **CRM-OPS-003 — Métricas:** latência, throughput, erro, cache, fila, retry e conector.
- **CRM-OPS-004 — Tracing:** requisição Portal → commercial-api → API DELPI/provedor.
- **CRM-OPS-005 — SLOs:** disponibilidade, latência e freshness por capacidade.
- **CRM-OPS-006 — Alertas:** erro, fila crescendo, webhook parado, token expirando, subscription vencendo e taxa limite.
- **CRM-OPS-007 — Circuit breaker:** dependência externa degradada não derrubará todo o CRM.
- **CRM-OPS-008 — Timeout:** por integração, com mensagem e fallback adequados.
- **CRM-OPS-009 — Retry/backoff:** somente para operações seguras/idempotentes.
- **CRM-OPS-010 — Dead-letter/replay:** operação administrável e auditada.
- **CRM-OPS-011 — Dashboard de conectores:** status, último sucesso, cursor, falha e próxima tentativa.
- **CRM-OPS-012 — Freshness por dado:** mostrar atraso de ERP, canal ou analytics.
- **CRM-OPS-013 — Backup:** banco, configuração e anexos conforme política.
- **CRM-OPS-014 — Restauração:** testes periódicos e RPO/RTO definidos.
- **CRM-OPS-015 — Deploy seguro:** migrations compatíveis, feature flags, rollback e smoke tests.
- **CRM-OPS-016 — Capacity:** dimensionar volume de eventos, mensagens, campanhas e anexos.
- **CRM-OPS-017 — Arquivamento:** mover dados frios sem quebrar auditoria/pesquisa autorizada.
- **CRM-OPS-018 — Runbooks:** incidentes de auth, ERP, Microsoft 365, mensageria, filas e IA.

---

### 8.44 Ajuda, onboarding e adoção

**Situação atual:** Parcial; o Portal já possui padrões de ajuda e glossário em várias telas.

**Objetivo:** garantir que usuários entendam processo, dados e indicadores.

#### Funcionalidades obrigatórias

- **CRM-HELP-001 — Tour inicial:** por persona e escopo.
- **CRM-HELP-002 — Checklists de adoção:** conectar canal, configurar perfil, importar base e criar primeira oportunidade.
- **CRM-HELP-003 — Ajuda contextual:** conceito, fonte, regra e exemplo ao lado da função.
- **CRM-HELP-004 — Glossário:** lead, oportunidade, pipeline, ROL, carteira, forecast, score e demais termos.
- **CRM-HELP-005 — Metodologia de KPI:** link direto no indicador.
- **CRM-HELP-006 — Central de ajuda:** busca por tarefa e área.
- **CRM-HELP-007 — Playbooks:** prospecção, reunião, proposta, reativação e handoff.
- **CRM-HELP-007A — Scripts de vendas:** roteiros versionados por etapa, segmento e canal, consumíveis na atividade.
- **CRM-HELP-008 — Novidades:** changelog por versão e impacto.
- **CRM-HELP-009 — Feedback:** reportar dúvida, erro e sugestão com contexto técnico.
- **CRM-HELP-010 — Telemetria de adoção:** uso de funcionalidades, abandonos e barreiras, sem vigilância indevida.
- **CRM-HELP-011 — Conteúdo administrável:** versão, owner, aprovação e validade.
- **CRM-HELP-012 — Ambiente de treinamento:** dados fictícios ou sandbox quando necessário.
- **CRM-HELP-013 — Role-play:** cenários de treinamento com script, feedback e registro opcional autorizado.

---

### 8.45 Rituais comerciais e coaching de gestão

**Situação atual:** Novo — gap preenchido a partir do benchmark Agendor ([rituais de vendas](https://www.agendor.com.br/blog/rituais-de-vendas/), [soluções](https://www.agendor.com.br/solucoes)).

**Objetivo:** embutir disciplina e rituais de alta performance no fluxo diário, sem transformar o CRM em controle de bem-estar ou ranking tóxico.

#### Funcionalidades obrigatórias

- **CRM-RIT-001 — Preparar o dia seguinte:** fluxo guiado no fim do expediente.
- **CRM-RIT-002 — Lista do dia:** checks, priorização e fechamento.
- **CRM-RIT-003 — Segmentar antes de prospectar:** fila agrupada por critérios comerciais.
- **CRM-RIT-004 — Script por perto:** roteiro na mesma tela da abordagem.
- **CRM-RIT-005 — Histórico antes do contato:** briefing recomendado ou obrigatório por política.
- **CRM-RIT-006 — Atualizar após abordagem:** outcome + próximo passo como gate de conclusão.
- **CRM-RIT-007 — Propósito × meta (opcional):** meta comercial ligada a objetivo pessoal privado do vendedor.
- **CRM-RIT-008 — Reunião semanal de gestão:** agenda gerada do sumário + forecast.
- **CRM-RIT-009 — 1-on-1:** pauta, feedback mútuo, acordos e histórico.
- **CRM-RIT-010 — Role-play:** cenários e feedback estruturado.
- **CRM-RIT-011 — SLA marketing–vendas:** artefato/reunião recorrente com critérios MQL/SQL e qualidade de handoff.
- **CRM-RIT-012 — Configuração por equipe:** rituais recomendados vs. obrigatórios, versionados.
- **CRM-RIT-013 — Fora de escopo:** Pomodoro, pausas de bem-estar e cronometragem de foco pessoal.

#### Regras críticas

- Aderência a rituais alimenta coaching e qualidade de dados, não “score de pessoa” opaco.
- Metas pessoais motivacionais são privadas por padrão.
- Fluxo inteligente e scripts sugerem; não enviam nem fecham negócio sem política/confirmação.

---

## 9. Funcionalidades transversais por entidade

Toda entidade principal do CRM deverá, quando aplicável, oferecer:

1. ID interno estável e referências externas;
2. owner, equipe, carteira, filial e escopo;
3. status e histórico de status;
4. tags e campos personalizados;
5. notas, comentários e menções;
6. tarefas, atividades e reuniões;
7. anexos e documentos;
8. timeline de eventos;
9. auditoria de criação, atualização, leitura sensível e exportação;
10. busca, filtros, views e exportação autorizada;
11. API e eventos de domínio;
12. soft delete/arquivamento conforme política;
13. versionamento/concorrência em mudanças críticas;
14. link profundo estável no Portal;
15. métricas de data de criação, última ação, aging e freshness;
16. recursos de IA apenas com escopo, fontes e confirmação adequados.


## 10. Modelo de dados funcional alvo

O modelo deverá evoluir de forma compatível com as tabelas atuais. Os nomes finais serão definidos no desenho técnico, mas o domínio precisa representar, no mínimo, as seguintes entidades.

### 10.1 Identidade comercial e escopo

| Entidade | Responsabilidade |
|---|---|
| `commercial_user_profile` | Preferências e identidade funcional do usuário no CRM. |
| `seller_portfolio` | Carteira comercial já existente. |
| `seller_portfolio_member` | Usuários e responsabilidades na carteira. |
| `portfolio_coverage` | Cobertura principal, secundária e temporária. |
| `commercial_group` | Grupo operacional, separado de RBAC. |
| `delegated_access` | Cobertura temporária e expirável. |
| `external_identity_link` | Mapeamento entre usuário Minha DELPI e identidade externa. |

### 10.2 Empresas e contatos

| Entidade | Responsabilidade |
|---|---|
| `account` | Empresa prospect ou cliente, com ID interno estável. |
| `account_external_ref` | Código/loja ERP, CNPJ, domínio e IDs de sistemas. |
| `account_relation` | Matriz, filial, grupo econômico e outras relações. |
| `contact` | Pessoa canônica. |
| `contact_account_role` | Vínculo e papel do contato em uma empresa. |
| `contact_point` | E-mail, telefone, mensageria e preferência. |
| `contact_external_ref` | IDs externos de Microsoft 365, mensageria e outros. |
| `consent` | Base legal, finalidade, canal, prova, vigência e revogação. |
| `suppression_entry` | Bloqueio de comunicação por canal/finalidade. |
| `account_plan` | Plano de conta. |
| `account_health_snapshot` | Score, fatores, data e versão da metodologia. |

### 10.3 Marketing e aquisição

| Entidade | Responsabilidade |
|---|---|
| `lead` | Registro pré-qualificação. |
| `lead_source` | Origem e taxonomia. |
| `lead_score` | Pontuação atual por dimensão. |
| `lead_score_event` | Explicação de cada mudança. |
| `segment` | Segmento estático ou dinâmico. |
| `segment_version` | Regra publicada e histórico. |
| `segment_member_snapshot` | Audiência congelada. |
| `campaign` | Campanha e orçamento. |
| `campaign_member` | Participação e estado por pessoa. |
| `marketing_asset` | Template, página, formulário e conteúdo. |
| `landing_page` | Página e versão publicada. |
| `form` | Definição do formulário. |
| `form_submission` | Conversão e prova de campos/consentimento. |
| `web_identity` | Identidade anônima/known de tracking. |
| `web_event` | Evento de comportamento digital. |
| `journey` | Automação de marketing. |
| `journey_version` | Grafo publicado. |
| `journey_enrollment` | Instância por lead/contato. |
| `attribution_touch` | Toque de origem/influência. |
| `marketing_cost` | Custo importado por campanha/canal. |

### 10.4 Vendas

| Entidade | Responsabilidade |
|---|---|
| `pipeline` | Processo comercial configurável. |
| `pipeline_stage` | Etapa, probabilidade, SLA e regras. |
| `opportunity` | Negócio nativo do CRM. |
| `opportunity_stage_history` | Aging e transições. |
| `opportunity_contact_role` | Contatos e papel no negócio. |
| `opportunity_team_member` | Colaboradores e participação. |
| `opportunity_item` | Produto/aplicação/volume estimado. |
| `opportunity_competitor` | Concorrência associada. |
| `qualification_answer` | Checklist e critérios. |
| `quote` | Proposta/cotação comercial. |
| `quote_version` | Snapshot de versão. |
| `quote_item` | Itens e condições. |
| `approval_request` | Fluxo de aprovação. |
| `approval_decision` | Decisão e justificativa. |
| `forecast_submission` | Forecast por usuário/equipe/período. |
| `forecast_snapshot` | Visão congelada por ciclo. |
| `goal_reference` | Referência à fonte oficial de meta. |
| `sample_request` | Amostra/protótipo e acompanhamento. |
| `technical_feasibility` | Parecer e pendências técnicas. |

### 10.5 Execução e colaboração

| Entidade | Responsabilidade |
|---|---|
| `task` | Base atual evoluída. |
| `task_assignee` | Responsáveis usuários. |
| `task_assignee_group` | Responsáveis por grupo. |
| `task_checklist_item` | Checklist. |
| `task_recurrence` | Regra de recorrência. |
| `activity` | Registro de atividade concluída/manual. |
| `meeting` | Reunião/visita do CRM. |
| `meeting_participant` | Participantes e respostas. |
| `interaction_room` | Sala interna existente. |
| `interaction_room_message` | Mensagem interna existente. |
| `mention` | Menções em mensagens/comentários. |
| `case` | Solicitação comercial. |
| `case_status_history` | SLA e transições. |
| `comment` | Comentário reutilizável por entidade. |
| `attachment` | Metadados de arquivo e classificação. |
| `document_version` | Versão e referência de documento. |

### 10.6 Comunicação e conectores

| Entidade | Responsabilidade |
|---|---|
| `conversation` | Thread externa normalizada. |
| `communication` | E-mail, mensagem, ligação ou evento normalizado. |
| `communication_participant` | Remetente/destinatários/participantes. |
| `external_message_ref` | ID no sistema de origem. |
| `call_record` | Metadados de chamada. |
| `transcript` | Referência/conteúdo autorizado e metadados. |
| `channel_connection` | Conexão de usuário, caixa, número, equipe ou tenant. |
| `integration_subscription` | Subscription/webhook e expiração. |
| `sync_cursor` | Cursor/delta/backfill por recurso. |
| `webhook_delivery` | Entrega, tentativas e estado. |
| `integration_dead_letter` | Falhas aguardando replay. |
| `message_template` | Template por canal. |
| `sequence` | Cadência de prospecção. |
| `sequence_version` | Versão publicada. |
| `sequence_enrollment` | Execução por contato/lead. |
| `sales_script` | Roteiro de vendas/qualificação versionado. |
| `sales_ritual` | Definição de ritual (fim de dia, sumário, 1-on-1, etc.). |
| `ritual_completion` | Execução/check de ritual por usuário/período. |
| `coaching_one_on_one` | Registro de 1-on-1 e acordos. |
| `deal_freeze` | Congelamento de oportunidade com motivo e retorno. |

### 10.7 Governança, analytics e IA

| Entidade | Responsabilidade |
|---|---|
| `audit_log` | Trilha imutável. |
| `entity_change` | Before/after quando necessário. |
| `data_export_job` | Exportação e justificativa. |
| `retention_policy` | Política por tipo de dado. |
| `metric_definition` | Metodologia e versão de KPI. |
| `metric_snapshot` | Valor calculado e freshness. |
| `automation` | Workflow comercial. |
| `automation_version` | Definição publicada. |
| `automation_run` | Instância e estado. |
| `automation_step_run` | Etapas, decisões e erros. |
| `ai_interaction` | Uso do AI Gateway e auditoria. |
| `ai_feedback` | Avaliação/correção do usuário. |
| `notification_outbox` | Eventos de notificação pós-commit. |
| `domain_event_outbox` | Eventos de integração confiáveis. |

### 10.8 Regras de modelagem

1. IDs internos não dependerão de códigos mutáveis do ERP.
2. Referências externas deverão ser únicas dentro do sistema de origem.
3. Conteúdo bruto de canal externo será separado de sua representação normalizada.
4. A entidade `communication` deverá aceitar novos canais sem alteração estrutural ampla.
5. Toda entidade temporal sensível terá timezone e timestamp UTC, com apresentação local.
6. Estados e transições importantes terão histórico próprio, não apenas `updated_at`.
7. Campos personalizados não deverão virar colunas arbitrárias por cliente; usar modelo tipado, indexação seletiva e validação.
8. Dados analíticos derivados deverão registrar versão da metodologia e período.
9. Soft delete não substituirá política formal de retenção/anonimização.
10. Não haverá foreign key direta para tabelas internas de outros bounded contexts quando um contrato/evento for suficiente.

---

## 11. Arquitetura funcional alvo

### 11.1 Visão macro

```text
Usuário
  ↓
Gateway Minha DELPI
  ↓
Portal / shell
  ↓
plugins/commercial
  ↓
commercial-api
  ├── PostgreSQL CRM
  ├── Object storage / documentos
  ├── Search index permissionado
  ├── Outbox / filas / workers
  ├── Socket.IO / eventos da plataforma
  ├── Core API (governança, notificações e visão autorizada)
  ├── API DELPI (ERP e integrações operacionais)
  ├── Microsoft 365 adapter
  ├── Messaging adapter
  ├── Telephony adapter
  ├── Marketing delivery adapter
  ├── Web tracking/collector
  ├── Signature adapter
  └── AI Gateway
```

### 11.2 Módulos internos recomendados no `commercial-api`

```text
commercial_app/
  domain/
    accounts/
    contacts/
    leads/
    marketing/
    campaigns/
    journeys/
    pipelines/
    opportunities/
    quotes/
    tasks/
    meetings/
    communications/
    collaboration/
    portfolios/
    orders/
    customer_success/
    forecasting/
    analytics/
    automation/
    governance/
    ai/
    integrations/

  application/
    use_cases/
    services/
    policies/
    validators/
    event_handlers/

  interface/
    http/
    webhooks/
    workers/
    realtime/

  infrastructure/
    persistence/
    messaging/
    search/
    storage/
    microsoft_graph/
    whatsapp/
    telephony/
    email_delivery/
    erp_gateway/
    ai_gateway/
    observability/
```

A estrutura final deverá seguir as convenções reais do repositório, mas a separação de bounded contexts é obrigatória para evitar um pacote monolítico de CRM.

### 11.3 Padrão de integração Microsoft 365

```text
Usuário autenticado na Minha DELPI
  ↓
Conecta conta Microsoft por OAuth aprovado
  ↓
commercial-api armazena referência/token cifrado
  ↓
Cria subscriptions autorizadas
  ↓
Webhook recebe mudança e valida assinatura/clientState
  ↓
Fila normaliza evento
  ↓
Adapter consulta recurso necessário
  ↓
Policy verifica escopo e vínculo
  ↓
Persistência idempotente
  ↓
Evento pós-commit atualiza timeline/Portal
```

Pontos obrigatórios:

- autenticação Keycloak e autorização Microsoft são fluxos distintos;
- `keycloak_user_id`, UPN/e-mail e `entra_user_id` deverão ser mapeados explicitamente;
- delegated access será preferido para conteúdo pessoal do usuário;
- Resource-Specific Consent será preferido quando aplicável a recurso específico;
- application permissions serão exceção administrativa;
- subscriptions deverão ter job de renovação;
- webhooks não serão considerados garantia única: haverá reconciliação;
- tokens e certificados ficarão fora do MFE;
- o conteúdo será sanitizado, classificado e limitado por retenção.

### 11.4 Padrão de comunicação omnicanal

```text
Canal externo
  ↓ webhook/polling
Connector adapter
  ↓
External event envelope
  ↓
Idempotency + identity resolution
  ↓
Conversation / Communication
  ↓
Association policy
  ↓
Timeline + notification + automation
```

O sistema deverá manter:

- ID externo e ID interno;
- estado de entrega;
- direção;
- participantes;
- conteúdo e anexos conforme política;
- entidade vinculada;
- origem da associação automática/manual;
- cursor e última sincronização;
- trilha de edição/exclusão.

---

## 12. Matriz de sistemas de registro

| Dado | Sistema de registro | Uso no CRM |
|---|---|---|
| Login e sessão SSO | Keycloak | Identificar usuário. |
| Permissões, roles, grupos de plataforma e apps | Core API | Autorizar acesso funcional e rotas. |
| Carteiras e escopo do Portal Comercial | `commercial-api` | Filtrar contas, ações e analytics. |
| Leads e prospects | `commercial-api` | Fonte oficial. |
| Contatos comerciais locais e consentimentos | `commercial-api` | Fonte oficial, com referências externas. |
| Pipelines e oportunidades nativas | `commercial-api` | Fonte oficial de pré-venda. |
| Tarefas, reuniões CRM e cadências | `commercial-api` | Fonte oficial da execução comercial. |
| Campanhas, segmentos, scoring e jornadas | `commercial-api` | Fonte oficial do marketing no CRM. |
| Conta 360 agregada | `commercial-api` | Read model composto. |
| Cadastro transacional do cliente | ERP via API DELPI | Fonte oficial após cadastro. |
| Produtos e famílias oficiais | ERP via API DELPI | Consulta e referência. |
| Estoque e disponibilidade | ERP/API operacional | Consulta, sem cópia como verdade. |
| Pedido de venda | ERP | Referência e status no CRM. |
| Nota fiscal e faturamento | ERP | Referência e analytics autorizados. |
| Dados financeiros oficiais | ERP/financeiro | Consulta restrita e homologada. |
| E-mail e calendário brutos | Microsoft 365 | Fonte do artefato; CRM armazena referência/normalização conforme política. |
| Chats/canais/reuniões brutos | Microsoft Teams | Fonte do artefato; CRM armazena vínculo e conteúdo permitido. |
| Mensagens de canal externo | Provedor oficial | Fonte de entrega/conversa; CRM normaliza. |
| Gravação de ligação | Provedor de telefonia | Fonte do artefato; CRM referencia ou copia conforme política. |
| Documentos do CRM | Storage autorizado | Conteúdo; metadados no `commercial-api`. |
| Metas corporativas | Serviço/indicador homologado | Referência, não duplicação. |
| Execução de modelo de IA | AI Gateway | Modelo/política; resultado auditado no CRM. |

---

## 13. Eventos de domínio e tempo real

### 13.1 Eventos mínimos

```text
crm.account.created
crm.account.updated
crm.account.merged
crm.contact.created
crm.contact.updated
crm.contact.consent_changed
crm.lead.created
crm.lead.assigned
crm.lead.qualified
crm.lead.converted
crm.lead.disqualified
crm.segment.refreshed
crm.campaign.published
crm.campaign.started
crm.campaign.completed
crm.form.submitted
crm.journey.enrolled
crm.journey.completed
crm.opportunity.created
crm.opportunity.stage_changed
crm.opportunity.owner_changed
crm.opportunity.won
crm.opportunity.lost
crm.quote.created
crm.quote.approval_requested
crm.quote.approved
crm.quote.sent
crm.quote.accepted
crm.task.created
crm.task.assigned
crm.task.due_soon
crm.task.overdue
crm.task.completed
crm.meeting.created
crm.meeting.completed
crm.communication.received
crm.communication.sent
crm.communication.linked
crm.teams.transcript_available
crm.order.exception_detected
crm.order.confirmation_requested
crm.order.confirmed
crm.case.created
crm.case.sla_breached
crm.forecast.submitted
crm.integration.degraded
crm.integration.recovered
crm.ai.suggestion_created
```

### 13.2 Regras de evento

1. Eventos serão coletados no caso de uso e publicados após commit.
2. Consumidores serão idempotentes.
3. Eventos não carregarão secrets nem payload operacional completo desnecessário.
4. Dados sensíveis serão reduzidos a IDs e metadados.
5. O Portal receberá apenas eventos relevantes ao usuário.
6. Mudança de acesso deverá invalidar caches e fechar/atualizar conexões.
7. Eventos externos terão envelope com provider, external ID, timestamp, event ID e assinatura validada.
8. Falha de consumidor não reverterá a transação original; será tratada por retry/dead-letter.

---

## 14. Modelo de permissões proposto

### 14.1 Permissões atuais preservadas

| Código | Uso |
|---|---|
| `commercial.access` | Acesso ao Portal Comercial e capacidades operacionais usuais dentro do escopo. |
| `commercial.manage` | Administração funcional e visão ampliada. |
| `commercial.billing.notify` | Destinatário específico de notificações de faturamento. |

### 14.2 Novas permissões específicas somente quando justificadas

O catálogo não deverá ser fragmentado por tela. Permissões adicionais deverão representar efeitos estreitos, irreversíveis, externos ou altamente sensíveis. Proposta inicial para avaliação:

| Código proposto | Justificativa |
|---|---|
| `commercial.marketing.send` | Autorizar envio massivo externo, sem conceder administração total. |
| `commercial.integrations.manage` | Configurar conexões, consentimentos administrativos, subscriptions e secrets por referência. |
| `commercial.communications.tenant_read` | Acesso excepcional a conteúdo corporativo em escopo de aplicação/tenant; nunca concedido por padrão. |
| `commercial.data.export_sensitive` | Exportar conteúdo/dados classificados. |
| `commercial.data.erase` | Executar anonimização/exclusão governada. |
| `commercial.approvals.financial` | Aprovar exceções financeiras/comerciais conforme alçada. |
| `commercial.ai.admin` | Configurar políticas, modelos e limites, sem significar acesso a todos os dados. |

Antes de incluir qualquer código no manifesto, a equipe deverá responder:

1. A capacidade pode usar `commercial.access` com escopo de registro?
2. É administração ampla e pode usar `commercial.manage`?
3. A ação produz efeito externo, massivo, irreversível ou sensível que justifica código próprio?
4. O código concede apenas o efeito necessário e não amplia silenciosamente o escopo de dados?
5. O PR atualiza manifesto, documentação, testes e matriz de roles?

### 14.3 Políticas complementares

Além dos permission codes, o `commercial-api` deverá avaliar:

- membership de carteira;
- owner e equipe do registro;
- filial/unidade;
- participação/menção;
- alçada de aprovação;
- consentimento do titular;
- autorização do conector externo;
- sensibilidade do campo/conteúdo;
- delegação temporária;
- estado do registro;
- finalidade da ação.

---

## 15. Requisitos não funcionais

### 15.1 Segurança

- OIDC/JWT validado por issuer, audience, assinatura e expiração.
- Nenhum secret em `VITE_*`, localStorage ou bundle.
- Tokens de integração cifrados e rotacionáveis.
- Sanitização de HTML, URLs e anexos externos.
- Proteção contra CSRF, XSS, SSRF, injection, upload malicioso e replay.
- Rate limit por usuário, aplicação, rota e webhook.
- Content Security Policy compatível com o MFE e conectores.
- Auditoria de operações sensíveis.
- Princípio de menor privilégio para Graph e demais provedores.

### 15.2 Desempenho

Metas iniciais a serem homologadas por ambiente:

- p95 de leitura local simples inferior a 500 ms no backend, sem incluir dependência externa;
- p95 de composição Conta 360 inferior a 2,5 s com carregamento progressivo;
- primeira resposta visual do MFE sem bloquear toda a página por uma integração lenta;
- listagens paginadas e virtualização quando necessário;
- busca global com resposta interativa sob carga prevista;
- campanhas e backfills executados por workers, nunca em requisição síncrona longa.

### 15.3 Disponibilidade e resiliência

- Degradação parcial: falha do canal externo não indisponibiliza cadastro, tarefas ou pipeline.
- Timeouts explícitos e fallback de dado indisponível.
- Circuit breaker em dependências.
- Retry somente em operações seguras.
- Outbox para eventos e notificações.
- Dead-letter e replay.
- Backups e teste de restauração.
- Health/readiness por serviço.

### 15.4 Escalabilidade

- Particionamento/arquivamento de eventos e comunicações conforme volume.
- Índices orientados a consultas reais.
- Search engine para conteúdo e filtros que não devem sobrecarregar o banco transacional.
- Workers escaláveis horizontalmente.
- Controle de concorrência por registro.
- Limites de backfill, campanha e exportação.
- Storage de arquivos separado do banco relacional.

### 15.5 Acessibilidade e compatibilidade

- WCAG 2.2 AA como alvo.
- Navegação por teclado e foco visível.
- Compatibilidade com navegadores corporativos suportados.
- Layout responsivo.
- pt-BR como idioma principal.
- Timezone `America/Sao_Paulo` na apresentação padrão, com persistência UTC.

### 15.6 Observabilidade

- correlation ID de ponta a ponta;
- logs estruturados e sem secrets;
- métricas de aplicação, domínio e integração;
- tracing entre `commercial-api`, API DELPI e provedores;
- dashboard de freshness;
- alertas de subscription/token/fila;
- runbooks e owner por serviço.

### 15.7 Testabilidade

- testes unitários de domínio e policies;
- testes de integração de repositórios e adapters;
- contract tests entre MFE, `commercial-api`, API DELPI e conectores;
- mocks/fixtures de webhooks;
- testes de idempotência e concorrência;
- testes de autorização negativos;
- smoke tests por rota crítica;
- testes E2E das jornadas principais;
- testes de carga para campanhas, busca e ingestão de mensagens;
- avaliação contínua de IA com conjunto de casos controlado.

---

## 16. Jornadas de aceite prioritárias

### 16.1 Lead digital até venda

1. Visitante converte em formulário com consentimento.
2. CRM cria ou atualiza lead, origem e campanha.
3. Eventos de site alteram score.
4. Ao atingir regra, lead entra em fila comercial.
5. Vendedor aceita e executa cadência.
6. Lead é qualificado e convertido em empresa, contato e oportunidade.
7. Oportunidade percorre pipeline com tarefas e reuniões.
8. Proposta é criada, aprovada, enviada e aceita.
9. O sistema transacional recebe o handoff.
10. Pedido e faturamento retornam à Conta 360.
11. Analytics liga campanha, lead, oportunidade e receita.

### 16.2 Reativação de cliente

1. Segmento identifica clientes sem compra pelo período homologado.
2. Marketing cria campanha/cadência com exclusões e consentimento.
3. Resposta é vinculada ao cliente.
4. Vendedor recebe tarefa e briefing.
5. Nova oportunidade é criada com origem “reativação”.
6. Resultado atualiza status e métricas de reativação.

### 16.3 Reunião via Teams

1. Usuário conecta conta Microsoft com consentimento adequado.
2. Reunião é criada ou vinculada à oportunidade.
3. Participantes e agenda sincronizam.
4. Antes da reunião, CRM gera briefing.
5. Após o encontro, transcript é importado somente se existir e estiver autorizado.
6. IA propõe resumo e tarefas com referências.
7. Usuário revisa e confirma.
8. Timeline recebe reunião, decisões e tarefas.
9. Auditoria registra acesso e uso do artefato.

### 16.4 Continuidade de carteira

1. Responsável entra em férias.
2. Gestor cria delegação temporária com período e motivo.
3. Substituto visualiza contas, próximas ações e histórico autorizado.
4. Tarefas e mensagens continuam sendo tratadas.
5. Ao fim, delegação expira automaticamente.
6. Titular recebe resumo das ações executadas.

### 16.5 Pedido com divergência

1. CRM identifica pedido que exige confirmação.
2. Vendedor envia snapshot ao cliente.
3. Cliente informa divergência em data/quantidade.
4. CRM cria caso e tarefas para áreas responsáveis.
5. Comunicação e decisões ficam ligadas ao pedido.
6. Nova versão é enviada.
7. Confirmação final é registrada e, quando necessário, encaminhada ao ERP.

### 16.6 Gestão de forecast

1. Oportunidades possuem valor, data, categoria e próxima ação.
2. Vendedor revisa e submete forecast.
3. Gestor aplica ajuste separado e justificado.
4. Período é congelado em snapshot.
5. Ao final, sistema compara previsto e realizado.
6. Dashboard mostra acurácia e causas de variação.

### 16.7 Ritual diário do vendedor e sumário semanal

1. Vendedor abre Meu Dia e executa a lista do dia com checks.
2. Antes de cada contato, abre briefing e script da etapa.
3. Ao concluir a abordagem, registra outcome e próximo passo (gate).
4. O sistema sugere fluxo inteligente de próxima atividade; o usuário confirma.
5. No fim do expediente, ritual “preparar amanhã” fecha gaps sem próximo passo.
6. Na segunda-feira, gestor e time recebem sumário semanal (atividades, pipeline, forecast).
7. Reunião semanal e 1-on-1 usam o sumário como pauta; acordos viram tarefas.
8. Aderência a rituais aparece no dashboard de coaching sem ranking público tóxico.

---

## 17. Fases recomendadas de entrega

As fases abaixo organizam dependências. Elas não reduzem o escopo funcional final.

### Fase 0 — Consolidação da fundação existente

- inventário automatizado de rotas, entidades e telas;
- estabilização de Conta 360, tarefas, carteiras, pedidos, propostas, analytics e sala;
- contratos, erros, paginação, idempotência e observabilidade;
- revisão de manifest/RBAC;
- outbox e base de eventos;
- migrações e testes de autorização.

### Fase 1 — Núcleo CRM nativo

- `account` interno para prospect/cliente;
- contatos evoluídos e consentimentos;
- leads, qualificação, distribuição e conversão;
- pipelines, etapas, oportunidades, mapa de vendas e congelamento;
- tarefas recorrentes, checklists, fluxo inteligente, scripts e rituais diários;
- reuniões, agenda local e briefing pré-contato;
- timeline unificada;
- busca, views e administração básica.

### Fase 2 — Microsoft 365 e produtividade

- conexão de identidade;
- Outlook e calendário;
- Teams chats/canais vinculados;
- reuniões e transcrições autorizadas;
- cadências;
- mapa/rota de visitas (sem tracking contínuo);
- sumário semanal/mensal e rituais de gestão (1-on-1, reunião semanal);
- resumo/briefing assistidos;
- central de integrações e subscriptions.

### Fase 3 — Marketing e aquisição

- importação/higienização;
- segmentos;
- campanhas e e-mail marketing;
- landing pages, formulários e tracking;
- scoring;
- jornadas e automações;
- atribuição e analytics de marketing.

### Fase 4 — Omnicanal e colaboração externa

- WhatsApp corporativo e caixa compartilhada;
- web chat/chatbot;
- telefonia e transcrição;
- templates multicanal;
- SLAs de atendimento;
- casos comerciais.

### Fase 5 — Operação industrial avançada

- viabilidade técnica;
- amostras/protótipos;
- proposta nativa, aprovação e assinatura;
- confirmação de pedido;
- exceções e marcos de entrega;
- handoffs estruturados.

### Fase 6 — Gestão, customer success e IA avançada

- forecast, quotas e snapshots;
- plano/saúde de conta;
- reativação e expansão;
- next best action;
- consulta em linguagem natural;
- forecast assistido;
- analytics executivo completo.

---

## 18. Estratégia de evolução sem regressão

### 18.1 Preservação de ativos

As seguintes bases não deverão ser reimplementadas sem necessidade:

- seller portfolios e memberships;
- account contacts atuais, que serão migrados/evoluídos;
- tasks, assignees, groups e completed_by;
- attachments;
- user profiles e avatars;
- audit logs;
- interaction rooms, messages, reads, mentions e unread states;
- BFF de pedidos, faturamento, oportunidades operacionais e propostas existentes;
- filtros, exportações, ajuda e componentes visuais já homologados.

### 18.2 Migração de dados

- Criar migrações incrementais e imutáveis.
- Introduzir IDs internos canônicos antes de migrar referências.
- Popular `account_external_ref` com pares código/loja atuais.
- Migrar contatos preservando IDs ou criando tabela de correspondência.
- Associar tarefas atuais às novas entidades sem quebrar links.
- Preservar salas e mensagens internas como colaboração, não convertê-las em canal externo.
- Não transformar oportunidade do ERP automaticamente em oportunidade nativa sem regra de correspondência.
- Manter propostas externas como referências até que o fluxo nativo esteja homologado.
- Executar reconciliação e relatórios de divergência antes de retirar qualquer leitura legada.
- Proibir dual-read permanente; todo período de transição terá owner, prazo e critério de saída.

### 18.3 Compatibilidade de URL e manifesto

- Manter rotas atuais sempre que possível.
- Novas áreas poderão entrar como subrotas de `/apps/commercial`.
- Mudança estrutural de rotas ou permission codes exigirá nova versão do manifesto.
- Deep links antigos deverão redirecionar ou continuar válidos.
- Favoritos e notificações deverão preservar destino.

---

## 19. Critérios de aceite do produto completo

O CRM Minha DELPI será considerado funcionalmente completo quando:

- [ ] qualquer prospect puder ser criado antes de existir no ERP;
- [ ] um lead puder ser capturado, qualificado, distribuído e convertido sem perder origem;
- [ ] empresas e contatos tiverem identidade canônica, consentimento e deduplicação;
- [ ] múltiplos pipelines puderem ser configurados sem alteração de código;
- [ ] oportunidades nativas tiverem etapas, produtos, contatos, atividades, histórico e motivos de encerramento;
- [ ] propostas puderem ser versionadas, aprovadas, enviadas e vinculadas ao processo transacional;
- [ ] tarefas suportarem checklist, recorrência, SLA, grupos e reuniões;
- [ ] a Conta 360 reunir marketing, vendas, comunicação, pedidos e plano de conta;
- [ ] e-mails e agendas corporativos puderem ser vinculados com consentimento e auditoria;
- [ ] conversas e mensagens do Teams puderem ser vinculadas em escopo autorizado, sem leitura global por padrão;
- [ ] transcrições de reuniões disponíveis puderem gerar rascunho de ata e tarefas com confirmação;
- [ ] WhatsApp corporativo puder ser sincronizado em caixa compartilhada, com histórico e opt-in;
- [ ] campanhas, segmentos, formulários, scoring e jornadas estiverem operacionais;
- [ ] site e formulários alimentarem origem e comportamento com consentimento;
- [ ] pedidos e exceções continuarem sendo exibidos a partir da fonte oficial;
- [ ] confirmação de pedido tiver evidência, versões e integração governada;
- [ ] forecast, metas referenciadas e snapshots puderem ser auditados;
- [ ] dashboards tiverem metodologia e drill-down;
- [ ] IA apresentar fontes, respeitar escopo e exigir confirmação para efeitos sensíveis;
- [ ] todas as integrações possuírem painel de saúde, cursor, retry e dead-letter;
- [ ] acesso, exportação e conteúdo sensível forem auditados;
- [ ] o produto atender requisitos de acessibilidade, responsividade, performance e resiliência;
- [ ] nenhuma regra de negócio crítica existir somente no MFE;
- [ ] nenhum secret ou token externo estiver exposto no frontend;
- [ ] o `commercial-api` permanecer dono do domínio e do escopo comercial;
- [ ] a Core API permanecer dona da governança da plataforma;
- [ ] o ERP permanecer fonte oficial das transações.

---

## 20. Decisões que precisam de homologação antes da implementação de cada bloco

### 20.1 Microsoft 365

- modelo padrão: delegated, consentimento específico ou application;
- tenant ID e app registrations;
- permissões mínimas por recurso;
- política de admin consent;
- caixas compartilhadas e equipes autorizadas;
- retenção de e-mail, chat, transcript e gravação;
- armazenamento de conteúdo completo versus referência/preview;
- mapeamento de usuários e convidados;
- uso de transcrição e atribuição de fala;
- política de exportação e auditoria.

### 20.2 Marketing

- domínio e provedor de envio;
- base legal e política de opt-in;
- frequência máxima;
- identidade visual e processo de aprovação;
- modelo de atribuição;
- fontes de custo;
- domínios que receberão tracking;
- política de cookies;
- critérios iniciais de scoring.

### 20.3 Vendas

- pipelines e etapas;
- critérios obrigatórios por etapa;
- motivos de perda/desqualificação;
- regras de distribuição;
- modelo de forecast;
- alçadas de aprovação;
- conceito de conta ativa/inativa/reativada;
- critérios de saúde e risco;
- dados industriais obrigatórios.

### 20.4 Canais e IA

- provedor de WhatsApp;
- números corporativos e filas;
- provedor de telefonia;
- política de gravação/transcrição;
- modelos de IA autorizados;
- dados que podem ser enviados ao AI Gateway;
- ações que sempre exigem confirmação;
- retenção de prompts e respostas;
- métricas de qualidade e custo.

---

## 21. Referências internas analisadas

### 21.1 Documentação oficial da Minha DELPI

Foram consideradas as documentações oficiais disponíveis sobre:

- visão geral, glossário e mapa da plataforma;
- arquitetura geral, estrutura de repositório, Clean Architecture, fluxo de requisição e eventos;
- ambientes, Docker Compose, Gateway, bancos e variáveis de ambiente;
- Keycloak, SSO, JWT, RBAC e Permission Resolver;
- Core API, controllers, use cases, repositories, Unit of Work, migrations, erros, notificações e modelos;
- plugin system, manifesto, registro, atualização, versionamento, rollback, microfrontends, iframe e backend-only;
- Portal, autenticação frontend, autorização de apps, menu dinâmico, consumo de plugins e favoritos.

Arquivos analisados:

```text
docs/00-visao-geral/glossario.md
docs/00-visao-geral/mapa-da-plataforma.md
docs/00-visao-geral/minha-delpi-visao-geral.md
docs/01-arquitetura/estrutura-de-repositorio.md
docs/01-arquitetura/arquitetura-geral.md
docs/01-arquitetura/clean-architecture.md
docs/01-arquitetura/fluxo-de-requisicao.md
docs/01-arquitetura/event-driven-e-socket.md
docs/02-infraestrutura/variaveis-de-ambiente.md
docs/02-infraestrutura/gateway-nginx.md
docs/02-infraestrutura/bancos-de-dados.md
docs/02-infraestrutura/ambientes-dev-prod.md
docs/02-infraestrutura/docker-compose.md
docs/03-autenticacao-autorizacao/permission-resolver.md
docs/03-autenticacao-autorizacao/rbac.md
docs/03-autenticacao-autorizacao/keycloak-sso.md
docs/03-autenticacao-autorizacao/jwt.md
docs/04-core-api/erros-api.md
docs/04-core-api/modelos-de-banco.md
docs/04-core-api/unit-of-work.md
docs/04-core-api/visao-geral-core-api.md
docs/04-core-api/repositories.md
docs/04-core-api/notificacoes.md
docs/04-core-api/controllers-e-rotas.md
docs/04-core-api/use-cases.md
docs/04-core-api/migrations.md
docs/05-plugin-system/atualizacao-de-manifesto.md
docs/05-plugin-system/versionamento-e-rollback.md
docs/05-plugin-system/backend-only.md
docs/05-plugin-system/registro-de-plugin.md
docs/05-plugin-system/manifesto-plugin.md
docs/05-plugin-system/microfrontends.md
docs/05-plugin-system/iframe.md
docs/06-portal-frontend/favoritos.md
docs/06-portal-frontend/autenticacao-frontend.md
docs/06-portal-frontend/consumo-de-plugins.md
docs/06-portal-frontend/visao-geral-portal.md
docs/06-portal-frontend/app-authorization.md
docs/06-portal-frontend/menu-dinamico.md
```

### 21.2 Código e documentação comercial analisados

```text
commercial-api/
commercial-api/commercial_app/domain/
commercial-api/commercial_app/application/
commercial-api/commercial_app/interface/
commercial-api/migrations/
commercial-api/docs/README.md

plugins/commercial/
plugins/commercial/src/
plugins/commercial/README.md
plugins/commercial/commercial.manifest.json

docs/12-roadmap-e-evolucao/commercial/API-ROUTES.md
docs/12-roadmap-e-evolucao/commercial/ATA-MAPA-NECESSIDADES.md
docs/12-roadmap-e-evolucao/commercial/ATA-FOLLOWUP-IMPLEMENTACOES-AGO2026.md
docs/12-roadmap-e-evolucao/commercial/DATA-MODEL.md
docs/12-roadmap-e-evolucao/commercial/DESIGN-IA-COMERCIAL.md
docs/12-roadmap-e-evolucao/commercial/PARCIAL-INVENTARIO.md
docs/12-roadmap-e-evolucao/commercial/PERFIS-E-PERMISSOES.md
docs/12-roadmap-e-evolucao/commercial/SCOPE-OWNERSHIP.md
docs/12-roadmap-e-evolucao/commercial/UX-E-TASKS-EVOLUTION.md
```

### 21.3 Referências técnicas externas verificadas

Para as integrações Microsoft 365, foram verificadas documentações oficiais sobre:

- listagem de mensagens em chats;
- listagem de mensagens e replies em canais;
- change notifications para chats e canais;
- mensagens e change notifications do Outlook;
- calendários e eventos;
- transcrições e gravações de reuniões;
- controles administrativos de acesso a transcrições;
- permissões delegadas, application permissions e Resource-Specific Consent.

As capacidades externas deverão ser novamente validadas no início da implementação, pois APIs, permissões, licenciamento e políticas de tenant podem evoluir.

### 21.4 Benchmark de mercado — Agendor CRM

Para preencher gaps de rituais, produtividade e saúde do funil (ago/2026), foram consultados:

- [8 rituais de vendas (+ 5 de gestão)](https://www.agendor.com.br/blog/rituais-de-vendas/);
- [Soluções Agendor](https://www.agendor.com.br/solucoes);
- [Funil / mapa de vendas](https://www.agendor.com.br/beneficios/funil-de-vendas);
- [Gestão de CRM](https://www.agendor.com.br/blog/gestao-crm/);
- Central de ajuda — fluxo inteligente de atividades e sumário semanal.

**Adaptação DELPI:** incorporar disciplina, sumários, mapa de vendas, handoff entre funis, scripts e coaching; **não** incorporar Pomodoro/controle de pausas; aderência a rituais serve a qualidade de dados e coaching, não ranking tóxico.

---

## 22. Conclusão

O CRM Minha DELPI deverá transformar o Portal Comercial atual em uma plataforma completa de relacionamento e execução comercial, sem descartar a base já construída e sem romper as fronteiras arquiteturais da Minha DELPI.

A evolução parte de uma fundação real — Conta 360, carteiras, tarefas, pedidos, propostas, analytics, anexos, auditoria e colaboração interna — e adiciona os domínios hoje ausentes: leads, prospects, scoring, segmentos, campanhas, automações, pipelines nativos com mapa de vendas, propostas governadas, comunicações omnicanal, Microsoft 365, forecast, rituais de execução e gestão, planos de conta, IA e governança de dados.

O resultado esperado é uma única visão operacional e histórica da relação com cada empresa, conectando aquisição, prospecção, negociação, pedido, entrega, recompra e expansão. O CRM deverá preservar a origem de cada fato, respeitar o sistema de registro adequado, explicar seus indicadores, controlar seus efeitos e permitir que a DELPI evolua o processo comercial com dados próprios, auditáveis e integrados — inclusive a disciplina diária que transforma o CRM em hábito (rituais), e não apenas em repositório.
