# Pesquisa de satisfação de clientes — Índice mestre de requisitos

> **Status:** escopo funcional completo do Word preservado; entrega 1 (pesquisa/indicadores) e entrega 2 (planos de ação/retorno) definidas em 11/11/2026; implementação **não comprovada**.  
> **Escopo:** evolução do Portal Comercial com persistência das pesquisas sob responsabilidade da API Comercial.  
> **Referência:** branch `main`; revalidar HEAD e contratos reais no início de cada frente, sem tratar um commit histórico como base fixa.

## Como usar este arquivo

**Este é o ponto de entrada.** A decisão de 11/11/2026 inclui uma única seção **Pesquisa de Satisfação do Cliente** na **Visão Geral** do Portal, com os indicadores gerais da primeira entrega, para todos com `commercial.access`, sem respostas individuais.  O [plano de frontend](./FRONTEND-FIRST-RELEASE-PLAN.md) detalha as interfaces da primeira entrega, sem estender o escopo.  A [primeira entrega da pesquisa](./SURVEY-FIRST-RELEASE-CONTRACT.md) foi delimitada em 11/11/2026: campanhas, participantes, convite copiável, formulário, respostas e indicadores. Requisitos não incluídos na entrega 1, especialmente tratamento e planos de ação, **permanecem obrigatórios na entrega 2**; o detalhamento técnico e execução serão programados posteriormente. O [padrão de backend e CAIO](./BACKEND-API-PROPOSAL.md) foi **aceito como arquitetura pelo solicitante em 10/11/2026**, sem comprovar implementação. Primeiro consulte a linha do requisito; só abra o documento em **Detalhe** quando precisar aprofundar aquela frente. Este índice descreve *o que* foi pedido/decidido, **não** comprova que o recurso já esteja implementado e não aprova automaticamente backlog, CRUD ou novas abstrações.

**Fontes e prioridade:** (1) **Plano de Monitoramento da Satisfação dos Clientes — Delpi** — documento integral de 5 páginas anexado às **fontes do projeto** (não há cópia integral publicada nesta pasta); (2) [registro das decisões da entrevista](./BUSINESS-DECISIONS.md), que complementa o plano quando o usuário decidiu um comportamento; (3) fontes técnicas canônicas, a identificar por frente. A página 1 do plano contém exemplos gerais de métodos de pesquisa; **as seções 1–10 e as decisões específicas** governam o produto proposto.

**Regra de prevalência:** a decisão de 11/11/2026 substitui o envio direto de e-mail por convite manual e **ordena** a implementação do plano completo: pesquisa/indicadores primeiro; classificação, planos de ação, retorno/reavaliação e indicadores de acompanhamento depois. “Fora da entrega 1” **nunca** significa “fora do produto”.

**Estados na tabela:** `ENTREGA 2 PLANEJADA` = requisito do Word preservado e obrigatório para a segunda entrega, ainda sem contrato executivo fechado; `DEFINIDO` = decisão funcional informada pelo solicitante; `FONTE DEFINIDA` = especificação explícita no plano; `DEFINIDO COM VALIDAÇÃO` = intenção definida, condicionada a verificação normativa; `TO_INVENTORY` = evidência/contrato técnico ainda a levantar. *Nenhum desses estados significa implementado, testado ou aprovado para release.*

**Regra antirretrabalho:** alterar a linha **somente** quando houver decisão nova, evidência canônica ou impedimento real para implementar/testar. Nunca reabrir assunto já respondido por mera hipótese. Quando uma linha exigir detalhes que não caibam aqui, criar **um documento por assunto necessário nesta mesma pasta** e adicionar o link na coluna Detalhe. Não criar arquivos vazios nem reproduzir todo o conteúdo das fontes. Um requisito fica **pronto para execução** quando regra, owner, contrato a respeitar, critérios verificáveis e dependências da frente estiverem suficientes; revisão técnica é limitada à frente, não a um inventário global recorrente.

## Cobertura do plano Word — sem perda de escopo

| Parte da fonte | Entrega | Cobertura planejada |
|---|---|---|
| §1 Objetivo | 1 e 2 | Monitorar percepção e promover melhoria por meio de pesquisa, análise e tratamento |
| §2 Periodicidade | 1 | Duas pesquisas anuais como referência e janelas configuráveis |
| §§3–6 Dimensões, IGS, NPS e abertas | 1 | Quinze perguntas com textos/escalas fiéis à fonte |
| §7 Segmentação | 1 | Cliente, segmento, vendedor, região, tempo, volume/faturamento e estratégicos, conforme fontes oficiais |
| §8 etapa 1 Consolidação em até cinco dias | 1 (dados e consulta) + processo Comercial | Taxa, IGS, NPS, dimensões, evolução, comentários relevantes e clientes críticos acessíveis a perfis autorizados; prazo operacional preservado |
| §8 etapas 2–4 Classificação, ação e retorno | **2** | Oito categorias, registros por oportunidade, responsável/prazo/status, resposta a clientes críticos |
| §9 Dashboard | 1 e 2 | Indicadores da pesquisa na 1; **indicador de ações concluídas na 2**, sem exibir zero fictício antes |
| §10 Registro no CRM Delpi | 1 e 2 no Portal Comercial | Sequência de referência do Word: Cliente → Pesquisa enviada → Data da pesquisa → Responsável → IGS → NPS → Notas por dimensão → Comentários → Pontos críticos → Plano de ação → Responsável pela ação → Prazo → Status → Reavaliação. Na entrega 1: vínculo campanha/cliente, data, resposta e indicadores; na 2: tratamento, plano, responsáveis, prazos, status e reavaliação. **Não interpretar “Pesquisa enviada” como comprovação de envio**, pois a distribuição do link é manual e não rastreada pela aplicação; IGS/NPS são agregados, não notas individuais. |

**Escopo integral obrigatório:** esta matriz é uma trilha de cobertura, não prova de implementação. O texto introdutório que descreve outros métodos de monitoramento é contextual, não uma lista explícita de funcionalidades contratadas; o plano numerado (§§1–10) é a referência de produto. Quando uma frente for implementada, registrar evidência e lacunas sem reabrir o requisito já decidido.

## Tabela de requisitos

### 01. Público, campanhas e questionário

| ID | Tema | Requisito / decisão | Base | Responsável / autoridade | Estado | Detalhe / verificação |
|---|---|---|---|---|---|---|
| CSS-001 | Público | Selecionar por campanha empresas já cadastradas no TOTVS e consultáveis pelo Portal; sem novo cadastro de clientes. | Decisão Q02–Q03 | Comercial (seleção); TOTVS (cadastro) | DEFINIDO | [Q02–Q03](./BUSINESS-DECISIONS.md); inventariar rota API DELPI |
| CSS-002 | Público | Uma única resposta definitiva por empresa em cada campanha; identificação vinculada à empresa, não à pessoa física. | Decisão Q01/Q04 | Comercial (regra) | DEFINIDO | [Q01/Q04](./BUSINESS-DECISIONS.md) |
| CSS-003 | Campanha | Usar duas campanhas anuais como referência (maio/junho e novembro/dezembro), com datas livremente configuráveis. | Plano §2 p.2; decisão Q05 | Comercial (marketing/manage) | DEFINIDO | [Q05](./BUSINESS-DECISIONS.md) |
| CSS-004 | Campanha | Abertura e encerramento automáticos pelas datas; aceitar respostas apenas durante a janela válida. | Decisão Q05 | Comercial (marketing/manage) | DEFINIDO | [Q05](./BUSINESS-DECISIONS.md); definir fuso e instante de corte na implementação ; [proposta backend](./BACKEND-API-PROPOSAL.md) |
| CSS-005 | Questionário | Preservar as 15 perguntas, texto e ordem: dez dimensões (1–5), satisfação geral (1–5), NPS (0–10), três abertas. | Plano §§3–6 p.2–3; decisão Q09 | Comercial (marketing/manage) | DEFINIDO | [Q09](./BUSINESS-DECISIONS.md); [15/15 textos literais e chaves mapeadas no contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md#14-catálogo-textual-canônico-das-15-perguntas--conferência-com-o-word-em-11112026); ID técnico **proposto** `delpi.commercial.satisfaction-survey.canonical-15@2026-11-11` (ainda não no código) |
| CSS-006 | Questionário | Exigir satisfação geral e recomendação; **exigir escolha explícita de nota 1–5 ou “Não se aplica” em cada uma das dez dimensões** (sem permitir campo em branco no envio); três abertas opcionais. | Decisão Q08, complemento 11/11/2026 | Comercial (marketing/manage) | DEFINIDO | [Q08](./BUSINESS-DECISIONS.md); contrato da entrega 1 distingue campo intocado de N/A selecionado; rascunho somente local antes do envio |
| CSS-007 | Questionário | Revisão antes de enviar; após submissão confirmada, resposta imutável inclusive com campanha aberta. | Decisão entrevista 10 / Q08 | Comercial (marketing/manage) | DEFINIDO | [Q08](./BUSINESS-DECISIONS.md) |

### 02. Convites e respostas

| ID | Tema | Requisito / decisão | Base | Responsável / autoridade | Estado | Detalhe / verificação |
|---|---|---|---|---|---|---|
| CSS-008 | Convite | Gerar link exclusivo e obrigatório por empresa/campanha; compartilhar sem criar segunda resposta. | Decisão Q02 | Comercial (marketing/manage) | DEFINIDO | [Q02](./BUSINESS-DECISIONS.md); inventariar segurança do link ; [proposta backend](./BACKEND-API-PROPOSAL.md) |
| CSS-009 | Convite | Pré-preencher contato/e-mail da consulta ao ERP; permitir edição no convite sem atualizar cadastro mestre. | Decisão Q03 | Comercial (marketing/manage) | DEFINIDO | [Q03](./BUSINESS-DECISIONS.md) |
| CSS-010 | Convite | Oferecer cópia do link e, opcionalmente, da mensagem de convite; usuário envia manualmente fora do Portal, sem disparo integrado. | Decisão Q06 | Comercial (marketing/manage) | DEFINIDO (11/11) | [Q06](./BUSINESS-DECISIONS.md); sem integração de e-mail ; [proposta backend](./BACKEND-API-PROPOSAL.md); [escopo/contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md) |
| CSS-011 | Convite | Copiar link para envio manual via WhatsApp, Teams, e-mail externo ou outros canais; sem integração de disparo desses aplicativos. | Decisão Q06 | Comercial (marketing/manage) | DEFINIDO | [Q06](./BUSINESS-DECISIONS.md) |
| CSS-012 | Convite | Exibir empresas sem resposta e permitir recopiar o mesmo link; usuário faz eventual novo contato fora do Portal. | Decisão Q07 | Comercial (marketing/manage) | DEFINIDO (11/11) | [Q07](./BUSINESS-DECISIONS.md); limites operacionais não especificados; [escopo/contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md) |

### 03. Indicadores, filtros e visualizações

| ID | Tema | Requisito / decisão | Base | Responsável / autoridade | Estado | Detalhe / verificação |
|---|---|---|---|---|---|---|
| CSS-013 | Indicadores | IGS = média aritmética das notas da pergunta geral (1–5), igual peso por empresa; sem ponderar faturamento. | Plano §4 p.3; decisão entrevista 11/Q10 | Comercial (regras); API Comercial (cálculos propostos) | DEFINIDO | [Q10](./BUSINESS-DECISIONS.md) |
| CSS-014 | Indicadores | NPS = % promotores (9–10) menos % detratores (0–6); neutros (7–8) no denominador; igual peso por empresa. | Plano §5 p.3; decisão entrevista 12/Q11 | Comercial (regras); API Comercial (cálculos propostos) | DEFINIDO | [Q11](./BUSINESS-DECISIONS.md) |
| CSS-015 | Indicadores | Calcular médias das dez dimensões só com notas válidas; 'Não se aplica' não é nota nem entra na média. | Plano §§3/9 p.2/4; decisão Q08 | Comercial (regras); API Comercial (cálculos propostos) | DEFINIDO | [Q08](./BUSINESS-DECISIONS.md) ; [proposta backend](./BACKEND-API-PROPOSAL.md) |
| CSS-016 | Indicadores | Classificar satisfação geral: 1–2 críticos, 3 neutros/intermediários, 4–5 satisfeitos; sem classificação individual por dimensão. | Plano §§3/9 p.2/4; decisão entrevista 13/Q12 | Comercial (regras); API Comercial (cálculos propostos) | DEFINIDO | [Q12](./BUSINESS-DECISIONS.md) |
| CSS-017 | Indicadores | Taxa de resposta = empresas respondentes ÷ empresas convidadas, por campanha. | Plano §9 p.4 | Comercial (regras); API Comercial (cálculos propostos) | FONTE DEFINIDA | [Plano no projeto](./README.md); validar semântica de convite no contrato |
| CSS-018 | Indicadores | Acompanhar evolução dos indicadores e comparar com pesquisa anterior, em visão semestral/anual, **identificando deterioração** em clientes ou dimensões; o Word §4 prioriza essa evolução em relação a uma “nota ideal”. | Plano §§8–9 p.4 | Comercial (regras); API Comercial (cálculos propostos) | FONTE DEFINIDA | [Q14](./BUSINESS-DECISIONS.md); mesma base de público não presumida |
| CSS-019 | Visualização | Exibir filtros: cliente, segmento, vendedor, região, tempo de relacionamento, volume/faturamento e estratégico versus demais. | Plano §7 p.3 | Comercial (regras); API Comercial (cálculos propostos) | FONTE DEFINIDA | [Q13](./BUSINESS-DECISIONS.md); inventariar fontes e períodos ; [proposta backend](./BACKEND-API-PROPOSAL.md) |
| CSS-020 | Visualização | Oferecer comparação simples Geral / Estratégicos / Demais para satisfação geral e dimensões, como no exemplo do plano. | Plano §7 p.3 | Comercial (regras); API Comercial (cálculos propostos) | FONTE DEFINIDA | [Q13](./BUSINESS-DECISIONS.md); valores ilustrativos não são dados reais |
| CSS-021 | Visualização | Disponibilizar IGS, NPS, taxa de resposta, médias dimensionais, % satisfeitos/críticos, evolução e ações concluídas. | Plano §9 p.4 | Comercial (regras); API Comercial (cálculos propostos) | FONTE DEFINIDA | [Q20](./BUSINESS-DECISIONS.md); evitar criar painéis além do necessário ; [proposta backend](./BACKEND-API-PROPOSAL.md); [seção Pesquisa de Satisfação](./FRONTEND-FIRST-RELEASE-PLAN.md#35-seção-pesquisa-de-satisfação-do-cliente-na-visão-geral-decisão-11112026) |

### 04. Consolidação e tratamento

| ID | Tema | Requisito / decisão | Base | Responsável / autoridade | Estado | Detalhe / verificação |
|---|---|---|---|---|---|---|
| CSS-022 | Consolidação | Até cinco dias após encerramento, consolidar indicadores, evolução, comentários relevantes e clientes críticos. A pergunta sobre **necessidades não atendidas** pode revelar oportunidades comerciais, técnicas e de relacionamento (Word §6); analisar tais comentários sem presumir classificação ou ação automática. | Plano §8 etapa 1 p.4 | Comercial (marketing/manage) | FONTE DEFINIDA | [Q20](./BUSINESS-DECISIONS.md); prazo do processo, não automação presumida |
| CSS-023 | Tratamento | Classificar problemas nas oito categorias: Produto, Qualidade, Entrega, Atendimento, Comercial, Técnico, Comunicação e Preço. | Plano §8 etapa 2 p.4 | Comercial (marketing/manage) | ENTREGA 2 PLANEJADA | [Q15](./BUSINESS-DECISIONS.md); regra automática de triagem não prevista ; [sequência e escopo](./README.md#decisão-de-escopo-completo-e-entregas-11112026) |
| CSS-024 | Tratamento | Registrar por oportunidade relevante: problema, cliente, causa, ação, responsável, prazo e status. | Plano §8 etapa 3 p.4 | Comercial (marketing/manage) | ENTREGA 2 PLANEJADA | [Q16](./BUSINESS-DECISIONS.md); status concretos a especificar no menor contrato ; [proposta backend](./BACKEND-API-PROPOSAL.md) ; [sequência e escopo](./README.md#decisão-de-escopo-completo-e-entregas-11112026) |
| CSS-025 | Tratamento | Marketing e Manage operam triagem, atribuição/acompanhamento de ações e registro de retornos/reavaliações. | Decisão Q04 e complemento 10/11 | Comercial (marketing/manage) | ENTREGA 2 PLANEJADA | [Q15–Q17](./BUSINESS-DECISIONS.md) ; [sequência e escopo](./README.md#decisão-de-escopo-completo-e-entregas-11112026) |
| CSS-026 | Tratamento | Acompanhar retorno aos clientes com críticas relevantes e sua reavaliação; preservar o **texto-modelo do Word §8 etapa 4** como referência editorial, não mensagem obrigatória nem autorização de disparo automático. | Plano §8 etapa 4 p.4 / §10 p.5 | Comercial (marketing/manage) | ENTREGA 2 PLANEJADA | [Q17](./BUSINESS-DECISIONS.md); canal específico não definido ; [sequência e escopo](./README.md#decisão-de-escopo-completo-e-entregas-11112026) |
| CSS-027 | Indicadores | Planos de ação concluídos = número de ações concluídas ÷ número de ações identificadas. | Plano §9 p.4 | Comercial (marketing/manage) | ENTREGA 2 PLANEJADA | [Q16/Q20](./BUSINESS-DECISIONS.md) ; [sequência e escopo](./README.md#decisão-de-escopo-completo-e-entregas-11112026) |

### 05. Acesso, dados e arquitetura

| ID | Tema | Requisito / decisão | Base | Responsável / autoridade | Estado | Detalhe / verificação |
|---|---|---|---|---|---|---|
| CSS-028 | Acesso | `commercial.marketing` (novo requisito) e `commercial.manage` (código existente) gerem campanhas, convites, respostas individualizadas e tratamento. | Decisão Q04 | Comercial (perfis); autoridade técnica inventariada 11/11/2026 | DEFINIDO / IMPLEMENTAR NA ETAPA | [Q04](./BUSINESS-DECISIONS.md); **confirmado no código:** `commercial.access` + `commercial.manage`; **`commercial.marketing` ausente** (manifest/API); matriz R13 em [contrato §4.1](./SURVEY-FIRST-RELEASE-CONTRACT.md); [UI-07 gates](./UI-07-DETALHES-RESPOSTA.md#0-matriz-dos-seis-gates-auditoria-11112026) |
| CSS-029 | Acesso | Demais usuários autorizados do Portal Comercial acessam somente resultados agregados, sem configuração ou respostas por empresa. | Decisão Q04 | Comercial (perfis); autoridade técnica TO_INVENTORY | DEFINIDO | [Q04](./BUSINESS-DECISIONS.md); evitar reidentificação por filtros; [seção Pesquisa de Satisfação](./FRONTEND-FIRST-RELEASE-PLAN.md#35-seção-pesquisa-de-satisfação-do-cliente-na-visão-geral-decisão-11112026) |
| CSS-030 | Dados | Entrega 1: guardar campanhas, participantes e respostas em três tabelas no domínio da API Comercial. Entrega 2: acrescentar persistência de classificação, planos de ação, retornos e reavaliação, vinculada à pesquisa. | Decisão 10/11 / Q18–Q19 | API Comercial (domínio) | CONTRATO DEFINIDO | [Q18–Q19](./BUSINESS-DECISIONS.md); contratos físicos TO_INVENTORY ; [proposta backend](./BACKEND-API-PROPOSAL.md); [escopo/contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md) |
| CSS-031 | Dados | Preservar histórico por tempo indeterminado para análise plurianual; revisar proteção e necessidade de dados pessoais conforme LGPD. | Decisão 10/11 / Q18 | Comercial (finalidade); governança LGPD a validar | DEFINIDO COM VALIDAÇÃO | [Q18](./BUSINESS-DECISIONS.md); validação jurídica/privacidade necessária |
| CSS-032 | Arquitetura | Reutilizar cadastro do TOTVS via API DELPI; a API Comercial é autoridade das regras e dados da pesquisa; frontend apenas interface. | Decisão Q03/Q19 | API Comercial (pesquisa); TOTVS (cadastro) | DEFINIDO / TO_INVENTORY | [Q03/Q19](./BUSINESS-DECISIONS.md); verificar owners e consumidores reais ; [proposta backend](./BACKEND-API-PROPOSAL.md) |
| CSS-033 | Implementação | Inventariar por frente antes de codificar: HEAD, branch, contratos, rotas, permissões backend, consumidores e testes; menor diff correto. | Decisão 10/11 / Q19 | Owner técnico TO_INVENTORY por frente | POR ETAPA | [Q19](./BUSINESS-DECISIONS.md); não transformar em inventário global interminável ; [proposta backend](./BACKEND-API-PROPOSAL.md); [escopo/contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md) |
| CSS-034 | Segurança | Autorizar gravações/consultas restritas no backend; validar dados, auditar operações, proteger tokens de convite e dados pessoais. | Diretrizes do projeto; decisões Q04/Q18 | Backend (autorização); owners de segurança TO_INVENTORY | POR ETAPA | [Q04/Q18](./BUSINESS-DECISIONS.md); conformidade e controles de segurança exigidos ; [proposta backend](./BACKEND-API-PROPOSAL.md); [escopo/contrato](./SURVEY-FIRST-RELEASE-CONTRACT.md) |

## Limites confirmados e critérios de avanço

- **Sequência obrigatória:** entrega 1 — pesquisa, respostas e indicadores; entrega 2 — classificação, planos de ação, acompanhamento, retorno ao cliente, reavaliação e percentual de ações concluídas. Todos os requisitos operacionais do Word permanecem no produto.
- **Não previstos como implementação (por decisão explícita):** envio de e-mail ou WhatsApp/Teams diretamente pelo Portal; lembretes automáticos; segunda resposta por empresa/campanha; edição após submissão definitiva; personalização das quinze perguntas; cadastro mestre paralelo ao TOTVS. O texto introdutório genérico do Word não cria sozinho escopo para CSAT/CES ou monitoramento de redes sociais.
- **Não inferir sem evidência:** rotas, tabelas físicas, enums de status, autorização já implementada, envio em lote/agendado, alertas automáticos, novas telas ou módulos complexos.
- **Aprofundar só ao implementar:** contrato de consulta a clientes, link copiável/token, modelos de campanhas/respostas, cálculos, filtros, permissões, auditoria e critérios de aceite; na segunda entrega, contratos de problemas, ações, retornos, reavaliação e percentual de conclusão. Cada frente deve identificar arquivos e testes reais.
- **Pendências que não reabrem negócio por si só:** detalhes de corte/fuso; rascunho/resposta interrompida; limites de reenvio; status das ações; canal de retorno; disponibilidade dos segmentos. Decidir o mínimo necessário apenas se bloquear uma frente.
- **Cuidados obrigatórios:** retenção histórica não dispensa LGPD; garantir finalidade, minimização, transparência, segurança, controle de acesso e revisão periódica da necessidade de dados pessoais.

## Documentos desta pasta

| Documento | Função | Quando ler |
|---|---|---|
| [README.md](./README.md) | Contexto e fontes resumidas | Para entender por que esta frente existe |
| **REQUIREMENTS-INDEX.md** (este arquivo) | Índice navegável e estado dos requisitos | Sempre, antes de investigar ou especificar uma frente |
| [BUSINESS-DECISIONS.md](./BUSINESS-DECISIONS.md) | Registro histórico das decisões, evidências e ressalvas | Somente quando a linha exigir detalhe de negócio |
| [BACKEND-API-PROPOSAL.md](./BACKEND-API-PROPOSAL.md) | Padrão de arquitetura aceito: REST, dados, autorização e paridade CAIO; implementação ainda pendente | Para trabalhar cada frente de backend |
| [SURVEY-FIRST-RELEASE-CONTRACT.md](./SURVEY-FIRST-RELEASE-CONTRACT.md) | Contrato técnico da primeira entrega, com três tabelas, formulários, indicadores e operações sem envio de e-mail nem plano de ação | Antes de desenvolver qualquer etapa da pesquisa |
| [FRONTEND-FIRST-RELEASE-PLAN.md](./FRONTEND-FIRST-RELEASE-PLAN.md) | Planejamento do frontend: navegação interna, formulário público, resultados, contratos e testes | Na implementação do plugin Comercial |
| [UI-01-RESULTADOS-PESQUISA.md](./UI-01-RESULTADOS-PESQUISA.md) | Página de Resultados: wireframe, filtros, indicadores, gráficos, tabelas e inventário PluginUI | Especificar/desenvolver resultados |
| [UI-02-CONFIGURACAO-PESQUISAS.md](./UI-02-CONFIGURACAO-PESQUISAS.md) | Página de Configuração: campanhas, participantes, cópia de convites, estados e componentes | Especificar/desenvolver gestão |
| [UI-03-FORMULARIO-PUBLICO.md](./UI-03-FORMULARIO-PUBLICO.md) | Página pública: 15 questões, revisão e submissão, reuso public-hub/PluginUI | Especificar/desenvolver formulário |
| [UI-04-INICIO-CARD-MARKETING.md](./UI-04-INICIO-CARD-MARKETING.md) | Integração no Início: card Marketing, navegação e capacidade | Inserir entrada no hub existente |
| [UI-05-VISAO-GERAL-SECAO-PESQUISA.md](./UI-05-VISAO-GERAL-SECAO-PESQUISA.md) | Integração na Visão Geral: seção única de indicadores consolidados | Integrar resumo existente |
| [UI-06-RESPOSTAS-POR-EMPRESA.md](./UI-06-RESPOSTAS-POR-EMPRESA.md) | Lista privada respondentes/pendentes; avatar; navegação para UI-07 | Especificar/desenvolver consulta identificada |
| [UI-07-DETALHES-RESPOSTA.md](./UI-07-DETALHES-RESPOSTA.md) | Página de detalhe da resposta; seis gates G01–G06; RatingDots candidato | Antes de implementar detalhe / PluginUI / R13 |
| Documento detalhado novo | Criar **quando necessário**, com ID(s) relacionado(s), owner, evidência, contrato, critérios de aceite e link no índice | Só na frente correspondente |

**Auditoria UI-07 (11/11/2026):** gates G01–G05 em `CLOSED_SPEC` (contratos); G06 `PENDING_IMPLEMENTATION`; **nenhum** `CLOSED_VERIFIED`. Implementação da página, R13, `commercial.marketing` e `RatingDots` exigem autorização posterior. Ver [matriz em UI-07](./UI-07-DETALHES-RESPOSTA.md#0-matriz-dos-seis-gates-auditoria-11112026).

**Critério de conclusão desta etapa:** organização documental, não implementação. Próxima atividade: escolher uma frente delimitada, inventariar seu contrato atual e produzir sua especificação/testes sem reabrir as decisões já fechadas.
